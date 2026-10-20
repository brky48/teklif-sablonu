"""Domain modellerinde kullanılan numaralandırma (Enum) ve sabit tanımları."""

from __future__ import annotations

from enum import Enum


class CurrencyCode(str, Enum):
    """Teklif genelinde geçerli para birimi."""

    TRY = "TRY"
    USD = "USD"
    EUR = "EUR"

    @property
    def symbol(self) -> str:
        symbols = {
            CurrencyCode.TRY: "₺",
            CurrencyCode.USD: "$",
            CurrencyCode.EUR: "€",
        }
        return symbols.get(self, self.value)


class QuantityUnit(str, Enum):
    """Teklif genelinde geçerli miktar birimi."""

    PIECE = "piece"
    LITRE = "litre"

    @property
    def label_tr(self) -> str:
        labels = {
            QuantityUnit.PIECE: "Adet",
            QuantityUnit.LITRE: "Litre",
        }
        return labels.get(self, self.value)

    @property
    def column_header(self) -> str:
        return f"Miktar ({self.label_tr})"


class DiscountType(str, Enum):
    """Satır bazlı iskonto türü."""

    NONE = "none"
    RATE = "rate"
    AMOUNT = "amount"

    @property
    def label_tr(self) -> str:
        labels = {
            DiscountType.NONE: "Yok",
            DiscountType.RATE: "Oran",
            DiscountType.AMOUNT: "Miktar",
        }
        return labels.get(self, self.value)


class ColumnKey(str, Enum):
    """Şartname Bölüm 6.2'deki 11 sabit sütun sırası."""

    PRODUCT_CODE = "product_code"
    DESCRIPTION = "description"
    QUANTITY = "quantity"
    PALLET = "pallet"
    UNIT_PRICE = "unit_price"
    DISCOUNT_TYPE = "discount_type"
    DISCOUNT_AMOUNT = "discount_amount"
    VAT = "vat"
    TOTAL_AMOUNT = "total_amount"
    TOTAL_DISCOUNTED = "total_discounted"
    TOTAL_WITH_VAT = "total_with_vat"

    @property
    def label_tr(self) -> str:
        labels = {
            ColumnKey.PRODUCT_CODE: "Ürün Kodu",
            ColumnKey.DESCRIPTION: "Ürün Açıklaması",
            ColumnKey.QUANTITY: "Miktar",
            ColumnKey.PALLET: "Palet",
            ColumnKey.UNIT_PRICE: "Birim Fiyat",
            ColumnKey.DISCOUNT_TYPE: "İskonto Türü",
            ColumnKey.DISCOUNT_AMOUNT: "İskonto Miktarı",
            ColumnKey.VAT: "KDV",
            ColumnKey.TOTAL_AMOUNT: "Toplam Tutar",
            ColumnKey.TOTAL_DISCOUNTED: "Toplam Tutar (İskontolu)",
            ColumnKey.TOTAL_WITH_VAT: "Toplam Tutar (KDV Dahil)",
        }
        return labels.get(self, self.value)

    @property
    def is_mandatory(self) -> bool:
        """Şartname Bölüm 6.3'e göre zorunlu ve kapatılamaz sütunlar."""
        return self in (
            ColumnKey.DESCRIPTION,
            ColumnKey.QUANTITY,
            ColumnKey.UNIT_PRICE,
            ColumnKey.TOTAL_AMOUNT,
        )


# Sabit sütun sırası (Bölüm 6.2)
FIXED_COLUMN_ORDER: list[ColumnKey] = [
    ColumnKey.PRODUCT_CODE,
    ColumnKey.DESCRIPTION,
    ColumnKey.QUANTITY,
    ColumnKey.PALLET,
    ColumnKey.UNIT_PRICE,
    ColumnKey.DISCOUNT_TYPE,
    ColumnKey.DISCOUNT_AMOUNT,
    ColumnKey.VAT,
    ColumnKey.TOTAL_AMOUNT,
    ColumnKey.TOTAL_DISCOUNTED,
    ColumnKey.TOTAL_WITH_VAT,
]


class SectionKey(str, Enum):
    """Şartname Bölüm 7.6'daki ticari koşul bölümleri."""

    DELIVERY_ADDRESS = "delivery_address"
    ORDER_NOTIFICATION = "order_notification"
    DELIVERY_METHOD = "delivery_method"
    PAYMENT_TERMS = "payment_terms"
    STORAGE_CONDITIONS = "storage_conditions"
    ADDITIONAL_NOTES = "additional_notes"

    @property
    def label_tr(self) -> str:
        labels = {
            SectionKey.DELIVERY_ADDRESS: "Teslimat Adresi",
            SectionKey.ORDER_NOTIFICATION: "Sipariş Bildirimi",
            SectionKey.DELIVERY_METHOD: "Teslim Şekli",
            SectionKey.PAYMENT_TERMS: "Ödeme Şartları",
            SectionKey.STORAGE_CONDITIONS: "Depolama Şartları",
            SectionKey.ADDITIONAL_NOTES: "Ek Alan",
        }
        return labels.get(self, self.value)

    @property
    def max_chars(self) -> int:
        """Karakter sınırı (Bölüm 7.6)."""
        if self == SectionKey.ADDITIONAL_NOTES:
            return 10000
        return 3000

    @property
    def is_rich_text(self) -> bool:
        return self == SectionKey.ADDITIONAL_NOTES
