"""Nahrané fotky: ověřit, že jde opravdu o obrázek, otočit podle EXIF, zmenšit
na čtverec s bílým pozadím (jako ostatní produktové fotky) a uložit pod náhodným
jménem. Původní soubor ani jeho metadata (GPS z telefonu) se neukládají."""
import secrets
from pathlib import Path

from flask import current_app
from PIL import Image, ImageOps

try:                                   # fotky z iPhonu (HEIC)
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:                    # pragma: no cover
    pass

Image.MAX_IMAGE_PIXELS = 60_000_000    # ochrana proti „dekompresní bombě“
STRANA = 640
VZORNIK = 112


class SpatnaFotka(ValueError):
    pass


def _otevri(soubor):
    try:
        im = Image.open(soubor)
        im.load()
    except Exception:
        raise SpatnaFotka("Soubor se nepodařilo otevřít jako obrázek (JPG, PNG, HEIC).")
    if im.format not in ("JPEG", "PNG", "WEBP", "HEIF", "MPO"):
        raise SpatnaFotka("Podporované jsou fotky JPG, PNG, WEBP a HEIC.")
    im = ImageOps.exif_transpose(im)
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        bila = Image.new("RGBA", im.size, (255, 255, 255, 255))
        im = Image.alpha_composite(bila, im)
    return im.convert("RGB")


def _cesta(prefix):
    slozka = Path(current_app.config["DATA_DIR"]) / "nahrane"
    slozka.mkdir(parents=True, exist_ok=True)
    jmeno = f"{prefix}-{secrets.token_hex(6)}.jpg"
    return slozka / jmeno, f"img/nahrane/{jmeno}"


def uloz_produktovou(soubor):
    """Vrátí (cesta_pro_web, cesta_k_vzorniku). Fotka se vejde do čtverce celá."""
    im = _otevri(soubor)
    ctverec = Image.new("RGB", (STRANA, STRANA), (255, 255, 255))
    kopie = im.copy()
    kopie.thumbnail((STRANA, STRANA), Image.LANCZOS)
    ctverec.paste(kopie, ((STRANA - kopie.width) // 2, (STRANA - kopie.height) // 2))
    disk, web = _cesta("foto")
    ctverec.save(disk, "JPEG", quality=88, optimize=True, progressive=True)

    # vzorník látky: výřez kousek pod středem (u bund a kalhot tam bývá látka, ne zip)
    w, h = im.size
    s = max(16, min(w, h) // 8)
    x, y = int(w * 0.33), int(h * 0.55)
    vyrez = im.crop((x, y, x + s, y + s)).resize((VZORNIK, VZORNIK), Image.LANCZOS)
    vdisk, vweb = _cesta("vzornik")
    vyrez.save(vdisk, "JPEG", quality=85)
    return web, vweb


def uloz_vzornik(soubor):
    im = _otevri(soubor)
    s = min(im.size)
    im = im.crop(((im.width - s) // 2, (im.height - s) // 2, (im.width + s) // 2, (im.height + s) // 2))
    im = im.resize((VZORNIK, VZORNIK), Image.LANCZOS)
    disk, web = _cesta("vzornik")
    im.save(disk, "JPEG", quality=85)
    return web
