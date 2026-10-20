"""storage paketi — Veri erişim katmanı (Repository ABC, SQLite)."""

from teklif_sablonu.storage.connection import get_connection
from teklif_sablonu.storage.migrations import (
    MIGRATIONS,
    apply_migrations,
    get_current_version,
)
from teklif_sablonu.storage.repository import (
    OfferRepository,
    RepositoryError,
    SqliteOfferRepository,
)

__all__ = [
    "get_connection",
    "get_current_version",
    "apply_migrations",
    "MIGRATIONS",
    "OfferRepository",
    "SqliteOfferRepository",
    "RepositoryError",
]
