"""Small schemas shared across modules."""

from pydantic import BaseModel


class Message(BaseModel):
    """Generic confirmation response, e.g. {"detail": "Produit supprimé."}."""

    detail: str
