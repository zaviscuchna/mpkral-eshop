"""Upozornění e-mailem. Dokud není nastavený SMTP (proměnné MPK_SMTP_*), nedělá nic:
objednávky a poptávky zůstávají v administraci, kde je obsluha vidí."""
import os
import smtplib
from email.message import EmailMessage


def _posli(komu, predmet, text):
    host = os.environ.get("MPK_SMTP_HOST")
    if not host or not komu:
        return False
    zprava = EmailMessage()
    zprava["From"] = os.environ.get("MPK_SMTP_OD", os.environ.get("MPK_SMTP_UZIVATEL", ""))
    zprava["To"] = komu
    zprava["Subject"] = predmet
    zprava.set_content(text)
    try:
        with smtplib.SMTP(host, int(os.environ.get("MPK_SMTP_PORT", 587)), timeout=15) as s:
            s.starttls()
            s.login(os.environ["MPK_SMTP_UZIVATEL"], os.environ["MPK_SMTP_HESLO"])
            s.send_message(zprava)
        return True
    except Exception:
        return False                     # objednávka je uložená tak jako tak


def nova_objednavka(cislo):
    _posli(os.environ.get("MPK_UPOZORNENI_NA"), f"Nová objednávka {cislo}",
           f"Na webu přišla objednávka {cislo}. Podrobnosti jsou v administraci.")


def nova_poptavka():
    _posli(os.environ.get("MPK_UPOZORNENI_NA"), "Nová poptávka z webu",
           "Na webu přišla poptávka. Podrobnosti jsou v administraci.")
