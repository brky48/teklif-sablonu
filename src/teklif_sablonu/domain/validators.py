"""Domain girdi doğrulama kuralları modülü."""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal

from teklif_sablonu.config.settings import RECIPIENT_MAX_CHARS
from teklif_sablonu.domain.calculator import calculate_item
from teklif_sablonu.domain.enums import (
    FIXED_COLUMN_ORDER,
    ColumnKey,
    DiscountType,
    SectionKey,
)
from teklif_sablonu.domain.models import Offer, OfferItem, OfferSection


@dataclass(frozen=True)
class ValidationError:
    """Tek bir doğrulama hatasını temsil eder."""

    message: str
    field: str | None = None
    row_index: int | None = None

    def __str__(self) -> str:
        loc = []
        if self.row_index is not None:
            loc.append(f"Satır {self.row_index + 1}")
        if self.field:
            loc.append(f"Alan: {self.field}")
        prefix = f"[{' - '.join(loc)}] " if loc else ""
        return f"{prefix}{self.message}"


@dataclass
class ValidationResult:
    """Bir doğrulama işleminin sonucu."""

    errors: list[ValidationError]

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def raise_if_invalid(self) -> None:
        """Hata varsa toplu ValueError fırlatır."""
        if not self.is_valid:
            msg = "\n".join(str(e) for e in self.errors)
            raise ValueError(f"Teklif doğrulaması başarısız:\n{msg}")


_HTML_TAG_RE = re.compile(r"<[^>]+>")


def get_visible_text_length(text: str, is_rich_text: bool = False) -> int:
    """Metnin görünür karakter sayısını hesaplar (HTML etiketlerini hariç tutar)."""
    if not text:
        return 0
    if is_rich_text:
        plain_text = _HTML_TAG_RE.sub("", text)
        return len(plain_text)
    return len(text)


def _check_decimal_places(val: Decimal, max_places: int = 2) -> bool:
    """Ondalık basamak sayısının sınırı aşıp aşmadığını denetler."""
    val_str = format(val, "f")
    if "." in val_str:
        dec_part = val_str.split(".")[1].rstrip("0")
        return len(dec_part) <= max_places
    return True


def _check_integer_digits(val: Decimal, max_digits: int = 10) -> bool:
    """Tam kısmın basamak sayısını denetler."""
    val_str = format(val, "f")
    int_part = val_str.split(".")[0].lstrip("-")
    return len(int_part) <= max_digits


def validate_item(
    item: OfferItem,
    row_index: int = 0,
    *,
    discount_enabled: bool = False,
) -> list[ValidationError]:
    """Tek bir ürün satırını doğrular. Tamamen boş satırlar için hata üretilmez."""
    errors: list[ValidationError] = []

    if item.is_empty():
        return errors

    # 1. Ürün Kodu (isteğe bağlı, max 64 karakter)
    if item.product_code and len(item.product_code) > 64:
        errors.append(
            ValidationError(
                message="Ürün kodu en fazla 64 karakter olabilir.",
                field="product_code",
                row_index=row_index,
            )
        )

    # 2. Ürün Açıklaması (zorunlu, max 64 karakter)
    desc = item.description.strip() if item.description else ""
    if not desc:
        errors.append(
            ValidationError(
                message="Ürün açıklaması zorunludur.",
                field="description",
                row_index=row_index,
            )
        )
    elif len(item.description) > 64:
        errors.append(
            ValidationError(
                message="Ürün açıklaması en fazla 64 karakter olabilir.",
                field="description",
                row_index=row_index,
            )
        )

    # 3. Miktar (zorunlu, pozitif > 0, en fazla 2 ondalık)
    if item.quantity is None or item.quantity <= Decimal("0"):
        errors.append(
            ValidationError(
                message="Miktar sıfırdan büyük bir pozitif sayı olmalıdır.",
                field="quantity",
                row_index=row_index,
            )
        )
    elif not _check_decimal_places(item.quantity, 2):
        errors.append(
            ValidationError(
                message="Miktar en fazla 2 ondalık basamak içerebilir.",
                field="quantity",
                row_index=row_index,
            )
        )

    # 4. Palet (isteğe bağlı, pozitif > 0, en fazla 2 ondalık)
    if item.pallet is not None:
        if item.pallet <= Decimal("0"):
            errors.append(
                ValidationError(
                    message="Palet miktarı pozitif bir sayı olmalıdır.",
                    field="pallet",
                    row_index=row_index,
                )
            )
        elif not _check_decimal_places(item.pallet, 2):
            errors.append(
                ValidationError(
                    message="Palet miktarı en fazla 2 ondalık basamak içerebilir.",
                    field="pallet",
                    row_index=row_index,
                )
            )

    # 5. Birim Fiyat (zorunlu, negatif olamaz >= 0, en fazla 2 ondalık)
    if item.unit_price is None or item.unit_price < Decimal("0"):
        errors.append(
            ValidationError(
                message="Birim fiyat negatif olamaz.",
                field="unit_price",
                row_index=row_index,
            )
        )
    elif not _check_decimal_places(item.unit_price, 2):
        errors.append(
            ValidationError(
                message="Birim fiyat en fazla 2 ondalık basamak içerebilir.",
                field="unit_price",
                row_index=row_index,
            )
        )

    # 6. İskonto Doğrulaması (İskonto etkinse)
    if discount_enabled and item.discount_type != DiscountType.NONE:
        disc_val = item.discount_value if item.discount_value is not None else Decimal("0")
        if disc_val < Decimal("0"):
            errors.append(
                ValidationError(
                    message="İskonto değeri negatif olamaz.",
                    field="discount_value",
                    row_index=row_index,
                )
            )
        elif not _check_decimal_places(disc_val, 2):
            errors.append(
                ValidationError(
                    message="İskonto değeri en fazla 2 ondalık basamak içerebilir.",
                    field="discount_value",
                    row_index=row_index,
                )
            )

        if item.discount_type == DiscountType.RATE:
            if disc_val > Decimal("100"):
                errors.append(
                    ValidationError(
                        message="Oran iskontosu 0 ile 100 arasında olmalıdır.",
                        field="discount_value",
                        row_index=row_index,
                    )
                )
        elif item.discount_type == DiscountType.AMOUNT:
            if not _check_integer_digits(disc_val, 10):
                errors.append(
                    ValidationError(
                        message="Sabit iskonto tutarının tam kısmı en fazla 10 basamak olabilir.",
                        field="discount_value",
                        row_index=row_index,
                    )
                )
            # Sabit tutar satır toplamını aşamaz
            if item.quantity and item.unit_price and item.quantity > Decimal("0") and item.unit_price >= Decimal("0"):
                line_total = item.quantity * item.unit_price
                if disc_val > line_total:
                    errors.append(
                        ValidationError(
                            message=f"Sabit iskonto tutarı ({disc_val}) satır toplamını ({line_total}) aşamaz.",
                            field="discount_value",
                            row_index=row_index,
                        )
                    )

    return errors


def validate_section(section: OfferSection) -> list[ValidationError]:
    """Bir ticari koşul bölümünü doğrular."""
    errors: list[ValidationError] = []
    if not section.enabled:
        return errors

    max_len = section.section_key.max_chars
    vis_len = get_visible_text_length(section.text, section.rich_text)
    if vis_len > max_len:
        errors.append(
            ValidationError(
                message=f"{section.section_key.label_tr} alanı en fazla {max_len} karakter olabilir (Mevcut: {vis_len}).",
                field=section.section_key.value,
            )
        )
    return errors


def validate_offer(offer: Offer) -> ValidationResult:
    """Bir teklifin tüm verilerini iş ve şartname kurallarına göre doğrular."""
    errors: list[ValidationError] = []

    # 1. Alıcı adı uzunluğu (en fazla RECIPIENT_MAX_CHARS)
    if offer.recipient_name and len(offer.recipient_name) > RECIPIENT_MAX_CHARS:
        errors.append(
            ValidationError(
                message=f"Alıcı bilgisi en fazla {RECIPIENT_MAX_CHARS} karakter olabilir.",
                field="recipient_name",
            )
        )

    # 2. Şirket seçimi
    if not offer.company_id:
        errors.append(
            ValidationError(
                message="Teklif için bir şirket seçilmelidir.",
                field="company_id",
            )
        )

    # 3. KDV oranı denetimi
    if offer.vat_enabled:
        if offer.vat_rate is None or offer.vat_rate < Decimal("0"):
            errors.append(
                ValidationError(
                    message="KDV oranı negatif olamaz.",
                    field="vat_rate",
                )
            )
        elif not _check_decimal_places(offer.vat_rate, 2):
            errors.append(
                ValidationError(
                    message="KDV oranı en fazla 2 ondalık basamak içerebilir.",
                    field="vat_rate",
                )
            )
    else:
        # KDV kapalıyken KDV sütunları seçilmişse uyarı/hata
        if ColumnKey.VAT in offer.selected_columns or ColumnKey.TOTAL_WITH_VAT in offer.selected_columns:
            errors.append(
                ValidationError(
                    message="KDV devre dışıyken KDV sütunları seçilemez.",
                    field="selected_columns",
                )
            )

    # 4. İskonto kapalıyken iskonto sütunları seçilmişse
    if not offer.discount_enabled:
        for disc_col in (ColumnKey.DISCOUNT_TYPE, ColumnKey.DISCOUNT_AMOUNT, ColumnKey.TOTAL_DISCOUNTED):
            if disc_col in offer.selected_columns:
                errors.append(
                    ValidationError(
                        message=f"İskonto devre dışıyken '{disc_col.label_tr}' sütunu seçilemez.",
                        field="selected_columns",
                    )
                )

    # 5. Zorunlu sütunların varlığı (Bölüm 6.3)
    mandatory_cols = [col for col in FIXED_COLUMN_ORDER if col.is_mandatory]
    for col in mandatory_cols:
        if col not in offer.selected_columns:
            errors.append(
                ValidationError(
                    message=f"'{col.label_tr}' zorunlu bir sütundur ve kapatılamaz.",
                    field="selected_columns",
                )
            )

    # 6. Ürün satırları denetimi (Bölüm 6.6)
    valid_items = offer.get_valid_items()
    if not valid_items:
        errors.append(
            ValidationError(
                message="Teklifte en az bir geçerli ürün satırı bulunmalıdır.",
                field="items",
            )
        )
    else:
        for idx, item in enumerate(offer.items):
            item_errors = validate_item(
                item,
                row_index=idx,
                discount_enabled=offer.discount_enabled,
            )
            errors.extend(item_errors)

    # 7. Koşul bölümleri denetimi
    for section in offer.sections:
        errors.extend(validate_section(section))

    return ValidationResult(errors=errors)
