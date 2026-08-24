"""Pydantic schemas for product/review reports (moderation queue)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.reports.models import ReportStatus, ReportType


class ReportCreate(BaseModel):
    reason: str = Field(min_length=3, max_length=300)


class ReportAdminUpdate(BaseModel):
    # PENDING n'est volontairement pas accepté ici — un signalement ne se
    # "dé-résout" pas, voir service.admin_resolve_report.
    status: ReportStatus
    admin_note: str | None = Field(default=None, max_length=300)


class ReportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    reporter_id: uuid.UUID
    report_type: ReportType
    product_id: uuid.UUID | None
    review_id: uuid.UUID | None
    reason: str
    status: ReportStatus
    admin_note: str | None
    created_at: datetime
    # Contexte dénormalisé, attaché en lecture (voir service._attach_report_context)
    # pour que l'admin n'ait pas à recroiser avec /products ou /reviews.
    product_name: str | None = None
    review_comment: str | None = None
    review_rating: int | None = None
