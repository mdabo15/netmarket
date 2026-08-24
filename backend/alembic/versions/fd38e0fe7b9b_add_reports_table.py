"""add reports table

Revision ID: fd38e0fe7b9b
Revises: 2018e0d98a47
Create Date: 2026-08-14 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fd38e0fe7b9b'
down_revision: Union[str, None] = '2018e0d98a47'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('reports',
    sa.Column('reporter_id', sa.UUID(), nullable=False),
    sa.Column('report_type', sa.Enum('product', 'review', name='report_type'), nullable=False),
    sa.Column('product_id', sa.UUID(), nullable=True),
    sa.Column('review_id', sa.UUID(), nullable=True),
    sa.Column('reason', sa.String(length=300), nullable=False),
    sa.Column('status', sa.Enum('pending', 'dismissed', 'actioned', name='report_status'), nullable=False),
    sa.Column('admin_note', sa.String(length=300), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['reporter_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['review_id'], ['reviews.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('reports')
    op.execute("DROP TYPE report_status")
    op.execute("DROP TYPE report_type")
