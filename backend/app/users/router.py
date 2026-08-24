"""Routes for the authenticated user's own profile."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.schemas import Message
from app.core.deps import get_current_user, get_db
from app.users import service
from app.users.models import User
from app.users.schemas import UserRead, UserUpdate, VerifyEmailRequest

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
async def read_my_profile(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.patch("/me", response_model=UserRead)
async def update_my_profile(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    return await service.update_profile(db, current_user, payload)


@router.post("/me/resend-verification-email", response_model=Message)
async def resend_verification_email(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> Message:
    await service.send_verification_code(db, current_user)
    return Message(detail="Code envoyé.")


@router.post("/me/verify-email", response_model=UserRead)
async def verify_email(
    payload: VerifyEmailRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    return await service.verify_email_code(db, current_user, payload.code)
