"""domain paketi — İş modelleri, doğrulama ve hesaplama motoru."""

from teklif_sablonu.domain.calculator import (
    CalculationError,
    DiscountExceedsTotalError,
    calculate_item,
    calculate_offer,
    calculate_offer_totals,
)
from teklif_sablonu.domain.enums import (
    FIXED_COLUMN_ORDER,
    ColumnKey,
    CurrencyCode,
    DiscountType,
    QuantityUnit,
    SectionKey,
)
from teklif_sablonu.domain.models import (
    Offer,
    OfferItem,
    OfferItemCalculation,
    OfferSection,
    OfferTotals,
    default_selected_columns,
)
from teklif_sablonu.domain.parsers import (
    ParseError,
    format_decimal_tr,
    parse_turkish_decimal,
)
from teklif_sablonu.domain.rounding import round_currency, round_quantity
from teklif_sablonu.domain.validators import (
    ValidationError,
    ValidationResult,
    get_visible_text_length,
    validate_item,
    validate_offer,
    validate_section,
)

__all__ = [
    # Enums
    "CurrencyCode",
    "QuantityUnit",
    "DiscountType",
    "ColumnKey",
    "FIXED_COLUMN_ORDER",
    "SectionKey",
    # Models
    "Offer",
    "OfferItem",
    "OfferSection",
    "OfferTotals",
    "OfferItemCalculation",
    "default_selected_columns",
    # Rounding
    "round_currency",
    "round_quantity",
    # Parsers
    "parse_turkish_decimal",
    "format_decimal_tr",
    "ParseError",
    # Calculator
    "calculate_item",
    "calculate_offer_totals",
    "calculate_offer",
    "CalculationError",
    "DiscountExceedsTotalError",
    # Validators
    "validate_offer",
    "validate_item",
    "validate_section",
    "ValidationError",
    "ValidationResult",
    "get_visible_text_length",
]
