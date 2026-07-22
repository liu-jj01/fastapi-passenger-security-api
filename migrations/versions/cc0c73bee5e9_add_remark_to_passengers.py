"""add remark to passengers

Revision ID: cc0c73bee5e9
Revises: d75b113abd20
Create Date: 2026-07-21 16:56:14.288584

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cc0c73bee5e9'
down_revision: Union[str, Sequence[str], None] = 'd75b113abd20'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add remark column."""
    op.add_column(
        "passengers",
        sa.Column(
            "remark",
            sa.String(length=200),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Remove remark column."""
    with op.batch_alter_table("passengers") as batch_op:
        batch_op.drop_column("remark")
