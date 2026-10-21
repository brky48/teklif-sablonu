"""Uygulama ayarları ve yardımcı fonksiyonlar.

Bu modül:
- İşletim sistemine uygun kullanıcı veri dizinini belirler (SQLite DB burada saklanır).
- Şirket ve varsayılan metin yapılandırmalarını yükler.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
import sys
from typing import Any

from platformdirs import user_data_dir

# ──────────────────────────────────────────────
# Sabitler
# ──────────────────────────────────────────────

APP_NAME = "TeklifSablonu"
APP_AUTHOR = "Endemiks"
DB_FILENAME = "teklif_sablonu.db"
RECIPIENT_MAX_CHARS = 200


def get_bundle_dir() -> Path:
    """Paketlenmiş (PyInstaller) veya geliştirme ortamındaki kök paket dizinini döndürür."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        meipass = Path(sys._MEIPASS)
        if (meipass / "teklif_sablonu" / "config").exists():
            return meipass / "teklif_sablonu"
        return meipass
    return Path(__file__).parent.parent


# ──────────────────────────────────────────────
# Veri dizini
# ──────────────────────────────────────────────


def get_user_data_dir() -> Path:
    """İşletim sistemine uygun yazılabilir kullanıcı veri dizinini döndürür.

    - Windows : %LOCALAPPDATA%/TeklifSablonu/
    - macOS   : ~/Library/Application Support/TeklifSablonu/
    - Linux   : ~/.local/share/TeklifSablonu/

    Dizin mevcut değilse oluşturulur.
    """
    data_dir = Path(user_data_dir(appname=APP_NAME, appauthor=APP_AUTHOR))
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_db_path() -> Path:
    """SQLite veritabanı dosyasının tam yolunu döndürür."""
    return get_user_data_dir() / DB_FILENAME


# ──────────────────────────────────────────────
# Yapılandırma yükleme
# ──────────────────────────────────────────────

_CONFIG_DIR = get_bundle_dir() / "config"


def _load_json(filename: str) -> dict[str, Any]:
    """config/ dizinindeki bir JSON dosyasını yükler."""
    filepath = _CONFIG_DIR / filename
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)


@dataclass(frozen=True)
class CompanyInfo:
    """Tek bir şirketin yapılandırma bilgileri."""

    id: str
    name: str
    display_name: str
    address_label: str
    address_lines: list[str]
    tax_office: str
    tax_id: str
    logo_path: str | None = None
    address_label_en: str = "Headquarters and Factory"

    def has_placeholder(self) -> bool:
        """Şirket bilgilerinde TODO/placeholder var mı kontrol eder."""
        fields = [
            self.address_label,
            self.tax_office,
            self.tax_id,
            *self.address_lines,
        ]
        return any("TODO" in f for f in fields)


@dataclass(frozen=True)
class SectionDefault:
    """Bir ticari koşul alanının varsayılan ayarları."""

    label: str
    default_text: str
    max_chars: int
    rich_text: bool = False


@dataclass(frozen=True)
class AppConfig:
    """Uygulamanın tüm yapılandırma verilerini tutan salt-okunur yapı."""

    companies: list[CompanyInfo] = field(default_factory=list)
    section_defaults: dict[str, SectionDefault] = field(default_factory=dict)


def load_companies() -> list[CompanyInfo]:
    """companies.json dosyasından şirket bilgilerini yükler."""
    data = _load_json("companies.json")
    return [CompanyInfo(**company) for company in data["companies"]]


def load_section_defaults() -> dict[str, SectionDefault]:
    """default_texts.json dosyasından varsayılan koşul metinlerini yükler."""
    data = _load_json("default_texts.json")
    return {
        key: SectionDefault(**section_data)
        for key, section_data in data["sections"].items()
    }


def load_app_config() -> AppConfig:
    """Tüm yapılandırmayı yükleyip döndürür."""
    return AppConfig(
        companies=load_companies(),
        section_defaults=load_section_defaults(),
    )


# ──────────────────────────────────────────────
# Assets dizini
# ──────────────────────────────────────────────

_PACKAGE_ROOT = get_bundle_dir()
ASSETS_DIR = _PACKAGE_ROOT / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
BRANDS_DIR = ASSETS_DIR / "brands"
COMPANIES_DIR = ASSETS_DIR / "companies"

