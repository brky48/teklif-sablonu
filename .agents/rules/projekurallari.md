---
trigger: always_on
---

# Teklif Şablonu Projesi - Kesinleşmiş Ajan ve Mimari Kuralları

Bu projede ana kaynak kök dizindeki `Teklif_Sablonu_Projesi_Sartname_ve_AI_Promptlari_v1.2.md` belgesidir. Tüm geliştirme adımlarında aşağıdaki kurallara istisnasız uyulmalıdır:

## 1. Genel Çalışma Prensipleri
- Önce mevcut dosyaları, işletim sistemini ve proje yapısını incele; var olmayan dosyaların var olduğunu varsayma.
- İşe başlamadan önce ilgili aşamanın hedefini ve değiştireceğin dosyaları kısaca belirt.
- Tüm uygulamayı tek yanıtta yazmaya çalışma; yalnızca o anki Prompt aşamasını tamamla, test et ve sonuçlarını raporla.
- Şartnamede kesinleştirilmiş kararları (yuvarlama, varsayılan koşul metinleri, iskonto sınırı, satır doğrulaması vb.) yeniden tartışmaya açma; yalnızca teknik bir engel veya yeni bir çelişki varsa odaklı soru sor[cite: 1, 2].
- Kod modüler, tip açıklamalı (type-hinted) ve yalnızca gerekli yerlerde yorum içerecek şekilde yazılmalıdır[cite: 1, 2].
- Girdi kontrolünü yalnızca UI (PySide6) üzerinde bırakma; mutlaka `domain` katmanında da doğrula[cite: 1, 2].
- Her aşamada ilgili `pytest` testlerini çalıştır; başarısız test varsa başarı iddiasında bulunma, hatayı gider veya net biçimde bildir[cite: 1, 2].
- Bir aşamada dosya yapısını gereksiz yere baştan yazma ve mevcut kullanıcı kodunu izinsiz silme[cite: 1, 2].
- Aşama sonunda: değişen dosyaları, çalıştırılan komutları, test sonuçlarını, kalan işleri ve belirsiz kararları listele[cite: 1, 2].

## 2. Mimari ve Katman Sınırları
- Teknoloji yığını: Python, PySide6 (UI), SQLite (yerel veritabanı), openpyxl (Excel), Türkçe font gömme destekli PDF kütüphanesi, pytest ve PyInstaller[cite: 1, 2].
- Katman ayrımı (`ui`, `domain`, `services`, `storage`, `templates`, `config`, `assets`, `tests`) kesinlikle korunmalıdır[cite: 1, 2].
- UI katmanı, hesaplama modülü ve PDF/Excel servisleri doğrudan SQLite SQL sorgularına bağlanmamalı; tüm veri işlemleri `repository` katmanı üzerinden yapılmalıdır[cite: 1, 2].
- SQLite veritabanı uygulama kurulum dizinine değil, işletim sisteminin kullanıcıya ait yazılabilir uygulama veri dizinine kaydedilmelidir[cite: 1, 2].
- Şirket bilgileri (`Endemiks Tarım Ticaret A.Ş.` ve `Endemiks Gıda LTD. ŞTİ.`), VKN/adresler ve logo yolları kodun içine sabit olarak gömülmemeli, `config` ve `assets` üzerinden yönetilmelidir[cite: 1, 2]. Eksik şirket bilgileri uydurulmamalı, placeholder/TODO olarak tutulmalıdır[cite: 1, 2].
- Geliştirme macOS üzerinde yapılabilir ancak nihai Windows `.exe` paketinin macOS'ta doğrudan tamamlanabildiğini varsayma; Windows derleme/test ortamı kullanılmalıdır[cite: 1, 2].

## 3. Kesinleşmiş İş ve Hesaplama Kuralları
- Tüm parasal hesaplamalarda Python `Decimal` ve merkezi tek bir yuvarlama fonksiyonunda `ROUND_HALF_UP` (2 ondalık basamak) kullanılmalıdır[cite: 1, 2].
- Genel toplam özeti (Ara Toplam, etkinse Toplam İskonto ve İskonto Sonrası Ara Toplam, etkinse Toplam KDV ve KDV Dâhil Genel Toplam), kullanıcıya gösterilen iki ondalık basamağa yuvarlanmış satır tutarları üzerinden hesaplanmalıdır[cite: 1, 2].
- Teklif genelinde tek para birimi (`TRY`, `USD` veya `EUR`), tek miktar birimi (`Adet` veya `Litre`) ve KDV etkinse tek bir KDV oranı seçilir[cite: 1, 2].
- İskonto ürün satırı bazında bağımsızdır: `Oran` (%0–100 aralığı, en fazla 2 ondalık) veya sabit `Miktar` (tam kısımda en az 10 basamak, en fazla 2 ondalık, satır toplamını aşamaz)[cite: 1, 2].
- Tamamen boş ürün satırları yok sayılır; kısmen doldurulmuş satırlarda `Ürün Açıklaması`, `Miktar` ve `Birim Fiyat` zorunludur ve en az bir geçerli satır olmadan kayıt/çıktı üretilemez[cite: 1, 2].
- Teklif numarası seçilen teklif tarihine göre `YYYYMMDD-NNN` formatında, teklif ilk kez kaydedilirken `transaction` içinde atomik olarak üretilir; yeniden dışa aktarımda değişmez, kopyalama/revizyonda ise yeni numarayla ayrı kayıt oluşturulur[cite: 1, 2].
- PDF ve Excel çıktılarında Bölüm 6.2'deki 11 sütunluk sabit sıra korunur; seçilmeyen veya tüm satırlarda tamamen boş olan sütunlar gizlenir[cite: 1, 2].
- Excel çıktısında tutarlar metin olarak değil gerçek sayısal hücre ve taşınabilir Excel formülleriyle yazılmalıdır[cite: 1, 2].