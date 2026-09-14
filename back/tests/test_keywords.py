import uuid

from app.db.models import Announcement


def _make_announcement(db, external_id, title) -> str:
    ann = Announcement(
        id=str(uuid.uuid4()),
        source="kstartup",
        external_id=external_id,
        title=title,
        department="과기정통부",
        status="Y",
    )
    db.add(ann)
    db.commit()
    return ann.id


def test_keyword_match_count_reflects_matching_announcements(client, db, make_user):
    user = make_user()
    client.post("/api/v1/keywords", json={"keyword": "AI"}, headers=user["headers"])
    _make_announcement(db, "ext-1", "AI 기반 시스템 개발")
    _make_announcement(db, "ext-2", "AI 창업 지원")
    _make_announcement(db, "ext-3", "스마트시티 통합플랫폼")  # 매칭 안 됨

    res = client.get("/api/v1/keywords", headers=user["headers"])
    assert res.status_code == 200
    assert res.json()["data"][0]["matchCount"] == 2


def test_create_and_list_keyword(client, make_user):
    user = make_user()
    res = client.post("/api/v1/keywords", json={"keyword": "AI"}, headers=user["headers"])
    assert res.status_code == 200
    assert res.json()["data"]["keyword"] == "AI"

    res2 = client.get("/api/v1/keywords", headers=user["headers"])
    assert res2.status_code == 200
    keywords = [row["keyword"] for row in res2.json()["data"]]
    assert keywords == ["AI"]


def test_create_duplicate_keyword(client, make_user):
    user = make_user()
    client.post("/api/v1/keywords", json={"keyword": "AI"}, headers=user["headers"])
    res = client.post("/api/v1/keywords", json={"keyword": "AI"}, headers=user["headers"])
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "DUPLICATE_KEYWORD"


def test_delete_keyword(client, make_user):
    user = make_user()
    created = client.post("/api/v1/keywords", json={"keyword": "AI"}, headers=user["headers"]).json()
    keyword_id = created["data"]["id"]

    res = client.delete(f"/api/v1/keywords/{keyword_id}", headers=user["headers"])
    assert res.status_code == 200

    res2 = client.get("/api/v1/keywords", headers=user["headers"])
    assert res2.json()["data"] == []


def test_delete_nonexistent_keyword(client, make_user):
    user = make_user()
    fake_id = "00000000-0000-0000-0000-000000000000"
    res = client.delete(f"/api/v1/keywords/{fake_id}", headers=user["headers"])
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "KEYWORD_NOT_FOUND"


def test_cannot_delete_other_users_keyword(client, make_user):
    """RLS가 없는 MySQL 전환 후 가장 중요한 보안 케이스 — user_id 필터 누락 회귀 방지."""
    user1 = make_user(emp_id="20230001", email="u1@test.com")
    user2 = make_user(emp_id="20230002", email="u2@test.com")

    created = client.post("/api/v1/keywords", json={"keyword": "AI"}, headers=user1["headers"]).json()
    keyword_id = created["data"]["id"]

    res = client.delete(f"/api/v1/keywords/{keyword_id}", headers=user2["headers"])
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "KEYWORD_NOT_FOUND"

    # user1은 여전히 자기 키워드를 갖고 있어야 함 (삭제 안 됐는지 확인)
    res2 = client.get("/api/v1/keywords", headers=user1["headers"])
    assert len(res2.json()["data"]) == 1
