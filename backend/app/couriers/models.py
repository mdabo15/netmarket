"""Courier ORM model — "livreur" (motard, taxi, société de livraison)
transporting a sub-order from a vendor to a buyer or pickup point.

Deliberately the simple version of a delivery system (cahier des charges
§4.2 leaves the full marketplace — open sign-up, auto-matching, live GPS
tracking — to phase 2): a courier is validated by the admin exactly like a
vendor, and assigned manually per sub-order by the vendor who owns it (see
app/orders — SubOrder.courier_id).
"""

import uuid
from enum import StrEnum

from sqlalchemy import Enum as SAEnum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.common.models import TimestampMixin, UUIDPrimaryKeyMixin
from app.core.database import Base


class CourierStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"


class VehicleType(StrEnum):
    MOTO = "moto"
    TAXI = "taxi"
    VOITURE = "voiture"


class Courier(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "couriers"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False
    )
    vehicle_type: Mapped[VehicleType] = mapped_column(
        SAEnum(VehicleType, name="vehicle_type", values_callable=lambda enum: [e.value for e in enum]),
        nullable=False,
    )
    # Zone de couverture textuelle (commune/quartier), même logique que Vendor.zone.
    zone: Mapped[str | None] = mapped_column(String(150), nullable=True)
    status: Mapped[CourierStatus] = mapped_column(
        SAEnum(CourierStatus, name="courier_status", values_callable=lambda enum: [e.value for e in enum]),
        default=CourierStatus.PENDING,
        nullable=False,
    )
