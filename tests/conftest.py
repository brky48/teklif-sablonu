"""Pytest fixtures for teklif_sablonu tests."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Generator

import pytest

# Offscreen platform for Qt in headless / CI environments
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture
def temp_data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Geçici kullanıcı veri dizini sağlar ve platformdirs.user_data_dir çağrısını yönlendirir."""
    target_dir = tmp_path / "TeklifSablonu"
    monkeypatch.setattr(
        "teklif_sablonu.config.settings.user_data_dir",
        lambda appname, appauthor: str(target_dir),
    )
    return target_dir


@pytest.fixture(autouse=True)
def prevent_gui_deadlock(monkeypatch: pytest.MonkeyPatch) -> None:
    """PySide6 modal diyaloglarının test sürecini bloke etmesini (deadlock) önler."""
    try:
        from PySide6.QtWidgets import QFileDialog, QMessageBox
    except ImportError:
        return

    monkeypatch.setattr(
        QMessageBox, "information", lambda *args, **kwargs: QMessageBox.StandardButton.Ok
    )
    monkeypatch.setattr(
        QMessageBox, "warning", lambda *args, **kwargs: QMessageBox.StandardButton.Ok
    )
    monkeypatch.setattr(
        QMessageBox, "critical", lambda *args, **kwargs: QMessageBox.StandardButton.Ok
    )
    monkeypatch.setattr(
        QMessageBox, "question", lambda *args, **kwargs: QMessageBox.StandardButton.Yes
    )
    monkeypatch.setattr(
        QMessageBox, "exec", lambda *args, **kwargs: QMessageBox.StandardButton.Ok
    )
    monkeypatch.setattr(
        QMessageBox, "exec_", lambda *args, **kwargs: QMessageBox.StandardButton.Ok
    )
    monkeypatch.setattr(
        QFileDialog,
        "getSaveFileName",
        lambda *args, **kwargs: (str(args[2]) if len(args) > 2 and args[2] else "/tmp/mock_file.pdf", "PDF"),
    )
    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        lambda *args, **kwargs: ("/tmp/mock_file.pdf", "PDF"),
    )


@pytest.fixture(autouse=True)
def qapp() -> Any:
    """Qt uygulaması tekil örneğini hazırlar."""
    try:
        from PySide6.QtWidgets import QApplication

        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        return app
    except ImportError:
        return None


