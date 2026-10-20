"""Merkezi yuvarlama kuralları modülü.

Şartname Bölüm 8.4 ve Kesinleşmiş Kural:
- Tüm parasal ve miktar hesaplamalarında Python Decimal kullanılır.
- Kesin yuvarlama kuralı ROUND_HALF_UP ve 2 ondalık basamaktır.
- Tek ve merkezi bir yuvarlama fonksiyonundan geçirilir.
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

_TWO_PLACES = Decimal("0.01")


def round_currency(value: Decimal | int | float | str) -> Decimal:
    """Parasal değeri 2 ondalık basamağa ROUND_HALF_UP ile yuvarlar.

    Örnek:
        round_currency(Decimal("10.005")) -> Decimal("10.01")
        round_currency(Decimal("10.004")) -> Decimal("10.00")
        round_currency(Decimal("-10.005")) -> Decimal("-10.01")
    """
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    return value.quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)


def round_quantity(value: Decimal | int | float | str) -> Decimal:
    """Miktar veya palet değerini 2 ondalık basamağa ROUND_HALF_UP ile yuvarlar."""
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    return value.quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)
