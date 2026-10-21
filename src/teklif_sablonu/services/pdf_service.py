"""PDF üretim servisi (ReportLab tabanlı profesyonel çıktı üretici)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm, mm
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    Image as RLImage,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from teklif_sablonu.config import (
    ASSETS_DIR,
    BRANDS_DIR,
    COMPANIES_DIR,
    load_companies,
)
from teklif_sablonu.domain.calculator import calculate_offer
from teklif_sablonu.domain.enums import (
    FIXED_COLUMN_ORDER,
    ColumnKey,
    DiscountType,
    DocumentLanguage,
    PageOrientation,
    SectionKey,
)
from teklif_sablonu.domain.models import Offer, OfferItem
from teklif_sablonu.domain.parsers import format_decimal_tr
from teklif_sablonu.domain.validators import validate_offer
from teklif_sablonu.services.html_utils import qt_html_to_reportlab
from teklif_sablonu.templates.pdf_styles import get_pdf_styles, register_turkish_fonts


class NumberedCanvas(canvas.Canvas):
    """Sayfa numarasını (Sayfa X / Y veya Page X / Y) hesaplayıp alt bilgiye yazan tuval."""

    document_language: DocumentLanguage = DocumentLanguage.TR

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._saved_page_states: list[dict[str, Any]] = []

    def showPage(self) -> None:
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_footer(num_pages)
            super().showPage()
        super().save()

    def draw_page_footer(self, page_count: int) -> None:
        self.saveState()
        font_name = register_turkish_fonts()
        self.setFont(font_name, 8)
        self.setFillColor(colors.HexColor("#718096"))
        page_w, _ = self._pagesize

        # Sağ alt: Sayfa X / Y veya Page X / Y
        is_en = getattr(self, "document_language", DocumentLanguage.TR) == DocumentLanguage.EN
        footer_text = f"Page {self._pageNumber} / {page_count}" if is_en else f"Sayfa {self._pageNumber} / {page_count}"
        self.drawRightString(page_w - 36, 18, footer_text)
        self.restoreState()


def get_desktop_dir() -> Path:
    """Kullanıcının gerçek Masaüstü (Desktop) dizinini bulur ve döndürür."""
    desktop = Path.home() / "Desktop"
    if desktop.exists() and os.access(desktop, os.W_OK):
        return desktop
    return Path.home()


class PdfService:
    """Teklif verilerinden standartlara uygun profesyonel PDF oluşturan servis."""

    def __init__(self) -> None:
        register_turkish_fonts()
        self.styles = get_pdf_styles()

    def get_default_output_path(self, offer_number: str) -> Path:
        """Varsayılan kayıt yolunu (<Masaüstü>/<TeklifNo>.pdf) döndürür."""
        clean_num = offer_number or "Teklif"
        return get_desktop_dir() / f"{clean_num}.pdf"

    def determine_page_orientation(
        self,
        visible_columns: list[ColumnKey],
        offer: Offer | None = None,
    ) -> tuple[Any, float]:
        """Sütun sayısına veya kullanıcının seçtiği sayfa yönüne göre Dikey veya Yatay A4 yönünü seçer.

        Bölüm 9.2:
        - Kullanıcı tercihi 'portrait' ise: Daima Dikey A4
        - Kullanıcı tercihi 'landscape' ise: Daima Yatay A4
        - 'auto' (varsayılan):
          - 7 veya daha az sütun: Dikey A4 (Portrait, genişlik: 595.27 pt, yazılabilir alan: 523.27 pt).
          - 8 veya daha fazla sütun: Yatay A4 (Landscape, genişlik: 841.89 pt, yazılabilir alan: 769.89 pt).
        """
        if offer is not None:
            if offer.page_orientation == PageOrientation.PORTRAIT or offer.page_orientation == "portrait":
                return A4, 595.27 - 72
            elif offer.page_orientation == PageOrientation.LANDSCAPE or offer.page_orientation == "landscape":
                return landscape(A4), 841.89 - 72

        if len(visible_columns) <= 7:
            return A4, 595.27 - 72  # 36pt sol/sağ marjin = 523.27 pt
        return landscape(A4), 841.89 - 72  # 769.89 pt

    def filter_visible_columns(self, offer: Offer, items: list[OfferItem]) -> list[ColumnKey]:
        """Şartname Bölüm 6.2 kuralına göre gösterilecek sütunları filtreler:

        - Seçilmeyen veya tüm ürün satırlarında tamamen boş kalan sütunlar çıkarılır.
        - Zorunlu sütunlar (Açıklama, Miktar, Fiyat, Toplam) daima korunur.
        - Sabit sıra (FIXED_COLUMN_ORDER) kesinlikle korunur.
        """
        visible: list[ColumnKey] = []

        for col in FIXED_COLUMN_ORDER:
            # Kullanıcı tarafından seçilmemişse atla
            if col not in offer.selected_columns:
                continue

            # Zorunlu sütunlar daima kalır
            if col.is_mandatory:
                visible.append(col)
                continue

            # Diğer opsiyonel sütunlar: En az bir satırda değer var mı kontrol et
            has_value = False
            for it in items:
                if col == ColumnKey.PRODUCT_CODE and it.product_code and it.product_code.strip():
                    has_value = True
                    break
                elif col == ColumnKey.PALLET and it.pallet is not None and it.pallet > 0:
                    has_value = True
                    break
                elif col == ColumnKey.DISCOUNT_TYPE and offer.discount_enabled and it.discount_type != DiscountType.NONE:
                    has_value = True
                    break
                elif col == ColumnKey.DISCOUNT_AMOUNT and offer.discount_enabled and it.discount_value > 0:
                    has_value = True
                    break
                elif col == ColumnKey.VAT and offer.vat_enabled and offer.vat_rate > 0:
                    has_value = True
                    break
                elif col == ColumnKey.TOTAL_DISCOUNTED and offer.discount_enabled:
                    has_value = True
                    break
                elif col == ColumnKey.TOTAL_WITH_VAT and offer.vat_enabled:
                    has_value = True
                    break

            if has_value:
                visible.append(col)

        return visible

    def calculate_column_widths(self, columns: list[ColumnKey], total_width: float) -> list[float]:
        """Sütun türlerine göre ağırlıklı genişlik dağılımı yapar."""
        # Göreceli ağırlıklar
        weights_map = {
            ColumnKey.PRODUCT_CODE: 2.2,
            ColumnKey.DESCRIPTION: 4.8,
            ColumnKey.QUANTITY: 2.0,
            ColumnKey.PALLET: 1.8,
            ColumnKey.UNIT_PRICE: 2.4,
            ColumnKey.DISCOUNT_TYPE: 2.0,
            ColumnKey.DISCOUNT_AMOUNT: 2.4,
            ColumnKey.VAT: 1.5,
            ColumnKey.TOTAL_AMOUNT: 2.6,
            ColumnKey.TOTAL_DISCOUNTED: 2.7,
            ColumnKey.TOTAL_WITH_VAT: 2.7,
        }

        total_weight = sum(weights_map.get(col, 2.0) for col in columns)
        unit_width = total_width / total_weight
        return [weights_map.get(col, 2.0) * unit_width for col in columns]

    def generate_pdf(
        self,
        offer: Offer,
        output_path: Path | str | None = None,
    ) -> Path:
        """Verilen Offer modelinden referans şablona uygun PDF belgesi üretir."""
        # 0. Domain seviyesinde kuralları doğrula
        validation = validate_offer(offer)
        validation.raise_if_invalid()

        if output_path is None:
            output_path = self.get_default_output_path(offer.offer_number)
        else:
            output_path = Path(output_path)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        valid_items = offer.get_valid_items()
        item_calcs, totals = calculate_offer(offer)

        # 1. Sayfa Yönü ve Genişliği Belirle
        visible_cols = self.filter_visible_columns(offer, valid_items)
        page_size, usable_width = self.determine_page_orientation(visible_cols, offer=offer)

        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=page_size,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=36,
        )

        flowables: list[Any] = []

        # ── 1. ÜST BÖLÜM (Header: Logolar, Teklif No/Tarih ve Şirket Bilgileri) ──
        header_table = self._build_header(offer, usable_width)
        flowables.append(header_table)
        flowables.append(Spacer(1, 14))

        # ── 2. ÜRÜN TABLOSU (Çok sayfada repeatRows=1 ile başlık tekrarı) ──
        items_table = self._build_items_table(offer, valid_items, item_calcs, visible_cols, usable_width)
        flowables.append(items_table)
        flowables.append(Spacer(1, 12))

        # ── 3. GENEL TOPLAM ÖZETİ (Bölüm 8.5) ──
        totals_table = self._build_totals_table(offer, totals, usable_width)
        flowables.append(totals_table)
        flowables.append(Spacer(1, 14))

        # ── 4. TİCARİ KOŞULLAR (Bölüm 7.6) ──
        conditions_block = self._build_conditions(offer, usable_width)
        if conditions_block:
            flowables.append(conditions_block)
            flowables.append(Spacer(1, 16))

        # ── 5. İMZA ALANLARI ──
        signature_table = self._build_signatures(offer, usable_width)
        flowables.append(KeepTogether(signature_table))

        # PDF oluştur
        class OfferNumberedCanvas(NumberedCanvas):
            document_language = offer.document_language

        doc.build(flowables, canvasmaker=OfferNumberedCanvas)
        return output_path

    def _build_header(self, offer: Offer, usable_width: float) -> Table:
        """Üst bölümü (Sol: Logolar, Sağ: Teklif No / Tarih ve Şirket Adresi) oluşturur."""
        # Şirket bilgilerini bul
        companies = load_companies()
        company = next((c for c in companies if c.id == offer.company_id), companies[0])

        # Sol taraf: Logo akışı
        left_elements: list[Any] = []

        # Şirket Logosu
        comp_logo_path = COMPANIES_DIR / f"{company.id}.png"
        if not comp_logo_path.exists() and company.logo_path:
            comp_logo_path = COMPANIES_DIR / company.logo_path

        if comp_logo_path.exists():
            # Oranını koruyarak yerleştir (Genişlik max 190 pt, Yükseklik max 50 pt)
            left_elements.append(RLImage(str(comp_logo_path), width=180, height=45))
        else:
            left_elements.append(Paragraph(company.display_name, self.styles["BoxTitle"]))

        # Marka Logosu (Eğer kullanıcı göster seçtiyse)
        if offer.brand_logo_visible:
            brand_logo_path = BRANDS_DIR / "juresh.png"
            if brand_logo_path.exists():
                left_elements.append(Spacer(1, 4))
                left_elements.append(RLImage(str(brand_logo_path), width=110, height=53))

        # Sağ taraf: Teklif No ve Tarih Kutuları + Şirket Bilgileri
        right_elements: list[Any] = []

        # Kutular tablosu (Teklif No ve Tarih)
        is_en = offer.document_language == DocumentLanguage.EN
        lbl_offer_no = "OFFER NO:" if is_en else "TEKLİF NO:"
        lbl_date = "DATE:" if is_en else "TARİH:"

        box_data = [
            [
                Paragraph(f"<b>{lbl_offer_no}</b> {offer.offer_number or '-'}", self.styles["BoxTitle"]),
            ],
            [
                Paragraph(f"<b>{lbl_date}</b> {offer.offer_date.strftime('%d.%m.%Y')}", self.styles["BoxTitle"]),
            ],
        ]
        box_table = Table(box_data, colWidths=[200])
        box_table.setStyle(
            TableStyle([
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#2D3748")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#A0AEC0")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F7FAFC")),
                ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#FFFFFF")),
            ])
        )
        right_elements.append(box_table)
        right_elements.append(Spacer(1, 6))

        # Şirket İletişim / Vergi Bilgileri
        addr_label = getattr(company, "address_label_en", "Headquarters and Factory") if is_en else company.address_label
        lines = [
            f"<b>{addr_label}:</b>",
            *company.address_lines,
            f"{company.tax_office}",
            f"{company.tax_id}",
        ]
        comp_text = "<br/>".join(lines)
        right_elements.append(Paragraph(comp_text, self.styles["CompanyInfo"]))

        # İki sütunlu üst tablo
        col_w = usable_width / 2.0
        header_data = [[left_elements, right_elements]]
        t = Table(header_data, colWidths=[col_w, col_w])
        t.setStyle(
            TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ])
        )
        return t

    def _build_items_table(
        self,
        offer: Offer,
        items: list[OfferItem],
        item_calcs: list[Any],
        columns: list[ColumnKey],
        usable_width: float,
    ) -> Table:
        """Ürünler tablosunu oluşturur (repeatRows=1 ile çok sayfada başlık tekrarı)."""
        col_widths = self.calculate_column_widths(columns, usable_width)
        is_en = offer.document_language == DocumentLanguage.EN

        # 1. Başlık Satırı
        header_row = []
        for col in columns:
            if col == ColumnKey.QUANTITY:
                title = offer.quantity_unit.get_column_header(offer.document_language).upper()
            else:
                title = col.label(offer.document_language).upper()
            header_row.append(Paragraph(f"<b>{title}</b>", self.styles["TableHeader"]))

        table_data = [header_row]

        # 2. Ürün Satırları
        curr_sym = f" {offer.currency_code.symbol}"
        for idx, (item, calc) in enumerate(zip(items, item_calcs)):
            row = []
            for col in columns:
                if col == ColumnKey.PRODUCT_CODE:
                    val = item.product_code or "-"
                    p = Paragraph(val, self.styles["TableCellCenter"])
                elif col == ColumnKey.DESCRIPTION:
                    val = item.description or "-"
                    p = Paragraph(f"<b>{val}</b>", self.styles["TableCellLeft"])
                elif col == ColumnKey.QUANTITY:
                    val = format_decimal_tr(item.quantity)
                    p = Paragraph(val, self.styles["TableCellCenter"])
                elif col == ColumnKey.PALLET:
                    val = format_decimal_tr(item.pallet) if item.pallet else "-"
                    p = Paragraph(val, self.styles["TableCellCenter"])
                elif col == ColumnKey.UNIT_PRICE:
                    val = format_decimal_tr(item.unit_price) + curr_sym
                    p = Paragraph(val, self.styles["TableCellRight"])
                elif col == ColumnKey.DISCOUNT_TYPE:
                    val = item.discount_type.label(offer.document_language) if item.discount_type != DiscountType.NONE else "-"
                    p = Paragraph(val, self.styles["TableCellCenter"])
                elif col == ColumnKey.DISCOUNT_AMOUNT:
                    if item.discount_type == DiscountType.RATE:
                        val = f"%{format_decimal_tr(item.discount_value)}"
                    elif item.discount_type == DiscountType.AMOUNT:
                        val = format_decimal_tr(item.discount_value) + curr_sym
                    else:
                        val = "-"
                    p = Paragraph(val, self.styles["TableCellRight"])
                elif col == ColumnKey.VAT:
                    rate_str = format_decimal_tr(offer.vat_rate, decimal_places=0 if offer.vat_rate % 1 == 0 else 2)
                    p = Paragraph(f"%{rate_str}", self.styles["TableCellCenter"])
                elif col == ColumnKey.TOTAL_AMOUNT:
                    val = format_decimal_tr(calc.line_total) + curr_sym
                    p = Paragraph(f"<b>{val}</b>", self.styles["TableCellRight"])
                elif col == ColumnKey.TOTAL_DISCOUNTED:
                    val = format_decimal_tr(calc.discounted_total) + curr_sym
                    p = Paragraph(f"<b>{val}</b>", self.styles["TableCellRight"])
                elif col == ColumnKey.TOTAL_WITH_VAT:
                    val = format_decimal_tr(calc.total_with_vat) + curr_sym
                    p = Paragraph(f"<b>{val}</b>", self.styles["TableCellRight"])
                else:
                    p = Paragraph("-", self.styles["TableCellCenter"])

                row.append(p)
            table_data.append(row)

        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        table.setStyle(
            TableStyle([
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#1A202C")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F7FAFC")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ])
        )
        return table

    def _build_totals_table(self, offer: Offer, totals: Any, usable_width: float) -> Table:
        """Genel toplam özetini sağa yaslı bir tablo olarak oluşturur."""
        curr_sym = f" {offer.currency_code.symbol}"
        is_en = offer.document_language == DocumentLanguage.EN
        rows: list[list[Any]] = []

        # 1. Ara Toplam (Daima)
        subtotal_lbl = "Subtotal:" if is_en else "Ara Toplam:"
        rows.append([
            Paragraph(subtotal_lbl, self.styles["TotalsTitle"]),
            Paragraph(format_decimal_tr(totals.subtotal) + curr_sym, self.styles["TotalsValue"]),
        ])

        # 2. İskonto
        if offer.discount_enabled:
            disc_lbl = "Total Discount:" if is_en else "Toplam İskonto:"
            disc_sub_lbl = "Subtotal After Discount:" if is_en else "İskonto Sonrası Ara Toplam:"
            rows.append([
                Paragraph(disc_lbl, self.styles["TotalsTitle"]),
                Paragraph(f"-{format_decimal_tr(totals.total_discount)}{curr_sym}", self.styles["TotalsValue"]),
            ])
            rows.append([
                Paragraph(disc_sub_lbl, self.styles["TotalsTitle"]),
                Paragraph(format_decimal_tr(totals.discounted_subtotal) + curr_sym, self.styles["TotalsValue"]),
            ])

        # 3. KDV
        if offer.vat_enabled:
            rate_str = format_decimal_tr(offer.vat_rate, decimal_places=0 if offer.vat_rate % 1 == 0 else 2)
            vat_lbl = f"Total VAT (%{rate_str}):" if is_en else f"Toplam KDV (%{rate_str}):"
            grand_vat_lbl = "<b>GRAND TOTAL (INCL. VAT):</b>" if is_en else "<b>KDV DÂHİL GENEL TOPLAM:</b>"
            rows.append([
                Paragraph(vat_lbl, self.styles["TotalsTitle"]),
                Paragraph(format_decimal_tr(totals.total_vat) + curr_sym, self.styles["TotalsValue"]),
            ])
            rows.append([
                Paragraph(grand_vat_lbl, self.styles["GrandTotalTitle"]),
                Paragraph(f"<b>{format_decimal_tr(totals.grand_total)}{curr_sym}</b>", self.styles["GrandTotalValue"]),
            ])
        else:
            final_total = totals.discounted_subtotal if offer.discount_enabled else totals.subtotal
            grand_lbl = "<b>GRAND TOTAL:</b>" if is_en else "<b>GENEL TOPLAM:</b>"
            rows.append([
                Paragraph(grand_lbl, self.styles["GrandTotalTitle"]),
                Paragraph(f"<b>{format_decimal_tr(final_total)}{curr_sym}</b>", self.styles["GrandTotalValue"]),
            ])

        # Genişlik: 220 pt sağa dayalı
        card_w = 230
        left_pad = usable_width - card_w

        totals_card = Table(rows, colWidths=[120, 110])
        totals_card.setStyle(
            TableStyle([
                ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#CBD5E0")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#EBF8FF")),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ])
        )

        wrapper = Table([["", totals_card]], colWidths=[left_pad, card_w])
        wrapper.setStyle(
            TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ])
        )
        return wrapper

    def _build_conditions(self, offer: Offer, usable_width: float) -> KeepTogether | None:
        """Etkin ticari koşul bölümlerini ve başlıksız tam genişlikli ek alan kutusunu hazırlar."""
        elements: list[Any] = []
        table_rows: list[list[Any]] = []
        add_notes_html: str | None = None

        for sec in offer.sections:
            if not sec.enabled or not sec.text or not sec.text.strip():
                continue

            if sec.section_key == SectionKey.ADDITIONAL_NOTES:
                # Kullanıcı şartı: Ek Alan içinde sabit başlık/yorum olmamalı, sadece girilen zengin metin yer almalı.
                clean_html = qt_html_to_reportlab(sec.text.strip())
                if clean_html:
                    add_notes_html = clean_html
            else:
                label_text = sec.section_key.label(offer.document_language)
                table_rows.append([
                    Paragraph(f"<b>{label_text}:</b>", self.styles["ConditionLabel"]),
                    Paragraph(sec.text.strip(), self.styles["ConditionText"]),
                ])

        if table_rows:
            label_col_w = 120
            text_col_w = usable_width - label_col_w
            cond_table = Table(table_rows, colWidths=[label_col_w, text_col_w])
            cond_table.setStyle(
                TableStyle([
                    ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#1A202C")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F7FAFC")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ])
            )
            elements.append(cond_table)

        # Ek Alan kutusu (Sabit başlıksız, sadece kullanıcının girdiği metin, tam genişlikte kenarlıklı kutu)
        if add_notes_html:
            if table_rows:
                elements.append(Spacer(1, 4))
            notes_table = Table([[Paragraph(add_notes_html, self.styles["ConditionText"])]], colWidths=[usable_width])
            notes_table.setStyle(
                TableStyle([
                    ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#1A202C")),
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFFFFF")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ])
            )
            elements.append(notes_table)

        if not elements:
            return None
        return KeepTogether(elements)

    def _build_signatures(self, offer: Offer, usable_width: float) -> Table:
        """Referans PDF'teki 2 kutulu imza ve onay alanını oluşturur."""
        companies = load_companies()
        company = next((c for c in companies if c.id == offer.company_id), companies[0])
        is_en = offer.document_language == DocumentLanguage.EN

        box_w = (usable_width - 20) / 2.0
        box_h = 75

        # Sol Kutu: Alıcı / Müşteri
        default_recipient = "CUSTOMER APPROVAL / SIGNATURE" if is_en else "MÜŞTERİ ONAY / İMZA"
        recipient_title = offer.recipient_name or default_recipient
        left_content = [
            Paragraph(f"<b>{recipient_title.upper()}</b>", self.styles["SignatureTitle"]),
            Spacer(1, box_h - 22),
        ]

        # Sağ Kutu: Şirket
        right_content = [
            Paragraph(f"<b>{company.display_name}</b>", self.styles["SignatureTitle"]),
            Spacer(1, box_h - 22),
        ]

        sig_data = [[left_content, "", right_content]]
        sig_table = Table(sig_data, colWidths=[box_w, 20, box_w])
        sig_table.setStyle(
            TableStyle([
                ("BOX", (0, 0), (0, 0), 1, colors.HexColor("#1A202C")),
                ("BOX", (2, 0), (2, 0), 1, colors.HexColor("#1A202C")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#FFFFFF")),
                ("BACKGROUND", (2, 0), (2, 0), colors.HexColor("#FFFFFF")),
            ])
        )
        return sig_table
