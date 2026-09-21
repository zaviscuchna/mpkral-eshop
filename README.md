# M+P Král — náčrt e-shopu

Statický náčrt pro klienta. Žádný backend, žádný build, žádné knihovny.
Otevři dvojklikem na **`SPUSTIT NAHLED.command`** (přes `file://` by se nenačetl
katalog ani šanon).

## Stránky
| soubor | co to je |
|---|---|
| `index.html` | homepage — hero, čísla, kategorie, řady, nejžádanější, detail pás, zakázka, zdravotnictví, profese, poptávka |
| `katalog.html` | výpis všech střihů s filtry a řazením |
| `produkt.html` | detail produktu, postavený na Bundě King |
| `sanon.html` | poptávkový „košík" včetně tisku |

## Směr návrhu — editorial
Původní směr „Střihárna" (dílenská dokumentace) dostal editorial vrstvu podle
referenčního magazínu: obří verzálkový headline, serifový deck v EB Garamond,
produkty leží **volně na ploše bez rámečků a stínů**, popisky verzálkami v monu,
hodně vzduchu. Nadpisy sekcí zůstaly sázené jako kóta na střihovém výkresu.

Podklad `#F2F0EB`, inkoust `#111110`, oranžová `#D8431A` jen na hover primárního
tlačítka. Produktové panely jsou bílé, protože fotky mají natvrdo bílé pozadí.

Slovník je vynucený: **šijeme, konstruujeme, nasamplujeme, střih, dílna** —
nikdy „nabízíme", „dodáváme", „sortiment", „zboží". Hlavní akce je vždy **poptávka**,
nikdy „koupit".

## Data
- `data/katalog.json` — 17 řad, 39 barevných variant, 104 fotek
- `data/meta.json` — texty řad, profese, co se připravuje
- `img/produkty/` — fotky 640×640 JPEG
- `img/vzorniky/` — výřezy látky 112×112, vyříznuté z produktových fotek

Přestavit stránky po změně dat: `python3 build.py`

Zdroj fotek je pipeline v `~/Projects/eshop-fotky`. Řetěz:
`bin/katalog.py` → `bin/web_fotky.py` → `bin/obohatit.py` → `build.py`

## Co je zástupné
**Všechny technické údaje** — materiál, gramáž, čísla střihů, normy, dodací lhůty,
telefon, kontaktní osoba. Na webu mají tečkované podtržení a v patičce je disclaimer.
Než to půjde do produkce, musí je M+P Král doplnit.

**Ceny nejsou nikde.** Místo nich je řádek „Cena podle množství a úpravy" a tabulka
množstevních hladin vyplněná pomlčkami. Až ceny přijdou, doplní se tři čísla do
připravené tabulky — layout se nemění.

## Co v náčrtu chybí, protože nejsou fotky
- celá **reflexní řada** (18 řad)
- **Zimní kombinéza King** (5 barev)
- **Pracovní plášť** — 1 varianta ze 3

Mají vlastní kartu „Fotografie dokončujeme" vykreslenou rýsovacími linkami,
takže výpis nevypadá rozbitě.

## Známá omezení náčrtu
- formuláře nic neodesílají, jen zobrazí potvrzení
- šanon žije v `localStorage` daného prohlížeče
- `produkt.html` je postavený jen pro Bundu King, ostatní řady na něj odkazují
- tmavý režim převrací jen rám stránky; produktové karty zůstávají bílé záměrně —
  invertovaná pracovní bunda je horší než žádný tmavý režim


## Na co si dát pozor při úpravách
1. **`.obal` se kombinuje s dalšími třídami** (`obal sekce`, `obal radek`).
   Proto smí být boční odsazení jen `padding-inline` a ostatní třídy jen
   `padding-block`. Zkratka `padding: X 0` boky vynuluje a obsah uteče k okraji.
2. **Žádné inline `grid-template-columns`** — přebije media queries a rozbije mobil.
3. **Rozpis velikostí nikdy jako tabulka s 11 sloupci.** Je to mřížka
   `repeat(auto-fill, minmax(68px, 1fr))`, která se zalamuje. Tabulka rozstřelila
   kartu na 694 px a stránku na 2463 px — třetí sloupec produktů pak byl nedostupný.
4. **Kontrolovat přetékání měřením, ne screenshotem.** macOS Chrome neumí okno
   pod ~500 px, takže mobilní screenshot lže. Měřit `documentElement.scrollWidth`
   v iframu nastaveném na cílovou šířku.
