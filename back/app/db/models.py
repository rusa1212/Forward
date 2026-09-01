"""SQLAlchemy ORM 모델. 이 파일이 DB 스키마의 기준이며,
alembic 마이그레이션(back/alembic/versions/)이 여기서 autogenerate됩니다.
(docs/be/alembic-마이그레이션.md)

MySQL/MariaDB 전환 노트 (docs/be/6th_wk_DB전환.md):
- MySQL엔 네이티브 UUID 컬럼 타입이 없어 PK/FK는 CHAR(36) 문자열로 저장하고,
  기본값은 DB 함수(gen_random_uuid) 대신 애플리케이션에서 str(uuid.uuid4())로 생성합니다.
- 시간 컬럼은 시간대 정보가 없는 DATETIME입니다. 세션 time_zone을 UTC로 고정해
  (app/db/session.py) CURRENT_TIMESTAMP가 항상 UTC로 저장되도록 합니다.
- MySQL은 TEXT 컬럼에 인덱스/UNIQUE를 걸 때 길이 제한이 있어,
  UNIQUE/FK 대상 문자열 컬럼은 TEXT가 아닌 VARCHAR(String)입니다.
- 제약·인덱스에 이름을 명시합니다 — 나중에 마이그레이션으로 drop/alter할 때 필요.
"""
import uuid
from datetime import date, datetime

from sqlalchemy import (
    CHAR,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _uuid_str() -> str:
    return str(uuid.uuid4())


# 모든 테이블 공통: DB 기본 charset과 무관하게 InnoDB + utf8mb4 로 강제
# (한글이 latin1로 깨지는 것 방지 — 테이블 단위로 고정)
_MYSQL_TABLE_ARGS = {
    "mysql_engine": "InnoDB",
    "mysql_charset": "utf8mb4",
    "mysql_collate": "utf8mb4_unicode_ci",
}


class Base(DeclarativeBase):
    pass


class Employee(Base):
    """사원 명부 (회원가입 시 사번+이름 인증용)."""
    __tablename__ = "employees"
    __table_args__ = (_MYSQL_TABLE_ARGS,)

    emp_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    department: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )


class User(Base):
    """가입 계정. emp_id는 사번 1개당 계정 1개만 허용."""
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("emp_id", name="users_emp_id_key"),
        UniqueConstraint("email", name="users_email_key"),
        _MYSQL_TABLE_ARGS,
    )

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=_uuid_str)
    emp_id: Mapped[str] = mapped_column(
        String(20), ForeignKey("employees.emp_id", name="fk_users_emp_id"), nullable=False
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )


class Announcement(Base):
    __tablename__ = "announcements"
    __table_args__ = (
        UniqueConstraint("source", "external_id", name="announcements_source_external_id_key"),
        Index("idx_announcements_department", "department"),
        Index("idx_announcements_status", "status"),
        Index("idx_announcements_reception", "reception_start", "reception_end"),
        Index("idx_announcements_collected_at", "collected_at"),
        _MYSQL_TABLE_ARGS,
    )

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=_uuid_str)
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
        _MYSQL_TABLE_ARGS,
    )

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=_uuid_str)
    user_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("users.id", name="fk_keywords_user_id", ondelete="CASCADE"),
        nullable=False,
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
        Index("idx_saved_announcements_announcement_id", "announcement_id"),
        _MYSQL_TABLE_ARGS,
    )

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=_uuid_str)
    user_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("users.id", name="fk_saved_user_id", ondelete="CASCADE"),
        nullable=False,
    )
    announcement_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("announcements.id", name="fk_saved_announcement_id", ondelete="CASCADE"),
        nullable=False,
    )
    saved_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
