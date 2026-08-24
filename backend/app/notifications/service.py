"""Order notifications: an in-app entry (persisted + pushed live over
WebSocket, see ws_manager.py) plus, for status changes, an email to the
buyer — both best-effort side effects of the action that triggered them
(placing an order, a vendor moving a sub-order forward).

SMS is on the roadmap (cahier des charges §4.1) but no SMS gateway is
integrated yet — there is no provider account for the Guinean market at
time of writing, and phone is the one field every account is guaranteed to
have (email is optional at buyer signup, see app/auth/service.py), so email
alone won't reach every buyer. The in-app channel doesn't have that gap —
every account can see its own notification feed — so it's the primary
channel now; email is a secondary nudge, silently skipped when the buyer
has no email on file.
"""

import logging
import smtplib
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.email import send_email
from app.notifications import repository
from app.notifications.models import Notification, NotificationType
from app.notifications.ws_manager import manager as ws_manager
from app.orders.models import OrderStatus, SubOrder
from app.users.models import User

logger = logging.getLogger(__name__)

_STATUS_LABELS = {
    OrderStatus.CONFIRMED: "confirmée",
    OrderStatus.PREPARING: "en préparation",
    OrderStatus.SHIPPED: "expédiée",
    OrderStatus.ARRIVED_AT_PICKUP_POINT: "arrivée à votre point de retrait",
    OrderStatus.DELIVERED: "livrée",
    OrderStatus.CANCELLED: "annulée",
}


async def _persist_and_push(
    db: AsyncSession, *, user_id: uuid.UUID, type_: NotificationType, title: str, body: str, order_id: uuid.UUID | None
) -> Notification:
    notification = await repository.create(
        db, user_id=user_id, type=type_, title=title, body=body, order_id=order_id
    )
    await db.commit()
    await db.refresh(notification)
    try:
        await ws_manager.send_to_user(
            user_id,
            {
                "id": str(notification.id),
                "type": notification.type.value,
                "title": notification.title,
                "body": notification.body,
                "order_id": str(notification.order_id) if notification.order_id else None,
                "read_at": None,
                "created_at": notification.created_at.isoformat(),
            },
        )
    except Exception:  # noqa: BLE001 - la notification est déjà persistée, un échec de push ne doit rien annuler
        logger.warning("Échec de push WebSocket pour la notification %s", notification.id, exc_info=True)
    return notification


async def notify_order_received(
    db: AsyncSession, *, vendor_user_id: uuid.UUID, shop_name: str, order_id: uuid.UUID, item_count: int, amount: int
) -> None:
    formatted_amount = f"{amount:,}".replace(",", " ")
    await _persist_and_push(
        db,
        user_id=vendor_user_id,
        type_=NotificationType.ORDER_RECEIVED,
        title="Nouvelle commande reçue",
        body=(
            f"Vous avez reçu une nouvelle commande pour « {shop_name} » "
            f"({item_count} article(s), {formatted_amount} GNF)."
        ),
        order_id=order_id,
    )


async def notify_sub_order_status_changed(db: AsyncSession, buyer: User, sub_order: SubOrder) -> None:
    label = _STATUS_LABELS.get(sub_order.status)
    if label is None:
        return

    await _persist_and_push(
        db,
        user_id=buyer.id,
        type_=NotificationType.ORDER_STATUS_CHANGED,
        title=f"Commande {label}",
        body=f"Votre commande chez « {sub_order.shop_name} » est maintenant {label}.",
        order_id=sub_order.order_id,
    )

    if not buyer.email:
        return
    try:
        await send_email(
            buyer.email,
            f"Votre commande chez {sub_order.shop_name} est {label}",
            f"Bonjour,\n\nVotre commande chez « {sub_order.shop_name} » est maintenant {label}.\n\n"
            "Vous pouvez suivre son statut dans votre espace « Mes commandes ».",
        )
    except (OSError, smtplib.SMTPException):
        logger.warning("Échec d'envoi de la notification de statut pour la sous-commande %s", sub_order.id)
