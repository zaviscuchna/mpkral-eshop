"""Databáze e-shopu: obyčejné sqlite3, jeden soubor v DATA_DIR.

Peníze jsou všude v haléřích (int), ať se nesčítají desetinná čísla.
"""
import json
import sqlite3
from datetime import datetime

from flask import current_app, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS uzivatel (
  id INTEGER PRIMARY KEY,
  login TEXT UNIQUE NOT NULL,
  jmeno TEXT NOT NULL,
  heslo TEXT,
  verze_hesla INTEGER NOT NULL DEFAULT 0,
  role TEXT NOT NULL DEFAULT 'obsluha',
  aktivni INTEGER NOT NULL DEFAULT 1,
  vytvoren TEXT NOT NULL,
  posledni_prihlaseni TEXT,
  nastavovaci_token TEXT,
  token_plati_do TEXT
);
CREATE TABLE IF NOT EXISTS pokus (
  id INTEGER PRIMARY KEY,
  druh TEXT NOT NULL,
  klic TEXT NOT NULL,
  kdy REAL NOT NULL,
  uspech INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS pokus_klic ON pokus(druh, klic, kdy);
CREATE TABLE IF NOT EXISTS produkt (
  id TEXT PRIMARY KEY,
  nazev TEXT NOT NULL,
  kategorie TEXT NOT NULL,
  znacka TEXT NOT NULL,
  predmet TEXT NOT NULL DEFAULT '',
  material TEXT NOT NULL DEFAULT '',
  gramaz TEXT NOT NULL DEFAULT '',
  velikosti TEXT NOT NULL DEFAULT '',
  popis TEXT NOT NULL DEFAULT '',
  pouziti TEXT NOT NULL DEFAULT '',
  norma TEXT NOT NULL DEFAULT '',
  cena INTEGER,
  hladiny TEXT NOT NULL DEFAULT '{}',
  overeno INTEGER NOT NULL DEFAULT 0,
  viditelny INTEGER NOT NULL DEFAULT 1,
  poradi INTEGER NOT NULL DEFAULT 0,
  upraveno TEXT
);
CREATE TABLE IF NOT EXISTS varianta (
  id INTEGER PRIMARY KEY,
  produkt_id TEXT NOT NULL REFERENCES produkt(id) ON DELETE CASCADE,
  slug TEXT NOT NULL,
  nazev TEXT NOT NULL,
  strih TEXT NOT NULL DEFAULT '',
  foto_predni TEXT,
  foto_zadni TEXT,
  foto_detail TEXT,
  vzornik TEXT,
  viditelna INTEGER NOT NULL DEFAULT 1,
  poradi INTEGER NOT NULL DEFAULT 0,
  UNIQUE(produkt_id, slug)
);
CREATE TABLE IF NOT EXISTS nastaveni (
  klic TEXT PRIMARY KEY,
  hodnota TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS objednavka (
  id INTEGER PRIMARY KEY,
  cislo TEXT UNIQUE NOT NULL,
  token TEXT UNIQUE NOT NULL,
  vytvoreno TEXT NOT NULL,
  stav TEXT NOT NULL DEFAULT 'nova',
  zakaznik TEXT NOT NULL,
  polozky TEXT NOT NULL,
  doprava TEXT NOT NULL,
  platba TEXT NOT NULL,
  zbozi INTEGER NOT NULL,
  bez_dph INTEGER NOT NULL,
  dph INTEGER NOT NULL,
  celkem INTEGER NOT NULL,
  sazba_dph INTEGER NOT NULL,
  na_dotaz INTEGER NOT NULL DEFAULT 0,
  poznamka TEXT NOT NULL DEFAULT '',
  interni_poznamka TEXT NOT NULL DEFAULT '',
  souhlas_kdy TEXT NOT NULL,
  upraveno TEXT
);
CREATE TABLE IF NOT EXISTS poptavka (
  id INTEGER PRIMARY KEY,
  vytvoreno TEXT NOT NULL,
  stav TEXT NOT NULL DEFAULT 'nova',
  firma TEXT NOT NULL DEFAULT '',
  ico TEXT NOT NULL DEFAULT '',
  osoba TEXT NOT NULL DEFAULT '',
  telefon TEXT NOT NULL DEFAULT '',
  email TEXT NOT NULL DEFAULT '',
  objednavka TEXT NOT NULL DEFAULT '',
  poznamka TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS audit (
  id INTEGER PRIMARY KEY,
  kdy TEXT NOT NULL,
  kdo TEXT NOT NULL,
  akce TEXT NOT NULL,
  detail TEXT NOT NULL DEFAULT ''
);
"""


def ted():
    return datetime.now().isoformat(timespec="seconds")


def pripoj(cesta):
    con = sqlite3.connect(cesta, timeout=15)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.execute("PRAGMA journal_mode = WAL")
    con.execute("PRAGMA busy_timeout = 15000")
    return con


def db():
    if "db" not in g:
        g.db = pripoj(current_app.config["DB_CESTA"])
    return g.db


def zavri(_=None):
    con = g.pop("db", None)
    if con is not None:
        con.close()


def vytvor(con):
    con.executescript(SCHEMA)
    con.commit()


def nast(klic, vychozi=None):
    """Nastavení obchodu je uložené jako JSON (čísla, seznamy dopravy a plateb…)."""
    r = db().execute("SELECT hodnota FROM nastaveni WHERE klic = ?", (klic,)).fetchone()
    return json.loads(r["hodnota"]) if r else vychozi


def uloz_nast(klic, hodnota, con=None):
    (con or db()).execute(
        "INSERT INTO nastaveni (klic, hodnota) VALUES (?, ?) "
        "ON CONFLICT(klic) DO UPDATE SET hodnota = excluded.hodnota",
        (klic, json.dumps(hodnota, ensure_ascii=False)))


def zapis_audit(kdo, akce, detail="", con=None):
    (con or db()).execute("INSERT INTO audit (kdy, kdo, akce, detail) VALUES (?, ?, ?, ?)",
                          (ted(), kdo, akce, detail[:2000]))
