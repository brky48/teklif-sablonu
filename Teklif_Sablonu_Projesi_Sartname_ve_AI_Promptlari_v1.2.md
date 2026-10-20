# Teklif Şablonu Projesi
## Gereksinim ve Teknik Şartname + Aşamalı AI Geliştirme Prompt'ları

**Sürüm:** 1.2 – Hesaplama ve doğrulama kararları kesinleştirilmiş şartname  
**Tarih:** 20.10.2026  
**Hedef platform:** Windows masaüstü uygulaması (`.exe`)  
**Geliştirme ortamı:** macOS; nihai Windows paketinin Windows ortamında oluşturulması ve test edilmesi  
**Belge durumu:** v1.2. Kullanıcı tarafından onaylanan yuvarlama, varsayılan koşul metinleri, iskonto sınırı ve çıktı öncesi doğrulama kuralları işlenmiştir. Bölüm 16 yalnızca uygulama varsayımlarını ve henüz teslim edilmemiş firma/görsel girdilerini listeler.

---

## Bu belge nasıl kullanılmalı?

Bu belge, uygulamanın kapsamını tanımlayan ana kaynak olmalıdır. Gemini, Codex, Claude Code veya başka bir kodlama ajanına verildiğinde ajan bu belgeyi okuyup uygulamayı tek seferde üretmeye çalışmamalı; Bölüm 12'deki geliştirme prompt'ları sırasıyla kullanılmalıdır.

Ajan, burada kesinleştirilmiş kararları değiştirmemelidir. Bölüm 16'daki uygulama varsayımlarını görünür tutmalı; bu şartnamede kesinleştirilmiş bir kuralı yeniden tartışmaya açmamalıdır. Yalnızca teknik bir engel veya yeni bir çelişki varsa kullanıcıya odaklı soru sormalıdır.

## 0. Onaylanmış temel kararlar

Aşağıdaki kararlar kullanıcı tarafından netleştirilmiştir ve geliştirme sırasında kesin gereksinim kabul edilmelidir:

- Uygulama Windows bilgisayarlarda çalışan masaüstü uygulaması olacak; geliştirme macOS üzerinde yapılabilecek, ancak nihai `.exe` Windows ortamında oluşturulup test edilecek.
- İlk sürüm her bilgisayarda yerel SQLite veri tabanı kullanacak. Merkezi veri paylaşımı ilk sürümde yoktur; gelecekte eklenebilmesi için veri erişim katmanı ayrıştırılacak.
- Teklif genelinde tek para birimi seçilecek: TRY, USD veya EUR.
- Her teklif için miktar birimi bir kez seçilecek: **Adet** veya **Litre**. Seçilen birim bütün ürün satırları için geçerli olacak; tablo başlığı `Miktar (Adet)` veya `Miktar (Litre)` olarak gösterilecek.
- Her teklif için tek bir KDV oranı girilecek ve bu oran bütün ürün satırlarına uygulanacak. KDV tablosu gösteriliyorsa aynı oran satırlarda gösterilebilir.
- İskonto ürün satırı bazında uygulanacak; her satırda iskonto türü (Oran/Miktar) ve değeri bağımsız olabilir.
- Sabit tutar iskontosu para birimi cinsinden girilecek, en fazla iki ondalık basamak içerecek ve tam kısmında en az 10 basamaklı sayıları destekleyecek. Oran iskontosu 0–100% aralığında olacak; sabit tutar iskontosu satır toplamını aşamayacak.
- Genel toplam özeti olacak: iskonto öncesi ara toplam; özellik etkinse toplam iskonto ve iskonto sonrası ara toplam; KDV etkinse toplam KDV ve KDV dâhil genel toplam. Genel toplamlar, iki ondalık basamağa `ROUND_HALF_UP` ile yuvarlanmış satır tutarları üzerinden hesaplanacak.
- PDF yönü sütun sayısı ve genişliklerine göre otomatik dikey veya yatay A4 seçilecek.
- Aynı kayıtlı tekliften PDF ve Excel üretilecek; teklifler ayrıca yerel SQLite veri tabanında saklanacak.
- Kayıtlı teklifler arşivden açılabilecek ve kopyalanabilecek. Düzenlenmiş sürüm yeni bir teklif/revizyon olarak kaydedilecek; önceki kayıt korunacak.
- PDF ve Excel dosyaları Windows kullanıcısının Masaüstü'ne teklif numarasıyla kaydedilecek. Çıktı üretimi için en az bir geçerli ürün satırı zorunlu olacak; kısmen doldurulmuş bir satırdaki zorunlu alanlar eksikse hata gösterilecek. Tamamen boş satırlar teklif verisine dahil edilmeyecek.
- Teklif numarası formatı `YYYYMMDD-NNN` olacak. Her bilgisayar yerel sayacını kullanacak; farklı bilgisayarlarda numara çakışması ihtimali ilk sürüm için kabul ediliyor.
- Ticari koşullar onaylanan başlangıç metinleriyle doldurulabilecek, kullanıcı tarafından düzenlenebilecek ve checkbox ile gizlenebilecek. Checkbox’lar başlangıçta kapalı olacak; kullanıcı alanı açtığında ilgili varsayılan metin düzenlenebilir biçimde yüklenecek. Depolama Şartları ve Ek Alan varsayılan olarak boş kalacak.
- `Ek Alan` zengin metin biçimlerini destekleyecek; en fazla 10.000 görünür karakter kabul edilecek. En az kalın, italik, altı çizili metin, paragraf/satır sonları ve madde işaretli/numaralı listeler desteklenecek.
- Şablonun görsel dili bütün tekliflerde sabit kalacak. Seçilen şirketin bilgileri, tek marka logosu göster/gizle tercihine göre belgeye aktarılacak.
- İlk şirketin mevcut PDF'de görünen bilgileri referans alınabilir. İkinci şirketin bilgileri kullanıcı tarafından daha sonra sağlanacak; eksik bilgiler uydurulmayacak.

## 1. Projenin amacı ve kapsamı

Amaç; iki şirketten biri adına teklif hazırlanabilen, dinamik ürün tablosuna sahip, temel ticari hesaplamaları yapan ve aynı teklif verisinden PDF ile düzenlenebilir Excel dosyası üreten bir Windows masaüstü uygulaması geliştirmektir.

İlk sürümde her bilgisayar kendi yerel veri tabanını kullanacaktır. Kullanıcıların teklifleri ortak bir veri tabanında paylaşması ilk sürüm kapsamına dahil değildir. Bununla birlikte mimari, ileride merkezi veri tabanına geçişi kolaylaştıracak şekilde katmanlı tasarlanmalıdır.

### 1.1 İlk sürüm kapsamına dahil

- Şirket seçimi, teklif tarihi ve teklif yapılacak müşteri/alıcı alanı.
- Tarihe göre otomatik teklif numarası.
- Marka logosunu gösterme/gizleme seçeneği.
- Seçilebilir ürün tablosu sütunları ve sınırsız olmayan ancak dinamik şekilde eklenebilen ürün satırları.
- Girdi doğrulama ve satır bazlı fiyat, iskonto ve KDV hesaplamaları.
- Seçilebilir ticari koşullar ve ek açıklama alanı.
- Aynı tasarım sistemini paylaşan PDF ve Excel çıktıları.
- PDF ve Excel dosyalarını Windows kullanıcısının Masaüstü klasörüne kaydetme.
- Teklif verilerinin yerel SQLite veri tabanına kaydedilmesi.
- Otomatik hesaplamalar ve teklif numaralandırması için otomatik testler.
- Windows `.exe` paketi oluşturma ve Windows üzerinde test etme.

### 1.2 İlk sürüm kapsamı dışında (geleceğe açık)

- Birden fazla bilgisayar arasında gerçek zamanlı veya otomatik veri paylaşımı.
- Merkezi kullanıcı yönetimi ve rol bazlı erişim.
- Bulut veri tabanı, şirketler arası ortak teklif arşivi ve çevrim içi yedekleme.
- E-fatura/e-arşiv entegrasyonu, ERP entegrasyonu, döviz kuru servisi.
- E-posta gönderimi veya elektronik imza entegrasyonu.

Bu özellikler talep edilirse sonraki fazda değerlendirilmelidir. İlk sürümde gereksiz karmaşıklık yaratılmamalıdır.

## 2. Referans dosyalar ve görsel yaklaşım

Kullanıcı tarafından sağlanan referanslar:

- `COFFEE-DO TEKLİF FORMU 08.10.2026.pdf`
- `COFFEE-DO TEKLİF FORMU 08.10.2026-2.xlsx`
- El yazısı “Teklif Formu Projesi” taslak fotoğrafı.

PDF örneğinde şu görsel unsurlar yer alıyor: üst bölgede şirket/teklif kimlik bilgileri; sağ üstte teklif numarası ve tarih; sağ tarafta şirket iletişim/adres ve vergi bilgileri; sayfanın orta bölümünde marka logosu ve ürün tablosu; tablonun altında isteğe bağlı açıklama/koşul satırları; alt bölümde dipnotlar ve iki imza/onay kutusu; sağ alt tarafta hafif bir dekoratif şekil.

Excel örneğinde bir çalışma sayfasında başlık bilgileri, ürün tablosu, iki ürün satırı, teklif koşulları ve açıklama alanları bulunuyor. Bu, bir teklifte birden fazla ürün satırının desteklenmesi gerektiğini doğruluyor.

Yeni PDF'nin referansla aynı piksel düzeninde olması şart değildir. Önemli olan kurumsal ve tutarlı bir görünüm, Türkçe karakterlerin sorunsuz gösterilmesi, seçilen alanların doğru sırayla sunulması ve sayfa taşmalarının önlenmesidir. Yüksek kaliteli logo dosyaları sağlanana kadar yer tutucu görseller kullanılabilir; logolar kodun içine gömülmemeli, kaynak dosyalar olarak yönetilmelidir.

## 3. Kullanıcı akışı ve ekranlar

Önerilen akış, tek pencereli ve bölümlere ayrılmış bir masaüstü arayüzüdür. Alanlar dikeyde uzarsa bölümlerin kaydırılabilir olması gerekir.

1. **Teklif üst bilgileri:** şirket, teklif tarihi, alıcı/müşteri, tek para birimi, miktar birimi (Adet/Litre), genel KDV oranı (KDV etkinse) ve marka logosu göster/gizle seçeneği.
2. **Tablo sütunları:** tabloda gösterilmek istenen alanlar checkbox'larla seçilir. Zorunlu sütunlar kapatılamaz.
3. **Ürün satırları:** dinamik tablo içinde ürün verileri düzenlenir; “Ürün satırı ekle”, “Satırı sil” ve “Satırı kopyala” işlemleri bulunur.
4. **Ticari koşullar:** teslimat adresi, sipariş bildirimi, teslim şekli, ödeme şartları, depolama şartları ve zengin metin destekli ek alan etkinleştirilip doldurulur.
5. **Ön izleme/çıktı:** PDF oluştur, Excel oluştur veya ikisini oluştur işlemi. Mümkün olduğunda PDF ön izleme gösterilir.
6. **Kaydetme ve arşiv:** teklif SQLite'a kaydedilir. Teklif arşivinde mevcut kayıtlar listelenebilir, aranabilir, açılabilir ve kopyalanarak yeni teklif/revizyon oluşturulabilir.

İlk ekranda şirket adı seçilmeden ve teklif tarihi belirlenmeden teklif üretimine izin verilmemelidir. Alıcı metni, dosya ve PDF içinde gerekli yerlerde yeniden kullanılmalıdır. Kayıtlı teklifler doğrudan aynı kayıt üzerine yazılarak değiştirilmemeli; revizyon/kopya yeni teklif numarasıyla ayrı kayıt olarak oluşturulmalı ve kaynak teklif korunmalıdır.

## 4. Üst bilgi alanları

### 4.1 Şirket seçimi

Kullanıcı teklif oluştururken aşağıdaki şirketlerden birini seçer:

- **Endemiks Tarım Ticaret A.Ş.**
- **Endemiks Gıda LTD. ŞTİ.**

Seçilen şirketin ticari adı, adresi, vergi dairesi ve VKN'si teklif şablonunda kullanılır. Şirket logosu ayrıca sağlanmadıkça varsayılmamalıdır; kullanıcının şu an belirttiği tek görsel, göster/gizle seçeneği olan marka logosudur. Referans PDF'de Endemiks Tarım Ticaret A.Ş. için görünen bilgiler, o örneğin verileridir; bu bilgiler otomatik olarak diğer şirketin kayıtlarına kopyalanmamalıdır. Endemiks Gıda LTD. ŞTİ. bilgilerinin kullanıcı tarafından ayrıca sağlanması gerekir.

Şirket bilgileri kod içine serpiştirilmemeli; bir yapılandırma dosyasından veya veri katmanından yönetilmelidir. Eksik şirket bilgileri sessizce başka şirkete ait bilgilerle doldurulmayıp uygulamada belirgin şekilde gösterilmelidir.

### 4.2 Marka logosu

- Kullanıcı marka logosunu göster/gizle checkbox'ı ile kontrol edebilir.
- Şirketin ticari adı ve vergi/iletişim bilgileri ile marka logosu ayrı kavramlardır; mevcut kapsamda yalnızca bir marka logosu varlığı vardır.
- Marka logosu açık olduğunda PDF ve uygun olduğunda Excel üst bölümünde yer alır; kapalı olduğunda bu logo için ayrılan alan da mümkün olduğunca yeniden düzenlenir.
- Kullanıcı tek bir marka logosu bulunduğunu belirtmiştir. İleride birden fazla marka eklenirse bu tasarım genişletilebilir olmalıdır.

### 4.3 Teklif tarihi ve alıcı

- Teklif tarihi kullanıcı tarafından seçilir; varsayılan değer bilgisayarın yerel tarihidir.
- “Teklifin kime yapılacağı” serbest metin alanıdır. Bu değer PDF/Excel içinde tasarımın gerekli yerlerinde kullanılabilir.
- Alıcı alanında Türkçe karakterler kullanılabilmelidir. Uzunluk limiti henüz belirlenmemiştir; önerilen varsayılan en fazla 200 karakterdir.

### 4.4 Para birimi

Teklif genelinde tek para birimi kullanılır. Kullanıcı bir radio button grubundan aşağıdakilerden birini seçer:

- TRY (arayüzde “TRY / Türk Lirası” veya “TL”)
- USD (ABD Doları)
- EUR (Euro)

Para birimi bütün ürün satırları için geçerlidir. Birim fiyat ve sabit tutarlı iskonto aynı para birimini kullanır. Tek teklif içinde farklı para birimlerinin toplanmasına izin verilmez. Döviz kuru çevirimi ilk sürüm kapsamına dahil değildir.

## 5. Teklif numarası üretimi

### 5.1 Format

Teklif numarası biçimi `YYYYMMDD-NNN` olacaktır. Örnekler:

- 20.10.2026 tarihli ilk numaralı teklif: `20261020-001`
- Aynı teklif tarihi için ikinci teklif: `20261020-002`
- 21.10.2026 tarihli ilk teklif: `20261021-001`

Üç haneli sıra numarası minimum genişliktir; 999'u aşan numaralarda numara kesilmemeli, sıra `1000` olarak devam etmelidir.

### 5.2 Kurallar

- Sıra numarası, bilgisayarın o anki tarihinden değil **kullanıcının seçtiği teklif tarihinden** türetilir.
- Her teklif tarihi için sayaç ayrı tutulur ve uygulama kapatılıp açılsa da korunur.
- Teklif numarası SQLite üzerinde benzersiz olmalıdır.
- Numarayı yalnızca ekranda tarih seçildiği anda ayırmak yerine teklif ilk kez veritabanına kaydedilirken atomik biçimde tahsis etmek önerilir. Böylece taslakta tarih değiştirme veya yarıda bırakma nedeniyle çok sayıda boşa numara ayrılması azaltılır.
- Teklif kaydedildikten ve numara verildikten sonra PDF/Excel yeniden oluşturulurken aynı teklif numarası korunur; yeni numara üretilmez.
- Numara tahsisi sayaç tablosu ve işlem/transaction ile yapılmalıdır; iki işlem aynı numarayı alamamalıdır.
- Dosya adı, teklif numarasının aynısı olur: `20261020-001.pdf` ve `20261020-001.xlsx`.

İlk sürümde numaralar bilgisayar başına yereldir. Başka bir bilgisayarda da aynı tarihli teklif aynı sıra numarasıyla oluşturulabilir; çünkü kullanıcılar henüz ortak veri tabanı kullanmıyor. Merkezi veri tabanına geçildiğinde sıra numarası üretimi sunucu tarafında atomik hâle getirilmelidir.

## 6. Ürün tablosu: dinamik satırlar ve sütunlar

### 6.1 Çoklu ürün satırları

Tek bir teklif bir veya daha fazla ürün/hizmet satırı içerebilir. Arayüzde başlangıçta bir boş ürün satırı gösterilmesi önerilir. Kullanıcı “Ürün satırı ekle” ile yeni satırlar ekleyebilir; gereksiz satırları silebilir. Her satırın girdi ve hesaplama değerleri bağımsızdır.

- Satırların sırası PDF ve Excel çıktısında korunmalıdır.
- Bir satır silinince diğer satırların verileri kaymamalı veya birbirine karışmamalıdır.
- Kullanıcıya satır ekleme/silme işlemi açıkça gösterilmelidir.
- Ürün kodu ve açıklama, satırın kimliğini belirleyen sabit anahtarlar olarak kullanılmamalıdır; her satıra iç sistemde ayrı bir kimlik verilmelidir.

### 6.2 Sütunların sabit sırası

PDF ve Excel tablolarında seçilebilir sütunların sırası daima aşağıdaki gibi olmalıdır:

1. Ürün Kodu
2. Ürün Açıklaması
3. Miktar (Adet) **veya** Miktar (Litre) — üst bilgide seçilen tek birime göre başlık oluşturulur
4. Palet
5. Birim Fiyat
6. İskonto Türü
7. İskonto Miktarı
8. KDV
9. Toplam Tutar
10. Toplam Tutar (İskontolu)
11. Toplam Tutar (KDV Dahil)

Adet ve Litre aynı teklifte iki ayrı sütun olarak gösterilmez. Kullanıcı üst bilgi alanında bir kez Adet veya Litre seçer; tüm satırlar bu birimi kullanır. Seçilmeyen veya tüm ürün satırlarında boş kalan sütunlar PDF/Excel çıktısında gösterilmez. Bir sütun en az bir satırda değer içeriyorsa sütun korunur; diğer satırlardaki boş hücreler boş bırakılır.

Kullanıcı sütunları farklı bir sıraya sürükleyerek değiştiremez. Çıktı sırası yukarıdaki sabit sıraya bağlıdır.

### 6.3 Zorunlu sütunlar

- Ürün Açıklaması her zaman bulunur.
- Tek bir Miktar sütunu her zaman bulunur; başlığı üst bilgide seçilen birime göre `Miktar (Adet)` veya `Miktar (Litre)` olur.
- Birim Fiyat her zaman bulunur.
- Toplam Tutar her zaman bulunur.
- Ürün Kodu, Palet ve koşullu sütunlar isteğe bağlıdır.
- Kullanıcı zorunlu bir sütunu kapatmaya çalışırsa checkbox kapalı hâle getirilememeli ve sebebi açıklanmalıdır.
- Miktar alanının birimi teklif bazında seçildiği için bir teklifin tüm satırları aynı birimi kullanır.

### 6.4 Sütun etkinleştirme ve bağımlılıklar

- **KDV:** KDV checkbox'ı teklif genelindeki tek KDV oranı alanını etkinleştirir. Bu kapalıysa `Toplam Tutar (KDV Dahil)` checkbox'ı pasif ve seçilemez olur. KDV sütunu gösteriliyorsa teklifin aynı KDV oranı her ürün satırında gösterilir.
- **İskonto Türü:** İskonto desteği bu sütunun checkbox'ı ile etkinleştirilir. Bu kapalıysa `İskonto Miktarı` ve `Toplam Tutar (İskontolu)` checkbox'ları pasif ve seçilemez olur. İskonto türü ve miktarı ürün satırı bazındadır.
- **Toplam Tutar:** Her zaman aktiftir ve kapatılamaz.
- Koşullu toplam sütunları yalnızca ilgili girdiler/özellik etkin olduğunda seçilebilir olmalıdır.
- Bir özellik kapatılırsa ona bağlı sütunlar devre dışı kalmalı; kullanıcıya verilerin kaybolabileceği durumlar açıkça bildirilmelidir.

### 6.5 Her satırın alanları

Ürün tablosu satırında, seçilen sütunların karşılığı olan giriş alanları bulunur. Görsel arayüzde ürün tablosu yatay olarak kaydırılabilir olabilir; ana amaç bütün girişlerin okunaklı kalmasıdır. PDF/Excel üretiminde kullanıcı seçimine ve Bölüm 6.2 sırasına uyulur.

### 6.6 Kaydetme ve çıktı öncesi ürün satırı doğrulaması

- Arayüz ilk açıldığında bir boş ürün satırı gösterebilir.
- Tamamen boş ürün satırları veri modeline/çıktıya dahil edilmez; kullanıcı bunları silmek zorunda bırakılmaz.
- Kısmen doldurulmuş bir ürün satırı varsa satırdaki zorunlu alanlar tamamlanmadan teklif kaydedilemez veya PDF/Excel'e aktarılamaz.
- Çıktı oluşturulmadan önce en az bir geçerli ürün satırı bulunmalıdır.
- Her geçerli satırda **Ürün Açıklaması, Miktar ve Birim Fiyat** doldurulmuş olmalıdır. Miktar pozitif, birim fiyat negatif olmayan geçerli sayısal değer olmalıdır.
- Doğrulama hataları genel bir hata mesajı olarak değil, ilgili alan/satır yanında açıkça gösterilmelidir.
- Boş bırakılması isteğe bağlı diğer alanlar (ör. Ürün Kodu ve Palet) zorunlu kılınmamalıdır.


## 7. Girdi doğrulama kuralları

### 7.1 Ürün Kodu ve Ürün Açıklaması

- Türkçe karakterler, sayılar ve normal metin karakterleri desteklenmelidir.
- Her alan için azami uzunluk 64 karakterdir.
- Yazım sırasında karakterler kaybolmamalı veya ASCII'ye zorlanmamalıdır.
- Alan metinleri başta/sonda gereksiz boşluklar açısından normalize edilebilir; metnin içindeki boşluk ve Türkçe karakterler korunmalıdır.

### 7.2 Miktar ve Palet

- Teklif üst bilgilerinde `Adet` veya `Litre` birimi bir kez seçilir. Bu seçim tüm ürün satırlarına uygulanır ve tablo başlığı `Miktar (Adet)` veya `Miktar (Litre)` olur.
- Miktar ve Palet alanları yalnızca pozitif sayısal değer kabul eder; sıfır ve negatif değerler reddedilir.
- Tam sayı veya virgülden sonra en fazla iki basamaklı ondalık sayı kabul edilir.
- Geçerli örnekler: `15`, `15,5`, `15,05`.
- Geçersiz örnek: `15,005`.
- Türkçe yerel ayarına uygun ondalık virgül kullanıcı arayüzünde desteklenmelidir. İç hesaplama için girişler güvenli biçimde sayıya dönüştürülmelidir.
- Binlik ayraçla karışıklık olmaması için giriş davranışı açık olmalı; tercihen kullanıcı giriş alanına binlik ayraç girmemelidir.

### 7.3 Birim Fiyat

- Para değeri olmalıdır ve negatif olamaz; sıfır izinlidir.
- Para birimi teklif genelinde seçilir ve bütün birim fiyatlara uygulanır.
- Kullanıcı arayüzü Türkçe sayı biçimini göstermelidir; içeride metin olarak para hesaplanmamalıdır.

### 7.4 KDV

- KDV etkinleştirilirse teklif üst bilgileri bölümünde tek bir KDV oranı girilir; bu oran bütün ürün satırlarına uygulanır.
- Oran negatif olamaz; sıfır izinlidir.
- Ondalık virgülden sonra en fazla iki basamağa izin verilir.
- Arayüz ve çıktıdaki anlamı yüzde olmalıdır: örneğin `10` değeri `%10` demektir. Hesaplamada 100'e bölünür.
- KDV sütunu çıktı için seçilmişse aynı teklif-geneli oran her satırda gösterilir. KDV dahil tutarların hesaplaması ise her satırın ilgili matrahı üzerinde yapılır.

### 7.5 İskonto Türü ve İskonto Miktarı

İskonto sütunları etkinleştirildiyse her satırda iskonto türü ve miktarı kendi satırına ait olmalıdır. İskonto türü iki seçenekten oluşur:

- **Oran:** İskonto değeri yüzde olarak yorumlanır. 0 ile 100 arasında (iki sınır dahil) olmalıdır; en fazla iki ondalık basamağa izin verilir. Örnek: `12,50` → `%12,50`. `100,01` ve negatif değerler reddedilir.
- **Miktar:** İskonto değeri teklifin para biriminde sabit bir tutardır. Para tutarı olduğu için en fazla iki ondalık basamağa izin verilir; tam kısmında en az 10 basamağa kadar değer girilebilmelidir (ör. `1234567890,25`). Negatif olamaz.

Kullanıcı isteği radio button olduğundan, her ürün satırının iskonto türü için ayrı bir “Oran / Miktar” radio button grubu kullanılması önerilir. PDF/Excel'de bu sütun “Oran” veya “Miktar” şeklinde gösterilir. Eğer daha kompakt bir UI gerekirse eşdeğer satır bazlı seçim kontrolü kullanılabilir; seçim hiçbir zaman tüm satırlara istemeden ortak uygulanmamalıdır.

İskonto uygulanmadıysa boş iskonto girdileri sıfır iskontoyla aynı sonuca yol açmalı; ancak iskontolu toplam sütununun çıktıda gösterimi Bölüm 6.2'deki tamamen boş sütun kuralına bağlıdır.

### 7.6 Metin alanları ve karakter limitleri

Checkbox ile etkinleştirilebilen alanlar:

- Teslimat Adresi – en fazla 3.000 karakter
- Sipariş Bildirimi – en fazla 3.000 karakter
- Teslim Şekli – en fazla 3.000 karakter
- Ödeme Şartları – en fazla 3.000 karakter
- Depolama Şartları – en fazla 3.000 karakter
- Ek Alan – en fazla 10.000 karakter

Bu alanlar Türkçe karakterleri ve sayıları desteklemelidir. Etkinleştirilmemiş alanlar PDF/Excel çıktısında yer almamalıdır. Checkbox'lar varsayılan olarak kapalıdır. Kullanıcı checkbox'ı açtığında aşağıdaki başlangıç metni ilgili alana getirilir; kullanıcı metni değiştirebilir. Kaydedilmiş teklif yeniden açıldığında o teklifte saklanan etkinlik durumu ve metin korunur.

Onaylanan başlangıç metinleri:

- **Teslimat Adresi:** `Tek bir merkezi noktaya Adres Teslimdir.`
- **Sipariş Bildirimi:** `Sipariş 15 gün önceden bildirilmelidir. Teklif geçerlilik süresi 7 gündür.`
- **Teslim Şekli:** `Tek bir merkezi noktaya Adres Teslimdir.`
- **Ödeme Şartları:** `Nakit veya kredi kartı ile ödeme uygundur.`
- **Depolama Şartları:** varsayılan metin yok; alan boş açılır.
- **Ek Alan:** varsayılan metin yok; zengin metin editörü boş açılır.

Referans PDF'deki ürün/teklif özel dipnotları (ör. etiket ücreti, ürün toleransı veya KDV'ye ilişkin müşteri/teklif özelindeki açıklamalar) genel varsayılan metin olarak otomatik eklenmemelidir.

Ek Alan dışındaki alanlar PDF/Excel'de kalın etiket ile başlamalıdır. Örnek: **Teslim Şekli:** Tek bir merkezi noktaya adres teslimidir. Ek Alan için otomatik etiket eklenmez; yazıldığı şekilde aktarılır. Ek Alan zengin metin editörü kullanır. En az kalın, italik, altı çizili metin, satır sonları/paragraflar ve madde işaretli/numaralı listeler desteklenmelidir. Karakter sınırı, HTML işaretlemeleri değil görünür metin karakterleri üzerinde uygulanır. Biçimlendirme yapısı veri tabanında güvenli ve yeniden üretilebilir biçimde saklanmalı; PDF çıktısında korunmalı, Excel çıktısında da mümkün olduğu ölçüde korunmalı ve desteklenmeyen biçimler sessizce kaybolmamalıdır.

## 8. Hesaplama kuralları

Hesaplama kodu arayüz bileşenlerinden ayrı bir modülde bulunmalı ve arayüzden bağımsız birim testleriyle doğrulanmalıdır. Para hesaplamalarında ikili kayan nokta hatalarını önlemek için Python `Decimal` kullanılmalıdır. Girdi metnindeki ondalık virgül güvenli biçimde normalize edilmelidir.

### 8.1 Satır toplamı

`Toplam Tutar = Miktar × Birim Fiyat`

Miktar birimi (Adet/Litre) teklif genelinde bir kez seçilir; tüm satırlar aynı birimi kullanır. Palet alanı bilgi alanıdır ve ayrıca bir fiyat bileşeni tanımlanmadıkça formüle katılmaz.

### 8.2 İskontolu toplam

İskonto türü **Oran** ise:

`İskontolu Tutar = Toplam Tutar × (1 − İskonto Oranı / 100)`

İskonto türü **Miktar** ise:

`İskontolu Tutar = Toplam Tutar − İskonto Tutarı`

İskonto tutarı satır toplamını aşarsa kayıt/çıktı engellenmeli ve ilgili satırda hata gösterilmelidir. Negatif iskontolu toplam üretilmemelidir.

### 8.3 KDV dahil toplam

Tek bir KDV oranı teklif genelinde geçerlidir. KDV oranı yüzde olarak girilir.

- İskonto etkinse: `KDV Dahil Toplam = İskontolu Tutar × (1 + KDV Oranı / 100)`
- İskonto etkin değilse: `KDV Dahil Toplam = Toplam Tutar × (1 + KDV Oranı / 100)`

Örnek: matrah 100 ve KDV `%10` ise sonuç 110 olur. İskontolu matrah 90 ve KDV `%10` ise sonuç 99 olur.

### 8.4 Yuvarlama ve para biçimi

- Hesaplamada `Decimal` kullanılmalıdır.
- Kullanıcı arayüzünde ve çıktıların para tutarı gösteriminde iki ondalık basamak kullanılmalıdır.
- Kesin yuvarlama kuralı `ROUND_HALF_UP` olacaktır. Gösterilen para tutarları iki ondalık basamağa yuvarlanır. Hesaplama motoru ara adımlarda yeterli `Decimal` hassasiyetini korur; satır bazında gösterilen iskonto, matrah, KDV ve KDV dâhil değerler tutarlı şekilde iki basamağa yuvarlanır. Genel toplamlar, kullanıcıya gösterilen yuvarlanmış satır değerlerinin toplamından üretilir.
- Yuvarlama tek, merkezi fonksiyonda uygulanmalı; sınır durumları otomatik testlerle güvence altına alınmalıdır.
- PDF ve Excel'deki sayı biçimi tutarlı olmalıdır. Excel'de sayısal hücreler gerçek numerik değer olmalı, metin biçiminde para değerleri olmamalıdır.

### 8.5 Teklif genel toplam özeti

PDF ve Excel teklifinin sonunda ayrı bir genel toplam özeti bulunmalıdır:

- **Ara Toplam (iskonto öncesi):** her ürün satırının `Toplam Tutar` değerlerinin toplamı; her zaman gösterilir.
- **Toplam İskonto:** iskonto özelliği etkinse, satır bazında iskonto tutarlarının toplam etkisi gösterilir.
- **İskonto Sonrası Ara Toplam:** iskonto özelliği etkinse, satırların iskontolu tutarlarının toplamı gösterilir.
- **Toplam KDV:** KDV özelliği etkinse, satır bazında oluşan KDV tutarlarının toplamı gösterilir.
- **KDV Dâhil Genel Toplam:** KDV özelliği etkinse, satırların KDV dahil tutarlarının toplamı gösterilir.

Bu özet, tabloda `Toplam Tutar (İskontolu)` veya `Toplam Tutar (KDV Dahil)` sütunlarının görünür seçilip seçilmediğinden bağımsız olarak, ilgili hesaplama özelliği etkinse gösterilir. Özetin toplamları aynı satır hesaplama motorundan üretilmeli; ekranda, PDF'de ve Excel'de birbirleriyle tutarlı olmalıdır.

## 9. PDF çıktısı

### 9.1 Genel gereksinimler

- PDF, kullanıcı tarafından seçilen teklif verilerinden üretilir.
- Teklif numarası ve tarih görünür olmalıdır.
- Seçilen şirketin ticari ve vergisel bilgileri gösterilir.
- Mevcut marka logosu yalnızca kullanıcı göster seçeneğini açtıysa gösterilir; ayrıca şirket logosu sağlanmadıkça varsayılmaz.
- Ürün tablosu Bölüm 6.2'deki sabit sırayı kullanır.
- Seçilmeyen veya tamamen boş olan sütunlar gösterilmez.
- Seçilmeyen koşul alanları ve boş metin alanları gösterilmez.
- Ek Alan, etiket eklenmeden gösterilir; diğer koşul alanları kalın etiketle başlar.
- Türkçe karakterleri kapsayan gömülebilir font kullanılmalıdır.
- Uzun ürün açıklamaları ve koşul metinleri hücre veya blok içinde satır kaydırmalıdır.
- İçerik sayfa dışına taşmamalı, logo/metin/tablo üst üste binmemelidir.

### 9.2 Sayfa yönü

PDF sayfa yönü sütun sayısına ve sütunların gereken genişliğine göre otomatik seçilir:

- Tablo dikey A4'e okunaklı şekilde sığıyorsa dikey A4.
- Tablo genişliği dikey kullanılabilir alanı aşıyorsa yatay A4.
- Yön kararı yalnızca basit sabit bir sütun sayısına bağlanmamalı; sütun türleri, başlık uzunluğu ve içerik genişlikleri dikkate alınmalıdır.
- Dikey/yatay kararından bağımsız olarak tablo çok sayfaya uzayabilir. Çok sayfalı tabloda başlık satırı her sayfada tekrarlanmalıdır.
- Aşırı küçültülmüş yazı kullanmak yerine sayfa yönü, sütun genişliği ve sayfa bölünmesi ayarlanmalıdır.

### 9.3 Görsel hiyerarşi

Referans dosyaya benzer biçimde bir şablon sistemi kullanılabilir:

- Üst bölüm: şirket kimlik bilgileri, teklif numarası, tarih ve alıcı bilgisi.
- Şirket adres/vergi bilgileri.
- Marka logosu (seçilirse).
- Ürün tablosu.
- Seçilen ticari koşullar ve zengin biçimlendirmesi korunmuş Ek Alan.
- Genel toplam özeti (iskonto öncesi ara toplam, özellik etkinse iskonto ve iskontolu ara toplam, özellik etkinse toplam KDV ve KDV dâhil genel toplam).
- Varsa açıklayıcı dipnotlar.
- İmza/onay alanları.

İmza alanlarının metni, boyutu ve sayısı ile dipnotların varsayılan içeriği henüz kesinleştirilmemiştir. Kullanıcı tarafından onaylanana kadar bunlar yapılandırılabilir olmalı ve örnekten alınan ticari metinler yeni her teklife otomatik eklenmemelidir.

### 9.4 Dosya konumu ve çakışma

- PDF, Windows kullanıcısının gerçek Masaüstü dizinine kaydedilir; sabit `C:\Users\...\Desktop` yolu kodlanmaz.
- Masaüstü bulunamaz/yazılamaz durumdaysa kullanıcıya “Farklı Kaydet” seçeneği sunulur.
- Dosya adı teklif numarasıdır: `<TeklifNo>.pdf`.
- Aynı adlı dosya varsa sessizce üzerine yazılmamalı; kullanıcıya üzerine yazma veya farklı konum/dosya adı seçeneği sunulmalıdır.

## 10. Excel çıktısı

- Excel dosyası `.xlsx` biçiminde olmalıdır.
- PDF ile aynı teklif verisini ve aynı ürün satırı sırasını kullanmalıdır.
- Dosya adı `<TeklifNo>.xlsx` olmalı ve Windows Masaüstü'ne kaydedilmelidir.
- Hücreler elle düzenlenebilir olmalıdır.
- Hesaplanabilir sütunlarda Excel formülleri kullanılması tercih edilir. Kullanıcı miktar veya birim fiyatı değiştirirse satır toplamları ve etkin hesaplanmış sütunlar güncellenebilmelidir.
- Çıktıda sadece seçili ve boş olmayan sütunlar, aynı sabit sıra ile bulunmalıdır.
- Para ve yüzde hücreleri uygun Excel sayı biçimine sahip olmalı; tutarlar metin olarak yazılmamalıdır.
- Sütun başlıkları, satır sınırları, metin kaydırma, sütun genişlikleri ve yazdırma yönü düzenli olmalıdır.
- Uzun koşul metinleri okunabilir ve düzenlenebilir biçimde tutulmalıdır. Ek Alanın zengin metin biçimleri desteklenen ölçüde korunmalı; metin satırları ve listeleri okunaklı aktarılmalıdır.
- Genel toplam özeti PDF ile aynı hesaplamaları içermelidir.
- Logo eklenmesi Excel yerleşimini bozmayacaksa desteklenebilir; PDF görsel kalitesi Excel'de birebir zorunlu değildir.
- Kullanıcı Excel dosyasında manuel düzenleme yaptıktan sonra bu düzenlemeler PDF'ye otomatik aktarılmaz. PDF ve Excel başlangıçta aynı kaydedilmiş teklif kaydından ayrı ayrı oluşturulur.

## 11. Yerel veri tabanı ve gelecekteki ortak veri tabanı

### 11.1 İlk sürüm: SQLite

- SQLite veritabanı, Windows'ta uygulamanın kurulu olduğu klasöre değil kullanıcının yazılabilir uygulama veri dizinine konmalıdır. Böylece uygulama güncellemesi/veri izinleri sorunları azaltılır.
- macOS geliştirme ortamında da platforma uygun kullanıcı veri dizini kullanılmalıdır.
- Teklif girdileri, ürün satırları, seçilen sütunlar, etkin koşul alanları, zengin metin içeriği, para birimi, miktar birimi, teklif-geneli KDV oranı, şirket seçimi, marka logosu tercihi, teklif tarihi ve teklif numarası saklanmalıdır.
- PDF/Excel tekrar üretildiğinde aynı kayıt kullanılmalıdır.
- İlk sürüm veri modelinde en az şu kavramlar olmalıdır: `Offer`, `OfferItem`, `OfferSection`, `CompanyConfig`, `DailySequence`.
- Veritabanı şema sürümü/migrasyon yaklaşımı en baştan eklenmelidir.
- Kaydetme ve numara tahsisi transaction içinde yapılmalıdır.
- Veritabanı bozulması/erişim hatası olursa kullanıcıya okunabilir bir hata gösterilmeli; veri sessizce silinmemelidir.

### 11.2 Geleceğe açık veri erişimi

Arayüz, hesaplama modülü ve PDF/Excel üretimi doğrudan SQLite SQL sorgularına bağlanmamalıdır. Bir repository/data access katmanı üzerinden veri okunup yazılmalıdır. İlk sürüm bu katmanda SQLite uygulamasını kullanır; ileride PostgreSQL veya bir API servisi eklenebilir.

Gelecekte birden fazla bilgisayar ortak veri kullanacaksa merkezi veri tabanı/servis tekil teklif numarası ve erişim kontrolünü yönetmelidir. Masaüstü uygulamasının içine yönetici veritabanı parolası veya gizli servis anahtarı gömülmemelidir. Merkezi kullanım için kimlik doğrulama, yetkilendirme, yedekleme ve eşzamanlı numara tahsisi ayrıca tasarlanmalıdır.

## 12. Önerilen teknik mimari ve dosya yapısı

Önerilen teknoloji seçimi:

- **Arayüz:** PySide6.
- **Yerel veri tabanı:** SQLite.
- **PDF:** Türkçe font gömme, tablo sayfalama ve ölçülü yerleşim sağlayan bir PDF kütüphanesi. Seçilen kütüphane Windows paketinde test edilmelidir.
- **Excel:** `openpyxl` veya ihtiyaca göre benzer bir `.xlsx` üretim kütüphanesi. Excel'de gerçek formüller ve sayısal hücreler oluşturulmalıdır.
- **Hesaplama:** `Decimal` kullanan saf iş mantığı fonksiyonları.
- **Testler:** `pytest` veya eşdeğeri.
- **Paketleme:** PyInstaller; Windows nihai paketi Windows ortamında oluşturulmalı ve test edilmelidir.

Önerilen ilk klasör yapısı (ajan, mevcut projeyi inceledikten sonra gerekirse adları iyileştirebilir; katman ayrımı korunmalıdır):

```text
teklif_sablonu/
  README.md
  pyproject.toml veya requirements.txt
  src/teklif_sablonu/
    main.py
    app.py
    ui/
      main_window.py
      offer_header_widget.py
      column_selection_widget.py
      items_table_model.py
      sections_widget.py
      preview_dialog.py
    domain/
      models.py
      validation.py
      calculations.py
      offer_numbering.py
    services/
      offer_service.py
      pdf_export_service.py
      excel_export_service.py
    storage/
      database.py
      migrations.py
      repositories.py
      sqlite_offer_repository.py
    templates/
      pdf_template.py
      styles.py
    config/
      companies.json
      settings.py
    assets/
      companies/
      brands/
      fonts/
  tests/
    test_validation.py
    test_calculations.py
    test_numbering.py
    test_storage.py
    test_pdf_export.py
    test_excel_export.py
```

Bu bir başlangıç önerisidir, mutlak dizin zorunluluğu değildir. Proje büyüdükçe uygun şekilde düzenlenebilir. Görsel dosyalar, şirket adresleri ve logo yolları ayrı yapılandırmada tutulmalıdır.

## 13. Asgari veri modeli

Ajan gerçek şemayı ayrıntılandırabilir; ancak aşağıdaki kavramlar birbirinden ayrılmalıdır.

### `offers`

- `id` (iç birincil anahtar)
- `offer_number` (benzersiz, ör. `20261020-001`)
- `offer_date` (seçilen tarih)
- `company_id`
- `recipient_name`
- `currency_code` (`TRY`, `USD`, `EUR`)
- `quantity_unit` (`piece` veya `litre`, teklif genelinde tek değer)
- `vat_rate` (KDV etkinse teklif-geneli oran)
- `brand_logo_visible`
- `selected_columns` (sıralamayı değiştirmeden seçimi saklayan yapı)
- `created_at`, `updated_at`
- `source_offer_id` (kopyalanan/revize edilen teklifin kaynak kaydı; isteğe bağlı)
- çıktı dosya yolları, gerekiyorsa

### `offer_items`

- `id`, `offer_id`, `position`
- `product_code`, `description`
- `quantity_value`, `pallet_count` (miktar birimi teklif kaydında saklanır)
- `unit_price`
- `discount_type`, `discount_value`
- hesaplamaların yeniden üretilebilmesi için gerekli tüm kaynak girdiler

### `offer_sections`

- `id`, `offer_id`, `section_key`, `enabled`, `text` veya güvenli zengin metin içeriği, `position`
- `section_key`, Teslimat Adresi/Sipariş Bildirimi/Teslim Şekli/Ödeme Şartları/Depolama Şartları/Ek Alan değerlerinden biri olmalıdır.

### `daily_sequences`

- `offer_date` birincil anahtar veya benzersiz alan
- `last_sequence`

### Şirket yapılandırması

Firma adı, adres, vergi dairesi, VKN ve logo yolu gibi sabit bilgiler uygulama yapılandırmasından okunabilir. Her teklif kaydında, teklifin yeniden üretilebilmesi için gereken şirket bilgisinin bir anlık görüntüsünü saklamak gerekip gerekmediği geliştirme sırasında değerlendirilmelidir; uzun vadede şirket bilgisi değişince eski teklifler değişmiş görünmemelidir.

## 14. Hata mesajları ve kullanıcı deneyimi

- Doğrulama hataları ilgili hücrenin yanında veya satır üzerinde gösterilmelidir.
- Hata bulunduğunda PDF/Excel üretimi durdurulmalı ve hangi alanın düzeltilmesi gerektiği açıklanmalıdır.
- Türkçe ondalık virgül doğru yorumlanmalıdır.
- Uzun metin alanlarında karakter sınırına yaklaşınca sayaç göstermek faydalıdır.
- Sütun checkbox'ı kapatıldığında buna bağlı girdiler kaybolacaksa kullanıcıya bildirim gösterilmelidir.
- Başarılı çıktıdan sonra dosya konumu gösterilmeli; dosya mevcutsa sessiz üzerine yazma yapılmamalıdır.
- Hesaplama sonucu her satırda anlık görünmelidir; çıktıdan önce mümkünse ön izleme sağlanmalıdır.
- PDF/Excel kaydedilmeden önce teklif numarası ve tarih görünür şekilde doğrulanmalıdır.

## 15. Kabul kriterleri ve test senaryoları

Uygulama teslim edildiğinde en az aşağıdaki kontroller otomatik veya belgelenmiş manuel testlerle doğrulanmalıdır.

### 15.1 Teklif numarası

1. Seçilen 20.10.2026 tarihi için ilk teklif `20261020-001` olur.
2. Aynı bilgisayarda aynı tarihte kaydedilen ikinci teklif `20261020-002` olur.
3. 21.10.2026 tarihindeki ilk teklif `20261021-001` olur.
4. Uygulama kapatılıp açıldığında yerel sıra bilgisi kaybolmaz.
5. Mevcut teklif yeniden dışa aktarılırken teklif numarası değişmez.
6. Aynı bilgisayardaki eşzamanlı kayıt denemeleri yerel veritabanında çift numara üretmez. Farklı bilgisayarlarda çakışma olasılığı ilk sürüm için kabul edilir.

### 15.2 Girdi doğrulama

1. `15`, `15,5`, `15,05` miktar girdileri kabul edilir; `15,005`, negatif miktar ve sıfır miktar reddedilir.
2. Teklifte Adet seçiliyse tüm satırlar `Miktar (Adet)`, Litre seçiliyse `Miktar (Litre)` olarak çıkar; aynı teklifte farklı miktar birimi kullanılamaz.
3. Ürün kodu/açıklaması 64 karakterden uzun olamaz ve Türkçe karakterleri korur.
4. Negatif birim fiyat reddedilir; sıfır fiyat kabul edilir.
5. Teklif-geneli KDV oranı için `10`, `10,25` kabul edilir; `10,256` ve negatif değer reddedilir.
6. Oran iskontosu 0–100 aralığında ve en fazla iki ondalık basamak kabul eder; 100 üzeri ve negatif değerler reddedilir.
7. Sabit tutar iskontosu en fazla iki ondalık basamak kabul eder; tam kısmında en az 10 basamak desteklenir.
8. Sabit iskonto satır toplamını aştığında kullanıcıya açık hata gösterilir; kayıt/çıktı engellenir.
9. Tamamen boş ürün satırları yok sayılır; kısmen doldurulmuş satırda Ürün Açıklaması, Miktar veya Birim Fiyat eksikse kayıt/çıktı engellenir. En az bir geçerli ürün satırı zorunludur.
10. Uzun metin alanları kendi karakter limitlerini aşamaz. Ek Alan için 10.000 görünür karakter sınırı uygulanır; zengin metin işaretleme kodu bu sayıya dahil edilmez.

### 15.3 Hesaplamalar

1. Miktar 10 × birim fiyat 100 → toplam 1.000,00.
2. 1.000,00 toplamın `%10` oran iskontosu → 900,00.
3. 1.000,00 toplamdan 100,00 sabit iskonto → 900,00.
4. 1.000,00 matrah ve `%10` KDV → KDV dâhil 1.100,00.
5. 1.000,00 toplam, `%10` satır iskontosu ve `%10` teklif-geneli KDV → KDV dâhil 990,00.
6. KDV etkinse bütün satırlar aynı teklif-geneli KDV oranını kullanır.
7. Genel toplam özeti ara toplamı, etkinse iskonto toplamını/iskonto sonrası ara toplamı ve KDV etkinse toplam KDV/KDV dâhil genel toplamı içerir.
8. İskonto kapalıysa iskontolu hesap sütunları; KDV kapalıysa KDV dâhil hesap sütunu seçilemez.
9. Toplam Tutar sütunu her durumda bulunur.

### 15.4 PDF/Excel

1. Sütunlar tam olarak Bölüm 6.2 sırasıyla çıkar; miktar başlığı teklif-geneli Adet/Litre seçimine göre yalnızca bir sütun olarak gösterilir.
2. Ürün satırı ekleme/silme/kopyalama PDF ve Excel'e doğru yansır.
3. Seçilmeyen ve tamamen boş sütunlar çıktıdan çıkarılır. Bazı satırlarda boş değer olması, başka bir satırda değer bulunan sütunu gizlemez.
4. Türkçe karakterler PDF'de düzgün görünür.
5. Uzun ürün açıklamaları ve koşul alanları kesilmez; Ek Alanın belirtilen temel zengin metin biçimleri PDF'de korunur.
6. Çok sütun seçildiğinde yatay A4 düzeni seçilebilir; az sütunla dikey düzen kullanılabilir.
7. Çok sayfalı tabloda başlık satırı tekrar eder ve satırlar bölünürken okunabilirlik korunur.
8. PDF ve Excel dosya adları aynı teklif numarasını taşır.
9. Excel'de tutar ve yüzde hücreleri sayısal/formüllü olarak kalır; girişler değiştiğinde hesaplama formülleri yeniden çalışabilir.
10. Excel'e Ek Alan biçimlendirmesi desteklenen kapsamda aktarılır; biçim kaybı varsa sessiz kalınmaz.
11. Aynı dosya adı mevcutsa kullanıcıya çakışma seçeneği sunulur.
12. Genel toplam özeti PDF ve Excel'de aynı hesaplamaları ve tutarları gösterir.
13. Oran iskontosu `0`, `100` ve `12,50` değerlerini kabul eder; `100,01` ve negatif değerleri reddeder.
14. Koşul checkbox'ları başlangıçta kapalıdır; etkinleştirildiğinde onaylanan başlangıç metni yüklenir ve kullanıcı tarafından değiştirilebilir. Depolama Şartları/Ek Alan boş başlar.

### 15.5 Arşiv, mimari ve paketleme

- Kayıtlı teklifler listelenebilir, aranabilir ve incelenebilir.
- Bir teklif kopyalandığında yeni numarayla yeni kayıt oluşur; kaynak teklif değişmeden kalır.
- Hesaplama mantığı UI'dan bağımsız test edilebilir.
- SQLite veri dosyası uygulama yükleme dizininin dışında, kullanıcıya ait veri dizinindedir.
- Şirket verileri ve varlık yolları kaynak kodun içine dağınık sabitler olarak gömülmemiştir.
- PDF/Excel üretimi doğrudan UI hücrelerinden değil, ortak teklif modelinden çalışır.
- Windows paketinde fontlar, görseller ve PDF/Excel bağımlılıkları eksiksiz bulunur.
- Nihai Windows `.exe` paketi temiz bir Windows ortamında test edilmiştir.

## 16. Kalan uygulama varsayımları ve teslim öncesi girdiler

Kullanıcı aşağıdaki kararları onaylamıştır; bunlar artık açık karar değildir: tek miktar birimi (Adet/Litre) teklif genelinde seçilir; KDV oranı teklif genelindedir; genel toplam özeti bulunur; arşivden teklif açma/kopyalama ve ayrı revizyon kaydı desteklenir; ticari koşul alanlarının varsayılan metinleri belirlenmiştir ve checkbox başlangıçta kapalıdır; Ek Alan zengin metin destekler; sabit tutar iskontosu iki ondalık basamakla sınırlandırılır; oran iskontosu 0–100 ile sınırlıdır; para yuvarlamasında `ROUND_HALF_UP` kullanılır; boş/kısmen dolu ürün satırlarının çıktı öncesi doğrulaması uygulanır; farklı bilgisayarlardaki teklif numarası çakışma riski ilk sürümde kabul edilir.

### 16.1 Uygulama varsayımları

1. **Kısmen dolu sütunlar:** Seçili bir sütun tüm ürün satırlarında boşsa PDF/Excel'den çıkarılır. En az bir satırda değer varsa sütun korunur ve diğer satırlardaki boş hücreler boş kalır.
2. **Yuvarlama (onaylandı):** `Decimal` ve `ROUND_HALF_UP` kullanılır. Satır düzeyindeki para gösterimleri iki ondalık basamağa yuvarlanır; genel toplam bu görünen satır değerleriyle mutabık kalacak şekilde hesaplanır.
3. **Alıcı alanı:** Başlangıç için 200 karakter limiti uygulanabilir; bu teknik bir varsayımdır ve gerektiğinde yapılandırmadan değiştirilebilir.
4. **Ek Alan biçimleri:** İlk sürümde kalın, italik, altı çizili, paragraf/satır sonu, madde işaretli ve numaralı liste desteklenir. Karakter limiti görünür karakterlere uygulanır. Biçimlendirme PDF'de korunmalı; Excel de desteklenen özellikleri korumalıdır.
5. **Varsayılan koşul metinleri (onaylandı):** 7.6 bölümündeki teslimat adresi, sipariş bildirimi, teslim şekli ve ödeme şartları metinleri kullanılır. Checkbox'lar varsayılan kapalıdır; açıldığında ilgili metin düzenlenebilir olarak yüklenir. Depolama Şartları ve Ek Alan boş başlar. Teklife/ürüne özel dipnotlar varsayılan olarak eklenmez. Metinler ileride kod değiştirmeden yapılandırılabilir olacak şekilde tutulmalıdır.
6. **Revizyon davranışı:** Kayıtlı teklifin kopyalanması yeni bir teklif kaydı ve yeni teklif numarası üretir; orijinal kayıt değişmeden korunur. Kaynak teklif ilişkisi arşivde tutulabilir.
7. **Sabit tutar iskontosu:** Para birimi teklif genelindeki para birimidir; tam kısmında 10 basamağa, kesir kısmında iki basamağa kadar girişe izin verilir.
8. **Yerel numara çakışması:** Her bilgisayarın yerel SQLite sayacı vardır. Farklı bilgisayarlarda aynı tarihli numaraların çakışması ilk sürümde kabul edilmiştir. Merkezi veri tabanına geçişte atomik sunucu tarafı numara tahsisi gerekecektir.
9. **Satır doğrulaması (onaylandı):** Tamamen boş satırlar yok sayılır. Kısmen doldurulmuş satırlarda Ürün Açıklaması, Miktar ve Birim Fiyat zorunludur. En az bir geçerli satır yoksa kayıt/çıktı engellenir.
10. **Oran iskontosu sınırı (onaylandı):** 0–100 aralığı ve en fazla iki ondalık basamak; sabit iskonto toplamı aşamaz.

### 16.2 Gerekli varlık ve firma bilgileri

- Endemiks Tarım Ticaret A.Ş. için referans PDF'deki adres/vergi bilgileri ilk yapılandırma için referans alınabilir; üretim öncesi doğrulanmalıdır.
- Endemiks Gıda LTD. ŞTİ. için adres, vergi dairesi ve VKN kullanıcı tarafından daha sonra sağlanacaktır. Bu bilgiler gelene kadar placeholder kullanılmalı, gerçek bilgi uydurulmamalıdır.
- Marka logosunun mümkünse yüksek çözünürlüklü PNG veya SVG dosyası gerekir.
- Şirketlere ait ayrı görsel/logo dosyaları sağlanmadıkça şirket logoları varsayılmamalıdır.
- Dipnotlar ve imza alanları yapılandırılabilir olmalı; kullanıcı onaylamadan referans PDF'deki müşteri özel metinleri tüm tekliflere otomatik kopyalanmamalıdır.

### 16.3 İleride ortak veri tabanına geçiş

İlk sürümde her bilgisayar yerel olarak çalışır. Aynı formatta teklif numarası üretmek için her bilgisayarın yerel sayacı yeterlidir ancak farklı bilgisayarlar arasında benzersizlik sağlamaz. İleride ortak teklif arşivi ve benzersiz numara istenirse merkezi veri tabanı/API ve atomik numara tahsisi gerekecektir. Bu özellik ilk sürümde geliştirilmeyecek, ancak repository/data access katmanı nedeniyle sonradan eklenebilmelidir.

## 17. Kodlama ajanı için genel çalışma kuralları

Aşağıdaki kurallar her aşamadaki prompt ile birlikte kullanılmalıdır:

- Önce mevcut dosyaları, işletim sistemini ve proje yapısını incele; var olmayan dosyaların var olduğunu varsayma.
- İşe başlamadan önce ilgili aşamanın hedefini ve değiştireceğin dosyaları kısaca belirt.
- Tüm uygulamayı tek yanıtta yazmaya çalışma. Bir aşamayı tamamla, test et ve sonuçlarını raporla.
- Gereksinimleri belirsiz olan hesaplama kurallarını açıkça işaretle; gizlice farklı iş kuralı uygulama.
- Kod modüler, tip açıklamalı ve yorumlar yalnızca gerekli yerlerde olacak şekilde yazılmalı.
- Girdi kontrolünü yalnızca UI üzerinde bırakma; domain katmanında da doğrula.
- Her aşamada ilgili testleri çalıştır. Başarısız test varsa başarı iddiasında bulunma; hatayı gider veya net biçimde bildir.
- Bir aşamada dosya yapısını gereksiz yere baştan yazma. Mevcut kullanıcı kodunu izinsiz silme.
- Çıktı dosyalarını gerçek örnek verilerle oluştur ve biçimsel sonuçlarını kontrol et.
- Windows `.exe` üretiminin macOS'ta doğrudan tamamlanabildiğini varsayma; uygun Windows derleme/test ortamı kullan.
- Aşama sonunda: değişen dosyaları, çalıştırılan komutları, test sonuçlarını, kalan işleri ve belirsiz kararları listele.

---

# 18. Aşamalı geliştirme prompt'ları

Aşağıdaki prompt'lar sırayla kullanılmalıdır. Her prompt'u kendi aşaması için kodlama ajanına ayrı bir mesaj olarak gönderin; ajan önceki aşamanın proje dosyalarını ve bu ana şartnameyi okuyarak devam etmelidir.

## Prompt 0 — Şartnameyi analiz et ve uygulama planı oluştur

```text
Bu projede ana gereksinim belgesi “Teklif Şablonu Projesi – Gereksinim ve Teknik Şartname”dir. Belgenin tamamını oku. İlk aşamada henüz kod yazma.

Görevlerin:
1. Gereksinimleri işlevsel modüllere ayır.
2. Bölüm 0'daki onaylı kararları kesin gereksinim kabul et. Bölüm 16'daki teknik varsayımları ve henüz sağlanmamış firma/logo girdilerini ayrı göster; yuvarlama, varsayılan koşullar, iskonto sınırı ve satır doğrulaması gibi onaylanmış kararları yeniden açık soru olarak sunma.
3. Önerilen Python + PySide6 + SQLite mimarisini, PDF/Excel üretim stratejisini ve katman sınırlarını değerlendir.
4. Aşamalı bir uygulama planı, dosya yapısı, bağımlılık listesi ve test planı çıkar.
5. Hangi firma bilgileri/logoların kullanıcıdan beklendiğini belirt; ilk şirket bilgilerini referans PDF ile, ikinci şirketi eksik/placeholder olarak ele al; tek marka logosu göster/gizle seçeneği olduğunu unutma.
6. Her aşama için somut “tamamlandı” ölçütleri belirle.

İstek: Şartnamede bulunmayan ticari kuralları kendin icat etme. Öneri sunduğunda bunu “öneri” olarak işaretle. Çıktında plan, riskler, sorulması gereken kararlar ve ilk uygulanacak küçük adımı ver. Henüz dosya değiştirme.
```

## Prompt 1 — Proje iskeleti ve geliştirme ortamı

```text
Onaylanan plana göre yalnızca proje iskeletini kur. Ana şartnameye ve genel ajan kurallarına uy.

Gereksinimler:
- Python projesi, bağımlılık dosyası ve README hazırla.
- PySide6 ile açılan basit bir ana pencere oluştur.
- domain, services, storage, ui, config, assets ve tests katmanlarını ayır.
- Şirket/marka bilgileri ve varlık yolları için örnek yapılandırma ekle; gerçek olmayan VKN/adres uydurma, eksik bilgileri TODO/placeholder olarak göster.
- Uygulama verilerinin kullanıcıya ait yazılabilir OS veri dizininde saklanacağı bir yardımcı fonksiyon oluştur.
- Test komutunu ve uygulamayı geliştirme ortamında çalıştırma komutunu README'ye yaz.
- Windows paketleme detaylarını şimdilik yalnızca planla; bu aşamada `.exe` üretmeyi zorunlu tutma.

Kabul: Uygulama açılır; klasör yapısı ve başlangıç testleri çalışır; bağımlılıklar açıkça listelenir. İlgisiz modülleri henüz uygulama.
```

## Prompt 2 — Domain modelleri, doğrulama ve hesaplama motoru

```text
Ana şartnameye göre UI'dan bağımsız domain modellerini, girdileri doğrulama fonksiyonlarını ve hesaplama motorunu uygula. Bu aşamada PDF/Excel tasarlama.

Uygula:
- Offer, OfferItem, OfferSection ve gerekli enum/değer nesneleri.
- Para birimi teklif genelinde TRY/USD/EUR. Miktar birimi teklif genelinde Adet veya Litre seçilir; bütün ürün satırları bu birimi kullanır.
- Türkçe virgüllü sayı girdisini güvenli şekilde parse et; hesaplarda Decimal kullan.
- Ürün kodu/açıklaması maksimum 64 karakter.
- Miktar ve palet pozitif; en fazla iki ondalık basamak.
- Birim fiyat negatif olamaz.
- KDV oranı teklif genelinde tek değerdir; yüzde olarak, negatif olamaz ve en fazla iki ondalık basamaklıdır.
- Satır iskontosu oran veya sabit tutar olarak seçilir; oran en fazla 2, sabit tutar en fazla 2 ondalık basamak ve tam kısmında en az 10 basamak destekler.
- Toplam = fiyatlandırma miktarı × birim fiyat.
- İskontolu toplam ve KDV dahil toplamı ana şartnamedeki formüllerle hesapla.
- İskonto satır toplamını aşarsa önerilen doğrulama hatasını üret.
- Hesaplama sonuçlarını test edilebilir saf fonksiyonlardan üret; UI nesnelerine bağımlı olma.

Hesaplama: `Toplam Tutar = Miktar × Birim Fiyat`. Oran iskontosu 0–100 aralığında ve en fazla iki ondalık basamaktır; sabit tutar iskontosu satır toplamını aşamaz. Satır iskontosu, ardından ortak KDV oranı uygulanır. Genel toplam özeti ara toplamı, etkinse toplam iskontoyu/iskontolu ara toplamı ve KDV etkinse toplam KDV/KDV dâhil genel toplamı içermelidir. Yuvarlama politikasını merkezi tek fonksiyonda uygula: Decimal + ROUND_HALF_UP, iki ondalık ve genel toplamlar görünür satır toplamlarıyla mutabık.

Birim testleri yaz: geçerli/geçersiz sayılar, Türkçe karakterler, sınırlar, oran/miktar iskontosu, KDV ve birleşik formüller. Testleri çalıştır, sonuçları raporla.
```

## Prompt 3 — Dinamik PySide6 kullanıcı arayüzü

```text
Ana şartnameye göre teklif oluşturma arayüzünü uygula. Hesaplama kurallarını yeniden UI içine yazma; Prompt 2'deki domain modüllerini kullan.

Arayüzde:
1. Şirket seçimi (Endemiks Tarım Ticaret A.Ş. / Endemiks Gıda LTD. ŞTİ.).
2. Teklif tarihi; alıcı metin alanı; teklif genel para birimi radio button grubu; teklif-geneli miktar birimi (Adet/Litre); KDV etkinse tek KDV oranı; marka logosu göster/gizle checkbox'ı.
3. Sütun seçim alanı. PDF/Excel için zorunlu sütunlar kapatılamasın. Sütun sırası ana şartnamedeki sırada sabit olsun.
4. KDV kapatıldığında KDV oranı alanını ve KDV dâhil toplam seçeneğini devre dışı bırak. İskonto Türü kapatıldığında İskonto Miktarı ve iskontolu toplam seçeneklerini devre dışı bırak.
5. Dinamik ürün tablosu: ürün satırı ekle/sil/kopyala. Her satırın girdisi ve hesaplaması diğer satırlardan bağımsız olsun; miktar birimi teklif genelinde, KDV oranı teklif genelinde seçilsin. Genel toplam özeti (iskonto öncesi ara toplam; aktifse iskonto, iskontolu ara toplam; aktifse toplam KDV ve KDV dâhil genel toplam) arayüzde de görünür olsun.
6. İskonto açıksa tür seçimi satır bazında olsun. Kullanıcı ihtiyacına uygun radyo düğmeleri kullan veya daha kompakt bir satır içi seçim gerekirse bunu gerekçelendir. Miktar birimi tüm satırlar için ortaktır; satır başına birim seçimi gösterme.
7. Alt ticari koşul checkbox'ları ve metin alanları; karakter limitleri uygula. Ek Alan zengin metin düzenleyici içermeli (kalın/italik/altı çizili, paragraf, madde işaretli/numaralı liste) ve biçimlendirme yapısı veri modeline aktarılmalı.
8. Teklif arşivi ekranı: kayıtlı teklifleri listele/ara/aç; bir teklifi kopyalayarak yeni numarayla yeni teklif oluştur; kaynak teklifi değiştirme.
9. Hesaplanan değerleri mümkün olduğunca anlık göster; satır hatalarını görünür kıl.

Görsel yaklaşım: sade ve profesyonel; Türkçe etiketler; uzun formda kaydırılabilir alan; okunaklı genişlikler. Bu aşamada PDF/Excel çıktılarını tamamlamak zorunda değilsin, ama UI verisini tek bir Offer modeline dönüştürebilmelisin.

Kabul: Tabloda satır ekleme/silme; sütun bağımlılıkları; domain doğrulaması ve hesaplamalar çalışır. UI testleri veya en azından test edilebilir yardımcı fonksiyonlar ekle. Uygulamayı açıp temel akışı manuel kontrol et.
```

## Prompt 4 — SQLite kaydı ve teklif numarası

```text
Yerel SQLite veri katmanını ana şartnameye göre uygula. Veritabanı uygulama kurulum klasörüne değil, işletim sistemindeki kullanıcı veri dizinine yazılmalı.

Gereksinimler:
- Offer, OfferItem, OfferSection ve gereken teklif ayarlarını kalıcı olarak sakla.
- Veri erişimini repository katmanından yap; UI'da SQL sorgusu yazma.
- Şema sürümü/migration yaklaşımı ekle.
- Teklif numarasını seçili teklif tarihine göre YYYYMMDD-NNN formatında üret.
- Her tarih için yerel sayaç sakla; aynı bilgisayardaki numarayı benzersiz tut; sayaç artırma ve teklif kaydını tek transaction içinde güvenli yap. Farklı bilgisayarlarda numara çakışması ilk sürüm için kabul edilir ve belgelendirilir.
- Teklif bir kez numara aldıktan sonra aynı kaydın PDF/Excel yeniden üretiminde numara değişmesin. Kayıtlı teklifler arşivden açılabilmeli ve kopyalanabilmeli; kopya yeni teklif numarasıyla yeni kayıt olmalı, orijinal değişmemeli.
- Günlük sıra üç hane ile başlasın; 999'u geçince kesilmeden devam etsin.
- Hata durumlarında rollback ve kullanıcıya anlaşılır hata mesajı kullan.

Birim/integrasyon testleri: farklı tarihler, aynı tarih içinde ardışık kayıt, yeniden açılışta sayaç devamı, aynı teklifi yeniden dışa aktarma mantığı ve başarısız kayıt rollback'i. Gelecekte SQLite yerine başka veri tabanı bağlanabilmesi için repository protokolünü açık tut.
```

## Prompt 5 — PDF üretimi ve sayfa düzeni

```text
PDF dışa aktarımını uygula. Ana şartname ve kullanıcının sağladığı PDF örneği görsel referans alınmalı; örnekteki vergi/iletişim bilgileri farklı şirket için otomatik kullanılmamalı.

Gereksinimler:
- Teklif numarası, teklif tarihi, alıcı ve seçilen şirketin ticari/vergisel bilgileri. Marka logosu yalnızca kullanıcı görünür seçtiğinde eklenir; şirket logosu sağlanmadıkça varsayılmaz.
- Marka logosu yalnızca kullanıcı görünür seçtiğinde.
- Ürün sütunları ana şartnamedeki sıralamada; seçilmeyen ve tamamen boş sütunlar çıkarılmış durumda.
- Satır bazında hesaplanan değerler Offer modelinden alınmalı.
- Koşul alanları yalnızca etkinse gösterilmeli; Ek Alan etiketsiz, diğer alanlar kalın etiketle.
- Türkçe karakter destekleyen font göm. Uzun metin ve ürün açıklamalarını satır kaydır.
- Sütun genişliklerini değerlendirerek dikey A4 veya yatay A4 yönünü otomatik seç.
- Çok sayfalı tabloda başlık satırını tekrarla; yazıyı aşırı küçültme; çakışma ve sayfa dışına taşmayı önle.
- Masaüstü dizinini işletim sisteminden bul, dosyayı `<TeklifNo>.pdf` adıyla kaydet.
- Dosya varsa sessizce üzerine yazma; kullanıcıya seçenek sun.
- Şirket ve marka görsellerini koddaki metinsel sabitler yerine assets/config üzerinden yükle.

Test/QA:
- Türkçe karakter ve uzun metin içeren örnek PDF oluştur.
- 4 sütunlu ve çok sütunlu örnek oluştur; sayfa yönünü doğrula.
- Birden fazla ürün ve birden fazla sayfa senaryosunu dene.
- PDF'yi render ederek görsel kontrol yap; taşan, kesilen veya üst üste binen içerik olmamalı.
- Kullanıcı tarafından sağlanmamış dipnotları otomatik ekleme. İmza alanları yapılandırılabilir olsun.
```

## Prompt 6 — Düzenlenebilir Excel üretimi

```text
Excel dışa aktarımını uygula. PDF ile aynı kaydedilmiş Offer modelini kullan; veriyi yeniden ve farklı kurallarla hesaplama.

Gereksinimler:
- `<TeklifNo>.xlsx` adıyla Windows Masaüstü'ne kaydet.
- PDF'deki ürün satırı sırasını ve sütun sırasını koru; seçilmeyen/tamamen boş sütunları çıkar.
- Hücreler düzenlenebilir olmalı. Para tutarları ve oranlar gerçek sayısal hücreler ve uygun sayı biçimleriyle yazılmalı.
- Toplam Tutar ve etkin hesaplanmış sütunlar için taşınabilir Excel formülleri kullan; kullanıcı miktar/fiyat/iskonto değerlerini veya teklif-geneli KDV oranını değiştirdiğinde sonuçlar güncellenebilsin.
- Seçilen firma/teklif metadatası, marka görsel tercihi ve etkin koşullar dosyada yer alsın.
- Metin kaydırma, sütun genişliği, satır yüksekliği, başlık biçimi, yazdırma alanı ve yön ayarlarını yap.
- Dosya mevcutsa kullanıcıya sessiz olmayan çakışma seçeneği sun.

Test et: Excel dosyasını yeniden aç, örnek hücre değer ve formüllerini kontrol et; formüllerin referansları seçili sütunlara göre doğru olsun. Kullanıcı manuel düzenleme yapınca PDF otomatik değişmez; bunu README'de belirt.
```

## Prompt 7 — Bütünleştirme, doğrulama ve kabul testleri

```text
Şimdi UI, domain, SQLite, PDF ve Excel modüllerini tek akışta bütünleştir. Ana şartnamedeki kabul kriterlerini maddeler halinde ele al.

Yapılacaklar:
- UI girişlerinden Offer modeli oluştur.
- Domain doğrulaması başarılı değilse kaydetme veya çıktı üretimini durdur ve ilgili hatayı göster.
- Teklif ilk kaydedildiğinde numara tahsis et; aynı teklif tekrar dışa aktarılırken numarayı koru.
- Aynı Offer modelinden PDF ve Excel üret.
- Sütun bağımlılıklarını, tüm zorunlu sütunları, tamamen boş sütun davranışını ve koşul checkbox'larını doğrula.
- Veritabanı hatası, yazılamayan masaüstü, dosya adı çakışması ve eksik logo gibi olumsuz durumları ele al.
- Unit/integration testleri çalıştır; kritik yol için manuel test senaryosu ve test verisi hazırla.
- En az şu örnekleri üret: tek ürün; iki ürün; çok sütun seçimi; iskonto oranı; sabit iskonto; KDV; iskontolu+KDV; uzun açıklama/koşullar; Türkçe karakter; farklı şirket seçimi.

Eksik veya başarısız testleri açıkça listele. Test edilmemiş bir özelliği çalışıyor olarak bildirme. Görsel kontrollerin sonuçlarını da raporla.
```

## Prompt 8 — Windows `.exe` paketleme ve temiz ortam testi

```text
Uygulamayı Windows dağıtımı için paketlemeye hazırla. Önce ortamın Windows olup olmadığını kontrol et. macOS üzerinde Windows `.exe` paketinin hazır olduğunu varsayma; uygun Windows VM/PC veya Windows CI ortamı kullan.

Gereksinimler:
- PyInstaller yapılandırması oluştur.
- Şirket logoları, marka görseli, fontlar, PDF şablonları ve gerekli kaynak dosyalarının pakete eklendiğini doğrula.
- SQLite veri tabanının kurulum klasöründe değil kullanıcı veri dizininde oluştuğunu doğrula.
- Kısayol/çalışma dizini farklı olduğunda göreli yol hataları oluşmamalı.
- Bir Windows ortamında `.exe` açılışı, teklif oluşturma, PDF ve Excel dışa aktarma, yeniden açılışta numara sayacı ve Türkçe karakterleri test et.
- Temiz bir Windows hesabında ya da temiz sanal ortamda test et; geliştirme bilgisayarına özgü dosya yolları kullanılmasın.
- Derleme adımları, gereken komutlar, bağımlılıklar ve sürüm bilgilerini README'ye ekle.

Kabul: Windows paketinin gerçek ortamda test sonuçları raporlanır. Sadece macOS'taki kod testlerinden hareketle Windows paketinin çalıştığı iddia edilmez.
```

## Prompt 9 — Son kod incelemesi ve devredilebilir dokümantasyon

```text
Ürünü bitmiş kabul etmeden önce tüm projeyi ana şartnameye karşı denetle.

Kontrol et:
- Hesaplama mantığı UI katmanında kopyalanmış mı?
- SQLite SQL'i UI içine dağılmış mı?
- Şirket verileri, VKN/adresler veya logo yolları koda gömülmüş mü?
- Teklif numarası atomik mi ve kayıtlı teklif yeniden dışa aktarılınca değişmiyor mu?
- Türkçe karakter, ondalık virgül, 64/3000/10000 karakter limitleri test edilmiş mi?
- PDF ve Excel sütun sıraları aynı mı; tamamen boş sütun politikası tutarlı mı?
- PDF sayfa yönü, çok sayfalı çıktı, tekrarlanan başlıklar ve uzun metinler incelenmiş mi?
- Excel'deki hesaplamalar gerçek formül mü; dosya açılınca hesaplanabiliyor mu?
- SQLite dosyası ve tüm kullanıcı verileri güncelleme sırasında korunuyor mu?
- Kullanıcı dostu hata mesajları, dosya çakışması ve başarısız kayıt senaryoları var mı?

README'yi şu bölümlerle tamamla: kurulum, macOS geliştirme, testleri çalıştırma, Windows derleme, uygulama/veri dosyalarının konumları, yedek alma, bilinen sınırlamalar, yerel numara çakışması riski ve gelecekte merkezi veri tabanına geçiş. Tüm testleri yeniden çalıştır ve sonuçları raporla. Gerçekten test edilmemiş noktaları açıkça işaretle.
```

---

## 19. İlk geliştirme için önerilen sıralama

1. Prompt 0 ile mimari planı ve dosya yapısını oluştur; burada onaylanmış iş kurallarını tekrar tartışmaya açma.
2. Prompt 1–2 ile proje iskeletini ve hesaplama kurallarını testlerle sabitle.
3. Prompt 3 ile kullanıcı arayüzü ve dinamik ürün satırlarını oluştur.
4. Prompt 4 ile yerel kayıt, arşiv ve tarih bazlı teklif numaralandırmasını tamamla.
5. Prompt 5–6 ile PDF/Excel çıktıları üret ve görsel olarak kontrol et.
6. Prompt 7–9 ile bütünleştir, test et, dokümante et ve Windows `.exe` oluştur.

**Kritik ilke:** Önce doğru hesaplama ve veri modeli; sonra görsel cilalama. PDF tasarımını erkenden örnek veriyle prototiplemek faydalıdır ancak hesaplama kurallarıyla aynı kod içinde birbirine karıştırılmamalıdır.
