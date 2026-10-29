"""Sütun seçim ve görünürlük kontrolü bileşeni."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QGridLayout,
    QGroupBox,
    QVBoxLayout,
    QWidget,
)

from teklif_sablonu.domain.enums import (
    FIXED_COLUMN_ORDER,
    ColumnKey,
    QuantityUnit,
)


class ColumnSelectorWidget(QWidget):
    """Bölüm 6.2 ve 6.3'teki 11 sütunun seçimini ve bağımlılıklarını yöneten bileşen."""

    columns_changed = Signal(list)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._checkboxes: dict[ColumnKey, QCheckBox] = {}
        self._vat_enabled = False
        self._discount_enabled = False
        self._quantity_unit = QuantityUnit.PIECE
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        group = QGroupBox("Görünür Sütunlar (PDF & Excel)")
        grid = QGridLayout(group)
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(8)

        # 11 sütun için checkbox'ları oluştur (2 satır x 6 sütun ızgara)
        for idx, col in enumerate(FIXED_COLUMN_ORDER):
            cb = QCheckBox(self._get_column_label(col))
            self._checkboxes[col] = cb

            # Zorunlu sütunlar kapatılamaz (Bölüm 6.3)
            if col.is_mandatory:
                cb.setChecked(True)
                cb.setEnabled(False)
                cb.setToolTip("Bu sütun zorunludur ve kapatılamaz.")
            elif col in (ColumnKey.PRODUCT_CODE, ColumnKey.PALLET, ColumnKey.TOTAL_AMOUNT):
                # Varsayılan açık opsiyonel sütunlar
                cb.setChecked(True)
            else:
                # İskonto ve KDV sütunları başlangıçta kapalı
                cb.setChecked(False)

            cb.toggled.connect(self._on_toggled)

            row = idx // 6
            c = idx % 6
            grid.addWidget(cb, row, c)

        main_layout.addWidget(group)
        self.update_feature_dependencies(vat_enabled=False, discount_enabled=False)

    def _get_column_label(self, col: ColumnKey) -> str:
        if col == ColumnKey.QUANTITY:
            return self._quantity_unit.column_header
        return col.label_tr

    def set_quantity_unit(self, unit: QuantityUnit) -> None:
        """Miktar birimi değiştiğinde sütun başlığını günceller."""
        self._quantity_unit = unit
        if ColumnKey.QUANTITY in self._checkboxes:
            self._checkboxes[ColumnKey.QUANTITY].setText(self._get_column_label(ColumnKey.QUANTITY))

    def update_feature_dependencies(self, *, vat_enabled: bool, discount_enabled: bool) -> None:
        """KDV veya İskonto açılıp kapatıldığında bağımlı sütunları devre dışı/etkin yapar."""
        self._vat_enabled = vat_enabled
        self._discount_enabled = discount_enabled

        # KDV bağımlılıkları
        vat_cols = (ColumnKey.VAT, ColumnKey.TOTAL_WITH_VAT)
        for col in vat_cols:
            cb = self._checkboxes.get(col)
            if cb:
                cb.setEnabled(vat_enabled)
                if not vat_enabled:
                    cb.setChecked(False)
                elif not cb.isChecked():
                    # KDV etkinleştirildiğinde varsayılan olarak aç
                    cb.setChecked(True)

        # İskonto bağımlılıkları
        disc_cols = (
            ColumnKey.DISCOUNT_TYPE,
            ColumnKey.DISCOUNT_AMOUNT,
            ColumnKey.TOTAL_DISCOUNTED,
        )
        for col in disc_cols:
            cb = self._checkboxes.get(col)
            if cb:
                cb.setEnabled(discount_enabled)
                if not discount_enabled:
                    cb.setChecked(False)
                elif not cb.isChecked():
                    # İskonto etkinleştirildiğinde varsayılan olarak aç
                    cb.setChecked(True)

        self._on_toggled()

    def _on_toggled(self) -> None:
        self.columns_changed.emit(self.get_selected_columns())

    def get_selected_columns(self) -> list[ColumnKey]:
        """Seçili sütunları FIXED_COLUMN_ORDER sırasını kesinlikle koruyarak döndürür."""
        selected: list[ColumnKey] = []
        for col in FIXED_COLUMN_ORDER:
            cb = self._checkboxes.get(col)
            if cb and cb.isChecked():
                selected.append(col)
        return selected

    def set_selected_columns(self, columns: list[ColumnKey]) -> None:
        """Sütun seçimlerini günceller."""
        for col, cb in self._checkboxes.items():
            if col.is_mandatory:
                cb.setChecked(True)
            else:
                cb.setChecked(col in columns)
        self._on_toggled()
