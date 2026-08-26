"""
SQLAlchemy ORM 모델 — 공공 R&D 과제 공고 키워드 모니터링 서비스

FastAPI 백엔드 리포에 그대로 붙여 쓰는 용도.
schema.sql(수기 DDL)과 1:1로 대응되며, 이 파일을 기준으로 Alembic 마이그레이션을
autogenerate 했습니다 (backend_db/migrations/versions/ 참고).

DBMS가 MySQL로 확정되면 postgresql.UUID / server_default text 부분만
String(36) + default=lambda: str(uuid4()) 형태로 바꿔주면 됩니다.
"""
import uuid
from datetime import date, datetime, time

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Text,
    Time,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Employee(Base):
    """1.2 — 회원가입 인증용 사원 마스터"""
    __tablename__ = "employees"

    employee_no: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    department: Mapped[str | None]
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=text("now()"))

    user: Mapped["User | None"] = relationship(back_populates="employee", uselist=False)


class User(Base):
    """1.2 — 로그인 계정"""
    __tablename__ = "users"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    employee_no: Mapped[str] = mapped_column(
        ForeignKey("employees.employee_no"), nullable=False, unique=True
    )
    email: Mapped[str] = mapped_column(nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(nullable=False, server_default=text("'active'"))
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=text("now()"))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime)

    employee: Mapped[Employee] = relationship(back_populates="user")
    keywords: Mapped[list["Keyword"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    saved_announcements: Mapped[list["SavedAnnouncement"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    notification_logs: Mapped[list["NotificationLog"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Announcement(Base):
    """1.3 — 공고"""
    __tablename__ = "announcements"
    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_announcements_source_external"),
        Index("idx_announcements_status_agency_dept", "status", "agency", "department"),
        Index("idx_announcements_end_date", "end_date"),
    )

    announcement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    source: Mapped[str] = mapped_column(nullable=False)
    external_id: Mapped[str] = mapped_column(nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    agency: Mapped[str | None]
    department: Mapped[str | None]
    status: Mapped[str | None]
    announce_date: Mapped[date | None] = mapped_column(Date)
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    original_url: Mapped[str | None] = mapped_column(Text)
    content: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=text("now()"))

    saved_by: Mapped[list["SavedAnnouncement"]] = relationship(back_populates="announcement")
    notification_logs: Mapped[list["NotificationLog"]] = relationship(back_populates="announcement")


class Keyword(Base):
    """1.4 — 키워드"""
    __tablename__ = "keywords"
    __table_args__ = (
        UniqueConstraint("user_id", "keyword", name="uq_keywords_user_keyword"),
        CheckConstraint("char_length(keyword) BETWEEN 1 AND 50", name="chk_keywords_length"),
    )

    keyword_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    keyword: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=text("now()"))

    user: Mapped[User] = relationship(back_populates="keywords")
    alert_setting: Mapped["AlertSetting | None"] = relationship(
        back_populates="keyword", uselist=False, cascade="all, delete-orphan"
    )
    notification_logs: Mapped[list["NotificationLog"]] = relationship(back_populates="keyword")


class SavedAnnouncement(Base):
    """1.4 — 저장 공고 (WBS 8.1에서 사용)"""
    __tablename__ = "saved_announcements"
    __table_args__ = (
        UniqueConstraint("user_id", "announcement_id", name="uq_saved_user_announcement"),
    )

    saved_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    announcement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("announcements.announcement_id", ondelete="CASCADE"), nullable=False
    )
    saved_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=text("now()"))

    user: Mapped[User] = relationship(back_populates="saved_announcements")
    announcement: Mapped[Announcement] = relationship(back_populates="saved_by")


class AlertSetting(Base):
    """1.4 — 키워드별 알림 설정 (WBS 11.1에서 사용)"""
    __tablename__ = "alert_settings"

    setting_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    keyword_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("keywords.keyword_id", ondelete="CASCADE"), nullable=False, unique=True
    )
    dashboard_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    email_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    email_frequency: Mapped[str | None]
    email_send_time: Mapped[time | None] = mapped_column(Time)
    alert_d7: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    alert_d3: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    alert_d1: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=text("now()"))

    keyword: Mapped[Keyword] = relationship(back_populates="alert_setting")


class NotificationLog(Base):
    """1.4 — 알림 발송 이력 (WBS 12.x에서 사용)"""
    __tablename__ = "notification_logs"
    __table_args__ = (
        UniqueConstraint("user_id", "announcement_id", "notify_type", name="uq_notification_dedup"),
        Index("idx_notification_logs_user_sent", "user_id", "sent_at"),
    )

    log_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    announcement_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("announcements.announcement_id", ondelete="SET NULL")
    )
    keyword_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("keywords.keyword_id", ondelete="SET NULL")
    )
    channel: Mapped[str] = mapped_column(nullable=False)
    notify_type: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(nullable=False, server_default=text("'success'"))
    sent_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=text("now()"))
    error_message: Mapped[str | None] = mapped_column(Text)

    user: Mapped[User] = relationship(back_populates="notification_logs")
    announcement: Mapped["Announcement | None"] = relationship(back_populates="notification_logs")
    keyword: Mapped["Keyword | None"] = relationship(back_populates="notification_logs")
