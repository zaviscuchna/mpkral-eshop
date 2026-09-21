#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Vygeneruje staticke stranky nacrtu e-shopu M+P Kral ze souboru data/katalog.json.

Obsah je v HTML natvrdo (funguje i s vypnutym JS). JS resi jen interakci:
prepinani variant a pohledu, sanon poptavky, rozpis velikosti, lupa.
"""
import hashlib
import json
from pathlib import Path

KOREN = Path(__file__).resolve().parent
KAT = json.loads((KOREN / "data" / "katalog.json").read_text(encoding="utf-8"))
META = json.loads((KOREN / "data" / "meta.json").read_text(encoding="utf-8"))

KATEGORIE = ["Kombinézy", "Kalhoty", "Laclové kalhoty", "Bundy a blůzy",
             "Kraťasy", "Pláště", "Soupravy"]
RADY = ["King", "Klasik", "Riedl", "Polar", "Reflexní"]

OTISK = hashlib.md5((KOREN / "css" / "style.css").read_bytes()).hexdigest()[:8]
OTISK_JS = hashlib.md5((KOREN / "js" / "app.js").read_bytes()).hexdigest()[:8]

ADRESA = "Nová 401, 378 62 Kunžak"
TELEFON = "+420 608 982 675"
TELFAX = "+420 384 399 306"
MAIL = "info@mpkral.cz"
ICO = "43861431"


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def zast(text):
    """Zastupny udaj - teckovane podtrzeni + title."""
    return f'<span class="zastupne" title="zástupný údaj — doplní M+P Král">{esc(text)}</span>'


def hlava(titulek, popis, cesta=""):
    return f"""<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(titulek)}</title>
<meta name="description" content="{esc(popis)}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&family=EB+Garamond:ital,wght@0,400;0,500;1,400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{cesta}css/style.css?v={OTISK}">
</head>
<body>
"""


def hlavicka(aktivni="", cesta=""):
    polozky = "".join(
        f'<li><a href="{cesta}katalog.html#{i}" class="{"aktivni" if k == aktivni else ""}">{esc(k)}</a></li>'
        for i, k in enumerate(KATEGORIE))
    return f"""<header class="hlavicka">
  <div class="obal hl-horni">
    <div class="hl-vlevo">
      <button class="hamburger" id="hamburger" aria-label="Menu" aria-expanded="false">Menu</button>
    </div>
    <a class="znacka" href="{cesta}index.html">
      <b>M+P Král</b>
      <span>Výroba pracovních oděvů · Kunžak · od 1993</span>
    </a>
    <div class="hl-vpravo">
      <input class="hledani" type="search" placeholder="Hledat" id="hledani" aria-label="Hledat">
      <a class="sanon-tlacitko" href="{cesta}sanon.html">Šanon <span class="sanon-pocet" data-sanon-pocet>0</span></a>
    </div>
  </div>
  <nav class="hl-dolni">
    <div class="obal">
      <ul class="navigace" id="navigace">{polozky}</ul>
    </div>
  </nav>
</header>
"""


def kota(cislo, nadpis, vpravo="", popis=""):
    p = f"<p>{popis}</p>" if popis else ""
    v = f'<span class="kota-vpravo">{esc(vpravo)}</span>' if vpravo else ""
    return f"""<div class="kota">
  <span class="kota-cislo">{cislo}</span>{v}
  <div><h2>{esc(nadpis)}</h2>{p}</div>
</div>"""


def paticka(cesta=""):
    kat = "".join(f'<li><a href="{cesta}katalog.html#{i}">{esc(k)}</a></li>'
                  for i, k in enumerate(KATEGORIE))
    rady = "".join(f"<li>{esc(r)}</li>" for r in RADY)
    return f"""<footer class="paticka">
  <div class="obal">
    <div class="zdvojena-linka" style="margin-bottom:32px"></div>
    <div class="paticka-mrizka">
      <div><h3>Kategorie</h3><ul>{kat}</ul></div>
      <div><h3>Řady</h3><ul>{rady}</ul></div>
      <div>
        <h3>Kontakt</h3>
        <ul>
          <li>M+P Král — Petr Král</li>
          <li>{esc(ADRESA)}</li>
          <li>okres Jindřichův Hradec</li>
          <li>{esc(TELEFON)}</li>
          <li>{esc(MAIL)}</li>
        </ul>
      </div>
    </div>
    <p class="disclaimer">
      Technické údaje (materiál, gramáž, čísla střihů, normy, lhůty) jsou v tomto náčrtu zástupné.<br>
      Šijeme <span class="kurziva">od roku 1993</span>.
    </p>
  </div>
</footer>
<script src="{cesta}js/app.js?v={OTISK_JS}"></script>
</body>
</html>
"""


def varianta_data(rada, var):
    return esc(json.dumps({
        "rada": rada["nazev"],
        "varianta": var["nazev"],
        "fotky": var["fotky"],
        "strih": var["strih"],
    }, ensure_ascii=False))


def produkt_karta(rada, velka=True):
    """Dlazdice = rada + jeji barvy. Produkt lezi volne na plose, bez ramecku."""
    v0 = rada["varianty"][0]
    predni = v0["fotky"].get("přední") or v0["hlavni"]
    zadni = v0["fotky"].get("zadní")

    if zadni:
        druha = f'<img src="{esc(zadni)}" alt="" loading="lazy" class="skryta" data-zadni>'
        znacka = ""
        prepinac = """<div class="prepinac-pohledu">
        <button type="button" class="aktivni" data-pohled="predni">Přední</button>
        <button type="button" data-pohled="zadni">Zadní</button>
      </div>"""
    else:
        druha = ""
        znacka = '<span class="znacka-pohledu">1 pohled</span>'
        prepinac = ""

    li = []
    for i, var in enumerate(rada["varianty"]):
        st = f'background-image:url({esc(var["vzornik"])})' if var.get("vzornik") else ""
        li.append(f'<li><button type="button" class="vzornik {"aktivni" if i == 0 else ""}" '
                  f'style="{st}" title="{esc(var["nazev"])}" aria-label="{esc(var["nazev"])}" '
                  f'data-varianta="{varianta_data(rada, var)}"></button></li>')
    vzorniky = f'<ul class="vzorniky">{"".join(li)}</ul>'

    pocet = len(rada["varianty"])
    slovo = "barva" if pocet == 1 else ("barvy" if pocet < 5 else "barev")

    return f"""<article class="produkt" data-produkt data-rada="{esc(rada['nazev'])}" data-kategorie="{esc(rada['kategorie'])}" data-znacka="{esc(rada['znacka'])}">
  <a class="produkt-fotka" href="produkt.html?rada={esc(rada['id'])}">
    <img src="{esc(predni)}" alt="{esc(rada['nazev'])} — {esc(v0['nazev'])}" loading="lazy" data-predni>
    {druha}{znacka}{prepinac}
  </a>
  <div class="produkt-telo">
    <div class="produkt-hlava">
      <h3 class="produkt-nazev"><a href="produkt.html?rada={esc(rada['id'])}">{esc(rada['nazev'])}</a></h3>
      <span class="produkt-rada">{esc(rada['znacka'])}</span>
    </div>
    <p class="produkt-mono">{zast(rada['material'])} · {zast(rada['gramaz'])}</p>
    {vzorniky}
    <p class="produkt-rozsah" data-rozsah>{pocet} {slovo} · vel. {zast(rada['velikosti'])}</p>
    <button type="button" class="tl tl-obrys tl-plna" data-otevrit-rozpis>Zapsat počty</button>
    <div class="rozpis-v-karte" data-rozpis>{rozpis_velikosti(rada, kompakt=True)}</div>
  </div>
</article>"""


def rozpis_velikosti(rada, kompakt=False):
    vel = [46, 48, 50, 52, 54, 56, 58, 60, 62, 64, 66]
    if rada["kategorie"] == "Kraťasy":
        vel = vel[:-1]
    # mrizka, ktera se zalamuje - nikdy nepretece kartu
    bunky = "".join(
        f'<label class="vel-bunka"><span>{v}</span>'
        f'<input type="number" min="0" placeholder="0" aria-label="Velikost {v}" data-ks="{v}"></label>'
        for v in vel)
    radky = "".join(
        f'<div class="velikost-radek"><b>{v}</b>'
        f'<div class="stepper"><button type="button" data-krok="-1" aria-label="Ubrat">−</button>'
        f'<output data-ks-out="{v}">0</output>'
        f'<button type="button" data-krok="1" aria-label="Přidat">+</button></div></div>'
        for v in vel)
    return f"""<div class="vel-mrizka">{bunky}</div>
<div class="velikosti-seznam">{radky}</div>
<div class="souhrn-kusu"><span>Celkem <b data-celkem>0</b> ks</span><span>bez DPH</span></div>
<button type="button" class="tl tl-hlavni tl-plna" data-do-sanonu>Přidat do šanonu</button>"""


# ---------------------------------------------------------------- index.html
def index():
    h = [hlava("M+P Král — výroba pracovních oděvů, Kunžak",
               "Český výrobce pracovních oděvů z Kunžaku. 1 300 vlastních střihů, zakázková výroba, certifikované oděvy.")]
    h.append(hlavicka("", ""))

    h.append(f"""<main>
<div class="obal">
  <section class="hero">
    <h1>Střih,<br>který si<br>ušijeme sami</h1>
    <div class="tlacitka">
      <a class="tl tl-hlavni" href="katalog.html">Prohlédnout řady</a>
      <a class="tl tl-obrys" href="#poptavka">Poptat zakázku</a>
    </div>
  </section>
</div>""")

    # 02 o firmě
    h.append(f"""<div class="obal">
  <section class="sekce" id="o-firme">
    {kota("01", "Pět lidí. Dnes čtyřicet pět.", "od roku 1993")}
    <div class="o-firme">
      <div class="o-firme-text">
        <p>Firmu založil Petr Král v roce 1993 a první pracovní oděvy šilo pět lidí.
        Dnes je nás pětačtyřicet a šijeme pořád na stejném místě v Kunžaku.</p>
        <p>Začínali jsme u několika druhů pracovních oděvů, spodního a nočního prádla.
        Postupně přibyly oděvy pro zdravotnictví a potravinářství a certifikované
        pracovní oděvy — tedy všude tam, kde na střihu a materiálu opravdu záleží.</p>
        <p>Veškerou výrobu si zajišťujeme sami: návrh, konstrukci, nastříhání i ušití.
        Nic nekupujeme hotové a nic nedáváme ven. Proto vám umíme říct, proč je
        v tom místě zesílení — a proto ho umíme posunout, když vám nesedí.</p>
        <p class="o-firme-zaver">Za svojí prací si stojíme. Férová cena, dodržené
        termíny a zákazník, který se vrátí. Nic složitějšího za tím není.</p>
      </div>
      <aside class="o-firme-fakta">
        <dl>
          <dt>Založeno</dt><dd>1993</dd>
          <dt>Lidí v dílně</dt><dd>45</dd>
          <dt>Kde</dt><dd>{esc(ADRESA)}</dd>
          <dt>Co děláme sami</dt><dd>návrh · konstrukce · střih · šití</dd>
          <dt>Specializace</dt><dd>zdravotnictví, potravinářství, certifikované oděvy</dd>
        </dl>
      </aside>
    </div>
  </section>
</div>""")

    # 03 kategorie
    dlazdice = []
    for i, k in enumerate(KATEGORIE):
        rady_k = [r for r in KAT if r["kategorie"] == k]
        barev = sum(len(r["varianty"]) for r in rady_k)
        dlazdice.append(f"""<a class="kategorie-karta" href="katalog.html#{i}">
      <span class="kod">K-{i + 1:02d}</span>
      <h3>{esc(k)}</h3>
      <span class="mono-popisek">{len(rady_k)} střihů · {barev} barev</span>
    </a>""")
    dlazdice.append(f"""<a class="kategorie-karta vse" href="katalog.html">
      <span class="kod">K-00</span>
      <h3>Všechny střihy</h3>
      <span class="mono-popisek">{len(KAT)} střihů · {sum(len(r["varianty"]) for r in KAT)} barev</span>
    </a>""")

    h.append(f"""<div class="obal">
  <section class="sekce">
    {kota("02", "Kategorie", f"{len(KATEGORIE)} kategorií")}
    <div class="kategorie-mrizka">{"".join(dlazdice)}</div>
  </section>
</div>""")

    # 04 řady
    karty_rad = []
    for rn in RADY:
        rady_r = [r for r in KAT if r["znacka"] == rn]
        veta = META["rady"].get(rn, "")
        if not rady_r:
            karty_rad.append(f"""<article class="rada-karta pripravujeme">
      <h3>{esc(rn)}</h3>
      <p>{esc(veta)}</p>
      <div class="ramecek"><div class="mono-popisek">Fotografie<br>dokončujeme</div></div>
    </article>""")
            continue
        vz = []
        for r in rady_r:
            for v in r["varianty"][:6]:
                if v.get("vzornik"):
                    vz.append(f'<li><span class="vzornik vzornik-maly" style="background-image:url({esc(v["vzornik"])})" title="{esc(v["nazev"])}"></span></li>')
        karty_rad.append(f"""<article class="rada-karta">
      <h3>{esc(rn)}</h3>
      <p>{esc(veta)}</p>
      <ul class="vzorniky">{"".join(vz[:8])}</ul>
      <p class="mono-popisek" style="margin-top:12px">{len(rady_r)} střihů</p>
    </article>""")
    h.append(f"""<div class="obal">
  <section class="sekce">
    {kota("03", "Naše řady", "5 řad", "Řada je rodina střihů ve stejném materiálu a stejné logice kapes. Uvnitř řady se dá sladit celý tým napříč profesemi.")}
    <div class="rady-mrizka">{"".join(karty_rad)}</div>
  </section>
</div>""")

    # 05 nejžádanější
    vyber = [r for r in KAT][:8]
    h.append(f"""<div class="obal">
  <section class="sekce">
    {kota("04", "Nejžádanější střihy", f"{sum(len(r['varianty']) for r in KAT)} barevných variant")}
    <div class="produkty po-ctyrech">{"".join(produkt_karta(r) for r in vyber)}</div>
    <p style="margin-top:24px"><a href="katalog.html">Zobrazit všech {len(KAT)} střihů →</a></p>
  </section>
</div>""")

    # 06 detail pás
    detaily = []
    for r in KAT:
        for v in r["varianty"]:
            if "detail" in v["fotky"] and len(detaily) < 3:
                detaily.append((r, v))
                break
    popisky = ["Prošití náprsní kapsy", "Přezka laclu", "Zesílený kolenní díl"]
    bloky = "".join(f"""<figure class="karta" style="margin:0">
      <div style="aspect-ratio:1"><img src="{esc(v['fotky']['detail'])}" alt="" loading="lazy" style="width:100%;height:100%;object-fit:contain"></div>
      <figcaption class="mono-popisek" style="padding:12px 14px">{esc(p)}</figcaption>
    </figure>""" for (r, v), p in zip(detaily, popisky))
    h.append(f"""<div class="obal">
  <section class="sekce">
    {kota("05", "Jak to vypadá zblízka", "detail", "Kvalita se nedá tvrdit, dá se ukázat. Tohle jsou nezmenšené výřezy z produktových fotek.")}
    <div class="produkty po-trech">{bloky}</div>
  </section>
</div>""")

    # 07 zakázka
    h.append(f"""<div class="obal">
  <section class="sekce">
    {kota("06", "Ušijeme podle vás", "zakázková výroba")}
    <p class="kurziva" style="font-size:20px;max-width:60ch;margin:0 0 28px">
      Nový vzor není u nás výjimka — nasamplujeme ho, vyzkoušíte ho v provozu a teprve pak se šije série.
    </p>
    <div class="kroky">
      <div class="krok"><span class="cislo">01</span><h3>Vzorek</h3><p>Ušijeme jeden kus podle vašeho zadání nebo podle existujícího střihu z archivu.</p></div>
      <div class="krok"><span class="cislo">02</span><h3>Úprava střihu</h3><p>Vyzkoušíte ho v provozu. Co nesedí, upravíme v konstrukci — délku, kapsy, zesílení.</p></div>
      <div class="krok"><span class="cislo">03</span><h3>Série</h3><p>Ušijeme celou zakázku v odsouhlaseném střihu, velikostech a barvě.</p></div>
    </div>
    <div class="tlacitka" style="margin-top:24px">
      <a class="tl tl-obrys" href="#poptavka">Objednat vzorek — 1 ks</a>
    </div>
  </section>
</div>""")

    # 08 navy
    plaste = [(r, v) for r in KAT if r["kategorie"] == "Pláště" for v in r["varianty"]][:2]
    karty_p = "".join(f"""<div class="karta" style="flex:1">
        <div style="aspect-ratio:1"><img src="{esc(v['hlavni'])}" alt="" loading="lazy" style="width:100%;height:100%;object-fit:contain"></div>
      </div>""" for r, v in plaste)
    h.append(f"""<div class="navy-blok">
  <div class="obal">
    {kota("07", "Pro zdravotnictví a potravinářství", "hygienické provozy")}
    <div class="navy-dva">
      <div style="display:flex;gap:16px">{karty_p}</div>
      <div>
        <p>Oddělená větev sortimentu s jinými požadavky než stavba: hladké materiály bez
        vnějších kapes na hrudi, zvýšená odolnost proti opakovanému praní na vysokou teplotu,
        barvy, na kterých je znečištění vidět.</p>
        <p>Šijeme i podle hygienických požadavků konkrétního provozu — včetně úprav střihu
        podle výstupu z auditu.</p>
        <p style="margin-top:18px">
          <span class="odznak">{zast("EN ISO 13688")}</span>
          <span class="odznak">{zast("praní 95 °C")}</span>
        </p>
      </div>
    </div>
  </div>
</div>""")

    # 10 profese
    profese = "".join(f"""<div class="krok">
      <h3>{esc(p['nazev'])}</h3><p>{esc(p['co'])}</p>
    </div>""" for p in META["profese"])
    h.append(f"""<div class="obal">
  <section class="sekce">
    {kota("08", "Oblečeme celý tým", f"{len(META['profese'])} profesí")}
    <div class="kategorie-mrizka">{profese}</div>
  </section>
</div>""")

    # 11 hladiny
    h.append(f"""<div class="obal">
  <section class="sekce">
    {kota("09", "Jak objednáte", "4 kroky")}
    <div class="kroky ctyri">
      <div class="krok"><span class="cislo">01</span><h3>Vyberete střih</h3><p>Řadu, barvu a provedení.</p></div>
      <div class="krok"><span class="cislo">02</span><h3>Zapíšete počty</h3><p>Po velikostech, ne jedno číslo.</p></div>
      <div class="krok"><span class="cislo">03</span><h3>Odešlete šanon</h3><p>Bez registrace a bez hesel.</p></div>
      <div class="krok"><span class="cislo">04</span><h3>Potvrdíme cenu</h3><p>Do dvou pracovních dnů i s termínem.</p></div>
    </div>
    <h3 style="margin:36px 0 12px;font-size:20px">Množstevní hladiny</h3>
    <table class="hladiny">
      <thead><tr><th>Množství</th><th>1–9 ks</th><th>10–49 ks</th><th>50+ ks</th></tr></thead>
      <tbody><tr><td>Cena / ks bez DPH</td><td>—</td><td>—</td><td>—</td></tr></tbody>
    </table>
    <p class="mono" style="color:var(--ocel);margin-top:10px">Ceník připravujeme. Rozpětí hladin platí, čísla doplní M+P Král.</p>
  </section>
</div>""")

    # 10 kontakt
    tel_href = "tel:" + TELEFON.replace(" ", "")
    h.append(f"""<div class="obal">
  <section class="sekce" id="poptavka">
    {kota("10", "Napište nám", "odpovídáme do 2 pracovních dnů")}

    <div class="kontakt-velky">
      <a class="kontakt-radek" href="{tel_href}">
        <span class="kontakt-stitek">Telefon</span>
        <span class="kontakt-hodnota">{esc(TELEFON)}</span>
      </a>
      <a class="kontakt-radek" href="mailto:{esc(MAIL)}">
        <span class="kontakt-stitek">E-mail</span>
        <span class="kontakt-hodnota">{esc(MAIL)}</span>
      </a>
    </div>

    <div class="kontakt-mrizka">
      <div class="kontakt-pole">
        <h3>Dílna</h3>
        <p>Nová 401<br>378 62 Kunžak<br>okres Jindřichův Hradec</p>
        <svg class="kontakt-znak" viewBox="0 0 120 120" aria-hidden="true" focusable="false">
          <circle cx="60" cy="60" r="30" fill="none" stroke="currentColor" stroke-width="1"/>
          <circle cx="60" cy="60" r="3" fill="currentColor"/>
          <path d="M60 8v30M60 82v30M8 60h30M82 60h30" stroke="currentColor" stroke-width="1"/>
          <path d="M14 14h14M14 14v14M106 14H92M106 14v14M14 106h14M14 106V92M106 106H92M106 106V92"
                stroke="currentColor" stroke-width="1" fill="none"/>
        </svg>
      </div>
      <div class="kontakt-pole">
        <h3>Fakturace</h3>
        <p>Petr Král M+P<br>IČ {esc(ICO)}<br>tel./fax {esc(TELFAX)}</p>
      </div>
      <div class="kontakt-pole">
        <h3>Provoz dílny</h3>
        <p>{zast("po–pá 7:00–15:30")}<br>{zast("so–ne zavřeno")}</p>
      </div>
      <div class="kontakt-pole">
        <h3>Jak to chodí</h3>
        <p>Napíšete, co potřebujete a kolik kusů.<br>
        Do dvou pracovních dnů potvrdíme cenu i termín.</p>
      </div>
    </div>

    <div class="kontakt-dole">
      <form class="formular" data-poptavka>
        <p class="mono-popisek" style="margin:0 0 6px">Poptávkový formulář</p>
        <div class="dva-sloupce">
          <div class="pole"><label for="f-firma">Firma</label><input id="f-firma" name="firma" required></div>
          <div class="pole"><label for="f-ico">IČO</label><input id="f-ico" name="ico" inputmode="numeric"></div>
        </div>
        <div class="dva-sloupce">
          <div class="pole"><label for="f-osoba">Kontaktní osoba</label><input id="f-osoba" name="osoba" required></div>
          <div class="pole"><label for="f-tel">Telefon</label><input id="f-tel" name="tel" type="tel"></div>
        </div>
        <div class="dva-sloupce">
          <div class="pole"><label for="f-mail">E-mail</label><input id="f-mail" name="mail" type="email" required></div>
          <div class="pole"><label for="f-obj">Číslo vaší objednávky</label><input id="f-obj" name="objednavka"></div>
        </div>
        <div class="pole"><label for="f-pozn">Co potřebujete</label><textarea id="f-pozn" name="poznamka" placeholder="Střih, barva, počty po velikostech, potisk, termín…"></textarea></div>
        <button type="submit" class="tl tl-hlavni">Odeslat poptávku</button>
        <p class="mono" style="color:var(--ocel);margin:0">Ceny uvádíme bez DPH. (náčrt — formulář zatím neodesílá)</p>
      </form>

      <aside class="kontakt-znovu">
        <p class="mono-popisek">Už jste u nás objednávali?</p>
        <p class="kontakt-znovu-text">Pošlete číslo poslední dodávky a ušijeme totéž —
        stejný střih, stejná barva, stejné velikosti. Nic vypisovat nemusíte.</p>
        <div class="pole"><label for="f-dodavka">Číslo dodávky</label><input id="f-dodavka" placeholder="např. 2025/0413"></div>
        <button type="button" class="tl tl-obrys tl-plna" style="margin-top:14px">Zopakovat objednávku</button>
      </aside>
    </div>
  </section>
</div>
</main>""")
    h.append(paticka(""))
    return "".join(h)


# ---------------------------------------------------------------- katalog.html
def katalog():
    h = [hlava("Katalog — M+P Král", "Všechny střihy pracovních oděvů M+P Král.")]
    h.append(hlavicka("", ""))
    filtry_kat = "".join(
        f'<label><input type="checkbox" data-filtr="kategorie" value="{esc(k)}"> {esc(k)}</label>'
        for k in KATEGORIE)
    filtry_rady = "".join(
        f'<label><input type="checkbox" data-filtr="znacka" value="{esc(r)}"> {esc(r)}</label>'
        for r in RADY)
    karty = "".join(produkt_karta(r) for r in KAT)

    pripravujeme = "".join(f"""<article class="produkt karta pripravujeme" data-produkt data-kategorie="" data-znacka="Reflexní">
    <div class="ramecek"><div class="mono-popisek">{esc(p['nazev'])}<br>{esc(p['detail'])}<br>{esc(p['stav'])}</div></div>
    <div class="produkt-telo">
      <h3 class="produkt-nazev">{esc(p['nazev'])}</h3>
      <p class="produkt-mono">{esc(p['detail'])}</p>
      <p class="produkt-rozsah">Fotografie dokončujeme</p>
    </div>
  </article>""" for p in META["pripravujeme"])

    h.append(f"""<main class="obal sekce">
  {kota("01", "Katalog", f"{len(KAT)} střihů · {sum(len(r['varianty']) for r in KAT)} barev")}
  <div class="lista-sanonu">
    <span>Vybráno do poptávky: <b data-sanon-polozky>0</b> položek · <b data-sanon-kusy>0</b> ks</span>
    <a class="tl tl-obrys" href="sanon.html" style="padding:8px 14px">Otevřít šanon</a>
  </div>
  <button class="tl tl-obrys filtry-tlacitko" id="filtry-tlacitko" style="margin-bottom:16px">Filtry</button>
  <div class="katalog-layout">
    <aside class="filtry" id="filtry">
      <div class="filtr-skupina"><h3>Kategorie</h3>{filtry_kat}</div>
      <div class="filtr-skupina"><h3>Řada</h3>{filtry_rady}</div>
      <div class="filtr-skupina"><h3>Řadit</h3>
        <select id="razeni" style="width:100%;padding:8px;border:1px solid var(--linka);border-radius:2px;background:var(--bila);color:var(--inkoust);font:inherit">
          <option value="rada">podle řady</option>
          <option value="kategorie">podle kategorie</option>
        </select>
      </div>
      <p class="mono" style="color:var(--ocel)">Ceník připravujeme, proto se neřadí podle ceny.</p>
    </aside>
    <div>
      <div class="produkty po-trech" id="vypis">{karty}{pripravujeme}</div>
      <p class="mono" style="color:var(--ocel);margin-top:24px" data-pocet-vypisu></p>
    </div>
  </div>
</main>""")
    h.append(paticka(""))
    return "".join(h)


# ---------------------------------------------------------------- produkt.html
def produkt():
    rada = next((r for r in KAT if r["nazev"] == "Bunda King"), KAT[0])
    v0 = rada["varianty"][0]
    hlavni = v0["fotky"].get("přední") or v0["hlavni"]

    nahledy = []
    for klic, popis in (("přední", "Přední"), ("zadní", "Zadní"), ("detail", "Detail")):
        if klic in v0["fotky"]:
            nahledy.append(f"""<button type="button" class="nahled {'aktivni' if klic == 'přední' else ''}" data-nahled="{klic}">
        <span class="ramecek karta" style="display:block"><img src="{esc(v0['fotky'][klic])}" alt=""></span>
        <span class="mono-popisek">{popis}</span>
      </button>""")

    vzorniky = "".join(
        f"""<li style="text-align:center">
      <button type="button" class="vzornik {'aktivni' if i == 0 else ''}" style="background-image:url({esc(v.get('vzornik') or '')})"
        data-varianta="{varianta_data(rada, v)}" aria-label="{esc(v['nazev'])}"></button>
      <span class="mono-popisek" style="display:block;margin-top:5px;max-width:64px">{esc(v['nazev'])}</span>
    </li>""" for i, v in enumerate(rada["varianty"]))

    h = [hlava(f"{rada['nazev']} — M+P Král", rada["popis"])]
    h.append(hlavicka(rada["kategorie"], ""))
    h.append(f"""<main class="obal sekce">
  <p class="mono" style="color:var(--ocel)"><a href="katalog.html">Katalog</a> / {esc(rada['kategorie'])} / {esc(rada['nazev'])}</p>
  <div class="detail-layout" style="margin-top:20px">
    <div class="detail-galerie">
      <div class="detail-hlavni karta">
        <div class="ramecek"><img src="{esc(hlavni)}" alt="{esc(rada['nazev'])}" id="hlavni-fotka"></div>
      </div>
      <div class="nahledy" id="nahledy">{"".join(nahledy)}</div>
      <ul class="vzorniky" id="varianty" style="margin-top:22px;gap:14px">{vzorniky}</ul>
    </div>

    <div class="detail-info">
      <h1 id="nazev-produktu">{esc(rada['nazev'])} — {esc(v0['nazev'])}</h1>
      <p class="technicky">{zast(rada['material'])} · {zast(rada['gramaz'])} · vel. {zast(rada['velikosti'])} · střih <span data-strih>{zast(v0['strih'])}</span></p>
      <p class="popis">{esc(rada['popis'])}</p>

      <h2 style="font-size:20px;margin:28px 0 10px">Rozpis velikostí</h2>
      <p class="mono" style="color:var(--ocel);margin:0 0 12px">Zapište počty kusů po velikostech.</p>
      {rozpis_velikosti(rada)}

      <div class="tlacitka" style="margin-top:14px">
        <a class="tl tl-obrys" href="index.html#poptavka">Objednat vzorek — 1 ks</a>
      </div>

      <div class="boxy">
        <div class="box karta">
          <h3>Materiál a gramáž</h3>
          <p>{zast(rada['material'])}, {zast(rada['gramaz'])}. {zast("Srážlivost do 3 %")}. {zast("Praní 60 °C")}.</p>
        </div>
        <div class="box karta">
          <h3>Normy a certifikace</h3>
          <p><span class="odznak">{zast(rada['norma'])}</span></p>
        </div>
        <div class="box karta">
          <h3>Potisk a výšivka</h3>
          <label style="display:flex;gap:8px;align-items:center;font-size:15px"><input type="checkbox" id="chci-logo"> Chci logo</label>
          <div id="logo-pole" style="display:none;margin-top:10px">
            <div class="pole"><label for="umisteni">Umístění</label>
              <select id="umisteni"><option>levá hruď</option><option>záda</option><option>rukáv</option><option>záda + hruď</option></select>
            </div>
            <div class="pole" style="margin-top:8px"><label for="logo-soubor">Soubor s logem</label><input type="file" id="logo-soubor"></div>
            <p class="mono" id="logo-nazev" style="color:var(--ocel);margin:6px 0 0"></p>
          </div>
        </div>
        <div class="box karta">
          <h3>Dodací lhůta a minimum</h3>
          <p>{zast("Skladové barvy do 5 dnů")}. {zast("Zakázková barva od 30 ks, 4–6 týdnů")}.</p>
        </div>
      </div>

      <p style="margin-top:24px">Chcete jinou barvu nebo úpravu střihu?
      <a href="index.html#poptavka">Nasamplujeme vzorek</a> — v archivu máme 1 300 střihů,
      většinou stačí vybrat a upravit.</p>
    </div>
  </div>

  <section class="sekce">
    {kota("02", "Ze stejné řady", esc(rada['znacka']))}
    <div class="produkty po-ctyrech">{"".join(produkt_karta(r) for r in KAT if r['znacka'] == rada['znacka'] and r['nazev'] != rada['nazev'])[:4] if False else "".join(produkt_karta(r) for r in [x for x in KAT if x['znacka'] == rada['znacka'] and x['nazev'] != rada['nazev']][:4])}</div>
  </section>
</main>
<div class="lupa" id="lupa"><img src="" alt="" id="lupa-fotka"></div>""")
    h.append(paticka(""))
    return "".join(h)


# ---------------------------------------------------------------- sanon.html
def sanon():
    h = [hlava("Šanon poptávky — M+P Král", "Rozpracovaná poptávka.")]
    h.append(hlavicka("", ""))
    h.append(f"""<main class="obal sekce">
  <div class="tisk-hlavicka">
    <h1 style="margin:0">Poptávka — M+P Král</h1>
    <p class="mono">{esc(ADRESA)} · Výroba pracovních oděvů</p>
  </div>
  {kota("01", "Šanon poptávky", "bez registrace", "Rozpis zůstává uložený ve vašem prohlížeči. Můžete ho vytisknout a přiložit k interní objednávce.")}
  <div id="sanon-obsah"></div>
  <div class="tlacitka" style="margin-top:24px">
    <button type="button" class="tl tl-obrys" onclick="window.print()">Vytisknout poptávku</button>
    <button type="button" class="tl tl-obrys" data-vyprazdnit>Vyprázdnit šanon</button>
  </div>

  <section class="sekce" id="odeslat">
    {kota("02", "Odeslat poptávku", "odpovídáme do 2 dnů")}
    <form class="formular" data-poptavka style="max-width:640px">
      <div class="dva-sloupce">
        <div class="pole"><label for="s-firma">Firma</label><input id="s-firma" required></div>
        <div class="pole"><label for="s-ico">IČO</label><input id="s-ico" inputmode="numeric"></div>
      </div>
      <div class="dva-sloupce">
        <div class="pole"><label for="s-osoba">Kontaktní osoba</label><input id="s-osoba" required></div>
        <div class="pole"><label for="s-tel">Telefon</label><input id="s-tel" type="tel"></div>
      </div>
      <div class="dva-sloupce">
        <div class="pole"><label for="s-mail">E-mail</label><input id="s-mail" type="email" required></div>
        <div class="pole"><label for="s-obj">Číslo vaší objednávky</label><input id="s-obj"></div>
      </div>
      <div class="pole"><label for="s-pozn">Poznámka</label><textarea id="s-pozn"></textarea></div>
      <p class="mono" style="color:var(--ocel);margin:0">Ceny uvádíme bez DPH.</p>
      <button type="submit" class="tl tl-hlavni">Odeslat poptávku</button>
      <p class="mono" style="color:var(--ocel);margin:0">(náčrt — formulář zatím neodesílá)</p>
    </form>
  </section>
</main>""")
    h.append(paticka(""))
    return "".join(h)


for nazev, obsah in (("index.html", index()), ("katalog.html", katalog()),
                     ("produkt.html", produkt()), ("sanon.html", sanon())):
    (KOREN / nazev).write_text(obsah, encoding="utf-8")
    print(f"{nazev:16} {len(obsah) // 1024} kB")
