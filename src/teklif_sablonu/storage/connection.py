"""SQLite bağlantı yönetimi modülü."""

from __future__ import annotations

from pathlib import Path
import sqlite3

from teklif_sablonu.config import get_db_path


def get_connection(db_path: Path | str | None = None) -> sqlite3.Connection:
    """SQLite veritabanı bağlantısı oluşturur ve yapılandırır.

    Kurallar:
    - db_path belirtilmezse işletim sisteminin kullanıcı veri dizinindeki
      (macOS: ~/Library/Application Support/TeklifSablonu/, Windows: %LOCALAPPDATA%/TeklifSablonu/)
      yol kullanılır.
    - foreign_keys = ON pragma'sı etkinleştirilir.
    - sqlite3.Row row_factory kullanılır.
    """
    if db_path is None:
        db_path = get_db_path()

    if isinstance(db_path, str) and db_path != ":memory:":
        db_path = Path(db_path)

    if isinstance(db_path, Path):
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path))
    else:
        conn = sqlite3.connect(":memory:")

    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    # Performans ve eşzamanlılık için WAL modu (bellek içi değilse)
    if isinstance(db_path, Path):
        conn.execute("PRAGMA journal_mode = WAL;")

    return conn
