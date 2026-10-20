"""UI temel duman (smoke) testi."""

from __future__ import annotations

import pytest

try:
    from PySide6.QtWidgets import QApplication
    from teklif_sablonu.ui.main_window import MainWindow

    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False


@pytest.mark.skipif(not PYSIDE6_AVAILABLE, reason="PySide6 kurulu değil")
def test_create_app() -> None:
    """create_app fonksiyonu geçerli app ve window çifti döndürmelidir."""
    from teklif_sablonu.app import create_app

    app, window = create_app(["test_app"])
    assert app.applicationName() == "Teklif Şablonu"
    assert app.organizationName() == "Endemiks"
    assert isinstance(window, MainWindow)
    window.close()
    app.processEvents()

