"""Výpočet ceny objednávky. Jediné místo, kterému se věří: bere ceny z databáze,
z prohlížeče přebírá jen co, v jaké barvě, velikosti a počtu."""
import json

from .db import db, nast
from .katalog import VELIKOSTI

MAX_RADKU = 60
MAX_KUSU = 9999


class Chyba(ValueError):
    """Chyba, kterou je možné ukázat zákazníkovi."""


def povolene_velikosti(kategorie):
    return VELIKOSTI[:-1] if kategorie == "Kraťasy" else VELIKOSTI


def cena_kusu(produkt, ks_rady):
    """Haléře bez DPH za kus podle množstevní hladiny (rozhoduje součet kusů řady)."""
    cena = produkt["cena"]
    if not cena:
        return None
    for od, c in sorted(((int(k), v) for k, v in json.loads(produkt["hladiny"] or "{}").items() if v)):
        if ks_rady >= od:
            cena = c
    return cena


def spocitej(polozky, doprava_id, platba_id):
    if not isinstance(polozky, list) or not polozky:
        raise Chyba("Košík je prázdný.")
    if len(polozky) > MAX_RADKU:
        raise Chyba("V košíku je příliš mnoho položek, rozdělte prosím objednávku.")

    radky, ks_rady = [], {}
    for p in polozky:
        if not isinstance(p, dict):
            raise Chyba("Neplatná položka v košíku.")
        produkt = db().execute("SELECT * FROM produkt WHERE id = ? AND viditelny = 1",
                               (str(p.get("rada_id", "")),)).fetchone()
        if produkt is None:
            raise Chyba("Některý produkt v košíku už v nabídce není. Odeberte ho prosím a zkuste to znovu.")
        varianta = db().execute("SELECT * FROM varianta WHERE produkt_id = ? AND slug = ? AND viditelna = 1",
                                (produkt["id"], str(p.get("varianta_id", "")))).fetchone()
        if varianta is None:
            raise Chyba(f"Barva u produktu {produkt['nazev']} už není k dispozici. Vyberte ji prosím znovu.")
        povolene = {str(v) for v in povolene_velikosti(produkt["kategorie"])}
        velikosti = {}
        for vel, ks in (p.get("velikosti") or {}).items():
            try:
                ks = int(ks)
            except (TypeError, ValueError):
                raise Chyba("Neplatný počet kusů.")
            if str(vel) not in povolene or not 0 <= ks <= MAX_KUSU:
                raise Chyba(f"Neplatná velikost nebo počet u produktu {produkt['nazev']}.")
            if ks:
                velikosti[str(vel)] = ks
        if not velikosti:
            continue
        ks = sum(velikosti.values())
        ks_rady[produkt["id"]] = ks_rady.get(produkt["id"], 0) + ks
        radky.append({"produkt": produkt, "varianta": varianta, "velikosti": velikosti, "ks": ks})
    if not radky:
        raise Chyba("Košík je prázdný.")

    zbozi, na_dotaz, vystup = 0, 0, []
    for r in radky:
        kus = cena_kusu(r["produkt"], ks_rady[r["produkt"]["id"]])
        if kus is None:
            na_dotaz += 1
        celkem = (kus or 0) * r["ks"]
        zbozi += celkem
        vystup.append({"rada_id": r["produkt"]["id"], "nazev": r["produkt"]["nazev"],
                       "varianta_id": r["varianta"]["slug"], "varianta": r["varianta"]["nazev"],
                       "foto": r["varianta"]["foto_predni"], "velikosti": dict(sorted(r["velikosti"].items())),
                       "ks": r["ks"], "kus": kus, "celkem": celkem})

    doprava = next((d for d in nast("doprava", []) if d["id"] == doprava_id), None)
    if doprava is None:
        raise Chyba("Vyberte prosím způsob dopravy.")
    platba = next((x for x in nast("platby", []) if x["id"] == platba_id), None)
    if platba is None or (platba.get("jen_doprava") and doprava["id"] not in platba["jen_doprava"]):
        raise Chyba("Vyberte prosím způsob platby, který jde s touto dopravou.")

    firma = nast("firma", {})
    sazba = int(firma.get("sazba_dph") or 0) if firma.get("platce_dph", True) else 0
    bez_dph = zbozi + (doprava.get("cena") or 0) + (platba.get("poplatek") or 0)
    dph = round(bez_dph * sazba / 100)
    return {"polozky": vystup, "zbozi": zbozi, "doprava": doprava, "platba": platba,
            "bez_dph": bez_dph, "dph": dph, "celkem": bez_dph + dph, "sazba": sazba, "na_dotaz": na_dotaz}


def kc(halere, desetiny=True):
    """1234567 → '12 345,67 Kč' (nezlomitelné mezery)."""
    if halere is None:
        return "na dotaz"
    kc_, hal = divmod(abs(int(halere)), 100)
    cele = f"{kc_:,}".replace(",", " ")
    znak = "−" if halere < 0 else ""
    return f"{znak}{cele},{hal:02d} Kč" if desetiny and hal else f"{znak}{cele} Kč"
