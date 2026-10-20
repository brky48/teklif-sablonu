"""OfferService birim testleri."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
import sqlite3
import pytest

from teklif_sablonu.domain.models import Offer, OfferItem
from teklif_sablonu.services.offer_service import OfferService
from teklif_sablonu.storage.repository import SqliteOfferRepository


@pytest.fixture
def service() -> OfferService:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    repo = SqliteOfferRepository(conn)
    return OfferService(repo)


def test_save_offer_validates_domain_rules(service: OfferService) -> None:
    """Geçersiz teklif (ürün satırı olmayan) veritabanına kaydedilmeden reddedilmelidir."""
    invalid_offer = Offer(
        company_id="endemiks_tarim",
        items=[],  # Boş teklif
    )
    with pytest.raises(ValueError, match="Teklif doğrulaması başarısız"):
        service.save_offer(invalid_offer)


def test_save_offer_success(service: OfferService) -> None:
    """Geçerli teklif başarıyla doğrulanıp kaydedilmeli ve numara tahsis edilmelidir."""
    valid_offer = Offer(
        offer_date=date(2026, 10, 20),
        company_id="endemiks_tarim",
        recipient_name="Başarılı Teklif A.Ş.",
        items=[OfferItem(description="Ürün X", quantity=Decimal("10"), unit_price=Decimal("50"))],
    )
    saved = service.save_offer(valid_offer)
    assert saved.id is not None
    assert saved.offer_number == "20261020-001"

    # Servis üzerinden getir
    fetched = service.get_offer(saved.id)
    assert fetched is not None
    assert fetched.offer_number == "20261020-001"


def test_duplicate_offer(service: OfferService) -> None:
    """Teklif kopyalama orijinal kaydı korumalı, yeni teklif olarak hazırlanmalıdır."""
    orig = Offer(
        offer_date=date(2026, 10, 15),
        company_id="endemiks_tarim",
        recipient_name="Orijinal Müşteri",
        items=[OfferItem(description="Ürün 1", quantity=Decimal("5"), unit_price=Decimal("100"))],
    )
    saved_orig = service.save_offer(orig)
    orig_id = saved_orig.id
    orig_num = saved_orig.offer_number
    assert orig_id is not None

    # Kopyala
    dup = service.duplicate_offer(orig_id)
    assert dup.id is None
    assert dup.offer_number == ""  # Numara henüz yok
    assert dup.source_offer_id == orig_id
    assert dup.offer_date == date.today()
    assert dup.recipient_name == "Orijinal Müşteri"
    assert len(dup.items) == 1
    assert dup.items[0].id is None  # Satır ID'si sıfırlanmış olmalı

    # Kopyayı kaydet
    saved_dup = service.save_offer(dup)
    assert saved_dup.id != orig_id
    assert saved_dup.offer_number != orig_num

    # Orijinal kaydın değişmediğini doğrula
    orig_check = service.get_offer(orig_id)
    assert orig_check is not None
    assert orig_check.offer_number == orig_num
    assert orig_check.recipient_name == "Orijinal Müşteri"


def test_duplicate_nonexistent_offer_raises(service: OfferService) -> None:
    """Var olmayan teklif kopyalanmaya çalışıldığında ValueError üretilmelidir."""
    with pytest.raises(ValueError, match="Kopyalanacak teklif bulunamadı"):
        service.duplicate_offer(99999)
