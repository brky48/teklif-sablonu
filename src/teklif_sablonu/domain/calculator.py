"""UI ve veritabanından bağımsız teklif hesaplama motoru."""

from __future__ import annotations

from decimal import Decimal

from teklif_sablonu.domain.enums import DiscountType
from teklif_sablonu.domain.models import (
    Offer,
    OfferItem,
    OfferItemCalculation,
    OfferTotals,
)
from teklif_sablonu.domain.rounding import round_currency


class CalculationError(ValueError):
    """Hesaplama sırasında oluşan kural hatası."""


class DiscountExceedsTotalError(CalculationError):
    """İskonto tutarının satır toplamını aştığı durum."""


def calculate_item(
    item: OfferItem,
    *,
    vat_rate: Decimal = Decimal("0"),
    vat_enabled: bool = False,
    discount_enabled: bool = False,
) -> OfferItemCalculation:
    """Tek bir ürün satırının hesaplanmış tutarlarını döndürür.

    Tüm hesaplanan tutarlar 2 ondalık basamağa ROUND_HALF_UP ile yuvarlanır.
    """
    # 1. Satır Toplamı (Bölüm 8.1): Miktar × Birim Fiyat
    qty = item.quantity if item.quantity is not None else Decimal("0")
    price = item.unit_price if item.unit_price is not None else Decimal("0")
    raw_line_total = qty * price
    line_total = round_currency(raw_line_total)

    # 2. İskonto (Bölüm 8.2)
    discount_amount = Decimal("0.00")
    if discount_enabled and item.discount_type != DiscountType.NONE:
        disc_val = item.discount_value if item.discount_value is not None else Decimal("0")
        if item.discount_type == DiscountType.RATE:
            # Oran iskontosu: line_total × (oran / 100)
            discount_amount = round_currency(line_total * (disc_val / Decimal("100")))
        elif item.discount_type == DiscountType.AMOUNT:
            # Sabit tutar iskontosu
            discount_amount = round_currency(disc_val)

        # Doğrulama: İskonto satır toplamını aşamaz
        if discount_amount > line_total:
            raise DiscountExceedsTotalError(
                f"İskonto tutarı ({discount_amount}) satır toplamını ({line_total}) aşamaz."
            )

    discounted_total = line_total - discount_amount

    # 3. KDV dahil toplam (Bölüm 8.3)
    vat_amount = Decimal("0.00")
    base = discounted_total if discount_enabled else line_total

    if vat_enabled and vat_rate is not None and vat_rate > Decimal("0"):
        vat_amount = round_currency(base * (vat_rate / Decimal("100")))

    total_with_vat = base + vat_amount

    return OfferItemCalculation(
        line_total=line_total,
        discount_amount=discount_amount,
        discounted_total=discounted_total,
        vat_amount=vat_amount,
        total_with_vat=total_with_vat,
    )


def calculate_offer_totals(
    items: list[OfferItem],
    *,
    vat_rate: Decimal = Decimal("0"),
    vat_enabled: bool = False,
    discount_enabled: bool = False,
) -> tuple[list[OfferItemCalculation], OfferTotals]:
    """Bir teklifteki tüm geçerli satırları ve genel toplam özetini hesaplar.

    Şartname Bölüm 8.5 & Kesinleşmiş Karar:
    Genel toplamlar, kullanıcıya gösterilen iki ondalık basamağa yuvarlanmış
    satır tutarlarının toplamı üzerinden üretilir.
    """
    item_calcs: list[OfferItemCalculation] = []

    subtotal = Decimal("0.00")
    total_discount = Decimal("0.00")
    discounted_subtotal = Decimal("0.00")
    total_vat = Decimal("0.00")
    grand_total = Decimal("0.00")

    for item in items:
        # Tamamen boş satırları hesaplamaya dahil etme
        if item.is_empty():
            continue

        calc = calculate_item(
            item,
            vat_rate=vat_rate,
            vat_enabled=vat_enabled,
            discount_enabled=discount_enabled,
        )
        item_calcs.append(calc)

        subtotal += calc.line_total
        total_discount += calc.discount_amount
        discounted_subtotal += calc.discounted_total
        total_vat += calc.vat_amount
        grand_total += calc.total_with_vat

    totals = OfferTotals(
        subtotal=round_currency(subtotal),
        total_discount=round_currency(total_discount),
        discounted_subtotal=round_currency(discounted_subtotal),
        total_vat=round_currency(total_vat),
        grand_total=round_currency(grand_total),
    )

    return item_calcs, totals


def calculate_offer(offer: Offer) -> tuple[list[OfferItemCalculation], OfferTotals]:
    """Offer nesnesinin satır hesaplamalarını ve genel toplamlarını döndürür."""
    return calculate_offer_totals(
        offer.items,
        vat_rate=offer.vat_rate,
        vat_enabled=offer.vat_enabled,
        discount_enabled=offer.discount_enabled,
    )
