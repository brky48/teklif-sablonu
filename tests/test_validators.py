"""Girdi doğrulama ve iş kuralı birim testleri."""

from __future__ import annotations

from decimal import Decimal
import pytest

from teklif_sablonu.domain.enums import (
    ColumnKey,
    CurrencyCode,
    DiscountType,
    QuantityUnit,
    SectionKey,
)
from teklif_sablonu.domain.models import Offer, OfferItem, OfferSection
from teklif_sablonu.domain.validators import (
    get_visible_text_length,
    validate_item,
    validate_offer,
    validate_section,
)


def _make_valid_offer() -> Offer:
    """Geçerli bir teklif nesnesi oluşturur."""
    return Offer(
        company_id="endemiks_tarim",
        recipient_name="Örnek Müşteri Ltd. Şti.",
        currency_code=CurrencyCode.TRY,
        quantity_unit=QuantityUnit.PIECE,
        vat_enabled=True,
        vat_rate=Decimal("20"),
        discount_enabled=True,
        selected_columns=[
            ColumnKey.DESCRIPTION,
            ColumnKey.QUANTITY,
            ColumnKey.UNIT_PRICE,
            ColumnKey.TOTAL_AMOUNT,
            ColumnKey.DISCOUNT_TYPE,
            ColumnKey.DISCOUNT_AMOUNT,
            ColumnKey.TOTAL_DISCOUNTED,
            ColumnKey.VAT,
            ColumnKey.TOTAL_WITH_VAT,
        ],
        items=[
            OfferItem(
                product_code="PRD-01",
                description="Gübre 25kg",
                quantity=Decimal("10"),
                unit_price=Decimal("100.00"),
                discount_type=DiscountType.RATE,
                discount_value=Decimal("10"),
            )
        ],
    )


def test_valid_offer() -> None:
    """Geçerli teklif doğrulamasından sıfır hata ile geçmelidir."""
    offer = _make_valid_offer()
    res = validate_offer(offer)
    assert res.is_valid
    assert len(res.errors) == 0


def test_empty_offer_no_items() -> None:
    """Ürün satırı olmayan teklif reddedilmelidir."""
    offer = _make_valid_offer()
    offer.items = []
    res = validate_offer(offer)
    assert not res.is_valid
    assert any("en az bir geçerli ürün satırı" in e.message for e in res.errors)


def test_offer_with_only_empty_rows_fails() -> None:
    """Yalnızca tamamen boş satırlardan oluşan teklif reddedilmelidir."""
    offer = _make_valid_offer()
    offer.items = [OfferItem(), OfferItem()]
    res = validate_offer(offer)
    assert not res.is_valid
    assert any("en az bir geçerli ürün satırı" in e.message for e in res.errors)


def test_offer_ignores_empty_row_alongside_valid_row() -> None:
    """Tamamen boş satır yok sayılır ve geçerli satır varsa teklif onaylanır."""
    offer = _make_valid_offer()
    offer.items.append(OfferItem())  # 2. satır tamamen boş
    res = validate_offer(offer)
    assert res.is_valid


def test_partially_filled_item_fails() -> None:
    """Kısmen doldurulmuş (açıklama var ama miktar yok) satır hata vermelidir."""
    offer = _make_valid_offer()
    offer.items.append(
        OfferItem(
            description="Eksik ürün",
            quantity=Decimal("0"),  # Geçersiz
            unit_price=Decimal("50"),
        )
    )
    res = validate_offer(offer)
    assert not res.is_valid
    assert any(e.field == "quantity" and e.row_index == 1 for e in res.errors)


def test_field_length_limits() -> None:
    """64 karakter sınırları (kod, açıklama) ve 200 karakter alıcı sınırı."""
    offer = _make_valid_offer()
    offer.recipient_name = "X" * 201
    offer.items[0].product_code = "C" * 65
    offer.items[0].description = "D" * 65

    res = validate_offer(offer)
    assert not res.is_valid
    assert any("Alıcı bilgisi en fazla" in e.message for e in res.errors)
    assert any("Ürün kodu en fazla 64" in e.message for e in res.errors)
    assert any("Ürün açıklaması en fazla 64" in e.message for e in res.errors)


def test_numeric_decimal_places_limit() -> None:
    """Miktar, birim fiyat ve palette en fazla 2 ondalık basamak olmalıdır."""
    item = OfferItem(
        description="Ürün",
        quantity=Decimal("10.005"),
        unit_price=Decimal("20.123"),
        pallet=Decimal("1.555"),
    )
    errors = validate_item(item, row_index=0)
    fields = [e.field for e in errors]
    assert "quantity" in fields
    assert "unit_price" in fields
    assert "pallet" in fields


def test_discount_validation_rules() -> None:
    """İskonto sınırları (oran 0-100, tutar <= satır toplamı)."""
    # Oran > 100
    item1 = OfferItem(
        description="Ürün 1",
        quantity=Decimal("1"),
        unit_price=Decimal("100"),
        discount_type=DiscountType.RATE,
        discount_value=Decimal("105"),
    )
    errors1 = validate_item(item1, row_index=0, discount_enabled=True)
    assert any("0 ile 100 arasında" in e.message for e in errors1)

    # Sabit tutar > satır toplamı
    item2 = OfferItem(
        description="Ürün 2",
        quantity=Decimal("2"),
        unit_price=Decimal("50"),  # Toplam: 100
        discount_type=DiscountType.AMOUNT,
        discount_value=Decimal("150"),  # 150 > 100
    )
    errors2 = validate_item(item2, row_index=1, discount_enabled=True)
    assert any("satır toplamını" in e.message for e in errors2)


def test_mandatory_columns_cannot_be_removed() -> None:
    """Zorunlu sütunlar (Açıklama, Miktar, Fiyat, Toplam) kapatılamaz."""
    offer = _make_valid_offer()
    # Açıklama sütununu çıkar
    offer.selected_columns = [
        col for col in offer.selected_columns if col != ColumnKey.DESCRIPTION
    ]
    res = validate_offer(offer)
    assert not res.is_valid
    assert any("Ürün Açıklaması" in e.message for e in res.errors)


def test_disabled_feature_columns_rejected() -> None:
    """KDV kapalıyken KDV sütunu seçilemez."""
    offer = _make_valid_offer()
    offer.vat_enabled = False
    # Seçili sütunlarda hâlâ KDV sütunları var
    res = validate_offer(offer)
    assert not res.is_valid
    assert any("KDV devre dışıyken" in e.message for e in res.errors)


def test_section_character_limits() -> None:
    """Ticari koşullarda 3000 ve zengin metinde 10000 sınırları kontrol edilir."""
    # Standart bölüm > 3000
    sec_standard = OfferSection(
        section_key=SectionKey.DELIVERY_ADDRESS,
        enabled=True,
        text="A" * 3001,
    )
    errs_std = validate_section(sec_standard)
    assert len(errs_std) == 1
    assert "en fazla 3000 karakter" in errs_std[0].message

    # Ek Alan (zengin metin): HTML etiketleri sayılmamalı
    html_text = "<p><strong>" + ("B" * 5000) + "</strong></p>"
    sec_rich = OfferSection(
        section_key=SectionKey.ADDITIONAL_NOTES,
        enabled=True,
        text=html_text,
        rich_text=True,
    )
    # Görünür karakter 5000 <= 10000 -> geçerli
    assert get_visible_text_length(html_text, is_rich_text=True) == 5000
    assert len(validate_section(sec_rich)) == 0

    # Görünür karakter 10001 -> hata
    sec_rich_over = OfferSection(
        section_key=SectionKey.ADDITIONAL_NOTES,
        enabled=True,
        text="<p>" + ("C" * 10001) + "</p>",
        rich_text=True,
    )
    assert len(validate_section(sec_rich_over)) == 1
    assert "en fazla 10000 karakter" in validate_section(sec_rich_over)[0].message


def test_enums_and_models_helpers() -> None:
    """Enum yardımcı özellikleri ve model metodları doğru çalışmalıdır."""
    assert CurrencyCode.TRY.symbol == "₺"
    assert CurrencyCode.USD.symbol == "$"
    assert CurrencyCode.EUR.symbol == "€"

    assert QuantityUnit.PIECE.label_tr == "Adet"
    assert QuantityUnit.PIECE.column_header == "Miktar (Adet)"
    assert QuantityUnit.LITRE.label_tr == "Litre"
    assert QuantityUnit.LITRE.column_header == "Miktar (Litre)"

    assert DiscountType.NONE.label_tr == "Yok"
    assert DiscountType.RATE.label_tr == "Oran"
    assert DiscountType.AMOUNT.label_tr == "Miktar"

    assert ColumnKey.DESCRIPTION.label_tr == "Ürün Açıklaması"
    assert ColumnKey.DESCRIPTION.is_mandatory is True
    assert ColumnKey.PALLET.is_mandatory is False

    assert SectionKey.DELIVERY_ADDRESS.label_tr == "Teslimat Adresi"
    assert SectionKey.DELIVERY_ADDRESS.max_chars == 3000
    assert SectionKey.ADDITIONAL_NOTES.is_rich_text is True

    offer = _make_valid_offer()
    assert offer.is_column_selected(ColumnKey.DESCRIPTION) is True
    assert offer.is_column_selected(ColumnKey.PALLET) is False

    item = offer.items[0]
    assert item.is_complete() is True
    assert item.is_partially_filled() is False


def test_validation_result_raise_if_invalid() -> None:
    """raise_if_invalid geçerli teklifte hata fırlatmamalı, geçersiz teklifte ValueError fırlatmalıdır."""
    valid_offer = _make_valid_offer()
    res_valid = validate_offer(valid_offer)
    res_valid.raise_if_invalid()  # Hatasız geçmeli

    invalid_offer = _make_valid_offer()
    invalid_offer.items = []
    res_invalid = validate_offer(invalid_offer)
    with pytest.raises(ValueError, match="Teklif doğrulaması başarısız"):
        res_invalid.raise_if_invalid()
