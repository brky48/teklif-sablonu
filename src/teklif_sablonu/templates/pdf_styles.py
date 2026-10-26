"""PDF üretiminde kullanılan yazı tipleri, stiller ve ölçü sabitleri."""

from __future__ import annotations

from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from teklif_sablonu.config import FONTS_DIR

_FONTS_REGISTERED = False


def register_turkish_fonts() -> str:
    """Türkçe karakterleri eksiksiz destekleyen TrueType fontlarını ReportLab'e kaydeder.

    Kullanılan birincil font: DejaVuSans (assets/fonts/).
    """
    global _FONTS_REGISTERED
    if _FONTS_REGISTERED:
        return "DejaVuSans"

    regular_path = FONTS_DIR / "DejaVuSans.ttf"
    bold_path = FONTS_DIR / "DejaVuSans-Bold.ttf"
    oblique_path = FONTS_DIR / "DejaVuSans-Oblique.ttf"
    bold_oblique_path = FONTS_DIR / "DejaVuSans-BoldOblique.ttf"

    if regular_path.exists():
        pdfmetrics.registerFont(TTFont("DejaVuSans", str(regular_path)))
        if bold_path.exists():
            pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", str(bold_path)))
        if oblique_path.exists():
            pdfmetrics.registerFont(TTFont("DejaVuSans-Oblique", str(oblique_path)))
        if bold_oblique_path.exists():
            pdfmetrics.registerFont(TTFont("DejaVuSans-BoldOblique", str(bold_oblique_path)))

        # Font ailelerini eşle
        pdfmetrics.registerFontFamily(
            "DejaVuSans",
            normal="DejaVuSans",
            bold="DejaVuSans-Bold",
            italic="DejaVuSans-Oblique",
            boldItalic="DejaVuSans-BoldOblique",
        )
        _FONTS_REGISTERED = True
        return "DejaVuSans"

    # Font bulunamazsa standart Helvetica kullanılır
    _FONTS_REGISTERED = True
    return "Helvetica"


def get_pdf_styles() -> dict[str, ParagraphStyle]:
    """PDF için özelleştirilmiş ParagraphStyle sözlüğünü hazırlar."""
    font_name = register_turkish_fonts()
    bold_font = f"{font_name}-Bold" if font_name == "DejaVuSans" else "Helvetica-Bold"
    italic_font = f"{font_name}-Oblique" if font_name == "DejaVuSans" else "Helvetica-Oblique"

    return {
        "Default": ParagraphStyle(
            name="Default",
            fontName=font_name,
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#2D3748"),
        ),
        "CompanyHeader": ParagraphStyle(
            name="CompanyHeader",
            fontName=bold_font,
            fontSize=10,
            leading=13,
            textColor=colors.HexColor("#1A202C"),
            alignment=TA_RIGHT,
        ),
        "CompanyHeaderCentered": ParagraphStyle(
            name="CompanyHeaderCentered",
            fontName=bold_font,
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#1A202C"),
            alignment=TA_CENTER,
        ),
        "CompanyInfo": ParagraphStyle(
            name="CompanyInfo",
            fontName=font_name,
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#4A5568"),
            alignment=TA_RIGHT,
        ),
        "BoxTitle": ParagraphStyle(
            name="BoxTitle",
            fontName=bold_font,
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#1A202C"),
            alignment=TA_CENTER,
        ),
        "TableHeader": ParagraphStyle(
            name="TableHeader",
            fontName=bold_font,
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#1A202C"),
            alignment=TA_CENTER,
        ),
        "TableCellLeft": ParagraphStyle(
            name="TableCellLeft",
            fontName=font_name,
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#2D3748"),
            alignment=TA_LEFT,
        ),
        "TableCellCenter": ParagraphStyle(
            name="TableCellCenter",
            fontName=font_name,
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#2D3748"),
            alignment=TA_CENTER,
        ),
        "TableCellRight": ParagraphStyle(
            name="TableCellRight",
            fontName=font_name,
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#2D3748"),
            alignment=TA_RIGHT,
        ),
        "TotalsTitle": ParagraphStyle(
            name="TotalsTitle",
            fontName=font_name,
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#4A5568"),
            alignment=TA_LEFT,
        ),
        "TotalsValue": ParagraphStyle(
            name="TotalsValue",
            fontName=bold_font,
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#1A202C"),
            alignment=TA_RIGHT,
        ),
        "GrandTotalTitle": ParagraphStyle(
            name="GrandTotalTitle",
            fontName=bold_font,
            fontSize=10,
            leading=13,
            textColor=colors.HexColor("#1A202C"),
            alignment=TA_LEFT,
        ),
        "GrandTotalValue": ParagraphStyle(
            name="GrandTotalValue",
            fontName=bold_font,
            fontSize=10.5,
            leading=13,
            textColor=colors.HexColor("#2B6CB0"),
            alignment=TA_RIGHT,
        ),
        "ConditionLabel": ParagraphStyle(
            name="ConditionLabel",
            fontName=bold_font,
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#2D3748"),
            alignment=TA_LEFT,
        ),
        "ConditionText": ParagraphStyle(
            name="ConditionText",
            fontName=font_name,
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#2D3748"),
            alignment=TA_LEFT,
        ),
        "SignatureTitle": ParagraphStyle(
            name="SignatureTitle",
            fontName=bold_font,
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#2D3748"),
            alignment=TA_CENTER,
        ),
        "TemplateTitle": ParagraphStyle(
            name="TemplateTitle",
            fontName=bold_font,
            fontSize=10,
            leading=13,
            textColor=colors.HexColor("#1A202C"),
            alignment=TA_LEFT,
        ),
        "TemplateNote": ParagraphStyle(
            name="TemplateNote",
            fontName=bold_font,
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#2D3748"),
            alignment=TA_LEFT,
        ),
        "ProductSectionHeader": ParagraphStyle(
            name="ProductSectionHeader",
            fontName=bold_font,
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#1A202C"),
            alignment=TA_LEFT,
        ),
        "ProductDetailText": ParagraphStyle(
            name="ProductDetailText",
            fontName=font_name,
            fontSize=7.8,
            leading=10.5,
            textColor=colors.HexColor("#2D3748"),
            alignment=TA_LEFT,
        ),
        "ProductDetailBullet": ParagraphStyle(
            name="ProductDetailBullet",
            fontName=font_name,
            fontSize=8,
            leading=11.5,
            textColor=colors.HexColor("#2D3748"),
            alignment=TA_LEFT,
            leftIndent=10,
        ),
    }
