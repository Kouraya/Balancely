import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import hashlib
import datetime
import re
import smtplib
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

st.set_page_config(page_title="Balancely", page_icon="⚖️", layout="wide")

def make_hashes(text):
    return hashlib.sha256(str.encode(text)).hexdigest()

def check_password_strength(password):
    if len(password) < 6:
        return False, "Das Passwort muss mindestens 6 Zeichen lang sein."
    if not re.search(r"[a-z]", password):
        return False, "Das Passwort muss mindestens einen Kleinbuchstaben enthalten."
    if not re.search(r"[A-Z]", password):
        return False, "Das Passwort muss mindestens einen Großbuchstaben enthalten."
    return True, ""

def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def generate_code():
    return str(random.randint(100000, 999999))

def send_email(to_email, subject, html_content):
    try:
        sender = st.secrets["email"]["sender"]
        password = st.secrets["email"]["password"]
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"Balancely ⚖️ <{sender}>"
        msg["To"] = to_email
        msg.attach(MIMEText(html_content, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, to_email, msg.as_string())
        return True
    except Exception as e:
        st.error(f"Email-Fehler: {e}")
        return False

def email_html(text, code):
    return f"""
    <html><body style="font-family:sans-serif;background:#020617;color:#f1f5f9;padding:40px;">
        <div style="max-width:480px;margin:auto;background:#0f172a;border-radius:16px;
             padding:40px;border:1px solid #1e293b;">
            <h2 style="color:#38bdf8;">Balancely ⚖️</h2>
            <p>{text}</p>
            <div style="margin:24px 0;padding:20px;background:#1e293b;border-radius:12px;
                text-align:center;font-size:36px;font-weight:800;letter-spacing:8px;color:#38bdf8;">
                {code}
            </div>
            <p style="color:#94a3b8;font-size:13px;">
                Dieser Code ist 10 Minuten gültig.<br>
                Falls du diese Anfrage nicht gestellt hast, ignoriere diese Email.
            </p>
        </div>
    </body></html>
    """

st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] {
        background: radial-gradient(circle at top right, #1e293b, #0f172a, #020617) !important;
    }
    .main-title {
        text-align: center; color: #f8fafc; font-size: 64px; font-weight: 800;
        letter-spacing: -2px; margin-bottom: 0px;
        text-shadow: 0 0 30px rgba(56, 189, 248, 0.4);
    }
    .sub-title {
        text-align: center; color: #94a3b8; font-size: 18px; margin-bottom: 40px;
    }
    [data-testid="stForm"] {
        background-color: rgba(30, 41, 59, 0.7) !important;
        backdrop-filter: blur(15px);
        padding: 40px !important;
        border-radius: 24px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    div[data-testid="stTextInputRootElement"] {
        background-color: transparent !important;
    }
    div[data-baseweb="input"],
    div[data-baseweb="base-input"] {
        background-color: transparent !important;
        border: 1px solid #1e293b !important;
        border-radius: 8px !important;
        padding-right: 0 !important;
        gap: 0 !important;
        box-shadow: none !important;
    }
    div[data-baseweb="input"]:focus-within,
    div[data-baseweb="base-input"]:focus-within {
        background-color: transparent !important;
        border-color: #38bdf8 !important;
        box-shadow: none !important;
    }
    div[data-testid="stDateInput"] > div {
        background-color: transparent !important;
        border: 1px solid #1e293b !important;
        border-radius: 8px !important;
        box-shadow: none !important;
    }
    div[data-baseweb="select"] > div:first-child {
        background-color: transparent !important;
        border: 1px solid #1e293b !important;
        border-radius: 8px !important;
        box-shadow: none !important;
    }
    div[data-baseweb="select"] > div:first-child:focus-within {
        border-color: #38bdf8 !important;
        box-shadow: none !important;
    }
    button[data-testid="stNumberInputStepDown"],
    button[data-testid="stNumberInputStepUp"] {
        display: none !important;
    }
    div[data-baseweb="input"] > div:not(:has(input)):not(:has(button)):not(:has(svg)) {
        display: none !important;
    }
    [data-testid="InputInstructions"],
    [data-testid="stInputInstructions"],
    div[class*="InputInstructions"],
    div[class*="stInputInstructions"] {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        overflow: hidden !important;
        position: absolute !important;
    }
    input { padding-left: 15px !important; color: #f1f5f9 !important; }
    [data-testid="stSidebar"] {
        background-color: #0b0f1a !important;
        border-right: 1px solid #1e293b !important;
    }
    button[kind="primaryFormSubmit"] {
        background: linear-gradient(135deg, #38bdf8, #1d4ed8) !important;
        border: none !important; height: 50px !important;
        border-radius: 12px !important; font-weight: 700 !important;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] > div > label {
        border: 1px solid #1e293b !important;
        border-radius: 10px !important;
        padding: 8px 12px !important;
        margin-bottom: 4px !important;
        color: #94a3b8 !important;
        transition: all 0.15s ease !important;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] > div > label:hover {
        border-color: #38bdf8 !important;
        color: #f1f5f9 !important;
        background: rgba(56,189,248,0.08) !important;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] > div > label:has(input:checked) {
        border-color: #38bdf8 !important;
        background: rgba(56,189,248,0.15) !important;
        color: #f1f5f9 !important;
        font-weight: 600 !important;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] > div > label > div:first-child {
        display: none !important;
    }
    </style>
""", unsafe_allow_html=True)

if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'user_name' not in st.session_state: st.session_state['user_name'] = ""
if 'auth_mode' not in st.session_state: st.session_state['auth_mode'] = 'login'
if 't_type' not in st.session_state: st.session_state['t_type'] = 'Ausgabe'
if 'pending_user' not in st.session_state: st.session_state['pending_user'] = {}
if 'verify_code' not in st.session_state: st.session_state['verify_code'] = ""
if 'verify_expiry' not in st.session_state: st.session_state['verify_expiry'] = None
if 'reset_email' not in st.session_state: st.session_state['reset_email'] = ""
if 'reset_code' not in st.session_state: st.session_state['reset_code'] = ""
if 'reset_expiry' not in st.session_state: st.session_state['reset_expiry'] = None

conn = st.connection("gsheets", type=GSheetsConnection)

if st.session_state['logged_in']:
    with st.sidebar:
        st.markdown("<h2 style='color:white;'>Balancely ⚖️</h2>", unsafe_allow_html=True)
        st.markdown(f"👤 Eingeloggt: **{st.session_state['user_name']}**")
        st.markdown("---")
        menu = st.radio("Navigation", ["📈 Dashboard", "💸 Transaktion", "📂 Analysen", "⚙️ Einstellungen"], label_visibility="collapsed")
        st.markdown("<div style='height: 30vh;'></div>", unsafe_allow_html=True)
        if st.button("Logout ➜", use_container_width=True, type="secondary"):
            st.session_state['logged_in'] = False
            st.rerun()

    if menu == "📈 Dashboard":
        st.title(f"Deine Übersicht, {st.session_state['user_name']}! ⚖️")
        try:
            df_t = conn.read(worksheet="transactions", ttl="0")
            if 'user' in df_t.columns:
                user_df = df_t[df_t['user'] == st.session_state['user_name']]
                if not user_df.empty:
                    ein = pd.to_numeric(user_df[user_df['typ'] == "Einnahme"]['betrag']).sum()
                    aus = abs(pd.to_numeric(user_df[user_df['typ'] == "Ausgabe"]['betrag']).sum())
                    bal = ein - aus
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Kontostand", f"{bal:,.2f} €")
                    c2.metric("Einnahmen", f"{ein:,.2f} €")
                    c3.metric("Ausgaben", f"{aus:,.2f} €", delta_color="inverse")
                    st.subheader("Ausgaben nach Kategorie")
                    ausg_df = user_df[user_df['typ'] == "Ausgabe"].copy()
                    ausg_df['betrag'] = abs(pd.to_numeric(ausg_df['betrag']))
                    st.bar_chart(data=ausg_df, x="kategorie", y="betrag", color="kategorie")
                else:
                    st.info("Noch keine Daten vorhanden.")
        except:
            st.warning("Verbindung wird hergestellt...")

    elif menu == "💸 Transaktion":
        st.title("Buchung hinzufügen ✍️")
        t_type = st.session_state['t_type']
        st.markdown("<p style='color:#94a3b8; font-size:13px; margin-bottom:4px;'>Typ wählen</p>", unsafe_allow_html=True)
        col_a, col_e, _ = st.columns([1, 1, 3])
        with col_a:
            if st.button("↗ Ausgabe ✓" if t_type == "Ausgabe" else "↗ Ausgabe", key="btn_ausgabe", use_container_width=True, type="primary" if t_type == "Ausgabe" else "secondary"):
                st.session_state['t_type'] = "Ausgabe"
                st.rerun()
        with col_e:
            if st.button("↙ Einnahme ✓" if t_type == "Einnahme" else "↙ Einnahme", key="btn_einnahme", use_container_width=True, type="primary" if t_type == "Einnahme" else "secondary"):
                st.session_state['t_type'] = "Einnahme"
                st.rerun()
        st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)
        with st.form("t_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                t_amount = st.number_input("Betrag in €", min_value=0.01, step=0.01, format="%.2f")
                t_date = st.date_input("Datum", datetime.date.today())
            with col2:
                cats = ["Gehalt", "Bonus", "Verkauf"] if t_type == "Einnahme" else ["Essen", "Miete", "Freizeit", "Transport", "Shopping"]
                t_cat = st.selectbox("Kategorie", cats)
                t_note = st.text_input("Notiz")
            if st.form_submit_button("Speichern", use_container_width=True):
                new_row = pd.DataFrame([{"user": st.session_state['user_name'], "datum": str(t_date), "typ": t_type, "kategorie": t_cat, "betrag": t_amount if t_type == "Einnahme" else -t_amount, "notiz": t_note}])
                df_old = conn.read(worksheet="transactions", ttl="0")
                conn.update(worksheet="transactions", data=pd.concat([df_old, new_row], ignore_index=True))
                st.success(f"✅ {t_type} über {t_amount:.2f} € gespeichert!")
                st.balloons()

    elif menu == "⚙️ Einstellungen":
        st.title("Einstellungen ⚙️")
        st.subheader("Passwort ändern")
        with st.form("pw_form"):
            pw_alt = st.text_input("Aktuelles Passwort", type="password")
            pw_neu = st.text_input("Neues Passwort", type="password")
            pw_neu2 = st.text_input("Neues Passwort wiederholen", type="password")
            if st.form_submit_button("Passwort ändern", use_container_width=True):
                df_u = conn.read(worksheet="users", ttl="0")
                idx = df_u[df_u['username'] == st.session_state['user_name']].index
                if idx.empty:
                    st.error("❌ Benutzer nicht gefunden.")
                elif make_hashes(pw_alt) != str(df_u.loc[idx[0], 'password']):
                    st.error("❌ Aktuelles Passwort ist falsch.")
                elif pw_neu == pw_alt:
                    st.error("❌ Das neue Passwort darf nicht dem alten entsprechen.")
                else:
                    is_strong, msg = check_password_strength(pw_neu)
                    if not is_strong:
                        st.error(f"❌ {msg}")
                    elif pw_neu != pw_neu2:
                        st.error("❌ Die neuen Passwörter stimmen nicht überein.")
                    else:
                        df_u.loc[idx[0], 'password'] = make_hashes(pw_neu)
                        conn.update(worksheet="users", data=df_u)
                        st.success("✅ Passwort erfolgreich geändert!")

else:
    st.markdown("<div style='height: 8vh;'></div>", unsafe_allow_html=True)
    st.markdown("<h1 class='main-title'>Balancely</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>Verwalte deine Finanzen mit Klarheit</p>", unsafe_allow_html=True)

    _, center_col, _ = st.columns([1, 1.2, 1])
    with center_col:

        # ===== LOGIN =====
        if st.form_submit_button("Anmelden"):
    df_u = conn.read(worksheet="users", ttl="0")
    user_row = df_u[df_u['username'] == u_in]
    if not user_row.empty and make_hashes(p_in) == str(user_row.iloc[0]['password']):
        verified = str(user_row.iloc[0].get('verified', 'True')).strip().lower()
        if verified not in ('true', '1', 'yes'):
            st.error("❌ Bitte verifiziere zuerst deine E-Mail-Adresse.")
        else:
            st.session_state['logged_in'] = True
            st.session_state['user_name'] = u_in
            st.rerun()
    else:
        st.error("Login ungültig.")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Konto erstellen", use_container_width=True):
                    st.session_state['auth_mode'] = 'signup'
                    st.rerun()
            with col2:
                if st.button("Passwort vergessen?", use_container_width=True, type="secondary"):
                    st.session_state['auth_mode'] = 'forgot'
                    st.rerun()

        # ===== REGISTRIERUNG =====
        elif st.session_state['auth_mode'] == 'signup':
            with st.form("s_f"):
                st.markdown("<h3 style='text-align:center; color:white;'>Registrierung</h3>", unsafe_allow_html=True)
                s_name = st.text_input("Name", placeholder="Max Mustermann")
                s_user = st.text_input("Username", placeholder="max123")
                s_email = st.text_input("E-Mail", placeholder="max@beispiel.de")
                s_pass = st.text_input("Passwort", type="password")
                c_pass = st.text_input("Passwort wiederholen", type="password")
                if st.form_submit_button("Konto erstellen"):
                    if not s_name or not s_user or not s_email or not s_pass:
                        st.error("❌ Bitte fülle alle Felder aus!")
                    elif len(s_name.strip().split()) < 2:
                        st.error("❌ Bitte gib deinen vollständigen Vor- und Nachnamen an.")
                    elif not is_valid_email(s_email):
                        st.error("❌ Bitte gib eine gültige E-Mail-Adresse ein.")
                    else:
                        is_strong, msg = check_password_strength(s_pass)
                        if not is_strong:
                            st.error(f"❌ {msg}")
                        elif s_pass != c_pass:
                            st.error("❌ Die Passwörter stimmen nicht überein.")
                        else:
                            df_u = conn.read(worksheet="users", ttl="0")
                            if s_user in df_u['username'].values:
                                st.error("⚠️ Dieser Username ist bereits vergeben.")
                            elif s_email.strip().lower() in df_u['email'].values:
                                st.error("⚠️ Diese E-Mail ist bereits registriert.")
                            else:
                                code = generate_code()
                                expiry = datetime.datetime.now() + datetime.timedelta(minutes=10)
                                html = email_html("Willkommen bei Balancely! Dein Verifizierungscode lautet:", code)
                                if send_email(s_email.strip().lower(), "Balancely – E-Mail verifizieren", html):
                                    st.session_state['pending_user'] = {
                                        "name": make_hashes(s_name.strip()),
                                        "username": s_user,
                                        "email": s_email.strip().lower(),
                                        "password": make_hashes(s_pass)
                                    }
                                    st.session_state['verify_code'] = code
                                    st.session_state['verify_expiry'] = expiry
                                    st.session_state['auth_mode'] = 'verify_email'
                                    st.rerun()
                                else:
                                    st.error("❌ E-Mail konnte nicht gesendet werden.")
            if st.button("Zurück zum Login", use_container_width=True):
                st.session_state['auth_mode'] = 'login'
                st.rerun()

        # ===== EMAIL VERIFIZIEREN =====
        elif st.session_state['auth_mode'] == 'verify_email':
            with st.form("verify_form"):
                st.markdown("<h3 style='text-align:center; color:white;'>E-Mail verifizieren</h3>", unsafe_allow_html=True)
                st.markdown(f"<p style='text-align:center; color:#94a3b8;'>Wir haben einen 6-stelligen Code an <b style='color:#38bdf8;'>{st.session_state['pending_user'].get('email','')}</b> gesendet.</p>", unsafe_allow_html=True)
                code_input = st.text_input("Code eingeben", placeholder="123456", max_chars=6)
                if st.form_submit_button("Bestätigen", use_container_width=True):
                    if datetime.datetime.now() > st.session_state['verify_expiry']:
                        st.error("⏰ Der Code ist abgelaufen. Bitte registriere dich erneut.")
                        st.session_state['auth_mode'] = 'signup'
                        st.rerun()
                    elif code_input.strip() != st.session_state['verify_code']:
                        st.error("❌ Falscher Code. Bitte versuche es erneut.")
                    else:
                        df_u = conn.read(worksheet="users", ttl="0")
                        new_u = pd.DataFrame([{
                            **st.session_state['pending_user'],
                            "verified": "True",
                            "token": "",
                            "token_expiry": ""
                        }])
                        conn.update(worksheet="users", data=pd.concat([df_u, new_u], ignore_index=True))
                        st.session_state['pending_user'] = {}
                        st.session_state['verify_code'] = ""
                        st.session_state['verify_expiry'] = None
                        st.session_state['auth_mode'] = 'login'
                        st.success("✅ E-Mail verifiziert! Du kannst dich jetzt einloggen.")
                        st.rerun()
            if st.button("Zurück", use_container_width=True):
                st.session_state['auth_mode'] = 'signup'
                st.rerun()

        # ===== PASSWORT VERGESSEN =====
        elif st.session_state['auth_mode'] == 'forgot':
            with st.form("forgot_form"):
                st.markdown("<h3 style='text-align:center; color:white;'>Passwort vergessen</h3>", unsafe_allow_html=True)
                st.markdown("<p style='text-align:center; color:#94a3b8;'>Gib deine E-Mail-Adresse ein.</p>", unsafe_allow_html=True)
                forgot_email = st.text_input("E-Mail", placeholder="deine@email.de")
                if st.form_submit_button("Code senden", use_container_width=True):
                    if not is_valid_email(forgot_email):
                        st.error("❌ Bitte gib eine gültige E-Mail-Adresse ein.")
                    else:
                        df_u = conn.read(worksheet="users", ttl="0")
                        idx = df_u[df_u['email'] == forgot_email.strip().lower()].index
                        if idx.empty:
                            st.success("✅ Falls diese E-Mail registriert ist, wurde ein Code gesendet.")
                        else:
                            code = generate_code()
                            expiry = datetime.datetime.now() + datetime.timedelta(minutes=10)
                            html = email_html("Dein Code zum Zurücksetzen des Passworts lautet:", code)
                            if send_email(forgot_email.strip().lower(), "Balancely – Passwort zurücksetzen", html):
                                st.session_state['reset_email'] = forgot_email.strip().lower()
                                st.session_state['reset_code'] = code
                                st.session_state['reset_expiry'] = expiry
                                st.session_state['auth_mode'] = 'reset_password'
                                st.rerun()
            if st.button("Zurück zum Login", use_container_width=True):
                st.session_state['auth_mode'] = 'login'
                st.rerun()

        # ===== PASSWORT ZURÜCKSETZEN =====
        elif st.session_state['auth_mode'] == 'reset_password':
            with st.form("reset_form"):
                st.markdown("<h3 style='text-align:center; color:white;'>Passwort zurücksetzen</h3>", unsafe_allow_html=True)
                st.markdown(f"<p style='text-align:center; color:#94a3b8;'>Code wurde an <b style='color:#38bdf8;'>{st.session_state['reset_email']}</b> gesendet.</p>", unsafe_allow_html=True)
                code_input = st.text_input("6-stelliger Code", placeholder="123456", max_chars=6)
                pw_neu = st.text_input("Neues Passwort", type="password")
                pw_neu2 = st.text_input("Passwort wiederholen", type="password")
                if st.form_submit_button("Passwort speichern", use_container_width=True):
                    if datetime.datetime.now() > st.session_state['reset_expiry']:
                        st.error("⏰ Der Code ist abgelaufen. Bitte fordere einen neuen an.")
                        st.session_state['auth_mode'] = 'forgot'
                        st.rerun()
                    elif code_input.strip() != st.session_state['reset_code']:
                        st.error("❌ Falscher Code.")
                    else:
                        is_strong, msg = check_password_strength(pw_neu)
                        if not is_strong:
                            st.error(f"❌ {msg}")
                        elif pw_neu != pw_neu2:
                            st.error("❌ Die Passwörter stimmen nicht überein.")
                        else:
                            df_u = conn.read(worksheet="users", ttl="0")
                            idx = df_u[df_u['email'] == st.session_state['reset_email']].index
                            if not idx.empty:
                                df_u.loc[idx[0], 'password'] = make_hashes(pw_neu)
                                conn.update(worksheet="users", data=df_u)
                                st.session_state['reset_email'] = ""
                                st.session_state['reset_code'] = ""
                                st.session_state['reset_expiry'] = None
                                st.session_state['auth_mode'] = 'login'
                                st.success("✅ Passwort geändert! Du kannst dich jetzt einloggen.")
                                st.rerun()
            if st.button("Zurück zum Login", use_container_width=True):
                st.session_state['auth_mode'] = 'login'
                st.rerun()

