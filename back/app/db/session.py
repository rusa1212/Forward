"""DB 세션. DATABASE_URL은 .env에서 옵니다 (app/core/config.py)."""
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# DB 전환 노트: MySQL/MariaDB의 DATETIME은 시간대 정보가 없으므로,
# 연결 시 세션 time_zone을 UTC로 고정해 CURRENT_TIMESTAMP(created_at 등)가
# 서버 위치와 무관하게 항상 UTC로 저장되게 한다. (표시용 KST 변환은 FE/응답 계층 몫)
connect_args = {}
if settings.DATABASE_URL.startswith("mysql"):
    connect_args["init_command"] = "SET time_zone = '+00:00'"

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    """FastAPI 라우터에서 Depends(get_db)로 주입해서 사용."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
