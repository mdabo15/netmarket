"""add structured delivery fields to orders

Revision ID: 2018e0d98a47
Revises: 85bb258fccb2
Create Date: 2026-08-13 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2018e0d98a47'
down_revision: Union[str, None] = '85bb258fccb2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Nullable et non rétro-remplies : les commandes existantes retombent sur
    # le texte combiné delivery_address déjà présent (voir
    # app/orders/service.py). Seules les nouvelles commandes remplissent ces
    # champs structurés, pour l'affichage ligne par ligne côté frontend.
    op.add_column('orders', sa.Column('delivery_zone', sa.String(length=300), nullable=True))
    op.add_column('orders', sa.Column('delivery_instructions', sa.String(length=300), nullable=True))
    op.add_column('orders', sa.Column('recipient_name', sa.String(length=150), nullable=True))
    op.add_column('orders', sa.Column('recipient_phone', sa.String(length=20), nullable=True))


def downgrade() -> None:
    op.drop_column('orders', 'recipient_phone')
    op.drop_column('orders', 'recipient_name')
    op.drop_column('orders', 'delivery_instructions')
    op.drop_column('orders', 'delivery_zone')
