import uuid
from datetime import date, datetime, timedelta

from app.db.models import Announcement


def _make_announcement(db, external_id, title="AI 기반 시스템 개발", collected_at=None) -> str:
    kwargs = dict(
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
    if collected_at is not None:
        kwargs["collected_at"] = collected_at
    ann = Announcement(**kwargs)
    db.add(ann)
    db.commit()
    return ann.id


def test_collected_today_filters_to_today_kst_only(client, db):
    today_id = _make_announcement(db, "ext-today", collected_at=datetime.utcnow())
    yesterday_id = _make_announcement(db, "ext-yesterday", collected_at=datetime.utcnow() - timedelta(days=2))

    res = client.get("/api/v1/announcements?collectedToday=true&page_size=100")
    assert res.status_code == 200
    ids = {row["id"] for row in res.json()["data"]}
    assert today_id in ids
    assert yesterday_id not in ids


def test_collected_today_false_by_default(client, db):
    _make_announcement(db, "ext-old", collected_at=datetime.utcnow() - timedelta(days=30))

    res = client.get("/api/v1/announcements?page_size=100")
    assert res.status_code == 200
    assert res.json()["meta"]["total"] >= 1
