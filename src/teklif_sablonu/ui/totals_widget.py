"""Genel toplam özeti gösterim kartı bileşeni."""

from __future__ import annotations

from decimal import Decimal

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from teklif_sablonu.domain.enums import CurrencyCode
from teklif_sablonu.domain.models import OfferTotals
from teklif_sablonu.domain.parsers import format_decimal_tr


class TotalsWidget(QWidget):
    """Bölüm 8.5'e göre teklif genel toplam özetini gösteren kart."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._currency = CurrencyCode.TRY
        self._vat_enabled = False
        self._discount_enabled = False
        self._vat_rate = Decimal("0")
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addStretch()

        card = QGroupBox("Genel Toplam Özeti")
        card.setMinimumWidth(360)
        grid = QGridLayout(card)
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(8)

        # 1. Ara Toplam (Daima Görünür)
        grid.addWidget(QLabel("Ara Toplam:"), 0, 0)
        self.lbl_subtotal = QLabel("0,00 ₺")
        self.lbl_subtotal.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.lbl_subtotal.setStyleSheet("font-weight: 600;")
        grid.addWidget(self.lbl_subtotal, 0, 1)

        # 2. Toplam İskonto (İskonto Etkinse)
        self.lbl_discount_title = QLabel("Toplam İskonto:")
        self.lbl_discount_title.setStyleSheet("color: #C53030;")
        self.lbl_discount = QLabel("-0,00 ₺")
        self.lbl_discount.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.lbl_discount.setStyleSheet("color: #C53030; font-weight: 600;")
        grid.addWidget(self.lbl_discount_title, 1, 0)
        grid.addWidget(self.lbl_discount, 1, 1)

        # 3. İskonto Sonrası Ara Toplam (İskonto Etkinse)
        self.lbl_disc_subtotal_title = QLabel("İskonto Sonrası Ara Toplam:")
        self.lbl_disc_subtotal = QLabel("0,00 ₺")
        self.lbl_disc_subtotal.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.lbl_disc_subtotal.setStyleSheet("font-weight: 600;")
        grid.addWidget(self.lbl_disc_subtotal_title, 2, 0)
        grid.addWidget(self.lbl_disc_subtotal, 2, 1)

        # Ayırıcı çizgi
        self.separator = QFrame()
        self.separator.setFrameShape(QFrame.Shape.HLine)
        self.separator.setFrameShadow(QFrame.Shadow.Sunken)
        grid.addWidget(self.separator, 3, 0, 1, 2)

        # 4. Toplam KDV (KDV Etkinse)
        self.lbl_vat_title = QLabel("Toplam KDV:")
        self.lbl_vat = QLabel("0,00 ₺")
        self.lbl_vat.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.lbl_vat.setStyleSheet("font-weight: 600;")
        grid.addWidget(self.lbl_vat_title, 4, 0)
        grid.addWidget(self.lbl_vat, 4, 1)

        # 5. KDV Dâhil Genel Toplam (KDV Etkinse, veya Genel Toplam)
        self.lbl_grand_total_title = QLabel("Genel Toplam:")
        self.lbl_grand_total_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #2B6CB0;")
        self.lbl_grand_total = QLabel("0,00 ₺")
        self.lbl_grand_total.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.lbl_grand_total.setStyleSheet(
            "font-weight: bold; font-size: 16px; color: #2B6CB0; background: #EBF8FF; padding: 4px 8px; border-radius: 4px;"
        )
        grid.addWidget(self.lbl_grand_total_title, 5, 0)
        grid.addWidget(self.lbl_grand_total, 5, 1)

        main_layout.addWidget(card)
        self.update_features(currency=CurrencyCode.TRY, vat_enabled=False, vat_rate=Decimal("0"), discount_enabled=False)

    def update_features(
        self,
        *,
        currency: CurrencyCode,
        vat_enabled: bool,
        vat_rate: Decimal,
        discount_enabled: bool,
    ) -> None:
        """Özet kartının aktif para birimi ve görünür alanlarını günceller."""
        self._currency = currency
        self._vat_enabled = vat_enabled
        self._vat_rate = vat_rate
        self._discount_enabled = discount_enabled

        # İskonto alanlarının görünürlüğü
        self.lbl_discount_title.setVisible(discount_enabled)
        self.lbl_discount.setVisible(discount_enabled)
        self.lbl_disc_subtotal_title.setVisible(discount_enabled)
        self.lbl_disc_subtotal.setVisible(discount_enabled)

        # KDV alanlarının görünürlüğü
        self.lbl_vat_title.setVisible(vat_enabled)
        self.lbl_vat.setVisible(vat_enabled)
        if vat_enabled:
            rate_str = format_decimal_tr(vat_rate, decimal_places=0 if vat_rate % 1 == 0 else 2)
            self.lbl_vat_title.setText(f"Toplam KDV (%{rate_str}):")
            self.lbl_grand_total_title.setText("KDV Dâhil Genel Toplam:")
        else:
            self.lbl_grand_total_title.setText("Genel Toplam:")

    def update_totals(self, totals: OfferTotals) -> None:
        """Hesaplanan OfferTotals değerlerini ekranda gösterir."""
        sym = f" {self._currency.symbol}"

        self.lbl_subtotal.setText(format_decimal_tr(totals.subtotal) + sym)
        self.lbl_discount.setText(f"-{format_decimal_tr(totals.total_discount)}{sym}")
        self.lbl_disc_subtotal.setText(format_decimal_tr(totals.discounted_subtotal) + sym)
        self.lbl_vat.setText(format_decimal_tr(totals.total_vat) + sym)

        if self._vat_enabled:
            self.lbl_grand_total.setText(format_decimal_tr(totals.grand_total) + sym)
        elif self._discount_enabled:
            self.lbl_grand_total.setText(format_decimal_tr(totals.discounted_subtotal) + sym)
        else:
            self.lbl_grand_total.setText(format_decimal_tr(totals.subtotal) + sym)
