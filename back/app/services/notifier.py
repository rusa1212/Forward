"""알림 생성 + 이메일 발송 자동화 (5주차 우선순위 P1 "알림·이메일 발송 자동화 파이프라인").

scheduler.py의 자동 수집(기본 하루 2회, 06시·18시) 직후 매 실행마다 이 순서로 돌아갑니다:
  ① 공고 수집·저장 (scheduler.py, storage.py — 기존)
  ② 키워드 매칭 + 저장공고 마감임박으로 알림 생성 → notification_logs 적재
     (generate_keyword_match_notifications)
  ③ 아직 이메일로 안 보낸 알림을 사용자별로 모아 이메일 발송 (send_pending_notification_emails)
     — 수집이 하루 2회이므로 daily 사용자는 새 매칭 공고를 반나절 안에 메일로 받는다.

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
- ②는 매 실행마다 전체를 다시 계산해도 안전합니다. notification_logs의 UNIQUE(user_id, announcement_id,
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

from sqlalchemy import or_, select
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import AlertSetting, Announcement, Keyword, NotificationLog, SavedAnnouncement, User
from app.db.session import SessionLocal

logger = logging.getLogger("app.notifier")


class EmailNotConfiguredError(RuntimeError):
    """SMTP_HOST가 비어있어 실제 이메일 발송이 불가능한 상태.

    자동 파이프라인(send_pending_notification_emails)은 이 경우 조용히 건너뛰지만,
    사용자가 화면에서 직접 "지금 이메일로 받기"를 누른 경우엔 왜 안 보내지는지
    알려줘야 하므로 예외로 구분한다."""


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


def _not_closed_yet():
    """메일에 담아도 되는 알림인지 — 그 공고가 아직 마감되지 않았는지의 SQL 조건.

    이미 마감된 공고를 메일로 보내봐야 사용자가 할 수 있는 일이 없다. 키워드 하나에
    매칭이 수백 건이면 그 대부분이 지나간 공고라(2026-09 실측: "축제" 475건 중 271건이
    마감), 걸러내지 않으면 지금 지원 가능한 공고가 그 안에 묻힌다.

    **모든 발송 경로가 이 조건을 함께 써야 한다.** 한 곳만 거르면 거기서 빠진 알림이
    emailed_at=NULL(미발송)로 남아, 다음에 다른 경로가 발송할 때 그대로 쓸려나간다
    (실제로 그렇게 마감 공고 271건이 30초 뒤 두 번째 메일로 다시 나갔다).

    마감일 정보가 없는 공고(기한미정)는 마감됐다고 단정할 수 없으므로 보낸다.
    알림에 announcement_id가 없는 경우(LEFT JOIN 미스)도 막지 않는다.
    """
    today = date.today()
    return or_(
        Announcement.id.is_(None),
        Announcement.reception_end.is_(None),
        Announcement.reception_end >= today,
    )


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


def notify_new_keyword_matches(db: Session, keyword: Keyword) -> int:
    """키워드를 막 등록한 직후, 그 키워드에 매칭되는 공고로 알림을 만들고 곧바로 메일을 보낸다.

    정기 수집(collect_cycle)의 2, 3단계를 방금 만든 키워드 하나에 대해서만 즉시 수행하는 것이다.
    generate_keyword_match_notifications처럼 전체 키워드를 다시 훑지는 않는다 — 등록 응답을
    기다리는 사용자를 (전체 키워드 x 공고 43,000건) 스캔으로 붙잡아 둘 이유가 없다.

    메일에는 **아직 마감되지 않은 공고만** 담는다. 매칭의 상당수가 이미 지나간 공고라
    (2026-09 실측: 키워드 "AI"는 1,684건 중 1,239건이 마감), 전부 보내면 지금 지원할 수 있는
    공고가 그 안에 묻힌다. 마감된 공고도 알림으로는 쌓이므로 화면에서는 그대로 볼 수 있다.

    발송 주기(daily/weekly)는 따지지 않는다 — 사용자가 방금 키워드를 등록한 직후라
    "지금 이메일로 받기"(send_notifications_to_user_now)와 같은 성격의 즉시 발송이다.

    반환값: 이번에 이메일로 보낸 알림 개수 (이메일 토글이 꺼져 있거나 SMTP 미설정이면 0).
    """
    # 정기 파이프라인과 같은 규칙: 대시보드 알림이 꺼진 키워드는 알림 자체를 만들지 않는다.
    if not keyword.dashboard_alert:
        return 0

    setting = _load_alert_settings(db).get(keyword.user_id, _DEFAULT_ALERT_SETTING)
    matched = db.execute(
        select(Announcement).where(Announcement.title.ilike(f"%{keyword.keyword}%"))
    ).scalars().all()

    rows_to_insert: list[dict] = []
    for ann in matched:
        rows_to_insert.append(
            {
                "id": str(uuid.uuid4()),
                "user_id": keyword.user_id,
                "announcement_id": ann.id,
                "keyword_id": keyword.id,
                "notify_type": "신규매칭",
                "title": f"[신규] {ann.title}",
            }
        )
        if _is_deadline_soon(ann.reception_end, setting.deadline_alert_days):
            rows_to_insert.append(
                {
                    "id": str(uuid.uuid4()),
                    "user_id": keyword.user_id,
                    "announcement_id": ann.id,
                    "keyword_id": keyword.id,
                    "notify_type": "마감임박",
                    "title": f"[마감임박] {ann.title}",
                }
            )

    if rows_to_insert:
        # 같은 공고가 다른 키워드로 이미 알림이 된 경우는 UNIQUE 제약 덕에 조용히 스킵된다.
        stmt = mysql_insert(NotificationLog).values(rows_to_insert).prefix_with("IGNORE")
        db.execute(stmt)
        db.commit()

    if not keyword.email_alert:
        return 0
    if not settings.SMTP_HOST:
        logger.info("SMTP_HOST가 비어있어 이메일 발송을 건너뜁니다 (알림 저장 자체는 정상 동작).")
        return 0

    pending = db.execute(
        select(NotificationLog)
        .join(Announcement, Announcement.id == NotificationLog.announcement_id, isouter=True)
        .where(
            NotificationLog.keyword_id == keyword.id,
            NotificationLog.emailed_at.is_(None),
            _not_closed_yet(),
        )
        .order_by(Announcement.reception_end.asc())
    ).scalars().all()
    if not pending:
        return 0

    user = db.get(User, keyword.user_id)
    if user is None:
        return 0

    _send_email(user.email, f"[Forward] 키워드 '{keyword.keyword}' 매칭 공고", _build_email_body(pending))
    now = datetime.utcnow()
    for row in pending:
        row.emailed_at = now
    db.commit()
    return len(pending)


def notify_new_keyword_matches_in_background(keyword_id: str) -> None:
    """FastAPI BackgroundTasks용 진입점.

    요청용 세션은 응답과 함께 닫히므로 여기서 자체 세션을 연다. 그리고 여기서 나는 오류가
    키워드 등록을 실패시키면 안 되므로(등록은 이미 커밋됐고 응답도 나갔다) 전부 잡아서 로그만
    남긴다 — 메일 서버가 죽어 있다고 키워드가 안 만들어지면 곤란하다.
    """
    db = SessionLocal()
    try:
        keyword = db.get(Keyword, keyword_id)
        if keyword is None:  # 등록 직후 삭제된 경우
            return
        sent = notify_new_keyword_matches(db, keyword)
        logger.info("키워드 등록 즉시 알림: keyword=%s emailed=%d", keyword.keyword, sent)
    except Exception:
        logger.exception("키워드 등록 직후 알림/발송 실패: keyword_id=%s", keyword_id)
    finally:
        db.close()


# 메일 한 통에 담을 최대 알림 수. 흔한 키워드는 매칭이 수백 건이라(예: "AI" 1,684건)
# 전부 나열하면 본문이 수백 줄이 되고, 메일 서버가 크기 제한으로 거부하기도 한다.
EMAIL_MAX_ITEMS = 100


def _build_email_body(rows: list[NotificationLog]) -> str:
    lines = [f"- {row.title}" for row in rows[:EMAIL_MAX_ITEMS]]
    if len(rows) > EMAIL_MAX_ITEMS:
        lines.append(f"... 외 {len(rows) - EMAIL_MAX_ITEMS}건 (앱에서 전체 확인)")
    return "Forward에 새로운 알림이 있습니다:\n\n" + "\n".join(lines) + "\n\n앱에서 확인해주세요."


def _send_email(to_email: str, subject: str, body: str) -> None:
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM_EMAIL or settings.SMTP_USERNAME
    msg["To"] = to_email

    # 포트 465는 관례상 "암시적 SSL"(연결 시작부터 전체 암호화)이라 SMTP_SSL을 쓰고,
    # 그 외 포트는 평문으로 연결한 뒤 STARTTLS로 승격하는 게 표준(587이 대표적)이다.
    # 사내 메일서버(예: 회사 SMTP 릴레이)가 465/SSL만 지원하는 경우가 있어, 그때 가서
    # 코드를 또 고치지 않도록 여기서 미리 둘 다 지원해둔다 — .env의 SMTP_PORT만 맞추면 된다.
    smtp_cls = smtplib.SMTP_SSL if settings.SMTP_PORT == 465 else smtplib.SMTP
    with smtp_cls(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
        if settings.SMTP_USE_TLS and settings.SMTP_PORT != 465:
            server.starttls()
        if settings.SMTP_USERNAME:
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.send_message(msg)


def send_pending_notification_emails(db: Session) -> int:
    """emailed_at이 비어있는 알림 중 이메일 설정이 켜진 것만 사용자별로 묶어 발송.

    scheduler가 수집(하루 2회)마다 ② 알림 생성 직후 호출한다. emailed_at으로 이미
    보낸 건 걸러지므로, 각 실행에서는 그 회차에 새로 생긴 매칭만 메일로 나간다
    (daily 사용자 기준 — weekly 사용자는 월요일 실행에만 발송).

    SMTP_HOST가 비어있으면(기본값) 실제 발송 없이 로그만 남기고 0을 반환한다.
    한 사용자에게 보내는 이메일이 실패해도 다른 사용자 발송은 계속 진행한다.
    반환값: 이번 호출에서 발송 처리(=emailed_at 갱신)된 알림 개수.
    """
    if not settings.SMTP_HOST:
        logger.info("SMTP_HOST가 비어있어 이메일 발송을 건너뜁니다 (알림 저장 자체는 정상 동작).")
        return 0

    # 마감된 공고의 알림은 제외한다 — 등록 즉시 발송이 걸러낸 것과 같은 기준이어야
    # 여기서 다시 쓸려나가지 않는다(_not_closed_yet 참고).
    pending = db.execute(
        select(NotificationLog)
        .join(Announcement, Announcement.id == NotificationLog.announcement_id, isouter=True)
        .where(NotificationLog.emailed_at.is_(None), _not_closed_yet())
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


def send_notifications_to_user_now(db: Session, user: User) -> int:
    """사용자가 화면에서 직접 요청한 "지금 이메일로 받기".

    자동 발송(send_pending_notification_emails)과 달리 발송 주기(daily/weekly)나
    키워드/즐겨찾기 이메일 토글을 따지지 않는다 — 사용자가 지금 명시적으로 눌렀으니
    아직 이메일로 보내지 않은(emailed_at IS NULL) 내 알림을 지금 보낸다.

    다만 이미 마감된 공고의 알림은 여기서도 빼는데(_not_closed_yet), 다른 경로가 일부러
    빼둔 것을 이 버튼이 도로 쓸어 보내면 필터가 무의미해지기 때문이다.

    - SMTP_HOST가 비어있으면 EmailNotConfiguredError를 던진다(자동 파이프라인은 조용히
      건너뛰지만, 사용자 액션에서는 이유를 알려줘야 한다).
    - 보낼 알림이 없으면 발송하지 않고 0을 반환한다(오류 아님).
    - 발송에 실패하면 emailed_at을 건드리지 않고 예외를 그대로 전파한다.
    반환값: 이번에 이메일로 보낸 알림 개수.
    """
    if not settings.SMTP_HOST:
        raise EmailNotConfiguredError

    pending = db.execute(
        select(NotificationLog)
        .join(Announcement, Announcement.id == NotificationLog.announcement_id, isouter=True)
        .where(
            NotificationLog.user_id == user.id,
            NotificationLog.emailed_at.is_(None),
            _not_closed_yet(),
        )
        .order_by(NotificationLog.created_at.desc())
    ).scalars().all()
    if not pending:
        return 0

    _send_email(user.email, "[Forward] 새 알림이 있습니다", _build_email_body(pending))

    now = datetime.utcnow()
    for row in pending:
        row.emailed_at = now
    db.commit()
    return len(pending)
