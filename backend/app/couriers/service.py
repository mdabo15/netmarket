"""Business logic for courier ("livreur") onboarding and admin validation."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.core.security import hash_password
from app.couriers import repository
from app.couriers.models import Courier, CourierStatus
from app.couriers.schemas import CourierAdminCreate, CourierAdminUpdate, CourierRegister
from app.users import repository as users_repository
from app.users.models import User, UserRole


async def register_courier(db: AsyncSession, user: User, data: CourierRegister) -> Courier:
    # Un seul rôle par compte (comme pour les vendeurs) — devenir livreur
    # remplacerait silencieusement le rôle vendeur/admin existant et casserait
    # l'accès aux espaces correspondants. Seul un acheteur peut s'inscrire.
    if user.role == UserRole.COURIER:
        raise ConflictError("Vous êtes déjà inscrit comme livreur.")
    if user.role != UserRole.BUYER:
        raise ForbiddenError("Seul un compte acheteur peut s'inscrire comme livreur.")

    courier = await repository.create(db, user_id=user.id, vehicle_type=data.vehicle_type, zone=data.zone)
    user.role = UserRole.COURIER
    await db.commit()
    return await repository.get_by_id(db, courier.id)


async def get_my_courier(db: AsyncSession, user: User) -> Courier:
    courier = await repository.get_by_user_id(db, user.id)
    if courier is None:
        raise NotFoundError("Vous n'avez pas encore de profil livreur.")
    return courier


async def list_public_couriers(db: AsyncSession) -> list[Courier]:
    return await repository.list_by_status(db, CourierStatus.APPROVED)


async def admin_create_courier(db: AsyncSession, data: CourierAdminCreate) -> Courier:
    if await users_repository.get_by_phone(db, data.phone) is not None:
        raise ConflictError("Ce numéro de téléphone est déjà utilisé.")

    user = await users_repository.create(
        db,
        phone=data.phone,
        password_hash=hash_password(data.password),
        role=UserRole.COURIER,
        first_name=data.first_name,
        last_name=data.last_name,
    )
    courier = await repository.create(db, user_id=user.id, vehicle_type=data.vehicle_type, zone=data.zone)
    # Un admin qui crée le compte EST la validation — pas besoin de repasser
    # par le statut pending comme pour l'auto-inscription.
    courier.status = CourierStatus.APPROVED
    await db.commit()
    return await repository.get_by_id(db, courier.id)


async def admin_list_couriers(db: AsyncSession, status: CourierStatus | None) -> list[Courier]:
    return await repository.list_by_status(db, status)


async def admin_update_courier(db: AsyncSession, courier_id: uuid.UUID, data: CourierAdminUpdate) -> Courier:
    courier = await repository.get_by_id(db, courier_id)
    if courier is None:
        raise NotFoundError("Livreur introuvable.")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(courier, field, value)
    await db.commit()
    return await repository.get_by_id(db, courier_id)
