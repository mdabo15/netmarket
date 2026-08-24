"""Pydantic schema for the image upload response."""

from pydantic import BaseModel


class UploadedImages(BaseModel):
    keys: list[str]
