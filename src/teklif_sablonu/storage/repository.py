"""Teklif verilerine erişim sağlayan Repository katmanı (Soyut Arayüz ve SQLite)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, datetime, timezone
from decimal import Decimal
import json
import sqlite3

from teklif_sablonu.domain.enums import (
    ColumnKey,
    CurrencyCode,
    DiscountType,
    DocumentLanguage,
    PageOrientation,
    QuantityUnit,
    SectionKey,
)
from teklif_sablonu.domain.models import Offer, OfferItem, OfferSection
from teklif_sablonu.storage.connection import get_connection
from teklif_sablonu.storage.migrations import apply_migrations


class RepositoryError(Exception):
    """Veritabanı işlem hatası."""


class OfferRepository(ABC):
    """Gelecekte SQLite yerine PostgreSQL veya REST API bağlanabilmesi için soyut Repository arayüzü."""

    @abstractmethod
    def save(self, offer: Offer) -> Offer:
        """Teklifi kaydeder veya günceller.

        Yeni tekliflerde seçilen tarihe göre YYYYMMDD-NNN formatında benzersiz numara üretir.
        Mevcut teklif güncellenirken numara kesinlikle değişmez.
        """
        ...

    @abstractmethod
    def get_by_id(self, offer_id: int) -> Offer | None:
        """ID'ye göre teklif ve ilişkili tüm ürün/koşul satırlarını getirir."""
        ...

    @abstractmethod
    def get_by_number(self, offer_number: str) -> Offer | None:
        """Teklif numarasına göre teklifi getirir."""
        ...

    @abstractmethod
    def list_offers(
        self,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Offer]:
        """Teklifleri arama ve sayfalamayla listeler."""
        ...

    @abstractmethod
    def delete(self, offer_id: int) -> bool:
        """Teklifi siler."""
        ...

    @abstractmethod
    def get_next_sequence(self, offer_date: date) -> tuple[int, str]:
        """Verilen tarih için bir sonraki sıra numarasını ve teklif numarasını (YYYYMMDD-NNN) üretir."""
        ...


class SqliteOfferRepository(OfferRepository):
    """OfferRepository arayüzünün SQLite uygulaması."""

    def __init__(self, conn: sqlite3.Connection | None = None) -> None:
        if conn is None:
            self.conn = get_connection()
        else:
            self.conn = conn

        # Şema sürümünü ve tabloları otomatik kontrol et/uygula
        apply_migrations(self.conn)

    def get_next_sequence(self, offer_date: date) -> tuple[int, str]:
        """Belirtilen tarih için atomik sıra numarası ve teklif numarasını üretir."""
        date_iso = offer_date.isoformat()
        date_prefix = offer_date.strftime("%Y%m%d")

        cursor = self.conn.execute(
            """
            INSERT INTO daily_sequences (offer_date, last_sequence)
            VALUES (?, 1)
            ON CONFLICT(offer_date) DO UPDATE SET last_sequence = last_sequence + 1
            RETURNING last_sequence;
            """,
            (date_iso,),
        )
        row = cursor.fetchone()
        if not row:
            raise RepositoryError(f"Teklif numarası üretilemedi: {offer_date}")

        seq = int(row[0])
        offer_num = f"{date_prefix}-{seq:03d}"
        return seq, offer_num

    def save(self, offer: Offer) -> Offer:
        """Teklifi ve bağlı satırları tek bir veritabanı transaction'ı içinde güvenle kaydeder."""
        now_iso = datetime.now(timezone.utc).isoformat()
        date_iso = offer.offer_date.isoformat()
        sel_cols_json = json.dumps([c.value for c in offer.selected_columns])

        try:
            with self.conn:
                if offer.id is None:
                    # Yeni Teklif: Atomik teklif numarası tahsis et
                    _, offer_number = self.get_next_sequence(offer.offer_date)

                    cursor = self.conn.execute(
                        """
                        INSERT INTO offers (
                            offer_number, offer_date, company_id, recipient_name,
                            currency_code, quantity_unit, vat_enabled, vat_rate,
                            discount_enabled, brand_logo_visible, page_orientation, document_language,
                            pdf_font_size,
                            template_packaging_info, template_storage_conditions,
                            template_product_info, template_product_info_items,
                            selected_columns, source_offer_id, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            offer_number,
                            date_iso,
                            offer.company_id,
                            offer.recipient_name,
                            offer.currency_code.value,
                            offer.quantity_unit.value,
                            1 if offer.vat_enabled else 0,
                            str(offer.vat_rate),
                            1 if offer.discount_enabled else 0,
                            1 if offer.brand_logo_visible else 0,
                            offer.page_orientation.value,
                            offer.document_language.value,
                            float(offer.pdf_font_size),
                            1 if offer.template_packaging_info else 0,
                            1 if offer.template_storage_conditions else 0,
                            1 if offer.template_product_info else 0,
                            json.dumps(offer.template_product_info_items),
                            sel_cols_json,
                            offer.source_offer_id,
                            now_iso,
                            now_iso,
                        ),
                    )
                    offer_id = cursor.lastrowid
                    if offer_id is None:
                        raise RepositoryError("Teklif kaydı oluşturulamadı.")
                    offer.id = offer_id
                    offer.offer_number = offer_number
                    offer.created_at = datetime.fromisoformat(now_iso)
                    offer.updated_at = datetime.fromisoformat(now_iso)
                else:
                    # Mevcut Teklif: Numarayı değiştirmeden güncelle
                    self.conn.execute(
                        """
                        UPDATE offers SET
                            offer_date = ?,
                            company_id = ?,
                            recipient_name = ?,
                            currency_code = ?,
                            quantity_unit = ?,
                            vat_enabled = ?,
                            vat_rate = ?,
                            discount_enabled = ?,
                            brand_logo_visible = ?,
                            page_orientation = ?,
                            document_language = ?,
                            pdf_font_size = ?,
                            template_packaging_info = ?,
                            template_storage_conditions = ?,
                            template_product_info = ?,
                            template_product_info_items = ?,
                            selected_columns = ?,
                            updated_at = ?
                        WHERE id = ?
                        """,
                        (
                            date_iso,
                            offer.company_id,
                            offer.recipient_name,
                            offer.currency_code.value,
                            offer.quantity_unit.value,
                            1 if offer.vat_enabled else 0,
                            str(offer.vat_rate),
                            1 if offer.discount_enabled else 0,
                            1 if offer.brand_logo_visible else 0,
                            offer.page_orientation.value,
                            offer.document_language.value,
                            float(offer.pdf_font_size),
                            1 if offer.template_packaging_info else 0,
                            1 if offer.template_storage_conditions else 0,
                            1 if offer.template_product_info else 0,
                            json.dumps(offer.template_product_info_items),
                            sel_cols_json,
                            now_iso,
                            offer.id,
                        ),
                    )
                    offer_id = offer.id
                    offer.updated_at = datetime.fromisoformat(now_iso)

                    # Eski satırları ve koşulları temizle
                    self.conn.execute("DELETE FROM offer_items WHERE offer_id = ?", (offer_id,))
                    self.conn.execute("DELETE FROM offer_sections WHERE offer_id = ?", (offer_id,))

                # Ürün satırlarını ekle
                for pos, item in enumerate(offer.items):
                    if item.is_empty():
                        continue
                    item_cursor = self.conn.execute(
                        """
                        INSERT INTO offer_items (
                            offer_id, position, product_code, description,
                            quantity_value, pallet_count, unit_price,
                            discount_type, discount_value
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            offer_id,
                            pos,
                            item.product_code,
                            item.description,
                            str(item.quantity),
                            str(item.pallet) if item.pallet is not None else None,
                            str(item.unit_price),
                            item.discount_type.value,
                            str(item.discount_value),
                        ),
                    )
                    item.id = item_cursor.lastrowid
                    item.offer_id = offer_id
                    item.position = pos

                # Koşul bölümlerini ekle
                for pos, sec in enumerate(offer.sections):
                    sec_cursor = self.conn.execute(
                        """
                        INSERT INTO offer_sections (
                            offer_id, section_key, enabled, text, rich_text, position
                        ) VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            offer_id,
                            sec.section_key.value,
                            1 if sec.enabled else 0,
                            sec.text,
                            1 if sec.rich_text else 0,
                            pos,
                        ),
                    )
                    sec.id = sec_cursor.lastrowid
                    sec.offer_id = offer_id
                    sec.position = pos

            return offer
        except Exception as exc:
            raise RepositoryError(f"Teklif veritabanına kaydedilirken hata oluştu: {exc}") from exc

    def get_by_id(self, offer_id: int) -> Offer | None:
        """ID'ye göre teklifi tüm ilişkili satırlarıyla getirir."""
        cursor = self.conn.execute("SELECT * FROM offers WHERE id = ?", (offer_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return self._row_to_offer(row)

    def get_by_number(self, offer_number: str) -> Offer | None:
        """Teklif numarasına göre teklifi tüm ilişkili satırlarıyla getirir."""
        cursor = self.conn.execute("SELECT * FROM offers WHERE offer_number = ?", (offer_number,))
        row = cursor.fetchone()
        if not row:
            return None
        return self._row_to_offer(row)

    def list_offers(
        self,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Offer]:
        """Teklifleri arama filtresi ve sayfalamayla listeler."""
        if search and search.strip():
            term = f"%{search.strip()}%"
            cursor = self.conn.execute(
                """
                SELECT * FROM offers
                WHERE offer_number LIKE ? OR recipient_name LIKE ? OR company_id LIKE ?
                ORDER BY offer_date DESC, id DESC
                LIMIT ? OFFSET ?
                """,
                (term, term, term, limit, offset),
            )
        else:
            cursor = self.conn.execute(
                """
                SELECT * FROM offers
                ORDER BY offer_date DESC, id DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            )

        rows = cursor.fetchall()
        return [self._row_to_offer(r) for r in rows]

    def delete(self, offer_id: int) -> bool:
        """Teklifi ve bağlı satırlarını siler."""
        with self.conn:
            cursor = self.conn.execute("DELETE FROM offers WHERE id = ?", (offer_id,))
            return cursor.rowcount > 0

    def _row_to_offer(self, row: sqlite3.Row) -> Offer:
        """SQLite satırını Offer nesnesine ve ilişkili çocuklarına dönüştürür."""
        offer_id = int(row["id"])

        # Ürün satırlarını çek
        item_cursor = self.conn.execute(
            "SELECT * FROM offer_items WHERE offer_id = ? ORDER BY position ASC, id ASC",
            (offer_id,),
        )
        items: list[OfferItem] = []
        for i_row in item_cursor.fetchall():
            pallet_raw = i_row["pallet_count"]
            pallet = Decimal(pallet_raw) if pallet_raw is not None else None
            items.append(
                OfferItem(
                    id=int(i_row["id"]),
                    offer_id=offer_id,
                    position=int(i_row["position"]),
                    product_code=i_row["product_code"],
                    description=i_row["description"],
                    quantity=Decimal(i_row["quantity_value"]),
                    pallet=pallet,
                    unit_price=Decimal(i_row["unit_price"]),
                    discount_type=DiscountType(i_row["discount_type"]),
                    discount_value=Decimal(i_row["discount_value"]),
                )
            )

        # Koşul bölümlerini çek
        sec_cursor = self.conn.execute(
            "SELECT * FROM offer_sections WHERE offer_id = ? ORDER BY position ASC, id ASC",
            (offer_id,),
        )
        sections: list[OfferSection] = []
        for s_row in sec_cursor.fetchall():
            sections.append(
                OfferSection(
                    id=int(s_row["id"]),
                    offer_id=offer_id,
                    section_key=SectionKey(s_row["section_key"]),
                    enabled=bool(s_row["enabled"]),
                    text=s_row["text"],
                    rich_text=bool(s_row["rich_text"]),
                    position=int(s_row["position"]),
                )
            )

        # Sütun listesi
        try:
            col_strings = json.loads(row["selected_columns"])
            selected_columns = [ColumnKey(c) for c in col_strings]
        except (json.JSONDecodeError, ValueError):
            selected_columns = []

        # Sayfa yönü
        page_orientation_raw = row["page_orientation"] if "page_orientation" in row.keys() else "auto"
        try:
            page_orientation = PageOrientation(page_orientation_raw)
        except ValueError:
            page_orientation = PageOrientation.AUTO

        # Belge dili
        document_language_raw = row["document_language"] if "document_language" in row.keys() else "tr"
        try:
            document_language = DocumentLanguage(document_language_raw)
        except ValueError:
            document_language = DocumentLanguage.TR

        template_packaging_info = bool(row["template_packaging_info"]) if "template_packaging_info" in row.keys() else False
        template_storage_conditions = bool(row["template_storage_conditions"]) if "template_storage_conditions" in row.keys() else False
        template_product_info = bool(row["template_product_info"]) if "template_product_info" in row.keys() else False
        template_product_info_items: list[str] = []
        if "template_product_info_items" in row.keys() and row["template_product_info_items"]:
            try:
                template_product_info_items = json.loads(row["template_product_info_items"])
            except Exception:
                template_product_info_items = []

        pdf_font_size = float(row["pdf_font_size"]) if "pdf_font_size" in row.keys() and row["pdf_font_size"] is not None else 8.0

        return Offer(
            id=offer_id,
            offer_number=row["offer_number"],
            offer_date=date.fromisoformat(row["offer_date"]),
            company_id=row["company_id"],
            recipient_name=row["recipient_name"],
            currency_code=CurrencyCode(row["currency_code"]),
            quantity_unit=QuantityUnit(row["quantity_unit"]),
            vat_enabled=bool(row["vat_enabled"]),
            vat_rate=Decimal(row["vat_rate"]),
            discount_enabled=bool(row["discount_enabled"]),
            brand_logo_visible=bool(row["brand_logo_visible"]),
            page_orientation=page_orientation,
            document_language=document_language,
            pdf_font_size=pdf_font_size,
            template_packaging_info=template_packaging_info,
            template_storage_conditions=template_storage_conditions,
            template_product_info=template_product_info,
            template_product_info_items=template_product_info_items,
            selected_columns=selected_columns,
            items=items,
            sections=sections,
            source_offer_id=row["source_offer_id"],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
            updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None,
        )
