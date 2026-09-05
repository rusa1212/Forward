import uuid
from datetime import date, timedelta

from app.db.models import Announcement, Keyword, NotificationLog, SavedAnnouncement
from app.services.notifier import generate_keyword_match_notifications, send_pending_notification_emails


def _make_announcement(db, external_id, title, days_to_end=10) -> str:
    ann = Announcement(
        id=str(uuid.uuid4()),
        source="kstartup",
        external_id=external_id,
        title=title,
        department="Dev",
        reception_start=date.today(),
        reception_end=date.today() + timedelta(days=days_to_end),
        status="Y",
        detail_url="http://example.com",
    )
    db.add(ann)
    db.commit()
    return ann.id


# ---- GET/PUT /me/alert-settings ----

def test_get_alert_settings_defaults_when_no_row(client, make_user):
    user = make_user()
    res = client.get("/api/v1/me/alert-settings", headers=user["headers"])
    assert res.status_code == 200, res.text
    assert res.json()["data"] == {
        "emailFrequency": "daily",
        "deadlineAlertDays": 7,
        "deadlineDashboardAlert": True,
        "deadlineEmailAlert": False,
    }


def test_put_alert_settings_persists(client, make_user):
    user = make_user()
    body = {
        "emailFrequency": "weekly",
        "deadlineAlertDays": 3,
        "deadlineDashboardAlert": False,
        "deadlineEmailAlert": True,
    }
    res = client.put("/api/v1/me/alert-settings", json=body, headers=user["headers"])
    assert res.status_code == 200, res.text
    assert res.json()["data"] == body

    res2 = client.get("/api/v1/me/alert-settings", headers=user["headers"])
    assert res2.json()["data"] == body


def test_put_alert_settings_invalid_deadline_days(client, make_user):
    user = make_user()
    body = {
        "emailFrequency": "daily",
        "deadlineAlertDays": 5,  # only 7/3/1 allowed
        "deadlineDashboardAlert": True,
        "deadlineEmailAlert": False,
    }
    res = client.put("/api/v1/me/alert-settings", json=body, headers=user["headers"])
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "VALIDATION_ERROR"


def test_put_alert_settings_invalid_frequency(client, make_user):
    user = make_user()
    body = {
        "emailFrequency": "monthly",
        "deadlineAlertDays": 7,
        "deadlineDashboardAlert": True,
        "deadlineEmailAlert": False,
    }
    res = client.put("/api/v1/me/alert-settings", json=body, headers=user["headers"])
    assert res.status_code == 422


# ---- keywords list/create include alert fields + PATCH /keywords/{id}/alerts ----

def test_keyword_create_includes_alert_defaults(client, make_user):
    user = make_user()
    res = client.post("/api/v1/keywords", json={"keyword": "AI"}, headers=user["headers"])
    assert res.status_code == 200, res.text
    data = res.json()["data"]
    assert data["dashboardAlert"] is True
    assert data["emailAlert"] is False


def test_patch_keyword_alerts(client, make_user):
    user = make_user()
    kw = client.post("/api/v1/keywords", json={"keyword": "AI"}, headers=user["headers"]).json()["data"]

    res = client.patch(
        f"/api/v1/keywords/{kw['id']}/alerts",
        json={"dashboardAlert": False, "emailAlert": True},
        headers=user["headers"],
    )
    assert res.status_code == 200, res.text
    assert res.json()["data"]["dashboardAlert"] is False
    assert res.json()["data"]["emailAlert"] is True

    listed = client.get("/api/v1/keywords", headers=user["headers"]).json()["data"]
    assert listed[0]["dashboardAlert"] is False
    assert listed[0]["emailAlert"] is True


def test_patch_keyword_alerts_of_other_user_is_404(client, make_user):
    user1 = make_user(emp_id="20230001")
    user2 = make_user(emp_id="20230002")
    kw = client.post("/api/v1/keywords", json={"keyword": "AI"}, headers=user1["headers"]).json()["data"]

    res = client.patch(
        f"/api/v1/keywords/{kw['id']}/alerts", json={"dashboardAlert": False}, headers=user2["headers"]
    )
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "KEYWORD_NOT_FOUND"


# ---- notifier.py: alert settings actually gate notification generation/emailing ----

def test_dashboard_alert_false_skips_notification_creation(db, make_user):
    user = make_user()
    kw = Keyword(id=str(uuid.uuid4()), user_id=user["userId"], keyword="AI", dashboard_alert=False)
    db.add(kw)
    db.commit()
    _make_announcement(db, "ext-1", "AI 기반 시스템")

    created = generate_keyword_match_notifications(db)
    assert created == 0

    notes = db.query(NotificationLog).filter(NotificationLog.user_id == user["userId"]).all()
    assert notes == []


def test_keyword_deadline_soon_uses_per_user_deadline_alert_days(client, db, make_user):
    user = make_user()
    # user sets D-3, global DEADLINE_SOON_DAYS(3) 이 값과 우연히 같지 않게 하기 위해 D-3로 설정
    client.put(
        "/api/v1/me/alert-settings",
        json={
            "emailFrequency": "daily",
            "deadlineAlertDays": 3,
            "deadlineDashboardAlert": True,
            "deadlineEmailAlert": False,
        },
        headers=user["headers"],
    )
    db.add(Keyword(id=str(uuid.uuid4()), user_id=user["userId"], keyword="AI"))
    db.commit()
    _make_announcement(db, "ext-1", "AI 마감임박 공고", days_to_end=2)  # within D-3

    generate_keyword_match_notifications(db)
    notes = db.query(NotificationLog).filter(NotificationLog.user_id == user["userId"]).all()
    types = {n.notify_type for n in notes}
    assert types == {"신규매칭", "마감임박"}


def test_saved_announcement_deadline_soon_creates_keywordless_notification(client, db, make_user):
    user = make_user()
    client.put(
        "/api/v1/me/alert-settings",
        json={
            "emailFrequency": "daily",
            "deadlineAlertDays": 7,
            "deadlineDashboardAlert": True,
            "deadlineEmailAlert": False,
        },
        headers=user["headers"],
    )
    ann_id = _make_announcement(db, "ext-1", "저장한 공고 마감임박", days_to_end=5)
    db.add(SavedAnnouncement(user_id=user["userId"], announcement_id=ann_id))
    db.commit()

    created = generate_keyword_match_notifications(db)
    assert created == 1

    note = db.query(NotificationLog).filter(NotificationLog.user_id == user["userId"]).one()
    assert note.notify_type == "마감임박"
    assert note.keyword_id is None


def test_saved_announcement_deadline_dashboard_alert_off_skips(client, db, make_user):
    user = make_user()
    client.put(
        "/api/v1/me/alert-settings",
        json={
            "emailFrequency": "daily",
            "deadlineAlertDays": 7,
            "deadlineDashboardAlert": False,
            "deadlineEmailAlert": False,
        },
        headers=user["headers"],
    )
    ann_id = _make_announcement(db, "ext-1", "저장한 공고 마감임박", days_to_end=5)
    db.add(SavedAnnouncement(user_id=user["userId"], announcement_id=ann_id))
    db.commit()

    created = generate_keyword_match_notifications(db)
    assert created == 0


def test_email_alert_false_never_emailed(db, make_user, monkeypatch):
    from app.core.config import settings
    from app.services import notifier

    user = make_user()
    db.add(Keyword(id=str(uuid.uuid4()), user_id=user["userId"], keyword="AI", email_alert=False))
    db.commit()
    _make_announcement(db, "ext-1", "AI 기반 시스템")
    generate_keyword_match_notifications(db)

    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(notifier, "_send_email", lambda to, subject, body: None)

    sent = send_pending_notification_emails(db)
    assert sent == 0

    note = db.query(NotificationLog).filter(NotificationLog.user_id == user["userId"]).one()
    assert note.emailed_at is None


def test_weekly_frequency_waits_until_monday(client, db, make_user, monkeypatch):
    from datetime import date as date_cls

    from app.core.config import settings
    from app.services import notifier

    user = make_user()
    client.put(
        "/api/v1/me/alert-settings",
        json={
            "emailFrequency": "weekly",
            "deadlineAlertDays": 7,
            "deadlineDashboardAlert": True,
            "deadlineEmailAlert": True,
        },
        headers=user["headers"],
    )
    ann_id = _make_announcement(db, "ext-1", "저장한 공고 마감임박", days_to_end=3)
    db.add(SavedAnnouncement(user_id=user["userId"], announcement_id=ann_id))
    db.commit()
    generate_keyword_match_notifications(db)

    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(notifier, "_send_email", lambda to, subject, body: None)

    class _NotMonday(date_cls):
        @classmethod
        def today(cls):
            return date_cls(2026, 9, 5)  # Saturday

    monkeypatch.setattr(notifier, "date", _NotMonday)
    sent = send_pending_notification_emails(db)
    assert sent == 0

    class _Monday(date_cls):
        @classmethod
        def today(cls):
            return date_cls(2026, 9, 7)  # Monday

    monkeypatch.setattr(notifier, "date", _Monday)
    sent2 = send_pending_notification_emails(db)
    assert sent2 == 1
