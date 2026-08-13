"""add task status

Revision ID: ff4f8a2832d2
Revises: 4e39e0445e1b
Create Date: 2026-08-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ff4f8a2832d2'
down_revision: Union[str, Sequence[str], None] = '4e39e0445e1b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'tasks',
        sa.Column(
            'status',
            sa.Enum('in_progress', 'done', name='taskstatus'),
            server_default='in_progress',
            nullable=False
        )
    )
    op.execute("UPDATE tasks SET status = 'in_progress' WHERE status IS NULL")


def downgrade() -> None:
    op.drop_column('tasks', 'status')
    op.execute("DROP TYPE IF EXISTS taskstatus")
