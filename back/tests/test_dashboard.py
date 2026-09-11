import uuid
from datetime import date, datetime, timedelta

from app.db.models import Announcement

KST_OFFSET = timedelta(hours=9)


def _make_announcement(db, external_id, title, reception_end_offset_days=10, collected_at=None):
    kwargs = dict(
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
    if collected_at is not None:
        kwargs["collected_at"] = collected_at
    ann = Announcement(**kwargs)
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


def test_trend_requires_login(client):
    res = client.get("/api/v1/dashboard/trend")
    assert res.status_code == 401


def test_trend_no_keywords_all_zero(client, make_user):
    user = make_user()
    res = client.get("/api/v1/dashboard/trend", headers=user["headers"])
    assert res.status_code == 200
    data = res.json()["data"]
    assert len(data["months"]) == 12
    for series in data["series"]:
        assert len(series["counts"]) == 12
        assert sum(series["counts"]) == 0


def test_trend_counts_by_month_kst(client, db, make_user):
    user = make_user()
    client.post("/api/v1/keywords", json={"keyword": "AI"}, headers=user["headers"])

    curr_year = (datetime.utcnow() + KST_OFFSET).year
    prev_year = curr_year - 1

    # UTC 새벽 시각으로 저장해도 KST 변환(+9h) 후에는 같은 날짜의 오전이라 월이 안 바뀐다.
    _make_announcement(db, "ext-mar-1", "AI 지원사업 공고", collected_at=datetime(curr_year, 3, 15, 3, 0, 0))
    _make_announcement(db, "ext-mar-2", "AI 창업 공고", collected_at=datetime(curr_year, 3, 20, 3, 0, 0))
    _make_announcement(db, "ext-dec", "AI 국비지원 공고", collected_at=datetime(prev_year, 12, 5, 3, 0, 0))
    # 매칭 안 되는 공고는 집계에서 제외돼야 한다
    _make_announcement(db, "ext-none", "스마트시티 통합플랫폼", collected_at=datetime(curr_year, 3, 15, 3, 0, 0))

    res = client.get("/api/v1/dashboard/trend", headers=user["headers"])
    assert res.status_code == 200
    series_by_year = {s["year"]: s["counts"] for s in res.json()["data"]["series"]}

    assert series_by_year[curr_year][2] == 2  # 3월 (0-indexed)
    assert series_by_year[prev_year][11] == 1  # 12월
    assert sum(series_by_year[curr_year]) == 2
