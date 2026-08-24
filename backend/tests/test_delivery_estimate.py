"""Unit tests for the rule-based delivery estimate (no DB needed — pure
function). See app/common/delivery_estimate.py for the rationale."""

from datetime import date

from app.common.delivery_estimate import estimate_delivery_window


def test_same_zone_ships_same_day_plus_preparation() -> None:
    result = estimate_delivery_window(
        vendor_zone="Kaloum", buyer_zone="Kaloum", preparation_days=1, from_date=date(2026, 8, 10)
    )

    assert result.min_date == date(2026, 8, 11)
    assert result.max_date == date(2026, 8, 12)


def test_different_zone_adds_a_transit_day() -> None:
    result = estimate_delivery_window(
        vendor_zone="Kaloum", buyer_zone="Ratoma", preparation_days=1, from_date=date(2026, 8, 10)
    )

    assert result.min_date == date(2026, 8, 12)
    assert result.max_date == date(2026, 8, 13)


def test_zone_match_is_case_and_whitespace_insensitive() -> None:
    result = estimate_delivery_window(
        vendor_zone="  Kaloum ", buyer_zone="kaloum", preparation_days=0, from_date=date(2026, 8, 10)
    )

    assert result.min_date == date(2026, 8, 10)


def test_zone_match_handles_pickup_point_composite_zone_string() -> None:
    # Voir AddressForm.vue côté frontend : delivery_zone pour un point de
    # retrait est "Nom du point — Zone", pas juste la zone seule.
    result = estimate_delivery_window(
        vendor_zone="Kaloum",
        buyer_zone="Point ABC — Kaloum",
        preparation_days=0,
        from_date=date(2026, 8, 10),
    )

    assert result.min_date == date(2026, 8, 10)


def test_unknown_zone_falls_back_to_default_transit() -> None:
    result = estimate_delivery_window(
        vendor_zone=None, buyer_zone=None, preparation_days=1, from_date=date(2026, 8, 10)
    )

    assert result.min_date == date(2026, 8, 12)
    assert result.max_date == date(2026, 8, 13)


def test_negative_preparation_days_is_clamped_to_zero() -> None:
    result = estimate_delivery_window(
        vendor_zone="Kaloum", buyer_zone="Kaloum", preparation_days=-3, from_date=date(2026, 8, 10)
    )

    assert result.min_date == date(2026, 8, 10)
