"""Türkçe sayı girdi ve biçimlendirme testleri."""

from __future__ import annotations

from decimal import Decimal
import pytest

from teklif_sablonu.domain.parsers import (
    ParseError,
    format_decimal_tr,
    parse_turkish_decimal,
)


def test_parse_turkish_decimal_valid() -> None:
    """Geçerli Türkçe virgüllü ve noktalı sayılar doğru parse edilmelidir."""
    assert parse_turkish_decimal("15") == Decimal("15")
    assert parse_turkish_decimal("15,5") == Decimal("15.5")
    assert parse_turkish_decimal("15,05") == Decimal("15.05")
    assert parse_turkish_decimal("  15,50  ") == Decimal("15.50")
    assert parse_turkish_decimal("1.234,50") == Decimal("1234.50")
    assert parse_turkish_decimal("1 234,50") == Decimal("1234.50")
    assert parse_turkish_decimal("1234.50") == Decimal("1234.50")
    assert parse_turkish_decimal(150) == Decimal("150")
    assert parse_turkish_decimal(Decimal("45.67")) == Decimal("45.67")


def test_parse_turkish_decimal_empty() -> None:
    """Boş girdiler None dönmelidir."""
    assert parse_turkish_decimal("") is None
    assert parse_turkish_decimal("   ") is None
    assert parse_turkish_decimal(None) is None


def test_parse_turkish_decimal_max_places_exceeded() -> None:
    """2'den fazla ondalık basamak girilirse ParseError fırlatılmalıdır."""
    with pytest.raises(ParseError, match="En fazla 2 ondalık basamak"):
        parse_turkish_decimal("15,005")

    with pytest.raises(ParseError, match="En fazla 2 ondalık basamak"):
        parse_turkish_decimal("1.234,567")


def test_parse_turkish_decimal_negative() -> None:
    """allow_negative=False iken negatif değer girilirse ParseError fırlatılmalıdır."""
    with pytest.raises(ParseError, match="negatif olamaz"):
        parse_turkish_decimal("-15,50")

    # allow_negative=True iken kabul edilmelidir
    assert parse_turkish_decimal("-15,50", allow_negative=True) == Decimal("-15.50")


def test_parse_turkish_decimal_invalid_format() -> None:
    """Geçersiz karakterler ParseError fırlatmalıdır."""
    with pytest.raises(ParseError, match="Geçersiz sayısal format"):
        parse_turkish_decimal("abc")

    with pytest.raises(ParseError, match="Geçersiz sayısal format"):
        parse_turkish_decimal("12,34,56")


def test_format_decimal_tr() -> None:
    """Decimal değerler Türkçe binlik nokta ve ondalık virgülle biçimlendirilmelidir."""
    assert format_decimal_tr(Decimal("1234.50")) == "1.234,50"
    assert format_decimal_tr(Decimal("1000000.00")) == "1.000.000,00"
    assert format_decimal_tr(Decimal("15.5")) == "15,50"
    assert format_decimal_tr(Decimal("0.00")) == "0,00"
    assert format_decimal_tr(None) == ""
    assert format_decimal_tr(Decimal("1234.5"), use_grouping=False) == "1234,50"
    assert format_decimal_tr(Decimal("1234"), decimal_places=0) == "1.234"
