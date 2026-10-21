"""Yapılandırma ve ayar testleri."""

from __future__ import annotations

from pathlib import Path

from teklif_sablonu.config import (
    ASSETS_DIR,
    BRANDS_DIR,
    COMPANIES_DIR,
    FONTS_DIR,
    AppConfig,
    CompanyInfo,
    SectionDefault,
    get_db_path,
    get_user_data_dir,
    load_app_config,
    load_companies,
    load_section_defaults,
)


def test_user_data_dir_creation(temp_data_dir: Path) -> None:
    """Kullanıcı veri dizini oluşturulabilir ve yazılabilir olmalıdır."""
    data_dir = get_user_data_dir()
    assert data_dir.exists()
    assert data_dir == temp_data_dir
    test_file = data_dir / "test.txt"
    test_file.write_text("ok", encoding="utf-8")
    assert test_file.read_text(encoding="utf-8") == "ok"


def test_db_path(temp_data_dir: Path) -> None:
    """Veritabanı yolu kullanıcı veri dizini içinde olmalıdır."""
    db_path = get_db_path()
    assert db_path.parent == temp_data_dir
    assert db_path.name == "teklif_sablonu.db"


def test_load_companies() -> None:
    """Şirket yapılandırması yüklenmeli; Endemiks Tarım tam, Gıda ise placeholder olmalıdır."""
    companies = load_companies()
    assert len(companies) == 2

    # Endemiks Tarım
    tarim = next((c for c in companies if c.id == "endemiks_tarim"), None)
    assert tarim is not None
    assert tarim.name == "Endemiks Tarım Ticaret A.Ş."
    assert "334" in tarim.tax_id
    assert not tarim.has_placeholder()

    # Endemiks Gıda - Gerçek şirket bilgileri girilmiş olmalı
    gida = next((c for c in companies if c.id == "endemiks_gida"), None)
    assert gida is not None
    assert gida.name == "Endemiks Gıda LTD. ŞTİ."
    assert not gida.has_placeholder()
    assert gida.tax_id == "334 126 0377"
    assert "KÖYCEĞİZ" in gida.tax_office


def test_load_section_defaults() -> None:
    """Bölüm 7.6'daki varsayılan koşul metinleri eksiksiz yüklenmelidir."""
    sections = load_section_defaults()
    expected_keys = [
        "delivery_address",
        "order_notification",
        "delivery_method",
        "payment_terms",
        "storage_conditions",
        "additional_notes",
    ]
    assert len(sections) == len(expected_keys)
    for key in expected_keys:
        assert key in sections, f"{key} eksik!"
        assert isinstance(sections[key], SectionDefault)
        assert sections[key].max_chars > 0

    # Saklama Koşulları ve Ek Alan varsayılan olarak boş başlamalıdır
    assert sections["storage_conditions"].default_text == ""
    assert sections["additional_notes"].default_text == ""
    # Ek Alan rich_text desteklemelidir
    assert sections["additional_notes"].rich_text is True


def test_load_app_config() -> None:
    """Tüm uygulama yapılandırması AppConfig dataclass'ına yüklenmelidir."""
    config = load_app_config()
    assert isinstance(config, AppConfig)
    assert len(config.companies) == 2
    assert len(config.section_defaults) == 6


def test_assets_directories_exist() -> None:
    """Asset dizin yolları tanımlı ve dizinler mevcut olmalıdır."""
    assert ASSETS_DIR.exists()
    assert COMPANIES_DIR.exists()
    assert BRANDS_DIR.exists()
    assert FONTS_DIR.exists()
