"""DB 세션. DATABASE_URL은 .env에서 옵니다 (app/core/config.py).

엔진을 import 시점이 아니라 **처음 쓸 때** 만든다. import 시점에 만들면 DATABASE_URL이
비어 있을 때 FastAPI가 시작되기도 전에 죽어서, DB가 아직 준비되지 않은 상태로는 배포
자체가 불가능하다. 지금은 DB 없이도 서버가 뜨고 /api/v1/health 가 응답하며, DB를 쓰는
요청만 503으로 떨어진다. DATABASE_URL을 채우고 재시작하면 그대로 정상 동작한다.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.core.errors import AppError

_engine = None
_session_factory = None


def _build_engine():
    if not settings.DATABASE_URL:
        raise AppError(
            503,
            "DATABASE_NOT_CONFIGURED",
            "데이터베이스가 아직 연결되지 않았습니다. 관리자에게 문의해주세요.",
        )

    # DB 전환 노트: MySQL/MariaDB의 DATETIME은 시간대 정보가 없으므로,
    # 연결 시 세션 time_zone을 UTC로 고정해 CURRENT_TIMESTAMP(created_at 등)가
    # 서버 위치와 무관하게 항상 UTC로 저장되게 한다. (표시용 KST 변환은 FE/응답 계층 몫)
    connect_args = {}
    if settings.DATABASE_URL.startswith("mysql"):
        connect_args["init_command"] = "SET time_zone = '+00:00'"

    return create_engine(settings.DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)


def get_engine():
    """엔진을 만들어 두고 재사용한다. DATABASE_URL이 비어 있으면 503을 던진다."""
    global _engine, _session_factory
    if _engine is None:
        _engine = _build_engine()
        _session_factory = sessionmaker(bind=_engine, autoflush=False, autocommit=False)
    return _engine


def SessionLocal() -> Session:
    """기존처럼 SessionLocal()로 세션을 얻는다 (내부적으로 엔진을 준비한 뒤 만든다)."""
    get_engine()
    return _session_factory()


def __getattr__(name):
    # `from app.db.session import engine` 을 그대로 쓰되, 그 시점에 엔진을 만든다.
    if name == "engine":
        return get_engine()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def get_db():
    """FastAPI 라우터에서 Depends(get_db)로 주입해서 사용."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
