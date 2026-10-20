"""SQLite veritabanı şema sürümü ve migrasyon yönetimi."""

from __future__ import annotations

from datetime import datetime, timezone
import sqlite3

MIGRATIONS: dict[int, str] = {
    1: """
    -- Şema sürüm takip tablosu
    CREATE TABLE IF NOT EXISTS schema_migrations (
        version INTEGER PRIMARY KEY,
        applied_at TEXT NOT NULL
    );

    -- Günlük teklif sayacı tablosu
    CREATE TABLE IF NOT EXISTS daily_sequences (
        offer_date TEXT PRIMARY KEY,
        last_sequence INTEGER NOT NULL DEFAULT 0
    );

    -- Ana teklif tablosu
    CREATE TABLE IF NOT EXISTS offers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        offer_number TEXT UNIQUE NOT NULL,
        offer_date TEXT NOT NULL,
        company_id TEXT NOT NULL,
        recipient_name TEXT NOT NULL,
        currency_code TEXT NOT NULL,
        quantity_unit TEXT NOT NULL,
        vat_enabled INTEGER NOT NULL DEFAULT 0,
        vat_rate TEXT NOT NULL DEFAULT '0',
        discount_enabled INTEGER NOT NULL DEFAULT 0,
        brand_logo_visible INTEGER NOT NULL DEFAULT 0,
        selected_columns TEXT NOT NULL,
        source_offer_id INTEGER REFERENCES offers(id) ON DELETE SET NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );

    -- Ürün satırları tablosu
    CREATE TABLE IF NOT EXISTS offer_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        offer_id INTEGER NOT NULL REFERENCES offers(id) ON DELETE CASCADE,
        position INTEGER NOT NULL,
        product_code TEXT NOT NULL DEFAULT '',
        description TEXT NOT NULL,
        quantity_value TEXT NOT NULL,
        pallet_count TEXT,
        unit_price TEXT NOT NULL,
        discount_type TEXT NOT NULL DEFAULT 'none',
        discount_value TEXT NOT NULL DEFAULT '0'
    );

    -- Ticari koşullar tablosu
    CREATE TABLE IF NOT EXISTS offer_sections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        offer_id INTEGER NOT NULL REFERENCES offers(id) ON DELETE CASCADE,
        section_key TEXT NOT NULL,
        enabled INTEGER NOT NULL DEFAULT 0,
        text TEXT NOT NULL DEFAULT '',
        rich_text INTEGER NOT NULL DEFAULT 0,
        position INTEGER NOT NULL DEFAULT 0
    );

    -- Performans ve arama indeksleri
    CREATE INDEX IF NOT EXISTS idx_offers_date ON offers(offer_date);
    CREATE INDEX IF NOT EXISTS idx_offers_recipient ON offers(recipient_name);
    CREATE INDEX IF NOT EXISTS idx_items_offer_id ON offer_items(offer_id);
    CREATE INDEX IF NOT EXISTS idx_sections_offer_id ON offer_sections(offer_id);
    """
}


def get_current_version(conn: sqlite3.Connection) -> int:
    """Uygulanmış en son şema sürümünü döndürür."""
    try:
        cursor = conn.execute("SELECT MAX(version) FROM schema_migrations")
        row = cursor.fetchone()
        return row[0] if (row and row[0] is not None) else 0
    except sqlite3.OperationalError:
        # schema_migrations tablosu henüz yoksa sürüm 0'dır
        return 0


def apply_migrations(conn: sqlite3.Connection) -> int:
    """Eksik tüm migrasyonları sırayla uygular ve güncel sürüm numarasını döndürür."""
    current_ver = get_current_version(conn)

    for ver in sorted(MIGRATIONS.keys()):
        if ver > current_ver:
            script = MIGRATIONS[ver]
            conn.executescript(script)
            now_iso = datetime.now(timezone.utc).isoformat()
            conn.execute(
                "INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)",
                (ver, now_iso),
            )
            conn.commit()
            current_ver = ver

    return current_ver
