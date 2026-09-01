"""initial schema

Supabase(Postgres)에서 전환한 MySQL/MariaDB 5개 테이블을 생성합니다.
(employees / users / announcements / keywords / saved_announcements)
기존 back/mysql/schema.sql(삭제됨)과 동일한 결과입니다.

Revision ID: 0001
Revises:
Create Date: 2026-09-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('announcements',
    sa.Column('id', sa.CHAR(length=36), nullable=False),
    sa.Column('source', sa.String(length=50), nullable=False),
    sa.Column('external_id', sa.String(length=100), nullable=False),
    sa.Column('title', sa.Text(), nullable=False),
    sa.Column('department', sa.String(length=255), nullable=True),
    sa.Column('reception_start', sa.Date(), nullable=True),
    sa.Column('reception_end', sa.Date(), nullable=True),
    sa.Column('status', sa.String(length=50), nullable=True),
    sa.Column('detail_url', sa.Text(), nullable=True),
    sa.Column('summary', sa.Text(), nullable=True),
    sa.Column('collected_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('source', 'external_id', name='announcements_source_external_id_key'),
    mysql_charset='utf8mb4',
    mysql_collate='utf8mb4_unicode_ci',
    mysql_engine='InnoDB'
    )
    op.create_index('idx_announcements_collected_at', 'announcements', ['collected_at'], unique=False)
    op.create_index('idx_announcements_department', 'announcements', ['department'], unique=False)
    op.create_index('idx_announcements_reception', 'announcements', ['reception_start', 'reception_end'], unique=False)
    op.create_index('idx_announcements_status', 'announcements', ['status'], unique=False)
    op.create_table('employees',
    sa.Column('emp_id', sa.String(length=20), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=False),
    sa.Column('department', sa.String(length=100), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.PrimaryKeyConstraint('emp_id'),
    mysql_charset='utf8mb4',
    mysql_collate='utf8mb4_unicode_ci',
    mysql_engine='InnoDB'
    )
    op.create_table('users',
    sa.Column('id', sa.CHAR(length=36), nullable=False),
    sa.Column('emp_id', sa.String(length=20), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.ForeignKeyConstraint(['emp_id'], ['employees.emp_id'], name='fk_users_emp_id'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email', name='users_email_key'),
    sa.UniqueConstraint('emp_id', name='users_emp_id_key'),
    mysql_charset='utf8mb4',
    mysql_collate='utf8mb4_unicode_ci',
    mysql_engine='InnoDB'
    )
    op.create_table('keywords',
    sa.Column('id', sa.CHAR(length=36), nullable=False),
    sa.Column('user_id', sa.CHAR(length=36), nullable=False),
    sa.Column('keyword', sa.String(length=50), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.CheckConstraint('char_length(keyword) BETWEEN 1 AND 50', name='keywords_keyword_length_check'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_keywords_user_id', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'keyword', name='keywords_user_id_keyword_key'),
    mysql_charset='utf8mb4',
    mysql_collate='utf8mb4_unicode_ci',
    mysql_engine='InnoDB'
    )
    op.create_table('saved_announcements',
    sa.Column('id', sa.CHAR(length=36), nullable=False),
    sa.Column('user_id', sa.CHAR(length=36), nullable=False),
    sa.Column('announcement_id', sa.CHAR(length=36), nullable=False),
    sa.Column('saved_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.ForeignKeyConstraint(['announcement_id'], ['announcements.id'], name='fk_saved_announcement_id', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_saved_user_id', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'announcement_id', name='saved_announcements_user_id_announcement_id_key'),
    mysql_charset='utf8mb4',
    mysql_collate='utf8mb4_unicode_ci',
    mysql_engine='InnoDB'
    )
    op.create_index('idx_saved_announcements_announcement_id', 'saved_announcements', ['announcement_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # 테이블을 지우면 그 위의 인덱스는 자동으로 함께 삭제되므로 drop_index는 호출하지 않는다
    # (FK가 참조하는 인덱스는 테이블 존재 중엔 drop_index가 거부됨 — MySQL error 1553).
    # FK 의존 순서: saved_announcements → keywords → announcements → users → employees
    op.drop_table('saved_announcements')
    op.drop_table('keywords')
    op.drop_table('announcements')
    op.drop_table('users')
    op.drop_table('employees')
