"""keywords.email_alert 기본값을 on으로

키워드를 등록하면 매칭 공고를 곧바로 메일로 받는 것이 기본 동작이 되었다
(POST /keywords가 등록 직후 알림 생성 + 발송까지 수행). 기본값이 off면 사용자가
키워드별 토글을 켜기 전까지 메일이 한 통도 나가지 않아 그 동작이 무의미해진다.

이미 등록된 키워드의 값은 건드리지 않는다 — 사용자가 직접 끈 것일 수 있어서,
기본값 변경이 그 선택을 덮어쓰면 안 된다. 이 마이그레이션은 앞으로 만들어지는
행에만 영향을 준다.

Revision ID: a7c31f9b2d04
Revises: c815da3d6eb6
Create Date: 2026-09-16
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a7c31f9b2d04"
down_revision: Union[str, Sequence[str], None] = "c815da3d6eb6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "keywords",
        "email_alert",
        existing_type=sa.Boolean(),
        existing_nullable=False,
        server_default=sa.text("1"),
    )


def downgrade() -> None:
    op.alter_column(
        "keywords",
        "email_alert",
        existing_type=sa.Boolean(),
        existing_nullable=False,
        server_default=sa.text("0"),
    )
