"""Report endpoints: buyer-facing creation nested under the target resource
(mirrors POST /products/{id}/reviews), plus an admin moderation queue."""

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, require_role
from app.reports import service
from app.reports.models import ReportStatus, ReportType
from app.reports.schemas import ReportAdminUpdate, ReportCreate, ReportRead
from app.users.models import User, UserRole

router = APIRouter(tags=["reports"])
admin_router = APIRouter(prefix="/admin/reports", tags=["admin"], dependencies=[Depends(require_role(UserRole.ADMIN))])


@router.post("/products/{product_id}/reports", response_model=ReportRead, status_code=status.HTTP_201_CREATED)
async def report_product(
    product_id: uuid.UUID,
    payload: ReportCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReportRead:
    return await service.report_product(db, current_user, product_id, payload)


@router.post("/reviews/{review_id}/reports", response_model=ReportRead, status_code=status.HTTP_201_CREATED)
async def report_review(
    review_id: uuid.UUID,
    payload: ReportCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReportRead:
    return await service.report_review(db, current_user, review_id, payload)


@admin_router.get("", response_model=list[ReportRead])
async def admin_list_reports(
    status_filter: ReportStatus | None = Query(default=None, alias="status"),
    type_filter: ReportType | None = Query(default=None, alias="type"),
    db: AsyncSession = Depends(get_db),
) -> list[ReportRead]:
    return await service.admin_list_reports(db, status_filter, type_filter)


@admin_router.patch("/{report_id}", response_model=ReportRead)
async def admin_resolve_report(
    report_id: uuid.UUID, payload: ReportAdminUpdate, db: AsyncSession = Depends(get_db)
) -> ReportRead:
    return await service.admin_resolve_report(db, report_id, payload)
