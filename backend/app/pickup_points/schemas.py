"""Pydantic schemas for admin-managed pickup points."""

import uuid

from pydantic import BaseModel, ConfigDict, Field


class PickupPointCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    zone: str = Field(min_length=3, max_length=300)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    is_active: bool = True


class PickupPointUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    zone: str | None = Field(default=None, min_length=3, max_length=300)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    is_active: bool | None = None


class PickupPointRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    zone: str
    latitude: float | None
    longitude: float | None
    is_active: bool
