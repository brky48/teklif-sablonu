"""html_utils modülü birim testleri."""

import pytest
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph

from teklif_sablonu.services.html_utils import qt_html_to_plain_text, qt_html_to_reportlab


SAMPLE_QT_HTML = """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<html><head><meta name="qrichtext" content="1" /><style type="text/css">
p, li { white-space: pre-wrap; }
hr { height: 1px; border-width: 0; }
li.unchecked::marker { content: "\\2610"; }
li.checked::marker { content: "\\2612"; }
</style></head><body style=" font-family:'.AppleSystemUIFont'; font-size:13pt; font-weight:400; font-style:normal;">
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-weight:700;">Önemli Not:</span> Bu teklif <span style=" font-style:italic;">15 gün</span> süreyle geçerlidir.</p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" text-decoration: underline;">Şartlar:</span></p>
<ul style="margin-top: 0px; margin-bottom: 0px; margin-left: 0px; margin-right: 0px; -qt-list-indent: 1;">
<li style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">Madde bir</li>
<li style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">Madde iki</li>
</ul>
</body></html>"""


def test_qt_html_to_reportlab_cleans_style_and_head():
    result = qt_html_to_reportlab(SAMPLE_QT_HTML)
    # CSS ve doctype kalıntıları kesinlikle bulunmamalı
    assert "white-space" not in result
    assert "DOCTYPE" not in result
    assert "<style" not in result
    assert "</style>" not in result
    assert "marker" not in result

    # Biçimlendirme etiketleri korunmalı
    assert "<b>Önemli Not:</b>" in result
    assert "<i>15 gün</i>" in result
    assert "<u>Şartlar:</u>" in result
    assert "• Madde bir" in result
    assert "• Madde iki" in result


def test_qt_html_to_reportlab_renders_in_paragraph():
    result = qt_html_to_reportlab(SAMPLE_QT_HTML)
    styles = getSampleStyleSheet()
    # ReportLab Paragraph hata vermeden oluşturulabilmeli
    p = Paragraph(result, styles["Normal"])
    assert p is not None


def test_qt_html_to_plain_text():
    result = qt_html_to_plain_text(SAMPLE_QT_HTML)
    assert "Önemli Not: Bu teklif 15 gün süreyle geçerlidir." in result
    assert "• Madde bir" in result
    assert "<" not in result
    assert ">" not in result
    assert "white-space" not in result


def test_qt_html_plain_fallback():
    plain = "Düz metin satır 1\nsatır 2"
    result = qt_html_to_reportlab(plain)
    assert "satır 1" in result
