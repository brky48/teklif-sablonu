"""Domain modellerinde kullanılan numaralandırma (Enum) ve sabit tanımları."""

from __future__ import annotations

from enum import Enum


class DocumentLanguage(str, Enum):
    """Teklif belge dili: TR veya EN."""

    TR = "tr"
    EN = "en"

    @property
    def label(self) -> str:
        return "TR" if self == DocumentLanguage.TR else "EN"


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
        return self.label(DocumentLanguage.TR)

    def label(self, lang: DocumentLanguage | str = DocumentLanguage.TR) -> str:
        is_en = (lang == DocumentLanguage.EN or lang == "en")
        if self == QuantityUnit.LITRE:
            return "Liter" if is_en else "Litre"
        return "Piece" if is_en else "Adet"

    @property
    def column_header(self) -> str:
        return self.get_column_header(DocumentLanguage.TR)

    def get_column_header(self, lang: DocumentLanguage | str = DocumentLanguage.TR) -> str:
        is_en = (lang == DocumentLanguage.EN or lang == "en")
        lbl = self.label(lang)
        return f"Quantity ({lbl})" if is_en else f"Miktar ({lbl})"


class DiscountType(str, Enum):
    """Satır bazlı iskonto türü."""

    NONE = "none"
    RATE = "rate"
    AMOUNT = "amount"

    @property
    def label_tr(self) -> str:
        return self.label(DocumentLanguage.TR)

    def label(self, lang: DocumentLanguage | str = DocumentLanguage.TR) -> str:
        is_en = (lang == DocumentLanguage.EN or lang == "en")
        if self == DiscountType.RATE:
            return "Rate" if is_en else "Oran"
        elif self == DiscountType.AMOUNT:
            return "Amount" if is_en else "Miktar"
        return "None" if is_en else "Yok"


class PageOrientation(str, Enum):
    """Sayfa yönü seçimi: Otomatik, Dikey veya Yatay."""

    AUTO = "auto"
    PORTRAIT = "portrait"
    LANDSCAPE = "landscape"

    @property
    def label_tr(self) -> str:
        labels = {
            PageOrientation.AUTO: "Otomatik",
            PageOrientation.PORTRAIT: "Dikey",
            PageOrientation.LANDSCAPE: "Yatay",
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
        return self.label(DocumentLanguage.TR)

    def label(self, lang: DocumentLanguage | str = DocumentLanguage.TR) -> str:
        is_en = (lang == DocumentLanguage.EN or lang == "en")
        if not is_en:
            labels_tr = {
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
            return labels_tr.get(self, self.value)

        labels_en = {
            ColumnKey.PRODUCT_CODE: "Product Code",
            ColumnKey.DESCRIPTION: "Description",
            ColumnKey.QUANTITY: "Quantity",
            ColumnKey.PALLET: "Pallet",
            ColumnKey.UNIT_PRICE: "Unit Price",
            ColumnKey.DISCOUNT_TYPE: "Discount Type",
            ColumnKey.DISCOUNT_AMOUNT: "Discount",
            ColumnKey.VAT: "VAT",
            ColumnKey.TOTAL_AMOUNT: "Total Amount",
            ColumnKey.TOTAL_DISCOUNTED: "Discounted Total",
            ColumnKey.TOTAL_WITH_VAT: "Total (Incl. VAT)",
        }
        return labels_en.get(self, self.value)

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
        return self.label(DocumentLanguage.TR)

    def label(self, lang: DocumentLanguage | str = DocumentLanguage.TR) -> str:
        is_en = (lang == DocumentLanguage.EN or lang == "en")
        if not is_en:
            labels_tr = {
                SectionKey.DELIVERY_ADDRESS: "Teslimat Adresi",
                SectionKey.ORDER_NOTIFICATION: "Sipariş Bildirimi",
                SectionKey.DELIVERY_METHOD: "Teslim Şekli",
                SectionKey.PAYMENT_TERMS: "Ödeme Şartları",
                SectionKey.STORAGE_CONDITIONS: "Depolama Şartları",
                SectionKey.ADDITIONAL_NOTES: "Ek Alan",
            }
            return labels_tr.get(self, self.value)

        labels_en = {
            SectionKey.DELIVERY_ADDRESS: "Delivery Address",
            SectionKey.ORDER_NOTIFICATION: "Order Notification",
            SectionKey.DELIVERY_METHOD: "Delivery Method",
            SectionKey.PAYMENT_TERMS: "Payment Terms",
            SectionKey.STORAGE_CONDITIONS: "Storage Conditions",
            SectionKey.ADDITIONAL_NOTES: "Additional Notes",
        }
        return labels_en.get(self, self.value)

    @property
    def max_chars(self) -> int:
        """Karakter sınırı (Bölüm 7.6)."""
        if self == SectionKey.ADDITIONAL_NOTES:
            return 10000
        return 3000

    @property
    def is_rich_text(self) -> bool:
        return self == SectionKey.ADDITIONAL_NOTES
