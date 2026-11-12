"""Administrace pro obsluhu e-shopu (mamka) a správce (Matyáš)."""
import json
import re
import secrets
import unicodedata
from datetime import datetime, timedelta

from flask import (Blueprint, abort, current_app, flash, redirect, render_template, request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

from .ceny import kc
from .db import db, nast, ted, uloz_nast, zapis_audit
from .fotky import SpatnaFotka, uloz_produktovou, uloz_vzornik
from .katalog import KATEGORIE, RADY, publikovat
from .pomocne import csrf_token, ip, over_csrf, prekroceno, prihlasen, prihlaseny, zapis_pokus
from .web import STAVY, souhrn_objednavky_html

bp = Blueprint("admin", __name__, url_prefix="/admin", template_folder="templates", static_folder="static")

MIN_HESLO = 10
_ATRAPA = []


def _atrapa():
    if not _ATRAPA:
        _ATRAPA.append(generate_password_hash(secrets.token_hex(16)))
    return _ATRAPA[0]


@bp.before_request
def _csrf():
    if request.method == "POST":
        over_csrf()


@bp.context_processor
def _globalni():
    u = prihlaseny()
    nove = db().execute("SELECT COUNT(*) FROM objednavka WHERE stav = 'nova'").fetchone()[0] if u else 0
    poptavky = db().execute("SELECT COUNT(*) FROM poptavka WHERE stav = 'nova'").fetchone()[0] if u else 0
    return {"csrf_token": csrf_token, "uzivatel": u, "kc": kc, "STAVY": STAVY,
            "pocet_novych": nove, "pocet_poptavek": poptavky}


def _kdo():
    u = prihlaseny()
    return u["login"] if u else f"anonym {ip()}"


def _po_zmene(akce, detail=""):
    """Zapsat do záznamu změn a znovu postavit web."""
    zapis_audit(_kdo(), akce, detail)
    db().commit()
    ok, zprava = publikovat()
    if not ok:
        current_app.logger.error("publikace selhala: %s", zprava)
        flash("Uloženo, ale web se nepodařilo přestavět. Dejte vědět Matyášovi.", "chyba")


def _slug(text, existujici):
    zaklad = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    zaklad = re.sub(r"[^a-z0-9]+", "-", zaklad).strip("-")[:60] or "polozka"
    slug, i = zaklad, 2
    while slug in existujici:
        slug, i = f"{zaklad}-{i}", i + 1
    return slug


def _halere(text, nazev="Cena"):
    """'590', '590,50', '1 290 Kč' → haléře; prázdné → None."""
    t = re.sub(r"[\s ]|Kč", "", str(text or "")).replace(",", ".")
    if not t:
        return None
    if not re.fullmatch(r"\d{1,7}(\.\d{1,2})?", t):
        raise ValueError(f"{nazev}: napište částku v korunách, např. 590 nebo 590,50.")
    return round(float(t) * 100)


def _na_kc(halere):
    if halere is None:
        return ""
    return str(halere // 100) if halere % 100 == 0 else f"{halere / 100:.2f}".replace(".", ",")


# ---------------------------------------------------------------- přihlášení
@bp.route("/prihlaseni", methods=["GET", "POST"])
def prihlaseni():
    if prihlaseny():
        return redirect(url_for("admin.prehled"))
    chyba = None
    if request.method == "POST":
        login = request.form.get("login", "").strip().lower()[:60]
        heslo = request.form.get("heslo", "")
        if prekroceno("prihlaseni-ip", ip(), 10, 900) or prekroceno("prihlaseni-login", login, 5, 900):
            chyba = "Příliš mnoho nepovedených pokusů. Zkuste to prosím za 15 minut."
        else:
            u = db().execute("SELECT * FROM uzivatel WHERE login = ? AND aktivni = 1", (login,)).fetchone()
            if u and u["heslo"]:
                spravne = check_password_hash(u["heslo"], heslo)
            else:
                # i pro neexistujícího uživatele počítáme hash, ať se z doby odpovědi nedá poznat, kdo existuje
                check_password_hash(_atrapa(), heslo)
                spravne = False
            if spravne:
                session.clear()
                session.permanent = bool(request.form.get("zapamatovat"))
                session["uid"], session["ver"] = u["id"], u["verze_hesla"]
                csrf_token()
                db().execute("UPDATE uzivatel SET posledni_prihlaseni = ? WHERE id = ?", (ted(), u["id"]))
                zapis_audit(u["login"], "přihlášení", ip())
                db().commit()
                zapis_pokus("prihlaseni-login", login, uspech=True)
                dalsi = request.args.get("dalsi", "")
                return redirect(dalsi if dalsi.startswith("/admin") and "//" not in dalsi else url_for("admin.prehled"))
            zapis_pokus("prihlaseni-ip", ip())
            zapis_pokus("prihlaseni-login", login)
            chyba = "Přihlašovací jméno nebo heslo nesedí."
    return render_template("admin/prihlaseni.html", chyba=chyba)


@bp.post("/odhlasit")
def odhlasit():
    session.clear()
    return redirect(url_for("admin.prihlaseni"))


@bp.route("/nastavit-heslo/<token>", methods=["GET", "POST"])
def nastavit_heslo(token):
    if not re.fullmatch(r"[A-Za-z0-9_-]{30,60}", token):
        abort(404)
    u = db().execute("SELECT * FROM uzivatel WHERE nastavovaci_token = ? AND aktivni = 1", (token,)).fetchone()
    if u is None or (u["token_plati_do"] or "") < ted():
        return render_template("admin/zprava.html", nadpis="Odkaz už neplatí",
                               text="Požádejte Matyáše o nový odkaz pro nastavení hesla."), 404
    chyba = None
    if request.method == "POST":
        h1, h2 = request.form.get("heslo", ""), request.form.get("heslo2", "")
        chyba = _kontrola_hesla(h1, h2, u["login"])
        if not chyba:
            db().execute("UPDATE uzivatel SET heslo = ?, verze_hesla = verze_hesla + 1, nastavovaci_token = NULL,"
                         " token_plati_do = NULL WHERE id = ?", (generate_password_hash(h1), u["id"]))
            zapis_audit(u["login"], "nastavení hesla odkazem")
            db().commit()
            flash("Heslo je nastavené. Přihlaste se.", "ok")
            return redirect(url_for("admin.prihlaseni"))
    return render_template("admin/nastavit_heslo.html", u=u, chyba=chyba)


def _kontrola_hesla(h1, h2, login):
    if h1 != h2:
        return "Hesla se neshodují."
    if len(h1) < MIN_HESLO:
        return f"Heslo musí mít aspoň {MIN_HESLO} znaků. Klidně celou větu, třeba „Kunžak má nejlepší bundy“."
    if login.lower() in h1.lower() or h1.lower() in ("mpkral1234", "1234567890", "heslo12345"):
        return "Tohle heslo je moc snadné na uhodnutí."
    return None


@bp.route("/ucet", methods=["GET", "POST"])
@prihlasen()
def ucet():
    u = prihlaseny()
    chyba = None
    if request.method == "POST" and request.form.get("akce") == "jmeno":
        jmeno = " ".join(request.form.get("jmeno", "").split())[:60]
        if not jmeno:
            flash("Jméno nesmí být prázdné.", "chyba")
        else:
            db().execute("UPDATE uzivatel SET jmeno = ? WHERE id = ?", (jmeno, u["id"]))
            zapis_audit(u["login"], "změna jména", jmeno)
            db().commit()
            flash("Jméno je uložené.", "ok")
        return redirect(url_for("admin.ucet"))
    if request.method == "POST":
        if not check_password_hash(u["heslo"], request.form.get("stare", "")):
            chyba = "Současné heslo nesedí."
        else:
            chyba = _kontrola_hesla(request.form.get("heslo", ""), request.form.get("heslo2", ""), u["login"])
        if not chyba:
            db().execute("UPDATE uzivatel SET heslo = ?, verze_hesla = verze_hesla + 1 WHERE id = ?",
                         (generate_password_hash(request.form["heslo"]), u["id"]))
            zapis_audit(u["login"], "změna hesla")
            db().commit()
            session["ver"] = u["verze_hesla"] + 1
            flash("Heslo je změněné. Ostatní zařízení se odhlásila.", "ok")
            return redirect(url_for("admin.prehled"))
    return render_template("admin/ucet.html", chyba=chyba)


# ---------------------------------------------------------------- přehled
@bp.get("/")
@prihlasen()
def prehled():
    firma = nast("firma", {})
    upozorneni = []
    bez_ceny = db().execute("SELECT nazev FROM produkt WHERE viditelny = 1 AND (cena IS NULL OR cena = 0)").fetchall()
    neovereno = db().execute("SELECT nazev FROM produkt WHERE viditelny = 1 AND overeno = 0").fetchall()
    if bez_ceny:
        upozorneni.append(f"{len(bez_ceny)} produktů nemá cenu (na webu „Cena na dotaz“).")
    if neovereno:
        upozorneni.append(f"{len(neovereno)} produktů má neověřené technické údaje (materiál, gramáž, norma).")
    if not firma.get("iban"):
        upozorneni.append("Chybí číslo účtu (IBAN) v Nastavení, bez něj se zákazníkům neukáže QR platba.")
    objednavky = db().execute("SELECT * FROM objednavka ORDER BY id DESC LIMIT 8").fetchall()
    return render_template("admin/prehled.html", upozorneni=upozorneni, objednavky=objednavky,
                           zakaznik=lambda o: json.loads(o["zakaznik"]))


@bp.post("/publikovat")
@prihlasen()
def publikovat_rucne():
    ok, zprava = publikovat()
    zapis_audit(_kdo(), "ruční publikace", "ok" if ok else zprava[:500])
    db().commit()
    flash("Web je aktualizovaný." if ok else "Web se nepodařilo přestavět. Dejte vědět Matyášovi.", "ok" if ok else "chyba")
    return redirect(url_for("admin.prehled"))


# ---------------------------------------------------------------- objednávky
@bp.get("/objednavky")
@prihlasen()
def objednavky():
    stav = request.args.get("stav", "")
    if stav and stav not in STAVY:
        abort(404)
    q = "SELECT * FROM objednavka" + (" WHERE stav = ?" if stav else "") + " ORDER BY id DESC LIMIT 500"
    seznam = db().execute(q, (stav,) if stav else ()).fetchall()
    return render_template("admin/objednavky.html", seznam=seznam, stav=stav,
                           zakaznik=lambda o: json.loads(o["zakaznik"]))


@bp.route("/objednavky/<cislo>", methods=["GET", "POST"])
@prihlasen()
def objednavka(cislo):
    o = db().execute("SELECT * FROM objednavka WHERE cislo = ?", (cislo,)).fetchone()
    if o is None:
        abort(404)
    if request.method == "POST":
        stav = request.form.get("stav", o["stav"])
        if stav not in STAVY:
            abort(400)
        poznamka = request.form.get("interni_poznamka", "")[:4000]
        db().execute("UPDATE objednavka SET stav = ?, interni_poznamka = ?, upraveno = ? WHERE id = ?",
                     (stav, poznamka, ted(), o["id"]))
        zapis_audit(_kdo(), f"objednávka {cislo}", f"stav {o['stav']} → {stav}" if stav != o["stav"] else "poznámka")
        db().commit()
        flash("Uloženo.", "ok")
        return redirect(url_for("admin.objednavka", cislo=cislo))
    return render_template("admin/objednavka.html", o=o, z=json.loads(o["zakaznik"]),
                           souhrn=souhrn_objednavky_html(o))


# ---------------------------------------------------------------- poptávky
@bp.get("/poptavky")
@prihlasen()
def poptavky():
    seznam = db().execute("SELECT * FROM poptavka ORDER BY id DESC LIMIT 500").fetchall()
    return render_template("admin/poptavky.html", seznam=seznam)


@bp.post("/poptavky/<int:pid>/stav")
@prihlasen()
def poptavka_stav(pid):
    stav = "vyrizena" if request.form.get("stav") == "vyrizena" else "nova"
    db().execute("UPDATE poptavka SET stav = ? WHERE id = ?", (stav, pid))
    zapis_audit(_kdo(), f"poptávka {pid}", stav)
    db().commit()
    return redirect(url_for("admin.poptavky"))


# ---------------------------------------------------------------- produkty
@bp.get("/produkty")
@prihlasen()
def produkty():
    radky = db().execute("SELECT * FROM produkt ORDER BY poradi, nazev").fetchall()
    fotky = {r["produkt_id"]: r["foto_predni"] for r in db().execute(
        "SELECT produkt_id, foto_predni FROM varianta WHERE id IN (SELECT MIN(id) FROM varianta GROUP BY produkt_id)")}
    pocty = {r[0]: r[1] for r in db().execute("SELECT produkt_id, COUNT(*) FROM varianta GROUP BY produkt_id")}
    podle_kat = {k: [r for r in radky if r["kategorie"] == k] for k in KATEGORIE}
    ostatni = [r for r in radky if r["kategorie"] not in KATEGORIE]
    if ostatni:
        podle_kat["Ostatní"] = ostatni
    return render_template("admin/produkty.html", podle_kat=podle_kat, fotky=fotky, pocty=pocty, na_kc=_na_kc)


def _hodnoty_produktu(p):
    """Hodnoty do formuláře: z databáze (ceny v Kč, hladiny rozepsané do políček)."""
    h = dict(p)
    h["cena"] = _na_kc(p["cena"])
    for i, (od, cena) in enumerate(sorted(json.loads(p["hladiny"] or "{}").items(), key=lambda x: int(x[0])), 1):
        h[f"hl_od_{i}"], h[f"hl_cena_{i}"] = od, _na_kc(cena)
    return h


def _formular_produktu(f):
    data = {k: f.get(k, "").strip()[:m] for k, m in (
        ("nazev", 120), ("kategorie", 60), ("znacka", 60), ("predmet", 120), ("material", 160), ("gramaz", 60),
        ("velikosti", 60), ("popis", 3000), ("pouziti", 300), ("norma", 120))}
    if not data["nazev"]:
        raise ValueError("Vyplňte název produktu.")
    if data["kategorie"] not in KATEGORIE:
        raise ValueError("Vyberte kategorii.")
    data["znacka"] = data["znacka"] or "Ostatní"
    data["cena"] = _halere(f.get("cena"))
    hladiny = {}
    for i in (1, 2):
        od, cena = f.get(f"hl_od_{i}", "").strip(), _halere(f.get(f"hl_cena_{i}"), "Cena pro větší množství")
        if od or cena:
            if not od.isdigit() or int(od) < 2 or cena is None:
                raise ValueError("Množstevní cena: vyplňte počet kusů (od 2) i cenu.")
            hladiny[od] = cena
    data["hladiny"] = json.dumps(hladiny)
    data["overeno"] = 1 if f.get("overeno") else 0
    data["viditelny"] = 1 if f.get("viditelny") else 0
    return data


@bp.route("/produkty/novy", methods=["GET", "POST"])
@prihlasen()
def produkt_novy():
    chyba = None
    if request.method == "POST":
        try:
            data = _formular_produktu(request.form)
            existujici = {r[0] for r in db().execute("SELECT id FROM produkt")}
            pid = _slug(data["nazev"], existujici)
            poradi = (db().execute("SELECT MAX(poradi) FROM produkt").fetchone()[0] or 0) + 10
            db().execute(
                "INSERT INTO produkt (id, nazev, kategorie, znacka, predmet, material, gramaz, velikosti, popis, pouziti,"
                " norma, cena, hladiny, overeno, viditelny, poradi, upraveno) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (pid, data["nazev"], data["kategorie"], data["znacka"], data["predmet"], data["material"],
                 data["gramaz"], data["velikosti"], data["popis"], data["pouziti"], data["norma"], data["cena"],
                 data["hladiny"], data["overeno"], data["viditelny"], poradi, ted()))
            _po_zmene("nový produkt", data["nazev"])
            flash("Produkt je založený. Teď mu přidejte barvu a fotky.", "ok")
            return redirect(url_for("admin.produkt", pid=pid) + "#barvy")
        except ValueError as e:
            chyba = str(e)
    return render_template("admin/produkt.html", p=None, varianty=[], f=request.form.to_dict(), chyba=chyba,
                           KATEGORIE=KATEGORIE, RADY=RADY, na_kc=_na_kc)


@bp.route("/produkty/<pid>", methods=["GET", "POST"])
@prihlasen()
def produkt(pid):
    p = db().execute("SELECT * FROM produkt WHERE id = ?", (pid,)).fetchone()
    if p is None:
        abort(404)
    chyba = None
    if request.method == "POST":
        try:
            data = _formular_produktu(request.form)
            db().execute(
                "UPDATE produkt SET nazev=?, kategorie=?, znacka=?, predmet=?, material=?, gramaz=?, velikosti=?,"
                " popis=?, pouziti=?, norma=?, cena=?, hladiny=?, overeno=?, viditelny=?, upraveno=? WHERE id=?",
                (data["nazev"], data["kategorie"], data["znacka"], data["predmet"], data["material"], data["gramaz"],
                 data["velikosti"], data["popis"], data["pouziti"], data["norma"], data["cena"], data["hladiny"],
                 data["overeno"], data["viditelny"], ted(), pid))
            _po_zmene("úprava produktu", data["nazev"])
            flash("Uloženo a zveřejněno na webu.", "ok")
            return redirect(url_for("admin.produkt", pid=pid))
        except ValueError as e:
            chyba = str(e)
    varianty = db().execute("SELECT * FROM varianta WHERE produkt_id = ? ORDER BY poradi, id", (pid,)).fetchall()
    return render_template("admin/produkt.html", p=p, varianty=varianty,
                           f=request.form.to_dict() if chyba else _hodnoty_produktu(p),
                           chyba=chyba, KATEGORIE=KATEGORIE, RADY=RADY, na_kc=_na_kc)


@bp.post("/produkty/<pid>/posun")
@prihlasen()
def produkt_posun(pid):
    _posun("produkt", "id", pid, request.form.get("smer"))
    _po_zmene("pořadí produktů", pid)
    return redirect(url_for("admin.produkty") + f"#p-{pid}")


@bp.post("/produkty/<pid>/smazat")
@prihlasen()
def produkt_smazat(pid):
    p = db().execute("SELECT nazev FROM produkt WHERE id = ?", (pid,)).fetchone()
    if p is None:
        abort(404)
    db().execute("DELETE FROM produkt WHERE id = ?", (pid,))      # barvy jdou s ním (ON DELETE CASCADE)
    _po_zmene("smazání produktu", p["nazev"])
    flash(f"Produkt {p['nazev']} je smazaný. Staré objednávky ho mají uložený dál.", "ok")
    return redirect(url_for("admin.produkty"))


def _posun(tabulka, sloupec, hodnota, smer, skupina=None):
    """Prohodí pořadí s vedlejší položkou (v rámci skupiny, např. barvy jednoho produktu)."""
    kde = f" WHERE produkt_id = ?" if skupina else ""
    radky = db().execute(f"SELECT {sloupec}, poradi FROM {tabulka}{kde} ORDER BY poradi, {sloupec}",
                         (skupina,) if skupina else ()).fetchall()
    ids = [r[0] for r in radky]
    for i, r in enumerate(radky):                                   # srovnat na 10, 20, 30…
        db().execute(f"UPDATE {tabulka} SET poradi = ? WHERE {sloupec} = ?", ((i + 1) * 10, r[0]))
    i = ids.index(hodnota) if hodnota in ids else -1
    j = i - 1 if smer == "nahoru" else i + 1
    if i >= 0 and 0 <= j < len(ids):
        db().execute(f"UPDATE {tabulka} SET poradi = ? WHERE {sloupec} = ?", ((j + 1) * 10, ids[i]))
        db().execute(f"UPDATE {tabulka} SET poradi = ? WHERE {sloupec} = ?", ((i + 1) * 10, ids[j]))


# ---------------------------------------------------------------- barvy (varianty)
def _fotky_z_formulare(f, soubory, puvodni=None):
    out = {}
    for pole in ("foto_predni", "foto_zadni", "foto_detail"):
        s = soubory.get(pole)
        if s and s.filename:
            cesta, vzornik = uloz_produktovou(s.stream)
            out[pole] = cesta
            if pole == "foto_predni" and not (puvodni and puvodni["vzornik"]):
                out["vzornik"] = vzornik
        elif f.get(f"smazat_{pole}") and pole != "foto_predni":
            out[pole] = None
    s = soubory.get("vzornik")
    if s and s.filename:
        out["vzornik"] = uloz_vzornik(s.stream)
    return out


@bp.post("/produkty/<pid>/barvy")
@prihlasen()
def barva_nova(pid):
    p = db().execute("SELECT * FROM produkt WHERE id = ?", (pid,)).fetchone()
    if p is None:
        abort(404)
    nazev = request.form.get("nazev", "").strip()[:80]
    if not nazev:
        flash("Napište název barvy, např. „modro-černá“.", "chyba")
        return redirect(url_for("admin.produkt", pid=pid) + "#barvy")
    if not (request.files.get("foto_predni") and request.files["foto_predni"].filename):
        flash("Nahrajte aspoň přední fotku.", "chyba")
        return redirect(url_for("admin.produkt", pid=pid) + "#barvy")
    try:
        fotky = _fotky_z_formulare(request.form, request.files)
    except SpatnaFotka as e:
        flash(str(e), "chyba")
        return redirect(url_for("admin.produkt", pid=pid) + "#barvy")
    existujici = {r[0] for r in db().execute("SELECT slug FROM varianta WHERE produkt_id = ?", (pid,))}
    poradi = (db().execute("SELECT MAX(poradi) FROM varianta WHERE produkt_id = ?", (pid,)).fetchone()[0] or 0) + 10
    db().execute("INSERT INTO varianta (produkt_id, slug, nazev, strih, foto_predni, foto_zadni, foto_detail, vzornik,"
                 " poradi) VALUES (?,?,?,?,?,?,?,?,?)",
                 (pid, _slug(nazev, existujici), nazev, request.form.get("strih", "").strip()[:30],
                  fotky.get("foto_predni"), fotky.get("foto_zadni"), fotky.get("foto_detail"), fotky.get("vzornik"),
                  poradi))
    _po_zmene("nová barva", f"{p['nazev']} · {nazev}")
    flash(f"Barva {nazev} je přidaná a je na webu.", "ok")
    return redirect(url_for("admin.produkt", pid=pid) + "#barvy")


@bp.route("/barvy/<int:vid>", methods=["GET", "POST"])
@prihlasen()
def barva(vid):
    v = db().execute("SELECT v.*, p.nazev AS produkt_nazev FROM varianta v JOIN produkt p ON p.id = v.produkt_id"
                     " WHERE v.id = ?", (vid,)).fetchone()
    if v is None:
        abort(404)
    if request.method == "POST":
        nazev = request.form.get("nazev", "").strip()[:80] or v["nazev"]
        try:
            fotky = _fotky_z_formulare(request.form, request.files, puvodni=v)
        except SpatnaFotka as e:
            flash(str(e), "chyba")
            return redirect(url_for("admin.barva", vid=vid))
        sloupce = {"nazev": nazev, "strih": request.form.get("strih", "").strip()[:30],
                   "viditelna": 1 if request.form.get("viditelna") else 0} | fotky
        db().execute("UPDATE varianta SET " + ", ".join(f"{k} = ?" for k in sloupce) + " WHERE id = ?",
                     (*sloupce.values(), vid))
        _po_zmene("úprava barvy", f"{v['produkt_nazev']} · {nazev}")
        flash("Uloženo a zveřejněno na webu.", "ok")
        return redirect(url_for("admin.produkt", pid=v["produkt_id"]) + "#barvy")
    return render_template("admin/barva.html", v=v)


@bp.post("/barvy/<int:vid>/posun")
@prihlasen()
def barva_posun(vid):
    v = db().execute("SELECT * FROM varianta WHERE id = ?", (vid,)).fetchone()
    if v is None:
        abort(404)
    _posun("varianta", "id", vid, request.form.get("smer"), skupina=v["produkt_id"])
    _po_zmene("pořadí barev", v["produkt_id"])
    return redirect(url_for("admin.produkt", pid=v["produkt_id"]) + "#barvy")


@bp.post("/barvy/<int:vid>/smazat")
@prihlasen()
def barva_smazat(vid):
    v = db().execute("SELECT * FROM varianta WHERE id = ?", (vid,)).fetchone()
    if v is None:
        abort(404)
    db().execute("DELETE FROM varianta WHERE id = ?", (vid,))
    _po_zmene("smazání barvy", f"{v['produkt_id']} · {v['nazev']}")
    flash(f"Barva {v['nazev']} je smazaná.", "ok")
    return redirect(url_for("admin.produkt", pid=v["produkt_id"]) + "#barvy")


# ---------------------------------------------------------------- nastavení obchodu
@bp.route("/nastaveni", methods=["GET", "POST"])
@prihlasen()
def nastaveni():
    firma = nast("firma", {})
    doprava, platby = nast("doprava", []), nast("platby", [])
    chyba = None
    if request.method == "POST":
        f = request.form
        try:
            nova_firma = {k: f.get(k, "").strip()[:200] for k in (
                "nazev", "adresa", "okres", "telefon", "telfax", "email", "ico", "dic", "ucet", "iban")}
            nova_firma["iban"] = re.sub(r"\s", "", nova_firma["iban"]).upper()
            if nova_firma["iban"] and not re.fullmatch(r"CZ\d{22}", nova_firma["iban"]):
                raise ValueError("IBAN má tvar CZ a 22 číslic (najdete ho v internetovém bankovnictví).")
            nova_firma["platce_dph"] = bool(f.get("platce_dph"))
            nova_firma["sazba_dph"] = int(f.get("sazba_dph") or 21)
            nova_doprava = []
            for i in range(len(doprava) + 2):
                nazev = f.get(f"d_nazev_{i}", "").strip()[:80]
                if nazev and not f.get(f"d_smazat_{i}"):
                    nova_doprava.append({"id": f.get(f"d_id_{i}") or _slug(nazev, {d["id"] for d in nova_doprava}),
                                         "nazev": nazev, "cena": _halere(f.get(f"d_cena_{i}"), "Cena dopravy") or 0})
            if not nova_doprava:
                raise ValueError("Nechte aspoň jeden způsob dopravy.")
            nove_platby = []
            for i in range(len(platby) + 2):
                nazev = f.get(f"p_nazev_{i}", "").strip()[:80]
                if nazev and not f.get(f"p_smazat_{i}"):
                    jen = [x for x in f.getlist(f"p_jen_{i}") if x in {d["id"] for d in nova_doprava}]
                    platba = {"id": f.get(f"p_id_{i}") or _slug(nazev, {p["id"] for p in nove_platby}),
                              "nazev": nazev, "poplatek": _halere(f.get(f"p_poplatek_{i}"), "Poplatek") or 0}
                    if jen and len(jen) < len(nova_doprava):
                        platba["jen_doprava"] = jen
                    nove_platby.append(platba)
            if not nove_platby:
                raise ValueError("Nechte aspoň jeden způsob platby.")
            uloz_nast("firma", nova_firma)
            uloz_nast("doprava", nova_doprava)
            uloz_nast("platby", nove_platby)
            uloz_nast("objednavky", bool(f.get("objednavky")))
            _po_zmene("nastavení obchodu")
            flash("Nastavení je uložené a web aktualizovaný.", "ok")
            return redirect(url_for("admin.nastaveni"))
        except ValueError as e:
            chyba = str(e)
    return render_template("admin/nastaveni.html", firma=firma, doprava=doprava, platby=platby,
                           objednavky=nast("objednavky", True), chyba=chyba, na_kc=_na_kc)


# ---------------------------------------------------------------- uživatelé a záznam změn (jen správce)
def _nastavovaci_odkaz(uid):
    token = secrets.token_urlsafe(32)
    plati = (datetime.now() + timedelta(days=3)).isoformat(timespec="seconds")
    db().execute("UPDATE uzivatel SET nastavovaci_token = ?, token_plati_do = ? WHERE id = ?", (token, plati, uid))
    return url_for("admin.nastavit_heslo", token=token, _external=True)


@bp.route("/uzivatele", methods=["GET", "POST"])
@prihlasen(role="spravce")
def uzivatele():
    odkaz = None
    if request.method == "POST":
        login = re.sub(r"[^a-z0-9._-]", "", request.form.get("login", "").strip().lower())[:40]
        jmeno = request.form.get("jmeno", "").strip()[:80]
        role = "spravce" if request.form.get("role") == "spravce" else "obsluha"
        if not login or not jmeno:
            flash("Vyplňte jméno i přihlašovací jméno.", "chyba")
        elif db().execute("SELECT 1 FROM uzivatel WHERE login = ?", (login,)).fetchone():
            flash("Takové přihlašovací jméno už existuje.", "chyba")
        else:
            cur = db().execute("INSERT INTO uzivatel (login, jmeno, role, vytvoren) VALUES (?, ?, ?, ?)",
                               (login, jmeno, role, ted()))
            odkaz = _nastavovaci_odkaz(cur.lastrowid)
            zapis_audit(_kdo(), "nový uživatel", f"{login} ({role})")
            db().commit()
    seznam = db().execute("SELECT * FROM uzivatel ORDER BY id").fetchall()
    return render_template("admin/uzivatele.html", seznam=seznam, odkaz=odkaz)


@bp.post("/uzivatele/<int:uid>/odkaz")
@prihlasen(role="spravce")
def uzivatel_odkaz(uid):
    u = db().execute("SELECT * FROM uzivatel WHERE id = ?", (uid,)).fetchone()
    if u is None:
        abort(404)
    odkaz = _nastavovaci_odkaz(uid)
    zapis_audit(_kdo(), "nový odkaz pro heslo", u["login"])
    db().commit()
    seznam = db().execute("SELECT * FROM uzivatel ORDER BY id").fetchall()
    return render_template("admin/uzivatele.html", seznam=seznam, odkaz=odkaz)


@bp.post("/uzivatele/<int:uid>/aktivni")
@prihlasen(role="spravce")
def uzivatel_aktivni(uid):
    if uid == prihlaseny()["id"]:
        flash("Sami sebe vypnout nejde.", "chyba")
        return redirect(url_for("admin.uzivatele"))
    db().execute("UPDATE uzivatel SET aktivni = 1 - aktivni, verze_hesla = verze_hesla + 1 WHERE id = ?", (uid,))
    zapis_audit(_kdo(), "zapnutí/vypnutí uživatele", str(uid))
    db().commit()
    return redirect(url_for("admin.uzivatele"))


@bp.get("/zaznam")
@prihlasen(role="spravce")
def zaznam():
    radky = db().execute("SELECT * FROM audit ORDER BY id DESC LIMIT 500").fetchall()
    return render_template("admin/zaznam.html", radky=radky)
