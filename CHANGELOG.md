# Değişiklik Günlüğü / Changelog

Bu belgede Teklif Şablonu uygulamasına ait sürüm güncellemeleri ve yapılan değişiklikler listelenmektedir.  
This document lists the release notes and detailed changes for the Teklif Şablonu application.

---

## [v1.3.3] - 2026-10-28

### 🇹🇷 Türkçe (Turkish)

#### 🚀 Yeni Özellikler (Features)
- **Dinamik PDF Font Boyutu Seçimi:**
  - Üst Bilgi paneline (Sayfa Yönü / Belge Dili yanına) **PDF Yazı Boyutu** açılır seçim kutusu eklendi.
  - Desteklenen punto seçenekleri:
    - `8.0 pt (Varsayılan - Standart)`
    - `7.5 pt (Küçük)`
    - `7.0 pt (Çok Küçük / Kompakt)`
    - `6.5 pt (Ekstra Kompakt)`
    - `8.5 pt (Büyük)`
    - `9.0 pt (Çok Büyük)`
  - Kullanıcı font boyutunu küçülttüğünde:
    - Tablo hücreleri, başlıklar, ticari koşullar ve toplam metinleri seçilen puntoya göre (`scale = base_font_size / 8.0`) orantılı olarak küçülür.
    - Tablo dikey hücre dolguları (`padding`), bölümler arası boşluklar (`Spacer`) ve imza kutusu yüksekliği de orantılı olarak daraltılır.
    - Böylece içerik yoğun tekliflerde imza kutularının bir sonraki sayfaya taşması/kayması tamamen engellenir ve teklifin tek sayfaya sığması sağlanır.
- **Veritabanı Kalıcılığı:**
  - SQLite şemasına 6. migrasyon (`pdf_font_size REAL NOT NULL DEFAULT 8.0`) eklendi.
  - Font boyutu tercihi teklifle birlikte kaydedilir, arşivden açıldığında ve kopyalandığında korunur.
- **macOS GitHub Actions Derleme İş Akışı:**
  - `.github/workflows/build_macos_app.yml` iş akışı eklendi. Artık GitHub deposuna her push yapıldığında hem Windows (`.exe`) hem de macOS (`.app` / `.zip`) paketleri otomatik olarak derlenip artifact olarak sunulur.

#### 📝 İçerik ve Şablon Güncellemeleri
- **Ürün Bilgileri (Tüketime Hazır Limonata):**
  - Boş kalan alan Türkçe ve İngilizce detaylı ürün açıklaması, içindekiler ve kullanım şekliyle dolduruldu.
- **Ürün Bilgileri (Greyfurt Suyu):**
  - Boş kalan alan Türkçe ve İngilizce %100 saf meyve suyu açıklamasıyla dolduruldu.
- **Limon Suyu Açıklaması Başlık Düzeltmesi:**
  - Türkçe açıklamada yer alan `Pulpalı Limon Suyu (Doğal ve Geleneksel):` başlığı `Pulplu Limon Suyu (Doğal ve Geleneksel):` olarak güncellendi.

#### 🔧 Arayüz ve Sistem İyileştirmeleri
- **Durum Çubuğu Sürüm Göstergesi:**
  - Durum çubuğunun sağ altındaki telif alanına sürüm bilgisi eklendi (`Geliştirici: Berkay Korkut | © 2026 | v1.3.3`).
- **Sürüm Senkronizasyonu:**
  - `__init__.py`, `app.py`, `pyproject.toml`, `version_info.txt` ve `teklif_sablonu.spec` dosyalarında sürüm `1.3.3` olarak eşitlendi.
- **Test Kapsamı:**
  - Font boyutu ölçeklemesi, ürün bilgileri içerikleri, UI kontrolleri ve veritabanı kalıcılığı için yeni testler eklendi; toplam test sayısı 105'e ulaştı (`105 passed`).

---

### 🇬🇧 English

#### 🚀 New Features
- **Dynamic PDF Font Size Control:**
  - Added a "PDF Font Size" dropdown in the Header panel (alongside Page Orientation and Document Language).
  - Supported point size presets:
    - `8.0 pt (Default - Standard)`
    - `7.5 pt (Small)`
    - `7.0 pt (Extra Small / Compact)`
    - `6.5 pt (Ultra Compact)`
    - `8.5 pt (Large)`
    - `9.0 pt (Extra Large)`
  - When the font size is reduced:
    - All paragraph styles (table cells, headers, terms, totals) scale proportionally based on `scale = base_font_size / 8.0`.
    - Table vertical cell padding, inter-section spacers, and signature box dimensions are tightened proportionally.
    - Prevents signature blocks from overflowing to an extra page on dense offers, allowing them to fit cleanly on a single page.
- **Database Persistence:**
  - Added Migration 6 (`pdf_font_size REAL NOT NULL DEFAULT 8.0`) to the SQLite schema.
  - User font size choices are persisted with the offer record, retained across saves, and restored from the archive.
- **macOS CI/CD Workflow on GitHub Actions:**
  - Added `.github/workflows/build_macos_app.yml`. Every push to GitHub now automatically compiles both Windows (`.exe`) and macOS (`.app` / `.zip`) distribution packages.

#### 📝 Content & Template Updates
- **Product Details (Ready-to-Drink Lemonade):**
  - Filled in comprehensive Turkish and English descriptions, ingredients list, and consumption directions.
- **Product Details (Grapefruit Juice):**
  - Filled in 100% pure grapefruit juice specifications in both Turkish and English.
- **Lemon Juice Header Correction:**
  - Corrected the Turkish description subtitle from `Pulpalı Limon Suyu (Doğal ve Geleneksel):` to `Pulplu Limon Suyu (Doğal ve Geleneksel):`.

#### 🔧 UI & System Improvements
- **Status Bar Version Display:**
  - Appended version info to the permanent status bar label (`Geliştirici: Berkay Korkut | © 2026 | v1.3.3`).
- **Centralized Version Synchronization:**
  - Synchronized version `1.3.3` across `__init__.py`, `app.py`, `pyproject.toml`, `version_info.txt`, and `teklif_sablonu.spec`.
- **Test Suite Expansion:**
  - Added tests for proportional font scaling, product details content verification, UI interactions, and database migrations, bringing the test suite to 105 passing tests (`105 passed`).
