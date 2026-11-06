"""Katalog: první naplnění z data/*.json, export pro generátor a publikace webu.

Veřejný web zůstává statický (build.py). Po každé změně v administraci se data
z databáze vyexportují do JSON a generátor postaví novou kopii webu vedle staré;
teprve když se povede, staré se vymění za nové. Rozbitý build tak web neshodí.
"""
import fcntl
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from flask import current_app

from .db import db, nast, uloz_nast, ted

KOREN = Path(__file__).resolve().parent.parent      # repo: build.py, css, js, img, data
KATEGORIE = ["Kombinézy", "Kalhoty", "Laclové kalhoty", "Bundy a blůzy", "Kraťasy", "Pláště", "Soupravy"]
RADY = ["King", "Klasik", "Riedl", "Polar", "Reflexní", "Ostatní"]
VELIKOSTI = [46, 48, 50, 52, 54, 56, 58, 60, 62, 64, 66]
POHLEDY = [("přední", "foto_predni"), ("zadní", "foto_zadni"), ("detail", "foto_detail")]

VYCHOZI_NASTAVENI = {
    "firma": {"nazev": "Petr Král M+P", "adresa": "Nová 401, 378 62 Kunžak", "okres": "okres Jindřichův Hradec",
              "telefon": "+420 608 982 675", "telfax": "+420 384 399 306", "email": "info@mpkral.cz",
              "ico": "43861431", "dic": "", "platce_dph": True, "sazba_dph": 21,
              "ucet": "", "iban": ""},
    # ceny dopravy a poplatky v haléřích, bez DPH
    "doprava": [
        {"id": "osobni", "nazev": "Osobní odběr v dílně v Kunžaku", "cena": 0},
        {"id": "ppl", "nazev": "PPL, doručení na adresu", "cena": 15000},
    ],
    "platby": [
        {"id": "prevod", "nazev": "Převodem předem (QR platba)", "poplatek": 0},
        {"id": "dobirka", "nazev": "Dobírka", "poplatek": 4000, "jen_doprava": ["ppl"]},
        {"id": "hotove", "nazev": "Hotově nebo kartou při odběru", "poplatek": 0, "jen_doprava": ["osobni"]},
    ],
    "objednavky": True,
}


def naplnit_z_repa(con):
    """Jednorázově převezme katalog z data/katalog.json (fotky zůstávají v repu)."""
    if con.execute("SELECT COUNT(*) FROM produkt").fetchone()[0]:
        return 0
    kat = json.loads((KOREN / "data" / "katalog.json").read_text(encoding="utf-8"))
    for i, r in enumerate(kat):
        con.execute(
            "INSERT INTO produkt (id, nazev, kategorie, znacka, predmet, material, gramaz, velikosti, popis,"
            " pouziti, norma, poradi, upraveno) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (r["id"], r["nazev"], r["kategorie"], r["znacka"], r.get("predmet", ""), r.get("material", ""),
             r.get("gramaz", ""), r.get("velikosti", ""), r.get("popis", ""), r.get("pouziti", ""),
             r.get("norma", ""), (i + 1) * 10, ted()))
        for j, v in enumerate(r["varianty"]):
            f = v.get("fotky", {})
            con.execute(
                "INSERT INTO varianta (produkt_id, slug, nazev, strih, foto_predni, foto_zadni, foto_detail,"
                " vzornik, poradi) VALUES (?,?,?,?,?,?,?,?,?)",
                (r["id"], v["id"], v["nazev"], v.get("strih", ""), f.get("přední") or v.get("hlavni"),
                 f.get("zadní"), f.get("detail"), v.get("vzornik"), (j + 1) * 10))
    for klic, hodnota in VYCHOZI_NASTAVENI.items():
        if con.execute("SELECT 1 FROM nastaveni WHERE klic = ?", (klic,)).fetchone() is None:
            uloz_nast(klic, hodnota, con)
    con.commit()
    return len(kat)


def produkty(jen_viditelne=False):
    """Řady s barvami ve tvaru, jaký čte build.py (ceny v Kč)."""
    q = "SELECT * FROM produkt" + (" WHERE viditelny = 1" if jen_viditelne else "") + " ORDER BY poradi, nazev"
    out = []
    for p in db().execute(q).fetchall():
        varianty = []
        for v in db().execute("SELECT * FROM varianta WHERE produkt_id = ? ORDER BY poradi, id", (p["id"],)):
            fotky = {k: v[sl] for k, sl in POHLEDY if v[sl]}
            varianty.append({"id": v["slug"], "db_id": v["id"], "nazev": v["nazev"], "strih": v["strih"],
                             "fotky": fotky, "hlavni": v["foto_predni"] or next(iter(fotky.values()), ""),
                             "vzornik": v["vzornik"], "viditelna": bool(v["viditelna"])})
        hladiny = json.loads(p["hladiny"] or "{}")
        out.append({k: p[k] for k in ("id", "nazev", "kategorie", "znacka", "predmet", "material", "gramaz",
                                       "velikosti", "popis", "pouziti", "norma")}
                   | {"cena": p["cena"] / 100 if p["cena"] else None,
                      "hladiny": {k: v / 100 for k, v in hladiny.items() if v},
                      "overeno": bool(p["overeno"]), "viditelny": bool(p["viditelny"]),
                      "varianty": varianty})
    return out


def _obchod_pro_web():
    """Nastavení pro generátor: ceny dopravy a plateb v Kč."""
    firma = nast("firma", VYCHOZI_NASTAVENI["firma"])
    return {
        "firma": {k: v for k, v in firma.items() if k not in ("ucet", "iban")},
        "doprava": [dict(d, cena=(d.get("cena") or 0) / 100) for d in nast("doprava", [])],
        "platby": [dict(p, poplatek=(p.get("poplatek") or 0) / 100) for p in nast("platby", [])],
        "objednavky": bool(nast("objednavky", True)),
    }


def publikovat():
    """Postaví web z databáze do DATA_DIR/web. Vrací (ok, zpráva)."""
    data_dir = Path(current_app.config["DATA_DIR"])
    prac = data_dir / "publikace"
    prac.mkdir(parents=True, exist_ok=True)
    with open(prac / ".zamek", "w") as zamek:          # dva workery najednou stavět nesmí
        fcntl.flock(zamek, fcntl.LOCK_EX)
        vstup = prac / "data"
        if vstup.exists():
            shutil.rmtree(vstup)
        vstup.mkdir()
        (vstup / "katalog.json").write_text(json.dumps(produkty(), ensure_ascii=False, indent=1), encoding="utf-8")
        shutil.copy(KOREN / "data" / "meta.json", vstup / "meta.json")
        (vstup / "obchod.json").write_text(json.dumps(_obchod_pro_web(), ensure_ascii=False, indent=1), encoding="utf-8")
        pravni = vstup / "pravni"
        pravni.mkdir()
        for zdroj in (KOREN / "data" / "pravni").glob("*.html"):
            vlastni = nast(f"pravni:{zdroj.stem}")
            (pravni / zdroj.name).write_text(vlastni or zdroj.read_text(encoding="utf-8"), encoding="utf-8")

        novy, web, stary = data_dir / "web.novy", data_dir / "web", data_dir / "web.stary"
        for d in (novy, stary):
            if d.exists():
                shutil.rmtree(d)
        env = dict(os.environ, MPK_DATA=str(vstup), MPK_VYSTUP=str(novy))
        vysledek = subprocess.run([sys.executable, str(KOREN / "build.py")], env=env, cwd=str(KOREN),
                                  capture_output=True, text=True, timeout=120)
        if vysledek.returncode != 0 or not (novy / "index.html").exists():
            return False, (vysledek.stderr or vysledek.stdout)[-1500:]
        if web.exists():
            web.rename(stary)
        novy.rename(web)
        if stary.exists():
            shutil.rmtree(stary)
        return True, "Web je aktualizovaný."
