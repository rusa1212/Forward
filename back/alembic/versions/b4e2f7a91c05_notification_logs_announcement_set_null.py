"""notification_logs.announcement_id FK를 ON DELETE SET NULL로

보관 기간이 지난 마감 공고를 자동으로 정리하게 되면서(services/collect_cycle.py),
기존 CASCADE로는 공고 한 건이 지워질 때 그 공고로 나갔던 알림 이력까지 함께 사라졌다.
알림 이력은 "내가 이 알림을 받았다"는 사용자 기록이라 보관 기간 정리로 지우면 안 된다.

notification_logs는 title을 자체 컬럼으로 갖고 있고, 조회/발송 경로가 모두 LEFT JOIN과
announcement_id NULL을 허용하도록 되어 있어(api/v1/notifications.py, services/notifier.py)
링크가 끊긴 알림도 그대로 표시된다.

saved_announcements는 그대로 CASCADE다 — 사용자가 저장한 공고는 정리 대상에서 아예
제외하므로(purge_stale_closed_announcements) 이 경로로 지워질 일이 없다.

Revision ID: b4e2f7a91c05
Revises: a7c31f9b2d04
Create Date: 2026-09-20
"""
from typing import Sequence, Union

from alembic import op

revision: str = "b4e2f7a91c05"
down_revision: Union[str, Sequence[str], None] = "a7c31f9b2d04"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_FK = "fk_notification_logs_announcement_id"


def _recreate_fk(ondelete: str) -> None:
    op.drop_constraint(_FK, "notification_logs", type_="foreignkey")
    op.create_foreign_key(
        _FK, "notification_logs", "announcements", ["announcement_id"], ["id"], ondelete=ondelete
    )


def upgrade() -> None:
    _recreate_fk("SET NULL")


def downgrade() -> None:
    _recreate_fk("CASCADE")
