"""Pydantic schemas for courier ("livreur") onboarding and admin validation."""

import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.auth.schemas import PHONE_PATTERN
from app.couriers.models import CourierStatus, VehicleType


class CourierRegister(BaseModel):
    vehicle_type: VehicleType
    zone: str | None = Field(default=None, max_length=150)


class CourierAdminCreate(BaseModel):
    """Admin-direct account creation — e.g. for a partner delivery company
    that shouldn't have to self-register as a buyer first. Approved immediately
    (an admin creating the account IS the validation), unlike self-registration."""

    phone: str = Field(pattern=PHONE_PATTERN, description="Format international, ex: +224621234567")
    password: str = Field(min_length=8)
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    vehicle_type: VehicleType
    zone: str | None = Field(default=None, max_length=150)


class CourierAdminUpdate(BaseModel):
    status: CourierStatus | None = None


class CourierRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    vehicle_type: VehicleType
    zone: str | None
    status: CourierStatus
    # Attachés en lecture depuis User (voir app/couriers/repository.py) — un
    # vendeur choisissant un livreur dans une liste a besoin de plus qu'un id.
    phone: str
    full_name: str | None = None
