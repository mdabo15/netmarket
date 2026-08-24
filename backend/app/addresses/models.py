"""Address ORM model: a buyer's saved delivery addresses / pickup points, reused at checkout.

Deliberately not referenced by Order (FK) — checkout still freezes a plain
delivery_address string onto the order (see app/orders/service.py), same
pattern as shop_name/product_name. An Address is only ever a template the
frontend uses to prefill that string; editing or deleting it later must not
be able to alter past orders.
"""

import uuid

from sqlalchemy import Boolean, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Enum as SAEnum

from app.common.models import TimestampMixin, UUIDPrimaryKeyMixin
from app.core.database import Base
from app.orders.models import DeliveryType


class Address(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "addresses"

    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    # Nom donné par l'acheteur pour s'y retrouver ("Maison", "Bureau", "Point Wari Madina"...).
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    delivery_type: Mapped[DeliveryType] = mapped_column(
        SAEnum(DeliveryType, name="delivery_type", values_callable=lambda enum: [e.value for e in enum]),
        default=DeliveryType.HOME_DELIVERY,
        nullable=False,
    )
    # Zone/quartier + point de repère textuel — même logique que Order.delivery_address.
    zone: Mapped[str] = mapped_column(String(300), nullable=False)
    # Quel point précis (annuaire admin) cette adresse pointe-t-elle — seulement
    # renseigné quand delivery_type == PICKUP_POINT. Additif : zone reste la
    # source d'affichage figée (voir docstring ci-dessus), cette FK sert
    # uniquement à router les commandes vers le bon gestionnaire de point.
    pickup_point_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("pickup_points.id"), nullable=True
    )
    recipient_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    recipient_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    instructions: Mapped[str | None] = mapped_column(String(300), nullable=True)
    # Position GPS optionnelle, captée via l'API de géolocalisation du navigateur
    # (bouton "Utiliser ma position actuelle") — vient en complément du repère
    # textuel, ne le remplace pas (cahier des charges §1 : adresses guinéennes
    # peu structurées).
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
