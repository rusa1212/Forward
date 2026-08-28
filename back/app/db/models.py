"""SQLAlchemy ORM 모델. Supabase에 이미 만들어진 실제 테이블 스키마와 1:1로 대응됩니다."""
import uuid
from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, Text, UniqueConstraint, text
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Employee(Base):
    """사원 명부 (회원가입 시 사번+이름 인증용)."""
    __tablename__ = "employees"

    emp_id: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    department: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class User(Base):
    """가입 계정. emp_id는 사번 1개당 계정 1개만 허용."""
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    emp_id: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    email: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class Announcement(Base):
    __tablename__ = "announcements"
    __table_args__ = (
        UniqueConstraint("source", "external_id", name="announcements_source_external_id_key"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    source: Mapped[str] = mapped_column(Text, nullable=False)
    external_id: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    department: Mapped[str | None] = mapped_column(Text)
    reception_start: Mapped[date | None] = mapped_column(Date)
    reception_end: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str | None] = mapped_column(Text)
    detail_url: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class Keyword(Base):
    """사용자가 등록한 알림 키워드 (5주차 1차 작업 순서 10)."""
    __tablename__ = "keywords"
    __table_args__ = (
        UniqueConstraint("user_id", "keyword", name="keywords_user_id_keyword_key"),
        CheckConstraint("char_length(keyword) BETWEEN 1 AND 50", name="keywords_keyword_length_check"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    keyword: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class SavedAnnouncement(Base):
    """사용자가 저장(즐겨찾기)한 공고 (5주차 1차 작업 순서 12)."""
    __tablename__ = "saved_announcements"
    __table_args__ = (
        UniqueConstraint("user_id", "announcement_id", name="saved_announcements_user_id_announcement_id_key"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    announcement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("announcements.id"), nullable=False
    )
    saved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
