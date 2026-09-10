def test_admin_endpoint_without_token(client):
    res = client.get("/api/v1/admin/employees")
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "UNAUTHORIZED"


def test_admin_endpoint_non_admin_forbidden(client, make_user):
    user = make_user()
    res = client.get("/api/v1/admin/employees", headers=user["headers"])
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "FORBIDDEN"


def test_admin_can_list_employees(client, make_user):
    admin = make_user(is_admin=True)
    res = client.get("/api/v1/admin/employees", headers=admin["headers"])
    assert res.status_code == 200
    # make_user()가 만든 자기 자신의 사원 정보가 joined=True로 보여야 함
    rows = res.json()["data"]
    assert any(row["empId"] == admin["empId"] and row["joined"] is True for row in rows)


def test_admin_create_employee(client, make_user):
    admin = make_user(is_admin=True)
    res = client.post(
        "/api/v1/admin/employees",
        json={"empId": "20239999", "name": "홍길동", "department": "개발팀"},
        headers=admin["headers"],
    )
    assert res.status_code == 200
    assert res.json()["data"]["joined"] is False


def test_admin_create_duplicate_employee(client, make_user):
    admin = make_user(is_admin=True)
    res = client.post(
        "/api/v1/admin/employees",
        json={"empId": admin["empId"], "name": "김민준"},
        headers=admin["headers"],
    )
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "DUPLICATE_EMP_ID"


def test_admin_delete_joined_employee_blocked(client, make_user):
    admin = make_user(is_admin=True)
    # admin 본인이 이미 가입한 사원이므로 삭제 시도하면 막혀야 함
    res = client.delete(f"/api/v1/admin/employees/{admin['empId']}", headers=admin["headers"])
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "EMPLOYEE_ALREADY_JOINED"


def test_admin_delete_unjoined_employee(client, make_user):
    admin = make_user(is_admin=True)
    client.post(
        "/api/v1/admin/employees",
        json={"empId": "20239999", "name": "홍길동"},
        headers=admin["headers"],
    )
    res = client.delete("/api/v1/admin/employees/20239999", headers=admin["headers"])
    assert res.status_code == 200


def test_admin_list_and_delete_user(client, make_user):
    admin = make_user(is_admin=True, emp_id="20230001", email="admin@test.com")
    normal = make_user(emp_id="20230002", email="normal@test.com")

    res = client.get("/api/v1/admin/users", headers=admin["headers"])
    assert res.status_code == 200
    assert len(res.json()["data"]) == 2

    del_res = client.delete(f"/api/v1/admin/users/{normal['userId']}", headers=admin["headers"])
    assert del_res.status_code == 200

    # 삭제된 계정으로는 더이상 로그인 안 되는지까지 확인 (실제 계정 삭제 효과 검증)
    login_res = client.post("/api/v1/auth/login", json={"empId": "20230002", "pw": "password1"})
    assert login_res.status_code == 401
