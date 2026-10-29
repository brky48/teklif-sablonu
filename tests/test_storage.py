"""SQLite depolama ve Repository katmanı birim/entegrasyon testleri."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
import sqlite3
import pytest

from teklif_sablonu.domain.enums import (
    ColumnKey,
    CurrencyCode,
    DiscountType,
    QuantityUnit,
    SectionKey,
)
from teklif_sablonu.domain.models import CustomPage, Offer, OfferItem, OfferSection
from teklif_sablonu.storage.connection import get_connection
from teklif_sablonu.storage.migrations import apply_migrations, get_current_version
from teklif_sablonu.storage.repository import (
    RepositoryError,
    SqliteOfferRepository,
)


@pytest.fixture
def mem_repo() -> SqliteOfferRepository:
    """Testler için temiz bellek-içi (in-memory) SQLite repository sağlar."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return SqliteOfferRepository(conn)


def test_schema_migrations(mem_repo: SqliteOfferRepository) -> None:
    """Veritabanı şema migrasyonları eksiksiz uygulanmalıdır."""
    ver = get_current_version(mem_repo.conn)
    assert ver >= 1

    # Tabloların varlığını doğrula
    cursor = mem_repo.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )
    table_names = {row["name"] for row in cursor.fetchall()}
    assert "schema_migrations" in table_names
    assert "daily_sequences" in table_names
    assert "offers" in table_names
    assert "offer_items" in table_names
    assert "offer_sections" in table_names


def test_daily_sequence_generation(mem_repo: SqliteOfferRepository) -> None:
    """Sayaç tarih bazlı artmalı; YYYYMMDD-NNN formatında üretilmeli ve 999'u kesilmeden geçmelidir."""
    d1 = date(2026, 10, 20)
    seq1, num1 = mem_repo.get_next_sequence(d1)
    assert seq1 == 1
    assert num1 == "20261020-001"

    seq2, num2 = mem_repo.get_next_sequence(d1)
    assert seq2 == 2
    assert num2 == "20261020-002"

    # Farklı tarihte sayaç 1'den başlamalıdır
    d2 = date(2026, 10, 21)
    seq_d2, num_d2 = mem_repo.get_next_sequence(d2)
    assert seq_d2 == 1
    assert num_d2 == "20261021-001"

    # 999'u aşma durumu (kesilmeden devam etmeli)
    mem_repo.conn.execute(
        "UPDATE daily_sequences SET last_sequence = 999 WHERE offer_date = ?",
        (d1.isoformat(),),
    )
    seq1000, num1000 = mem_repo.get_next_sequence(d1)
    assert seq1000 == 1000
    assert num1000 == "20261020-1000"


def test_save_and_retrieve_offer(mem_repo: SqliteOfferRepository) -> None:
    """Yeni teklif kaydedilmeli, otomatik numara almalı ve geri okunabilmelidir."""
    offer = Offer(
        offer_date=date(2026, 10, 20),
        company_id="endemiks_tarim",
        recipient_name="Antalya Tarım A.Ş.",
        currency_code=CurrencyCode.TRY,
        quantity_unit=QuantityUnit.PIECE,
        vat_enabled=True,
        vat_rate=Decimal("20.00"),
        discount_enabled=True,
        brand_logo_visible=True,
        selected_columns=[ColumnKey.DESCRIPTION, ColumnKey.QUANTITY, ColumnKey.UNIT_PRICE, ColumnKey.TOTAL_AMOUNT],
        items=[
            OfferItem(
                product_code="KOD-1",
                description="Ürün 1",
                quantity=Decimal("15.50"),
                pallet=Decimal("2.00"),
                unit_price=Decimal("120.00"),
                discount_type=DiscountType.RATE,
                discount_value=Decimal("10.00"),
            )
        ],
        sections=[
            OfferSection(
                section_key=SectionKey.DELIVERY_ADDRESS,
                enabled=True,
                text="Adrese teslim",
            )
        ],
    )

    saved = mem_repo.save(offer)
    assert saved.id is not None
    assert saved.offer_number == "20261020-001"
    assert saved.created_at is not None

    # ID ile getir
    retrieved = mem_repo.get_by_id(saved.id)
    assert retrieved is not None
    assert retrieved.offer_number == "20261020-001"
    assert retrieved.recipient_name == "Antalya Tarım A.Ş."
    assert retrieved.vat_enabled is True
    assert retrieved.vat_rate == Decimal("20.00")
    assert retrieved.brand_logo_visible is True
    assert len(retrieved.items) == 1
    assert retrieved.items[0].description == "Ürün 1"
    assert retrieved.items[0].quantity == Decimal("15.50")
    assert retrieved.items[0].unit_price == Decimal("120.00")
    assert retrieved.items[0].discount_type == DiscountType.RATE
    assert retrieved.items[0].discount_value == Decimal("10.00")
    assert len(retrieved.sections) == 1
    assert retrieved.sections[0].text == "Adrese teslim"

    # Numara ile getir
    by_num = mem_repo.get_by_number("20261020-001")
    assert by_num is not None
    assert by_num.id == saved.id


def test_update_offer_preserves_number(mem_repo: SqliteOfferRepository) -> None:
    """Mevcut teklif güncellendiğinde teklif numarası kesinlikle değişmemelidir."""
    offer = Offer(
        offer_date=date(2026, 10, 20),
        company_id="endemiks_tarim",
        recipient_name="İlk Alıcı",
        items=[OfferItem(description="Kalem", quantity=Decimal("1"), unit_price=Decimal("10"))],
    )
    saved = mem_repo.save(offer)
    orig_num = saved.offer_number
    orig_id = saved.id

    # Güncelle
    saved.recipient_name = "Güncellenmiş Alıcı"
    saved.items[0].quantity = Decimal("5")
    updated = mem_repo.save(saved)

    assert updated.id == orig_id
    assert updated.offer_number == orig_num
    assert updated.recipient_name == "Güncellenmiş Alıcı"

    # Yeniden sorgula
    fresh = mem_repo.get_by_id(orig_id)
    assert fresh is not None
    assert fresh.offer_number == orig_num
    assert fresh.recipient_name == "Güncellenmiş Alıcı"
    assert fresh.items[0].quantity == Decimal("5")


def test_list_offers_and_search(mem_repo: SqliteOfferRepository) -> None:
    """Teklif listesi ve arama sorguları doğru çalışmalıdır."""
    o1 = Offer(
        offer_date=date(2026, 10, 20),
        recipient_name="Toros Gübre",
        items=[OfferItem(description="A", quantity=Decimal("1"), unit_price=Decimal("10"))],
    )
    o2 = Offer(
        offer_date=date(2026, 10, 20),
        recipient_name="Çukurova Tarım",
        items=[OfferItem(description="B", quantity=Decimal("2"), unit_price=Decimal("20"))],
    )
    mem_repo.save(o1)
    mem_repo.save(o2)

    all_offers = mem_repo.list_offers()
    assert len(all_offers) == 2

    # Arama
    res_toros = mem_repo.list_offers(search="Toros")
    assert len(res_toros) == 1
    assert res_toros[0].recipient_name == "Toros Gübre"

    res_none = mem_repo.list_offers(search="Bulunamayan")
    assert len(res_none) == 0


def test_delete_offer_cascade(mem_repo: SqliteOfferRepository) -> None:
    """Teklif silindiğinde ilişkili kalemleri de silinmelidir."""
    offer = Offer(
        offer_date=date(2026, 10, 20),
        recipient_name="Silinecek Firma",
        items=[OfferItem(description="Madde 1", quantity=Decimal("1"), unit_price=Decimal("10"))],
        sections=[OfferSection(section_key=SectionKey.DELIVERY_ADDRESS, text="Test")],
    )
    saved = mem_repo.save(offer)
    offer_id = saved.id
    assert offer_id is not None

    deleted = mem_repo.delete(offer_id)
    assert deleted is True

    assert mem_repo.get_by_id(offer_id) is None
    # İlişkili tabloların boşaldığını doğrula (ON DELETE CASCADE)
    items_count = mem_repo.conn.execute(
        "SELECT count(*) FROM offer_items WHERE offer_id = ?", (offer_id,)
    ).fetchone()[0]
    assert items_count == 0


def test_rollback_on_failure(mem_repo: SqliteOfferRepository) -> None:
    """Hata durumunda transaction geri alınmalı (rollback) ve bozuk kayıt kalmamalıdır."""
    offer = Offer(
        offer_date=date(2026, 10, 20),
        recipient_name="Hata Testi",
        items=[OfferItem(description="Madde 1", quantity=Decimal("1"), unit_price=Decimal("10"))],
    )

    # offer_items tablosuna yazarken hata fırlatacak bir trigger ekle
    mem_repo.conn.execute(
        "CREATE TRIGGER test_fail_trigger BEFORE INSERT ON offer_items BEGIN SELECT RAISE(FAIL, 'Simule edilmis DB hatasi'); END;"
    )

    with pytest.raises(RepositoryError, match="veritabanına kaydedilirken hata"):
        mem_repo.save(offer)

    # offers tablosuna kayıt eklenmemiş olmalıdır (Rollback doğrulandı)
    count = mem_repo.conn.execute("SELECT count(*) FROM offers").fetchone()[0]
    assert count == 0


def test_ready_templates_persistence(mem_repo: SqliteOfferRepository) -> None:
    """Hazır şablon checkbox tercihleri veritabanına doğru kaydedilip okunmalıdır."""
    offer = Offer(
        offer_date=date(2026, 10, 26),
        recipient_name="Hazır Şablon Testi",
        template_packaging_info=True,
        template_storage_conditions=False,
        template_harvest_calendar=True,
        template_product_info=True,
        template_product_info_items=["quality_guarantee", "lemonade_extract"],
        items=[OfferItem(description="Ürün", quantity=Decimal("1"), unit_price=Decimal("100"))],
    )
    saved = mem_repo.save(offer)
    retrieved = mem_repo.get_by_id(saved.id)
    assert retrieved is not None
    assert retrieved.template_packaging_info is True
    assert retrieved.template_storage_conditions is False
    assert retrieved.template_harvest_calendar is True
    assert retrieved.template_product_info is True
    assert retrieved.template_product_info_items == ["quality_guarantee", "lemonade_extract"]

    # Güncelleme testi
    retrieved.template_storage_conditions = True
    retrieved.template_harvest_calendar = False
    retrieved.template_product_info_items = ["quality_guarantee", "orange_juice", "pomegranate_juice"]
    updated = mem_repo.save(retrieved)
    re_retrieved = mem_repo.get_by_id(updated.id)
    assert re_retrieved is not None
    assert re_retrieved.template_packaging_info is True
    assert re_retrieved.template_storage_conditions is True
    assert re_retrieved.template_harvest_calendar is False
    assert re_retrieved.template_product_info is True
    assert re_retrieved.template_product_info_items == ["quality_guarantee", "orange_juice", "pomegranate_juice"]


def test_pdf_font_size_persistence(mem_repo: SqliteOfferRepository) -> None:
    """PDF font boyutu tercihi veritabanına doğru kaydedilip güncellenmelidir."""
    offer = Offer(
        offer_date=date(2026, 10, 26),
        recipient_name="Font Boyutu Testi",
        pdf_font_size=7.5,
        items=[OfferItem(description="Ürün", quantity=Decimal("1"), unit_price=Decimal("100"))],
    )
    saved = mem_repo.save(offer)
    retrieved = mem_repo.get_by_id(saved.id)
    assert retrieved is not None
    assert abs(retrieved.pdf_font_size - 7.5) < 0.01

    # Güncelleme
    retrieved.pdf_font_size = 6.5
    updated = mem_repo.save(retrieved)
    re_retrieved = mem_repo.get_by_id(updated.id)
    assert re_retrieved is not None
    assert abs(re_retrieved.pdf_font_size - 6.5) < 0.01


def test_custom_pages_persistence(mem_repo: SqliteOfferRepository) -> None:
    """Özel / Ek Sayfalar (Custom Pages) veritabanına kaydedilmeli, geri okunmalı ve güncellenebilmelidir."""
    offer = Offer(
        offer_date=date(2026, 10, 29),
        recipient_name="Ek Sayfa Testi Ltd.",
        custom_pages=[
            CustomPage(
                position=0,
                title="EK-1: ULUSLARARASI LEZZET VE KALİTE SERTİFİKASI",
                content_html="<p>Bu sertifika bağımsız şefler tarafından test edilmiştir.</p>",
                image_path="/path/to/cert.png",
                font_size=8.0,
            ),
            CustomPage(
                position=1,
                title="EK-2: ANALİZ VE AKREDİTASYON",
                content_html="<p>Laboratuvar analiz değerleri.</p>",
                image_path=None,
                font_size=7.5,
            ),
        ],
        items=[OfferItem(description="Kalem 1", quantity=Decimal("1"), unit_price=Decimal("100"))],
    )
    saved = mem_repo.save(offer)
    assert saved.id is not None

    retrieved = mem_repo.get_by_id(saved.id)
    assert retrieved is not None
    assert len(retrieved.custom_pages) == 2
    assert retrieved.custom_pages[0].position == 0
    assert retrieved.custom_pages[0].title == "EK-1: ULUSLARARASI LEZZET VE KALİTE SERTİFİKASI"
    assert "bağımsız şefler" in retrieved.custom_pages[0].content_html
    assert retrieved.custom_pages[0].image_path == "/path/to/cert.png"
    assert abs(retrieved.custom_pages[0].font_size - 8.0) < 0.01

    assert retrieved.custom_pages[1].position == 1
    assert retrieved.custom_pages[1].title == "EK-2: ANALİZ VE AKREDİTASYON"
    assert retrieved.custom_pages[1].image_path is None or retrieved.custom_pages[1].image_path == ""
    assert abs(retrieved.custom_pages[1].font_size - 7.5) < 0.01

    # Güncelleme: 1 sayfayı sil, birini değiştir, yeni sayfa ekle
    retrieved.custom_pages = [
        CustomPage(
            position=0,
            title="EK-1: GÜNCELLENMİŞ SERTİFİKA",
            content_html="<p>Güncellenmiş içerik</p>",
            image_path="/path/to/new_cert.png",
            font_size=9.0,
        )
    ]
    updated = mem_repo.save(retrieved)
    re_retrieved = mem_repo.get_by_id(updated.id)
    assert re_retrieved is not None
    assert len(re_retrieved.custom_pages) == 1
    assert re_retrieved.custom_pages[0].title == "EK-1: GÜNCELLENMİŞ SERTİFİKA"
    assert re_retrieved.custom_pages[0].image_path == "/path/to/new_cert.png"
    assert abs(re_retrieved.custom_pages[0].font_size - 9.0) < 0.01

    # Silme durumunda cascade
    offer_id = updated.id
    mem_repo.delete(offer_id)
    cp_count = mem_repo.conn.execute(
        "SELECT count(*) FROM offer_custom_pages WHERE offer_id = ?", (offer_id,)
    ).fetchone()[0]
    assert cp_count == 0

