"""Qt zengin metin HTML'ini ReportLab uyumlu basit HTML'e dönüştürme yardımcıları.

Qt'nin QTextEdit.toHtml() çıktısı tam bir HTML belgesidir (<!DOCTYPE>, <html>,
<head>, <style> blokları dahil).  ReportLab'ın Paragraph() sınıfı yalnızca
sınırlı bir HTML alt kümesini destekler: <b>, <i>, <u>, <br/>, <font>, <p>.

Bu modül, Qt HTML'ini temizleyip ReportLab'a güvenle aktarılabilir hale getirir.
"""

from __future__ import annotations

import re
from html import unescape


# ── Derlenen regex kalıpları ──

# DOCTYPE, html, head, meta etiketlerini ve <style>...</style> bloklarını temizle
_DOCTYPE_RE = re.compile(r"<!DOCTYPE[^>]*>", re.IGNORECASE)
_HTML_TAG_RE = re.compile(r"</?html[^>]*>", re.IGNORECASE)
_HEAD_BLOCK_RE = re.compile(r"<head[^>]*>.*?</head>", re.IGNORECASE | re.DOTALL)
_STYLE_BLOCK_RE = re.compile(r"<style[^>]*>.*?</style>", re.IGNORECASE | re.DOTALL)
_BODY_TAG_RE = re.compile(r"</?body[^>]*>", re.IGNORECASE)

# Qt'nin <span style="..."> etiketlerinden biçimlendirme bilgisi çıkarma
_SPAN_STYLE_RE = re.compile(
    r'<span\s+style="([^"]*)">(.*?)</span>',
    re.IGNORECASE | re.DOTALL,
)
_FONT_WEIGHT_BOLD_RE = re.compile(r"font-weight:\s*(bold|[6-9]\d{2})", re.IGNORECASE)
_FONT_STYLE_ITALIC_RE = re.compile(r"font-style:\s*italic", re.IGNORECASE)
_TEXT_DECORATION_UNDERLINE_RE = re.compile(r"text-decoration:\s*underline", re.IGNORECASE)

# Paragraf ve liste etiketleri
_P_OPEN_RE = re.compile(r'<p[^>]*style="[^"]*"[^>]*>', re.IGNORECASE)
_P_OPEN_PLAIN_RE = re.compile(r"<p[^>]*>", re.IGNORECASE)
_P_CLOSE_RE = re.compile(r"</p>", re.IGNORECASE)

# Liste etiketleri
_UL_RE = re.compile(r"<ul[^>]*>", re.IGNORECASE)
_OL_RE = re.compile(r"<ol[^>]*>", re.IGNORECASE)
_UL_OL_CLOSE_RE = re.compile(r"</[uo]l>", re.IGNORECASE)
_LI_OPEN_RE = re.compile(r"<li[^>]*>", re.IGNORECASE)
_LI_CLOSE_RE = re.compile(r"</li>", re.IGNORECASE)

# Bilinmeyen/gereksiz etiketleri kaldırma (izin verilenler dışında)
_ALLOWED_TAGS = {"b", "i", "u", "br", "font", "sub", "sup", "a"}
_UNKNOWN_TAG_RE = re.compile(r"</?([a-zA-Z]+)[^>]*>")

# Boş satır fazlalıklarını temizleme
_MULTI_BR_RE = re.compile(r"(<br\s*/?>){3,}", re.IGNORECASE)
_TRAILING_BR_RE = re.compile(r"(<br\s*/?>)+\s*$", re.IGNORECASE)
_LEADING_BR_RE = re.compile(r"^\s*(<br\s*/?>)+", re.IGNORECASE)


def qt_html_to_reportlab(html: str) -> str:
    """Qt QTextEdit HTML çıktısını ReportLab Paragraph() ile uyumlu basit HTML'e dönüştürür.

    Desteklenen dönüşümler:
    - <style> bloklarını temizler
    - <!DOCTYPE>, <html>, <head>, <body> yapılarını kaldırır
    - <span style="font-weight:bold"> → <b>
    - <span style="font-style:italic"> → <i>
    - <span style="text-decoration:underline"> → <u>
    - <ul>/<ol> listelerini metin tabanlı formata dönüştürür
    - <p> etiketlerini <br/> ile değiştirir
    - Bilinmeyen etiketleri temizler
    """
    if not html or not html.strip():
        return ""

    text = html

    # Eğer metin HTML etiketi içermeyen düz metinse
    if not re.search(r"<[a-zA-Z/!]", text):
        from html import escape
        return escape(text).replace("\r\n", "\n").replace("\n", "<br/>").strip()

    # 1. Yapısal HTML etiketlerini temizle
    text = _DOCTYPE_RE.sub("", text)
    text = _HEAD_BLOCK_RE.sub("", text)
    text = _STYLE_BLOCK_RE.sub("", text)
    text = _HTML_TAG_RE.sub("", text)
    text = _BODY_TAG_RE.sub("", text)

    # 2. Listeleri metin tabanlı formata dönüştür
    text = _convert_lists(text)

    # 3. Qt <span style="..."> etiketlerini ReportLab etiketlerine dönüştür
    text = _convert_spans(text)

    # 4. <p> etiketlerini <br/>'ye dönüştür
    text = _P_OPEN_RE.sub("", text)
    text = _P_OPEN_PLAIN_RE.sub("", text)
    text = _P_CLOSE_RE.sub("<br/>", text)

    # 5. Bilinmeyen etiketleri kaldır
    text = _remove_unknown_tags(text)

    # 6. <br> varyantlarını standart <br/>'ye dönüştür
    text = re.sub(r"<br\s*/?>", "<br/>", text, flags=re.IGNORECASE)

    # 7. Fazla boşluk/satırları temizle
    text = _MULTI_BR_RE.sub("<br/><br/>", text)
    text = _TRAILING_BR_RE.sub("", text)
    text = _LEADING_BR_RE.sub("", text)

    # 8. HTML entity'lerini düzelt
    text = text.replace("&nbsp;", " ")

    return text.strip()


def qt_html_to_plain_text(html: str) -> str:
    """Qt HTML çıktısını düz metne dönüştürür (PDF'te basit metin olarak kullanım için)."""
    if not html or not html.strip():
        return ""

    text = html

    # Yapısal etiketleri temizle
    text = _DOCTYPE_RE.sub("", text)
    text = _HEAD_BLOCK_RE.sub("", text)
    text = _STYLE_BLOCK_RE.sub("", text)
    text = _HTML_TAG_RE.sub("", text)
    text = _BODY_TAG_RE.sub("", text)

    # <br>, </p> → yeni satır
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</p>", "\n", text)

    # Liste öğelerini düz metin formatına çevir
    text = re.sub(r"(?i)<li[^>]*>", "• ", text)
    text = re.sub(r"(?i)</li>", "\n", text)

    # Kalan tüm HTML etiketlerini kaldır
    text = re.sub(r"<[^>]+>", "", text)

    # HTML entity'lerini çöz
    text = unescape(text)
    text = text.replace("&nbsp;", " ")

    # Fazla boş satırları temizle
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def _convert_spans(text: str) -> str:
    """Qt <span style="..."> etiketlerini ReportLab biçimlendirme etiketlerine dönüştürür."""

    def _replace_span(match: re.Match) -> str:
        style = match.group(1)
        content = match.group(2)

        prefix = ""
        suffix = ""

        if _FONT_WEIGHT_BOLD_RE.search(style):
            prefix += "<b>"
            suffix = "</b>" + suffix

        if _FONT_STYLE_ITALIC_RE.search(style):
            prefix += "<i>"
            suffix = "</i>" + suffix

        if _TEXT_DECORATION_UNDERLINE_RE.search(style):
            prefix += "<u>"
            suffix = "</u>" + suffix

        return f"{prefix}{content}{suffix}"

    # Birden fazla geçiş yaparak iç içe span'ları da yakala
    prev = ""
    while prev != text:
        prev = text
        text = _SPAN_STYLE_RE.sub(_replace_span, text)

    return text


def _convert_lists(text: str) -> str:
    """HTML <ul>/<ol> listelerini metin tabanlı formata dönüştürür.

    - <ul> → her <li> önüne "• " ekler
    - <ol> → her <li> önüne "1. ", "2. " gibi numara ekler
    """
    # Önce iç içe olmayan listeleri bul ve dönüştür
    result = text

    # Sırasız liste (ul) dönüşümü
    ul_pattern = re.compile(
        r"<ul[^>]*>(.*?)</ul>",
        re.IGNORECASE | re.DOTALL,
    )
    while ul_pattern.search(result):
        def _replace_ul(match: re.Match) -> str:
            inner = match.group(1)
            items = re.findall(r"<li[^>]*>(.*?)</li>", inner, re.IGNORECASE | re.DOTALL)
            lines = [f"• {_strip_inner_tags(item).strip()}" for item in items if item.strip()]
            return "<br/>".join(lines)

        result = ul_pattern.sub(_replace_ul, result, count=1)

    # Sıralı liste (ol) dönüşümü
    ol_pattern = re.compile(
        r"<ol[^>]*>(.*?)</ol>",
        re.IGNORECASE | re.DOTALL,
    )
    while ol_pattern.search(result):
        def _replace_ol(match: re.Match) -> str:
            inner = match.group(1)
            items = re.findall(r"<li[^>]*>(.*?)</li>", inner, re.IGNORECASE | re.DOTALL)
            lines = [
                f"{idx}. {_strip_inner_tags(item).strip()}"
                for idx, item in enumerate(items, 1)
                if item.strip()
            ]
            return "<br/>".join(lines)

        result = ol_pattern.sub(_replace_ol, result, count=1)

    return result


def _strip_inner_tags(text: str) -> str:
    """Liste öğelerinin içindeki span etiketlerini önceden dönüştürüp temizler."""
    cleaned = _convert_spans(text)
    # p etiketlerini kaldır
    cleaned = _P_OPEN_RE.sub("", cleaned)
    cleaned = _P_OPEN_PLAIN_RE.sub("", cleaned)
    cleaned = _P_CLOSE_RE.sub("", cleaned)
    return cleaned


def _remove_unknown_tags(text: str) -> str:
    """İzin verilen etiketler dışındakileri kaldırır."""

    def _filter_tag(match: re.Match) -> str:
        tag_name = match.group(1).lower()
        if tag_name in _ALLOWED_TAGS:
            return match.group(0)
        return ""

    return _UNKNOWN_TAG_RE.sub(_filter_tag, text)
