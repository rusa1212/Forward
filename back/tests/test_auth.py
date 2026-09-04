from app.db.models import Employee


def _seed_employee(db, emp_id="20230001", name="김민준"):
    db.add(Employee(emp_id=emp_id, name=name, department="개발팀"))
    db.commit()


def test_verify_employee_success(client, db):
    _seed_employee(db)
    res = client.post("/api/v1/auth/verify-employee", json={"empId": "20230001", "name": "김민준"})
    assert res.status_code == 200
    assert res.json()["data"]["verified"] is True


def test_verify_employee_mismatch(client, db):
    _seed_employee(db)
    res = client.post("/api/v1/auth/verify-employee", json={"empId": "20230001", "name": "다른사람"})
    assert res.status_code == 200
    assert res.json()["data"]["verified"] is False


def test_signup_success(client, db):
    _seed_employee(db)
    res = client.post(
        "/api/v1/auth/signup",
        json={"empId": "20230001", "name": "김민준", "email": "a@test.com", "pw": "password1"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert body["data"]["empId"] == "20230001"


def test_signup_employee_not_found(client, db):
    res = client.post(
        "/api/v1/auth/signup",
        json={"empId": "00000000", "name": "없는사람", "email": "x@test.com", "pw": "password1"},
    )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "EMPLOYEE_NOT_FOUND"


def test_signup_duplicate_emp_id(client, db):
    _seed_employee(db)
    client.post(
        "/api/v1/auth/signup",
        json={"empId": "20230001", "name": "김민준", "email": "a@test.com", "pw": "password1"},
    )
    res = client.post(
        "/api/v1/auth/signup",
        json={"empId": "20230001", "name": "김민준", "email": "b@test.com", "pw": "password1"},
    )
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "DUPLICATE_EMP_ID"


def test_signup_duplicate_email(client, db):
    _seed_employee(db, emp_id="20230001", name="김민준")
    _seed_employee(db, emp_id="20230002", name="이서연")
    client.post(
        "/api/v1/auth/signup",
        json={"empId": "20230001", "name": "김민준", "email": "same@test.com", "pw": "password1"},
    )
    res = client.post(
        "/api/v1/auth/signup",
        json={"empId": "20230002", "name": "이서연", "email": "same@test.com", "pw": "password2"},
    )
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "DUPLICATE_EMAIL"


def test_login_success(client, make_user):
    user = make_user()
    assert user["token"]


def test_login_wrong_password(client, db):
    _seed_employee(db)
    client.post(
        "/api/v1/auth/signup",
        json={"empId": "20230001", "name": "김민준", "email": "a@test.com", "pw": "password1"},
    )
    res = client.post("/api/v1/auth/login", json={"empId": "20230001", "pw": "wrongpw"})
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_login_unknown_emp_id(client):
    res = client.post("/api/v1/auth/login", json={"empId": "99999999", "pw": "whatever"})
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_protected_endpoint_without_token(client):
    res = client.get("/api/v1/keywords")
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "UNAUTHORIZED"


def test_protected_endpoint_invalid_token(client):
    res = client.get("/api/v1/keywords", headers={"Authorization": "Bearer not-a-real-token"})
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "INVALID_TOKEN"


def test_protected_endpoint_with_valid_token(client, make_user):
    user = make_user()
    res = client.get("/api/v1/keywords", headers=user["headers"])
    assert res.status_code == 200
