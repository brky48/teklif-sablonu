"""Uygulama giriş noktası."""

from __future__ import annotations

import sys


def main() -> None:
    """Uygulamayı başlatır."""
    from teklif_sablonu.app import create_app

    app, window = create_app()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
