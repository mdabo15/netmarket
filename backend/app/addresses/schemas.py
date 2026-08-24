"""Pydantic schemas for the buyer's saved addresses / pickup points."""

import uuid

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.orders.models import DeliveryType

_MISSING_LOCATION_MESSAGE = (
    "Indique soit une position GPS, soit une description de l'endroit (au moins 3 caractères)."
)
_MISSING_PICKUP_POINT_MESSAGE = "Un point de retrait doit être choisi pour ce mode de livraison."


class AddressCreate(BaseModel):
    label: str = Field(min_length=1, max_length=100)
    delivery_type: DeliveryType = DeliveryType.HOME_DELIVERY
    # Optionnel dès qu'une position GPS est fournie (livraison à domicile) —
    # voir le model_validator ci-dessous pour la règle croisée.
    zone: str = Field(default="", max_length=300)
    pickup_point_id: uuid.UUID | None = None
    recipient_name: str | None = Field(default=None, max_length=150)
    recipient_phone: str | None = Field(default=None, max_length=20)
    instructions: str | None = Field(default=None, max_length=300)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    is_default: bool = False

    # Filet de sécurité serveur derrière la validation du frontend
    # (AddressForm.vue::validateAddressForm) — sans ça, une adresse "point de
    # retrait" enregistrable sans pickup_point_id passe cette étape mais
    # échoue plus tard, de façon confuse, au moment du checkout (409 "un
    # point de retrait doit être sélectionné").
    @model_validator(mode="after")
    def _require_zone_or_position(self) -> "AddressCreate":
        if self.delivery_type == DeliveryType.PICKUP_POINT:
            if self.pickup_point_id is None:
                raise ValueError(_MISSING_PICKUP_POINT_MESSAGE)
            return self
        has_position = self.latitude is not None and self.longitude is not None
        if not has_position and len(self.zone.strip()) < 3:
            raise ValueError(_MISSING_LOCATION_MESSAGE)
        return self


class AddressUpdate(BaseModel):
    label: str | None = Field(default=None, min_length=1, max_length=100)
    delivery_type: DeliveryType | None = None
    zone: str | None = Field(default=None, max_length=300)
    pickup_point_id: uuid.UUID | None = None
    recipient_name: str | None = Field(default=None, max_length=150)
    recipient_phone: str | None = Field(default=None, max_length=20)
    instructions: str | None = Field(default=None, max_length=300)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    is_default: bool | None = None


class AddressRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    label: str
    delivery_type: DeliveryType
    zone: str
    pickup_point_id: uuid.UUID | None
    recipient_name: str | None
    recipient_phone: str | None
    instructions: str | None
    latitude: float | None
    longitude: float | None
    is_default: bool
