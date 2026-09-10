import uuid
from datetime import date, timedelta

from app.db.models import Announcement


def _make_announcement(db, external_id, title, reception_end_offset_days=10):
    ann = Announcement(
        id=str(uuid.uuid4()),
        source="kstartup",
        external_id=external_id,
        title=title,
        department="과기정통부",
        reception_start=date.today() - timedelta(days=1),
        reception_end=date.today() + timedelta(days=reception_end_offset_days),
        status="Y",
        detail_url="http://example.com",
    )
    db.add(ann)
    db.commit()
    return ann.id


def test_dashboard_requires_login(client):
    res = client.get("/api/v1/dashboard/summary")
    assert res.status_code == 401


def test_dashboard_counts_keyword_match(client, db, make_user):
    user = make_user()
    client.post("/api/v1/keywords", json={"keyword": "AI"}, headers=user["headers"])

    _make_announcement(db, "ext-ai", "AI 기반 시스템 개발", reception_end_offset_days=1)  # 마감임박
    _make_announcement(db, "ext-none", "스마트시티 통합플랫폼")  # 매칭 안 됨

    res = client.get("/api/v1/dashboard/summary", headers=user["headers"])
    assert res.status_code == 200
    counts = res.json()["data"]["counts"]
    assert counts["matched"] == 1
    assert counts["urgent"] == 1
