"""Hazır Şablonlar bileşeni — Paketleme, Muhafaza ve Ürün Bilgileri Checkbox yönetimi."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

ORDERED_SUB_ITEMS: list[tuple[str, str]] = [
    ("quality_guarantee", "KALİTE & GÜVENCE"),
    ("products_list", "ÜRÜNLER"),
    ("main_features", "ÜRÜNLERİN ANA ÖZELLİKLERİ"),
    ("production_process", "ÜRETİM SÜRECİ BİLGİSİ"),
    ("lemonade_extract", "LİMONATA ÖZÜTÜ"),
    ("orange_juice", "PORTAKAL SUYU"),
    ("pomegranate_juice", "NAR SUYU"),
    ("lemonade_rtd", "TÜKETİME HAZIR LİMONATA"),
    ("bodrum_mandarin_extract", "BODRUM MANDALİNATASI ÖZÜTÜ"),
    ("grapefruit_juice", "GREYFURT SUYU"),
    ("lemon_juice", "LİMON SUYU"),
    ("mulberry_squash", "KARADUT SQUASH"),
    ("strawberry_squash", "ÇİLEK SQUASH"),
]


class ReadyTemplatesWidget(QWidget):
    """Teklife eklenecek hazır şablon sayfalarını (Paketleme, Muhafaza ve Ürün Bilgileri) yöneten bileşen."""

    templates_changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._sub_checkboxes: dict[str, QCheckBox] = {}
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        group = QGroupBox("Hazır Şablonlar")
        group_layout = QVBoxLayout(group)
        group_layout.setContentsMargins(12, 10, 12, 10)
        group_layout.setSpacing(8)

        info_lbl = QLabel("Seçilen hazır tablolar PDF belgesine yeni bir sayfa olarak eklenir. Hiçbiri seçilmezse ek sayfa açılmaz.")
        info_lbl.setStyleSheet("color: #718096; font-size: 11px;")
        group_layout.addWidget(info_lbl)

        # Ana Checkbox'lar
        checkboxes_layout = QHBoxLayout()
        checkboxes_layout.setSpacing(24)

        self.cb_packaging = QCheckBox("Ürün Miktar Bilgileri")
        self.cb_packaging.setStyleSheet("font-weight: 600; color: #2B6CB0;")
        self.cb_packaging.setChecked(False)
        self.cb_packaging.toggled.connect(self._on_toggled)

        self.cb_storage = QCheckBox("Muhafaza Koşulları")
        self.cb_storage.setStyleSheet("font-weight: 600; color: #2B6CB0;")
        self.cb_storage.setChecked(False)
        self.cb_storage.toggled.connect(self._on_toggled)

        self.cb_harvest = QCheckBox("Hasat Takvimi")
        self.cb_harvest.setStyleSheet("font-weight: 600; color: #2B6CB0;")
        self.cb_harvest.setChecked(False)
        self.cb_harvest.toggled.connect(self._on_toggled)

        self.cb_product_info = QCheckBox("Ürün Bilgileri")
        self.cb_product_info.setStyleSheet("font-weight: 600; color: #2B6CB0;")
        self.cb_product_info.setChecked(False)
        self.cb_product_info.toggled.connect(self._on_product_info_toggled)

        checkboxes_layout.addWidget(self.cb_packaging)
        checkboxes_layout.addWidget(self.cb_storage)
        checkboxes_layout.addWidget(self.cb_harvest)
        checkboxes_layout.addWidget(self.cb_product_info)
        checkboxes_layout.addStretch()

        group_layout.addLayout(checkboxes_layout)

        # Ürün Bilgileri Alt Seçenekler Alanı
        self.sub_container = QFrame()
        self.sub_container.setStyleSheet(
            "QFrame { background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 6px; }"
        )
        self.sub_container.setVisible(False)
        sub_layout = QVBoxLayout(self.sub_container)
        sub_layout.setContentsMargins(8, 6, 8, 6)
        sub_layout.setSpacing(6)

        # Başlık ve Hızlı Seçim Butonları
        header_row = QHBoxLayout()
        lbl_sub = QLabel("Ürün Bilgisi Alanları (Seçilenler sırasıyla eklenecektir):")
        lbl_sub.setStyleSheet("font-weight: 600; font-size: 11px; color: #4A5568; border: none; background: transparent;")
        header_row.addWidget(lbl_sub)
        header_row.addStretch()

        btn_select_all = QPushButton("Tümünü Seç")
        btn_select_all.setStyleSheet(
            "QPushButton { font-size: 10px; padding: 2px 8px; background: #EDF2F7; border: 1px solid #CBD5E0; border-radius: 3px; color: #2D3748; }"
            "QPushButton:hover { background: #E2E8F0; }"
        )
        btn_select_all.clicked.connect(self._select_all_sub_items)
        header_row.addWidget(btn_select_all)

        btn_clear_all = QPushButton("Temizle")
        btn_clear_all.setStyleSheet(
            "QPushButton { font-size: 10px; padding: 2px 8px; background: #EDF2F7; border: 1px solid #CBD5E0; border-radius: 3px; color: #2D3748; }"
            "QPushButton:hover { background: #E2E8F0; }"
        )
        btn_clear_all.clicked.connect(self._clear_all_sub_items)
        header_row.addWidget(btn_clear_all)

        sub_layout.addLayout(header_row)

        # 3 Sütunlu Grid Layout
        grid = QGridLayout()
        grid.setSpacing(8)

        total_items = len(ORDERED_SUB_ITEMS)
        items_per_col = (total_items + 2) // 3  # 5, 5, 3

        for idx, (key, label) in enumerate(ORDERED_SUB_ITEMS):
            col = idx // items_per_col
            row = idx % items_per_col

            cb = QCheckBox(label)
            cb.setStyleSheet("font-size: 11px; color: #2D3748; font-weight: 500; border: none; background: transparent;")
            cb.setChecked(False)
            cb.toggled.connect(self._on_toggled)
            self._sub_checkboxes[key] = cb
            grid.addWidget(cb, row, col)

        sub_layout.addLayout(grid)
        group_layout.addWidget(self.sub_container)

        main_layout.addWidget(group)

    def _on_product_info_toggled(self, checked: bool) -> None:
        self.sub_container.setVisible(checked)
        self.templates_changed.emit()

    def _on_toggled(self) -> None:
        self.templates_changed.emit()

    def _select_all_sub_items(self) -> None:
        for cb in self._sub_checkboxes.values():
            cb.setChecked(True)

    def _clear_all_sub_items(self) -> None:
        for cb in self._sub_checkboxes.values():
            cb.setChecked(False)

    def is_packaging_enabled(self) -> bool:
        return self.cb_packaging.isChecked()

    def set_packaging_enabled(self, enabled: bool) -> None:
        self.cb_packaging.setChecked(enabled)

    def is_storage_enabled(self) -> bool:
        return self.cb_storage.isChecked()

    def set_storage_enabled(self, enabled: bool) -> None:
        self.cb_storage.setChecked(enabled)

    def is_harvest_enabled(self) -> bool:
        return self.cb_harvest.isChecked()

    def set_harvest_enabled(self, enabled: bool) -> None:
        self.cb_harvest.setChecked(enabled)

    def is_product_info_enabled(self) -> bool:
        return self.cb_product_info.isChecked()

    def set_product_info_enabled(self, enabled: bool) -> None:
        self.cb_product_info.setChecked(enabled)
        self.sub_container.setVisible(enabled)

    def get_selected_product_info_items(self) -> list[str]:
        if not self.cb_product_info.isChecked():
            return []
        return [k for k, _ in ORDERED_SUB_ITEMS if self._sub_checkboxes[k].isChecked()]

    def set_selected_product_info_items(self, items: list[str]) -> None:
        for k, cb in self._sub_checkboxes.items():
            cb.setChecked(k in items)

    def clear(self) -> None:
        self.cb_packaging.setChecked(False)
        self.cb_storage.setChecked(False)
        self.cb_harvest.setChecked(False)
        self.cb_product_info.setChecked(False)
        self.sub_container.setVisible(False)
        for cb in self._sub_checkboxes.values():
            cb.setChecked(False)
