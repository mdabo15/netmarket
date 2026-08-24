"""PickupPointManager ORM model — a User with role=PICKUP_POINT_MANAGER,
staffing one specific PickupPoint. Accounts are admin-created only (see
app/pickup_point_managers/service.py::admin_create_manager) — unlike Courier
there is no self-registration/approval lifecycle: an admin creating the
account IS the validation, and reassigning/removing it is a plain
update/delete rather than a status flip.
"""

import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.common.models import TimestampMixin, UUIDPrimaryKeyMixin
from app.core.database import Base


class PickupPointManager(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "pickup_point_managers"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False
    )
    # Plusieurs gestionnaires peuvent couvrir le même point (équipes/relais) —
    # pas de contrainte d'unicité côté point, seulement côté user.
    pickup_point_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("pickup_points.id"), nullable=False
    )
