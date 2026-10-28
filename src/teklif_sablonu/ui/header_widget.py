"""Teklif üst bilgi formu bileşeni (Şirket, Alıcı, Tarih, Para Birimi, Miktar Birimi, KDV, vb.)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from PySide6.QtCore import QDate, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from teklif_sablonu.config import load_companies
from teklif_sablonu.config.settings import RECIPIENT_MAX_CHARS
from teklif_sablonu.domain.enums import CurrencyCode, DocumentLanguage, PageOrientation, QuantityUnit


class HeaderWidget(QWidget):
    """Teklif genel üst bilgi ayarlarını yöneten bileşen."""

    values_changed = Signal()
    quantity_unit_changed = Signal(QuantityUnit)
    currency_changed = Signal(CurrencyCode)
    vat_changed = Signal(bool, Decimal)
    discount_changed = Signal(bool)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        group = QGroupBox("Teklif Üst Bilgileri")
        grid = QGridLayout(group)
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(12)

        # 1. Şirket Seçimi
        grid.addWidget(QLabel("Şirket:"), 0, 0)
        self.company_combo = QComboBox()
        self.companies = load_companies()
        for comp in self.companies:
            self.company_combo.addItem(comp.name, comp.id)
        self.company_combo.currentIndexChanged.connect(self._on_changed)
        grid.addWidget(self.company_combo, 0, 1)

        # 2. Teklif Tarihi
        grid.addWidget(QLabel("Teklif Tarihi:"), 0, 2)
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        today = date.today()
        self.date_edit.setDate(QDate(today.year, today.month, today.day))
        self.date_edit.dateChanged.connect(self._on_changed)
        grid.addWidget(self.date_edit, 0, 3)

        # 3. Alıcı Bilgisi (Max RECIPIENT_MAX_CHARS)
        grid.addWidget(QLabel("Alıcı / Müşteri:"), 1, 0)
        recipient_layout = QHBoxLayout()
        self.recipient_input = QLineEdit()
        self.recipient_input.setMaxLength(RECIPIENT_MAX_CHARS)
        self.recipient_input.setPlaceholderText("Teklifin verileceği firma veya şahıs adı")
        self.recipient_input.textChanged.connect(self._update_recipient_counter)
        self.recipient_counter_lbl = QLabel(f"0/{RECIPIENT_MAX_CHARS}")
        self.recipient_counter_lbl.setStyleSheet("color: #718096; font-size: 11px;")
        recipient_layout.addWidget(self.recipient_input)
        recipient_layout.addWidget(self.recipient_counter_lbl)
        grid.addLayout(recipient_layout, 1, 1, 1, 3)

        # 4. Para Birimi (Radyo Buton Grubu)
        grid.addWidget(QLabel("Para Birimi:"), 2, 0)
        curr_layout = QHBoxLayout()
        self.curr_btn_group = QButtonGroup(self)
        self.rb_try = QRadioButton("TRY (₺)")
        self.rb_usd = QRadioButton("USD ($)")
        self.rb_eur = QRadioButton("EUR (€)")
        self.rb_try.setChecked(True)
        self.curr_btn_group.addButton(self.rb_try, 0)
        self.curr_btn_group.addButton(self.rb_usd, 1)
        self.curr_btn_group.addButton(self.rb_eur, 2)
        curr_layout.addWidget(self.rb_try)
        curr_layout.addWidget(self.rb_usd)
        curr_layout.addWidget(self.rb_eur)
        curr_layout.addStretch()
        self.curr_btn_group.idToggled.connect(self._on_currency_toggled)
        grid.addLayout(curr_layout, 2, 1)

        # 5. Miktar Birimi (Teklif Genelinde Tek Seçim: Adet / Litre)
        grid.addWidget(QLabel("Miktar Birimi:"), 2, 2)
        unit_layout = QHBoxLayout()
        self.unit_btn_group = QButtonGroup(self)
        self.rb_piece = QRadioButton("Adet")
        self.rb_litre = QRadioButton("Litre")
        self.rb_piece.setChecked(True)
        self.unit_btn_group.addButton(self.rb_piece, 0)
        self.unit_btn_group.addButton(self.rb_litre, 1)
        unit_layout.addWidget(self.rb_piece)
        unit_layout.addWidget(self.rb_litre)
        unit_layout.addStretch()
        self.unit_btn_group.idToggled.connect(self._on_unit_toggled)
        grid.addLayout(unit_layout, 2, 3)

        # 6. KDV Uygulama ve Teklif-Geneli KDV Oranı
        grid.addWidget(QLabel("KDV Durumu:"), 3, 0)
        vat_layout = QHBoxLayout()
        self.vat_checkbox = QCheckBox("KDV Uygula")
        self.vat_checkbox.setChecked(False)
        self.vat_spin = QDoubleSpinBox()
        self.vat_spin.setRange(0.00, 100.00)
        self.vat_spin.setDecimals(2)
        self.vat_spin.setValue(20.00)
        self.vat_spin.setSuffix(" %")
        self.vat_spin.setEnabled(False)
        self.vat_checkbox.toggled.connect(self._on_vat_toggled)
        self.vat_spin.valueChanged.connect(self._on_vat_rate_changed)
        vat_layout.addWidget(self.vat_checkbox)
        vat_layout.addWidget(self.vat_spin)
        vat_layout.addStretch()
        grid.addLayout(vat_layout, 3, 1)

        # 7. İskonto Uygulama & Marka Logosu Göster
        grid.addWidget(QLabel("Ek Seçenekler:"), 3, 2)
        opts_layout = QHBoxLayout()
        self.discount_checkbox = QCheckBox("İskonto Uygula")
        self.discount_checkbox.setChecked(False)
        self.discount_checkbox.toggled.connect(self._on_discount_toggled)

        self.brand_logo_checkbox = QCheckBox("Marka Logosu Göster")
        self.brand_logo_checkbox.setChecked(False)
        self.brand_logo_checkbox.toggled.connect(self._on_changed)

        opts_layout.addWidget(self.discount_checkbox)
        opts_layout.addWidget(self.brand_logo_checkbox)
        opts_layout.addStretch()
        grid.addLayout(opts_layout, 3, 3)

        # 8. Sayfa Yönü (PDF & Excel: Otomatik / Dikey / Yatay)
        grid.addWidget(QLabel("Sayfa Yönü:"), 4, 0)
        self.orientation_combo = QComboBox()
        self.orientation_combo.addItem("🔄 Otomatik (Sütun Sayısına Göre)", PageOrientation.AUTO.value)
        self.orientation_combo.addItem("📐 Dikey (Portrait)", PageOrientation.PORTRAIT.value)
        self.orientation_combo.addItem("📐 Yatay (Landscape)", PageOrientation.LANDSCAPE.value)
        self.orientation_combo.currentIndexChanged.connect(self._on_changed)
        grid.addWidget(self.orientation_combo, 4, 1)

        # 9. Belge Dili (TR / EN)
        grid.addWidget(QLabel("Belge Dili:"), 4, 2)
        self.lang_combo = QComboBox()
        self.lang_combo.addItem("TR", DocumentLanguage.TR.value)
        self.lang_combo.addItem("EN", DocumentLanguage.EN.value)
        self.lang_combo.currentIndexChanged.connect(self._on_changed)
        grid.addWidget(self.lang_combo, 4, 3)

        # 10. PDF Yazı Boyutu (Font Size)
        grid.addWidget(QLabel("PDF Yazı Boyutu:"), 5, 0)
        self.font_size_combo = QComboBox()
        self.font_size_combo.addItem("8.0 pt (Varsayılan - Standart)", 8.0)
        self.font_size_combo.addItem("7.5 pt (Küçük)", 7.5)
        self.font_size_combo.addItem("7.0 pt (Çok Küçük / Kompakt)", 7.0)
        self.font_size_combo.addItem("6.5 pt (Ekstra Kompakt)", 6.5)
        self.font_size_combo.addItem("8.5 pt (Büyük)", 8.5)
        self.font_size_combo.addItem("9.0 pt (Çok Büyük)", 9.0)
        self.font_size_combo.currentIndexChanged.connect(self._on_changed)
        grid.addWidget(self.font_size_combo, 5, 1)

        main_layout.addWidget(group)

    def _update_recipient_counter(self) -> None:
        count = len(self.recipient_input.text())
        self.recipient_counter_lbl.setText(f"{count}/{RECIPIENT_MAX_CHARS}")
        if count >= RECIPIENT_MAX_CHARS:
            self.recipient_counter_lbl.setStyleSheet("color: #E53E3E; font-weight: bold; font-size: 11px;")
        else:
            self.recipient_counter_lbl.setStyleSheet("color: #718096; font-size: 11px;")
        self._on_changed()

    def _on_currency_toggled(self) -> None:
        self.currency_changed.emit(self.get_currency_code())
        self._on_changed()

    def _on_unit_toggled(self) -> None:
        self.quantity_unit_changed.emit(self.get_quantity_unit())
        self._on_changed()

    def _on_vat_toggled(self, checked: bool) -> None:
        self.vat_spin.setEnabled(checked)
        self.vat_changed.emit(checked, self.get_vat_rate())
        self._on_changed()

    def _on_vat_rate_changed(self) -> None:
        if self.vat_checkbox.isChecked():
            self.vat_changed.emit(True, self.get_vat_rate())
        self._on_changed()

    def _on_discount_toggled(self, checked: bool) -> None:
        self.discount_changed.emit(checked)
        self._on_changed()

    def _on_changed(self) -> None:
        self.values_changed.emit()

    # ── Getter & Setter Metotları ──

    def get_company_id(self) -> str:
        return str(self.company_combo.currentData())

    def set_company_id(self, comp_id: str) -> None:
        idx = self.company_combo.findData(comp_id)
        if idx >= 0:
            self.company_combo.setCurrentIndex(idx)

    def get_offer_date(self) -> date:
        qdate = self.date_edit.date()
        return date(qdate.year(), qdate.month(), qdate.day())

    def set_offer_date(self, d: date) -> None:
        self.date_edit.setDate(QDate(d.year, d.month, d.day))

    def get_recipient_name(self) -> str:
        return self.recipient_input.text().strip()

    def set_recipient_name(self, name: str) -> None:
        self.recipient_input.setText(name)

    def get_currency_code(self) -> CurrencyCode:
        if self.rb_usd.isChecked():
            return CurrencyCode.USD
        if self.rb_eur.isChecked():
            return CurrencyCode.EUR
        return CurrencyCode.TRY

    def set_currency_code(self, curr: CurrencyCode) -> None:
        if curr == CurrencyCode.USD:
            self.rb_usd.setChecked(True)
        elif curr == CurrencyCode.EUR:
            self.rb_eur.setChecked(True)
        else:
            self.rb_try.setChecked(True)

    def get_quantity_unit(self) -> QuantityUnit:
        if self.rb_litre.isChecked():
            return QuantityUnit.LITRE
        return QuantityUnit.PIECE

    def set_quantity_unit(self, unit: QuantityUnit) -> None:
        if unit == QuantityUnit.LITRE:
            self.rb_litre.setChecked(True)
        else:
            self.rb_piece.setChecked(True)

    def is_vat_enabled(self) -> bool:
        return self.vat_checkbox.isChecked()

    def set_vat_enabled(self, enabled: bool) -> None:
        self.vat_checkbox.setChecked(enabled)
        self.vat_spin.setEnabled(enabled)

    def get_vat_rate(self) -> Decimal:
        return Decimal(str(self.vat_spin.value()))

    def set_vat_rate(self, rate: Decimal) -> None:
        self.vat_spin.setValue(float(rate))

    def is_discount_enabled(self) -> bool:
        return self.discount_checkbox.isChecked()

    def set_discount_enabled(self, enabled: bool) -> None:
        self.discount_checkbox.setChecked(enabled)

    def is_brand_logo_visible(self) -> bool:
        return self.brand_logo_checkbox.isChecked()

    def set_brand_logo_visible(self, visible: bool) -> None:
        self.brand_logo_checkbox.setChecked(visible)

    def get_page_orientation(self) -> PageOrientation:
        data = self.orientation_combo.currentData()
        try:
            return PageOrientation(data)
        except ValueError:
            return PageOrientation.AUTO

    def set_page_orientation(self, orientation: PageOrientation | str) -> None:
        val = orientation.value if isinstance(orientation, PageOrientation) else str(orientation)
        idx = self.orientation_combo.findData(val)
        if idx >= 0:
            self.orientation_combo.setCurrentIndex(idx)
        else:
            self.orientation_combo.setCurrentIndex(0)

    def get_document_language(self) -> DocumentLanguage:
        data = self.lang_combo.currentData()
        try:
            return DocumentLanguage(data)
        except ValueError:
            return DocumentLanguage.TR

    def set_document_language(self, lang: DocumentLanguage | str) -> None:
        val = lang.value if isinstance(lang, DocumentLanguage) else str(lang)
        idx = self.lang_combo.findData(val)
        if idx >= 0:
            self.lang_combo.setCurrentIndex(idx)
        else:
            self.lang_combo.setCurrentIndex(0)

    def get_pdf_font_size(self) -> float:
        """Kullanıcının seçtiği PDF font büyüklüğünü döndürür (varsayılan: 8.0 pt)."""
        data = self.font_size_combo.currentData()
        try:
            return float(data) if data is not None else 8.0
        except (ValueError, TypeError):
            return 8.0

    def set_pdf_font_size(self, size: float | None) -> None:
        """PDF font büyüklüğünü ayarlar."""
        target = float(size) if size is not None else 8.0
        for idx in range(self.font_size_combo.count()):
            val = self.font_size_combo.itemData(idx)
            if val is not None and abs(float(val) - target) < 0.05:
                self.font_size_combo.setCurrentIndex(idx)
                return
        self.font_size_combo.setCurrentIndex(0)
