# Teklif Şablonu

Endemiks şirketleri (**Endemiks Tarım Ticaret A.Ş.** ve **Endemiks Gıda LTD. ŞTİ.**) için geliştirilmiş modern, modüler, güvenilir ve çift dilde (Türkçe arayüz ve çıktılar) çalışan profesyonel masaüstü teklif hazırlama uygulaması.

---

## 1. Mimari ve Katmanlı Tasarım

Proje; iş kurallarını (domain), veri depolamayı (storage), dışa aktarım servislerini (services) ve kullanıcı arayüzünü (PySide6) birbirinden kesin hatlarla ayıran **temiz ve katmanlı bir mimariye (Clean Architecture)** sahiptir:

```text
teklif_sablonu/
├── src/
│   └── teklif_sablonu/
│       ├── config/        # Şirket bilgileri, varsayılan ticari koşullar ve OS veri yolu ayarları
│       ├── domain/        # Teklif modelleri, girdi doğrulayıcılar ve hesaplama motoru (Decimal)
│       ├── services/      # Teklif CRUD (OfferService), PDF (ReportLab) ve Excel (openpyxl) servisleri
│       ├── storage/       # SQLite veritabanı bağlantısı, şema geçişleri ve Repository katmanı
│       ├── ui/            # PySide6 masaüstü arayüz bileşenleri, tablolar ve anlık hesaplama kontrolleri
│       ├── templates/     # PDF stilleri, sayfa düzeni kuralları ve font kayıt mekanizmaları
│       ├── assets/        # Şirket ve marka logoları, Türkçe TrueType fontlar (DejaVuSans)
│       ├── app.py         # QApplication fabrikası ve küresel olay döngüsü yapılandırması
│       └── main.py        # CLI ve masaüstü uygulama giriş noktası
├── tests/                 # 82 adet kapsamlı pytest birim, entegrasyon ve kabul testi
├── pyproject.toml         # Proje yapılandırması, Python 3.11+ bağımlılıkları ve pytest ayarları
├── teklif_sablonu.spec    # PyInstaller Windows .exe paketleme yapılandırması
├── build_windows.bat      # Windows tek tıkla derleme betiği (CMD)
├── build_windows.ps1      # Windows tek tıkla derleme betiği (PowerShell)
├── .github/workflows/     # GitHub Actions Windows CI iş akışı (windows-latest)
└── README.md
```

### Kesinleşmiş Mimari İlkeler:
1. **Domain Bağımsızlığı:** UI veya veritabanı hiçbir hesaplama mantığı içermez. Tüm parasal hesaplamalar Python `Decimal` modülü ve merkezi `ROUND_HALF_UP` yuvarlama algoritmasıyla (2 ondalık basamak) `domain/calculator.py` içinde icra edilir.
2. **Repository Soyutlaması:** UI katmanı veya servisler doğrudan SQLite SQL sorgusu çalıştırmaz. Tüm veri erişimi `SqliteOfferRepository` üzerinden soyutlanmıştır.
3. **Kullanıcı Veri Güvenliği:** SQLite veritabanı (`teklif_sablonu.db`) asla uygulama kurulum klasörüne yazılmaz; işletim sisteminin kullanıcı veri dizininde (`platformdirs`) saklanır. Uygulama güncellense veya silinse bile teklif arşivi korunur.
4. **Harici Yapılandırma:** Şirket bilgileri (`companies.json`), varsayılan koşul metinleri (`default_texts.json`) ve görsel varlıklar (`assets/`) kod içine gömülü değildir, yapılandırma dosyalarından dinamik yüklenir. Eksik şirket bilgileri için uydurma veri kullanılmamış; açıkça `TODO` placeholder olarak bırakılmıştır.

---

## 2. Kurulum ve Geliştirme Ortamı

### Sistem Gereksinimleri
- **İşletim Sistemi:** macOS (geliştirme), Windows 10/11 x64 (hedef dağıtım) veya Linux
- **Python:** Python >= 3.11 (Python 3.12 önerilir)

### Adım Adım Kurulum

```bash
# 1. Proje dizinine gidin
cd teklif_sablonu

# 2. Sanal ortamı oluşturun ve etkinleştirin
python3 -m venv .venv
source .venv/bin/activate       # macOS / Linux
# Windows için: .venv\Scripts\activate

# 3. Bağımlılıkları geliştirme modunda kurun
pip install --upgrade pip
pip install -e ".[dev]"
```

---

## 3. Uygulamayı Çalıştırma

Geliştirme ortamında arayüzü başlatmak için:

```bash
# Yöntem 1: Proje script komutu ile
teklif-sablonu

# Yöntem 2: Python modülü olarak
python -m teklif_sablonu.main
```

---

## 4. Testleri Çalıştırma ve Kapsam Raporu

Projede 82 adet otomatik birim, entegrasyon, UI ve kabul testi bulunmaktadır.

```bash
# Standart test koşumu
pytest -v

# Kod kapsamı (coverage) raporu ile birlikte çalıştırma
pytest --cov=teklif_sablonu --cov-report=term-missing
```

*Mevcut Test Durumu: 82 passed in 1.1s (Kod Kapsamı: %94).*

---

## 5. Çıktı Üretim Kuralları (PDF ve Excel)

Her iki dışa aktarım servisi aynı kaydedilmiş `Offer` modelini temel alır; veriyi bağımsız veya farklı kurallarla yeniden hesaplamaz:

1. **Sabit 11 Sütun Sıralaması:**  
   `Ürün Kodu` | `Ürün Açıklaması` | `Miktar` | `Palet` | `Birim Fiyat` | `İskonto Türü` | `İskonto Değeri` | `KDV %` | `Toplam Tutar` | `İskontolu Tutar` | `KDV Dahil`
2. **Kısmen Dolu Sütun Politikası:**  
   Seçilmeyen veya tüm satırlarda tamamen boş kalan sütunlar PDF ve Excel'den otomatik elenir. En az bir satırda değer varsa sütun korunur.
3. **Sayfa Yönü Otomasyonu:**  
   - 7 veya daha az sütun: **Dikey A4 (Portrait)**
   - 8 veya daha fazla sütun (KDV, İskonto, Palet vb. aktif): **Yatay A4 (Landscape)**
4. **Taşınabilir Excel Formülleri (`openpyxl`):**  
   Excel çıktısındaki tutarlar metin değil, gerçek sayısal hücrelerdir. Satır toplamları (`=C10*D10`), iskonto düşümleri, KDV ve alt toplam kartı (`=SUM(...)`) gerçek Excel formülleriyle oluşturulur; kullanıcı miktarı veya fiyatı değiştirdiğinde sonuçlar otomatik güncellenir.
5. **PDF Baskı Kalitesi (`ReportLab`):**  
   Türkçe özel karakterler için TrueType `DejaVuSans` fontu PDF içine gömülüdür. Çok sayfalı tablolarda başlık satırı her sayfada otomatik tekrarlanır ve sayfa numaraları (Sayfa X / Y) tuvale yazılır.
6. **Dosya Çakışma Güvenliği:**  
   Kullanıcının Masaüstünde aynı isimde bir `<TeklifNo>.pdf` veya `<TeklifNo>.xlsx` varsa sistem sessizce üzerine yazmaz; kullanıcıya Üzerine Yaz / Farklı Kaydet / İptal seçenekleri sunar.

---

## 6. Veri Dosyalarının Konumları ve Yedek Alma

Uygulamanın oluşturduğu tüm veriler işletim sistemi standartlarına uygun olarak saklanır:

| Veri Türü | macOS / Linux | Windows |
| :--- | :--- | :--- |
| **SQLite Veritabanı** | `~/Library/Application Support/TeklifSablonu/teklif_sablonu.db` | `%LOCALAPPDATA%\TeklifSablonu\teklif_sablonu.db` |
| **Varsayılan Çıktılar** | `~/Desktop/<TeklifNo>.pdf` ve `.xlsx` | `C:\Users\<Kullanıcı>\Desktop\<TeklifNo>.pdf` ve `.xlsx` |

### Veritabanı Yedeği Alma
Tüm teklif geçmişini, günlük sayaçları ve arşiv verilerini yedeklemek için tek yapmanız gereken yukarıdaki dizinde yer alan `teklif_sablonu.db` dosyasını harici bir diske veya bulut klasörünüze kopyalamaktır. Yeni bir bilgisayara geçildiğinde dosya aynı konuma bırakılarak tüm geçmiş anında geri yüklenir.

---

## 7. Windows Dağıtımı (`.exe` Paketleme)

Şartname gereğince, macOS üzerinde doğrudan Windows PE formatında `.exe` üretilemeyeceği için Windows paketleme işlemleri Windows ortamında veya GitHub Actions CI üzerinde yürütülür:

### A. Windows Bilgisayarında Tek Tıkla Derleme
Windows ortamında kaynak kod indirildikten sonra:
- `build_windows.bat` dosyasına çift tıklayın veya
- PowerShell üzerinden `.\build_windows.ps1` komutunu çalıştırın.
Derleme sonucunda `dist\TeklifSablonu.exe` tek dosya olarak üretilir.

### B. GitHub Actions ile Bulutta Otomatik Derleme
Depo GitHub'a gönderildiğinde (push/pull request), `.github/workflows/build_windows_exe.yml` iş akışı otomatik olarak `windows-latest` sanal makinesinde tüm testleri koşar ve `TeklifSablonu.exe` dosyasını GitHub Artifacts olarak sunar.

---

## 8. Bilinen Sınırlamalar ve Riskler

1. **Yerel Tek Kullanıcı Tasarımı:**  
   Mevcut sürüm tekil masaüstü kullanımına yöneliktir. SQLite veritabanı her kullanıcının yerel bilgisayarında saklanır.
2. **Çok Kullanıcılı Ortamda Numara Çakışması Riski:**  
   İki farklı kullanıcı aynı gün bağımsız bilgisayarlarda teklif oluşturursa, her ikisinin de yerel sayacı `20261020-001` üretecektir. Bu durum yerel sistemin doğasından kaynaklanmaktadır.
3. **Excel Manuel Düzenlemelerinin PDF'e Yansımaması:**  
   Kullanıcı Excel çıktısını açıp hücreleri manuel olarak değiştirdiğinde bu değişiklikler PDF dosyasına otomatik yansımaz; PDF ve Excel teklif ilk kaydedildiğinde ayrı ayrı oluşturulur.

---

## 9. Gelecekte Merkezi Veritabanına (PostgreSQL / REST API) Geçiş Rehberi

Uygulama, gelecekte merkezi bir sunucuya veya bulut veritabanına geçilmesini kolaylaştırmak için **Repository Pattern** ile tasarlanmıştır:

1. `src/teklif_sablonu/storage/repository.py` içerisindeki `OfferRepository` protokolü standart CRUD metotlarını (`save`, `get_by_id`, `list_all`, `delete`, `get_next_sequence`) tanımlar.
2. Merkezi PostgreSQL veya REST API servisine geçilmek istendiğinde; arayüze (UI), hesaplama motoruna (calculator) veya PDF/Excel servislerine dokunulmadan yalnızca yeni bir `PostgresOfferRepository` veya `ApiOfferRepository` sınıfı yazılıp `OfferService`'e enjekte edilmesi yeterlidir.
3. Böylece çok kullanıcılı ortamlarda günlük sıra sayacı sunucu tarafında merkezi transaction ile yönetilerek numara çakışması riski tamamen ortadan kaldırılabilir.
