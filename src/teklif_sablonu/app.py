"""QApplication oluşturma ve yapılandırma."""

from __future__ import annotations

import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from teklif_sablonu import __version__
from teklif_sablonu.config import ASSETS_DIR
from teklif_sablonu.ui.main_window import MainWindow


def create_app(argv: list[str] | None = None) -> tuple[QApplication, MainWindow]:
    """QApplication ve ana pencereyi oluşturur.

    Returns:
        (app, window) çifti.
    """
    if argv is None:
        argv = sys.argv

    app = QApplication.instance()
    if app is None:
        app = QApplication(argv)
    app.setApplicationName("Teklif Şablonu")
    app.setOrganizationName("Endemiks")
    app.setApplicationVersion(__version__)

    icon_path = ASSETS_DIR / "app_icon.png"
    if icon_path.exists():
        app_icon = QIcon(str(icon_path))
        app.setWindowIcon(app_icon)

    window = MainWindow()
    if icon_path.exists():
        window.setWindowIcon(QIcon(str(icon_path)))

    return app, window

