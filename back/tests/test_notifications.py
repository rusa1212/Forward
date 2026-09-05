import uuid
from datetime import date, timedelta

from app.core.config import settings
from app.db.models import Announcement, Keyword, NotificationLog
from app.services import notifier
from app.services.notifier import (
    generate_keyword_match_notifications,
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


def _add_keyword(db, user_id, keyword="AI") -> str:
    kw = Keyword(id=str(uuid.uuid4()), user_id=user_id, keyword=keyword)
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


# ---- notifier service (pipeline step 3: email, SMTP_HOST unset by default) ----

def test_send_pending_emails_noop_without_smtp_host(db, make_user):
    user = make_user()
    _add_keyword(db, user["userId"], "AI")
    _make_announcement(db, title="AI 기반 시스템 개발")
    generate_keyword_match_notifications(db)

    sent = send_pending_notification_emails(db)
    assert sent == 0  # settings.SMTP_HOST is empty by default -> emails skipped, no crash

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
