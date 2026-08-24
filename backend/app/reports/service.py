"""Business logic for reporting products/reviews and admin moderation."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.catalog import repository as catalog_repository
from app.catalog.models import ProductStatus
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.reports import repository
from app.reports.models import Report, ReportStatus, ReportType
from app.reports.schemas import ReportAdminUpdate, ReportCreate
from app.reviews import repository as reviews_repository
from app.users.models import User


async def report_product(db: AsyncSession, user: User, product_id: uuid.UUID, data: ReportCreate) -> Report:
    product = await catalog_repository.get_product_by_id(db, product_id)
    if product is None:
        raise NotFoundError("Produit introuvable.")
    if await repository.get_existing(db, user.id, product_id=product_id) is not None:
        raise ConflictError("Vous avez déjà signalé ce produit.")

    report = await repository.create(
        db, reporter_id=user.id, report_type=ReportType.PRODUCT, product_id=product_id, reason=data.reason
    )
    await db.commit()
    return await _attach_report_context(db, await repository.get_by_id(db, report.id))


async def report_review(db: AsyncSession, user: User, review_id: uuid.UUID, data: ReportCreate) -> Report:
    review = await reviews_repository.get_by_id(db, review_id)
    if review is None:
        raise NotFoundError("Avis introuvable.")
    if await repository.get_existing(db, user.id, review_id=review_id) is not None:
        raise ConflictError("Vous avez déjà signalé cet avis.")

    report = await repository.create(
        db, reporter_id=user.id, report_type=ReportType.REVIEW, review_id=review_id, reason=data.reason
    )
    await db.commit()
    return await _attach_report_context(db, await repository.get_by_id(db, report.id))


async def admin_list_reports(db: AsyncSession, status: ReportStatus | None, report_type: ReportType | None) -> list[Report]:
    reports = await repository.list_reports(db, status, report_type)
    return [await _attach_report_context(db, r) for r in reports]


async def admin_resolve_report(db: AsyncSession, report_id: uuid.UUID, data: ReportAdminUpdate) -> Report:
    report = await repository.get_by_id(db, report_id)
    if report is None:
        raise NotFoundError("Signalement introuvable.")
    if report.status != ReportStatus.PENDING:
        raise ConflictError("Ce signalement a déjà été traité.")
    if data.status == ReportStatus.PENDING:
        raise ForbiddenError("Un signalement ne peut pas être remis en attente.")

    if data.status == ReportStatus.ACTIONED:
        if report.report_type == ReportType.PRODUCT:
            product = await catalog_repository.get_product_by_id(db, report.product_id)
            if product is not None:
                product.status = ProductStatus.INACTIVE
        else:
            review = await reviews_repository.get_by_id(db, report.review_id)
            if review is not None:
                await reviews_repository.delete(db, review)
                # L'avis n'existe plus — on ne peut plus le référencer, mais le
                # signalement lui-même garde une trace de review_id pour l'audit.

    report.status = data.status
    report.admin_note = data.admin_note
    await db.commit()

    updated = await repository.get_by_id(db, report_id)
    return await _attach_report_context(db, updated)


async def _attach_report_context(db: AsyncSession, report: Report) -> Report:
    report.product_name = None
    report.review_comment = None
    report.review_rating = None
    if report.report_type == ReportType.PRODUCT and report.product_id is not None:
        product = await catalog_repository.get_product_by_id(db, report.product_id)
        if product is not None:
            report.product_name = product.name
    elif report.report_type == ReportType.REVIEW and report.review_id is not None:
        review = await reviews_repository.get_by_id(db, report.review_id)
        if review is not None:
            report.review_comment = review.comment
            report.review_rating = review.rating
    return report
