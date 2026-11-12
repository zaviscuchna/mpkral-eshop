"""Příkazy pro správu z terminálu:

  flask --app eshop publikovat
  flask --app eshop pridat-uzivatele mamka "Jméno Příjmení" --adresa https://…   → odkaz pro nastavení hesla
  flask --app eshop zaloha /cesta/soubor.db
"""
import secrets
import sqlite3
from datetime import datetime, timedelta

import click

from .db import db, ted, zapis_audit
from .katalog import publikovat


def registruj(app):
    @app.cli.command("publikovat")
    def publikovat_cmd():
        ok, zprava = publikovat()
        click.echo(zprava if ok else "CHYBA: " + zprava)
        raise SystemExit(0 if ok else 1)

    @app.cli.command("pridat-uzivatele")
    @click.argument("login")
    @click.argument("jmeno")
    @click.option("--role", type=click.Choice(["obsluha", "spravce"]), default="obsluha")
    @click.option("--adresa", required=True, help="Veřejná adresa webu, např. https://mpkral.cz")
    def pridat(login, jmeno, role, adresa):
        login = login.strip().lower()
        u = db().execute("SELECT id FROM uzivatel WHERE login = ?", (login,)).fetchone()
        uid = u["id"] if u else db().execute("INSERT INTO uzivatel (login, jmeno, role, vytvoren) VALUES (?,?,?,?)",
                                             (login, jmeno, role, ted())).lastrowid
        token = secrets.token_urlsafe(32)
        plati = (datetime.now() + timedelta(days=3)).isoformat(timespec="seconds")
        db().execute("UPDATE uzivatel SET nastavovaci_token = ?, token_plati_do = ? WHERE id = ?", (token, plati, uid))
        zapis_audit("terminál", "odkaz pro nastavení hesla", f"{login} ({role})")
        db().commit()
        click.echo(f"{adresa.rstrip('/')}/admin/nastavit-heslo/{token}")
        click.echo(f"(platí 3 dny, do {plati})")

    @app.cli.command("zaloha")
    @click.argument("cil")
    def zaloha(cil):
        """Konzistentní kopie databáze i za běhu (sqlite backup API)."""
        dst = sqlite3.connect(cil)
        db().backup(dst)
        dst.close()
        click.echo(cil)
