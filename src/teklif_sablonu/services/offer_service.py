"""Uygulama teklif servisi (İş kuralları ve veri erişim koordinasyonu)."""

from __future__ import annotations

import copy
from datetime import date

from teklif_sablonu.domain.models import Offer
from teklif_sablonu.domain.validators import validate_offer
from teklif_sablonu.storage.repository import OfferRepository, SqliteOfferRepository


class OfferService:
    """Teklif işlemlerini yöneten merkezi servis."""

    def __init__(self, repository: OfferRepository | None = None) -> None:
        self.repository = repository or SqliteOfferRepository()

    def save_offer(self, offer: Offer) -> Offer:
        """Teklifi doğrular ve veritabanına kaydeder.

        Doğrulama hatası varsa ValueError fırlatır; veritabanı rollback'i repository tarafından sağlanır.
        """
        # 1. Domain seviyesinde doğrula
        validation = validate_offer(offer)
        validation.raise_if_invalid()

        # 2. Repository üzerinden atomik olarak kaydet
        return self.repository.save(offer)

    def get_offer(self, offer_id: int) -> Offer | None:
        """ID'ye göre teklif getirir."""
        return self.repository.get_by_id(offer_id)

    def get_offer_by_number(self, offer_number: str) -> Offer | None:
        """Teklif numarasına göre getirir."""
        return self.repository.get_by_number(offer_number)

    def list_offers(
        self,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Offer]:
        """Teklifleri arama filtresiyle listeler."""
        return self.repository.list_offers(search=search, limit=limit, offset=offset)

    def duplicate_offer(self, source_offer_id: int) -> Offer:
        """Belirtilen teklifi kopyalayarak yeni bir teklif nesnesi oluşturur.

        Şartname Kuralı:
        - Orijinal teklif kesinlikle değişmez.
        - Kopya yeni bir teklif numarası alacak şekilde id ve numarası sıfırlanır.
        - Tarih bugünün tarihi yapılır.
        - Kaynak teklif referansı (source_offer_id) tutulur.
        """
        source = self.repository.get_by_id(source_offer_id)
        if not source:
            raise ValueError(f"Kopyalanacak teklif bulunamadı (ID: {source_offer_id})")

        dup = copy.deepcopy(source)
        dup.id = None
        dup.offer_number = ""  # Kaydedilirken yeni numara üretilecek
        dup.offer_date = date.today()
        dup.source_offer_id = source_offer_id

        # Satır ID'lerini sıfırla
        for item in dup.items:
            item.id = None
            item.offer_id = None

        for sec in dup.sections:
            sec.id = None
            sec.offer_id = None

        return dup

    def delete_offer(self, offer_id: int) -> bool:
        """Teklifi siler."""
        return self.repository.delete(offer_id)
