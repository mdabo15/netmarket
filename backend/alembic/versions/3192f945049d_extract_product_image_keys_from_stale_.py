"""extract product image keys from stale absolute urls

Revision ID: 3192f945049d
Revises: 1e1f66dadaf3
Create Date: 2026-08-16 17:13:52.276816

Product.images used to store full absolute MinIO URLs
(http://<host>:<port>/<bucket>/<key>.jpg) — that host:port went stale
whenever the machine's LAN IP changed (see app/core/storage.py, now
proxying images through the API instead). This rewrites existing rows to
store just the bare key, matching what new uploads write from now on.
Entries that don't look like one of our own MinIO URLs (e.g. a vendor's
manually-pasted external image URL — see ProductForm.vue) are left
untouched.
"""
import re
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '3192f945049d'
down_revision: Union[str, None] = '1e1f66dadaf3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Ancien format : http://<host-quelconque>:<port>/<bucket>/<uuid>.jpg —
# reconnu par son dernier segment (le nom de fichier généré par
# storage.upload_image), peu importe l'hôte/bucket qui a pu changer depuis.
_OLD_URL_PATTERN = re.compile(r"^https?://[^/]+/[^/]+/[0-9a-f-]{36}\.jpg$")


def _extract_key(value: str) -> str:
    return value.rsplit("/", 1)[-1]


def upgrade() -> None:
    connection = op.get_bind()
    rows = connection.execute(sa.text("SELECT id, images FROM products WHERE images != '{}'")).fetchall()

    for row in rows:
        product_id, images = row
        rewritten = [_extract_key(v) if _OLD_URL_PATTERN.match(v) else v for v in images]
        if rewritten != images:
            connection.execute(
                sa.text("UPDATE products SET images = CAST(:images AS text[]) WHERE id = :id"),
                {"images": rewritten, "id": product_id},
            )


def downgrade() -> None:
    # Irréversible par choix : reconstruire d'anciennes URLs absolues
    # réintroduirait exactement le problème que cette migration corrige
    # (un hôte figé, potentiellement déjà obsolète).
    pass
