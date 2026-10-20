"""Merkezi yuvarlama kuralları birim testleri."""

from __future__ import annotations

from decimal import Decimal
import pytest

from teklif_sablonu.domain.rounding import round_currency, round_quantity


def test_round_currency_half_up() -> None:
    """ROUND_HALF_UP kuralına göre 0.005 yukarı, 0.004 aşağı yuvarlanmalıdır."""
    assert round_currency(Decimal("10.005")) == Decimal("10.01")
    assert round_currency(Decimal("10.004")) == Decimal("10.00")
    assert round_currency(Decimal("10.005001")) == Decimal("10.01")
    assert round_currency(Decimal("10.004999")) == Decimal("10.00")


def test_round_currency_types() -> None:
    """String, float ve int girdiler güvenle Decimal olarak yuvarlanmalıdır."""
    assert round_currency("12.345") == Decimal("12.35")
    assert round_currency(100) == Decimal("100.00")
    assert round_currency("0") == Decimal("0.00")


def test_round_currency_negative() -> None:
    """Negatif sayılarda da simetrik ROUND_HALF_UP çalışmalıdır."""
    assert round_currency(Decimal("-10.005")) == Decimal("-10.01")
    assert round_currency(Decimal("-10.004")) == Decimal("-10.00")


def test_round_quantity() -> None:
    """Miktar yuvarlaması 2 ondalık basamak üretmelidir."""
    assert round_quantity(Decimal("15.5")) == Decimal("15.50")
    assert round_quantity(Decimal("15.555")) == Decimal("15.56")
    assert round_quantity(Decimal("15")) == Decimal("15.00")
    assert round_quantity("15.555") == Decimal("15.56")
    assert round_quantity(15.555) == Decimal("15.56")
