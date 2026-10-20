"""Teklif arşivi listeleme, arama, açma ve kopyalama ekranı."""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
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

from teklif_sablonu.domain.calculator import calculate_offer
from teklif_sablonu.domain.models import Offer
from teklif_sablonu.domain.parsers import format_decimal_tr


class ArchiveWidget(QWidget):
    """Kayıtlı teklifleri listeleyen, arayan, açan ve kopyalayan arşiv ekranı."""

    open_offer_requested = Signal(Offer)
    duplicate_offer_requested = Signal(Offer)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._offers: list[Offer] = []
        self._filtered_offers: list[Offer] = []
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        group = QGroupBox("Teklif Arşivi")
        group_layout = QVBoxLayout(group)

        # Arama ve filtreleme çubuğu
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("🔍 Teklif Ara:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Teklif numarası, alıcı adı veya şirkete göre filtrele...")
        self.search_input.textChanged.connect(self._apply_filter)
        search_layout.addWidget(self.search_input)

        self.btn_refresh = QPushButton("🔄 Yenile")
        self.btn_refresh.setProperty("class", "secondary")
        self.btn_refresh.clicked.connect(self._apply_filter)
        search_layout.addWidget(self.btn_refresh)

        group_layout.addLayout(search_layout)

        # Teklif listesi tablosu
        self.table = QTableWidget(0, 7)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setHorizontalHeaderLabels([
            "Teklif No",
            "Tarih",
            "Şirket",
            "Alıcı Firma / Şahıs",
            "Para Birimi",
            "Ürün Sayısı",
            "Genel Toplam",
        ])
        self.table.doubleClicked.connect(self._on_open_clicked)
        group_layout.addWidget(self.table)

        # Alt aksiyon butonları
        btn_layout = QHBoxLayout()
        self.btn_open = QPushButton("📂 Seçili Teklifi Aç")
        self.btn_open.clicked.connect(self._on_open_clicked)

        self.btn_duplicate = QPushButton("📋 Teklifi Kopyala ve Yeni Oluştur")
        self.btn_duplicate.setProperty("class", "secondary")
        self.btn_duplicate.setToolTip(
            "Seçili teklifin kopyasını oluşturarak yeni bir teklif olarak açar. Orijinal teklif değişmez."
        )
        self.btn_duplicate.clicked.connect(self._on_duplicate_clicked)

        self.lbl_count = QLabel("Toplam: 0 teklif")
        self.lbl_count.setStyleSheet("color: #718096;")

        btn_layout.addWidget(self.btn_open)
        btn_layout.addWidget(self.btn_duplicate)
        btn_layout.addStretch()
        btn_layout.addWidget(self.lbl_count)

        group_layout.addLayout(btn_layout)
        layout.addWidget(group)

    def set_offers(self, offers: list[Offer]) -> None:
        """Arşivdeki teklif listesini günceller."""
        self._offers = list(offers)
        self._apply_filter()

    def _apply_filter(self) -> None:
        query = self.search_input.text().strip().lower()
        if not query:
            self._filtered_offers = list(self._offers)
        else:
            self._filtered_offers = [
                o
                for o in self._offers
                if (
                    query in (o.offer_number or "").lower()
                    or query in (o.recipient_name or "").lower()
                    or query in (o.company_id or "").lower()
                )
            ]

        self._render_table()

    def _render_table(self) -> None:
        self.table.setRowCount(0)
        for row_idx, offer in enumerate(self._filtered_offers):
            self.table.insertRow(row_idx)

            _, totals = calculate_offer(offer)
            grand_total_str = format_decimal_tr(totals.grand_total) + f" {offer.currency_code.symbol}"

            items_count = len(offer.get_valid_items())

            cells = [
                offer.offer_number or "(Taslak)",
                offer.offer_date.strftime("%d.%m.%Y"),
                "Endemiks Tarım" if "tarim" in offer.company_id else "Endemiks Gıda",
                offer.recipient_name or "-",
                offer.currency_code.value,
                str(items_count),
                grand_total_str,
            ]

            for col_idx, text in enumerate(cells):
                item = QTableWidgetItem(text)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if col_idx in (1, 4, 5, 6):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter if col_idx != 6 else Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row_idx, col_idx, item)

        self.lbl_count.setText(f"Toplam: {len(self._filtered_offers)} teklif")

    def _get_selected_offer(self) -> Offer | None:
        row = self.table.currentRow()
        if 0 <= row < len(self._filtered_offers):
            return self._filtered_offers[row]
        return None

    def _on_open_clicked(self) -> None:
        offer = self._get_selected_offer()
        if offer:
            self.open_offer_requested.emit(offer)

    def _on_duplicate_clicked(self) -> None:
        offer = self._get_selected_offer()
        if offer:
            self.duplicate_offer_requested.emit(offer)
