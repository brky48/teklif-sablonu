"""Ticari koşullar ve zengin metin düzenleme bileşeni."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QTextCursor, QTextListFormat
from PySide6.QtWidgets import (
    QCheckBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from teklif_sablonu.config import load_section_defaults
from teklif_sablonu.domain.enums import SectionKey
from teklif_sablonu.domain.models import OfferSection
from teklif_sablonu.domain.validators import get_visible_text_length


class RichTextToolBar(QWidget):
    """Ek Alan için kalın, italik, altı çizili ve liste butonları içeren araç çubuğu."""

    def __init__(self, editor: QTextEdit, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.editor = editor
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 4)
        layout.setSpacing(4)

        self.btn_bold = QPushButton("B")
        self.btn_bold.setFixedSize(28, 28)
        self.btn_bold.setToolTip("Kalın (Ctrl+B)")
        self.btn_bold.setStyleSheet("font-weight: bold;")
        self.btn_bold.clicked.connect(self._toggle_bold)

        self.btn_italic = QPushButton("I")
        self.btn_italic.setFixedSize(28, 28)
        self.btn_italic.setToolTip("İtalik (Ctrl+I)")
        self.btn_italic.setStyleSheet("font-style: italic;")
        self.btn_italic.clicked.connect(self._toggle_italic)

        self.btn_underline = QPushButton("U")
        self.btn_underline.setFixedSize(28, 28)
        self.btn_underline.setToolTip("Altı Çizili (Ctrl+U)")
        self.btn_underline.setStyleSheet("text-decoration: underline;")
        self.btn_underline.clicked.connect(self._toggle_underline)

        self.btn_bullet_list = QPushButton("• Liste")
        self.btn_bullet_list.setFixedHeight(28)
        self.btn_bullet_list.clicked.connect(self._insert_bullet_list)

        self.btn_num_list = QPushButton("1. Liste")
        self.btn_num_list.setFixedHeight(28)
        self.btn_num_list.clicked.connect(self._insert_numbered_list)

        layout.addWidget(self.btn_bold)
        layout.addWidget(self.btn_italic)
        layout.addWidget(self.btn_underline)
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

    def _insert_bullet_list(self) -> None:
        cursor = self.editor.textCursor()
        cursor.createList(QTextListFormat.Style.ListDisc)
        self.editor.setFocus()

    def _insert_numbered_list(self) -> None:
        cursor = self.editor.textCursor()
        cursor.createList(QTextListFormat.Style.ListDecimal)
        self.editor.setFocus()


class SingleSectionCard(QWidget):
    """Tek bir ticari koşul bölümünü (checkbox + metin kutusu + sayaç) yöneten kart."""

    changed = Signal()

    def __init__(
        self,
        section_key: SectionKey,
        label: str,
        default_text: str,
        max_chars: int,
        is_rich_text: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.section_key = section_key
        self.label_text = label
        self.default_text = default_text
        self.max_chars = max_chars
        self.is_rich_text = is_rich_text

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)

        # Başlık ve Checkbox
        header_layout = QHBoxLayout()
        self.checkbox = QCheckBox(self.label_text)
        self.checkbox.setStyleSheet("font-weight: 600; color: #2B6CB0;")
        self.checkbox.setChecked(False)

        self.counter_lbl = QLabel(f"0 / {self.max_chars}")
        self.counter_lbl.setStyleSheet("color: #718096; font-size: 11px;")

        header_layout.addWidget(self.checkbox)
        header_layout.addStretch()
        header_layout.addWidget(self.counter_lbl)
        layout.addLayout(header_layout)

        if self.is_rich_text:
            # Zengin metin düzenleyici
            self.toolbar = RichTextToolBar(None, self)
            layout.addWidget(self.toolbar)

            self.rich_editor = QTextEdit()
            self.rich_editor.setEnabled(False)
            self.rich_editor.setMaximumHeight(140)
            self.rich_editor.setPlaceholderText("İsteğe bağlı zengin metin notları...")
            self.toolbar.editor = self.rich_editor
            self.rich_editor.textChanged.connect(self._on_text_changed)
            layout.addWidget(self.rich_editor)
            self.plain_editor = None
        else:
            # Standart düz metin düzenleyici
            self.plain_editor = QPlainTextEdit()
            self.plain_editor.setEnabled(False)
            self.plain_editor.setMaximumHeight(80)
            self.plain_editor.textChanged.connect(self._on_text_changed)
            layout.addWidget(self.plain_editor)
            self.rich_editor = None
            self.toolbar = None

        self.checkbox.toggled.connect(self._on_toggled)

    def _on_toggled(self, checked: bool) -> None:
        editor = self.rich_editor if self.is_rich_text else self.plain_editor
        editor.setEnabled(checked)

        if self.toolbar:
            self.toolbar.setEnabled(checked)

        if checked:
            # Eğer kutu boşsa varsayılan metni getir
            current_text = self.get_text()
            if not current_text and self.default_text:
                self.set_text(self.default_text)
        self._update_counter()
        self.changed.emit()

    def _on_text_changed(self) -> None:
        self._update_counter()
        self.changed.emit()

    def _update_counter(self) -> None:
        text = self.get_text()
        vis_len = get_visible_text_length(text, self.is_rich_text)
        self.counter_lbl.setText(f"{vis_len} / {self.max_chars}")
        if vis_len > self.max_chars:
            self.counter_lbl.setStyleSheet("color: #E53E3E; font-weight: bold; font-size: 11px;")
        else:
            self.counter_lbl.setStyleSheet("color: #718096; font-size: 11px;")

    def is_enabled(self) -> bool:
        return self.checkbox.isChecked()

    def set_enabled(self, enabled: bool) -> None:
        self.checkbox.setChecked(enabled)

    def get_text(self) -> str:
        if self.is_rich_text and self.rich_editor:
            return self.rich_editor.toHtml()
        if self.plain_editor:
            return self.plain_editor.toPlainText()
        return ""

    def set_text(self, text: str) -> None:
        if self.is_rich_text and self.rich_editor:
            self.rich_editor.setHtml(text)
        elif self.plain_editor:
            self.plain_editor.setPlainText(text)
        self._update_counter()

    def to_offer_section(self, position: int = 0) -> OfferSection:
        return OfferSection(
            section_key=self.section_key,
            enabled=self.is_enabled(),
            text=self.get_text(),
            rich_text=self.is_rich_text,
            position=position,
        )


class SectionsWidget(QWidget):
    """Şartname Bölüm 7.6'daki 6 ticari koşul alanını yöneten bileşen."""

    sections_changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._cards: dict[SectionKey, SingleSectionCard] = {}
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        group = QGroupBox("Ticari Koşullar ve Ek Notlar")
        grid = QGridLayout(group)
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(12)

        defaults = load_section_defaults()

        sections_info = [
            (SectionKey.DELIVERY_ADDRESS, 0, 0),
            (SectionKey.ORDER_NOTIFICATION, 0, 1),
            (SectionKey.DELIVERY_METHOD, 1, 0),
            (SectionKey.PAYMENT_TERMS, 1, 1),
            (SectionKey.STORAGE_CONDITIONS, 2, 0),
            (SectionKey.ADDITIONAL_NOTES, 2, 1),
        ]

        for s_key, r, c in sections_info:
            d_conf = defaults.get(s_key.value)
            label = d_conf.label if d_conf else s_key.label_tr
            d_text = d_conf.default_text if d_conf else ""
            max_c = d_conf.max_chars if d_conf else s_key.max_chars
            is_rich = d_conf.rich_text if d_conf else s_key.is_rich_text

            card = SingleSectionCard(
                section_key=s_key,
                label=label,
                default_text=d_text,
                max_chars=max_c,
                is_rich_text=is_rich,
            )
            card.changed.connect(self._on_changed)
            self._cards[s_key] = card
            grid.addWidget(card, r, c)

        main_layout.addWidget(group)

    def _on_changed(self) -> None:
        self.sections_changed.emit()

    def get_sections(self) -> list[OfferSection]:
        return [card.to_offer_section(pos) for pos, card in enumerate(self._cards.values())]

    def set_sections(self, sections: list[OfferSection]) -> None:
        sec_map = {s.section_key: s for s in sections}
        for s_key, card in self._cards.items():
            if s_key in sec_map:
                s = sec_map[s_key]
                card.set_text(s.text)
                card.set_enabled(s.enabled)
            else:
                card.set_enabled(False)
                card.set_text("")
