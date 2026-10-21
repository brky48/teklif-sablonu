"""Domain veri modelleri ve değer nesneleri."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal

from teklif_sablonu.domain.enums import (
    FIXED_COLUMN_ORDER,
    ColumnKey,
    CurrencyCode,
    DiscountType,
    DocumentLanguage,
    PageOrientation,
    QuantityUnit,
    SectionKey,
)


@dataclass
class OfferItem:
    """Teklif içindeki tek bir ürün satırı."""

    id: int | None = None
    offer_id: int | None = None
    position: int = 0
    product_code: str = ""
    description: str = ""
    quantity: Decimal = Decimal("0")
    pallet: Decimal | None = None
    unit_price: Decimal = Decimal("0")
    discount_type: DiscountType = DiscountType.NONE
    discount_value: Decimal = Decimal("0")

    def is_empty(self) -> bool:
        """Satır tamamen boş mu kontrol eder.

        Şartname Bölüm 6.6: Tamamen boş ürün satırları yok sayılır.
        """
        has_code = bool(self.product_code and self.product_code.strip())
        has_desc = bool(self.description and self.description.strip())
        has_qty = self.quantity is not None and self.quantity > Decimal("0")
        has_pallet = self.pallet is not None and self.pallet > Decimal("0")
        has_price = self.unit_price is not None and self.unit_price > Decimal("0")
        has_discount = (
            self.discount_type != DiscountType.NONE
            and self.discount_value is not None
            and self.discount_value > Decimal("0")
        )
        return not (
            has_code
            or has_desc
            or has_qty
            or has_pallet
            or has_price
            or has_discount
        )

    def is_partially_filled(self) -> bool:
        """Satır kısmen doldurulmuş mu kontrol eder."""
        return not self.is_empty() and not self.is_complete()

    def is_complete(self) -> bool:
        """Satırın zorunlu alanları (Açıklama, Miktar > 0, Birim Fiyat >= 0) dolu mu?"""
        has_desc = bool(self.description and self.description.strip())
        has_qty = self.quantity is not None and self.quantity > Decimal("0")
        has_price = self.unit_price is not None and self.unit_price >= Decimal("0")
        return has_desc and has_qty and has_price


@dataclass
class OfferSection:
    """Teklif altındaki bir ticari koşul bölümü."""

    id: int | None = None
    offer_id: int | None = None
    section_key: SectionKey = SectionKey.DELIVERY_ADDRESS
    enabled: bool = False
    text: str = ""
    rich_text: bool = False
    position: int = 0


@dataclass(frozen=True)
class OfferItemCalculation:
    """Bir ürün satırının hesaplanmış tutarları (tümü 2 basamağa yuvarlanmış)."""

    line_total: Decimal
    discount_amount: Decimal
    discounted_total: Decimal
    vat_amount: Decimal
    total_with_vat: Decimal


@dataclass(frozen=True)
class OfferTotals:
    """Teklifin genel toplam özeti (tümü 2 basamağa yuvarlanmış).

    Şartname Bölüm 8.5:
    - Ara Toplam: her ürünün line_total toplamı (daima gösterilir).
    - Toplam İskonto: iskonto etkinse satır iskonto tutarlarının toplamı.
    - İskonto Sonrası Ara Toplam: iskonto etkinse satırların iskontolu toplamları.
    - Toplam KDV: KDV etkinse satır bazında oluşan KDV tutarlarının toplamı.
    - KDV Dâhil Genel Toplam: KDV etkinse satırların KDV dahil toplamı.
    """

    subtotal: Decimal
    total_discount: Decimal
    discounted_subtotal: Decimal
    total_vat: Decimal
    grand_total: Decimal


def default_selected_columns() -> list[ColumnKey]:
    """Varsayılan olarak seçili gelen sütun listesi (Bölüm 6.2 ve 6.3)."""
    return [
        ColumnKey.PRODUCT_CODE,
        ColumnKey.DESCRIPTION,
        ColumnKey.QUANTITY,
        ColumnKey.PALLET,
        ColumnKey.UNIT_PRICE,
        ColumnKey.TOTAL_AMOUNT,
    ]


@dataclass
class Offer:
    """Bir teklifin tüm verilerini içeren ana domain modeli."""

    id: int | None = None
    offer_number: str = ""
    offer_date: date = field(default_factory=date.today)
    company_id: str = "endemiks_tarim"
    recipient_name: str = ""
    currency_code: CurrencyCode = CurrencyCode.TRY
    quantity_unit: QuantityUnit = QuantityUnit.PIECE
    vat_enabled: bool = False
    vat_rate: Decimal = Decimal("0")
    discount_enabled: bool = False
    brand_logo_visible: bool = False
    page_orientation: PageOrientation = PageOrientation.AUTO
    document_language: DocumentLanguage = DocumentLanguage.TR
    selected_columns: list[ColumnKey] = field(default_factory=default_selected_columns)
    items: list[OfferItem] = field(default_factory=list)
    sections: list[OfferSection] = field(default_factory=list)
    source_offer_id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def get_valid_items(self) -> list[OfferItem]:
        """Tamamen boş satırları hariç tutarak geçerli ürün satırlarını döndürür."""
        return [item for item in self.items if not item.is_empty()]

    def is_column_selected(self, column: ColumnKey) -> bool:
        return column in self.selected_columns
