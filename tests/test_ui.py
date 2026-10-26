"""PySide6 Kullanıcı Arayüzü (UI) bileşenleri kapsamlı testleri."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path
import pytest

from PySide6.QtWidgets import QApplication

from teklif_sablonu.domain.enums import (
    ColumnKey,
    CurrencyCode,
    DiscountType,
    PageOrientation,
    QuantityUnit,
    SectionKey,
)
from teklif_sablonu.domain.models import Offer, OfferItem, OfferSection
from teklif_sablonu.services.offer_service import OfferService
from teklif_sablonu.ui.archive_widget import ArchiveWidget
from teklif_sablonu.ui.column_selector_widget import ColumnSelectorWidget
from teklif_sablonu.ui.header_widget import HeaderWidget
from teklif_sablonu.ui.items_table_widget import ItemsTableWidget
from teklif_sablonu.ui.main_window import MainWindow
from teklif_sablonu.ui.sections_widget import SectionsWidget
from teklif_sablonu.ui.totals_widget import TotalsWidget


@pytest.fixture(autouse=True)
def qapp() -> QApplication:
    """Qt uygulaması tekil örneğini hazırlar."""
    return QApplication.instance() or QApplication([])


def test_main_window_structure() -> None:
    """MainWindow tüm alt bileşenleriyle eksiksiz başlatılabilmelidir."""
    win = MainWindow()
    assert win.header_widget is not None
    assert win.column_selector is not None
    assert win.items_table is not None
    assert win.totals_widget is not None
    assert win.sections_widget is not None
    assert win.archive_widget is not None
    assert win.tab_widget.count() == 2
    win.close()


def test_header_widget_controls() -> None:
    """HeaderWidget alanları, getter/setter ve sinyalleri doğru çalışmalıdır."""
    header = HeaderWidget()

    # Şirket seçimi
    assert header.company_combo.count() >= 2
    header.set_company_id("endemiks_gida")
    assert header.get_company_id() == "endemiks_gida"

    # Tarih
    today = date(2026, 10, 20)
    header.set_offer_date(today)
    assert header.get_offer_date() == today

    # Alıcı adı
    header.set_recipient_name("Test Müşteri Ltd.")
    assert header.get_recipient_name() == "Test Müşteri Ltd."

    # Para birimi
    header.set_currency_code(CurrencyCode.EUR)
    assert header.get_currency_code() == CurrencyCode.EUR

    # Miktar birimi
    header.set_quantity_unit(QuantityUnit.LITRE)
    assert header.get_quantity_unit() == QuantityUnit.LITRE

    # KDV
    header.set_vat_enabled(True)
    header.set_vat_rate(Decimal("10.00"))
    assert header.is_vat_enabled() is True
    assert header.get_vat_rate() == Decimal("10.00")

    # İskonto & Marka Logosu
    header.set_discount_enabled(True)
    assert header.is_discount_enabled() is True
    header.set_brand_logo_visible(True)
    assert header.is_brand_logo_visible() is True


def test_column_selector_dependencies() -> None:
    """Zorunlu sütunlar kilitli olmalı; KDV/İskonto kapalıyken bağımlı sütunlar pasif olmalıdır."""
    selector = ColumnSelectorWidget()

    # 1. Zorunlu sütunlar kapalı olamaz
    for col in (ColumnKey.DESCRIPTION, ColumnKey.QUANTITY, ColumnKey.UNIT_PRICE, ColumnKey.TOTAL_AMOUNT):
        cb = selector._checkboxes[col]
        assert cb.isChecked() is True
        assert cb.isEnabled() is False

    # 2. KDV kapalıyken KDV sütunları devre dışı ve işaretsiz olmalı
    selector.update_feature_dependencies(vat_enabled=False, discount_enabled=False)
    assert selector._checkboxes[ColumnKey.VAT].isEnabled() is False
    assert selector._checkboxes[ColumnKey.VAT].isChecked() is False
    assert selector._checkboxes[ColumnKey.TOTAL_WITH_VAT].isEnabled() is False

    # 3. KDV açıldığında aktifleşmeli
    selector.update_feature_dependencies(vat_enabled=True, discount_enabled=False)
    assert selector._checkboxes[ColumnKey.VAT].isEnabled() is True
    assert selector._checkboxes[ColumnKey.VAT].isChecked() is True

    # 4. İskonto kapalıyken iskonto sütunları devre dışı olmalı
    assert selector._checkboxes[ColumnKey.DISCOUNT_TYPE].isEnabled() is False
    assert selector._checkboxes[ColumnKey.TOTAL_DISCOUNTED].isEnabled() is False

    # 5. İskonto açıldığında aktifleşmeli
    selector.update_feature_dependencies(vat_enabled=True, discount_enabled=True)
    assert selector._checkboxes[ColumnKey.DISCOUNT_TYPE].isEnabled() is True
    assert selector._checkboxes[ColumnKey.TOTAL_DISCOUNTED].isEnabled() is True

    # 6. Sütun sırası daima sabit 11 sütun sırasına uymalıdır
    cols = selector.get_selected_columns()
    assert cols[0] == ColumnKey.PRODUCT_CODE
    assert cols[-1] == ColumnKey.TOTAL_WITH_VAT


def test_items_table_add_duplicate_delete() -> None:
    """Ürün tablosunda satır ekleme, kopyalama ve silme işlemleri çalışmalıdır."""
    table = ItemsTableWidget()
    assert table.table.rowCount() == 1  # Başlangıçta 1 boş satır

    # 1. Yeni satır ekle
    table.add_row(
        OfferItem(
            product_code="KOD-01",
            description="Ürün 1",
            quantity=Decimal("5"),
            unit_price=Decimal("100"),
        )
    )
    assert table.table.rowCount() == 2

    # 2. Satırı kopyala
    table.table.selectRow(1)
    table._duplicate_selected_row()
    assert table.table.rowCount() == 3
    items = table.get_items()
    assert items[2].description == "Ürün 1"
    assert items[2].quantity == Decimal("5")

    # 3. Satırı sil
    table.table.selectRow(2)
    table._delete_selected_row()
    assert table.table.rowCount() == 2


def test_table_instant_calculations_and_totals() -> None:
    """Tabloda girdi yapıldığında anlık hesaplama çalışmalıdır."""
    win = MainWindow()

    # Miktar ve fiyat gir
    row = win.items_table._rows[0]
    row.desc_edit.setText("Örnek Gübre")
    row.qty_edit.setText("10")
    row.price_edit.setText("150,00")

    # Satır toplamı 1.500,00 olmalı
    assert row.total_lbl.text() == "1.500,00"
    assert "1.500,00" in win.totals_widget.lbl_subtotal.text()

    # İskonto uygula (%10)
    win.header_widget.set_discount_enabled(True)
    row.disc_type_combo.setCurrentIndex(1)  # Oran
    row.disc_val_edit.setText("10")

    assert row.disc_total_lbl.text() == "1.350,00"
    assert "150,00" in win.totals_widget.lbl_discount.text()
    assert "1.350,00" in win.totals_widget.lbl_disc_subtotal.text()

    # KDV uygula (%20)
    win.header_widget.set_vat_enabled(True)
    win.header_widget.set_vat_rate(Decimal("20.00"))

    # 1.350 * 0.20 = 270.00 KDV; Toplam: 1.620,00
    assert row.vat_total_lbl.text() == "1.620,00"
    assert "270,00" in win.totals_widget.lbl_vat.text()
    assert "1.620,00" in win.totals_widget.lbl_grand_total.text()
    win.close()


def test_to_offer_and_load_offer_symmetry() -> None:
    """MainWindow.to_offer() ve load_offer() veri kaybı olmadan birbirini tamamlamalıdır."""
    win = MainWindow()

    win.header_widget.set_company_id("endemiks_tarim")
    win.header_widget.set_recipient_name("Antalya Seracılık A.Ş.")
    win.header_widget.set_currency_code(CurrencyCode.USD)
    win.header_widget.set_quantity_unit(QuantityUnit.LITRE)
    win.header_widget.set_vat_enabled(True)
    win.header_widget.set_vat_rate(Decimal("10.00"))
    win.header_widget.set_discount_enabled(True)

    test_items = [
        OfferItem(
            product_code="L-101",
            description="Sıvı Gübre 20L",
            quantity=Decimal("50"),
            pallet=Decimal("2"),
            unit_price=Decimal("45.50"),
            discount_type=DiscountType.RATE,
            discount_value=Decimal("5"),
        )
    ]
    win.items_table.set_items(test_items)

    offer = win.to_offer()
    assert offer.company_id == "endemiks_tarim"
    assert offer.recipient_name == "Antalya Seracılık A.Ş."
    assert offer.currency_code == CurrencyCode.USD
    assert offer.quantity_unit == QuantityUnit.LITRE
    assert offer.vat_enabled is True
    assert offer.vat_rate == Decimal("10.00")
    assert offer.discount_enabled is True
    assert len(offer.items) == 1
    assert offer.items[0].description == "Sıvı Gübre 20L"

    # Başka bir pencerede load_offer ile yükle
    win2 = MainWindow()
    win2.load_offer(offer)

    assert win2.header_widget.get_recipient_name() == "Antalya Seracılık A.Ş."
    assert win2.header_widget.get_currency_code() == CurrencyCode.USD
    assert win2.header_widget.get_quantity_unit() == QuantityUnit.LITRE
    assert win2.header_widget.is_vat_enabled() is True
    assert win2.header_widget.get_vat_rate() == Decimal("10.00")
    assert win2.header_widget.is_discount_enabled() is True
    assert len(win2.items_table.get_items()) == 1

    win.close()
    win2.close()


def test_sections_widget_and_rich_text() -> None:
    """Ticari koşullar varsayılan metinleri ve zengin metin araç çubuğu çalışmalıdır."""
    sec_widget = SectionsWidget()

    # Teslimat şekli checkbox açıldığında varsayılan metin yüklenmeli
    addr_card = sec_widget._cards[SectionKey.DELIVERY_METHOD]
    assert addr_card.is_enabled() is False
    addr_card.set_enabled(True)
    assert addr_card.is_enabled() is True
    assert "Tek bir merkezi noktaya" in addr_card.get_text()

    # Ek Alan (zengin metin) araç çubuğu butonları
    notes_card = sec_widget._cards[SectionKey.ADDITIONAL_NOTES]
    notes_card.set_enabled(True)
    assert notes_card.rich_editor is not None
    notes_card.rich_editor.setPlainText("Test Notu")

    # Kalın/İtalik buton çağrıları hatasız çalışmalı
    notes_card.toolbar._toggle_bold()
    notes_card.toolbar._toggle_italic()
    notes_card.toolbar._toggle_underline()
    notes_card.toolbar._insert_bullet_list()
    notes_card.toolbar._insert_numbered_list()


def test_archive_widget_filtering_and_events() -> None:
    """Arşiv ekranında arama ve sinyal tetikleme çalışmalıdır."""
    archive = ArchiveWidget()

    offer1 = Offer(
        offer_number="20261020-001",
        offer_date=date(2026, 10, 20),
        recipient_name="Ahmet Yılmaz",
        currency_code=CurrencyCode.TRY,
        items=[OfferItem(description="Ürün 1", quantity=Decimal("1"), unit_price=Decimal("100"))],
    )
    offer2 = Offer(
        offer_number="20261020-002",
        offer_date=date(2026, 10, 20),
        recipient_name="Mehmet Öz",
        currency_code=CurrencyCode.USD,
        items=[OfferItem(description="Ürün 2", quantity=Decimal("2"), unit_price=Decimal("200"))],
    )

    archive.set_offers([offer1, offer2])
    assert archive.table.rowCount() == 2

    # Arama filtresi
    archive.search_input.setText("Ahmet")
    assert archive.table.rowCount() == 1

    archive.search_input.setText("20261020-002")
    assert archive.table.rowCount() == 1

    archive.search_input.clear()
    assert archive.table.rowCount() == 2

    # Sinyal dinleyicileri
    opened_offers: list[Offer] = []
    duplicated_offers: list[Offer] = []
    archive.open_offer_requested.connect(opened_offers.append)
    archive.duplicate_offer_requested.connect(duplicated_offers.append)

    archive.table.selectRow(0)
    archive.btn_open.click()
    assert len(opened_offers) == 1
    assert opened_offers[0].offer_number == "20261020-001"

    archive.btn_duplicate.click()
    assert len(duplicated_offers) == 1
    assert duplicated_offers[0].offer_number == "20261020-001"


def test_main_window_save_open_duplicate_flow(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """MainWindow üzerinden teklif kaydetme, arşivden açma ve kopyalama akışı."""
    import sqlite3
    from teklif_sablonu.services.excel_service import ExcelService
    from teklif_sablonu.services.offer_service import OfferService
    from teklif_sablonu.services.pdf_service import PdfService
    from teklif_sablonu.storage.repository import SqliteOfferRepository

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    mem_service = OfferService(SqliteOfferRepository(conn))

    # PDF ve Excel çıktılarını masaüstü yerine geçici test dizinine yönlendir
    custom_pdf_service = PdfService()
    monkeypatch.setattr(
        custom_pdf_service,
        "get_default_output_path",
        lambda offer_num: tmp_path / f"{offer_num}.pdf",
    )
    custom_excel_service = ExcelService()
    monkeypatch.setattr(
        custom_excel_service,
        "get_default_output_path",
        lambda offer_num: tmp_path / f"{offer_num}.xlsx",
    )

    win = MainWindow(
        offer_service=mem_service,
        pdf_service=custom_pdf_service,
        excel_service=custom_excel_service,
    )

    # 1. Geçerli teklif verileri gir
    win.header_widget.set_recipient_name("Ege Tarım San. Tic.")
    row = win.items_table._rows[0]
    row.desc_edit.setText("Toprak Düzenleyici")
    row.qty_edit.setText("20")
    row.price_edit.setText("85,00")

    # 2. Kaydet
    win.btn_save.click()
    archived = win.offer_service.list_offers()
    assert len(archived) == 1
    saved_num = archived[0].offer_number
    assert saved_num != ""
    assert win.archive_widget.table.rowCount() == 1

    # 3. Formu temizle
    win.clear_offer()
    assert win.header_widget.get_recipient_name() == ""
    assert win.items_table._rows[0].desc_edit.text() == ""

    # 4. Arşivden aç
    win.archive_widget.table.selectRow(0)
    win.archive_widget.btn_open.click()
    assert win.header_widget.get_recipient_name() == "Ege Tarım San. Tic."
    assert win.items_table._rows[0].desc_edit.text() == "Toprak Düzenleyici"

    # 5. Arşivden kopyalayarak yeni oluştur
    win.archive_widget.table.selectRow(0)
    win.archive_widget.btn_duplicate.click()
    assert win._current_offer_number == ""  # Yeni teklif olduğu için numara sıfırlandı
    assert win._source_offer_id is not None
    assert win.header_widget.get_recipient_name() == "Ege Tarım San. Tic."

    # 6. Doğrula butonunu çalıştır
    win.btn_validate.click()
    assert win.validate_current_offer().is_valid is True

    # 7. Dışa aktarım butonlarını çalıştır (PDF tmp_path altına üretilmeli)
    win.btn_export_pdf.click()
    win.btn_export_excel.click()

    QApplication.processEvents()
    win.close()


def test_ui_page_orientation_and_copyright() -> None:
    """Sayfa yönü seçimi, telif hakkı etiketi ve zengin metin araç çubuğu doğrulanmalıdır."""
    import sqlite3
    from teklif_sablonu.storage.repository import SqliteOfferRepository
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    service = OfferService(SqliteOfferRepository(conn))
    win = MainWindow(offer_service=service)

    # 1. Copyright etiketi kontrolü
    assert hasattr(win, "copyright_lbl")
    assert "Berkay Korkut" in win.copyright_lbl.text()

    # 2. Sayfa yönü combo varsayılanı ve değiştirilmesi
    assert win.header_widget.get_page_orientation() == PageOrientation.AUTO

    win.header_widget.set_page_orientation(PageOrientation.LANDSCAPE)
    assert win.header_widget.get_page_orientation() == PageOrientation.LANDSCAPE
    offer = win.to_offer()
    assert offer.page_orientation == PageOrientation.LANDSCAPE

    win.header_widget.set_page_orientation(PageOrientation.PORTRAIT)
    assert win.header_widget.get_page_orientation() == PageOrientation.PORTRAIT

    # 3. Zengin metin araç çubuğu butonlarının varlığı ve stilleri
    additional_notes_card = win.sections_widget._cards.get(SectionKey.ADDITIONAL_NOTES)
    assert additional_notes_card is not None
    assert additional_notes_card.is_rich_text is True
    assert additional_notes_card.toolbar is not None
    assert additional_notes_card.toolbar.btn_bold.property("class") == "toolbar"
    assert additional_notes_card.toolbar.btn_italic.property("class") == "toolbar"
    assert additional_notes_card.toolbar.btn_underline.property("class") == "toolbar"

    # 4. Ürün tablosunun minimum yüksekliği
    assert win.items_table.table.minimumHeight() >= 250

    QApplication.processEvents()
    win.close()


def test_ready_templates_widget_and_main_window_integration() -> None:
    """Hazır Şablonlar bileşeni ve MainWindow entegrasyonu test edilmelidir."""
    from teklif_sablonu.ui.ready_templates_widget import ReadyTemplatesWidget

    # 1. Bağımsız bileşen testi
    widget = ReadyTemplatesWidget()
    assert widget.is_packaging_enabled() is False
    assert widget.is_storage_enabled() is False

    signals_received = []
    widget.templates_changed.connect(lambda: signals_received.append(True))

    widget.set_packaging_enabled(True)
    assert widget.is_packaging_enabled() is True
    assert len(signals_received) == 1

    widget.set_storage_enabled(True)
    assert widget.is_storage_enabled() is True
    assert len(signals_received) == 2

    # Ürün Bilgileri testi
    assert widget.is_product_info_enabled() is False
    assert widget.sub_container.isHidden() is True
    widget.set_product_info_enabled(True)
    assert widget.is_product_info_enabled() is True
    assert widget.sub_container.isHidden() is False
    assert len(widget.get_selected_product_info_items()) == 0

    # Alt ögeleri seçme
    widget.set_selected_product_info_items(["quality_guarantee", "orange_juice"])
    assert widget.get_selected_product_info_items() == ["quality_guarantee", "orange_juice"]

    # Hızlı butonlar
    widget._select_all_sub_items()
    assert len(widget.get_selected_product_info_items()) == 13
    widget._clear_all_sub_items()
    assert len(widget.get_selected_product_info_items()) == 0

    widget.clear()
    assert widget.is_packaging_enabled() is False
    assert widget.is_storage_enabled() is False
    assert widget.is_product_info_enabled() is False
    assert widget.sub_container.isHidden() is True

    # 2. MainWindow entegrasyonu
    import sqlite3
    from teklif_sablonu.storage.repository import SqliteOfferRepository
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    service = OfferService(SqliteOfferRepository(conn))
    win = MainWindow(offer_service=service)

    assert hasattr(win, "ready_templates_widget")
    assert win.ready_templates_widget.is_packaging_enabled() is False
    assert win.ready_templates_widget.is_storage_enabled() is False
    assert win.ready_templates_widget.is_product_info_enabled() is False

    # Checkbox'ları işaretleyip to_offer() ile Offer'a yansıdığını doğrula
    win.ready_templates_widget.set_packaging_enabled(True)
    win.ready_templates_widget.set_storage_enabled(True)
    win.ready_templates_widget.set_product_info_enabled(True)
    win.ready_templates_widget.set_selected_product_info_items(["quality_guarantee", "lemonade_extract"])
    offer = win.to_offer()
    assert offer.template_packaging_info is True
    assert offer.template_storage_conditions is True
    assert offer.template_product_info is True
    assert offer.template_product_info_items == ["quality_guarantee", "lemonade_extract"]

    # load_offer ile geri yükleme
    offer2 = Offer(
        template_packaging_info=False,
        template_storage_conditions=True,
        template_product_info=True,
        template_product_info_items=["orange_juice"],
    )
    win.load_offer(offer2)
    assert win.ready_templates_widget.is_packaging_enabled() is False
    assert win.ready_templates_widget.is_storage_enabled() is True
    assert win.ready_templates_widget.is_product_info_enabled() is True
    assert win.ready_templates_widget.get_selected_product_info_items() == ["orange_juice"]

    # clear_offer ile sıfırlama
    win.clear_offer()
    assert win.ready_templates_widget.is_packaging_enabled() is False
    assert win.ready_templates_widget.is_storage_enabled() is False
    assert win.ready_templates_widget.is_product_info_enabled() is False

    QApplication.processEvents()
    win.close()



