"""templates paketi — PDF şablon düzeni ve stil sabitleri."""

from teklif_sablonu.templates.pdf_styles import (
    get_pdf_styles,
    register_turkish_fonts,
)

__all__ = [
    "register_turkish_fonts",
    "get_pdf_styles",
]
