import uuid
from datetime import date, timedelta

from app.db.models import Announcement


def _make_announcement(db, external_id="ext-1", title="AI 기반 시스템 개발") -> str:
    ann = Announcement(
        id=str(uuid.uuid4()),
        source="kstartup",
        external_id=external_id,
        title=title,
        department="과기정통부",
        reception_start=date.today() - timedelta(days=1),
        reception_end=date.today() + timedelta(days=10),
        status="Y",
        detail_url="http://example.com",
    )
    db.add(ann)
    db.commit()
    return ann.id


def test_save_and_list(client, db, make_user):
    user = make_user()
    ann_id = _make_announcement(db)

    res = client.post("/api/v1/saved-announcements", json={"announcementId": ann_id}, headers=user["headers"])
    assert res.status_code == 200
    assert res.json()["data"]["announcement"]["id"] == ann_id

    res2 = client.get("/api/v1/saved-announcements", headers=user["headers"])
    assert res2.status_code == 200
    assert len(res2.json()["data"]) == 1


def test_save_duplicate(client, db, make_user):
    user = make_user()
    ann_id = _make_announcement(db)
    client.post("/api/v1/saved-announcements", json={"announcementId": ann_id}, headers=user["headers"])
    res = client.post("/api/v1/saved-announcements", json={"announcementId": ann_id}, headers=user["headers"])
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "ALREADY_SAVED"


def test_save_nonexistent_announcement(client, make_user):
    user = make_user()
    fake_id = str(uuid.uuid4())
    res = client.post("/api/v1/saved-announcements", json={"announcementId": fake_id}, headers=user["headers"])
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "ANNOUNCEMENT_NOT_FOUND"


def test_unsave(client, db, make_user):
    user = make_user()
    ann_id = _make_announcement(db)
    client.post("/api/v1/saved-announcements", json={"announcementId": ann_id}, headers=user["headers"])

    res = client.delete(f"/api/v1/saved-announcements/{ann_id}", headers=user["headers"])
    assert res.status_code == 200

    res2 = client.get("/api/v1/saved-announcements", headers=user["headers"])
    assert res2.json()["data"] == []


def test_unsave_not_saved(client, db, make_user):
    user = make_user()
    ann_id = _make_announcement(db)
    res = client.delete(f"/api/v1/saved-announcements/{ann_id}", headers=user["headers"])
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "SAVED_ANNOUNCEMENT_NOT_FOUND"
