"""알림 생성 + 이메일 발송 자동화 (5주차 우선순위 P1 "알림·이메일 발송 자동화 파이프라인").

scheduler.py의 매일 06시(기본) 자동 수집 직후 이 순서로 실행됩니다:
  ① 공고 수집·저장 (scheduler.py, storage.py — 기존)
  ② 키워드 매칭으로 알림 생성 → notification_logs 적재 (generate_keyword_match_notifications)
  ③ 아직 이메일로 안 보낸 알림을 사용자별로 모아 이메일 발송 (send_pending_notification_emails)

주의:
- ②는 매일 전체를 다시 계산해도 안전합니다. notification_logs의 UNIQUE(user_id, announcement_id,
  notify_type) 제약 + INSERT IGNORE로, 이미 만들어진 알림은 자동으로 건너뜁니다.
- "마감임박" 판정 기준은 announcements.py의 DEADLINE_SOON_DAYS(현재 3일, 팀 확정 값 아님)를
  그대로 재사용합니다 — 기준이 나중에 바뀌면 그쪽만 고치면 여기도 같이 반영됩니다.
- ③(이메일 발송)은 .env에 SMTP_HOST가 설정되어 있어야 실제로 동작합니다. 아직 어떤 이메일
  서비스(SMTP 릴레이/Gmail/SendGrid 등)를 쓸지 팀 결정 전이라, 기본값(SMTP_HOST 빈 값)에서는
  실제 발송 없이 로그만 남기고 넘어갑니다 — 즉 이 상태로 배포해도 안전합니다(알림 저장까지는
  정상 동작, 이메일만 보류). SMTP 값이 채워지면 코드 수정 없이 바로 발송이 시작됩니다.
"""
import logging
import smtplib
import uuid
from datetime import datetime
from email.mime.text import MIMEText

from sqlalchemy import select
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.orm import Session

from app.api.v1.announcements import _status_label
from app.core.config import settings
from app.db.models import Announcement, Keyword, NotificationLog, User

logger = logging.getLogger("app.notifier")


def generate_keyword_match_notifications(db: Session) -> int:
    """모든 사용자의 키워드 × 공고 제목을 매칭해서 notification_logs에 알림을 쌓는다.

    - notify_type="신규매칭": 제목에 키워드가 포함된 공고
    - notify_type="마감임박": 그중 announcements.py와 동일 기준으로 마감임박 상태인 것
    반환값은 이번 호출에서 새로 생긴 알림 개수(중복 스킵분 제외).
    """
    keyword_rows = db.execute(select(Keyword.id, Keyword.user_id, Keyword.keyword)).all()
    if not keyword_rows:
        return 0

    rows_to_insert: list[dict] = []
    for keyword_id, user_id, keyword in keyword_rows:
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
            if _status_label(ann.reception_start, ann.reception_end) == "마감임박":
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

    if not rows_to_insert:
        return 0

    # 이미 있는 (user_id, announcement_id, notify_type) 조합은 INSERT IGNORE로 조용히 스킵
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
    """emailed_at이 비어있는 알림을 사용자별로 묶어 이메일 1통으로 발송, 성공하면 emailed_at 채움.

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

    by_user: dict[str, list[NotificationLog]] = {}
    for row in pending:
        by_user.setdefault(row.user_id, []).append(row)

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
