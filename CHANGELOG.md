# Değişiklik Günlüğü / Changelog

Bu belgede Teklif Şablonu uygulamasına ait sürüm güncellemeleri ve yapılan değişiklikler listelenmektedir.  
This document lists the release notes and detailed changes for the Teklif Şablonu application.

---

## [v1.4.0] - 2026-10-29

### 🇹🇷 Türkçe (Turkish)

#### 🚀 Yeni Özellikler (New Features)
- **Özel / Ek Sayfalar (Boş Sayfa Ekle):**
  - Formun en sonuna ("Hazır Şablonlar" sonrasına) kullanıcıların dilediği sayıda resmi sertifika, analiz raporu veya akreditasyon belgesi ekleyebileceği **Özel / Ek Sayfalar (Boş Sayfa Ekle)** bölümü eklendi.
  - Arayüzden dinamik olarak sayfa eklenebilir, sıralaması değiştirilebilir (Yukarı ▲ / Aşağı ▼) ve silinebilir.
  - Her sayfa için bağımsız Sayfa Başlığı, sistem font standartlarında font boyutu seçimi (6.5 pt - 9.0 pt), önizlemeli görsel yükleme alanı ve zengin metin düzenleyicisi (Kalın, İtalik, Altı Çizili, Sola/Ortaya/Sağa Hizalama, Madde İmleri ve Numaralı Liste) sunulur.
  - PDF çıktısında her ek sayfa bağımsız bir A4 sayfası olarak `PageBreak()` ile ayrılır; üst mini-başlık barı (`Juresh / Endemiks ... Sayfa X/Y`), ortalı başlık, en-boy oranı korunarak ölçeklenen tam sayfa görsel ve iki aşamalı alt bilgi (iletişim footer'ı ve `Sayfa X / Y` numaralandırması) eksiksiz korunur.
  - Excel çıktısına da 8.1 Özel Sayfalar başlığı altında görsel ve açıklamalar dahil edilmiştir.
- **Hasat ve Olgunlaşma Takvimi Şablonu (Harvest and Maturation Calendar):**
  - PDF şablonunda "Muhafaza Koşulları" ile "Ürün Bilgileri" arasına ReportLab `Table` yapısıyla dinamik bir Gantt şeması takvimi eklendi.
  - 12 aylık periyot (Eylül - Ağustos) ve 3'er aylık mevsim blokları (`SPAN` ile Sonbahar, Kış, İlkbahar, Yaz) yapılandırıldı.
  - Meyve ikonları (Nar, Limon Enterdonat, Limon Lamas, Greyfurt, Portakal Washington, Portakal Valencia) tabloya dahil edildi.
  - Hasat dönemleri açık kurumsal pastel renkle arka plan dolgusu (Gantt shading) yapılarak ortalı metinlerle gösterildi.
  - Portakal (Valencia) dönemi Nisan-Temmuz aylarını kapsayacak şekilde düzenlendi; İngilizce açıklamada "Enterdonato" yazımı "Interdonato" olarak güncellendi.
  - Dil seçimine göre dinamik dipnot metni eklendi.
- **Birim Fiyat Teklif Modu (Toplam Tutar Göster/Gizle):**
  - Sütun seçim paneline "Toplam Tutar" CheckBox kontrolü açılarak tekil ürün fiyat listesi / birim fiyat tekliflerinde toplam tutar sütunu ve Genel Toplam özet tablosunun PDF çıktısında gizlenebilmesi sağlandı.
- **Teklif İletişim Bilgileri (Quotation Contact Information):**
  - "Ticari Koşullar ve Ek Notlar" panelinin en üstünde CheckBox ile kontrol edilen, 5.000 karakter sınırına ve zengin metin desteğine sahip bağımsız iletişim kutusu konuşlandırıldı.

#### 🗄️ Veritabanı ve Depolama (Database & Storage)
- **SQLite Migrasyonları (Migration 7 ve 8):**
  - Migration 7: `offers` tablosuna `template_harvest_calendar` sütunu eklendi.
  - Migration 8: Sınırsız ek sayfa desteği için ilişkili `offer_custom_pages` tablosu (`ON DELETE CASCADE`) oluşturuldu.
  - Teklif kaydedildiğinde, güncellendiğinde veya arşivden yüklendiğinde ek sayfaların sırası, başlığı, HTML içeriği, görsel yolu ve font boyutu kalıcı olarak saklanır.

#### 🔄 CI/CD ve Dağıtım Otomasyonu (CI/CD Automation)
- **PC ve Mac Eşzamanlı Derleme (Windows .exe ve macOS .app):**
  - GitHub Actions iş akışları (`build_windows_exe.yml` ve `build_macos_app.yml`) sürüm etiketleri (`v*`) için tetiklenecek şekilde yapılandırıldı.
  - `softprops/action-gh-release@v2` entegrasyonu ile etiket push edildiğinde Windows `TeklifSablonu.exe` ve macOS `TeklifSablonu-macOS.zip` paketlerinin otomatik olarak GitHub Release varlığı olarak yayınlanması sağlandı.

#### 🔧 Arayüz ve Sistem İyileştirmeleri (UI & System)
- **Merkezi Sürüm Güncellemesi:**
  - Uygulama sürümü `1.4.0` olarak güncellendi; `__init__.py`, `pyproject.toml`, `version_info.txt`, `teklif_sablonu.spec` ve ana pencere durum çubuğunda eşitlendi.
- **Test Kapsamı:**
  - Ek sayfalar, veritabanı kalıcılığı, PDF oluşturma ve arayüz etkileşimleri için yeni testler eklenerek toplam test sayısı **113**'e yükseltildi (`113 passed`).

---

### 🇬🇧 English

#### 🚀 New Features
- **Custom Appendix Pages ("Add Blank Page"):**
  - Added an "Özel / Ek Sayfalar (Boş Sayfa Ekle)" section at the very bottom of the form (after Ready Templates) supporting an unlimited number of custom appendix pages (official certificates, taste accreditation, lab test reports).
  - UI offers dynamic page addition, deletion, and order management (Move Up ▲ / Move Down ▼).
  - Each card provides a page title input, typography point size selector (6.5 pt to 9.0 pt matching system presets), image picker with live thumbnail preview, and a full-featured Rich Text editor (Bold, Italic, Underline, Alignments, Bullet & Numbered lists).
  - In PDF export, each appendix page is cleanly rendered on its own A4 sheet via `PageBreak()`, complete with a mini-header bar (`Juresh / Endemiks ... Page X/Y`), centered bold title, aspect-ratio-preserved image rendering (Pillow), Rich Text descriptions, and standard two-pass numbered footer.
  - Rendered in Excel Section 8.1 with titles, embedded images, and text notes.
- **Harvest and Maturation Calendar Template:**
  - Added a dynamic Gantt chart table positioned between "Storage Conditions" and "Product Information" rendered natively via ReportLab `Table`.
  - Configured with 12 monthly columns (Sep-Aug) and seasonal 3-month header blocks (`SPAN` grouping for Autumn, Winter, Spring, Summer).
  - Embedded miniature product icons (Pomegranate, Interdonato Lemon, Lamas Lemon, Grapefruit, Washington Orange, Valencia Orange).
  - Has pastel background shading (Gantt shading) with centered period text.
  - Adjusted Valencia Orange harvest window to cover April–July; corrected English naming from "Enterdonato" to "Interdonato".
  - Bilingual footnote on climatic variability included.
- **Unit Price Quotation Mode (Hide Grand Total):**
  - Unlocked the "Toplam Tutar" (Total Amount) column in the Column Selector, allowing users to toggle it off for unit-price-only rate sheets, which automatically omits the column and the entire Grand Total summary section in PDF and Excel.
- **Quotation Contact Information:**
  - Dedicated full-width Rich Text contact info box toggled via CheckBox at the top of the Commercial Terms panel.

#### 🗄️ Database & Storage
- **SQLite Migrations (Migrations 7 & 8):**
  - Migration 7: Added `template_harvest_calendar` flag to `offers`.
  - Migration 8: Created `offer_custom_pages` table with cascading deletes (`ON DELETE CASCADE`) to persist arbitrary appendix pages.
  - Preserved page positions, titles, HTML content, image paths, and font sizes across saves, updates, and archive retrieval.

#### 🔄 CI/CD & Release Automation
- **Dual Platform Automated Builds (PC & Mac):**
  - Configured GitHub Actions workflows (`build_windows_exe.yml` and `build_macos_app.yml`) to trigger on version tags (`v*`).
  - Integrated `softprops/action-gh-release@v2` to automatically publish Windows `TeklifSablonu.exe` and macOS `TeklifSablonu-macOS.zip` binaries on GitHub Releases.

#### 🔧 UI & System Improvements
- **Centralized Version Synchronization:**
  - Synchronized version `1.4.0` across `__init__.py`, `pyproject.toml`, `version_info.txt`, `teklif_sablonu.spec`, and the status bar copyright text.
- **Test Suite Expansion:**
  - Expanded the test suite with new tests covering custom appendix pages, database persistence, and PDF layout rendering, reaching **113 passing tests** (`113 passed`).

---

## [v1.3.4] - 2026-10-28

### 🇹🇷 Türkçe (Turkish)

#### 🚀 Yeni Özellikler (Features)
- **Teklif İletişim Bilgileri (Quotation Contact Information) Alanı:**
  - "Ticari Koşullar ve Ek Notlar" panelinin en üstünde tam genişlikte yer alan ve CheckBox ile açılıp kapatılabilen **Teklif İletişim Bilgileri** alanı eklendi.
  - Alan 5.000 görünür karakter sınırına sahiptir ve kalın, italik, altı çizili, madde imleri ve numaralı liste gibi zengin metin (Rich Text) biçimlendirmelerini destekler.
  - PDF çıktısında Genel Toplam ile Ticari Koşullar / Ek Notlar arasında bağımsız tam genişlikli çerçeveli bir kutu olarak konumlandırıldı; Genel Toplam ile arasındaki üst boşluk ve Ticari Koşullar / Ek Notlar ile arasındaki alt boşluk (4 pt) şartnameye uygun olarak korunmuştur.
  - Excel çıktısında Genel Toplam satırlarının hemen altında, Ticari Koşullar başlığından önce zengin metinden arındırılmış temiz metin olarak yerleştirildi.
  - Dil desteği: Türkçe `Teklif İletişim Bilgileri`, İngilizce `Quotation Contact Information` olarak tanımlandı.
- **Sürüm Güncellemesi:**
  - Sürüm numarası v1.3.4 olarak güncellendi ve tüm yapılandırma dosyalarında (`__init__.py`, `pyproject.toml`, `teklif_sablonu.spec`, `version_info.txt`) eşitlendi.

---

### 🇬🇧 English

#### 🚀 New Features
- **Quotation Contact Information Section:**
  - Added a new **Quotation Contact Information** section positioned at the very top of the "Commercial Terms and Additional Notes" panel, toggled via a dedicated CheckBox.
  - Features a 5,000 visible-character limit with full Rich Text formatting support (Bold, Italic, Underline, Bullet Lists, and Numbered Lists).
  - Positioned in the PDF output immediately between Grand Total and Commercial Terms / Additional Notes in its own bordered full-width box, preserving the top gap from Grand Total and the 4 pt bottom spacing towards subsequent condition boxes.
  - Rendered in Excel exports between Grand Total and the Terms & Conditions header with formatted plain text wrapping.
  - Full bilingual support: Turkish `Teklif İletişim Bilgileri` and English `Quotation Contact Information`.
- **Version Bump:**
  - Version updated to v1.3.4 across `__init__.py`, `pyproject.toml`, `teklif_sablonu.spec`, and `version_info.txt`.

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
