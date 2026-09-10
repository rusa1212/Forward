from app.db.models import User


def test_get_me(client, make_user):
    user = make_user(email="me1@test.com")
    res = client.get("/api/v1/me", headers=user["headers"])
    assert res.status_code == 200, res.text
    data = res.json()["data"]
    assert data["empId"] == user["empId"]
    assert data["email"] == "me1@test.com"
    assert data["name"] == "김민준"
    assert data["department"] == "개발팀"


def test_get_me_requires_auth(client):
    res = client.get("/api/v1/me")
    assert res.status_code in (401, 403)


def test_update_email(client, db, make_user):
    user = make_user(email="old@test.com")
    res = client.patch("/api/v1/me", json={"email": "new@test.com"}, headers=user["headers"])
    assert res.status_code == 200, res.text
    assert res.json()["data"]["email"] == "new@test.com"

    updated = db.get(User, user["userId"])
    assert updated.email == "new@test.com"


def test_update_email_duplicate(client, make_user):
    make_user(emp_id="20230001", email="taken@test.com")
    user2 = make_user(emp_id="20230002", email="user2@test.com")

    res = client.patch("/api/v1/me", json={"email": "taken@test.com"}, headers=user2["headers"])
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "DUPLICATE_EMAIL"


def test_update_email_same_value_ok(client, make_user):
    user = make_user(email="same@test.com")
    res = client.patch("/api/v1/me", json={"email": "same@test.com"}, headers=user["headers"])
    assert res.status_code == 200
    assert res.json()["data"]["email"] == "same@test.com"


def test_update_email_invalid_format(client, make_user):
    user = make_user()
    res = client.patch("/api/v1/me", json={"email": "not-an-email"}, headers=user["headers"])
    assert res.status_code == 422


def test_change_password_success(client, make_user):
    user = make_user(pw="password1")
    res = client.post(
        "/api/v1/me/change-password",
        json={"currentPw": "password1", "newPw": "newpassword1"},
        headers=user["headers"],
    )
    assert res.status_code == 200, res.text

    relogin_old = client.post("/api/v1/auth/login", json={"empId": user["empId"], "pw": "password1"})
    assert relogin_old.status_code != 200

    relogin_new = client.post("/api/v1/auth/login", json={"empId": user["empId"], "pw": "newpassword1"})
    assert relogin_new.status_code == 200


def test_change_password_wrong_current(client, make_user):
    user = make_user(pw="password1")
    res = client.post(
        "/api/v1/me/change-password",
        json={"currentPw": "wrongpw", "newPw": "newpassword1"},
        headers=user["headers"],
    )
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_change_password_too_short(client, make_user):
    user = make_user(pw="password1")
    res = client.post(
        "/api/v1/me/change-password",
        json={"currentPw": "password1", "newPw": "abc"},
        headers=user["headers"],
    )
    assert res.status_code == 422
