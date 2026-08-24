"""Database access for Report."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.reports.models import Report, ReportStatus, ReportType


async def create(db: AsyncSession, **fields) -> Report:
    report = Report(**fields)
    db.add(report)
    await db.flush()
    return report


async def get_by_id(db: AsyncSession, report_id: uuid.UUID) -> Report | None:
    result = await db.execute(select(Report).where(Report.id == report_id))
    return result.scalar_one_or_none()


async def get_existing(
    db: AsyncSession, reporter_id: uuid.UUID, *, product_id: uuid.UUID | None = None, review_id: uuid.UUID | None = None
) -> Report | None:
    stmt = select(Report).where(Report.reporter_id == reporter_id)
    stmt = stmt.where(Report.product_id == product_id) if product_id is not None else stmt.where(Report.review_id == review_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def list_reports(db: AsyncSession, status: ReportStatus | None, report_type: ReportType | None) -> list[Report]:
    stmt = select(Report)
    if status is not None:
        stmt = stmt.where(Report.status == status)
    if report_type is not None:
        stmt = stmt.where(Report.report_type == report_type)
    stmt = stmt.order_by(Report.created_at.desc())
    return list((await db.execute(stmt)).scalars().all())
