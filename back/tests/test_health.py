def test_health(client):
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json()["success"] is True


def test_health_db(client):
    res = client.get("/api/v1/health/db")
    assert res.status_code == 200
    assert res.json()["data"]["db"] == "connected"
