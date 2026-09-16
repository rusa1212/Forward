import uuid
from datetime import date, timedelta

import pytest

from app.core.config import settings
from app.db.models import AlertSetting, Announcement, Keyword, NotificationLog, User
from app.services import notifier
from app.services.notifier import (
    EmailNotConfiguredError,
    generate_keyword_match_notifications,
    send_notifications_to_user_now,
    send_pending_notification_emails,
)


def _make_announcement(db, external_id="ext-1", title="AI 기반 시스템 개발", days_to_end=10) -> str:
    ann = Announcement(
        id=str(uuid.uuid4()),
        source="kstartup",
        external_id=external_id,
        title=title,
        department="과기정통부",
        reception_start=date.today() - timedelta(days=1),
        reception_end=date.today() + timedelta(days=days_to_end),
        status="Y",
        detail_url="http://example.com",
    )
    db.add(ann)
    db.commit()
    return ann.id


def _add_keyword(db, user_id, keyword="AI", email_alert=True) -> str:
    # 컬럼 기본값도 True다 — 키워드를 등록하면 매칭 공고를 바로 메일로 받는 게 기본 동작이라
    # (POST /keywords가 등록 직후 발송까지 한다). 끄는 경우를 보려면 email_alert=False로 넘긴다.
    kw = Keyword(id=str(uuid.uuid4()), user_id=user_id, keyword=keyword, email_alert=email_alert)
    db.add(kw)
    db.commit()
    return kw.id


# ---- notifier service (pipeline step 2: generate) ----

def test_generate_keyword_match_notifications_creates_row(db, make_user):
    user = make_user()
    _add_keyword(db, user["userId"], "AI")
    _make_announcement(db, title="AI 기반 시스템 개발", days_to_end=10)

    created = generate_keyword_match_notifications(db)
    assert created == 1

    rows = db.query(NotificationLog).filter(NotificationLog.user_id == user["userId"]).all()
    assert len(rows) == 1
    assert rows[0].notify_type == "신규매칭"
    assert "AI 기반 시스템 개발" in rows[0].title


def test_generate_deadline_soon_creates_two_notifications(db, make_user):
    user = make_user()
    _add_keyword(db, user["userId"], "AI")
    _make_announcement(db, title="AI 마감임박 공고", days_to_end=1)

    created = generate_keyword_match_notifications(db)
    assert created == 2

    types = {
        row.notify_type
        for row in db.query(NotificationLog).filter(NotificationLog.user_id == user["userId"]).all()
    }
    assert types == {"신규매칭", "마감임박"}


def test_generate_is_idempotent_on_rerun(db, make_user):
    user = make_user()
    _add_keyword(db, user["userId"], "AI")
    _make_announcement(db, title="AI 기반 시스템 개발", days_to_end=10)

    first = generate_keyword_match_notifications(db)
    second = generate_keyword_match_notifications(db)
    assert first == 1
    assert second == 0  # UNIQUE + INSERT IGNORE dedupe

    rows = db.query(NotificationLog).filter(NotificationLog.user_id == user["userId"]).all()
    assert len(rows) == 1


def test_generate_no_match_no_keywords(db, make_user):
    make_user()
    created = generate_keyword_match_notifications(db)
    assert created == 0


# ---- notifier service (pipeline step 3: email) ----
# 로컬 .env에 SMTP_HOST가 채워져 있을 수 있으므로 "SMTP 미설정" 테스트는 명시적으로 비운다.

def test_send_pending_emails_noop_without_smtp_host(db, make_user, monkeypatch):
    monkeypatch.setattr(settings, "SMTP_HOST", "")
    user = make_user()
    _add_keyword(db, user["userId"], "AI")
    _make_announcement(db, title="AI 기반 시스템 개발")
    generate_keyword_match_notifications(db)

    sent = send_pending_notification_emails(db)
    assert sent == 0  # SMTP_HOST 비어있음 -> 발송 건너뜀, 크래시 없음

    rows = db.query(NotificationLog).filter(NotificationLog.user_id == user["userId"]).all()
    assert all(row.emailed_at is None for row in rows)  # nothing marked as emailed


def test_send_pending_emails_success_marks_emailed_at(db, make_user, monkeypatch):
    user = make_user(email="notify-me@test.com")
    _add_keyword(db, user["userId"], "AI")
    _make_announcement(db, title="AI 기반 시스템 개발")
    generate_keyword_match_notifications(db)

    sent_messages = []
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(notifier, "_send_email", lambda to, subject, body: sent_messages.append((to, subject, body)))

    sent = send_pending_notification_emails(db)
    assert sent == 1
    assert sent_messages[0][0] == "notify-me@test.com"

    rows = db.query(NotificationLog).filter(NotificationLog.user_id == user["userId"]).all()
    assert all(row.emailed_at is not None for row in rows)

    # re-running should find nothing pending (already emailed)
    sent_again = send_pending_notification_emails(db)
    assert sent_again == 0
    assert len(sent_messages) == 1


def test_send_pending_emails_failure_for_one_user_does_not_block_others(db, make_user, monkeypatch):
    good_user = make_user(emp_id="20230001", email="good@test.com")
    bad_user = make_user(emp_id="20230002", email="bad@test.com")
    _add_keyword(db, good_user["userId"], "AI")
    _add_keyword(db, bad_user["userId"], "AI")
    _make_announcement(db, title="AI 기반 시스템 개발")
    generate_keyword_match_notifications(db)

    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.com")

    def fake_send(to, subject, body):
        if to == "bad@test.com":
            raise RuntimeError("smtp failure")

    monkeypatch.setattr(notifier, "_send_email", fake_send)

    sent = send_pending_notification_emails(db)
    assert sent == 1  # only the good user's notification counted

    good_row = db.query(NotificationLog).filter(NotificationLog.user_id == good_user["userId"]).one()
    bad_row = db.query(NotificationLog).filter(NotificationLog.user_id == bad_user["userId"]).one()
    assert good_row.emailed_at is not None
    assert bad_row.emailed_at is None  # left pending so a future run retries it


# ---- notifier service: "지금 이메일로 받기" (send_notifications_to_user_now) ----

def test_send_now_raises_without_smtp_host(db, make_user, monkeypatch):
    monkeypatch.setattr(settings, "SMTP_HOST", "")
    user_row = db.get(User, make_user()["userId"])
    with pytest.raises(EmailNotConfiguredError):
        send_notifications_to_user_now(db, user_row)


def test_send_now_returns_zero_when_nothing_pending(db, make_user, monkeypatch):
    user_row = db.get(User, make_user()["userId"])
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.com")

    def _fail(*a, **k):
        raise AssertionError("should not send")

    monkeypatch.setattr(notifier, "_send_email", _fail)

    assert send_notifications_to_user_now(db, user_row) == 0


def test_send_now_sends_pending_ignoring_toggles_and_frequency(db, make_user, monkeypatch):
    user = make_user(email="now@test.com")
    user_row = db.get(User, user["userId"])
    # email_alert=False on the keyword + weekly frequency — auto pipeline would skip these,
    # but the explicit "send now" button must send them anyway.
    _add_keyword(db, user["userId"], "AI", email_alert=False)
    _make_announcement(db, title="AI 마감임박 공고", days_to_end=1)
    generate_keyword_match_notifications(db)
    db.add(AlertSetting(user_id=user["userId"], email_frequency="weekly", deadline_email_alert=False))
    db.commit()

    sent_messages = []
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(notifier, "_send_email", lambda to, subject, body: sent_messages.append((to, subject, body)))

    sent = send_notifications_to_user_now(db, user_row)
    assert sent == 2  # 신규매칭 + 마감임박
    assert sent_messages[0][0] == "now@test.com"

    rows = db.query(NotificationLog).filter(NotificationLog.user_id == user["userId"]).all()
    assert all(row.emailed_at is not None for row in rows)

    # nothing pending on a second call
    assert send_notifications_to_user_now(db, user_row) == 0
    assert len(sent_messages) == 1


def test_send_now_does_not_mark_emailed_on_failure(db, make_user, monkeypatch):
    user = make_user()
    user_row = db.get(User, user["userId"])
    _add_keyword(db, user["userId"], "AI", email_alert=False)
    _make_announcement(db, title="AI 기반 시스템 개발")
    generate_keyword_match_notifications(db)

    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.com")

    def boom(*a, **k):
        raise RuntimeError("smtp down")

    monkeypatch.setattr(notifier, "_send_email", boom)

    try:
        send_notifications_to_user_now(db, user_row)
        assert False, "exception expected"
    except RuntimeError:
        pass

    rows = db.query(NotificationLog).filter(NotificationLog.user_id == user["userId"]).all()
    assert all(row.emailed_at is None for row in rows)


# ---- notification-email API (POST /me/notification-email) ----

def test_send_my_notification_email_not_configured(client, make_user, monkeypatch):
    monkeypatch.setattr(settings, "SMTP_HOST", "")
    user = make_user()
    res = client.post("/api/v1/me/notification-email", headers=user["headers"])
    assert res.status_code == 503
    assert res.json()["error"]["code"] == "EMAIL_NOT_CONFIGURED"


def test_send_my_notification_email_nothing_pending(client, make_user, monkeypatch):
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.com")
    user = make_user()
    res = client.post("/api/v1/me/notification-email", headers=user["headers"])
    assert res.status_code == 200, res.text
    assert res.json()["data"] == {"sent": 0, "message": "새로 보낼 알림이 없습니다."}


def test_send_my_notification_email_success(client, db, make_user, monkeypatch):
    user = make_user(email="me-now@test.com")
    _add_keyword(db, user["userId"], "AI", email_alert=False)
    _make_announcement(db, title="AI 기반 시스템 개발")
    generate_keyword_match_notifications(db)

    sent_messages = []
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(notifier, "_send_email", lambda to, subject, body: sent_messages.append(to))

    res = client.post("/api/v1/me/notification-email", headers=user["headers"])
    assert res.status_code == 200, res.text
    data = res.json()["data"]
    assert data["sent"] == 1
    assert data["sentTo"] == "me-now@test.com"
    assert sent_messages == ["me-now@test.com"]


def test_send_my_notification_email_requires_auth(client):
    res = client.post("/api/v1/me/notification-email")
    assert res.status_code in (401, 403)


# ---- notifications API (list / read / read-all) ----

def test_list_notifications_empty(client, make_user):
    user = make_user()
    res = client.get("/api/v1/notifications", headers=user["headers"])
    assert res.status_code == 200, res.text
    assert res.json()["data"] == {"unreadCount": 0, "notifications": []}


def test_list_notifications_after_generate(client, db, make_user):
    user = make_user()
    _add_keyword(db, user["userId"], "AI")
    _make_announcement(db, title="AI 기반 시스템 개발")
    generate_keyword_match_notifications(db)

    res = client.get("/api/v1/notifications", headers=user["headers"])
    assert res.status_code == 200, res.text
    data = res.json()["data"]
    assert data["unreadCount"] == 1
    assert len(data["notifications"]) == 1
    note = data["notifications"][0]
    assert note["keyword"] == "AI"
    assert note["isRead"] is False


def test_list_notifications_only_own(client, db, make_user):
    user1 = make_user(emp_id="20230001")
    user2 = make_user(emp_id="20230002")
    _add_keyword(db, user1["userId"], "AI")
    _make_announcement(db, title="AI 기반 시스템 개발")
    generate_keyword_match_notifications(db)

    res = client.get("/api/v1/notifications", headers=user2["headers"])
    assert res.json()["data"] == {"unreadCount": 0, "notifications": []}


def test_mark_notification_read(client, db, make_user):
    user = make_user()
    _add_keyword(db, user["userId"], "AI")
    _make_announcement(db, title="AI 기반 시스템 개발")
    generate_keyword_match_notifications(db)

    note_id = db.query(NotificationLog).filter(NotificationLog.user_id == user["userId"]).one().id
    res = client.post(f"/api/v1/notifications/{note_id}/read", headers=user["headers"])
    assert res.status_code == 200, res.text

    list_res = client.get("/api/v1/notifications", headers=user["headers"])
    assert list_res.json()["data"]["unreadCount"] == 0
    assert list_res.json()["data"]["notifications"][0]["isRead"] is True


def test_mark_notification_read_not_found(client, make_user):
    user = make_user()
    res = client.post(f"/api/v1/notifications/{uuid.uuid4()}/read", headers=user["headers"])
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "NOTIFICATION_NOT_FOUND"


def test_mark_notification_read_malformed_id(client, make_user):
    user = make_user()
    res = client.post("/api/v1/notifications/not-a-uuid/read", headers=user["headers"])
    assert res.status_code == 404


def test_mark_notification_read_of_other_user_is_404(client, db, make_user):
    user1 = make_user(emp_id="20230001")
    user2 = make_user(emp_id="20230002")
    _add_keyword(db, user1["userId"], "AI")
    _make_announcement(db, title="AI 기반 시스템 개발")
    generate_keyword_match_notifications(db)

    note_id = db.query(NotificationLog).filter(NotificationLog.user_id == user1["userId"]).one().id
    res = client.post(f"/api/v1/notifications/{note_id}/read", headers=user2["headers"])
    assert res.status_code == 404


def test_mark_all_notifications_read(client, db, make_user):
    user = make_user()
    _add_keyword(db, user["userId"], "AI")
    _make_announcement(db, title="AI 마감임박 공고", days_to_end=1)  # 2 notifications
    generate_keyword_match_notifications(db)

    res = client.post("/api/v1/notifications/read-all", headers=user["headers"])
    assert res.status_code == 200, res.text
    assert res.json()["data"]["count"] == 2

    list_res = client.get("/api/v1/notifications", headers=user["headers"])
    assert list_res.json()["data"]["unreadCount"] == 0


class _FakeSmtpConn:
    """smtplib.SMTP/SMTP_SSL 대역 — 실제로 접속하지 않고 호출 내역만 기록한다."""
    last_instance: "_FakeSmtpConn | None" = None

    def __init__(self, host, port, timeout=None):
        self.host, self.port = host, port
        self.starttls_called = False
        self.login_args = None
        self.sent_message = None
        _FakeSmtpConn.last_instance = self

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def starttls(self):
        self.starttls_called = True

    def login(self, username, password):
        self.login_args = (username, password)

    def send_message(self, msg):
        self.sent_message = msg


def _fail_if_used(*a, **k):
    raise AssertionError("이 SMTP 클래스는 이 포트에서 쓰이면 안 된다")


def test_send_email_starttls_on_587(monkeypatch):
    """587(또는 그 외 포트) + SMTP_USE_TLS=True → 평문 연결 후 STARTTLS로 승격."""
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(settings, "SMTP_PORT", 587)
    monkeypatch.setattr(settings, "SMTP_USE_TLS", True)
    monkeypatch.setattr(settings, "SMTP_USERNAME", "user@example.com")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "pw")
    monkeypatch.setattr(settings, "SMTP_FROM_EMAIL", "")
    monkeypatch.setattr(notifier.smtplib, "SMTP", _FakeSmtpConn)
    monkeypatch.setattr(notifier.smtplib, "SMTP_SSL", _fail_if_used)

    notifier._send_email("to@example.com", "제목", "본문")

    inst = _FakeSmtpConn.last_instance
    assert inst.port == 587
    assert inst.starttls_called is True
    assert inst.login_args == ("user@example.com", "pw")
    assert inst.sent_message["To"] == "to@example.com"


def test_send_email_implicit_ssl_on_465(monkeypatch):
    """465 → SMTP_SSL로 처음부터 암호화 연결, STARTTLS는 호출하지 않는다.

    회사 SMTP 릴레이(예: 비즈메카 등)가 465/SSL만 지원하는 경우를 대비한 것 —
    back/.env의 SMTP_PORT만 465로 맞추면 코드 수정 없이 동작해야 한다.
    """
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(settings, "SMTP_PORT", 465)
    monkeypatch.setattr(settings, "SMTP_USE_TLS", True)
    monkeypatch.setattr(settings, "SMTP_USERNAME", "user@example.com")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "pw")
    monkeypatch.setattr(settings, "SMTP_FROM_EMAIL", "")
    monkeypatch.setattr(notifier.smtplib, "SMTP", _fail_if_used)
    monkeypatch.setattr(notifier.smtplib, "SMTP_SSL", _FakeSmtpConn)

    notifier._send_email("to@example.com", "제목", "본문")

    inst = _FakeSmtpConn.last_instance
    assert inst.port == 465
    assert inst.starttls_called is False
    assert inst.login_args == ("user@example.com", "pw")


# ---- 키워드 등록 즉시 알림 + 발송 (notify_new_keyword_matches) ----

def test_new_keyword_emails_only_open_announcements(db, make_user, monkeypatch):
    """등록 즉시 나가는 메일에는 아직 마감되지 않은 공고만 담는다.

    매칭의 상당수가 이미 지나간 공고라 전부 보내면 지금 지원할 수 있는 공고가 묻힌다.
    마감된 공고도 알림(notification_logs)으로는 쌓여서 화면에서는 볼 수 있어야 한다."""
    user = make_user(email="new-kw@test.com")
    _make_announcement(db, external_id="open-1", title="AI 기반 시스템 개발", days_to_end=10)
    _make_announcement(db, external_id="closed-1", title="AI 창업 지원사업", days_to_end=-5)

    sent_messages = []
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(
        notifier, "_send_email", lambda to, subject, body: sent_messages.append((to, subject, body))
    )

    keyword_id = _add_keyword(db, user["userId"], "AI")
    sent = notifier.notify_new_keyword_matches(db, db.get(Keyword, keyword_id))

    assert sent == 1
    assert len(sent_messages) == 1  # 여러 건이어도 메일은 한 통으로 묶인다
    to, subject, body = sent_messages[0]
    assert to == "new-kw@test.com"
    assert "AI" in subject
    assert "AI 기반 시스템 개발" in body
    assert "AI 창업 지원사업" not in body  # 마감된 공고는 메일에서 빠진다

    rows = db.query(NotificationLog).filter(NotificationLog.user_id == user["userId"]).all()
    assert len(rows) == 2  # 마감 공고도 알림으로는 쌓인다
    assert sum(row.emailed_at is not None for row in rows) == 1


def test_new_keyword_does_not_email_when_email_alert_off(db, make_user, monkeypatch):
    """키워드의 이메일 토글이 꺼져 있으면 알림만 쌓고 메일은 보내지 않는다."""
    user = make_user()
    _make_announcement(db, title="AI 기반 시스템 개발")

    sent_messages = []
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(notifier, "_send_email", lambda *args: sent_messages.append(args))

    keyword_id = _add_keyword(db, user["userId"], "AI", email_alert=False)
    sent = notifier.notify_new_keyword_matches(db, db.get(Keyword, keyword_id))

    assert sent == 0
    assert sent_messages == []
    assert db.query(NotificationLog).filter(NotificationLog.user_id == user["userId"]).count() == 1


def test_create_keyword_api_sends_email_right_after_response(client, db, make_user, monkeypatch):
    """POST /keywords 가 응답 후 BackgroundTasks로 알림 생성 + 발송까지 이어간다."""
    user = make_user(email="api-kw@test.com")
    _make_announcement(db, title="AI 기반 시스템 개발")

    sent_messages = []
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(
        notifier, "_send_email", lambda to, subject, body: sent_messages.append((to, subject, body))
    )

    res = client.post("/api/v1/keywords", json={"keyword": "AI"}, headers=user["headers"])
    assert res.status_code == 200
    assert res.json()["data"]["emailAlert"] is True  # 새 키워드는 이메일 알림이 기본 on

    assert len(sent_messages) == 1
    assert sent_messages[0][0] == "api-kw@test.com"

    # 백그라운드 작업은 별도 세션에서 커밋한다. MySQL 기본 격리수준(REPEATABLE READ)에서는
    # 이 세션이 이미 연 트랜잭션의 스냅샷에 그 커밋이 안 보이므로, rollback으로 끊고 새로 읽는다.
    db.rollback()
    rows = db.query(NotificationLog).filter(NotificationLog.user_id == user["userId"]).all()
    assert len(rows) == 1
    assert rows[0].emailed_at is not None


def test_create_keyword_survives_email_failure(client, db, make_user, monkeypatch):
    """메일 서버가 죽어 있어도 키워드 등록 자체는 성공해야 한다 (등록은 이미 커밋됐다)."""
    user = make_user()
    _make_announcement(db, title="AI 기반 시스템 개발")

    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.com")

    def boom(to, subject, body):
        raise RuntimeError("smtp down")

    monkeypatch.setattr(notifier, "_send_email", boom)

    res = client.post("/api/v1/keywords", json={"keyword": "AI"}, headers=user["headers"])
    assert res.status_code == 200

    listed = client.get("/api/v1/keywords", headers=user["headers"])
    assert [row["keyword"] for row in listed.json()["data"]] == ["AI"]

    # 백그라운드 작업은 별도 세션에서 커밋한다. MySQL 기본 격리수준(REPEATABLE READ)에서는
    # 이 세션이 이미 연 트랜잭션의 스냅샷에 그 커밋이 안 보이므로, rollback으로 끊고 새로 읽는다.
    db.rollback()
    rows = db.query(NotificationLog).filter(NotificationLog.user_id == user["userId"]).all()
    assert len(rows) == 1
    assert rows[0].emailed_at is None  # 발송 실패분은 pending으로 남아 다음 기회에 재시도된다


def test_withheld_closed_notifications_are_not_swept_by_other_send_paths(db, make_user, monkeypatch):
    """등록 즉시 발송이 뺀 "마감된 공고" 알림이 다른 발송 경로로 다시 나가면 안 된다.

    실제로 그런 일이 있었다 — 등록 직후 메일(마감 안 된 것만)이 나간 30초 뒤에
    "지금 이메일로 받기"를 누르자, 일부러 뺐던 마감 공고 271건이 두 번째 메일로 그대로
    나갔다. 세 발송 경로가 같은 기준(_not_closed_yet)을 써야 한다."""
    user = make_user(email="sweep@test.com")
    _make_announcement(db, external_id="open-1", title="AI 기반 시스템 개발", days_to_end=10)
    _make_announcement(db, external_id="closed-1", title="AI 창업 지원사업", days_to_end=-5)

    sent_messages = []
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(
        notifier, "_send_email", lambda to, subject, body: sent_messages.append((to, subject, body))
    )

    keyword_id = _add_keyword(db, user["userId"], "AI")
    assert notifier.notify_new_keyword_matches(db, db.get(Keyword, keyword_id)) == 1

    user_row = db.get(User, user["userId"])
    # 두 경로 모두 마감 공고를 다시 집어가면 안 된다
    assert send_notifications_to_user_now(db, user_row) == 0
    assert send_pending_notification_emails(db) == 0
    assert len(sent_messages) == 1  # 등록 직후 한 통이 전부

    closed_rows = [
        row
        for row in db.query(NotificationLog).filter(NotificationLog.user_id == user["userId"]).all()
        if "창업" in row.title
    ]
    assert len(closed_rows) == 1
    assert closed_rows[0].emailed_at is None  # 미발송으로 남되, 메일로는 나가지 않는다
