"""Dinamik ürün tablosu bileşeni (Satır ekle/sil/kopyala, anlık hesaplama ve sütun yönetimi)."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from teklif_sablonu.domain.calculator import (
    DiscountExceedsTotalError,
    calculate_item,
)
from teklif_sablonu.domain.enums import (
    FIXED_COLUMN_ORDER,
    ColumnKey,
    CurrencyCode,
    DiscountType,
    QuantityUnit,
)
from teklif_sablonu.domain.models import OfferItem, OfferItemCalculation
from teklif_sablonu.domain.parsers import (
    format_decimal_tr,
    parse_turkish_decimal,
)


class ItemRowWidgets:
    """Tek bir ürün satırındaki girdi ve etiket bileşenlerini tutar."""

    def __init__(self, row: int, table: QTableWidget) -> None:
        self.row = row
        self.table = table

        # Girdi bileşenleri
        self.code_edit = QLineEdit()
        self.code_edit.setMaxLength(64)
        self.code_edit.setPlaceholderText("Ürün Kodu")

        self.desc_edit = QLineEdit()
        self.desc_edit.setMaxLength(64)
        self.desc_edit.setPlaceholderText("Ürün Açıklaması *")

        self.qty_edit = QLineEdit()
        self.qty_edit.setPlaceholderText("0,00")
        self.qty_edit.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.pallet_edit = QLineEdit()
        self.pallet_edit.setPlaceholderText("0,00")
        self.pallet_edit.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.price_edit = QLineEdit()
        self.price_edit.setPlaceholderText("0,00")
        self.price_edit.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.disc_type_combo = QComboBox()
        self.disc_type_combo.addItem(DiscountType.NONE.label_tr, DiscountType.NONE)
        self.disc_type_combo.addItem(f"{DiscountType.RATE.label_tr} (%)", DiscountType.RATE)
        self.disc_type_combo.addItem(DiscountType.AMOUNT.label_tr, DiscountType.AMOUNT)

        self.disc_val_edit = QLineEdit()
        self.disc_val_edit.setPlaceholderText("0,00")
        self.disc_val_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.disc_val_edit.setEnabled(False)

        # Hesaplanan salt-okunur etiketler
        self.vat_lbl = QLabel("%0")
        self.vat_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.vat_lbl.setStyleSheet("color: #4A5568;")

        self.total_lbl = QLabel("0,00")
        self.total_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.total_lbl.setStyleSheet("font-weight: 600;")

        self.disc_total_lbl = QLabel("0,00")
        self.disc_total_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.disc_total_lbl.setStyleSheet("font-weight: 600; color: #2B6CB0;")

        self.vat_total_lbl = QLabel("0,00")
        self.vat_total_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.vat_total_lbl.setStyleSheet("font-weight: 600; color: #2B6CB0;")

    def to_offer_item(self) -> OfferItem:
        """Widget üzerindeki değerleri OfferItem modeline dönüştürür."""
        raw_disc = self.disc_type_combo.currentData()
        try:
            disc_type = DiscountType(raw_disc)
        except (ValueError, TypeError):
            disc_type = DiscountType.NONE

        qty = parse_turkish_decimal(self.qty_edit.text()) or Decimal("0")
        pallet = parse_turkish_decimal(self.pallet_edit.text())
        price = parse_turkish_decimal(self.price_edit.text()) or Decimal("0")
        disc_val = parse_turkish_decimal(self.disc_val_edit.text()) or Decimal("0")

        return OfferItem(
            position=self.row,
            product_code=self.code_edit.text().strip(),
            description=self.desc_edit.text().strip(),
            quantity=qty,
            pallet=pallet,
            unit_price=price,
            discount_type=disc_type,
            discount_value=disc_val,
        )

    def load_from_item(self, item: OfferItem) -> None:
        """OfferItem verisini widget alanlarına doldurur."""
        self.code_edit.setText(item.product_code)
        self.desc_edit.setText(item.description)
        if item.quantity > Decimal("0"):
            self.qty_edit.setText(format_decimal_tr(item.quantity))
        else:
            self.qty_edit.clear()

        if item.pallet is not None and item.pallet > Decimal("0"):
            self.pallet_edit.setText(format_decimal_tr(item.pallet))
        else:
            self.pallet_edit.clear()

        if item.unit_price > Decimal("0"):
            self.price_edit.setText(format_decimal_tr(item.unit_price))
        else:
            self.price_edit.clear()

        idx = self.disc_type_combo.findData(item.discount_type.value)
        if idx < 0:
            idx = self.disc_type_combo.findData(item.discount_type)
        if idx >= 0:
            self.disc_type_combo.setCurrentIndex(idx)

        if item.discount_value > Decimal("0"):
            self.disc_val_edit.setText(format_decimal_tr(item.discount_value))
        else:
            self.disc_val_edit.clear()

        self.disc_val_edit.setEnabled(item.discount_type != DiscountType.NONE)


class ItemsTableWidget(QWidget):
    """Dinamik ürün tablosu ana bileşeni."""

    items_changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._rows: list[ItemRowWidgets] = []
        self._quantity_unit = QuantityUnit.PIECE
        self._currency = CurrencyCode.TRY
        self._vat_enabled = False
        self._vat_rate = Decimal("0")
        self._discount_enabled = False
        self._selected_columns = list(FIXED_COLUMN_ORDER)
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        group = QGroupBox("Teklif Edilen Ürünler")
        layout = QVBoxLayout(group)

        # Tablo araç çubuğu
        toolbar = QHBoxLayout()
        self.btn_add = QPushButton("➕ Satır Ekle")
        self.btn_add.clicked.connect(lambda: self.add_row())

        self.btn_duplicate = QPushButton("📋 Seçili Satırı Kopyala")
        self.btn_duplicate.setProperty("class", "secondary")
        self.btn_duplicate.clicked.connect(self._duplicate_selected_row)

        self.btn_delete = QPushButton("🗑️ Seçili Satırı Sil")
        self.btn_delete.setProperty("class", "danger")
        self.btn_delete.clicked.connect(self._delete_selected_row)

        toolbar.addWidget(self.btn_add)
        toolbar.addWidget(self.btn_duplicate)
        toolbar.addWidget(self.btn_delete)
        toolbar.addStretch()

        layout.addLayout(toolbar)

        # Tablo Yapılandırması
        self.table = QTableWidget(0, len(FIXED_COLUMN_ORDER))
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.verticalHeader().setDefaultSectionSize(38)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setStretchLastSection(False)

        self._update_column_headers()
        layout.addWidget(self.table)
        main_layout.addWidget(group)

        # Başlangıçta 1 boş satır ekle (Bölüm 6.6)
        self.add_row()

    def _update_column_headers(self) -> None:
        headers = []
        for col in FIXED_COLUMN_ORDER:
            if col == ColumnKey.QUANTITY:
                headers.append(self._quantity_unit.column_header)
            else:
                headers.append(col.label_tr)
        self.table.setHorizontalHeaderLabels(headers)

        # Başlangıç sütun genişlikleri
        widths = [110, 220, 100, 90, 110, 110, 110, 70, 120, 130, 130]
        for idx, w in enumerate(widths):
            self.table.setColumnWidth(idx, w)

    def add_row(self, item: OfferItem | None = None) -> int:
        """Yeni bir satır ekler ve widget'larını yerleştirir."""
        row_idx = self.table.rowCount()
        self.table.insertRow(row_idx)

        widgets = ItemRowWidgets(row_idx, self.table)
        self._rows.append(widgets)

        # Hücrelere widget'ları bağla
        col_map = {
            ColumnKey.PRODUCT_CODE: widgets.code_edit,
            ColumnKey.DESCRIPTION: widgets.desc_edit,
            ColumnKey.QUANTITY: widgets.qty_edit,
            ColumnKey.PALLET: widgets.pallet_edit,
            ColumnKey.UNIT_PRICE: widgets.price_edit,
            ColumnKey.DISCOUNT_TYPE: widgets.disc_type_combo,
            ColumnKey.DISCOUNT_AMOUNT: widgets.disc_val_edit,
            ColumnKey.VAT: widgets.vat_lbl,
            ColumnKey.TOTAL_AMOUNT: widgets.total_lbl,
            ColumnKey.TOTAL_DISCOUNTED: widgets.disc_total_lbl,
            ColumnKey.TOTAL_WITH_VAT: widgets.vat_total_lbl,
        }

        for col_idx, col_key in enumerate(FIXED_COLUMN_ORDER):
            w = col_map[col_key]
            self.table.setCellWidget(row_idx, col_idx, w)

        # Olayları bağla
        widgets.code_edit.textChanged.connect(lambda: self._on_cell_changed(widgets))
        widgets.desc_edit.textChanged.connect(lambda: self._on_cell_changed(widgets))
        widgets.qty_edit.textChanged.connect(lambda: self._on_cell_changed(widgets))
        widgets.pallet_edit.textChanged.connect(lambda: self._on_cell_changed(widgets))
        widgets.price_edit.textChanged.connect(lambda: self._on_cell_changed(widgets))
        widgets.disc_type_combo.currentIndexChanged.connect(lambda: self._on_disc_type_changed(widgets))
        widgets.disc_val_edit.textChanged.connect(lambda: self._on_cell_changed(widgets))

        if item is not None:
            widgets.load_from_item(item)

        self._recalculate_row(widgets)
        self._apply_column_visibility()
        self.items_changed.emit()
        return row_idx

    def _delete_selected_row(self) -> None:
        selected_row = self.table.currentRow()
        if selected_row < 0 or len(self._rows) <= 1:
            # En az bir satır her zaman açık kalır
            return

        self.table.removeRow(selected_row)
        self._rows.pop(selected_row)
        # Satır indekslerini güncelle
        for idx, w in enumerate(self._rows):
            w.row = idx

        self.items_changed.emit()

    def _duplicate_selected_row(self) -> None:
        selected_row = self.table.currentRow()
        if selected_row < 0 or selected_row >= len(self._rows):
            return

        source_item = self._rows[selected_row].to_offer_item()
        self.add_row(source_item)

    def _on_disc_type_changed(self, widgets: ItemRowWidgets) -> None:
        raw_disc = widgets.disc_type_combo.currentData()
        try:
            disc_type = DiscountType(raw_disc)
        except (ValueError, TypeError):
            disc_type = DiscountType.NONE
        enabled = (disc_type != DiscountType.NONE) and self._discount_enabled
        widgets.disc_val_edit.setEnabled(enabled)
        if not enabled:
            widgets.disc_val_edit.clear()
        self._on_cell_changed(widgets)

    def _on_cell_changed(self, widgets: ItemRowWidgets) -> None:
        self._recalculate_row(widgets)
        self.items_changed.emit()

    def _recalculate_row(self, widgets: ItemRowWidgets) -> None:
        """Satırın hesaplanan tutarlarını domain calculator modülü ile hesaplar ve günceller."""
        item = widgets.to_offer_item()

        # KDV oranı etiketi
        if self._vat_enabled and self._vat_rate > Decimal("0"):
            rate_str = format_decimal_tr(self._vat_rate, decimal_places=0 if self._vat_rate % 1 == 0 else 2)
            widgets.vat_lbl.setText(f"%{rate_str}")
        else:
            widgets.vat_lbl.setText("-")

        try:
            calc = calculate_item(
                item,
                vat_rate=self._vat_rate,
                vat_enabled=self._vat_enabled,
                discount_enabled=self._discount_enabled,
            )
            widgets.total_lbl.setText(format_decimal_tr(calc.line_total))
            widgets.disc_total_lbl.setText(format_decimal_tr(calc.discounted_total))
            widgets.vat_total_lbl.setText(format_decimal_tr(calc.total_with_vat))

            # Hata stillerini temizle
            widgets.disc_val_edit.setStyleSheet("")
            widgets.disc_val_edit.setToolTip("")
        except DiscountExceedsTotalError as err:
            widgets.disc_val_edit.setStyleSheet("border: 1.5px solid #E53E3E; background: #FFF5F5;")
            widgets.disc_val_edit.setToolTip(str(err))
            widgets.disc_total_lbl.setText("Hata!")
            widgets.vat_total_lbl.setText("Hata!")

    def _apply_column_visibility(self) -> None:
        """Seçilen sütunlara göre sütunların gizlenip gösterilmesini sağlar."""
        for col_idx, col_key in enumerate(FIXED_COLUMN_ORDER):
            visible = col_key in self._selected_columns
            self.table.setColumnHidden(col_idx, not visible)

    # ── Ortak Kontrol ve Veri Metotları ──

    def set_quantity_unit(self, unit: QuantityUnit) -> None:
        self._quantity_unit = unit
        self._update_column_headers()

    def set_currency(self, currency: CurrencyCode) -> None:
        self._currency = currency
        # Tüm satırları yeniden hesapla
        for w in self._rows:
            self._recalculate_row(w)
        self.items_changed.emit()

    def set_vat(self, enabled: bool, rate: Decimal) -> None:
        self._vat_enabled = enabled
        self._vat_rate = rate
        for w in self._rows:
            self._recalculate_row(w)
        self.items_changed.emit()

    def set_discount(self, enabled: bool) -> None:
        self._discount_enabled = enabled
        for w in self._rows:
            raw_disc = w.disc_type_combo.currentData()
            try:
                disc_type = DiscountType(raw_disc)
            except (ValueError, TypeError):
                disc_type = DiscountType.NONE
            w.disc_val_edit.setEnabled(enabled and disc_type != DiscountType.NONE)
            self._recalculate_row(w)
        self.items_changed.emit()

    def set_selected_columns(self, columns: list[ColumnKey]) -> None:
        self._selected_columns = columns
        self._apply_column_visibility()

    def get_items(self) -> list[OfferItem]:
        """Tüm satırlardaki ürün modellerini sırayla döndürür."""
        return [w.to_offer_item() for w in self._rows]

    def set_items(self, items: list[OfferItem]) -> None:
        """Verilen ürün listesiyle tabloyu doldurur."""
        self.table.setRowCount(0)
        self._rows.clear()
        if not items:
            self.add_row()
            return

        for item in items:
            self.add_row(item)
