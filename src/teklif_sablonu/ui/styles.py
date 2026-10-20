"""Uygulama arayüz stilleri (QSS) ve görsel sabitler."""

MAIN_STYLE = """
/* Genel Pencere ve Yazı Tipleri */
QWidget {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
    color: #2D3748;
}

QMainWindow, QDialog {
    background-color: #F7FAFC;
}

QScrollArea {
    border: none;
    background-color: transparent;
}

/* Grup Kutuları */
QGroupBox {
    font-weight: 600;
    font-size: 13px;
    color: #2B6CB0;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    margin-top: 14px;
    padding-top: 18px;
    padding-bottom: 12px;
    padding-left: 12px;
    padding-right: 12px;
    background-color: #FFFFFF;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 2px 8px;
    background-color: #EBF8FF;
    border: 1px solid #BEE3F8;
    border-radius: 4px;
    left: 14px;
}

/* Giriş Alanları */
QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox {
    border: 1px solid #CBD5E0;
    border-radius: 6px;
    padding: 6px 10px;
    background-color: #FFFFFF;
    selection-background-color: #3182CE;
}

QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1.5px solid #3182CE;
    background-color: #F7FAFC;
}

QLineEdit:disabled, QComboBox:disabled, QDateEdit:disabled {
    background-color: #EDF2F7;
    color: #A0AEC0;
    border-color: #E2E8F0;
}

/* Butonlar */
QPushButton {
    background-color: #3182CE;
    color: #FFFFFF;
    font-weight: 500;
    border: none;
    border-radius: 6px;
    padding: 6px 14px;
}

QPushButton:hover {
    background-color: #2B6CB0;
}

QPushButton:pressed {
    background-color: #2C5282;
}

QPushButton:disabled {
    background-color: #CBD5E0;
    color: #A0AEC0;
}

QPushButton.secondary {
    background-color: #EDF2F7;
    color: #4A5568;
    border: 1px solid #CBD5E0;
}

QPushButton.secondary:hover {
    background-color: #E2E8F0;
    color: #2D3748;
}

QPushButton.danger {
    background-color: #E53E3E;
    color: #FFFFFF;
}

QPushButton.danger:hover {
    background-color: #C53030;
}

/* Tablolar */
QTableWidget {
    background-color: #FFFFFF;
    alternate-background-color: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    gridline-color: #EDF2F7;
    selection-background-color: #EBF8FF;
    selection-color: #2B6CB0;
}

QHeaderView::section {
    background-color: #EDF2F7;
    color: #4A5568;
    font-weight: 600;
    font-size: 12px;
    border: none;
    border-bottom: 2px solid #CBD5E0;
    border-right: 1px solid #E2E8F0;
    padding: 6px;
}

/* Sekmeler */
QTabWidget::pane {
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    background-color: #FFFFFF;
    top: -1px;
}

QTabBar::tab {
    background-color: #EDF2F7;
    color: #4A5568;
    font-weight: 600;
    padding: 8px 18px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}

QTabBar::tab:selected {
    background-color: #FFFFFF;
    color: #2B6CB0;
    border: 1px solid #E2E8F0;
    border-bottom: 2px solid #3182CE;
}

/* Durum Çubuğu */
QStatusBar {
    background-color: #EDF2F7;
    color: #4A5568;
    border-top: 1px solid #E2E8F0;
    font-size: 12px;
}
"""
