"""add pickup_point_id to addresses and orders

Revision ID: 85bb258fccb2
Revises: 9789e3658e95
Create Date: 2026-08-13 10:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '85bb258fccb2'
down_revision: Union[str, None] = '9789e3658e95'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('addresses', sa.Column('pickup_point_id', sa.UUID(), nullable=True))
    op.create_foreign_key(None, 'addresses', 'pickup_points', ['pickup_point_id'], ['id'])
    op.add_column('orders', sa.Column('pickup_point_id', sa.UUID(), nullable=True))
    op.create_foreign_key(None, 'orders', 'pickup_points', ['pickup_point_id'], ['id'])


def downgrade() -> None:
    op.drop_constraint(None, 'orders', type_='foreignkey')
    op.drop_column('orders', 'pickup_point_id')
    op.drop_constraint(None, 'addresses', type_='foreignkey')
    op.drop_column('addresses', 'pickup_point_id')
