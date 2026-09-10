"""pytest 공통 fixture (5주차 우선순위 "API 테스트 보강").

⚠️ 이 테스트는 전용 테스트 DB를 매 실행마다 드롭/재생성하고, 각 테스트마다 테이블을
비운다(clean_db fixture). 그래서 **개발용 DATABASE_URL DB는 절대 건드리지 않는다** —
아래 _resolve_test_db_url()이 TEST_DATABASE_URL(없으면 "<DB이름>_test")을 쓰고,
그게 DATABASE_URL과 같은 DB를 가리키면 실행 자체를 막는다.

MySQL 전환 노트: SQLite 등 인메모리 DB로 바꾸지 않고 실제 MySQL/MariaDB(테스트 DB)에
대고 테스트한다. 이 프로젝트가 MySQL 전용 문법(INSERT ... ON DUPLICATE KEY UPDATE,
CHECK 제약, utf8mb4 등)을 쓰기 때문이다.
"""
import sys
from pathlib import Path

# back/ 디렉터리를 sys.path에 추가 (어느 위치에서 pytest를 실행해도 `import app...`이 되도록)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from app.core.config import settings


def _resolve_test_db_url() -> str:
    """테스트 DB URL을 정하고, 개발 DB와 같으면 즉시 실행을 중단한다."""
    if not settings.DATABASE_URL:
        raise pytest.UsageError("DATABASE_URL이 비어 있습니다. back/.env를 설정하세요.")

    main_url = make_url(settings.DATABASE_URL)
    if settings.TEST_DATABASE_URL:
        test_url = make_url(settings.TEST_DATABASE_URL)
    else:
        test_url = main_url.set(database=f"{main_url.database}_test")

    same_db = (test_url.database, test_url.host, test_url.port) == (
        main_url.database,
        main_url.host,
        main_url.port,
    )
    if same_db:
        raise pytest.UsageError(
            f"테스트 DB('{test_url.database}')가 DATABASE_URL('{main_url.database}')와 같습니다.\n"
            "clean_db fixture가 이 DB를 통째로 지웁니다 — 개발 데이터가 날아갑니다.\n"
            "back/.env에 TEST_DATABASE_URL을 다른 DB로 지정하세요."
        )
    return test_url.render_as_string(hide_password=False)


def _ensure_test_db_exists(test_db_url: str) -> None:
    """테스트 DB가 없으면 만든다 (개발 DB에 접속해서 CREATE DATABASE)."""
    test_db_name = make_url(test_db_url).database
    admin_engine = create_engine(settings.DATABASE_URL)
    try:
        with admin_engine.connect() as conn:
            conn.execute(
                text(
                    f"CREATE DATABASE IF NOT EXISTS `{test_db_name}` "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
            )
            conn.commit()
    except Exception as exc:  # pragma: no cover - 환경 문제
        raise pytest.UsageError(
            f"테스트 DB '{test_db_name}' 생성 실패: {exc}\n"
            "계정에 CREATE 권한이 없으면 직접 만들거나 TEST_DATABASE_URL을 지정하세요."
        )
    finally:
        admin_engine.dispose()


_TEST_DB_URL = _resolve_test_db_url()
_ensure_test_db_exists(_TEST_DB_URL)

# 앱 코드가 엔진을 만들기 전에 URL을 테스트 DB로 바꿔놓는다.
# (app.db.session이 import 시점에 create_engine(settings.DATABASE_URL) 하므로 순서가 중요)
settings.DATABASE_URL = _TEST_DB_URL

from app.db.models import Base  # noqa: E402
from app.db.models import Employee, User  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

# 테스트 세션 시작 시 스키마를 새로 만든다 (models.py 기준). alembic 불필요.
with engine.begin() as _conn:
    _conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
    Base.metadata.drop_all(bind=_conn)
    Base.metadata.create_all(bind=_conn)
    _conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))

_CLEAN_TABLES = (
    "notification_logs",
    "alert_settings",
    "saved_announcements",
    "keywords",
    "users",
    "announcements",
    "employees",
)


@pytest.fixture(autouse=True)
def clean_db():
    """각 테스트 시작 전에 관련 테이블을 비운다 (FK 순서 걱정 없이 FK 체크를 잠깐 꺼둠).

    대상은 전용 테스트 DB다 (conftest 상단에서 DATABASE_URL을 이미 교체했다).
    """
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
