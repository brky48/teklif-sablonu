# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller yapılandırma dosyası (spec) — Teklif Şablonu.

Bu yapılandırma:
- PySide6, ReportLab, openpyxl, platformdirs ve SQLite bağımlılıklarını,
- Gömülü Türkçe fontları, şirket ve marka logolarını,
- Yapılandırma JSON dosyalarını (companies.json, default_texts.json)
Windows ortamında tekil .exe paketine dahil eder.
"""

from __future__ import annotations

import os
from pathlib import Path
import sys

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Proje dizinleri
project_root = Path(SPECPATH).resolve()
src_dir = project_root / "src"
package_dir = src_dir / "teklif_sablonu"

# Gömülecek veri dosyaları (assets ve config)
datas = [
    (str(package_dir / "config" / "*.json"), "teklif_sablonu/config"),
    (str(package_dir / "assets"), "teklif_sablonu/assets"),
]

# ReportLab font dosyalarını da topla
datas += collect_data_files("reportlab")

# Gizli importlar (dinamik yüklenen PySide6 ve kütüphaneler)
hiddenimports = [
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "PySide6.QtPdf",
    "reportlab",
    "reportlab.platypus",
    "reportlab.lib",
    "reportlab.lib.colors",
    "reportlab.lib.pagesizes",
    "reportlab.lib.styles",
    "reportlab.lib.units",
    "reportlab.pdfgen",
    "reportlab.pdfgen.canvas",
    "reportlab.pdfbase",
    "reportlab.pdfbase.ttfonts",
    "openpyxl",
    "openpyxl.styles",
    "openpyxl.styles.borders",
    "openpyxl.styles.fonts",
    "openpyxl.styles.fills",
    "openpyxl.styles.alignment",
    "openpyxl.utils",
    "openpyxl.drawing.image",
    "PIL",
    "PIL.Image",
    "platformdirs",
    "sqlite3",
]
hiddenimports += collect_submodules("teklif_sablonu")

a = Analysis(
    [str(package_dir / "main.py")],
    pathex=[str(src_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "unittest", "pytest"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher,
)

# Tek dosya (.exe) dağıtımı
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="TeklifSablonu",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Konsol penceresi gizli (Saf GUI masaüstü uygulaması)
    version=str(project_root / "version_info.txt"),
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
