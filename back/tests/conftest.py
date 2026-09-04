"""pytest 공통 fixture (5주차 우선순위 "API 테스트 보강").

주의: 이 테스트는 .env의 DATABASE_URL이 가리키는 DB의 users/employees/announcements/
keywords/saved_announcements 테이블 내용을 각 테스트 전에 전부 지운다(clean_db fixture).
로컬 개발용 DB에서만 실행하세요 — 운영/공유 DB에 대고 실행하면 안 됩니다.

MySQL 전환 노트: SQLite 등 인메모리 DB로 바꾸지 않고 실제 개발용 MySQL/MariaDB에 대고
테스트를 돌립니다. 이 프로젝트가 MySQL 전용 문법(INSERT ... ON DUPLICATE KEY UPDATE,
CHECK 제약, utf8mb4 등)을 쓰고 있어서 SQLite로는 같은 동작을 보장할 수 없기 때문입니다.
"""
import sys
from pathlib import Path

# back/ 디렉터리를 sys.path에 추가 (어느 위치에서 pytest를 실행해도 `import app...`이 되도록)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, text

from app.db.models import Employee, User
from app.db.session import SessionLocal
from app.main import app

_CLEAN_TABLES = ("saved_announcements", "keywords", "users", "announcements", "employees")


@pytest.fixture(autouse=True)
def clean_db():
    """각 테스트 시작 전에 관련 테이블을 비운다 (FK 순서 걱정 없이 FK 체크를 잠깐 꺼둠)."""
    db = SessionLocal()
    try:
        db.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        for table in _CLEAN_TABLES:
            db.execute(text(f"DELETE FROM {table}"))
        db.execute(text("SET FOREIGN_KEY_CHECKS=1"))
        db.commit()
    finally:
        db.close()
    yield


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def make_user(client, db):
    """사원 등록 + 회원가입 + 로그인까지 한 번에 처리하고 토큰/헤더를 돌려주는 헬퍼.

    사용 예: user = make_user()  /  admin = make_user(is_admin=True)
    """

    def _make(
        emp_id: str = "20230001",
        name: str = "김민준",
        email: str | None = None,
        pw: str = "password1",
        is_admin: bool = False,
    ) -> dict:
        email = email or f"{emp_id}@test.com"
        db.add(Employee(emp_id=emp_id, name=name, department="개발팀"))
        db.commit()

        signup = client.post(
            "/api/v1/auth/signup",
            json={"empId": emp_id, "name": name, "email": email, "pw": pw},
        )
        assert signup.status_code == 200, signup.text

        if is_admin:
            user = db.execute(select(User).where(User.emp_id == emp_id)).scalar_one()
            user.is_admin = True
            db.commit()

        login = client.post("/api/v1/auth/login", json={"empId": emp_id, "pw": pw})
        assert login.status_code == 200, login.text
        token = login.json()["data"]["token"]

        return {
            "empId": emp_id,
            "userId": signup.json()["data"]["id"],
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"},
        }

    return _make
