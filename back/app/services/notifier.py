"""알림 생성 + 이메일 발송 자동화 (5주차 우선순위 P1 "알림·이메일 발송 자동화 파이프라인").

scheduler.py의 매일 06시(기본) 자동 수집 직후 이 순서로 실행됩니다:
  ① 공고 수집·저장 (scheduler.py, storage.py — 기존)
  ② 키워드 매칭 + 저장공고 마감임박으로 알림 생성 → notification_logs 적재
     (generate_keyword_match_notifications)
  ③ 아직 이메일로 안 보낸 알림을 사용자별로 모아 이메일 발송 (send_pending_notification_emails)

알림 설정 반영 (docs/fe/alert-settings-API-제안.md):
- 알림 종류는 두 갈래다 — ① 키워드 매칭(신규매칭 + 그 공고의 마감임박, keyword_id 있음)은
  keywords.dashboard_alert/email_alert를 따르고, ② 즐겨찾기(저장공고) 마감임박(keyword_id
  NULL)은 alert_settings.deadline_dashboard_alert/deadline_email_alert를 따른다(6-1 A안:
  화면이 "즐겨찾기 마감임박"이라고 약속한 대로, 저장공고 자체를 기준으로 판정한다).
- "마감임박" 판정은 announcements.py의 전역 DEADLINE_SOON_DAYS(공고 목록 배지 표시용)가
  아니라 사용자별 alert_settings.deadline_alert_days(없으면 기본값 7)를 쓴다 — 이 둘은
  이름은 같지만 다른 개념이다(6-2절).
- alert_settings 행이 없는 사용자는 화면 기본값(매일 발송, D-7, 대시보드 on/이메일 off)으로
  취급한다.

주의:
- ②는 매일 전체를 다시 계산해도 안전합니다. notification_logs의 UNIQUE(user_id, announcement_id,
  notify_type) 제약 + INSERT IGNORE로, 이미 만들어진 알림은 자동으로 건너뜁니다. 키워드 마감임박과
  즐겨찾기 마감임박이 같은 공고를 가리켜도 이 제약 덕분에 한 행으로 자연스럽게 합쳐집니다.
- ③(이메일 발송)은 .env에 SMTP_HOST가 설정되어 있어야 실제로 동작합니다. 아직 어떤 이메일
  서비스(SMTP 릴레이/Gmail/SendGrid 등)를 쓸지 팀 결정 전이라, 기본값(SMTP_HOST 빈 값)에서는
  실제 발송 없이 로그만 남기고 넘어갑니다 — 즉 이 상태로 배포해도 안전합니다(알림 저장까지는
  정상 동작, 이메일만 보류). SMTP 값이 채워지면 코드 수정 없이 바로 발송이 시작됩니다.
- email_alert=false(키워드)나 email_frequency=weekly인데 오늘이 월요일이 아닌 경우처럼
  "지금은 보낼 대상이 아닌" 알림은 emailed_at을 채우지 않고 그대로 pending으로 남겨서
  다음 실행(주간 발송이면 다음 월요일)에 다시 판단하게 한다.
"""
import logging
import smtplib
import uuid
from datetime import date, datetime, timedelta
from email.mime.text import MIMEText
from typing import NamedTuple

from sqlalchemy import select
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import AlertSetting, Announcement, Keyword, NotificationLog, SavedAnnouncement, User

logger = logging.getLogger("app.notifier")


class _AlertSettingView(NamedTuple):
    email_frequency: str
    deadline_alert_days: int
    deadline_dashboard_alert: bool
    deadline_email_alert: bool


_DEFAULT_ALERT_SETTING = _AlertSettingView(
    email_frequency="daily", deadline_alert_days=7, deadline_dashboard_alert=True, deadline_email_alert=False
)


def _load_alert_settings(db: Session) -> dict[str, _AlertSettingView]:
    rows = db.execute(select(AlertSetting)).scalars().all()
    return {
        row.user_id: _AlertSettingView(
            row.email_frequency, row.deadline_alert_days, row.deadline_dashboard_alert, row.deadline_email_alert
        )
        for row in rows
    }


def _is_deadline_soon(reception_end: date | None, days: int) -> bool:
    """마감일이 아직 안 지났고, days일 이내로 다가왔는지. reception_end 정보가 없으면 판단 불가(False)."""
    if reception_end is None:
        return False
    today = date.today()
    return today <= reception_end <= today + timedelta(days=days)


def generate_keyword_match_notifications(db: Session) -> int:
    """키워드 매칭 + 즐겨찾기 마감임박으로 notification_logs에 알림을 쌓는다.

    - notify_type="신규매칭": 제목에 키워드가 포함된 공고 (keyword.dashboard_alert=false면 건너뜀)
    - notify_type="마감임박": 위 매칭 중 사용자의 deadline_alert_days 이내로 마감인 것(keyword_id 있음),
      그리고 즐겨찾기(저장공고) 중 같은 기준으로 마감임박인 것(keyword_id NULL, alert_settings의
      deadline_dashboard_alert가 true인 사용자만)
    반환값은 이번 호출에서 새로 생긴 알림 개수(중복 스킵분 제외).
    """
    alert_settings_by_user = _load_alert_settings(db)
    rows_to_insert: list[dict] = []

    keyword_rows = db.execute(
        select(Keyword.id, Keyword.user_id, Keyword.keyword).where(Keyword.dashboard_alert.is_(True))
    ).all()
    for keyword_id, user_id, keyword in keyword_rows:
        deadline_days = alert_settings_by_user.get(user_id, _DEFAULT_ALERT_SETTING).deadline_alert_days
        matched = db.execute(
            select(Announcement).where(Announcement.title.ilike(f"%{keyword}%"))
        ).scalars().all()
        for ann in matched:
            rows_to_insert.append(
                {
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "announcement_id": ann.id,
                    "keyword_id": keyword_id,
                    "notify_type": "신규매칭",
                    "title": f"[신규] {ann.title}",
                }
            )
            if _is_deadline_soon(ann.reception_end, deadline_days):
                rows_to_insert.append(
                    {
                        "id": str(uuid.uuid4()),
                        "user_id": user_id,
                        "announcement_id": ann.id,
                        "keyword_id": keyword_id,
                        "notify_type": "마감임박",
                        "title": f"[마감임박] {ann.title}",
                    }
                )

    saved_rows = db.execute(
        select(SavedAnnouncement.user_id, Announcement)
        .join(Announcement, Announcement.id == SavedAnnouncement.announcement_id)
    ).all()
    for user_id, ann in saved_rows:
        setting = alert_settings_by_user.get(user_id, _DEFAULT_ALERT_SETTING)
        if not setting.deadline_dashboard_alert:
            continue
        if _is_deadline_soon(ann.reception_end, setting.deadline_alert_days):
            rows_to_insert.append(
                {
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "announcement_id": ann.id,
                    "keyword_id": None,
                    "notify_type": "마감임박",
                    "title": f"[마감임박] {ann.title}",
                }
            )

    if not rows_to_insert:
        return 0

    # 이미 있는 (user_id, announcement_id, notify_type) 조합은 INSERT IGNORE로 조용히 스킵
    # (키워드발 마감임박과 즐겨찾기발 마감임박이 같은 공고를 가리켜도 한 행으로 합쳐짐)
    stmt = mysql_insert(NotificationLog).values(rows_to_insert).prefix_with("IGNORE")
    result = db.execute(stmt)
    db.commit()
    return result.rowcount


def _build_email_body(rows: list[NotificationLog]) -> str:
    lines = [f"- {row.title}" for row in rows]
    return "Forward에 새로운 알림이 있습니다:\n\n" + "\n".join(lines) + "\n\n앱에서 확인해주세요."


def _send_email(to_email: str, subject: str, body: str) -> None:
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM_EMAIL or settings.SMTP_USERNAME
    msg["To"] = to_email

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
        if settings.SMTP_USE_TLS:
            server.starttls()
        if settings.SMTP_USERNAME:
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.send_message(msg)


def send_pending_notification_emails(db: Session) -> int:
    """emailed_at이 비어있는 알림 중 이메일 설정이 켜진 것만 사용자별로 묶어 발송.

    SMTP_HOST가 비어있으면(기본값) 실제 발송 없이 로그만 남기고 0을 반환한다.
    한 사용자에게 보내는 이메일이 실패해도 다른 사용자 발송은 계속 진행한다.
    반환값: 이번 호출에서 발송 처리(=emailed_at 갱신)된 알림 개수.
    """
    if not settings.SMTP_HOST:
        logger.info("SMTP_HOST가 비어있어 이메일 발송을 건너뜁니다 (알림 저장 자체는 정상 동작).")
        return 0

    pending = db.execute(
        select(NotificationLog).where(NotificationLog.emailed_at.is_(None))
    ).scalars().all()
    if not pending:
        return 0

    keyword_email_alert = dict(db.execute(select(Keyword.id, Keyword.email_alert)).all())
    alert_settings_by_user = _load_alert_settings(db)
    today_is_monday = date.today().weekday() == 0

    by_user: dict[str, list[NotificationLog]] = {}
    for row in pending:
        setting = alert_settings_by_user.get(row.user_id, _DEFAULT_ALERT_SETTING)
        if setting.email_frequency == "weekly" and not today_is_monday:
            continue  # 다음 실행(다음 월요일)에 다시 판단 — emailed_at은 그대로 둔다

        if row.keyword_id is not None:
            eligible = keyword_email_alert.get(row.keyword_id, False)
        else:
            eligible = setting.deadline_email_alert
        if not eligible:
            continue

        by_user.setdefault(row.user_id, []).append(row)

    if not by_user:
        return 0

    emailed_count = 0
    for user_id, rows in by_user.items():
        user = db.get(User, user_id)
        if user is None:
            continue
        try:
            _send_email(user.email, "[Forward] 새 알림이 있습니다", _build_email_body(rows))
        except Exception:
            logger.exception("알림 이메일 발송 실패: user_id=%s", user_id)
            continue
        now = datetime.utcnow()
        for row in rows:
            row.emailed_at = now
        emailed_count += len(rows)

    db.commit()
    return emailed_count
