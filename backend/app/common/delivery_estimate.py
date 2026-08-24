"""Rule-based delivery estimate — no real logistics tracking (no carrier
transit-time data, no warehouse/sorting network like a Wildberries-style
operation would have). Instead: the vendor's own stated preparation time
(Vendor.preparation_days) plus a coarse zone heuristic, since zones are
free-text (Vendor.zone, Address.zone — no structured commune/city list
exists anywhere in the app to compare against precisely). Good enough to
give the buyer a rough "aujourd'hui / demain / après-demain" expectation;
not a promise of a specific carrier SLA.
"""

from dataclasses import dataclass
from datetime import date, timedelta

# Le jour même si la zone de l'acheteur correspond à celle du vendeur, sinon
# un jour de trajet de plus par défaut. Toutes les zones actuellement
# saisies dans l'app sont des quartiers de Conakry, donc "différent" veut
# dire "pas forcément à côté", pas "une autre région" — un jour reste une
# hypothèse raisonnable tant qu'il n'y a pas de vraie donnée de trajet.
_SAME_ZONE_TRANSIT_DAYS = 0
_DEFAULT_TRANSIT_DAYS = 1


def _normalize(zone: str | None) -> str | None:
    if not zone:
        return None
    normalized = zone.strip().lower()
    return normalized or None


def _is_same_zone(vendor_zone: str | None, buyer_zone: str | None) -> bool:
    vz, bz = _normalize(vendor_zone), _normalize(buyer_zone)
    if vz is None or bz is None:
        return False
    # Comparaison souple (égalité ou inclusion) : delivery_zone peut être un
    # texte plus long que le simple nom de zone du vendeur (ex. "Point ABC —
    # Kaloum" pour une livraison en point de retrait, voir AddressForm.vue
    # côté frontend), donc une égalité stricte manquerait des correspondances
    # évidentes.
    return vz == bz or vz in bz or bz in vz


@dataclass(frozen=True)
class DeliveryEstimate:
    min_date: date
    max_date: date


def estimate_delivery_window(
    *, vendor_zone: str | None, buyer_zone: str | None, preparation_days: int, from_date: date
) -> DeliveryEstimate:
    transit_days = _SAME_ZONE_TRANSIT_DAYS if _is_same_zone(vendor_zone, buyer_zone) else _DEFAULT_TRANSIT_DAYS
    min_days = max(preparation_days, 0) + transit_days
    return DeliveryEstimate(
        min_date=from_date + timedelta(days=min_days),
        max_date=from_date + timedelta(days=min_days + 1),
    )
