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


def get_pdf_styles(base_font_size: float = 8.0) -> dict[str, ParagraphStyle]:
    """PDF için özelleştirilmiş ParagraphStyle sözlüğünü hazırlar.

    Args:
        base_font_size: Tablo ve gövde metinleri için temel punto büyüklüğü (varsayılan: 8.0 pt).
            Tüm stiller bu orana göre (scale = base_font_size / 8.0) orantılı olarak ölçeklenir.
    """
    font_name = register_turkish_fonts()
    bold_font = f"{font_name}-Bold" if font_name == "DejaVuSans" else "Helvetica-Bold"
    italic_font = f"{font_name}-Oblique" if font_name == "DejaVuSans" else "Helvetica-Oblique"

    scale = max(0.5, float(base_font_size) / 8.0)

    def _sz(sz: float, lead: float) -> tuple[float, float]:
        if abs(scale - 1.0) < 1e-4:
            return sz, lead
        return round(sz * scale, 2), round(lead * scale, 2)

    def_fs, def_ld = _sz(9, 12)
    ch_fs, ch_ld = _sz(10, 13)
    chc_fs, chc_ld = _sz(11, 14)
    ci_fs, ci_ld = _sz(8, 11)
    bt_fs, bt_ld = _sz(8.5, 11)
    th_fs, th_ld = _sz(8, 10)
    tc_fs, tc_ld = _sz(8, 10)
    tt_fs, tt_ld = _sz(8.5, 11)
    gt_fs, gt_ld = _sz(10, 13)
    gv_fs, gv_ld = _sz(10.5, 13)
    cl_fs, cl_ld = _sz(8, 11)
    st_fs, st_ld = _sz(8.5, 11)
    tmpl_fs, tmpl_ld = _sz(10, 13)
    tmpn_fs, tmpn_ld = _sz(8, 11)
    psh_fs, psh_ld = _sz(11, 14)
    pdt_fs, pdt_ld = _sz(7.8, 10.5)
    pdb_fs, pdb_ld = _sz(8, 11.5)

    return {
        "Default": ParagraphStyle(
            name="Default",
            fontName=font_name,
            fontSize=def_fs,
            leading=def_ld,
            textColor=colors.HexColor("#2D3748"),
        ),
        "CompanyHeader": ParagraphStyle(
            name="CompanyHeader",
            fontName=bold_font,
            fontSize=ch_fs,
            leading=ch_ld,
            textColor=colors.HexColor("#1A202C"),
            alignment=TA_RIGHT,
        ),
        "CompanyHeaderCentered": ParagraphStyle(
            name="CompanyHeaderCentered",
            fontName=bold_font,
            fontSize=chc_fs,
            leading=chc_ld,
            textColor=colors.HexColor("#1A202C"),
            alignment=TA_CENTER,
        ),
        "CompanyInfo": ParagraphStyle(
            name="CompanyInfo",
            fontName=font_name,
            fontSize=ci_fs,
            leading=ci_ld,
            textColor=colors.HexColor("#4A5568"),
            alignment=TA_RIGHT,
        ),
        "BoxTitle": ParagraphStyle(
            name="BoxTitle",
            fontName=bold_font,
            fontSize=bt_fs,
            leading=bt_ld,
            textColor=colors.HexColor("#1A202C"),
            alignment=TA_CENTER,
        ),
        "TableHeader": ParagraphStyle(
            name="TableHeader",
            fontName=bold_font,
            fontSize=th_fs,
            leading=th_ld,
            textColor=colors.HexColor("#1A202C"),
            alignment=TA_CENTER,
        ),
        "TableCellLeft": ParagraphStyle(
            name="TableCellLeft",
            fontName=font_name,
            fontSize=tc_fs,
            leading=tc_ld,
            textColor=colors.HexColor("#2D3748"),
            alignment=TA_LEFT,
        ),
        "TableCellCenter": ParagraphStyle(
            name="TableCellCenter",
            fontName=font_name,
            fontSize=tc_fs,
            leading=tc_ld,
            textColor=colors.HexColor("#2D3748"),
            alignment=TA_CENTER,
        ),
        "TableCellRight": ParagraphStyle(
            name="TableCellRight",
            fontName=font_name,
            fontSize=tc_fs,
            leading=tc_ld,
            textColor=colors.HexColor("#2D3748"),
            alignment=TA_RIGHT,
        ),
        "TotalsTitle": ParagraphStyle(
            name="TotalsTitle",
            fontName=font_name,
            fontSize=tt_fs,
            leading=tt_ld,
            textColor=colors.HexColor("#4A5568"),
            alignment=TA_LEFT,
        ),
        "TotalsValue": ParagraphStyle(
            name="TotalsValue",
            fontName=bold_font,
            fontSize=tt_fs,
            leading=tt_ld,
            textColor=colors.HexColor("#1A202C"),
            alignment=TA_RIGHT,
        ),
        "GrandTotalTitle": ParagraphStyle(
            name="GrandTotalTitle",
            fontName=bold_font,
            fontSize=gt_fs,
            leading=gt_ld,
            textColor=colors.HexColor("#1A202C"),
            alignment=TA_LEFT,
        ),
        "GrandTotalValue": ParagraphStyle(
            name="GrandTotalValue",
            fontName=bold_font,
            fontSize=gv_fs,
            leading=gv_ld,
            textColor=colors.HexColor("#2B6CB0"),
            alignment=TA_RIGHT,
        ),
        "ConditionLabel": ParagraphStyle(
            name="ConditionLabel",
            fontName=bold_font,
            fontSize=cl_fs,
            leading=cl_ld,
            textColor=colors.HexColor("#2D3748"),
            alignment=TA_LEFT,
        ),
        "ConditionText": ParagraphStyle(
            name="ConditionText",
            fontName=font_name,
            fontSize=cl_fs,
            leading=cl_ld,
            textColor=colors.HexColor("#2D3748"),
            alignment=TA_LEFT,
        ),
        "SignatureTitle": ParagraphStyle(
            name="SignatureTitle",
            fontName=bold_font,
            fontSize=st_fs,
            leading=st_ld,
            textColor=colors.HexColor("#2D3748"),
            alignment=TA_CENTER,
        ),
        "TemplateTitle": ParagraphStyle(
            name="TemplateTitle",
            fontName=bold_font,
            fontSize=tmpl_fs,
            leading=tmpl_ld,
            textColor=colors.HexColor("#1A202C"),
            alignment=TA_LEFT,
        ),
        "TemplateNote": ParagraphStyle(
            name="TemplateNote",
            fontName=bold_font,
            fontSize=tmpn_fs,
            leading=tmpn_ld,
            textColor=colors.HexColor("#2D3748"),
            alignment=TA_LEFT,
        ),
        "ProductSectionHeader": ParagraphStyle(
            name="ProductSectionHeader",
            fontName=bold_font,
            fontSize=psh_fs,
            leading=psh_ld,
            textColor=colors.HexColor("#1A202C"),
            alignment=TA_LEFT,
        ),
        "ProductDetailText": ParagraphStyle(
            name="ProductDetailText",
            fontName=font_name,
            fontSize=pdt_fs,
            leading=pdt_ld,
            textColor=colors.HexColor("#2D3748"),
            alignment=TA_LEFT,
        ),
        "ProductDetailBullet": ParagraphStyle(
            name="ProductDetailBullet",
            fontName=font_name,
            fontSize=pdb_fs,
            leading=pdb_ld,
            textColor=colors.HexColor("#2D3748"),
            alignment=TA_LEFT,
            leftIndent=10,
        ),
    }
