#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Samostatný mobilní návrh e-shopu M+P Král -> mobil.html + mobil-nahled.html.

Desktop (build.py) se tím nemění. Mobil má vlastní CSS i JS přímo ve stránce,
aby se dal ladit úplně odděleně. Data bere ze stejného data/katalog.json.
"""
import json
from pathlib import Path

KOREN = Path(__file__).resolve().parent
KAT = json.loads((KOREN / "data" / "katalog.json").read_text(encoding="utf-8"))
META = json.loads((KOREN / "data" / "meta.json").read_text(encoding="utf-8"))
VYSTUP = KOREN

KATEGORIE = ["Kombinézy", "Kalhoty", "Laclové kalhoty", "Bundy a blůzy",
             "Kraťasy", "Pláště", "Soupravy"]
RADY = ["King", "Klasik", "Riedl", "Polar", "Reflexní"]
TELEFON = "+420 608 982 675"
MAIL = "info@mpkral.cz"
ADRESA = "Nová 401, 378 62 Kunžak"


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def img(cesta):
    return cesta


def sklon(n, jedna, dve, pet):
    return f"{n} {jedna if n == 1 else (dve if n < 5 else pet)}"


def vzorniky(rada, kolik=6):
    v = [x["vzornik"] for x in rada["varianty"] if x.get("vzornik")][:kolik]
    return "".join(f'<i style="background-image:url({esc(img(x))})"></i>' for x in v)


def karta_svisle(rada):
    """Karta do vodorovného posuvníku: fotka, název, řada, barvy."""
    v0 = rada["varianty"][0]
    return f"""<a class="pk" href="produkt.html?rada={esc(rada['id'])}">
        <span class="pk-foto"><img src="{esc(img(v0['hlavni']))}" alt="" loading="lazy"></span>
        <b>{esc(rada['nazev'])}</b>
        <span class="mono">{esc(rada['znacka'])} · {sklon(len(rada['varianty']), 'barva', 'barvy', 'barev')}</span>
        <span class="vz">{vzorniky(rada)}</span>
      </a>"""


def stranka():
    # --- co šijeme: rozbalovací kategorie s posuvníkem produktů
    kategorie = []
    for i, k in enumerate(KATEGORIE):
        rady_k = [r for r in KAT if r["kategorie"] == k]
        barev = sum(len(r["varianty"]) for r in rady_k)
        nahledy = "".join(
            f'<img src="{esc(img(r["varianty"][0]["hlavni"]))}" alt="" loading="lazy">'
            for r in rady_k[:3])
        otevrena = " otevrena" if i == 0 else ""
        kategorie.append(f"""<div class="kat{otevrena}" data-kat>
      <button type="button" class="kat-hlava" aria-expanded="{'true' if i == 0 else 'false'}" data-kat-tl>
        <span class="kod">K-{i + 1:02d}</span>
        <span class="kat-nazev">{esc(k)}<small>{sklon(len(rady_k), 'střih', 'střihy', 'střihů')} · {sklon(barev, 'barva', 'barvy', 'barev')}</small></span>
        <span class="kat-mini" aria-hidden="true">{nahledy}</span>
        <span class="kat-sipka" aria-hidden="true"></span>
      </button>
      <div class="kat-telo">
        <div class="posuvnik">{"".join(karta_svisle(r) for r in rady_k)}
          <a class="pk pk-vse" href="katalog.html#{i}"><span>Celá kategorie</span><span class="mono">{sklon(len(rady_k), 'střih', 'střihy', 'střihů')} →</span></a>
        </div>
      </div>
    </div>""")

    # --- řady
    rady = []
    for r in RADY:
        rady_r = [x for x in KAT if x["znacka"] == r]
        cesty = [v["vzornik"] for x in rady_r for v in x["varianty"] if v.get("vzornik")][:10]
        vz = "".join(f'<i style="background-image:url({esc(img(c))})"></i>' for c in cesty)
        rady.append(f"""<article class="rada">
        <h3>{esc(r)}</h3>
        <p>{esc(META['rady'].get(r, ''))}</p>
        <span class="vz vz-velke">{vz}</span>
        <span class="mono">{sklon(len(rady_r), 'střih', 'střihy', 'střihů')}</span>
      </article>""")

    # --- nejžádanější: řada King
    nej = [r for r in KAT if r["znacka"] == "King"][:4]
    mrizka = "".join(f"""<article class="nk">
        <a href="produkt.html?rada={esc(r['id'])}" class="pk-foto"><img src="{esc(img(r['varianty'][0]['hlavni']))}" alt="{esc(r['nazev'])}" loading="lazy"></a>
        <b>{esc(r['nazev'])}</b>
        <span class="vz">{vzorniky(r, 5)}</span>
        <button type="button" class="nk-tl" data-do-sanonu>+ Do šanonu</button>
      </article>""" for r in nej)

    hero = [r for r in KAT if r["znacka"] == "King"]
    hero_foto = "".join(
        f'<img src="{esc(img(r["varianty"][0]["hlavni"]))}" alt="{esc(r["nazev"])}">'
        for r in hero[:3])

    hledani_data = json.dumps(
        [{"n": r["nazev"], "k": r["kategorie"], "r": r["znacka"], "id": r["id"],
          "f": img(r["varianty"][0]["hlavni"])} for r in KAT], ensure_ascii=False)
    chipy = "".join(f'<button type="button" data-chip="{esc(k)}">{esc(k)}</button>' for k in KATEGORIE)

    return f"""<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#f2f0eb">
<title>M+P Král · mobil</title>
<link rel="icon" type="image/png" href="img/favicon.png">
<link rel="apple-touch-icon" href="img/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;600;700;800&family=IBM+Plex+Mono:wght@400;500&family=EB+Garamond:ital,wght@0,400;0,500;1,400&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>

<header class="lista">
  <a class="logo" href="#"><img src="img/logo-mp.png" width="249" height="128" alt="M+P Král"><span>Kunžak · od 1993</span></a>
  <button type="button" class="ikona" aria-label="Hledat" data-otevrit-hledani>
    <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5"/><path d="M15.5 15.5 21 21"/></svg>
  </button>
</header>

<main>
  <section class="hero">
    <p class="mono">Výroba pracovních oděvů</p>
    <h1>Střih, který si ušijeme sami</h1>
    <p class="deck">Návrh, konstrukce, střih i šití. Všechno v jedné dílně v Kunžaku, od roku 1993.</p>
    <div class="hero-foto">{hero_foto}</div>
    <dl class="fakta">
      <div><dt>Založeno</dt><dd>1993</dd></div>
      <div><dt>V dílně</dt><dd>45 lidí</dd></div>
      <div><dt>Střihů</dt><dd>1 300</dd></div>
    </dl>
  </section>

  <figure class="ilustrace">
    <img src="img/ilustrace/dilna.jpg" alt="Šicí dílna" loading="lazy">
    <figcaption><span>Dílna v Kunžaku</span><span class="mono">ilustrační foto</span></figcaption>
  </figure>
  <p class="citat">Nic nekupujeme hotové a nic nedáváme ven. Proto víme, proč je v tom místě zesílení, a umíme ho posunout.</p>

  <section class="sekce" id="co-sijeme">
    <div class="kota"><span>01</span><h2>Co šijeme</h2><span>{len(KAT)} střihů</span></div>
    <div class="kategorie">{"".join(kategorie)}</div>
  </section>

  <section class="sekce">
    <div class="kota"><span>02</span><h2>Naše řady</h2><span>{len(RADY)} řad</span></div>
    <p class="uvod">Řada je rodina střihů ve stejném materiálu. Celý tým oblečete do jedné.</p>
    <div class="posuvnik rady">{"".join(rady)}</div>
  </section>

  <section class="sekce">
    <div class="kota"><span>03</span><h2>Nejžádanější</h2><span>řada King</span></div>
    <div class="mrizka2">{mrizka}</div>
  </section>

  <figure class="ilustrace detail">
    <img src="img/ilustrace/detail.jpg" alt="Dvojitý šev na pracovních kalhotách" loading="lazy">
    <figcaption><span>Dvojitý šev, zesílený díl</span><span class="mono">ilustrační foto</span></figcaption>
  </figure>

  <section class="navy">
    <img class="navy-foto" src="img/ilustrace/strih.jpg" alt="Střihový stůl" loading="lazy">
    <p class="mono">Na zakázku</p>
    <h2>Nesedí vám střih? Posuneme ho.</h2>
    <ol class="kroky">
      <li><b>Zavoláte nebo pošlete poptávku</b><span>Řekněte, co děláte a kolik lidí oblékáte.</span></li>
      <li><b>Nasamplujeme vzorek</b><span>Jeden kus k vyzkoušení, i s vaším logem.</span></li>
      <li><b>Ušijeme sérii</b><span>Ve vlastní dílně, v dohodnutém termínu.</span></li>
    </ol>
    <a class="tl tl-svetle" href="#poptavka">Poptat zakázku</a>
  </section>

  <section class="sekce" id="poptavka">
    <div class="kota"><span>04</span><h2>Ozvěte se</h2><span>do 2 dnů</span></div>
    <a class="velky-kontakt" href="tel:{TELEFON.replace(' ', '')}"><span class="mono">Zavolat</span>{esc(TELEFON)}</a>
    <a class="velky-kontakt" href="mailto:{MAIL}"><span class="mono">Napsat</span>{esc(MAIL)}</a>
    <p class="adresa">{esc(ADRESA)}<br>okres Jindřichův Hradec</p>
  </section>

  <footer class="paticka">
    <img class="paticka-logo" src="img/logo-mp.png" width="249" height="128" alt="M+P Král" loading="lazy">
    <p>Technické údaje jsou v náčrtu zástupné.</p>
    <p class="kurziva">Šijeme od roku 1993.</p>
  </footer>
</main>

<nav class="spodni" aria-label="Hlavní">
  <a href="#" class="aktivni"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 11 12 4l8 7v9h-5v-6H9v6H4z"/></svg>Domů</a>
  <a href="#co-sijeme"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5h16M4 12h16M4 19h10"/></svg>Katalog</a>
  <a href="sanon.html"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 3h12v18l-6-4-6 4z"/></svg>Šanon<em data-pocet>0</em></a>
  <a href="#poptavka" class="poptat">Poptat</a>
</nav>

<div class="hledani" data-hledani hidden>
  <div class="hledani-hlava">
    <input type="search" placeholder="Co hledáte? Třeba laclové" aria-label="Hledat" data-hledani-pole>
    <button type="button" data-zavrit-hledani>Zavřít</button>
  </div>
  <div class="chipy">{chipy}</div>
  <ul class="vysledky" data-vysledky></ul>
</div>

<div class="toast" data-toast>Přidáno do šanonu</div>

<script>
var PRODUKTY = {hledani_data};
{JS}
</script>
</body>
</html>
"""


CSS = r"""
:root{--papir:#f2f0eb;--bila:#fff;--inkoust:#111110;--ocel:#706d66;--linka:#d6d1c7;
--oranzova:#d8431a;--navy:#1d2f4d;--jas:1;--spodek:64px}
@media (prefers-color-scheme:dark){:root{--papir:#131311;--inkoust:#efece4;--ocel:#9b978d;
--linka:#34322c;--oranzova:#ff6b3d;--navy:#22354f;--jas:.9}}
*,*::before,*::after{box-sizing:border-box}
html{-webkit-text-size-adjust:100%;scroll-behavior:smooth;scroll-padding-top:64px;scrollbar-width:none}
html::-webkit-scrollbar{display:none}
body{margin:0;background:var(--papir);color:var(--inkoust);font-family:Archivo,-apple-system,sans-serif;
font-size:16px;line-height:1.5;padding-bottom:calc(var(--spodek) + env(safe-area-inset-bottom))}
img{display:block;max-width:100%}
a{color:inherit;text-decoration:none}
button{font:inherit;color:inherit;background:none;border:0;padding:0;cursor:pointer}
.mono{font-family:"IBM Plex Mono",monospace;font-size:10.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--ocel)}
.kurziva{font-family:"EB Garamond",Georgia,serif;font-style:italic}

/* horní lišta */
.lista{position:sticky;top:0;z-index:20;display:flex;align-items:center;justify-content:space-between;
height:56px;padding:0 16px;background:color-mix(in srgb,var(--papir) 92%,transparent);
backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);border-bottom:1px solid var(--linka)}
.logo{display:flex;flex-direction:column;line-height:1}
.logo img{display:block;height:26px;width:auto;align-self:flex-start}
.logo span{font-family:"IBM Plex Mono",monospace;font-size:9px;letter-spacing:.14em;text-transform:uppercase;color:var(--ocel);margin-top:4px}
.ikona{width:44px;height:44px;display:grid;place-items:center;margin-right:-10px}
.ikona svg,.spodni svg{width:22px;height:22px;fill:none;stroke:currentColor;stroke-width:1.6;stroke-linecap:round;stroke-linejoin:round}

/* hero */
.hero{padding:28px 16px 8px}
.hero h1{margin:10px 0 14px;font-size:44px;line-height:.95;font-weight:800;letter-spacing:-.035em;text-transform:uppercase}
.deck{margin:0 0 22px;font-family:"EB Garamond",Georgia,serif;font-size:19px;line-height:1.35}
.hero-foto{display:grid;grid-template-columns:1.4fr 1fr;grid-template-rows:1fr 1fr;gap:6px;height:300px}
.hero-foto img{width:100%;height:100%;object-fit:contain;background:var(--bila);filter:brightness(var(--jas))}
.hero-foto img:first-child{grid-row:1/3}
.fakta{display:grid;grid-template-columns:repeat(3,1fr);margin:18px 0 0;border-top:1px solid var(--inkoust)}
.fakta div{padding:12px 0 4px}
.fakta div+div{padding-left:12px;border-left:1px solid var(--linka)}
.fakta dt{font-family:"IBM Plex Mono",monospace;font-size:9.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--ocel)}
.fakta dd{margin:2px 0 0;font-size:22px;font-weight:700;letter-spacing:-.02em}

/* sekce + kóta */
.sekce{padding:40px 16px 8px}
.kota{display:grid;grid-template-columns:auto 1fr auto;align-items:baseline;gap:10px;
border-bottom:1px solid var(--inkoust);padding-bottom:10px;margin-bottom:16px}
.kota span{font-family:"IBM Plex Mono",monospace;font-size:10.5px;letter-spacing:.1em;color:var(--ocel);text-transform:uppercase}
.kota h2{margin:0;font-size:28px;line-height:1;font-weight:800;letter-spacing:-.03em;text-transform:uppercase}
.uvod{margin:0 0 16px;font-family:"EB Garamond",Georgia,serif;font-size:18px;line-height:1.35}

/* kategorie: mobilní obdoba hover náhledu na desktopu */
.kat{border-bottom:1px solid var(--linka)}
.kat-hlava{display:grid;grid-template-columns:38px 1fr auto 18px;align-items:center;gap:10px;width:100%;
min-height:68px;padding:10px 0;text-align:left}
.kod{font-family:"IBM Plex Mono",monospace;font-size:10px;letter-spacing:.08em;color:var(--ocel)}
.kat-nazev{font-size:19px;font-weight:600;letter-spacing:-.015em;line-height:1.15}
.kat-nazev small{display:block;margin-top:3px;font-family:"IBM Plex Mono",monospace;font-size:9.5px;font-weight:400;letter-spacing:.1em;text-transform:uppercase;color:var(--ocel)}
.kat-mini{display:flex}
.kat-mini img{width:30px;height:30px;object-fit:contain;background:var(--bila);border:1px solid var(--papir);border-radius:50%;margin-left:-8px;filter:brightness(var(--jas))}
.kat-sipka{width:10px;height:10px;border-right:1.5px solid currentColor;border-bottom:1.5px solid currentColor;transform:rotate(45deg) translate(-3px,-3px);transition:transform .2s}
.kat.otevrena .kat-sipka{transform:rotate(-135deg)}
.kat.otevrena .kat-mini{opacity:0}
.kat-telo{display:grid;grid-template-rows:0fr;transition:grid-template-rows .25s ease}
.kat-telo>.posuvnik{min-height:0;overflow:hidden}
.kat.otevrena .kat-telo{grid-template-rows:1fr}
.kat.otevrena .kat-telo>.posuvnik{overflow-x:auto;padding-bottom:18px}

/* vodorovný posuvník */
.posuvnik{display:flex;gap:10px;overflow-x:auto;scroll-snap-type:x mandatory;margin:0 -16px;padding:0 16px;
scroll-padding-inline:16px;scrollbar-width:none;-webkit-overflow-scrolling:touch}
.posuvnik::-webkit-scrollbar{display:none}
.pk{flex:0 0 46%;scroll-snap-align:start;display:flex;flex-direction:column;gap:3px;min-width:0}
.pk b{font-size:14px;font-weight:600;line-height:1.25}
.pk-foto{display:block;aspect-ratio:1;background:var(--bila);margin-bottom:6px;filter:brightness(var(--jas))}
.pk-foto img{width:100%;height:100%;object-fit:contain}
.pk-vse{justify-content:center;align-items:flex-start;padding:16px;border:1px solid var(--inkoust);aspect-ratio:1;gap:8px}
.pk-vse span:first-child{font-size:20px;font-weight:700;letter-spacing:-.02em;line-height:1.1}
.vz{display:flex;gap:3px;margin-top:4px;flex-wrap:wrap}
.vz i{width:14px;height:14px;border-radius:50%;background-size:cover;background-position:center;box-shadow:inset 0 0 0 1px rgba(0,0,0,.15)}
.vz-velke i{width:22px;height:22px;border-radius:2px}

/* řady */
.rady .rada{flex:0 0 78%;scroll-snap-align:start;border-top:2px solid var(--inkoust);padding-top:14px}
.rada h3{margin:0 0 8px;font-size:26px;font-weight:800;letter-spacing:-.02em;text-transform:uppercase}
.rada p{margin:0 0 14px;font-family:"EB Garamond",Georgia,serif;font-size:17px;line-height:1.35}
.rada .mono{display:block;margin-top:12px}

/* nejžádanější */
.mrizka2{display:grid;grid-template-columns:1fr 1fr;gap:20px 10px}
.nk{display:flex;flex-direction:column;gap:3px}
.nk b{font-size:14px;font-weight:600;line-height:1.25}
.nk-tl{margin-top:8px;min-height:40px;border:1px solid var(--inkoust);font-family:"IBM Plex Mono",monospace;font-size:10.5px;letter-spacing:.08em;text-transform:uppercase}
.nk-tl:active{background:var(--inkoust);color:var(--papir)}

/* ilustrační fotky */
.ilustrace{margin:28px 0 0;position:relative}
.ilustrace img{width:100%;aspect-ratio:4/5;object-fit:cover}
.ilustrace.detail{margin-top:40px}
.ilustrace.detail img{aspect-ratio:1}
.ilustrace figcaption{position:absolute;left:0;right:0;bottom:0;display:flex;justify-content:space-between;align-items:flex-end;
padding:40px 16px 14px;background:linear-gradient(transparent,rgba(17,17,16,.7));color:#fff;font-weight:600;font-size:15px}
.ilustrace figcaption .mono{color:rgba(255,255,255,.75);font-size:9.5px}
.citat{margin:0;padding:22px 16px 0;font-family:"EB Garamond",Georgia,serif;font-style:italic;font-size:21px;line-height:1.3}
.navy-foto{width:calc(100% + 32px);max-width:none;margin:-40px -16px 28px;aspect-ratio:3/2;object-fit:cover}
.ilustrace.detail+.navy{margin-top:0}

/* na zakázku */
.navy{margin-top:40px;padding:40px 16px;background:var(--navy);color:#f2f0eb}
.navy .mono{color:rgba(242,240,235,.65)}
.navy h2{margin:8px 0 22px;font-size:32px;line-height:1;font-weight:800;letter-spacing:-.03em;text-transform:uppercase}
.kroky{list-style:none;margin:0 0 26px;padding:0;counter-reset:k}
.kroky li{counter-increment:k;display:grid;grid-template-columns:34px 1fr;padding:14px 0;border-top:1px solid rgba(242,240,235,.2)}
.kroky li::before{content:"0" counter(k);grid-row:1/3;font-family:"IBM Plex Mono",monospace;font-size:11px;color:rgba(242,240,235,.6);padding-top:3px}
.kroky b{font-size:17px;font-weight:600}
.kroky span{font-family:"EB Garamond",Georgia,serif;font-size:16px;opacity:.85}
.tl{display:flex;align-items:center;justify-content:center;min-height:52px;font-weight:600;font-size:16px}
.tl-svetle{background:#f2f0eb;color:#111110}

/* kontakt */
.velky-kontakt{display:block;padding:16px 0;border-bottom:1px solid var(--linka);font-size:26px;font-weight:700;letter-spacing:-.02em;line-height:1.1}
.velky-kontakt .mono{display:block;margin-bottom:4px}
.adresa{margin:16px 0 0;font-family:"EB Garamond",Georgia,serif;font-size:18px}
.paticka{padding:40px 16px 24px;color:var(--ocel);font-size:13px}
.paticka p{margin:0 0 4px}
.paticka-logo{display:block;height:40px;width:auto;margin-bottom:14px}

/* spodní lišta, na dosah palce */
.spodni{position:fixed;left:0;right:0;bottom:0;z-index:30;display:grid;grid-template-columns:1fr 1fr 1fr 1.25fr;
align-items:center;gap:4px;height:calc(var(--spodek) + env(safe-area-inset-bottom));padding:6px 8px calc(6px + env(safe-area-inset-bottom));
background:var(--papir);border-top:1px solid var(--linka)}
.spodni a{position:relative;display:flex;flex-direction:column;align-items:center;gap:2px;font-size:10.5px;font-weight:500;color:var(--ocel)}
.spodni a.aktivni{color:var(--inkoust)}
.spodni em{position:absolute;top:-4px;left:calc(50% + 6px);min-width:17px;height:17px;padding:0 4px;border-radius:9px;
background:var(--oranzova);color:#fff;font-style:normal;font-size:10px;font-weight:700;line-height:17px;text-align:center}
.spodni a.poptat{flex-direction:row;justify-content:center;height:48px;background:var(--inkoust);color:var(--papir);font-size:15px;font-weight:600}

/* hledání přes celou obrazovku */
.hledani{position:fixed;inset:0;z-index:50;background:var(--papir);overflow-y:auto;padding:0 16px 24px}
.hledani[hidden]{display:none}
.hledani-hlava{position:sticky;top:0;display:flex;gap:12px;align-items:center;height:64px;background:var(--papir);border-bottom:1px solid var(--inkoust)}
.hledani-hlava input{flex:1;min-width:0;height:44px;border:0;background:none;color:inherit;font:inherit;font-size:20px;font-weight:600;outline:none}
.hledani-hlava input::-webkit-search-cancel-button{-webkit-appearance:none}
.hledani-hlava button{font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.1em;text-transform:uppercase}
.chipy{display:flex;flex-wrap:wrap;gap:8px;padding:16px 0}
.chipy button{min-height:36px;padding:0 14px;border:1px solid var(--linka);border-radius:18px;font-size:14px}
.chipy button.aktivni{background:var(--inkoust);color:var(--papir);border-color:var(--inkoust)}
.vysledky{list-style:none;margin:0;padding:0}
.vysledky a{display:grid;grid-template-columns:56px 1fr;gap:12px;align-items:center;padding:8px 0;border-bottom:1px solid var(--linka)}
.vysledky img{width:56px;height:56px;object-fit:contain;background:var(--bila)}
.vysledky b{display:block;font-size:15px;font-weight:600}

.toast{position:fixed;left:16px;right:16px;bottom:calc(var(--spodek) + 12px + env(safe-area-inset-bottom));z-index:40;
padding:14px 16px;background:var(--inkoust);color:var(--papir);font-size:14px;font-weight:500;
opacity:0;transform:translateY(8px);transition:.2s;pointer-events:none}
.toast.vidno{opacity:1;transform:none}
@media (prefers-reduced-motion:reduce){*{transition:none!important;scroll-behavior:auto!important}}
"""

JS = r"""
(function () {
  /* kategorie: jedna otevřená naráz */
  var kat = document.querySelectorAll("[data-kat]");
  kat.forEach(function (k) {
    k.querySelector("[data-kat-tl]").addEventListener("click", function () {
      var otevrit = !k.classList.contains("otevrena");
      kat.forEach(function (x) {
        x.classList.remove("otevrena");
        x.querySelector("[data-kat-tl]").setAttribute("aria-expanded", "false");
      });
      if (otevrit) {
        k.classList.add("otevrena");
        this.setAttribute("aria-expanded", "true");
      }
    });
  });

  /* šanon: jen počítadlo pro ukázku */
  var pocet = 0, toast = document.querySelector("[data-toast]"), cas;
  document.querySelectorAll("[data-do-sanonu]").forEach(function (b) {
    b.addEventListener("click", function () {
      pocet++;
      document.querySelector("[data-pocet]").textContent = pocet;
      toast.classList.add("vidno");
      clearTimeout(cas);
      cas = setTimeout(function () { toast.classList.remove("vidno"); }, 1600);
    });
  });

  /* hledání */
  var okno = document.querySelector("[data-hledani]");
  var pole = document.querySelector("[data-hledani-pole]");
  var vys = document.querySelector("[data-vysledky]");
  var chip = "";
  function norm(s) { return s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, ""); }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]; }); }
  function vykresli() {
    var q = norm(pole.value.trim());
    var r = PRODUKTY.filter(function (p) {
      return (!chip || p.k === chip) && (!q || norm(p.n + " " + p.k + " " + p.r).indexOf(q) > -1);
    });
    vys.innerHTML = r.map(function (p) {
      return '<li><a href="produkt.html?rada=' + encodeURIComponent(p.id) + '"><img src="' + esc(p.f) + '" alt="">'
        + '<span><b>' + esc(p.n) + '</b><span class="mono">' + esc(p.k) + ' · ' + esc(p.r) + '</span></span></a></li>';
    }).join("") || '<li class="mono" style="padding:16px 0">Nic nenalezeno. Zavolejte, ušijeme to.</li>';
  }
  document.querySelector("[data-otevrit-hledani]").addEventListener("click", function () {
    okno.hidden = false; document.body.style.overflow = "hidden"; vykresli(); pole.focus();
  });
  document.querySelector("[data-zavrit-hledani]").addEventListener("click", function () {
    okno.hidden = true; document.body.style.overflow = "";
  });
  pole.addEventListener("input", vykresli);
  document.querySelectorAll("[data-chip]").forEach(function (b) {
    b.addEventListener("click", function () {
      var k = b.getAttribute("data-chip");
      chip = chip === k ? "" : k;
      document.querySelectorAll("[data-chip]").forEach(function (x) {
        x.classList.toggle("aktivni", x.getAttribute("data-chip") === chip);
      });
      vykresli();
    });
  });
})();
"""


NAHLED = """<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>M+P Král · mobilní náhled</title>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@600;800&family=IBM+Plex+Mono&display=swap" rel="stylesheet">
<style>
body{margin:0;min-height:100vh;background:#e4e1d9;font-family:Archivo,sans-serif;color:#111110}
header{padding:28px 40px 0}
h1{margin:0;font-size:28px;font-weight:800;text-transform:uppercase;letter-spacing:-.02em}
header p{margin:6px 0 0;font-family:"IBM Plex Mono",monospace;font-size:12px;color:#706d66}
.telefony{display:flex;gap:48px;justify-content:center;flex-wrap:wrap;padding:32px 24px 48px}
figure{margin:0;text-align:center}
.telefon{width:414px;height:868px;padding:12px;border-radius:56px;background:#111110;
box-shadow:0 40px 80px -30px rgba(0,0,0,.45),inset 0 0 0 2px #3a3a38}
iframe{width:390px;height:844px;border:0;border-radius:44px;background:#f2f0eb;display:block}
figcaption{margin-top:16px;font-family:"IBM Plex Mono",monospace;font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:#706d66}
</style>
</head>
<body>
<header>
  <h1>M+P Král · mobilní verze</h1>
  <p>390 × 844 (iPhone 15). Obě obrazovky jsou živé, dá se v nich posouvat a klikat.</p>
</header>
<div class="telefony">
  <figure><div class="telefon"><iframe src="mobil.html" title="Úvod"></iframe></div><figcaption>Úvod</figcaption></figure>
  <figure><div class="telefon"><iframe src="mobil.html#co-sijeme" title="Co šijeme"></iframe></div><figcaption>Co šijeme · kategorie</figcaption></figure>
</div>
</body>
</html>
"""

(VYSTUP / "mobil.html").write_text(stranka(), encoding="utf-8")
(VYSTUP / "mobil-nahled.html").write_text(NAHLED, encoding="utf-8")
print("mobil.html, mobil-nahled.html")
