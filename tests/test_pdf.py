"""PDF oluşturma servisi birim ve entegrasyon testleri."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path
import pytest

from PySide6.QtPdf import QPdfDocument

from teklif_sablonu.domain.enums import (
    FIXED_COLUMN_ORDER,
    ColumnKey,
    CurrencyCode,
    DiscountType,
    DocumentLanguage,
    PageOrientation,
    QuantityUnit,
    SectionKey,
)
from teklif_sablonu.domain.models import Offer, OfferItem, OfferSection
from teklif_sablonu.services.pdf_service import PdfService


@pytest.fixture
def pdf_service() -> PdfService:
    return PdfService()


def test_pdf_generation_portrait(pdf_service: PdfService, tmp_path: Path) -> None:
    """Az sütunlu teklif Dikey A4 (Portrait) olarak oluşturulmalıdır."""
    out_pdf = tmp_path / "test_portrait.pdf"

    offer = Offer(
        offer_number="20261020-001",
        offer_date=date(2026, 10, 20),
        company_id="endemiks_tarim",
        recipient_name="Antalya Narenciye Ltd.",
        currency_code=CurrencyCode.TRY,
        quantity_unit=QuantityUnit.PIECE,
        vat_enabled=False,
        discount_enabled=False,
        brand_logo_visible=True,
        selected_columns=[
            ColumnKey.DESCRIPTION,
            ColumnKey.QUANTITY,
            ColumnKey.UNIT_PRICE,
            ColumnKey.TOTAL_AMOUNT,
        ],
        items=[
            OfferItem(
                description="Portakal Suyu 1LT",
                quantity=Decimal("100"),
                unit_price=Decimal("45.00"),
            )
        ],
        sections=[
            OfferSection(
                section_key=SectionKey.DELIVERY_ADDRESS,
                enabled=True,
                text="Tek bir merkezi noktaya Adres Teslimdir.",
            )
        ],
    )

    result_path = pdf_service.generate_pdf(offer, out_pdf)
    assert result_path.exists()
    assert result_path.stat().st_size > 1000

    # QtPdf ile sayfa yönünü doğrula
    doc = QPdfDocument()
    doc.load(str(result_path))
    assert doc.pageCount() == 1
    size = doc.pagePointSize(0)
    # Dikey A4: Genişlik ~595, Yükseklik ~842
    assert size.width() < size.height()
    assert abs(size.width() - 595.27) < 2


def test_pdf_generation_landscape(pdf_service: PdfService, tmp_path: Path) -> None:
    """Çok sütunlu (8+ sütun) teklif Yatay A4 (Landscape) olarak oluşturulmalıdır."""
    out_pdf = tmp_path / "test_landscape.pdf"

    offer = Offer(
        offer_number="20261020-002",
        offer_date=date(2026, 10, 20),
        company_id="endemiks_gida",
        recipient_name="İstanbul Toptan Gıda A.Ş.",
        currency_code=CurrencyCode.EUR,
        quantity_unit=QuantityUnit.LITRE,
        vat_enabled=True,
        vat_rate=Decimal("20.00"),
        discount_enabled=True,
        brand_logo_visible=True,
        selected_columns=[
            ColumnKey.PRODUCT_CODE,
            ColumnKey.DESCRIPTION,
            ColumnKey.QUANTITY,
            ColumnKey.PALLET,
            ColumnKey.UNIT_PRICE,
            ColumnKey.DISCOUNT_TYPE,
            ColumnKey.DISCOUNT_AMOUNT,
            ColumnKey.VAT,
            ColumnKey.TOTAL_AMOUNT,
            ColumnKey.TOTAL_DISCOUNTED,
            ColumnKey.TOTAL_WITH_VAT,
        ],
        items=[
            OfferItem(
                product_code="PRD-99",
                description="Sıvı Gübre Premium",
                quantity=Decimal("500"),
                pallet=Decimal("5"),
                unit_price=Decimal("12.50"),
                discount_type=DiscountType.RATE,
                discount_value=Decimal("10.00"),
            )
        ],
    )

    result_path = pdf_service.generate_pdf(offer, out_pdf)
    assert result_path.exists()

    # QtPdf ile sayfa yönünü doğrula
    doc = QPdfDocument()
    doc.load(str(result_path))
    assert doc.pageCount() == 1
    size = doc.pagePointSize(0)
    # Yatay A4: Genişlik ~842, Yükseklik ~595
    assert size.width() > size.height()
    assert abs(size.width() - 841.89) < 2


def test_pdf_explicit_landscape_override(pdf_service: PdfService, tmp_path: Path) -> None:
    """Az sütunlu teklif kullanıcı tarafından Yatay seçildiyse Yatay oluşturulmalıdır."""
    out_pdf = tmp_path / "test_forced_landscape.pdf"
    offer = Offer(
        page_orientation=PageOrientation.LANDSCAPE,
        selected_columns=[
            ColumnKey.DESCRIPTION,
            ColumnKey.QUANTITY,
            ColumnKey.UNIT_PRICE,
            ColumnKey.TOTAL_AMOUNT,
        ],
        items=[OfferItem(description="Test", quantity=Decimal("1"), unit_price=Decimal("10"))],
    )
    result_path = pdf_service.generate_pdf(offer, out_pdf)
    doc = QPdfDocument()
    doc.load(str(result_path))
    size = doc.pagePointSize(0)
    assert size.width() > size.height()


def test_pdf_explicit_portrait_override(pdf_service: PdfService, tmp_path: Path) -> None:
    """Çok sütunlu teklif kullanıcı tarafından Dikey seçildiyse Dikey oluşturulmalıdır."""
    out_pdf = tmp_path / "test_forced_portrait.pdf"
    offer = Offer(
        page_orientation=PageOrientation.PORTRAIT,
        vat_enabled=True,
        vat_rate=Decimal("20.00"),
        discount_enabled=True,
        selected_columns=list(FIXED_COLUMN_ORDER),
        items=[
            OfferItem(
                product_code="KOD1",
                description="Test",
                quantity=Decimal("1"),
                pallet=Decimal("1"),
                unit_price=Decimal("10"),
                discount_type=DiscountType.RATE,
                discount_value=Decimal("5"),
            )
        ],
    )
    result_path = pdf_service.generate_pdf(offer, out_pdf)
    doc = QPdfDocument()
    doc.load(str(result_path))
    size = doc.pagePointSize(0)
    assert size.width() < size.height()


def test_pdf_multipage_pagination(pdf_service: PdfService, tmp_path: Path) -> None:
    """Çok sayıda ürün içeren teklif birden fazla sayfaya taşmalı ve sayfa numaraları yazılmalıdır."""
    out_pdf = tmp_path / "test_multipage.pdf"

    items = [
        OfferItem(
            product_code=f"KOD-{i:03d}",
            description=f"Özel Tarımsal Ürün Çeşidi {i}",
            quantity=Decimal("10"),
            unit_price=Decimal("25.00"),
        )
        for i in range(1, 35)
    ]

    offer = Offer(
        offer_number="20261020-003",
        offer_date=date(2026, 10, 20),
        company_id="endemiks_tarim",
        recipient_name="Çok Kalemli Müşteri A.Ş.",
        items=items,
    )

    result_path = pdf_service.generate_pdf(offer, out_pdf)
    assert result_path.exists()

    doc = QPdfDocument()
    doc.load(str(result_path))
    # 34 kalem en az 2 sayfaya taşmalıdır
    assert doc.pageCount() >= 2


def test_pdf_turkish_characters(pdf_service: PdfService, tmp_path: Path) -> None:
    """Türkçe özel karakterler (Ş, ğ, İ, ö, ü, ç, ı) hatasız gömülmelidir."""
    out_pdf = tmp_path / "test_turkish.pdf"

    offer = Offer(
        offer_number="20261020-004",
        offer_date=date(2026, 10, 20),
        recipient_name="Şahanoğlu Çiftliği & Çağdaş Tarım Ltd. Şti.",
        items=[
            OfferItem(
                description="İçerik: Şeker Pancarı, Çavdar, Söğüt Özü ve Ispanak",
                quantity=Decimal("15"),
                unit_price=Decimal("120.00"),
            )
        ],
        sections=[
            OfferSection(
                section_key=SectionKey.ADDITIONAL_NOTES,
                enabled=True,
                text="<b>Önemli Not:</b> Ürünler <i>ışık almayan</i> serin yerde saklanmalıdır.",
                rich_text=True,
            )
        ],
    )

    result_path = pdf_service.generate_pdf(offer, out_pdf)
    assert result_path.exists()
    assert result_path.stat().st_size > 1000


def test_pdf_generation_with_full_qt_html_rich_text(pdf_service: PdfService, tmp_path: Path) -> None:
    """Qt QTextEdit.toHtml() tam HTML çıktısı (DOCTYPE, style, span) PDF üretimini çökertmemelidir."""
    out_pdf = tmp_path / "test_qt_rich_text.pdf"

    qt_html = """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<html><head><meta name="qrichtext" content="1" /><style type="text/css">
p, li { white-space: pre-wrap; }
hr { height: 1px; border-width: 0; }
li.unchecked::marker { content: "\\2610"; }
li.checked::marker { content: "\\2612"; }
</style></head><body style=" font-family:'.AppleSystemUIFont'; font-size:13pt; font-weight:400; font-style:normal;">
<p style=" margin-top:0px; margin-bottom:0px;"><span style=" font-weight:700;">Önemli:</span> Bu teklif <span style=" font-style:italic;">15 gün</span> geçerlidir.</p>
<ul style="margin-top: 0px; margin-bottom: 0px;">
<li>Sevkiyat öncesi arayınız</li>
<li>Ödeme peşindir</li>
</ul>
</body></html>"""

    offer = Offer(
        offer_number="20261021-099",
        company_id="endemiks_tarim",
        recipient_name="Test Müşteri",
        items=[OfferItem(description="Test Ürün", quantity=Decimal("1"), unit_price=Decimal("100"))],
        sections=[
            OfferSection(
                section_key=SectionKey.ADDITIONAL_NOTES,
                enabled=True,
                text=qt_html,
                rich_text=True,
            )
        ],
    )

    result_path = pdf_service.generate_pdf(offer, out_pdf)
    assert result_path.exists()
    assert result_path.stat().st_size > 1000


def test_pdf_filters_empty_columns(pdf_service: PdfService) -> None:
    """Tüm satırlarda boş olan sütunlar PDF'ten elenmelidir."""
    offer = Offer(
        selected_columns=[
            ColumnKey.PRODUCT_CODE,  # Boş kalacak
            ColumnKey.DESCRIPTION,
            ColumnKey.QUANTITY,
            ColumnKey.PALLET,        # Boş kalacak
            ColumnKey.UNIT_PRICE,
            ColumnKey.TOTAL_AMOUNT,
        ],
        items=[
            OfferItem(
                product_code="",     # Boş
                description="Ürün",
                quantity=Decimal("1"),
                pallet=None,         # Boş
                unit_price=Decimal("10"),
            )
        ],
    )

    visible = pdf_service.filter_visible_columns(offer, offer.items)
    assert ColumnKey.PRODUCT_CODE not in visible
    assert ColumnKey.PALLET not in visible
    assert ColumnKey.DESCRIPTION in visible
    assert ColumnKey.QUANTITY in visible
    assert ColumnKey.UNIT_PRICE in visible
    assert ColumnKey.TOTAL_AMOUNT in visible


def test_pdf_footer_links_and_header_alignment(pdf_service: PdfService, tmp_path: Path) -> None:
    """PDF alt bilgi linkleri (tel, web, mail) ve ortalanmış başlık doğru üretilmelidir."""
    out_pdf = tmp_path / "test_footer_links.pdf"
    offer = Offer(
        offer_number="20261026-099",
        offer_date=date(2026, 10, 26),
        recipient_name="Test Müşteri",
        items=[OfferItem(description="Test Kalemi", quantity=Decimal("10"), unit_price=Decimal("50"))],
    )
    result = pdf_service.generate_pdf(offer, out_pdf)
    assert result.exists()

    with open(result, "rb") as f:
        content = f.read()

    # Tıklanabilir linkler üretilmiş olmalı
    assert b"tel:+905310846885" in content
    assert b"http://www.juresh.com.tr" in content
    assert b"mailto:info@endemiks.com" in content

    # Header tablosunun ilk satırında logo ortalanmış ve SPAN yapılmış olmalı
    header_table = pdf_service._build_header(offer, 500)
    assert len(header_table._cellvalues) == 2
    # İlk satır SPAN ile 2 hücreli
    assert header_table._cellvalues[0][1] == ""


def test_pdf_ready_templates_page_count_and_content(pdf_service: PdfService, tmp_path: Path) -> None:
    """Hazır şablonlar seçilmediğinde 1 sayfa kalmalı, seçildiğinde yeni sayfada tablolar üretilmelidir."""
    # 1. Şablonlar kapalıyken -> Kesinlikle 1 sayfa
    offer_no_tpl = Offer(
        offer_number="20261026-T1",
        offer_date=date(2026, 10, 26),
        recipient_name="Tek Sayfa Firma",
        template_packaging_info=False,
        template_storage_conditions=False,
        items=[OfferItem(description="Kalem", quantity=Decimal("1"), unit_price=Decimal("10"))],
    )
    p_no_tpl = tmp_path / "no_tpl.pdf"
    pdf_service.generate_pdf(offer_no_tpl, p_no_tpl)
    doc = QPdfDocument()
    doc.load(str(p_no_tpl))
    assert doc.pageCount() == 1

    # 2. Türkçe versiyon: Paketleme ve Muhafaza açık -> 2 sayfa
    offer_tr = Offer(
        offer_number="20261026-T2",
        offer_date=date(2026, 10, 26),
        document_language=DocumentLanguage.TR,
        recipient_name="İki Sayfa Firma TR",
        template_packaging_info=True,
        template_storage_conditions=True,
        items=[OfferItem(description="Kalem", quantity=Decimal("1"), unit_price=Decimal("10"))],
    )
    p_tr = tmp_path / "tr_tpl.pdf"
    pdf_service.generate_pdf(offer_tr, p_tr)
    doc_tr = QPdfDocument()
    doc_tr.load(str(p_tr))
    assert doc_tr.pageCount() == 2

    # Türkçe şablon içerikleri
    tr_elements = pdf_service._build_ready_templates(offer_tr, 500)
    tr_text = " ".join(el.text for el in tr_elements if hasattr(el, "text"))
    assert "PAKETLEME BİLGİLERİ" in tr_text
    assert "MUHAFAZA KOŞULLARI" in tr_text
    assert "*80 x 120 cm palet boyutu referans alınmaktadır." in tr_text
    assert "*Ürünler çözündükten sonra buzdolabı sıcaklığında (+4°C’de) muhafaza edilmelidir." in tr_text
    assert "*Ürün çözündükten sonra tekrar dondurmayınız." in tr_text

    # 3. İngilizce versiyon: Paketleme ve Muhafaza açık -> 2 sayfa
    offer_en = Offer(
        offer_number="20261026-T3",
        offer_date=date(2026, 10, 26),
        document_language=DocumentLanguage.EN,
        recipient_name="Two Page Firm EN",
        template_packaging_info=True,
        template_storage_conditions=True,
        items=[OfferItem(description="Item", quantity=Decimal("1"), unit_price=Decimal("10"))],
    )
    p_en = tmp_path / "en_tpl.pdf"
    pdf_service.generate_pdf(offer_en, p_en)
    doc_en = QPdfDocument()
    doc_en.load(str(p_en))
    assert doc_en.pageCount() == 2

    # İngilizce şablon içerikleri
    en_elements = pdf_service._build_ready_templates(offer_en, 500)
    en_text = " ".join(el.text for el in en_elements if hasattr(el, "text"))
    assert "PACKAGING INFORMATION" in en_text
    assert "STORAGE CONDITIONS" in en_text
    assert "*The 80 × 120 cm pallet size is used as a reference." in en_text
    assert "*After thawing, products must be stored at +4°C." in en_text
    assert "*Do not refreeze after thawing." in en_text

    from reportlab.platypus import Table
    stg_table = next(el for el in en_elements if isinstance(el, Table) and len(el._colWidths) == 10)
    stg_header_texts = " ".join(cell.text for cell in stg_table._cellvalues[0] if hasattr(cell, "text"))
    assert "GRAPEFRUIT JUICE" in stg_header_texts
    assert "BLACK MULBERRY SQUASH" in stg_header_texts
    assert "GREYFURT JUICE" not in stg_header_texts


def test_pdf_signature_bottom_anchoring_and_header_right_alignment(
    pdf_service: PdfService, tmp_path: Path
) -> None:
    """İmza kutularının sayfanın en altına itilmesi ve Teklif No kutusunun sağa hizalanması test edilir."""
    from reportlab.platypus import Table
    from teklif_sablonu.services.pdf_service import DynamicBottomSpacer

    offer = Offer(
        offer_number="20261026-ALIGN1",
        offer_date=date(2026, 10, 26),
        recipient_name="Align Test Corp",
        items=[OfferItem(description="Ürün", quantity=Decimal("1"), unit_price=Decimal("100"))],
    )

    # 1. Header sağa hizalama kontrolü
    header_table = pdf_service._build_header(offer, 520)
    right_elements = header_table._cellvalues[1][1]
    assert len(right_elements) >= 2
    # İlk eleman 2 sütunlu wrapper Table olmalı ve toplam genişliği 260 olmalı
    box_wrapper = right_elements[0]
    assert isinstance(box_wrapper, Table)
    assert sum(box_wrapper._colWidths) == 260.0  # usable_width / 2
    assert box_wrapper._colWidths[1] == 165.0  # sağ hücre kutunun tam genişliği

    # 2. DynamicBottomSpacer davranışı kontrolü
    sig_table = pdf_service._build_signatures(offer, 520)
    spacer = DynamicBottomSpacer(target_flowable=sig_table, min_gap=12.0)
    w, h = spacer.wrap(520, 400)
    # 400 pt boşluk varsa, imza tablosu ~75 pt olduğundan kalan boşluğu doldurmalıdır (~325 pt)
    assert h > 300
    assert w == 0

    # Yeterli alan yoksa bir sonraki sayfaya taşması için availHeight + 1 döndürmelidir
    w_overflow, h_overflow = spacer.wrap(520, 50)
    assert h_overflow == 51

    # 3. PDF çıktısının başarıyla üretilmesi
    out_pdf = tmp_path / "align_test.pdf"
    res = pdf_service.generate_pdf(offer, out_pdf)
    assert res.exists()


def test_pdf_ready_templates_product_info(pdf_service: PdfService, tmp_path: Path) -> None:
    """Ürün Bilgileri altındaki seçilen şablonların sıralı ve doğru dilde üretilmesi test edilir."""
    from reportlab.platypus import Paragraph, Table

    # 1. Türkçe versiyon
    offer_tr = Offer(
        offer_number="20261026-PINFO-TR",
        offer_date=date(2026, 10, 26),
        document_language=DocumentLanguage.TR,
        recipient_name="TR Test",
        template_packaging_info=False,
        template_storage_conditions=False,
        template_product_info=True,
        # Sırasız versek bile çıktıda sıralı olmalı:
        template_product_info_items=["mulberry_squash", "quality_guarantee", "orange_juice"],
        items=[OfferItem(description="Kalem", quantity=Decimal("1"), unit_price=Decimal("10"))],
    )
    p_tr = tmp_path / "tr_pinfo.pdf"
    pdf_service.generate_pdf(offer_tr, p_tr)
    doc_tr = QPdfDocument()
    doc_tr.load(str(p_tr))
    assert doc_tr.pageCount() >= 2

    tr_elements = pdf_service._build_ready_templates(offer_tr, 500)
    all_texts = []
    for el in tr_elements:
        if isinstance(el, Paragraph):
            all_texts.append(el.text)
        elif isinstance(el, Table):
            for row in el._cellvalues:
                for cell in row:
                    if hasattr(cell, "text"):
                        all_texts.append(cell.text)

    joined_tr = " ".join(all_texts)
    assert "KALİTE & GÜVENCE" in joined_tr
    assert "HACCP ve gıda güvenliği" in joined_tr
    assert "ÜRÜN DETAYLARI" in joined_tr
    assert "PORTAKAL SUYU" in joined_tr
    assert "KARADUT SQUASH" in joined_tr

    # Sıralama kontrolü: KALİTE & GÜVENCE -> PORTAKAL SUYU -> KARADUT SQUASH
    idx_quality = joined_tr.index("KALİTE & GÜVENCE")
    idx_orange = joined_tr.index("PORTAKAL SUYU")
    idx_mulberry = joined_tr.index("KARADUT SQUASH")
    assert idx_quality < idx_orange < idx_mulberry

    # 2. İngilizce versiyon
    offer_en = Offer(
        offer_number="20261026-PINFO-EN",
        offer_date=date(2026, 10, 26),
        document_language=DocumentLanguage.EN,
        recipient_name="EN Test",
        template_product_info=True,
        template_product_info_items=["quality_guarantee", "lemonade_extract", "grapefruit_juice"],
        items=[OfferItem(description="Item", quantity=Decimal("1"), unit_price=Decimal("10"))],
    )
    p_en = tmp_path / "en_pinfo.pdf"
    pdf_service.generate_pdf(offer_en, p_en)
    doc_en = QPdfDocument()
    doc_en.load(str(p_en))
    assert doc_en.pageCount() >= 2

    en_elements = pdf_service._build_ready_templates(offer_en, 500)
    en_all_texts = []
    for el in en_elements:
        if isinstance(el, Paragraph):
            en_all_texts.append(el.text)
        elif isinstance(el, Table):
            for row in el._cellvalues:
                for cell in row:
                    if hasattr(cell, "text"):
                        en_all_texts.append(cell.text)

    joined_en = " ".join(en_all_texts)
    assert "QUALITY & GUARANTEE" in joined_en
    assert "PRODUCT DETAILS" in joined_en
    assert "LEMONADE EXTRACT" in joined_en
    assert "GRAPEFRUIT JUICE" in joined_en



