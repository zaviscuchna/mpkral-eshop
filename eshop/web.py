"""Veřejná část: postavený statický web, objednávka, poptávka, potvrzení objednávky."""
import json
import re
import secrets
from datetime import date
from pathlib import Path

from flask import Blueprint, abort, current_app, jsonify, request, send_from_directory, url_for, Response
from markupsafe import escape

from . import posta
from .ceny import Chyba, kc, spocitej
from .db import db, nast, ted
from .katalog import KOREN
from .platba import qr_svg, spayd
from .pomocne import ip, prekroceno, zapis_pokus

bp = Blueprint("web", __name__)

STAVY = {"nova": "Přijatá", "potvrzena": "Potvrzená", "zaplacena": "Zaplacená", "vyrobena": "Ušitá, připravená",
         "odeslana": "Odeslaná", "vyrizena": "Vyřízená", "zrusena": "Zrušená"}


def _web():
    return Path(current_app.config["DATA_DIR"]) / "web"


# ---------------------------------------------------------------- statický web
@bp.get("/")
def uvod():
    return _stranka_ze_souboru("index")


@bp.get("/<string:jmeno>.html")
def stranka(jmeno):
    return _stranka_ze_souboru(jmeno)


def _stranka_ze_souboru(jmeno):
    if jmeno.startswith("_") or not re.fullmatch(r"[a-z0-9-]+", jmeno):
        abort(404)
    if not (_web() / f"{jmeno}.html").exists():
        abort(404)
    return send_from_directory(_web(), f"{jmeno}.html", max_age=0)


@bp.get("/css/<path:soubor>")
def css(soubor):
    return send_from_directory(KOREN / "css", soubor, max_age=86400)


@bp.get("/js/<path:soubor>")
def js(soubor):
    return send_from_directory(KOREN / "js", soubor, max_age=86400)


@bp.get("/img/<path:soubor>")
def img(soubor):
    if soubor.startswith("nahrane/"):
        return send_from_directory(Path(current_app.config["DATA_DIR"]) / "nahrane", soubor[len("nahrane/"):],
                                   max_age=30 * 86400)
    return send_from_directory(KOREN / "img", soubor, max_age=7 * 86400)


@bp.get("/robots.txt")
def robots():
    if current_app.config["TESTOVACI"]:
        text = "User-agent: *\nDisallow: /\n"
    else:
        text = "User-agent: *\nDisallow: /admin\nDisallow: /api\nDisallow: /objednavka\n"
    return Response(text, mimetype="text/plain")


# ---------------------------------------------------------------- API
def _json_pozadavek(druh, max_za_hodinu):
    """Společné kontroly: JSON, rozumná velikost, původ ze stejného webu, limit pokusů."""
    if not request.is_json or (request.content_length or 0) > 64 * 1024:
        abort(400)
    puvod = request.headers.get("Origin")
    if puvod and puvod.rstrip("/") != request.host_url.rstrip("/"):
        abort(403)
    if prekroceno(druh, ip(), max_za_hodinu, 3600, jen_neuspechy=False):
        return None, (jsonify(chyba="Příliš mnoho pokusů. Zkuste to prosím za hodinu, nebo zavolejte."), 429)
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        abort(400)
    return data, None


def _text(data, klic, max_delka=200, povinne=False, nazev=""):
    hodnota = str(data.get(klic) or "").strip()
    if povinne and not hodnota:
        raise Chyba(f"Vyplňte prosím pole {nazev}.")
    if len(hodnota) > max_delka:
        raise Chyba(f"Pole {nazev} je příliš dlouhé.")
    return hodnota


def _zakaznik(z):
    out = {
        "firma": _text(z, "firma", 160, nazev="Firma"),
        "ico": re.sub(r"\s", "", _text(z, "ico", 20, nazev="IČO")),
        "dic": re.sub(r"\s", "", _text(z, "dic", 20, nazev="DIČ")).upper(),
        "jmeno": _text(z, "jmeno", 120, True, "Jméno a příjmení"),
        "email": _text(z, "email", 160, True, "E-mail"),
        "telefon": _text(z, "telefon", 30, True, "Telefon"),
        "ulice": _text(z, "ulice", 160, True, "Ulice a číslo"),
        "mesto": _text(z, "mesto", 120, True, "Město"),
        "psc": re.sub(r"\s", "", _text(z, "psc", 10, True, "PSČ")),
    }
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}", out["email"]):
        raise Chyba("Zkontrolujte prosím e-mail.")
    if not re.fullmatch(r"\+?[\d ]{9,20}", out["telefon"]):
        raise Chyba("Zkontrolujte prosím telefon.")
    if not re.fullmatch(r"\d{5}", out["psc"]):
        raise Chyba("PSČ má pět číslic.")
    if out["ico"] and not re.fullmatch(r"\d{8}", out["ico"]):
        raise Chyba("IČO má osm číslic.")
    if z.get("jina_adresa"):
        out["dodaci"] = {"jmeno": _text(z, "dod_jmeno", 160, True, "Příjemce"),
                         "ulice": _text(z, "dod_ulice", 160, True, "Ulice a číslo (doručení)"),
                         "mesto": _text(z, "dod_mesto", 120, True, "Město (doručení)"),
                         "psc": re.sub(r"\s", "", _text(z, "dod_psc", 10, True, "PSČ (doručení)"))}
        if not re.fullmatch(r"\d{5}", out["dodaci"]["psc"]):
            raise Chyba("PSČ pro doručení má pět číslic.")
    return out


def _nove_cislo():
    rok = date.today().year
    posledni = db().execute("SELECT cislo FROM objednavka WHERE cislo LIKE ? ORDER BY cislo DESC LIMIT 1",
                            (f"{rok}%",)).fetchone()
    poradi = int(posledni["cislo"][4:]) + 1 if posledni else 1
    return f"{rok}{poradi:04d}"


@bp.post("/api/objednavka")
def objednavka_api():
    data, odmitnuto = _json_pozadavek("objednavka", 10)
    if odmitnuto:
        return odmitnuto
    if data.get("web"):                         # past na roboty: tváříme se, že je hotovo
        return jsonify(odkaz=url_for("web.uvod"))
    if not nast("objednavky", True):
        return jsonify(chyba="Objednávky přes web jsou dočasně vypnuté. Zavolejte nám prosím."), 503
    try:
        if not data.get("souhlas"):
            raise Chyba("Pro odeslání je potřeba souhlas s obchodními podmínkami.")
        zakaznik = _zakaznik(data.get("zakaznik") or {})
        v = spocitej(data.get("polozky"), str(data.get("doprava") or ""), str(data.get("platba") or ""))
        poznamka = _text(data, "poznamka", 2000, nazev="Poznámka")
    except Chyba as e:
        zapis_pokus("objednavka", ip())
        return jsonify(chyba=str(e)), 400

    con = db()
    con.execute("BEGIN IMMEDIATE")                 # číslo objednávky nesmí dostat dva zákazníci
    cislo, token = _nove_cislo(), secrets.token_urlsafe(18)
    con.execute(
        "INSERT INTO objednavka (cislo, token, vytvoreno, zakaznik, polozky, doprava, platba, zbozi, bez_dph, dph,"
        " celkem, sazba_dph, na_dotaz, poznamka, souhlas_kdy) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (cislo, token, ted(), json.dumps(zakaznik, ensure_ascii=False), json.dumps(v["polozky"], ensure_ascii=False),
         json.dumps(v["doprava"], ensure_ascii=False), json.dumps(v["platba"], ensure_ascii=False),
         v["zbozi"], v["bez_dph"], v["dph"], v["celkem"], v["sazba"], v["na_dotaz"], poznamka, ted()))
    con.commit()
    zapis_pokus("objednavka", ip(), uspech=True)
    posta.nova_objednavka(cislo)
    return jsonify(cislo=cislo, odkaz=url_for("web.objednavka", token=token))


@bp.post("/api/poptavka")
def poptavka_api():
    data, odmitnuto = _json_pozadavek("poptavka", 6)
    if odmitnuto:
        return odmitnuto
    if data.get("web"):
        return jsonify(ok=True)
    try:
        p = {k: _text(data, k, m, nazev=n) for k, m, n in (
            ("firma", 160, "Firma"), ("ico", 20, "IČO"), ("osoba", 120, "Kontaktní osoba"), ("tel", 30, "Telefon"),
            ("mail", 160, "E-mail"), ("objednavka", 60, "Číslo objednávky"), ("poznamka", 3000, "Co potřebujete"))}
        if not p["mail"] and not p["tel"]:
            raise Chyba("Napište nám prosím e-mail nebo telefon, ať se můžeme ozvat.")
        if p["mail"] and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}", p["mail"]):
            raise Chyba("Zkontrolujte prosím e-mail.")
    except Chyba as e:
        zapis_pokus("poptavka", ip())
        return jsonify(chyba=str(e)), 400
    db().execute("INSERT INTO poptavka (vytvoreno, firma, ico, osoba, telefon, email, objednavka, poznamka)"
                 " VALUES (?,?,?,?,?,?,?,?)", (ted(), p["firma"], p["ico"], p["osoba"], p["tel"], p["mail"],
                                                p["objednavka"], p["poznamka"]))
    db().commit()
    zapis_pokus("poptavka", ip(), uspech=True)
    posta.nova_poptavka()
    return jsonify(ok=True)


# ---------------------------------------------------------------- potvrzení objednávky
def obal_stranky(titulek, obsah_html, stav=200):
    """Vloží obsah do šablony webu (hlavička, patička). Obsah musí být už ošetřený."""
    sablona = _web() / "_sablona.html"
    if not sablona.exists():
        return Response(obsah_html, status=stav, mimetype="text/html")
    html = sablona.read_text(encoding="utf-8")
    html = html.replace("__MPK_TITULEK__", str(escape(titulek))).replace("<!--MPK_OBSAH-->", obsah_html)
    return Response(html, status=stav, mimetype="text/html")


@bp.get("/objednavka/<token>")
def objednavka(token):
    if not re.fullmatch(r"[A-Za-z0-9_-]{20,40}", token):
        abort(404)
    o = db().execute("SELECT * FROM objednavka WHERE token = ?", (token,)).fetchone()
    if o is None:
        abort(404)
    return obal_stranky(f"Objednávka {o['cislo']}", souhrn_objednavky_html(o, pro_zakaznika=True))


def souhrn_objednavky_html(o, pro_zakaznika=False):
    e = escape
    polozky = json.loads(o["polozky"])
    doprava, platba, z = json.loads(o["doprava"]), json.loads(o["platba"]), json.loads(o["zakaznik"])
    sazba = o["sazba_dph"]
    s_dph = (lambda h: None if h is None else round(h * (100 + sazba) / 100))
    radky = "".join(
        f"<tr><td><b>{e(p['nazev'])}</b><br><span class='mono'>{e(p['varianta'])} · "
        + ", ".join(f"{e(vel)}×{ks}" for vel, ks in p["velikosti"].items())
        + f"</span></td><td>{p['ks']} ks</td><td>{e(kc(s_dph(p['kus'])))}</td><td>{e(kc(s_dph(p['celkem'])) if p['kus'] is not None else 'na dotaz')}</td></tr>"
        for p in polozky)
    firma = nast("firma", {})
    platebni = ""
    if platba.get("id") == "prevod" and o["stav"] not in ("zaplacena", "zrusena"):
        kod = spayd(firma.get("iban"), o["celkem"], o["cislo"], f"Objednavka {o['cislo']}")
        qr = f'<div class="qr">{qr_svg(kod)}</div>' if kod and not o["na_dotaz"] else ""
        ucet = firma.get("ucet") or firma.get("iban") or "číslo účtu vám pošleme e-mailem"
        platebni = (f"<h2 class='nadpis-platby'>Platba převodem</h2><div class='potvrzeni'><dl>"
                    f"<dt>Účet</dt><dd>{e(ucet)}</dd><dt>Variabilní symbol</dt><dd>{e(o['cislo'])}</dd>"
                    f"<dt>Částka</dt><dd>{e(kc(o['celkem']))}</dd></dl>{qr}</div>"
                    + ("<p>U některých položek je cena na dotaz. Než zaplatíte, pošleme vám konečnou částku.</p>"
                       if o["na_dotaz"] else "<p>Výrobu spustíme po připsání platby.</p>"))
    uvod = (f"<p class='mono stav-objednavky'>Stav: {e(STAVY.get(o['stav'], o['stav']))}</p>"
            f"<h1 class='dekujeme'>Děkujeme, objednávka {e(o['cislo'])} je přijatá.</h1>"
            f"<p>Potvrzení a další postup vám pošleme na {e(z.get('email', ''))}. Tuto stránku si můžete uložit.</p>"
            if pro_zakaznika else "")
    souhrn = (f"<div class='souhrn-objednavky souhrn-vpravo'>"
              f"<div><span>Zboží</span><span>{e(kc(s_dph(o['zbozi'])))}</span></div>"
              f"<div><span>Doprava · {e(doprava['nazev'])}</span><span>{e(kc(s_dph(doprava.get('cena') or 0)))}</span></div>"
              + (f"<div><span>Platba · {e(platba['nazev'])}</span><span>{e(kc(s_dph(platba.get('poplatek') or 0)))}</span></div>"
                 if platba.get("poplatek") else f"<div><span>Platba</span><span>{e(platba['nazev'])}</span></div>")
              + (f"<div><span>Bez DPH</span><span>{e(kc(o['bez_dph']))}</span></div>"
                 f"<div><span>DPH {sazba} %</span><span>{e(kc(o['dph']))}</span></div>" if sazba else "")
              + f"<div class='celkem'><span>Celkem</span><span>{e(kc(o['celkem']))}</span></div></div>")
    return (f"{uvod}<table class='hladiny polozky-objednavky'><tr><th>Položka</th><th>Kusů</th>"
            f"<th>Za kus{' s DPH' if sazba else ''}</th><th>Celkem</th></tr>{radky}</table>{souhrn}{platebni}")
