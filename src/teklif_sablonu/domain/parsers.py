"""Türkçe yerel sayı girdilerini güvenli parse etme ve biçimlendirme modülü."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation


class ParseError(ValueError):
    """Sayısal girdi dönüştürme hatası."""


def parse_turkish_decimal(
    text: str | int | float | Decimal | None,
    *,
    allow_negative: bool = False,
    max_decimal_places: int = 2,
    max_integer_digits: int | None = None,
) -> Decimal | None:
    """Türkçe formatlı sayı metnini güvenli şekilde Python Decimal'e dönüştürür.

    Kurallar:
    - Boş veya yalnızca boşluk içeren metinler için `None` döner.
    - Ondalık ayraç olarak virgül (,) veya nokta (.) kabul edilir.
    - Binlik ayraç (örn. '1.234,50' veya '1 234,50') varsa güvenle temizlenir.
    - max_decimal_places aşılırsa ParseError fırlatır (örn. '15,005' -> hata).
    - allow_negative=False iken negatif değer gelirse ParseError fırlatır.
    """
    if text is None:
        return None

    if isinstance(text, Decimal):
        val = text
    elif isinstance(text, (int, float)):
        val = Decimal(str(text))
    else:
        cleaned = text.strip()
        if not cleaned:
            return None

        # Boşlukları temizle (örn. "1 234,50")
        cleaned = cleaned.replace(" ", "")

        # Para sembollerini temizle
        for sym in ("₺", "$", "€", "TL"):
            cleaned = cleaned.replace(sym, "")

        # Format kontrolü: '1.234,56' (TR format) veya '1234,56' veya '1234.56'
        if "," in cleaned and "." in cleaned:
            # Örn: 1.234,56
            if cleaned.rfind(",") > cleaned.rfind("."):
                # Noktalar binlik ayraç, virgül ondalık
                cleaned = cleaned.replace(".", "").replace(",", ".")
            else:
                # Örn: 1,234.56 (EN format)
                cleaned = cleaned.replace(",", "")
        elif "," in cleaned:
            # Yalnızca virgül var: ondalık ayraç kabul edilir
            cleaned = cleaned.replace(",", ".")

        try:
            val = Decimal(cleaned)
        except InvalidOperation as exc:
            raise ParseError(f"Geçersiz sayısal format: '{text}'") from exc

    # Negatif kontrolü
    if not allow_negative and val < Decimal("0"):
        raise ParseError("Değer negatif olamaz.")

    # Ondalık basamak kontrolü
    # Normalize veya exponent kontrolü
    val_str = format(val, "f")
    if "." in val_str:
        dec_part = val_str.split(".")[1].rstrip("0")
        if len(dec_part) > max_decimal_places:
            raise ParseError(
                f"En fazla {max_decimal_places} ondalık basamak girilebilir: '{text}'"
            )

    # Tam basamak kontrolü
    if max_integer_digits is not None:
        int_part = val_str.split(".")[0].lstrip("-")
        if len(int_part) > max_integer_digits:
            raise ParseError(
                f"Tam kısım en fazla {max_integer_digits} basamak olabilir: '{text}'"
            )

    return val


def format_decimal_tr(
    value: Decimal | None,
    *,
    decimal_places: int = 2,
    use_grouping: bool = True,
) -> str:
    """Decimal değeri Türkçe gösterim biçimine (1.234,56) dönüştürür."""
    if value is None:
        return ""

    val_str = f"{value:.{decimal_places}f}"
    if "." in val_str:
        int_part, dec_part = val_str.split(".", 1)
    else:
        int_part, dec_part = val_str, ""

    if use_grouping:
        # Binlik gruplama (nokta ile)
        is_negative = int_part.startswith("-")
        digits = int_part[1:] if is_negative else int_part
        # Sağdan sola 3'erli grupla
        groups = []
        while digits:
            groups.append(digits[-3:])
            digits = digits[:-3]
        grouped_int = ".".join(reversed(groups))
        if is_negative:
            grouped_int = f"-{grouped_int}"
    else:
        grouped_int = int_part

    if decimal_places > 0:
        return f"{grouped_int},{dec_part}"
    return grouped_int
