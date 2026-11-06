"""E-shop M+P Král: statický web z build.py + administrace + objednávky.

Lokálně:  .venv/bin/flask --app eshop run -p 5068     (data v ./instance)
Server:   gunicorn 'eshop:create_app()'  s DATA_DIR=/opt/mpkral/data PROXY=1
"""
import os
import secrets
from datetime import timedelta
from pathlib import Path

from flask import Flask, request

from . import db as dbm

KOREN = Path(__file__).resolve().parent.parent


def _secret_key(data_dir):
    klic = os.environ.get("SECRET_KEY")
    if klic:
        return klic
    cesta = data_dir / ".secret_key"
    if not cesta.exists():
        cesta.write_text(secrets.token_hex(32))
        cesta.chmod(0o600)
    return cesta.read_text().strip()


def create_app(data_dir=None):
    data_dir = Path(data_dir or os.environ.get("DATA_DIR") or KOREN / "instance").resolve()
    data_dir.mkdir(parents=True, exist_ok=True)
    proxy = os.environ.get("PROXY") == "1"

    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=_secret_key(data_dir),
        DATA_DIR=str(data_dir),
        DB_CESTA=str(data_dir / "eshop.db"),
        MAX_CONTENT_LENGTH=40 * 1024 * 1024,          # tři fotky z telefonu najednou
        SESSION_COOKIE_NAME="mpk_admin",
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=proxy,
        PERMANENT_SESSION_LIFETIME=timedelta(days=7),
        TESTOVACI=os.environ.get("TESTOVACI") == "1",  # testovací adresa: celý web mimo vyhledávače
    )
    if proxy:
        # za Traefikem: správné https a skutečná IP klienta (jen z první proxy, hlavičce zvenku nevěříme)
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    app.teardown_appcontext(dbm.zavri)
    with app.app_context():
        con = dbm.pripoj(app.config["DB_CESTA"])
        dbm.vytvor(con)
        from .katalog import naplnit_z_repa
        naplnit_z_repa(con)
        con.close()

    from .web import bp as web_bp
    from .admin import bp as admin_bp
    app.register_blueprint(web_bp)
    app.register_blueprint(admin_bp)
    from .cli import registruj
    registruj(app)
    _hlavicky(app, proxy)
    if not (data_dir / "web" / "index.html").exists():     # první spuštění: postavit web z databáze
        with app.app_context():
            from .katalog import publikovat
            ok, zprava = publikovat()
            if not ok:
                app.logger.error("první publikace selhala: %s", zprava)
    return app


CSP_WEB = ("default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
           "font-src https://fonts.gstatic.com; script-src 'self' 'unsafe-inline'; connect-src 'self'; "
           "frame-ancestors 'none'; base-uri 'self'; form-action 'self'; object-src 'none'")
# administrace nemá žádný inline skript, takže tu může být přísná politika
CSP_ADMIN = ("default-src 'self'; img-src 'self' data: blob:; style-src 'self'; script-src 'self'; "
             "connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'; object-src 'none'")


def _hlavicky(app, proxy):
    @app.after_request
    def hlavicky(resp):
        admin = request.path.startswith("/admin")
        resp.headers["Content-Security-Policy"] = CSP_ADMIN if admin else CSP_WEB
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-Frame-Options"] = "DENY"
        resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        resp.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=()"
        if proxy:
            resp.headers["Strict-Transport-Security"] = "max-age=31536000"
        if admin or request.path.startswith(("/api", "/objednavka")):
            resp.headers["Cache-Control"] = "no-store"
            resp.headers["X-Robots-Tag"] = "noindex, nofollow"
        elif app.config["TESTOVACI"]:
            resp.headers["X-Robots-Tag"] = "noindex, nofollow"
        return resp
