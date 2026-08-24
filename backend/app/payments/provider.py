"""Abstract payment provider interface.

Only CashOnDeliveryProvider exists today — cash changes hands at delivery
time, off-platform, so "initiating" it is pure bookkeeping (see
service.mark_paid, called once every sub-order of an order is delivered).
NimbaPayProvider slots in here — implementing the same initiate() contract,
plus a webhook-driven confirm step once one exists — as soon as merchant API
access/docs are obtained from GuiM/BCRG (see README.md "Paiement NimbaPay").
Nothing outside this module needs to change when that happens: add the enum
value to PaymentMethod (app/orders/models.py) and register the provider in
_PROVIDERS below.
"""

from abc import ABC, abstractmethod

from app.orders.models import Order, PaymentMethod
from app.payments.models import PaymentStatus


class PaymentProvider(ABC):
    @abstractmethod
    async def initiate(self, order: Order) -> tuple[PaymentStatus, str | None]:
        """Start payment for an order. Returns (initial status, provider reference)."""


class CashOnDeliveryProvider(PaymentProvider):
    async def initiate(self, order: Order) -> tuple[PaymentStatus, str | None]:
        return PaymentStatus.PENDING, None


_PROVIDERS: dict[PaymentMethod, PaymentProvider] = {
    PaymentMethod.CASH_ON_DELIVERY: CashOnDeliveryProvider(),
}


def get_provider(method: PaymentMethod) -> PaymentProvider:
    return _PROVIDERS[method]
