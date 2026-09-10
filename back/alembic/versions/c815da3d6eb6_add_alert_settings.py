"""add alert_settings table and keyword alert columns

Revision ID: c815da3d6eb6
Revises: 822df0e14869
Create Date: 2026-09-05 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c815da3d6eb6'
down_revision: Union[str, Sequence[str], None] = '822df0e14869'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('keywords', sa.Column('dashboard_alert', sa.Boolean(), server_default=sa.text('1'), nullable=False))
    op.add_column('keywords', sa.Column('email_alert', sa.Boolean(), server_default=sa.text('0'), nullable=False))

    op.create_table('alert_settings',
    sa.Column('user_id', sa.CHAR(length=36), nullable=False),
    sa.Column('email_frequency', sa.String(length=10), server_default=sa.text("'daily'"), nullable=False),
    sa.Column('deadline_alert_days', sa.Integer(), server_default=sa.text('7'), nullable=False),
    sa.Column('deadline_dashboard_alert', sa.Boolean(), server_default=sa.text('1'), nullable=False),
    sa.Column('deadline_email_alert', sa.Boolean(), server_default=sa.text('0'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=False),
    sa.CheckConstraint('deadline_alert_days IN (7, 3, 1)', name='alert_settings_deadline_alert_days_check'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_alert_settings_user_id', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('user_id'),
    mysql_charset='utf8mb4',
    mysql_collate='utf8mb4_unicode_ci',
    mysql_engine='InnoDB'
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('alert_settings')
    op.drop_column('keywords', 'email_alert')
    op.drop_column('keywords', 'dashboard_alert')
