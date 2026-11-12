"""Přihlášení, CSRF a omezení počtu pokusů. Pokusy se počítají v databázi, ne v paměti
procesu — server běží s víc workery a limit v paměti by se dal obejít."""
import hashlib
import secrets
import time
from functools import wraps

from flask import abort, current_app, g, redirect, request, session, url_for

from .db import db


def csrf_token():
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_urlsafe(32)
    return session["_csrf"]


def over_csrf():
    tok = request.form.get("_csrf") or request.headers.get("X-CSRF")
    if not tok or not secrets.compare_digest(tok, session.get("_csrf", "")):
        abort(400, "Formulář vypršel. Načtěte prosím stránku znovu.")


def ip():
    # za Traefikem ji opravuje ProxyFix (PROXY=1); hlavičce od klienta nevěříme
    return request.remote_addr or ""


def otisk(text):
    """IP adresy ukládáme jen jako otisk se solí (k omezení pokusů stačí, k identifikaci ne)."""
    return hashlib.sha256((current_app.config["SECRET_KEY"] + "|" + text).encode()).hexdigest()[:24]


def prekroceno(druh, klic, max_pocet, okno_s, jen_neuspechy=True):
    od = time.time() - okno_s
    q = "SELECT COUNT(*) FROM pokus WHERE druh = ? AND klic = ? AND kdy > ?" + (" AND uspech = 0" if jen_neuspechy else "")
    return db().execute(q, (druh, otisk(klic), od)).fetchone()[0] >= max_pocet


def zapis_pokus(druh, klic, uspech=False):
    db().execute("INSERT INTO pokus (druh, klic, kdy, uspech) VALUES (?, ?, ?, ?)",
                 (druh, otisk(klic), time.time(), 1 if uspech else 0))
    db().execute("DELETE FROM pokus WHERE kdy < ?", (time.time() - 7 * 86400,))
    db().commit()


def prihlaseny():
    """Aktuální uživatel, nebo None. Změna hesla (verze) odhlásí všechna ostatní zařízení."""
    if "uzivatel" in g:
        return g.uzivatel
    g.uzivatel = None
    uid = session.get("uid")
    if uid:
        u = db().execute("SELECT * FROM uzivatel WHERE id = ? AND aktivni = 1", (uid,)).fetchone()
        if u and u["verze_hesla"] == session.get("ver"):
            g.uzivatel = u
        else:
            session.clear()
    return g.uzivatel


def prihlasen(role=None):
    def dekorator(f):
        @wraps(f)
        def obal(*a, **kw):
            u = prihlaseny()
            if u is None:
                return redirect(url_for("admin.prihlaseni", dalsi=request.path))
            if role and u["role"] != role:
                abort(403)
            return f(*a, **kw)
        return obal
    return dekorator
