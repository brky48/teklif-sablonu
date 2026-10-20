"""PDF oluşturma servisi birim ve entegrasyon testleri."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path
import pytest

from PySide6.QtPdf import QPdfDocument

from teklif_sablonu.domain.enums import (
    ColumnKey,
    CurrencyCode,
    DiscountType,
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
