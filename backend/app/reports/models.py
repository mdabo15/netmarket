"""Report ORM model: a buyer flagging a product or a review as inappropriate
or non-compliant, queued for admin moderation (cahier des charges §4.1 —
"modération des produits (signalés, non conformes)").

One table for both target types rather than two near-identical ones — a
single admin queue is simpler to review than two separate lists, and the
workflow (pending → dismissed/actioned) is identical either way. Which
target is set is enforced structurally in app/reports/service.py (separate
report_product/report_review functions each set exactly one FK), not via a
DB CHECK constraint (avoids fragile enum-vs-string comparisons in raw SQL).
"""

import uuid
from enum import StrEnum

from sqlalchemy import Enum as SAEnum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.common.models import TimestampMixin, UUIDPrimaryKeyMixin
from app.core.database import Base


class ReportType(StrEnum):
    PRODUCT = "product"
    REVIEW = "review"


class ReportStatus(StrEnum):
    PENDING = "pending"
    DISMISSED = "dismissed"
    ACTIONED = "actioned"


class Report(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "reports"

    reporter_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    report_type: Mapped[ReportType] = mapped_column(
        SAEnum(ReportType, name="report_type", values_callable=lambda enum: [e.value for e in enum]),
        nullable=False,
    )
    # Exactly one of the two is set, matching report_type — see schemas.py.
    # ondelete="SET NULL" : une action de modération sur un signalement avis
    # supprime l'avis lui-même (voir service.admin_resolve_report) — sans ça,
    # la suppression échouerait à cause de cette FK (et d'éventuels autres
    # signalements pointant sur le même avis resteraient bloqués aussi).
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("products.id", ondelete="SET NULL"), nullable=True
    )
    review_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("reviews.id", ondelete="SET NULL"), nullable=True
    )
    reason: Mapped[str] = mapped_column(String(300), nullable=False)
    status: Mapped[ReportStatus] = mapped_column(
        SAEnum(ReportStatus, name="report_status", values_callable=lambda enum: [e.value for e in enum]),
        default=ReportStatus.PENDING,
        nullable=False,
    )
    # Note admin optionnelle, remplie à la résolution (rejet ou action).
    admin_note: Mapped[str | None] = mapped_column(String(300), nullable=True)
