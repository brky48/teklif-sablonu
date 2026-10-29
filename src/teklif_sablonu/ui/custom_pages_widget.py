"""Özel / Ek Sayfalar (Boş Sayfa Ekle) bileşeni.

Kullanıcının teklif sonuna sertifika, analiz raporu, akreditasyon belgesi gibi
istediği sayıda bağımsız A4 ek sayfası eklemesini sağlar.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap, QTextCursor, QTextListFormat
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from teklif_sablonu.domain.models import CustomPage


class CustomPageToolBar(QWidget):
    """Zengin metin düzenleme araç çubuğu (Kalın, İtalik, Altı Çizili, Hizalamalar ve Listeler)."""

    def __init__(self, editor: QTextEdit, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.editor = editor
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 4)
        layout.setSpacing(4)

        self.btn_bold = QPushButton("B")
        self.btn_bold.setProperty("class", "toolbar")
        self.btn_bold.setFixedSize(30, 26)
        self.btn_bold.setToolTip("Kalın (Ctrl+B)")
        self.btn_bold.setStyleSheet("font-weight: bold; font-size: 13px;")
        self.btn_bold.clicked.connect(self._toggle_bold)

        self.btn_italic = QPushButton("I")
        self.btn_italic.setProperty("class", "toolbar")
        self.btn_italic.setFixedSize(30, 26)
        self.btn_italic.setToolTip("İtalik (Ctrl+I)")
        self.btn_italic.setStyleSheet("font-style: italic; font-size: 13px; font-family: serif;")
        self.btn_italic.clicked.connect(self._toggle_italic)

        self.btn_underline = QPushButton("U")
        self.btn_underline.setProperty("class", "toolbar")
        self.btn_underline.setFixedSize(30, 26)
        self.btn_underline.setToolTip("Altı Çizili (Ctrl+U)")
        self.btn_underline.setStyleSheet("text-decoration: underline; font-size: 13px;")
        self.btn_underline.clicked.connect(self._toggle_underline)

        self.btn_align_left = QPushButton("◀ Sola")
        self.btn_align_left.setProperty("class", "toolbar")
        self.btn_align_left.setFixedHeight(26)
        self.btn_align_left.clicked.connect(lambda: self._set_alignment(Qt.AlignmentFlag.AlignLeft))

        self.btn_align_center = QPushButton("▲ Ortala")
        self.btn_align_center.setProperty("class", "toolbar")
        self.btn_align_center.setFixedHeight(26)
        self.btn_align_center.clicked.connect(lambda: self._set_alignment(Qt.AlignmentFlag.AlignCenter))

        self.btn_align_right = QPushButton("▶ Sağa")
        self.btn_align_right.setProperty("class", "toolbar")
        self.btn_align_right.setFixedHeight(26)
        self.btn_align_right.clicked.connect(lambda: self._set_alignment(Qt.AlignmentFlag.AlignRight))

        self.btn_bullet_list = QPushButton("• Madde")
        self.btn_bullet_list.setProperty("class", "toolbar")
        self.btn_bullet_list.setFixedHeight(26)
        self.btn_bullet_list.clicked.connect(self._insert_bullet_list)

        self.btn_num_list = QPushButton("1. Liste")
        self.btn_num_list.setProperty("class", "toolbar")
        self.btn_num_list.setFixedHeight(26)
        self.btn_num_list.clicked.connect(self._insert_numbered_list)

        layout.addWidget(self.btn_bold)
        layout.addWidget(self.btn_italic)
        layout.addWidget(self.btn_underline)
        layout.addWidget(self.btn_align_left)
        layout.addWidget(self.btn_align_center)
        layout.addWidget(self.btn_align_right)
        layout.addWidget(self.btn_bullet_list)
        layout.addWidget(self.btn_num_list)
        layout.addStretch()

    def _toggle_bold(self) -> None:
        weight = QFont.Weight.Bold if self.editor.fontWeight() != QFont.Weight.Bold else QFont.Weight.Normal
        self.editor.setFontWeight(weight)
        self.editor.setFocus()

    def _toggle_italic(self) -> None:
        self.editor.setFontItalic(not self.editor.fontItalic())
        self.editor.setFocus()

    def _toggle_underline(self) -> None:
        self.editor.setFontUnderline(not self.editor.fontUnderline())
        self.editor.setFocus()

    def _set_alignment(self, align: Qt.AlignmentFlag) -> None:
        self.editor.setAlignment(align)
        self.editor.setFocus()

    def _insert_bullet_list(self) -> None:
        cursor = self.editor.textCursor()
        cursor.createList(QTextListFormat.Style.ListDisc)
        self.editor.setFocus()

    def _insert_numbered_list(self) -> None:
        cursor = self.editor.textCursor()
        cursor.createList(QTextListFormat.Style.ListDecimal)
        self.editor.setFocus()


class SingleCustomPageCard(QFrame):
    """Tek bir özel sayfa düzenleyici kartı."""

    changed = Signal()
    delete_requested = Signal(object)
    move_up_requested = Signal(object)
    move_down_requested = Signal(object)

    def __init__(self, index: int = 1, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.index = index
        self._image_path: str = ""
        self._init_ui()

    def _init_ui(self) -> None:
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(
            "SingleCustomPageCard { background: #FFFFFF; border: 1px solid #CBD5E0; border-radius: 6px; padding: 4px; }"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)

        # 1. Başlık ve Aksiyon Butonları Çubuğu
        header_bar = QHBoxLayout()
        self.lbl_card_title = QLabel(f"📄 Ek Sayfa #{self.index}")
        self.lbl_card_title.setStyleSheet("font-weight: bold; font-size: 13px; color: #2B6CB0;")
        header_bar.addWidget(self.lbl_card_title)
        header_bar.addStretch()

        self.btn_up = QPushButton("▲")
        self.btn_up.setFixedSize(28, 26)
        self.btn_up.setToolTip("Yukarı Taşı")
        self.btn_up.clicked.connect(lambda: self.move_up_requested.emit(self))
        header_bar.addWidget(self.btn_up)

        self.btn_down = QPushButton("▼")
        self.btn_down.setFixedSize(28, 26)
        self.btn_down.setToolTip("Aşağı Taşı")
        self.btn_down.clicked.connect(lambda: self.move_down_requested.emit(self))
        header_bar.addWidget(self.btn_down)

        self.btn_del = QPushButton("🗑️ Sayfayı Sil")
        self.btn_del.setStyleSheet("color: #E53E3E; font-weight: 600; padding: 3px 8px;")
        self.btn_del.clicked.connect(lambda: self.delete_requested.emit(self))
        header_bar.addWidget(self.btn_del)
        layout.addLayout(header_bar)

        # 2. Üst Form: Sayfa Başlığı ve Yazı Boyutu Seçimi
        top_grid = QGridLayout()
        top_grid.setHorizontalSpacing(12)
        top_grid.setVerticalSpacing(6)

        top_grid.addWidget(QLabel("Sayfa Başlığı:"), 0, 0)
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Örn: EK-1: ULUSLARARASI LEZZET VE KALİTE SERTİFİKASI")
        self.title_input.textChanged.connect(self._on_changed)
        top_grid.addWidget(self.title_input, 0, 1)

        top_grid.addWidget(QLabel("Yazı Boyutu:"), 0, 2)
        self.font_size_combo = QComboBox()
        self.font_size_combo.addItem("8.0 pt (Varsayılan - Standart)", 8.0)
        self.font_size_combo.addItem("7.5 pt (Küçük)", 7.5)
        self.font_size_combo.addItem("7.0 pt (Çok Küçük)", 7.0)
        self.font_size_combo.addItem("6.5 pt (Ekstra Kompakt)", 6.5)
        self.font_size_combo.addItem("8.5 pt (Büyük)", 8.5)
        self.font_size_combo.addItem("9.0 pt (Çok Büyük)", 9.0)
        self.font_size_combo.currentIndexChanged.connect(self._on_changed)
        top_grid.addWidget(self.font_size_combo, 0, 3)
        layout.addLayout(top_grid)

        # 3. Görsel Ekleme Alanı
        img_box = QGroupBox("Görsel / Belge Eki (İsteğe Bağlı)")
        img_layout = QHBoxLayout(img_box)
        img_layout.setContentsMargins(8, 6, 8, 6)
        img_layout.setSpacing(10)

        self.btn_choose_img = QPushButton("🖼️ Görsel Seç (PNG / JPG / WEBP)...")
        self.btn_choose_img.clicked.connect(self._choose_image)
        img_layout.addWidget(self.btn_choose_img)

        self.btn_remove_img = QPushButton("✕ Görseli Kaldır")
        self.btn_remove_img.setEnabled(False)
        self.btn_remove_img.clicked.connect(self._remove_image)
        img_layout.addWidget(self.btn_remove_img)

        self.lbl_img_path = QLabel("Seçilen görsel: Yok")
        self.lbl_img_path.setStyleSheet("color: #718096; font-size: 11px;")
        img_layout.addWidget(self.lbl_img_path, 1)

        self.lbl_thumbnail = QLabel()
        self.lbl_thumbnail.setFixedSize(60, 45)
        self.lbl_thumbnail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_thumbnail.setStyleSheet("background: #EDF2F7; border: 1px dashed #CBD5E0; border-radius: 4px;")
        img_layout.addWidget(self.lbl_thumbnail)
        layout.addWidget(img_box)

        # 4. Zengin Metin Alanı
        text_box = QGroupBox("Zengin Metin / Açıklama / Dipnot")
        text_layout = QVBoxLayout(text_box)
        text_layout.setContentsMargins(8, 6, 8, 6)
        text_layout.setSpacing(4)

        self.text_editor = QTextEdit()
        self.text_editor.setPlaceholderText("İsteğe bağlı sertifika açıklaması, duyusal test sonuçları, dipnot vb...")
        self.text_editor.setMaximumHeight(100)
        self.text_editor.textChanged.connect(self._on_changed)

        self.toolbar = CustomPageToolBar(self.text_editor, self)
        text_layout.addWidget(self.toolbar)
        text_layout.addWidget(self.text_editor)
        layout.addWidget(text_box)

    def set_index(self, index: int) -> None:
        self.index = index
        self.lbl_card_title.setText(f"📄 Ek Sayfa #{self.index}")

    def _choose_image(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Ek Sayfa Görseli Seç",
            "",
            "Görsel Dosyaları (*.png *.jpg *.jpeg *.webp *.bmp);;Tüm Dosyalar (*.*)",
        )
        if file_path:
            self.set_image_path(file_path)
            self._on_changed()

    def _remove_image(self) -> None:
        self.set_image_path("")
        self._on_changed()

    def set_image_path(self, path: str) -> None:
        self._image_path = path or ""
        if self._image_path and Path(self._image_path).exists():
            p = Path(self._image_path)
            self.lbl_img_path.setText(f"✓ {p.name}")
            self.lbl_img_path.setToolTip(str(p))
            self.btn_remove_img.setEnabled(True)

            pix = QPixmap(str(p))
            if not pix.isNull():
                scaled = pix.scaled(56, 41, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.lbl_thumbnail.setPixmap(scaled)
            else:
                self.lbl_thumbnail.setText("Hata")
        else:
            self._image_path = ""
            self.lbl_img_path.setText("Seçilen görsel: Yok")
            self.lbl_img_path.setToolTip("")
            self.btn_remove_img.setEnabled(False)
            self.lbl_thumbnail.clear()
            self.lbl_thumbnail.setText("-")

    def get_image_path(self) -> str:
        return self._image_path

    def _on_changed(self) -> None:
        self.changed.emit()

    def to_custom_page(self, pos: int = 0) -> CustomPage:
        data = self.font_size_combo.currentData()
        font_size = float(data) if data is not None else 8.0
        return CustomPage(
            position=pos,
            title=self.title_input.text().strip(),
            content_html=self.text_editor.toHtml().strip() if self.text_editor.toPlainText().strip() else "",
            image_path=self._image_path,
            font_size=font_size,
        )

    def set_custom_page(self, page: CustomPage) -> None:
        self.title_input.setText(page.title)
        self.set_image_path(page.image_path)
        if page.content_html:
            self.text_editor.setHtml(page.content_html)
        else:
            self.text_editor.clear()

        # Font size ayarla
        target_f = float(page.font_size) if page.font_size else 8.0
        for i in range(self.font_size_combo.count()):
            v = self.font_size_combo.itemData(i)
            if v is not None and abs(float(v) - target_f) < 0.05:
                self.font_size_combo.setCurrentIndex(i)
                break


class CustomPagesWidget(QWidget):
    """Bölüm sonundaki Özel / Ek Sayfalar yöneticisi (İstenildiği kadar sayfa ekleme/silme)."""

    pages_changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._cards: list[SingleCustomPageCard] = []
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.group = QGroupBox("Özel / Ek Sayfalar (Boş Sayfa Ekle)")
        group_layout = QVBoxLayout(self.group)
        group_layout.setSpacing(10)

        # Üst Bilgilendirme ve Ekleme Butonu
        top_bar = QHBoxLayout()
        desc_lbl = QLabel(
            "Teklifin sonuna istediğiniz sayıda özel sayfa (resmi sertifika, analiz raporu, "
            "akreditasyon belgesi vb.) ekleyebilirsiniz. Her sayfa bağımsız bir sayfa olarak PDF ve Excel çıktısına eklenir."
        )
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet("color: #4A5568; font-size: 11px;")
        top_bar.addWidget(desc_lbl, 1)

        self.btn_add_page = QPushButton("➕ Boş Sayfa Ekle")
        self.btn_add_page.setStyleSheet("font-weight: bold; background: #EBF8FF; color: #2B6CB0; padding: 6px 14px;")
        self.btn_add_page.clicked.connect(lambda: self.add_page())
        top_bar.addWidget(self.btn_add_page)
        group_layout.addLayout(top_bar)

        # Sayfa kartlarının listeleneceği yer
        self.cards_layout = QVBoxLayout()
        self.cards_layout.setSpacing(10)
        group_layout.addLayout(self.cards_layout)

        main_layout.addWidget(self.group)

    def add_page(self, page: CustomPage | None = None) -> SingleCustomPageCard:
        idx = len(self._cards) + 1
        card = SingleCustomPageCard(index=idx, parent=self)
        if page is not None:
            card.set_custom_page(page)

        card.changed.connect(self._on_card_changed)
        card.delete_requested.connect(self._on_delete_page)
        card.move_up_requested.connect(self._on_move_up)
        card.move_down_requested.connect(self._on_move_down)

        self._cards.append(card)
        self.cards_layout.addWidget(card)
        self._update_indices()
        self.pages_changed.emit()
        return card

    def _on_delete_page(self, card: SingleCustomPageCard) -> None:
        if card in self._cards:
            self._cards.remove(card)
            self.cards_layout.removeWidget(card)
            card.setParent(None)
            card.deleteLater()
            self._update_indices()
            self.pages_changed.emit()

    def _on_move_up(self, card: SingleCustomPageCard) -> None:
        idx = self._cards.index(card)
        if idx > 0:
            self._cards[idx], self._cards[idx - 1] = self._cards[idx - 1], self._cards[idx]
            self._rebuild_layout()
            self._update_indices()
            self.pages_changed.emit()

    def _on_move_down(self, card: SingleCustomPageCard) -> None:
        idx = self._cards.index(card)
        if idx < len(self._cards) - 1:
            self._cards[idx], self._cards[idx + 1] = self._cards[idx + 1], self._cards[idx]
            self._rebuild_layout()
            self._update_indices()
            self.pages_changed.emit()

    def _rebuild_layout(self) -> None:
        for card in self._cards:
            self.cards_layout.removeWidget(card)
        for card in self._cards:
            self.cards_layout.addWidget(card)

    def _update_indices(self) -> None:
        for idx, card in enumerate(self._cards, 1):
            card.set_index(idx)
            card.btn_up.setEnabled(idx > 1)
            card.btn_down.setEnabled(idx < len(self._cards))

    def _on_card_changed(self) -> None:
        self.pages_changed.emit()

    def get_pages(self) -> list[CustomPage]:
        """Tüm kartlardaki modelleri sırayla döndürür."""
        return [card.to_custom_page(pos=i) for i, card in enumerate(self._cards)]

    def set_pages(self, pages: list[CustomPage]) -> None:
        """Verilen sayfa listesini arayüze yükler."""
        self.clear()
        for page in pages:
            self.add_page(page)

    def clear(self) -> None:
        """Tüm sayfaları temizler."""
        for card in list(self._cards):
            self.cards_layout.removeWidget(card)
            card.setParent(None)
            card.deleteLater()
        self._cards.clear()
        self.pages_changed.emit()
