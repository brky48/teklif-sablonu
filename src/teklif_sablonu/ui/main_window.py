"""Ana pencere — Teklif Şablonu uygulamasının merkezi kullanıcı arayüzü."""

from __future__ import annotations

import copy
from datetime import date
from decimal import Decimal
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from teklif_sablonu.domain.calculator import calculate_offer_totals
from teklif_sablonu.domain.enums import ColumnKey, CurrencyCode, QuantityUnit
from teklif_sablonu.domain.models import Offer, OfferItem
from teklif_sablonu.domain.validators import ValidationResult, validate_offer
from teklif_sablonu.services.excel_service import ExcelService
from teklif_sablonu.services.offer_service import OfferService
from teklif_sablonu.services.pdf_service import PdfService
from teklif_sablonu.ui.archive_widget import ArchiveWidget
from teklif_sablonu.ui.column_selector_widget import ColumnSelectorWidget
from teklif_sablonu.ui.header_widget import HeaderWidget
from teklif_sablonu.ui.items_table_widget import ItemsTableWidget
from teklif_sablonu.ui.sections_widget import SectionsWidget
from teklif_sablonu.ui.styles import MAIN_STYLE
from teklif_sablonu.ui.totals_widget import TotalsWidget


class MainWindow(QMainWindow):
    """Teklif hazırlama ve arşiv ana penceresi."""

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        offer_service: OfferService | None = None,
        pdf_service: PdfService | None = None,
        excel_service: ExcelService | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Teklif Şablonu — Endemiks")
        self.resize(1180, 850)
        self.setMinimumSize(960, 680)

        self.offer_service = offer_service or OfferService()
        self.pdf_service = pdf_service or PdfService()
        self.excel_service = excel_service or ExcelService()
        self._current_offer_id: int | None = None
        self._current_offer_number: str = ""
        self._source_offer_id: int | None = None

        self.setStyleSheet(MAIN_STYLE)
        self._init_ui()
        self._connect_signals()
        self._recalculate_all()
        self.refresh_archive()

    def _init_ui(self) -> None:
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)

        self.tab_widget = QTabWidget()

        # ── SEKME 1: Teklif Düzenle ──
        editor_tab = QWidget()
        editor_layout = QVBoxLayout(editor_tab)
        editor_layout.setContentsMargins(0, 0, 0, 0)

        # Uzun formlar için kaydırılabilir alan (QScrollArea)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(14)
        scroll_layout.setContentsMargins(12, 12, 12, 12)

        # 1. Üst bilgiler
        self.header_widget = HeaderWidget()
        scroll_layout.addWidget(self.header_widget)

        # 2. Sütun seçici
        self.column_selector = ColumnSelectorWidget()
        scroll_layout.addWidget(self.column_selector)

        # 3. Ürün tablosu
        self.items_table = ItemsTableWidget()
        scroll_layout.addWidget(self.items_table)

        # 4. Genel toplam özeti kartı
        self.totals_widget = TotalsWidget()
        scroll_layout.addWidget(self.totals_widget)

        # 5. Ticari koşullar ve ek alan
        self.sections_widget = SectionsWidget()
        scroll_layout.addWidget(self.sections_widget)

        # 6. Alt aksiyon butonları
        action_bar = QHBoxLayout()
        self.btn_new = QPushButton("📄 Yeni Teklif")
        self.btn_new.setProperty("class", "secondary")
        self.btn_new.clicked.connect(self.clear_offer)

        self.btn_validate = QPushButton("✓ Teklifi Doğrula")
        self.btn_validate.setProperty("class", "secondary")
        self.btn_validate.clicked.connect(self._on_validate_clicked)

        self.btn_save = QPushButton("💾 Teklifi Kaydet")
        self.btn_save.clicked.connect(self._on_save_clicked)

        self.btn_export_pdf = QPushButton("📑 PDF Oluştur")
        self.btn_export_pdf.setProperty("class", "secondary")
        self.btn_export_pdf.setToolTip("PDF dışa aktarma (Prompt 5'te etkinleştirilecek)")
        self.btn_export_pdf.clicked.connect(self._on_export_pdf_clicked)

        self.btn_export_excel = QPushButton("📊 Excel Oluştur")
        self.btn_export_excel.setProperty("class", "secondary")
        self.btn_export_excel.setToolTip("Excel dışa aktarma (Prompt 5'te etkinleştirilecek)")
        self.btn_export_excel.clicked.connect(self._on_export_excel_clicked)

        action_bar.addWidget(self.btn_new)
        action_bar.addWidget(self.btn_validate)
        action_bar.addWidget(self.btn_save)
        action_bar.addSpacing(20)
        action_bar.addWidget(self.btn_export_pdf)
        action_bar.addWidget(self.btn_export_excel)
        action_bar.addStretch()

        scroll_layout.addLayout(action_bar)
        scroll_area.setWidget(scroll_content)
        editor_layout.addWidget(scroll_area)

        self.tab_widget.addTab(editor_tab, "📝 Teklif Hazırla")

        # ── SEKME 2: Teklif Arşivi ──
        self.archive_widget = ArchiveWidget()
        self.tab_widget.addTab(self.archive_widget, "📁 Teklif Arşivi")

        main_layout.addWidget(self.tab_widget)

        # Durum Çubuğu
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Hazır")

    def _connect_signals(self) -> None:
        """Bileşenler arası sinyal ve veri akışı bağlantıları."""
        # Üst bilgi değişiklikleri
        self.header_widget.quantity_unit_changed.connect(self._on_quantity_unit_changed)
        self.header_widget.currency_changed.connect(self._on_currency_changed)
        self.header_widget.vat_changed.connect(self._on_vat_changed)
        self.header_widget.discount_changed.connect(self._on_discount_changed)
        self.header_widget.values_changed.connect(self._recalculate_all)

        # Sütun seçici değişiklikleri
        self.column_selector.columns_changed.connect(self.items_table.set_selected_columns)

        # Tablo satır değişiklikleri
        self.items_table.items_changed.connect(self._recalculate_all)

        # Arşiv sinyalleri
        self.archive_widget.open_offer_requested.connect(self._on_open_offer_from_archive)
        self.archive_widget.duplicate_offer_requested.connect(self._on_duplicate_offer_from_archive)

    # ── Dinamik Olay İşleyicileri ──

    def _on_quantity_unit_changed(self, unit: QuantityUnit) -> None:
        self.column_selector.set_quantity_unit(unit)
        self.items_table.set_quantity_unit(unit)
        self._recalculate_all()

    def _on_currency_changed(self, currency: CurrencyCode) -> None:
        self.items_table.set_currency(currency)
        self._recalculate_all()

    def _on_vat_changed(self, enabled: bool, rate: Decimal) -> None:
        self.column_selector.update_feature_dependencies(
            vat_enabled=enabled,
            discount_enabled=self.header_widget.is_discount_enabled(),
        )
        self.items_table.set_vat(enabled, rate)
        self._recalculate_all()

    def _on_discount_changed(self, enabled: bool) -> None:
        self.column_selector.update_feature_dependencies(
            vat_enabled=self.header_widget.is_vat_enabled(),
            discount_enabled=enabled,
        )
        self.items_table.set_discount(enabled)
        self._recalculate_all()

    def _recalculate_all(self) -> None:
        """Domain calculator modülünü kullanarak genel toplamları anlık hesaplar."""
        items = self.items_table.get_items()
        curr = self.header_widget.get_currency_code()
        vat_enabled = self.header_widget.is_vat_enabled()
        vat_rate = self.header_widget.get_vat_rate()
        discount_enabled = self.header_widget.is_discount_enabled()

        self.totals_widget.update_features(
            currency=curr,
            vat_enabled=vat_enabled,
            vat_rate=vat_rate,
            discount_enabled=discount_enabled,
        )

        _, totals = calculate_offer_totals(
            items,
            vat_rate=vat_rate,
            vat_enabled=vat_enabled,
            discount_enabled=discount_enabled,
        )
        self.totals_widget.update_totals(totals)

        valid_count = len([i for i in items if not i.is_empty()])
        self.status_bar.showMessage(
            f"Geçerli Ürün Sayısı: {valid_count} | Para Birimi: {curr.value} | Ara Toplam: {totals.subtotal} {curr.symbol}"
        )

    # ── Model Dönüşüm ve Veri Metotları ──

    def to_offer(self) -> Offer:
        """Arayüzdeki tüm verileri tek bir domain Offer modeline dönüştürür."""
        return Offer(
            id=self._current_offer_id,
            offer_number=self._current_offer_number,
            offer_date=self.header_widget.get_offer_date(),
            company_id=self.header_widget.get_company_id(),
            recipient_name=self.header_widget.get_recipient_name(),
            currency_code=self.header_widget.get_currency_code(),
            quantity_unit=self.header_widget.get_quantity_unit(),
            vat_enabled=self.header_widget.is_vat_enabled(),
            vat_rate=self.header_widget.get_vat_rate(),
            discount_enabled=self.header_widget.is_discount_enabled(),
            brand_logo_visible=self.header_widget.is_brand_logo_visible(),
            selected_columns=self.column_selector.get_selected_columns(),
            items=self.items_table.get_items(),
            sections=self.sections_widget.get_sections(),
            source_offer_id=self._source_offer_id,
        )

    def load_offer(self, offer: Offer) -> None:
        """Verilen domain Offer modelini tüm arayüz bileşenlerine aktarır."""
        self._current_offer_id = offer.id
        self._current_offer_number = offer.offer_number
        self._source_offer_id = offer.source_offer_id

        self.header_widget.set_company_id(offer.company_id)
        self.header_widget.set_offer_date(offer.offer_date)
        self.header_widget.set_recipient_name(offer.recipient_name)
        self.header_widget.set_currency_code(offer.currency_code)
        self.header_widget.set_quantity_unit(offer.quantity_unit)
        self.header_widget.set_vat_enabled(offer.vat_enabled)
        self.header_widget.set_vat_rate(offer.vat_rate)
        self.header_widget.set_discount_enabled(offer.discount_enabled)
        self.header_widget.set_brand_logo_visible(offer.brand_logo_visible)

        self.column_selector.set_quantity_unit(offer.quantity_unit)
        self.column_selector.update_feature_dependencies(
            vat_enabled=offer.vat_enabled,
            discount_enabled=offer.discount_enabled,
        )
        self.column_selector.set_selected_columns(offer.selected_columns)

        self.items_table.set_quantity_unit(offer.quantity_unit)
        self.items_table.set_currency(offer.currency_code)
        self.items_table.set_vat(offer.vat_enabled, offer.vat_rate)
        self.items_table.set_discount(offer.discount_enabled)
        self.items_table.set_selected_columns(offer.selected_columns)
        self.items_table.set_items(offer.items)

        self.sections_widget.set_sections(offer.sections)
        self._recalculate_all()

    def clear_offer(self) -> None:
        """Arayüzü sıfırlayarak yeni boş bir teklif başlatır."""
        self._current_offer_id = None
        self._current_offer_number = ""
        self._source_offer_id = None

        self.header_widget.set_company_id("endemiks_tarim")
        self.header_widget.set_offer_date(date.today())
        self.header_widget.set_recipient_name("")
        self.header_widget.set_currency_code(CurrencyCode.TRY)
        self.header_widget.set_quantity_unit(QuantityUnit.PIECE)
        self.header_widget.set_vat_enabled(False)
        self.header_widget.set_vat_rate(Decimal("20.00"))
        self.header_widget.set_discount_enabled(False)
        self.header_widget.set_brand_logo_visible(False)

        self.column_selector.set_quantity_unit(QuantityUnit.PIECE)
        self.column_selector.update_feature_dependencies(vat_enabled=False, discount_enabled=False)

        self.items_table.set_quantity_unit(QuantityUnit.PIECE)
        self.items_table.set_currency(CurrencyCode.TRY)
        self.items_table.set_vat(False, Decimal("20.00"))
        self.items_table.set_discount(False)
        self.items_table.set_selected_columns(self.column_selector.get_selected_columns())
        self.items_table.set_items([])

        self.sections_widget.set_sections([])
        self._recalculate_all()
        self.status_bar.showMessage("Yeni teklif oluşturuldu.")

    def validate_current_offer(self) -> ValidationResult:
        """Domain doğrulama modülünü çalıştırarak sonucu döndürür."""
        offer = self.to_offer()
        return validate_offer(offer)

    # ── Aksiyon Butonu İşleyicileri ──

    def _on_validate_clicked(self) -> None:
        result = self.validate_current_offer()
        if result.is_valid:
            QMessageBox.information(
                self,
                "Doğrulama Başarılı",
                "Teklif tüm kurallara uygundur. Kaydedilebilir veya dışa aktarılabilir.",
            )
            self.status_bar.showMessage("✓ Teklif doğrulandı, hata yok.")
        else:
            errors_str = "\n• ".join(str(e) for e in result.errors)
            QMessageBox.warning(
                self,
                "Doğrulama Hataları",
                f"Lütfen aşağıdaki hataları düzeltin:\n\n• {errors_str}",
            )
            self.status_bar.showMessage(f"⚠ {len(result.errors)} doğrulama hatası bulundu!")

    def refresh_archive(self) -> None:
        """Kayıtlı teklifleri veritabanından çekerek arşivi günceller."""
        offers = self.offer_service.list_offers()
        self.archive_widget.set_offers(offers)

    def _on_save_clicked(self) -> None:
        result = self.validate_current_offer()
        if not result.is_valid:
            self._on_validate_clicked()
            return

        try:
            offer = self.to_offer()
            saved_offer = self.offer_service.save_offer(offer)
            self._current_offer_id = saved_offer.id
            self._current_offer_number = saved_offer.offer_number
            self.refresh_archive()

            QMessageBox.information(
                self,
                "Teklif Kaydedildi",
                f"Teklif başarıyla kaydedildi.\nTeklif Numarası: {saved_offer.offer_number}",
            )
            self.status_bar.showMessage(f"Teklif kaydedildi: {saved_offer.offer_number}")
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Kayıt Hatası",
                f"Teklif kaydedilirken bir hata oluştu:\n{exc}",
            )
            self.status_bar.showMessage("❌ Teklif kaydedilemedi.")

    def _on_open_offer_from_archive(self, offer: Offer) -> None:
        self.load_offer(copy.deepcopy(offer))
        self.tab_widget.setCurrentIndex(0)
        self.status_bar.showMessage(f"Teklif açıldı: {offer.offer_number}")

    def _on_duplicate_offer_from_archive(self, source_offer: Offer) -> None:
        """Teklifi kopyalayarak yeni bir teklif oluşturur; kaynak teklif değişmeden kalır."""
        try:
            if source_offer.id is not None:
                dup = self.offer_service.duplicate_offer(source_offer.id)
            else:
                dup = copy.deepcopy(source_offer)
                dup.id = None
                dup.offer_number = ""
                dup.offer_date = date.today()

            self.load_offer(dup)
            self.tab_widget.setCurrentIndex(0)
            QMessageBox.information(
                self,
                "Teklif Kopyalandı",
                f"'{source_offer.offer_number}' nolu teklif temel alınarak yeni bir teklif kopyası oluşturuldu.\nOrijinal teklif değişmemiştir.",
            )
            self.status_bar.showMessage(f"Kopyalandı: {source_offer.offer_number} -> Yeni Teklif")
        except Exception as exc:
            QMessageBox.critical(self, "Kopyalama Hatası", f"Teklif kopyalanamadı:\n{exc}")

    def _on_export_pdf_clicked(self) -> None:
        result = self.validate_current_offer()
        if not result.is_valid:
            self._on_validate_clicked()
            return

        # Teklif henüz kaydedilmemişse önce veritabanına kaydet (böylece numarası oluşur)
        if not self._current_offer_number:
            self._on_save_clicked()
            if not self._current_offer_number:
                return

        offer = self.to_offer()
        target_path = self.pdf_service.get_default_output_path(offer.offer_number)

        # Dosya çakışma kontrolü (Bölüm 9.4)
        if target_path.exists():
            reply = QMessageBox.question(
                self,
                "Dosya Zaten Mevcut",
                f"'{target_path.name}' Masaüstünde zaten mevcut.\n\nÜzerine yazılsın mı?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Cancel:
                return
            elif reply == QMessageBox.StandardButton.No:
                custom_path, _ = QFileDialog.getSaveFileName(
                    self,
                    "PDF Olarak Farklı Kaydet",
                    str(target_path),
                    "PDF Belgeleri (*.pdf)",
                )
                if not custom_path:
                    return
                target_path = Path(custom_path)

        try:
            out_file = self.pdf_service.generate_pdf(offer, target_path)
            QMessageBox.information(
                self,
                "PDF Başarıyla Oluşturuldu",
                f"Teklif PDF belgesi başarıyla oluşturuldu!\n\nDosya: {out_file.name}\nKonum: {out_file}",
            )
            self.status_bar.showMessage(f"PDF oluşturuldu: {out_file.name}")
        except Exception as exc:
            QMessageBox.critical(
                self,
                "PDF Üretim Hatası",
                f"PDF oluşturulurken bir hata meydana geldi:\n{exc}",
            )
            self.status_bar.showMessage("❌ PDF oluşturulamadı.")

    def _on_export_excel_clicked(self) -> None:
        result = self.validate_current_offer()
        if not result.is_valid:
            self._on_validate_clicked()
            return

        # Teklif henüz kaydedilmemişse önce veritabanına kaydet
        if not self._current_offer_number:
            self._on_save_clicked()
            if not self._current_offer_number:
                return

        offer = self.to_offer()
        target_path = self.excel_service.get_default_output_path(offer.offer_number)

        # Dosya çakışma kontrolü (Bölüm 10)
        if target_path.exists():
            reply = QMessageBox.question(
                self,
                "Dosya Zaten Mevcut",
                f"'{target_path.name}' Masaüstünde zaten mevcut.\n\nÜzerine yazılsın mı?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Cancel:
                return
            elif reply == QMessageBox.StandardButton.No:
                custom_path, _ = QFileDialog.getSaveFileName(
                    self,
                    "Excel Olarak Farklı Kaydet",
                    str(target_path),
                    "Excel Belgeleri (*.xlsx)",
                )
                if not custom_path:
                    return
                target_path = Path(custom_path)

        try:
            out_file = self.excel_service.generate_excel(offer, target_path)
            QMessageBox.information(
                self,
                "Excel Başarıyla Oluşturuldu",
                f"Teklif Excel belgesi başarıyla oluşturuldu!\n\nDosya: {out_file.name}\nKonum: {out_file}",
            )
            self.status_bar.showMessage(f"Excel oluşturuldu: {out_file.name}")
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Excel Üretim Hatası",
                f"Excel oluşturulurken bir hata meydana geldi:\n{exc}",
            )
            self.status_bar.showMessage("❌ Excel oluşturulamadı.")

