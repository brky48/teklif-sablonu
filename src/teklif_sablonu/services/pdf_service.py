"""PDF üretim servisi (ReportLab tabanlı profesyonel çıktı üretici)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm, mm
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    Flowable,
    HRFlowable,
    Image as RLImage,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from teklif_sablonu.config import (
    ASSETS_DIR,
    BRANDS_DIR,
    COMPANIES_DIR,
    load_companies,
)
from teklif_sablonu.domain.calculator import calculate_offer
from teklif_sablonu.domain.enums import (
    FIXED_COLUMN_ORDER,
    ColumnKey,
    DiscountType,
    DocumentLanguage,
    PageOrientation,
    SectionKey,
)
from teklif_sablonu.domain.models import Offer, OfferItem
from teklif_sablonu.domain.parsers import format_decimal_tr
from teklif_sablonu.domain.validators import validate_offer
from teklif_sablonu.services.html_utils import qt_html_to_reportlab
from teklif_sablonu.templates.pdf_styles import get_pdf_styles, register_turkish_fonts


class DynamicBottomSpacer(Flowable):
    """Alt imza kutularını teklif sayfasının en altına iten dinamik boşluk akış nesnesi."""

    def __init__(
        self,
        target_flowable: Flowable | None = None,
        element_height: float = 75.0,
        min_gap: float = 12.0,
    ) -> None:
        super().__init__()
        self.target_flowable = target_flowable
        self.element_height = element_height
        self.min_gap = min_gap

    def wrap(self, availWidth: float, availHeight: float) -> tuple[float, float]:
        elem_h = self.element_height
        if self.target_flowable is not None:
            try:
                _, h = self.target_flowable.wrap(availWidth, availHeight)
                if h > 0:
                    elem_h = h
            except Exception:
                pass
        needed = elem_h + self.min_gap
        if availHeight >= needed:
            return 0, availHeight - elem_h
        return 0, availHeight + 1

    def draw(self) -> None:
        pass


class NumberedCanvas(canvas.Canvas):
    """Sayfa numarasını ve alt bilgi tıklanabilir iletişim banner'ını çizen tuval."""

    document_language: DocumentLanguage = DocumentLanguage.TR

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._saved_page_states: list[dict[str, Any]] = []

    def showPage(self) -> None:
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            current_annot_count = getattr(self, "_annotationCount", 0)
            self.__dict__.update(state)
            self._annotationCount = current_annot_count
            self.draw_page_footer(num_pages)
            super().showPage()
        super().save()

    def draw_page_footer(self, page_count: int) -> None:
        self.saveState()
        font_name = register_turkish_fonts()
        self.setFont(font_name, 8)
        self.setFillColor(colors.HexColor("#718096"))
        page_w, _ = self._pagesize

        # Sağ alt: Sayfa X / Y veya Page X / Y
        is_en = getattr(self, "document_language", DocumentLanguage.TR) == DocumentLanguage.EN
        footer_text = f"Page {self._pageNumber} / {page_count}" if is_en else f"Sayfa {self._pageNumber} / {page_count}"
        self.drawRightString(page_w - 36, 18, footer_text)

        # Alt İletişim Bilgileri (Telefon, Web, Mail) - Sola Hizalı Tıklanabilir Linkler
        footer_img_path = ASSETS_DIR / "contact_footer.png"
        if footer_img_path.exists():
            banner_w = 380.0
            banner_h = banner_w * (78.0 / 1024.0)  # ~28.9 pt
            banner_pad_left = (34.0 / 1024.0) * banner_w  # ~12.6 pt
            banner_x = 36.0 - banner_pad_left  # Sol marjin (36 pt) ile ilk ikonun sol kenarı tam hizalı
            banner_y = 12.0

            self.drawImage(
                str(footer_img_path),
                banner_x,
                banner_y,
                width=banner_w,
                height=banner_h,
                preserveAspectRatio=True,
                mask="auto",
            )

            # Tıklanabilir link alanları (sola hizalı banner_x)
            tel_x1 = banner_x + (34.0 / 1024.0) * banner_w
            tel_x2 = banner_x + (294.0 / 1024.0) * banner_w
            self.linkURL("tel:+905310846885", (tel_x1, banner_y, tel_x2, banner_y + banner_h), relative=0)

            web_x1 = banner_x + (365.0 / 1024.0) * banner_w
            web_x2 = banner_x + (635.0 / 1024.0) * banner_w
            self.linkURL("http://www.juresh.com.tr", (web_x1, banner_y, web_x2, banner_y + banner_h), relative=0)

            mail_x1 = banner_x + (702.0 / 1024.0) * banner_w
            mail_x2 = banner_x + (991.0 / 1024.0) * banner_w
            self.linkURL("mailto:info@endemiks.com", (mail_x1, banner_y, mail_x2, banner_y + banner_h), relative=0)

        self.restoreState()


def get_desktop_dir() -> Path:
    """Kullanıcının gerçek Masaüstü (Desktop) dizinini bulur ve döndürür."""
    desktop = Path.home() / "Desktop"
    if desktop.exists() and os.access(desktop, os.W_OK):
        return desktop
    return Path.home()


ORDERED_PRODUCT_KEYS: list[str] = [
    "quality_guarantee",
    "products_list",
    "main_features",
    "production_process",
    "lemonade_extract",
    "orange_juice",
    "pomegranate_juice",
    "lemonade_rtd",
    "bodrum_mandarin_extract",
    "grapefruit_juice",
    "lemon_juice",
    "mulberry_squash",
    "strawberry_squash",
]

PRODUCT_INFO_DATA: dict[str, dict[str, Any]] = {
    "quality_guarantee": {
        "title_tr": "KALİTE & GÜVENCE",
        "title_en": "QUALITY & GUARANTEE",
        "type": "bullets",
        "bullets_tr": [
            "HACCP ve gıda güvenliği standartlarına uygun üretim",
            "Soğuk zincir korumalı sevkiyat",
            "Tüm ürünler kalite kontrol süreçlerinden geçer",
        ],
        "bullets_en": [
            "Production in compliance with HACCP and food safety standards",
            "Cold chain protected shipment",
            "All products undergo quality control processes",
        ],
    },
    "products_list": {
        "title_tr": "ÜRÜNLER:",
        "title_en": "PRODUCTS:",
        "type": "bullets",
        "bullets_tr": [
            "Limonata Özütü",
            "Portakal Suyu",
            "Nar Suyu",
            "Tüketime Hazır Limonata",
            "Bodrum Mandalinatası Özütü",
            "Greyfurt Suyu",
            "Limon Suyu",
            "Karadut Squash",
            "Çilek Squash",
        ],
        "bullets_en": [
            "Lemonade Extract",
            "Orange Juice",
            "Pomegranate Juice",
            "Lemonade Ready To Drink",
            "Bodrum Mandarin Extract",
            "Grapefruit Juice",
            "Lemon Juice",
            "Black Mulberry Squash",
            "Strawberry Squash",
        ],
    },
    "main_features": {
        "title_tr": "Ürünlerin Ana Özellikleri:",
        "title_en": "Main Features of Products:",
        "type": "bullets",
        "bullets_tr": [
            "%100 doğal, katkısız, koruyucusuz",
            "Soğuk sıkım yöntemiyle üretilmiştir",
            "Besin değerleri dondurularak korunur",
            "-18 °C'de depolanır ve taşınır",
        ],
        "bullets_en": [
            "100% natural, additive-free, preservative-free",
            "Produced by cold-press method",
            "Nutritional values preserved by freezing",
            "Stored and transported at -18 °C",
        ],
    },
    "production_process": {
        "title_tr": "Üretim Süreci Bilgisi",
        "title_en": "Production Process Information",
        "type": "paragraph",
        "text_tr": (
            "Nar, limon ve portakal gibi meyveler doğrudan Muğla, Mersin ve çevre bölgelerdeki "
            "çiftçilerden temin edilmektedir. Kapsamlı yıkama ve seçme işlemlerinin ardından, "
            "doğrudan presleme ve mekanik sıkım yoluyla işlenirler. Ürünler, tazeliğini korumak "
            "için -40 °C'de şoklanarak dondurulur ve -18 °C'de depolanır. Hiçbir katkı maddesi "
            "veya koruyucu kullanılmaz. Şişeleme, ambalajlama ve paletleme işlemlerinden önce "
            "kalite kontrolleri ve duyusal analizler gerçekleştirilir."
        ),
        "text_en": (
            "Fruits such as pomegranates, lemons, and oranges are sourced directly from farmers "
            "in Muğla, Mersin, and surrounding regions. After thorough washing and selection, "
            "they are processed by direct pressing and mechanical squeezing. Products are "
            "shock-frozen at -40 °C and stored at -18 °C to preserve freshness. No additives "
            "or preservatives are used. Quality checks and sensory analyses are performed before "
            "bottling, packaging, and palletizing."
        ),
    },
    "lemonade_extract": {
        "title_tr": "LİMONATA ÖZÜTÜ",
        "title_en": "LEMONADE EXTRACT",
        "type": "box",
        "content_tr": (
            "<b>İçindekiler:</b> Limon Suyu, Pancar Şekeri, Portakal Suyu, Limon Kabuğu, Portakal Kabuğu.<br/>"
            "<b>Tüketim Şekli:</b> Donuk olan ürün tamamen eridikten sonra 1 litre Juresh Limonata Özütü’ne "
            "4 litre temiz içme suyu ilave edilerek limonata hazır hale getirilir.<br/><br/>"
            "Ürünlerimiz Muğla, Mersin ve çevre illerdeki çiftçilerimizin emeklerini ve meyvelerin "
            "tazeliğini, aromasını içinde saklar. Pancar şekeri ve doğal meyve içeriği ile geleneksel "
            "lezzeti tüm doğallığı ile sizlere sunar."
        ),
        "content_en": (
            "<b>Ingredients:</b> Lemon Juice, Beet Sugar, Orange Juice, Lemon Peel, Orange Peel.<br/>"
            "<b>Consumption Method:</b> After the frozen product is completely thawed, add 4 liters of "
            "clean drinking water to 1 liter of Juresh Lemonade Extract to prepare lemonade.<br/><br/>"
            "Our products preserve the freshness, aroma, and the hard work of farmers from Muğla, "
            "Mersin, and surrounding provinces. With beet sugar and natural fruit content, it "
            "delivers traditional flavor in its purest form."
        ),
    },
    "orange_juice": {
        "title_tr": "PORTAKAL SUYU",
        "title_en": "ORANGE JUICE",
        "type": "box",
        "content_tr": (
            "<b>İçindekiler:</b> %100 Portakal Suyu.<br/>"
            "<b>Tüketim Şekli:</b> Direkt tüketim için uygundur.<br/><br/>"
            "<b>Premium Portakal Suyu (Berrak & Kristal):</b><br/>"
            "Cancan sıkım teknolojisiyle üretilen bu özel portakal suyu, meyvenin yalnızca öz suyunu değil; "
            "portakal kabuğunda doğal olarak bulunan aromatik kabuk yağlarını da kontrollü biçimde ürüne taşır. "
            "Bu sayede ürün, standart portakal sularından ayrışan daha derin, canlı ve rafine bir aroma profiline "
            "sahip olur. Bu yöntemle elde edilen portakal suyunun rengi berrak ve parlak bir görünüm sunar; görsel netlik, "
            "premium algıyı ilk bakışta güçlendirir. Tat ve görünümde sağlanan bu duyusal bütünlük, ürünü aroma "
            "zenginliği ile kaliteyi aynı anda sunan, üst segmentte konumlanan seçkin bir portakal suyu haline getirir.<br/><br/>"
            "<b>Pres Sıkım Yoğun Portakal Suyu (Yoğun Kıvam ve Lezzet):</b><br/>"
            "Portakalın dış kabuğu ayrılarak pres sıkım yöntemiyle elde edilen Pres Sıkım Yoğun Portakal Suyu, "
            "hafif ve nötr tatlardan ziyade yoğunluk ve belirgin lezzet arayanlar için tasarlanmıştır. Daha konsantre "
            "yapısı ve derin aroma profiliyle, portakalın gerçek karakterini güçlü şekilde hissetmek isteyen kullanıcılar "
            "için üst segment bir tercih sunar.<br/><br/>"
            "<b>Harman Portakal Suyu:</b><br/>"
            "Cancan sıkımın kontrollü, seçici işleme yaklaşımı ile pres sıkımın sağladığı doğal yoğunluk ve gövde, "
            "bu üründe kusursuz bir dengede buluşur. Cancan ve pres sıkım tekniklerinin bilinçli şekilde bir araya "
            "getirilmesiyle, klasik portakal sularının ötesinde, yeni bir kalite seviyesi ortaya çıkarılmıştır. "
            "Bu özel üretim modeli sayesinde ürün; portakalın doğal lif yapısını koruyan posalı dokusu, belirgin doğal "
            "yoğunluğu ve güçlü lezzet karakteriyle öne çıkar. Cancan sisteminin hassas proses kontrolü, pres sıkımın "
            "verdiği derinlik ve dolgunlukla birleşerek, tam kıvamında ve karakterli bir içim sunar. Ortaya çıkan bu ürün, "
            "yoğunluk ve lezzetten ödün vermek istemeyenler için geliştirilmiş; doğallığı, gövdeyi ve aromayı aynı potada "
            "buluşturan üst segment, karakteri net şekilde tanımlanmış bir portakal suyudur."
        ),
        "content_en": (
            "<b>Ingredients:</b> 100% Orange Juice.<br/>"
            "<b>Consumption Method:</b> Suitable for direct consumption.<br/><br/>"
            "<b>Premium Orange Juice (Clear & Crystal):</b><br/>"
            "Produced with Cancan pressing technology, this juice captures not only the fruit’s essence "
            "but also the aromatic peel oils naturally present in orange peel. This creates a deeper, "
            "livelier, and more refined flavor profile than standard orange juices. The result is a "
            "clear, bright appearance that enhances its premium perception.<br/><br/>"
            "<b>Pressed Rich Orange Juice (Dense Texture & Flavor):</b><br/>"
            "Made by removing the peel and pressing the fruit, this juice is designed for those seeking "
            "intensity and bold flavor rather than light or neutral tastes. With a concentrated structure "
            "and deep aroma, it offers a premium choice for experiencing the true character of orange.<br/><br/>"
            "<b>Blended Orange Juice:</b><br/>"
            "Combining Cancan pressing’s controlled precision with the natural density of pressed juice, "
            "this product achieves perfect balance. It preserves pulp and fiber, offering richness and "
            "authenticity. The harmony of Cancan’s process control with pressed juice’s depth creates a "
            "premium orange juice with strong character and full-bodied taste."
        ),
    },
    "pomegranate_juice": {
        "title_tr": "NAR SUYU",
        "title_en": "POMEGRANATE JUICE",
        "type": "box",
        "content_tr": (
            "<b>İçindekiler:</b> %100 Nar Suyu.<br/>"
            "<b>Tüketim Şekli:</b> Direkt tüketim için uygundur.<br/><br/>"
            "Ürünümüz, Muğla bölgesinin iklimi ve toprak yapısıyla karakter kazanan lezzeti ve yüksek "
            "antioksidan değeriyle öne çıkan seçkin narlar kullanılarak üretilmektedir. Hasat sonrası en "
            "kısa sürede üretime alınan narlardan elde edilen nar suyu, donuk muhafaza yöntemiyle tazeliğini "
            "korur; bu sayede meyvenin canlı doğal rengi, yoğun ve dengeli aroması ile yüksek antioksidan "
            "kapasitesi ilk günkü haliyle muhafaza edilir.<br/><br/>"
            "Ürün içeriğinde ilave şeker, katkı maddesi veya koruyucu bulunmaz; narın doğallığı ve saf "
            "karakteri olduğu gibi sunulur."
        ),
        "content_en": (
            "<b>Ingredients:</b> 100% Pomegranate Juice.<br/>"
            "<b>Consumption Method:</b> Suitable for direct consumption.<br/><br/>"
            "Our product is made from select pomegranates grown in Muğla, distinguished by their flavor "
            "shaped by the region’s climate and soil, and their high antioxidant value. The juice is "
            "produced from freshly harvested pomegranates and preserved by frozen storage, maintaining "
            "freshness, vibrant natural color, balanced aroma, and antioxidant capacity as on the first day.<br/><br/>"
            "No added sugar, additives, or preservatives—only the natural purity of pomegranate."
        ),
    },
    "lemonade_rtd": {
        "title_tr": "TÜKETİME HAZIR LİMONATA",
        "title_en": "LEMONADE READY TO DRINK",
        "type": "box",
        "content_tr": "-",
        "content_en": "-",
    },
    "bodrum_mandarin_extract": {
        "title_tr": "BODRUM MANDALİNATASI ÖZÜTÜ",
        "title_en": "BODRUM MANDARIN EXTRACT",
        "type": "box",
        "content_tr": (
            "<b>İçindekiler:</b> Limon Suyu, Pancar Şekeri, Bodrum Mandalina Suyu, Limon Kabuğu, Mandalina Kabuğu.<br/>"
            "<b>Tüketim Şekli:</b> Donuk olan ürün tamamen eridikten sonra 1 litre Juresh Bodrum Mandalinatası "
            "Özütü’ne 3 litre temiz içme suyu ilave edilerek limonata hazır hale getirilir.<br/><br/>"
            "Ürünümüz Muğla, Mersin ve çevre illerdeki çiftçilerimizin emeklerini ve meyvelerin tazeliğini, "
            "ek olarak coğrafi işaretli bodrum mandalinasının aromasını ve kokusunu içinde saklar. "
            "Pancar şekeri ve doğal meyve içeriği ile geleneksel lezzeti tüm doğallığı ile sizlere sunar."
        ),
        "content_en": (
            "<b>Ingredients:</b> Lemon Juice, Beet Sugar, Bodrum Mandarin Juice, Lemon Peel, Orange Peel.<br/>"
            "<b>Consumption Method:</b> Once the frozen product has completely thawed, add 3 liters of clean "
            "drinking water to 1 liter of Juresh Bodrum Mandarin Extract to prepare a refreshing mandarin lemonade.<br/><br/>"
            "Our product preserves the hard work of farmers in Muğla, Mersin, and the surrounding regions, "
            "along with the freshness of their fruits and the distinctive aroma and fragrance of geographically "
            "indicated Bodrum mandarins. Made with beet sugar and natural fruit ingredients, it brings you "
            "the authentic taste of tradition in all its natural goodness."
        ),
    },
    "grapefruit_juice": {
        "title_tr": "GREYFURT SUYU",
        "title_en": "GRAPEFRUIT JUICE",
        "type": "box",
        "content_tr": "-",
        "content_en": "-",
    },
    "lemon_juice": {
        "title_tr": "LİMON SUYU",
        "title_en": "LEMON JUICE",
        "type": "box",
        "content_tr": (
            "<b>İçindekiler:</b> %100 Limon Suyu.<br/><br/>"
            "<b>Premium Limon Suyu (Berrak & Kristal):</b><br/>"
            "Günümüz limon suyu pazarında farklılaşma, yalnızca doğallıkla değil, aynı zamanda berraklık "
            "ve premium algısıyla da sağlanmaktadır. Cancan Premium Limon Suyu (Berrak ve Kristal), yüksek "
            "stabilitesi, kristal berraklığı ve hassas proses kontrolüyle öne çıkar. Tortu içermeyen formülü "
            "sayesinde homojenliğini korur ve karışımların rengini değiştirmez. Bu özellikleriyle kokteyller, "
            "gurme yemekler, barmenler ve fine dining şefleri için ideal bir seçenektir.<br/><br/>"
            "<b>Pulpalı Limon Suyu (Doğal ve Geleneksel):</b><br/>"
            "Limon suyunda gerçek doğallık, meyvenin kendine özgü yapısının korunmasıyla mümkündür. "
            "Pulpalı Limon Suyu (Doğal ve Geleneksel), yüksek posa içeriğini ve yoğun aromasını koruyarak "
            "otantik bir tat ve ev yapımı hissi sunar. Doğal posa içeriği, tüketicilere gerçek meyve "
            "kullanıldığını hissettirir. Güçlü aroması ve belirgin lezzetiyle limonata tarifleri ve "
            "özgün soslar için güvenilir bir tercihtir."
        ),
        "content_en": (
            "<b>Ingredients:</b> 100% Lemon Juice.<br/><br/>"
            "<b>Premium Lemon Juice (Clear & Crystal):</b><br/>"
            "In today’s lemon juice market, differentiation comes not only from naturalness but also "
            "from clarity and premium perception. Cancan Premium Lemon Juice (Clear & Crystal) offers "
            "high stability, crystal clarity, and precise process control. With its sediment-free formula, "
            "it maintains consistency and does not alter the color of mixtures, making it ideal for cocktails, "
            "gourmet dishes, bartenders, and fine-dining chefs.<br/><br/>"
            "<b>Pulpy Lemon Juice (Natural & Traditional):</b><br/>"
            "True naturalness in lemon juice means preserving the fruit’s unique structure. Pulpy Lemon Juice "
            "(Natural & Traditional) retains high pulp content and intense aroma, offering authenticity and "
            "a homemade feel. The natural pulp reassures consumers of real fruit use. Its strong flavor makes "
            "it a reliable choice for lemonade recipes and signature sauces."
        ),
    },
    "mulberry_squash": {
        "title_tr": "KARADUT SQUASH",
        "title_en": "BLACK MULBERRY SQUASH",
        "type": "box",
        "content_tr": (
            "<b>İçindekiler:</b> Şeker, su, karadut püresi, havuç suyu konsantresi, sitrik asit, malik asit, "
            "sodyum benzoat ve aroma ile karıştırılmış karadut suyu.<br/>"
            "<b>Tüketim Şekli:</b> Squash ürün tamamen eridikten sonra 1 litre Juresh Karadut Squash "
            "ürününe 4 litre temiz içme suyu ilave edilerek hazır hale getirilir. Ürün buzlu bardak ile "
            "servis edilecek ise eklenen Juresh Karadut Squash oranı buz oranına kıyasla artırılmalıdır. "
            "Tercihen diğer içeceklere istenen oranlarda ekleme yapılarak tüketilebilir. Karadutlu limonata "
            "içeceği için 350 ml limonata içerisine 50 ml (~5 yemek kaşığı) Karadut Squash eklenerek "
            "tüketimi önerilir."
        ),
        "content_en": (
            "<b>Ingredients:</b> Sugar, Water, Black Mulberry Puree, Carrot Juice Concentrate, Citric Acid, "
            "Malic Acid, Sodium Benzoate, and flavoring mixed with black mulberry juice.<br/>"
            "<b>Consumption Method:</b> After thawing, add 4 liters of clean drinking water to 1 liter of "
            "Juresh Black Mulberry Squash to prepare. If served with ice, increase the squash ratio relative "
            "to the ice. It can also be added to other beverages in desired proportions. For Black Mulberry "
            "Lemonade, add 50 ml (~5 tablespoons) of Black Mulberry Squash to 350 ml of lemonade."
        ),
    },
    "strawberry_squash": {
        "title_tr": "ÇİLEK SQUASH",
        "title_en": "STRAWBERRY SQUASH",
        "type": "box",
        "content_tr": (
            "<b>İçindekiler:</b> Şeker, su, çilek suyu, çilek püresi, havuç suyu konsantresi, sitrik asit, "
            "malik asit, sodyum benzoat ve aroma ile karıştırılmış çilek suyu.<br/>"
            "<b>Tüketim Şekli:</b> Squash ürün tamamen eridikten sonra 1 litre Juresh Çilek Squash "
            "ürününe 4 litre temiz içme suyu ilave edilerek hazır hale getirilir. Ürün buzlu bardak ile "
            "servis edilecek ise eklenen Juresh Çilek Squash oranı buz oranına kıyasla artırılmalıdır. "
            "Tercihen diğer içeceklere istenen oranlarda ekleme yapılarak tüketilebilir. Çilekli limonata "
            "içeceği için 350 ml limonata içerisine 50 ml (~5 yemek kaşığı) Çilek Squash eklenerek "
            "tüketimi önerilir."
        ),
        "content_en": (
            "<b>Ingredients:</b> Sugar, Water, Strawberry Juice, Strawberry Puree, Carrot Juice Concentrate, "
            "Citric Acid, Malic Acid, Sodium Benzoate, and flavoring mixed with strawberry juice.<br/>"
            "<b>Consumption Method:</b> After thawing, add 4 liters of clean drinking water to 1 liter of "
            "Juresh Strawberry Squash to prepare. If served with ice, increase the squash ratio relative to the ice. "
            "It can also be added to other beverages in desired proportions. For Strawberry Lemonade, add 50 ml "
            "(~5 tablespoons) of Strawberry Squash to 350 ml of lemonade."
        ),
    },
}


class PdfService:
    """Teklif verilerinden standartlara uygun profesyonel PDF oluşturan servis."""

    def __init__(self) -> None:
        register_turkish_fonts()
        self.styles = get_pdf_styles()

    def get_default_output_path(self, offer_number: str) -> Path:
        """Varsayılan kayıt yolunu (<Masaüstü>/<TeklifNo>.pdf) döndürür."""
        clean_num = offer_number or "Teklif"
        return get_desktop_dir() / f"{clean_num}.pdf"

    def determine_page_orientation(
        self,
        visible_columns: list[ColumnKey],
        offer: Offer | None = None,
    ) -> tuple[Any, float]:
        """Sütun sayısına veya kullanıcının seçtiği sayfa yönüne göre Dikey veya Yatay A4 yönünü seçer.

        Bölüm 9.2:
        - Kullanıcı tercihi 'portrait' ise: Daima Dikey A4
        - Kullanıcı tercihi 'landscape' ise: Daima Yatay A4
        - 'auto' (varsayılan):
          - 7 veya daha az sütun: Dikey A4 (Portrait, genişlik: 595.27 pt, yazılabilir alan: 523.27 pt).
          - 8 veya daha fazla sütun: Yatay A4 (Landscape, genişlik: 841.89 pt, yazılabilir alan: 769.89 pt).
        """
        if offer is not None:
            if offer.page_orientation == PageOrientation.PORTRAIT or offer.page_orientation == "portrait":
                return A4, 595.27 - 72
            elif offer.page_orientation == PageOrientation.LANDSCAPE or offer.page_orientation == "landscape":
                return landscape(A4), 841.89 - 72

        if len(visible_columns) <= 7:
            return A4, 595.27 - 72  # 36pt sol/sağ marjin = 523.27 pt
        return landscape(A4), 841.89 - 72  # 769.89 pt

    def filter_visible_columns(self, offer: Offer, items: list[OfferItem]) -> list[ColumnKey]:
        """Şartname Bölüm 6.2 kuralına göre gösterilecek sütunları filtreler:

        - Seçilmeyen veya tüm ürün satırlarında tamamen boş kalan sütunlar çıkarılır.
        - Zorunlu sütunlar (Açıklama, Miktar, Fiyat, Toplam) daima korunur.
        - Sabit sıra (FIXED_COLUMN_ORDER) kesinlikle korunur.
        """
        visible: list[ColumnKey] = []

        for col in FIXED_COLUMN_ORDER:
            # Kullanıcı tarafından seçilmemişse atla
            if col not in offer.selected_columns:
                continue

            # Zorunlu sütunlar daima kalır
            if col.is_mandatory:
                visible.append(col)
                continue

            # Diğer opsiyonel sütunlar: En az bir satırda değer var mı kontrol et
            has_value = False
            for it in items:
                if col == ColumnKey.PRODUCT_CODE and it.product_code and it.product_code.strip():
                    has_value = True
                    break
                elif col == ColumnKey.PALLET and it.pallet is not None and it.pallet > 0:
                    has_value = True
                    break
                elif col == ColumnKey.DISCOUNT_TYPE and offer.discount_enabled and it.discount_type != DiscountType.NONE:
                    has_value = True
                    break
                elif col == ColumnKey.DISCOUNT_AMOUNT and offer.discount_enabled and it.discount_value > 0:
                    has_value = True
                    break
                elif col == ColumnKey.VAT and offer.vat_enabled and offer.vat_rate > 0:
                    has_value = True
                    break
                elif col == ColumnKey.TOTAL_DISCOUNTED and offer.discount_enabled:
                    has_value = True
                    break
                elif col == ColumnKey.TOTAL_WITH_VAT and offer.vat_enabled:
                    has_value = True
                    break

            if has_value:
                visible.append(col)

        return visible

    def calculate_column_widths(self, columns: list[ColumnKey], total_width: float) -> list[float]:
        """Sütun türlerine göre ağırlıklı genişlik dağılımı yapar."""
        # Göreceli ağırlıklar
        weights_map = {
            ColumnKey.PRODUCT_CODE: 2.2,
            ColumnKey.DESCRIPTION: 4.8,
            ColumnKey.QUANTITY: 2.0,
            ColumnKey.PALLET: 1.8,
            ColumnKey.UNIT_PRICE: 2.4,
            ColumnKey.DISCOUNT_TYPE: 2.0,
            ColumnKey.DISCOUNT_AMOUNT: 2.4,
            ColumnKey.VAT: 1.5,
            ColumnKey.TOTAL_AMOUNT: 2.6,
            ColumnKey.TOTAL_DISCOUNTED: 2.7,
            ColumnKey.TOTAL_WITH_VAT: 2.7,
        }

        total_weight = sum(weights_map.get(col, 2.0) for col in columns)
        unit_width = total_width / total_weight
        return [weights_map.get(col, 2.0) * unit_width for col in columns]

    def generate_pdf(
        self,
        offer: Offer,
        output_path: Path | str | None = None,
    ) -> Path:
        """Verilen Offer modelinden referans şablona uygun PDF belgesi üretir."""
        # 0. Domain seviyesinde kuralları doğrula
        validation = validate_offer(offer)
        validation.raise_if_invalid()

        if output_path is None:
            output_path = self.get_default_output_path(offer.offer_number)
        else:
            output_path = Path(output_path)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        valid_items = offer.get_valid_items()
        item_calcs, totals = calculate_offer(offer)

        # 1. Sayfa Yönü ve Genişliği Belirle
        visible_cols = self.filter_visible_columns(offer, valid_items)
        page_size, usable_width = self.determine_page_orientation(visible_cols, offer=offer)

        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=page_size,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=45,
        )

        flowables: list[Any] = []

        # ── 1. ÜST BÖLÜM (Header: Logolar, Teklif No/Tarih ve Şirket Bilgileri) ──
        header_table = self._build_header(offer, usable_width)
        flowables.append(header_table)
        flowables.append(Spacer(1, 10))

        # ── 2. ÜRÜN TABLOSU (Çok sayfada repeatRows=1 ile başlık tekrarı) ──
        items_table = self._build_items_table(offer, valid_items, item_calcs, visible_cols, usable_width)
        flowables.append(items_table)
        flowables.append(Spacer(1, 10))

        # ── 3. GENEL TOPLAM ÖZETİ (Bölüm 8.5) ──
        totals_table = self._build_totals_table(offer, totals, usable_width)
        flowables.append(totals_table)
        flowables.append(Spacer(1, 10))

        # ── 4. TİCARİ KOŞULLAR (Bölüm 7.6) ──
        conditions_block = self._build_conditions(offer, usable_width)
        if conditions_block:
            flowables.append(conditions_block)

        # ── 5. İMZA ALANLARI (Sayfanın en altına itilmiş) ──
        signature_table = self._build_signatures(offer, usable_width)
        flowables.append(DynamicBottomSpacer(target_flowable=signature_table, min_gap=12.0))
        flowables.append(signature_table)

        # ── 6. HAZIR ŞABLONLAR (Opsiyonel Yeni Sayfa) ──
        has_ready_templates = (
            offer.template_packaging_info
            or offer.template_storage_conditions
            or (offer.template_product_info and bool(offer.template_product_info_items))
        )
        if has_ready_templates:
            flowables.append(PageBreak())
            template_elements = self._build_ready_templates(offer, usable_width)
            flowables.extend(template_elements)

        # PDF oluştur
        class OfferNumberedCanvas(NumberedCanvas):
            document_language = offer.document_language

        doc.build(flowables, canvasmaker=OfferNumberedCanvas)
        return output_path

    def _build_header(self, offer: Offer, usable_width: float) -> Table:
        """Üst bölümü (Ortalanmış şirket logosu, altında sol: marka logosu, sağ: teklif no/tarih ve şirket adresi) oluşturur."""
        # Şirket bilgilerini bul
        companies = load_companies()
        company = next((c for c in companies if c.id == offer.company_id), companies[0])
        is_en = offer.document_language == DocumentLanguage.EN

        # 1. Şirket Logosu: Sayfanın en üstünde ve yatayda ortalanmış
        comp_logo_path = COMPANIES_DIR / f"{company.id}.png"
        if not comp_logo_path.exists() and company.logo_path:
            comp_logo_path = COMPANIES_DIR / company.logo_path

        if comp_logo_path.exists():
            top_logo = RLImage(str(comp_logo_path), width=180, height=45)
            top_logo.hAlign = "CENTER"
        else:
            top_logo = Paragraph(company.display_name, self.styles.get("CompanyHeaderCentered", self.styles["BoxTitle"]))

        # 2. Alt Bölüm - Sol: Marka Logosu (Juresh)
        left_elements: list[Any] = []
        if offer.brand_logo_visible:
            brand_logo_path = BRANDS_DIR / "juresh.png"
            if brand_logo_path.exists():
                left_elements.append(RLImage(str(brand_logo_path), width=105, height=50))

        # 2. Alt Bölüm - Sağ: Teklif No / Tarih Kutusu + Şirket Bilgileri
        right_elements: list[Any] = []
        col_w = usable_width / 2.0

        lbl_offer_no = "OFFER NO:" if is_en else "TEKLİF NO:"
        lbl_date = "DATE:" if is_en else "TARİH:"

        # Teklif no ve Tarih kutusu: Sağa tam hizalı ve bir tık küçültülmüş (genişlik 165 pt)
        box_w = 165.0
        box_data = [
            [
                Paragraph(f"<b>{lbl_offer_no}</b> {offer.offer_number or '-'}", self.styles["BoxTitle"]),
            ],
            [
                Paragraph(f"<b>{lbl_date}</b> {offer.offer_date.strftime('%d.%m.%Y')}", self.styles["BoxTitle"]),
            ],
        ]
        box_table = Table(box_data, colWidths=[box_w])
        box_table.setStyle(
            TableStyle([
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#2D3748")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#A0AEC0")),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F7FAFC")),
                ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#FFFFFF")),
            ])
        )
        box_pad = col_w - box_w
        box_wrapper = Table([["", box_table]], colWidths=[box_pad, box_w])
        box_wrapper.setStyle(
            TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ])
        )
        right_elements.append(box_wrapper)
        right_elements.append(Spacer(1, 4))

        # Şirket İletişim / Vergi Bilgileri (sağa yaslı)
        addr_label = getattr(company, "address_label_en", "Headquarters and Factory") if is_en else company.address_label
        lines = [
            f"<b>{addr_label}:</b>",
            *company.address_lines,
            f"{company.tax_office}",
            f"{company.tax_id}",
        ]
        comp_text = "<br/>".join(lines)
        right_elements.append(Paragraph(comp_text, self.styles["CompanyInfo"]))

        # 2 sütunlu, üst satırı SPAN ile birleştirilmiş tek ana başlık tablosu
        col_w = usable_width / 2.0
        header_data = [
            [top_logo, ""],
            [left_elements, right_elements],
        ]
        t = Table(header_data, colWidths=[col_w, col_w])
        t.setStyle(
            TableStyle([
                ("SPAN", (0, 0), (1, 0)),
                ("ALIGN", (0, 0), (1, 0), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (1, 0), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 1), (-1, -1), 0),
            ])
        )
        return t

    def _build_items_table(
        self,
        offer: Offer,
        items: list[OfferItem],
        item_calcs: list[Any],
        columns: list[ColumnKey],
        usable_width: float,
    ) -> Table:
        """Ürünler tablosunu oluşturur (repeatRows=1 ile çok sayfada başlık tekrarı)."""
        col_widths = self.calculate_column_widths(columns, usable_width)
        is_en = offer.document_language == DocumentLanguage.EN

        # 1. Başlık Satırı
        header_row = []
        for col in columns:
            if col == ColumnKey.QUANTITY:
                title = offer.quantity_unit.get_column_header(offer.document_language).upper()
            else:
                title = col.label(offer.document_language).upper()
            header_row.append(Paragraph(f"<b>{title}</b>", self.styles["TableHeader"]))

        table_data = [header_row]

        # 2. Ürün Satırları
        curr_sym = f" {offer.currency_code.symbol}"
        for idx, (item, calc) in enumerate(zip(items, item_calcs)):
            row = []
            for col in columns:
                if col == ColumnKey.PRODUCT_CODE:
                    val = item.product_code or "-"
                    p = Paragraph(val, self.styles["TableCellCenter"])
                elif col == ColumnKey.DESCRIPTION:
                    val = item.description or "-"
                    p = Paragraph(f"<b>{val}</b>", self.styles["TableCellLeft"])
                elif col == ColumnKey.QUANTITY:
                    val = format_decimal_tr(item.quantity)
                    p = Paragraph(val, self.styles["TableCellCenter"])
                elif col == ColumnKey.PALLET:
                    val = format_decimal_tr(item.pallet) if item.pallet else "-"
                    p = Paragraph(val, self.styles["TableCellCenter"])
                elif col == ColumnKey.UNIT_PRICE:
                    val = format_decimal_tr(item.unit_price) + curr_sym
                    p = Paragraph(val, self.styles["TableCellRight"])
                elif col == ColumnKey.DISCOUNT_TYPE:
                    val = item.discount_type.label(offer.document_language) if item.discount_type != DiscountType.NONE else "-"
                    p = Paragraph(val, self.styles["TableCellCenter"])
                elif col == ColumnKey.DISCOUNT_AMOUNT:
                    if item.discount_type == DiscountType.RATE:
                        val = f"%{format_decimal_tr(item.discount_value)}"
                    elif item.discount_type == DiscountType.AMOUNT:
                        val = format_decimal_tr(item.discount_value) + curr_sym
                    else:
                        val = "-"
                    p = Paragraph(val, self.styles["TableCellRight"])
                elif col == ColumnKey.VAT:
                    rate_str = format_decimal_tr(offer.vat_rate, decimal_places=0 if offer.vat_rate % 1 == 0 else 2)
                    p = Paragraph(f"%{rate_str}", self.styles["TableCellCenter"])
                elif col == ColumnKey.TOTAL_AMOUNT:
                    val = format_decimal_tr(calc.line_total) + curr_sym
                    p = Paragraph(f"<b>{val}</b>", self.styles["TableCellRight"])
                elif col == ColumnKey.TOTAL_DISCOUNTED:
                    val = format_decimal_tr(calc.discounted_total) + curr_sym
                    p = Paragraph(f"<b>{val}</b>", self.styles["TableCellRight"])
                elif col == ColumnKey.TOTAL_WITH_VAT:
                    val = format_decimal_tr(calc.total_with_vat) + curr_sym
                    p = Paragraph(f"<b>{val}</b>", self.styles["TableCellRight"])
                else:
                    p = Paragraph("-", self.styles["TableCellCenter"])

                row.append(p)
            table_data.append(row)

        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        table.setStyle(
            TableStyle([
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#1A202C")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F7FAFC")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ])
        )
        return table

    def _build_totals_table(self, offer: Offer, totals: Any, usable_width: float) -> Table:
        """Genel toplam özetini sağa yaslı bir tablo olarak oluşturur."""
        curr_sym = f" {offer.currency_code.symbol}"
        is_en = offer.document_language == DocumentLanguage.EN
        rows: list[list[Any]] = []

        # 1. Ara Toplam (Daima)
        subtotal_lbl = "Subtotal:" if is_en else "Ara Toplam:"
        rows.append([
            Paragraph(subtotal_lbl, self.styles["TotalsTitle"]),
            Paragraph(format_decimal_tr(totals.subtotal) + curr_sym, self.styles["TotalsValue"]),
        ])

        # 2. İskonto
        if offer.discount_enabled:
            disc_lbl = "Total Discount:" if is_en else "Toplam İskonto:"
            disc_sub_lbl = "Subtotal After Discount:" if is_en else "İskonto Sonrası Ara Toplam:"
            rows.append([
                Paragraph(disc_lbl, self.styles["TotalsTitle"]),
                Paragraph(f"-{format_decimal_tr(totals.total_discount)}{curr_sym}", self.styles["TotalsValue"]),
            ])
            rows.append([
                Paragraph(disc_sub_lbl, self.styles["TotalsTitle"]),
                Paragraph(format_decimal_tr(totals.discounted_subtotal) + curr_sym, self.styles["TotalsValue"]),
            ])

        # 3. KDV
        if offer.vat_enabled:
            rate_str = format_decimal_tr(offer.vat_rate, decimal_places=0 if offer.vat_rate % 1 == 0 else 2)
            vat_lbl = f"Total VAT (%{rate_str}):" if is_en else f"Toplam KDV (%{rate_str}):"
            grand_vat_lbl = "<b>GRAND TOTAL (INCL. VAT):</b>" if is_en else "<b>KDV DÂHİL GENEL TOPLAM:</b>"
            rows.append([
                Paragraph(vat_lbl, self.styles["TotalsTitle"]),
                Paragraph(format_decimal_tr(totals.total_vat) + curr_sym, self.styles["TotalsValue"]),
            ])
            rows.append([
                Paragraph(grand_vat_lbl, self.styles["GrandTotalTitle"]),
                Paragraph(f"<b>{format_decimal_tr(totals.grand_total)}{curr_sym}</b>", self.styles["GrandTotalValue"]),
            ])
        else:
            final_total = totals.discounted_subtotal if offer.discount_enabled else totals.subtotal
            grand_lbl = "<b>GRAND TOTAL:</b>" if is_en else "<b>GENEL TOPLAM:</b>"
            rows.append([
                Paragraph(grand_lbl, self.styles["GrandTotalTitle"]),
                Paragraph(f"<b>{format_decimal_tr(final_total)}{curr_sym}</b>", self.styles["GrandTotalValue"]),
            ])

        # Genişlik: 220 pt sağa dayalı
        card_w = 230
        left_pad = usable_width - card_w

        totals_card = Table(rows, colWidths=[120, 110])
        totals_card.setStyle(
            TableStyle([
                ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#CBD5E0")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#EBF8FF")),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ])
        )

        wrapper = Table([["", totals_card]], colWidths=[left_pad, card_w])
        wrapper.setStyle(
            TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ])
        )
        return wrapper

    def _build_conditions(self, offer: Offer, usable_width: float) -> KeepTogether | None:
        """Etkin ticari koşul bölümlerini ve başlıksız tam genişlikli ek alan kutusunu hazırlar."""
        elements: list[Any] = []
        table_rows: list[list[Any]] = []
        add_notes_html: str | None = None

        for sec in offer.sections:
            if not sec.enabled or not sec.text or not sec.text.strip():
                continue

            if sec.section_key == SectionKey.ADDITIONAL_NOTES:
                # Kullanıcı şartı: Ek Alan içinde sabit başlık/yorum olmamalı, sadece girilen zengin metin yer almalı.
                clean_html = qt_html_to_reportlab(sec.text.strip())
                if clean_html:
                    add_notes_html = clean_html
            else:
                label_text = sec.section_key.label(offer.document_language)
                table_rows.append([
                    Paragraph(f"<b>{label_text}:</b>", self.styles["ConditionLabel"]),
                    Paragraph(sec.text.strip(), self.styles["ConditionText"]),
                ])

        if table_rows:
            label_col_w = 120
            text_col_w = usable_width - label_col_w
            cond_table = Table(table_rows, colWidths=[label_col_w, text_col_w])
            cond_table.setStyle(
                TableStyle([
                    ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#1A202C")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F7FAFC")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ])
            )
            elements.append(cond_table)

        # Ek Alan kutusu (Sabit başlıksız, sadece kullanıcının girdiği metin, tam genişlikte kenarlıklı kutu)
        if add_notes_html:
            if table_rows:
                elements.append(Spacer(1, 4))
            notes_table = Table([[Paragraph(add_notes_html, self.styles["ConditionText"])]], colWidths=[usable_width])
            notes_table.setStyle(
                TableStyle([
                    ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#1A202C")),
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFFFFF")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ])
            )
            elements.append(notes_table)

        if not elements:
            return None
        return KeepTogether(elements)

    def _build_signatures(self, offer: Offer, usable_width: float) -> Table:
        """Referans PDF'teki 2 kutulu imza ve onay alanını oluşturur."""
        companies = load_companies()
        company = next((c for c in companies if c.id == offer.company_id), companies[0])
        is_en = offer.document_language == DocumentLanguage.EN

        box_w = (usable_width - 20) / 2.0
        box_h = 75

        # Sol Kutu: Alıcı / Müşteri
        default_recipient = "CUSTOMER APPROVAL / SIGNATURE" if is_en else "MÜŞTERİ ONAY / İMZA"
        recipient_title = offer.recipient_name or default_recipient
        left_content = [
            Paragraph(f"<b>{recipient_title.upper()}</b>", self.styles["SignatureTitle"]),
            Spacer(1, box_h - 22),
        ]

        # Sağ Kutu: Şirket
        right_content = [
            Paragraph(f"<b>{company.display_name}</b>", self.styles["SignatureTitle"]),
            Spacer(1, box_h - 22),
        ]

        sig_data = [[left_content, "", right_content]]
        sig_table = Table(sig_data, colWidths=[box_w, 20, box_w])
        sig_table.setStyle(
            TableStyle([
                ("BOX", (0, 0), (0, 0), 1, colors.HexColor("#1A202C")),
                ("BOX", (2, 0), (2, 0), 1, colors.HexColor("#1A202C")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#FFFFFF")),
                ("BACKGROUND", (2, 0), (2, 0), colors.HexColor("#FFFFFF")),
            ])
        )
        return sig_table

    def _build_ready_templates(self, offer: Offer, usable_width: float) -> list[Any]:
        """Kullanıcının seçtiği hazır şablon tablolarını (Paketleme Bilgileri ve/veya Muhafaza Koşulları) üretir."""
        elements: list[Any] = []
        is_en = offer.document_language == DocumentLanguage.EN

        # 1. Ürün Miktar Bilgileri (PAKETLEME BİLGİLERİ / PACKAGING INFORMATION)
        if offer.template_packaging_info:
            pkg_title = "PACKAGING INFORMATION" if is_en else "PAKETLEME BİLGİLERİ"
            elements.append(Paragraph(f"<b>{pkg_title}</b>", self.styles["TemplateTitle"]))
            elements.append(Spacer(1, 6))

            if is_en:
                pkg_headers = ["Product Size", "Bottles per Shrink Pack", "Shrink Packs", "Bottles per Pallet"]
                pkg_rows = [
                    ["250 Mililiters", "15 Bottles", "210 Packs", "3150 Bottles"],
                    ["1 Liter (Round Bottle)", "9 Bottles", "90 Packs", "810 Bottles"],
                    ["1 Liter (Square Bottle)", "12 Bottles", "70 Packs", "840 Bottles"],
                    ["2 Liters", "6 Bottles", "64 Packs", "384 Bottles"],
                    ["5 Liters", "8x4 Bottles / 4x2 Bottles", "40 Packs", "160 Bottles"],
                ]
                pkg_note = "*The 80 × 120 cm pallet size is used as a reference."
            else:
                pkg_headers = ["Ürün Boyutları", "Paket İçi Şişe Miktarı", "Paket Miktarı", "Paletteki Şişe Miktarı"]
                pkg_rows = [
                    ["250 Mililitre", "15 Adet", "210 Paket", "3150 Adet"],
                    ["1 Litre (Yuvarlak Şişe)", "9 Adet", "90 Paket", "810 Adet"],
                    ["1 Litre (Kare Şişe)", "12 Adet", "70 Paket", "840 Adet"],
                    ["2 Litre", "6 Adet", "64 Paket", "384 Adet"],
                    ["5 Litre", "8x4 Adet / 4x2 Adet", "40 Paket", "160 Adet"],
                ]
                pkg_note = "*80 x 120 cm palet boyutu referans alınmaktadır."

            col_widths = [
                usable_width * 0.34,
                usable_width * 0.22,
                usable_width * 0.22,
                usable_width * 0.22,
            ]

            pkg_data: list[list[Any]] = []
            header_cells = [Paragraph(f"<b>{h}</b>", self.styles["TableHeader"]) for h in pkg_headers]
            pkg_data.append(header_cells)

            for row in pkg_rows:
                row_cells = [
                    Paragraph(f"<b>{row[0]}</b>", self.styles["TableCellLeft"]),
                    Paragraph(row[1], self.styles["TableCellCenter"]),
                    Paragraph(row[2], self.styles["TableCellCenter"]),
                    Paragraph(f"<b>{row[3]}</b>", self.styles["TableCellCenter"]),
                ]
                pkg_data.append(row_cells)

            pkg_table = Table(pkg_data, colWidths=col_widths)
            pkg_table.setStyle(
                TableStyle([
                    ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#1A202C")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F7FAFC")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ])
            )
            elements.append(pkg_table)
            elements.append(Spacer(1, 4))
            elements.append(Paragraph(f"<b>{pkg_note}</b>", self.styles["TemplateNote"]))

        # İki tablo da varsa araya boşluk
        if offer.template_packaging_info and offer.template_storage_conditions:
            elements.append(Spacer(1, 14))

        # 2. Muhafaza Koşulları (MUHAFAZA KOŞULLARI / STORAGE CONDITIONS)
        if offer.template_storage_conditions:
            stg_title = "STORAGE CONDITIONS" if is_en else "MUHAFAZA KOŞULLARI"
            elements.append(Paragraph(f"<b>{stg_title}</b>", self.styles["TemplateTitle"]))
            elements.append(Spacer(1, 6))

            if is_en:
                stg_headers = [
                    "",
                    "LEMONADE EXTRACT",
                    "ORANGE JUICE",
                    "POMEGRANATE JUICE",
                    "LEMONADE READY TO DRINK",
                    "BODRUM MANDARIN EXTRACT",
                    "GRAPEFRUIT JUICE",
                    "LEMON JUICE",
                    "BLACK MULBERRY SQUASH",
                    "STRAWBERRY SQUASH",
                ]
                stg_rows = [
                    ["Shelf Life (Frozen)", "-18°C / 2 Years", "-18°C / 2 Years", "-18°C / 2 Years", "-18°C / 18 Months", "-18°C / 2 Years", "-18°C / 2 Years", "-18°C / 2 Years", "-18°C / 2 Years", "-18°C / 2 Years"],
                    ["Thawing Time", "~12 Hours", "~22 Hours", "~22 Hours", "~20 Hours", "~12 Hours", "~22 Hours", "~22 Hours", "~12 Hours", "~12 Hours"],
                    ["Shelf Life After Thawing", "6 days", "3 days", "2 days", "2 days", "6 days", "3 days", "3 days", "7 days", "7 days"],
                ]
                stg_notes = [
                    "*After thawing, products must be stored at +4°C.",
                    "*Do not refreeze after thawing.",
                ]
            else:
                stg_headers = [
                    "",
                    "LİMONATA ÖZÜTÜ",
                    "PORTAKAL SUYU",
                    "NAR SUYU",
                    "TÜKETİME HAZIR LİMONATA",
                    "BODRUM MANDALİNATASI ÖZÜTÜ",
                    "GREYFURT SUYU",
                    "LİMON SUYU",
                    "KARADUT SQUASH",
                    "ÇİLEK SQUASH",
                ]
                stg_rows = [
                    ["Ürün Raf Ömrü", "-18°C / 2 Yıl", "-18°C / 2 Yıl", "-18°C / 2 Yıl", "-18°C / 18 Ay", "-18°C / 2 Yıl", "-18°C / 2 Yıl", "-18°C / 2 Yıl", "-18°C / 2 Yıl", "-18°C / 2 Yıl"],
                    ["Çözündürme Süresi", "~12 Saat", "~22 Saat", "~22 Saat", "~20 Saat", "~12 Saat", "~22 Saat", "~22 Saat", "~12 Saat", "~12 Saat"],
                    ["Çözündükten Sonra Raf Ömrü", "6 gün", "3 gün", "2 gün", "2 gün", "6 gün", "3 gün", "3 gün", "7 gün", "7 gün"],
                ]
                stg_notes = [
                    "*Ürünler çözündükten sonra buzdolabı sıcaklığında (+4°C’de) muhafaza edilmelidir.",
                    "*Ürün çözündükten sonra tekrar dondurmayınız.",
                ]

            # 10 sütunluk genişlik dağılımı (1 etiket sütunu + 9 ürün sütunu)
            label_col_w = min(82.0, usable_width * 0.17)
            item_col_w = (usable_width - label_col_w) / 9.0
            col_widths = [label_col_w] + [item_col_w] * 9

            stg_th_style = self.styles["TableHeader"].clone("STG_TH", fontSize=5.8, leading=7.2)
            stg_tc_style = self.styles["TableCellCenter"].clone("STG_TC", fontSize=6.2, leading=7.8)
            stg_tl_style = self.styles["TableCellLeft"].clone("STG_TL", fontSize=6.2, leading=7.8)

            stg_data: list[list[Any]] = []
            header_cells = [Paragraph(f"<b>{h}</b>", stg_th_style) for h in stg_headers]
            stg_data.append(header_cells)

            for r in stg_rows:
                r_cells = [Paragraph(f"<b>{r[0]}</b>", stg_tl_style)]
                for val in r[1:]:
                    r_cells.append(Paragraph(val, stg_tc_style))
                stg_data.append(r_cells)

            stg_table = Table(stg_data, colWidths=col_widths)
            stg_table.setStyle(
                TableStyle([
                    ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#1A202C")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F7FAFC")),
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F7FAFC")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 2),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ])
            )
            elements.append(stg_table)
            elements.append(Spacer(1, 4))
            for note in stg_notes:
                elements.append(Paragraph(f"<b>{note}</b>", self.styles["TemplateNote"]))

        # 3. Ürün Bilgileri (Seçilen alt ögeler)
        if offer.template_product_info and offer.template_product_info_items:
            # Önceki hazır şablonlar varsa araya boşluk
            if elements:
                elements.append(Spacer(1, 14))

            has_rendered_product_details_header = False

            for key in ORDERED_PRODUCT_KEYS:
                if key not in offer.template_product_info_items:
                    continue

                item_data = PRODUCT_INFO_DATA.get(key)
                if not item_data:
                    continue

                item_type = item_data["type"]

                if item_type == "bullets":
                    title = item_data["title_en"] if is_en else item_data["title_tr"]
                    bullets = item_data["bullets_en"] if is_en else item_data["bullets_tr"]

                    elements.append(Paragraph(f"<b>{title}</b>", self.styles["TemplateTitle"]))
                    elements.append(Spacer(1, 4))
                    for b in bullets:
                        elements.append(Paragraph(f"&bull;&nbsp;&nbsp;{b}", self.styles["ProductDetailBullet"]))
                    elements.append(Spacer(1, 10))

                elif item_type == "paragraph":
                    title = item_data["title_en"] if is_en else item_data["title_tr"]
                    p_text = item_data["text_en"] if is_en else item_data["text_tr"]

                    elements.append(Paragraph(f"<b>{title}</b>", self.styles["TemplateTitle"]))
                    elements.append(Spacer(1, 4))
                    elements.append(Paragraph(p_text, self.styles["ProductDetailText"]))
                    elements.append(Spacer(1, 10))

                elif item_type == "box":
                    # İlk kutu öncesi "ÜRÜN DETAYLARI" / "PRODUCT DETAILS" başlığı
                    if not has_rendered_product_details_header:
                        header_title = "PRODUCT DETAILS" if is_en else "ÜRÜN DETAYLARI"
                        elements.append(Paragraph(f"<b>{header_title}</b>", self.styles["ProductSectionHeader"]))
                        elements.append(Spacer(1, 6))
                        has_rendered_product_details_header = True

                    box_title = item_data["title_en"] if is_en else item_data["title_tr"]
                    box_content = item_data["content_en"] if is_en else item_data["content_tr"]

                    inner_content = f"<b>{box_title}</b>"
                    if box_content and box_content.strip() != "-":
                        inner_content += f"<br/>{box_content}"
                    else:
                        inner_content += "<br/>-"

                    inner_p = Paragraph(inner_content, self.styles["ProductDetailText"])
                    box_table = Table([[inner_p]], colWidths=[usable_width])
                    box_table.setStyle(
                        TableStyle([
                            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#2D3748")),
                            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFFFFF")),
                            ("TOPPADDING", (0, 0), (-1, -1), 6),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                            ("LEFTPADDING", (0, 0), (-1, -1), 8),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                        ])
                    )
                    elements.append(box_table)
                    elements.append(Spacer(1, 8))

        return elements


