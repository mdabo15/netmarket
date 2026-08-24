"""add pickup point manager role and table

Revision ID: 9789e3658e95
Revises: 4215279f1c8f
Create Date: 2026-08-13 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9789e3658e95'
down_revision: Union[str, None] = '4215279f1c8f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Alembic autogenerate doesn't detect new values on an existing Postgres
    # enum (only column/table structure) — added by hand. Safe inside this
    # transaction on PG12+ as long as the new value isn't used until a later
    # transaction (it isn't, here).
    op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'pickup_point_manager'")
    op.execute("ALTER TYPE order_status ADD VALUE IF NOT EXISTS 'arrived_at_pickup_point'")

    op.create_table('pickup_point_managers',
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('pickup_point_id', sa.UUID(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['pickup_point_id'], ['pickup_points.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id')
    )


def downgrade() -> None:
    op.drop_table('pickup_point_managers')
    # 'pickup_point_manager' / 'arrived_at_pickup_point' stay in their enums —
    # Postgres has no direct "remove enum value" operation (would mean
    # rebuilding the type + every column using it); not worth it for a
    # downgrade path, same rationale as 9b25433107ab.
