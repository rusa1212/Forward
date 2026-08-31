"""SQLAlchemy ORM 모델. back/mysql/schema.sql의 실제 테이블 스키마와 1:1로 대응됩니다.

MySQL/MariaDB 전환 노트 (docs/be/6th_wk_DB전환.md):
- MySQL엔 네이티브 UUID 컬럼 타입이 없어 PK/FK는 CHAR(36) 문자열로 저장하고,
  기본값은 DB 함수(gen_random_uuid) 대신 애플리케이션에서 str(uuid.uuid4())로 생성합니다.
- 시간 컬럼은 시간대 정보가 없는 DATETIME입니다. 세션 time_zone을 UTC로 고정해
  (app/db/session.py) CURRENT_TIMESTAMP가 항상 UTC로 저장되도록 합니다.
- MySQL은 TEXT 컬럼에 인덱스/UNIQUE를 걸 때 길이 제한이 있어,
  PK/UNIQUE/FK 대상 문자열 컬럼은 TEXT가 아닌 VARCHAR(String)입니다.
"""
import uuid
from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, String, Text, UniqueConstraint, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _uuid_str() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


class Employee(Base):
    """사원 명부 (회원가입 시 사번+이름 인증용)."""
    __tablename__ = "employees"

    emp_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    department: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )


class User(Base):
    """가입 계정. emp_id는 사번 1개당 계정 1개만 허용."""
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    emp_id: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )


class Announcement(Base):
    __tablename__ = "announcements"
    __table_args__ = (
        UniqueConstraint("source", "external_id", name="announcements_source_external_id_key"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    external_id: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    department: Mapped[str | None] = mapped_column(String(255))
    reception_start: Mapped[date | None] = mapped_column(Date)
    reception_end: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str | None] = mapped_column(String(50))
    detail_url: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)
    collected_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )


class Keyword(Base):
    """사용자가 등록한 알림 키워드 (5주차 1차 작업 순서 10)."""
    __tablename__ = "keywords"
    __table_args__ = (
        UniqueConstraint("user_id", "keyword", name="keywords_user_id_keyword_key"),
        CheckConstraint("char_length(keyword) BETWEEN 1 AND 50", name="keywords_keyword_length_check"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    keyword: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )


class SavedAnnouncement(Base):
    """사용자가 저장(즐겨찾기)한 공고 (5주차 1차 작업 순서 12)."""
    __tablename__ = "saved_announcements"
    __table_args__ = (
        UniqueConstraint("user_id", "announcement_id", name="saved_announcements_user_id_announcement_id_key"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    announcement_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("announcements.id", ondelete="CASCADE"), nullable=False
    )
    saved_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
