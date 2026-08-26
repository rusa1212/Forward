"""DB 세션. DATABASE_URL은 .env에서 옵니다 (app/core/config.py)."""
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    """FastAPI 라우터에서 Depends(get_db)로 주입해서 사용."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
