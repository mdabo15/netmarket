"""Business logic for the buyer's saved addresses: ownership checks, and
keeping "is_default" unique per user."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.addresses import repository
from app.addresses.models import Address
from app.addresses.schemas import AddressCreate, AddressUpdate
from app.core.exceptions import ConflictError, NotFoundError
from app.orders.models import DeliveryType
from app.users.models import User


async def create_address(db: AsyncSession, user: User, data: AddressCreate) -> Address:
    existing = await repository.list_for_user(db, user.id)
    # La toute première adresse devient le défaut automatiquement — sinon
    # rien n'est jamais pré-rempli au premier achat, ce qui est justement ce
    # qu'on essaie d'éviter.
    make_default = data.is_default or not existing

    if make_default:
        await repository.unset_default_for_user(db, user.id)

    address = await repository.create(db, user_id=user.id, **{**data.model_dump(), "is_default": make_default})
    await db.commit()
    await db.refresh(address)
    return address


async def list_my_addresses(db: AsyncSession, user: User) -> list[Address]:
    return await repository.list_for_user(db, user.id)


async def _get_owned(db: AsyncSession, user: User, address_id: uuid.UUID) -> Address:
    address = await repository.get_by_id(db, address_id)
    if address is None or address.user_id != user.id:
        raise NotFoundError("Adresse introuvable.")
    return address


async def update_address(db: AsyncSession, user: User, address_id: uuid.UUID, data: AddressUpdate) -> Address:
    address = await _get_owned(db, user, address_id)

    if data.is_default:
        await repository.unset_default_for_user(db, user.id, except_id=address.id)

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(address, field, value)

    # Même filet de sécurité qu'à la création (voir
    # AddressCreate._require_zone_or_position) — recalculé ici sur l'état
    # fusionné puisqu'un PATCH partiel ne voit que les champs qu'il modifie.
    if address.delivery_type == DeliveryType.PICKUP_POINT:
        if address.pickup_point_id is None:
            raise ConflictError("Un point de retrait doit être choisi pour ce mode de livraison.")
    else:
        has_position = address.latitude is not None and address.longitude is not None
        if not has_position and len(address.zone.strip()) < 3:
            raise ConflictError(
                "Indique soit une position GPS, soit une description de l'endroit (au moins 3 caractères)."
            )

    await db.commit()
    await db.refresh(address)
    return address


async def delete_address(db: AsyncSession, user: User, address_id: uuid.UUID) -> None:
    address = await _get_owned(db, user, address_id)
    await repository.delete(db, address)
    await db.commit()
