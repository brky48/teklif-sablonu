"""Teklif hesaplama motoru birim testleri."""

from __future__ import annotations

from decimal import Decimal
import pytest

from teklif_sablonu.domain.calculator import (
    DiscountExceedsTotalError,
    calculate_item,
    calculate_offer,
    calculate_offer_totals,
)
from teklif_sablonu.domain.enums import DiscountType
from teklif_sablonu.domain.models import Offer, OfferItem


def test_calculate_item_standard() -> None:
    """İskonto ve KDV olmadan standart satır toplamı: Miktar × Birim Fiyat."""
    item = OfferItem(
        description="Ürün A",
        quantity=Decimal("10"),
        unit_price=Decimal("150.50"),
    )
    calc = calculate_item(item)
    assert calc.line_total == Decimal("1505.00")
    assert calc.discount_amount == Decimal("0.00")
    assert calc.discounted_total == Decimal("1505.00")
    assert calc.vat_amount == Decimal("0.00")
    assert calc.total_with_vat == Decimal("1505.00")


def test_calculate_item_rate_discount() -> None:
    """Oran iskontosu doğru uygulanmalıdır (%12,50)."""
    item = OfferItem(
        description="Ürün B",
        quantity=Decimal("10"),
        unit_price=Decimal("100.00"),
        discount_type=DiscountType.RATE,
        discount_value=Decimal("12.50"),
    )
    calc = calculate_item(item, discount_enabled=True)
    assert calc.line_total == Decimal("1000.00")
    assert calc.discount_amount == Decimal("125.00")
    assert calc.discounted_total == Decimal("875.00")


def test_calculate_item_amount_discount() -> None:
    """Sabit tutar iskontosu doğru uygulanmalıdır."""
    item = OfferItem(
        description="Ürün C",
        quantity=Decimal("5"),
        unit_price=Decimal("200.00"),
        discount_type=DiscountType.AMOUNT,
        discount_value=Decimal("150.00"),
    )
    calc = calculate_item(item, discount_enabled=True)
    assert calc.line_total == Decimal("1000.00")
    assert calc.discount_amount == Decimal("150.00")
    assert calc.discounted_total == Decimal("850.00")


def test_calculate_item_discount_exceeds_total_error() -> None:
    """İskonto tutarı satır toplamını aşarsa DiscountExceedsTotalError fırlatılmalıdır."""
    item = OfferItem(
        description="Ürün D",
        quantity=Decimal("1"),
        unit_price=Decimal("50.00"),
        discount_type=DiscountType.AMOUNT,
        discount_value=Decimal("60.00"),
    )
    with pytest.raises(DiscountExceedsTotalError):
        calculate_item(item, discount_enabled=True)


def test_calculate_item_vat_without_discount() -> None:
    """Şartname Bölüm 8.3: Matrah 100 ve KDV %10 ise sonuç 110 olur."""
    item = OfferItem(
        description="Ürün E",
        quantity=Decimal("1"),
        unit_price=Decimal("100.00"),
    )
    calc = calculate_item(item, vat_rate=Decimal("10"), vat_enabled=True)
    assert calc.line_total == Decimal("100.00")
    assert calc.vat_amount == Decimal("10.00")
    assert calc.total_with_vat == Decimal("110.00")


def test_calculate_item_vat_with_discount() -> None:
    """Şartname Bölüm 8.3: İskontolu matrah 90 ve KDV %10 ise sonuç 99 olur."""
    item = OfferItem(
        description="Ürün F",
        quantity=Decimal("1"),
        unit_price=Decimal("100.00"),
        discount_type=DiscountType.AMOUNT,
        discount_value=Decimal("10.00"),
    )
    calc = calculate_item(
        item,
        vat_rate=Decimal("10"),
        vat_enabled=True,
        discount_enabled=True,
    )
    assert calc.line_total == Decimal("100.00")
    assert calc.discount_amount == Decimal("10.00")
    assert calc.discounted_total == Decimal("90.00")
    assert calc.vat_amount == Decimal("9.00")
    assert calc.total_with_vat == Decimal("99.00")


def test_calculate_offer_totals_multiple_items() -> None:
    """Genel toplamlar satır bazında yuvarlanmış tutarların toplamı olmalıdır."""
    items = [
        OfferItem(
            description="Ürün 1",
            quantity=Decimal("2"),
            unit_price=Decimal("50.00"),  # Toplam: 100.00
            discount_type=DiscountType.RATE,
            discount_value=Decimal("10.00"),  # İskonto: 10.00, İskontolu: 90.00
        ),
        OfferItem(
            description="Ürün 2",
            quantity=Decimal("1"),
            unit_price=Decimal("200.00"),  # Toplam: 200.00
            discount_type=DiscountType.AMOUNT,
            discount_value=Decimal("50.00"),  # İskonto: 50.00, İskontolu: 150.00
        ),
        OfferItem(),  # Tamamen boş satır - hesaplamaya etki etmemeli
    ]

    item_calcs, totals = calculate_offer_totals(
        items,
        vat_rate=Decimal("20"),
        vat_enabled=True,
        discount_enabled=True,
    )

    assert len(item_calcs) == 2

    # Ürün 1: line=100.00, disc=10.00, disc_tot=90.00, vat=18.00, tot_vat=108.00
    # Ürün 2: line=200.00, disc=50.00, disc_tot=150.00, vat=30.00, tot_vat=180.00
    assert totals.subtotal == Decimal("300.00")
    assert totals.total_discount == Decimal("60.00")
    assert totals.discounted_subtotal == Decimal("240.00")
    assert totals.total_vat == Decimal("48.00")
    assert totals.grand_total == Decimal("288.00")

    # Kesin kural doğrulaması: Genel toplam tam olarak satırların toplamına eşit
    assert totals.subtotal == sum(c.line_total for c in item_calcs)
    assert totals.total_discount == sum(c.discount_amount for c in item_calcs)
    assert totals.discounted_subtotal == sum(c.discounted_total for c in item_calcs)
    assert totals.total_vat == sum(c.vat_amount for c in item_calcs)
    assert totals.grand_total == sum(c.total_with_vat for c in item_calcs)


def test_calculate_offer_helper() -> None:
    """calculate_offer yardımcı fonksiyonu Offer modeliyle doğru çalışmalıdır."""
    offer = Offer(
        vat_enabled=True,
        vat_rate=Decimal("10"),
        discount_enabled=False,
        items=[
            OfferItem(
                description="Test",
                quantity=Decimal("5"),
                unit_price=Decimal("10.00"),
            )
        ],
    )
    calcs, totals = calculate_offer(offer)
    assert totals.subtotal == Decimal("50.00")
    assert totals.total_vat == Decimal("5.00")
    assert totals.grand_total == Decimal("55.00")
