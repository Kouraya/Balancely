import hashlib
import datetime
import re
import smtplib
import random
import pandas as pd
import streamlit as st
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def make_hashes(text):
    return hashlib.sha256(str.encode(text)).hexdigest()


def check_password_strength(pw):
    if len(pw) < 6:
        return False, "Mindestens 6 Zeichen erforderlich."
    if not re.search(r"[a-z]", pw):
        return False, "Mindestens ein Kleinbuchstabe erforderlich."
    if not re.search(r"[A-Z]", pw):
        return False, "Mindestens ein Großbuchstabe erforderlich."
    return True, ""


def is_valid_email(e):
    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", e))


def generate_code():
    return str(random.randint(100000, 999999))


def is_verified(v):
    try:
        return float(v) >= 1.0
    except:
        return str(v).strip().lower() in ('true', '1', 'yes')


def format_timestamp(ts_str, datum_str):
    now = datetime.datetime.now()
    today = now.date()
    try:
        ts = datetime.datetime.strptime(str(ts_str).strip(), "%Y-%m-%d %H:%M")
        uhr = ts.strftime("%H:%M")
        if ts.date() == today:
            return f"heute {uhr}"
        if ts.date() == today - datetime.timedelta(days=1):
            return f"gestern {uhr}"
        return ts.strftime("%d.%m.%Y %H:%M")
    except:
        try:
            d = datetime.date.fromisoformat(str(datum_str))
            if d == today:
                return "heute"
            if d == today - datetime.timedelta(days=1):
                return "gestern"
            return d.strftime("%d.%m.%Y")
        except:
            return str(datum_str)


def find_row_mask(df, row):
    return (
        (df['user'] == row['user']) &
        (df['datum'].astype(str) == str(row['datum'])) &
        (pd.to_numeric(df['betrag'], errors='coerce') == pd.to_numeric(row['betrag'], errors='coerce')) &
        (df['kategorie'] == row['kategorie']) &
        (~df['deleted'].astype(str).str.strip().str.lower().isin(['true', '1', '1.0']))
    )


def send_email(to_email, subject, html_content):
    try:
        sender = st.secrets["email"]["sender"]
        password = st.secrets["email"]["password"]
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"Balancely ⚖️ <{sender}>"
        msg["To"] = to_email
        msg.attach(MIMEText(html_content, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(sender, password)
            s.sendmail(sender, to_email, msg.as_string())
        return True
    except Exception as e:
        st.error(f"Email-Fehler: {e}")
        return False


def email_html(text, code):
    return f"""<html><body style="font-family:sans-serif;background:#020617;color:#f1f5f9;padding:40px;">
    <div style="max-width:480px;margin:auto;background:#0f172a;border-radius:16px;padding:40px;border:1px solid #1e293b;">
        <h2 style="color:#38bdf8;">Balancely ⚖️</h2><p>{text}</p>
        <div style="margin:24px 0;padding:20px;background:#1e293b;border-radius:12px;text-align:center;
                    font-size:36px;font-weight:800;letter-spacing:8px;color:#38bdf8;">{code}</div>
        <p style="color:#94a3b8;font-size:13px;">Dieser Code ist 10 Minuten gültig.<br>
        Falls du diese Anfrage nicht gestellt hast, ignoriere diese Email.</p>
    </div></body></html>"""
