"""QR platba (formát SPAYD, který čtou české bankovní aplikace)."""
import re
import unicodedata
from io import BytesIO

import qrcode
import qrcode.image.svg


def _ascii(text):
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()


def spayd(iban, castka_halere, vs, zprava=""):
    iban = re.sub(r"\s+", "", iban or "").upper()
    if not re.fullmatch(r"CZ\d{22}", iban):
        return None
    casti = ["SPD*1.0", f"ACC:{iban}", f"AM:{castka_halere // 100}.{castka_halere % 100:02d}", "CC:CZK",
             f"X-VS:{vs}"]
    if zprava:
        casti.append("MSG:" + re.sub(r"[*]", " ", _ascii(zprava))[:60])
    return "*".join(casti)


def qr_svg(text):
    """SVG jako řetězec (vkládá se do stránky, žádný externí obrázek)."""
    img = qrcode.make(text, image_factory=qrcode.image.svg.SvgPathImage, box_size=10, border=2)
    buf = BytesIO()
    img.save(buf)
    svg = buf.getvalue().decode()
    return svg[svg.index("<svg"):]          # bez XML hlavičky, vkládá se přímo do HTML
