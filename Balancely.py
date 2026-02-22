# ============================================================
#  Balancely — Persönliche Finanzverwaltung  v2
# ============================================================

import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import hashlib
import datetime
import re
import smtplib
import random
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ── Seitenkonfiguration ──────────────────────────────────────
st.set_page_config(page_title="Balancely", page_icon="⚖️", layout="wide")


# ============================================================
#  Hilfsfunktionen
# ============================================================

def make_hashes(text: str) -> str:
    return hashlib.sha256(str.encode(text)).hexdigest()


def check_password_strength(password: str):
    if len(password) < 6:
        return False, "Das Passwort muss mindestens 6 Zeichen lang sein."
    if not re.search(r"[a-z]", password):
        return False, "Das Passwort muss mindestens einen Kleinbuchstaben enthalten."
    if not re.search(r"[A-Z]", password):
        return False, "Das Passwort muss mindestens einen Großbuchstaben enthalten."
    return True, ""


def is_valid_email(email: str) -> bool:
    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))


def generate_code() -> str:
    return str(random.randint(100000, 999999))


def is_deleted(value) -> bool:
    try:
        return float(value) >= 1.0
    except (ValueError, TypeError):
        return str(value).strip().lower() in ('true', '1', 'yes')


def is_verified(value) -> bool:
    try:
        return float(value) >= 1.0
    except (ValueError, TypeError):
        return str(value).strip().lower() in ('true', '1', 'yes')


def format_timestamp(ts_str, datum_str) -> str:
    now   = datetime.datetime.now()
    today = now.date()
    try:
        ts = datetime.datetime.strptime(str(ts_str).strip(), "%Y-%m-%d %H:%M")
        uhr = ts.strftime("%H:%M")
        if ts.date() == today:
            return f"heute {uhr}"
        elif ts.date() == today - datetime.timedelta(days=1):
            return f"gestern {uhr}"
        else:
            return ts.strftime("%d.%m.%Y %H:%M")
    except Exception:
        try:
            d = datetime.date.fromisoformat(str(datum_str))
            if d == today:
                return "heute"
            elif d == today - datetime.timedelta(days=1):
                return "gestern"
            else:
                return d.strftime("%d.%m.%Y")
        except Exception:
            return str(datum_str)


def find_row_mask(df: pd.DataFrame, row: pd.Series) -> pd.Series:
    return (
        (df['user'] == row['user']) &
        (df['datum'].astype(str) == str(row['datum'])) &
        (pd.to_numeric(df['betrag'], errors='coerce') ==
         pd.to_numeric(row['betrag'], errors='coerce')) &
        (df['kategorie'] == row['kategorie']) &
        (~df['deleted'].astype(str).str.strip().str.lower().isin(['true', '1', '1.0']))
    )


def send_email(to_email: str, subject: str, html_content: str) -> bool:
    try:
        sender   = st.secrets["email"]["sender"]
        password = st.secrets["email"]["password"]
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"Balancely ⚖️ <{sender}>"
        msg["To"]      = to_email
        msg.attach(MIMEText(html_content, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, to_email, msg.as_string())
        return True
    except Exception as e:
        st.error(f"Email-Fehler: {e}")
        return False


def email_html(text: str, code: str) -> str:
    return f"""
    <html><body style="font-family:sans-serif;background:#020617;color:#f1f5f9;padding:40px;">
        <div style="max-width:480px;margin:auto;background:#0f172a;border-radius:16px;
                    padding:40px;border:1px solid #1e293b;">
            <h2 style="color:#38bdf8;">Balancely ⚖️</h2>
            <p>{text}</p>
            <div style="margin:24px 0;padding:20px;background:#1e293b;border-radius:12px;
                        text-align:center;font-size:36px;font-weight:800;
                        letter-spacing:8px;color:#38bdf8;">
                {code}
            </div>
            <p style="color:#94a3b8;font-size:13px;">
                Dieser Code ist 10 Minuten gültig.<br>
                Falls du diese Anfrage nicht gestellt hast, ignoriere diese Email.
            </p>
        </div>
    </body></html>
    """


# ============================================================
#  Globales CSS — Premium Redesign
# ============================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,300&family=DM+Mono:wght@400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    font-family: 'DM Sans', sans-serif !important;
}

[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(ellipse 80% 50% at 20% -10%, rgba(56,189,248,0.06) 0%, transparent 60%),
        radial-gradient(ellipse 60% 40% at 80% 110%, rgba(99,102,241,0.05) 0%, transparent 55%),
        linear-gradient(160deg, #070d1a 0%, #080e1c 40%, #050b16 100%) !important;
    min-height: 100vh;
}

/* ── Typography ─────────────────────────────────────────── */
h1, h2, h3, h4 { font-family: 'DM Sans', sans-serif !important; letter-spacing: -0.5px; }

/* ── Remove default padding ─────────────────────────────── */
[data-testid="stMain"] .block-container {
    padding-top: 2rem !important;
    max-width: 1200px !important;
}

/* ── Branding ───────────────────────────────────────────── */
.main-title {
    text-align: center;
    color: #f8fafc;
    font-size: clamp(48px, 8vw, 72px);
    font-weight: 700;
    letter-spacing: -3px;
    margin-bottom: 0;
    line-height: 1;
    background: linear-gradient(135deg, #e2e8f0 0%, #94a3b8 50%, #64748b 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.sub-title {
    text-align: center;
    color: #475569;
    font-size: 15px;
    font-weight: 400;
    letter-spacing: 0.3px;
    margin-bottom: 48px;
    margin-top: 8px;
}

/* ── Forms ──────────────────────────────────────────────── */
[data-testid="stForm"] {
    background: linear-gradient(145deg, rgba(15,23,42,0.9) 0%, rgba(10,16,32,0.95) 100%) !important;
    backdrop-filter: blur(20px) !important;
    padding: 40px !important;
    border-radius: 20px !important;
    border: 1px solid rgba(148,163,184,0.08) !important;
    box-shadow: 0 25px 50px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.04) !important;
}

/* ── Inputs ─────────────────────────────────────────────── */
div[data-testid="stTextInputRootElement"] { background-color: transparent !important; }
div[data-baseweb="input"],
div[data-baseweb="base-input"] {
    background-color: rgba(15,23,42,0.6) !important;
    border: 1px solid rgba(148,163,184,0.1) !important;
    border-radius: 10px !important;
    transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
    padding-right: 0 !important;
    gap: 0 !important;
    box-shadow: none !important;
}
div[data-baseweb="input"]:focus-within,
div[data-baseweb="base-input"]:focus-within {
    background-color: rgba(15,23,42,0.8) !important;
    border-color: rgba(56,189,248,0.5) !important;
    box-shadow: 0 0 0 3px rgba(56,189,248,0.08) !important;
}
input {
    padding-left: 15px !important;
    color: #e2e8f0 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 14px !important;
}
input::placeholder { color: #334155 !important; }

/* ── Date & Select ──────────────────────────────────────── */
div[data-testid="stDateInput"] > div {
    background-color: rgba(15,23,42,0.6) !important;
    border: 1px solid rgba(148,163,184,0.1) !important;
    border-radius: 10px !important;
    box-shadow: none !important;
    min-height: 42px !important;
    overflow: hidden !important;
}
div[data-baseweb="select"] > div:first-child {
    background-color: rgba(15,23,42,0.6) !important;
    border: 1px solid rgba(148,163,184,0.1) !important;
    border-radius: 10px !important;
    box-shadow: none !important;
}
div[data-baseweb="select"] > div:first-child:focus-within {
    border-color: rgba(56,189,248,0.5) !important;
    box-shadow: 0 0 0 3px rgba(56,189,248,0.08) !important;
}

/* ── Buttons ─────────────────────────────────────────────── */
button[kind="primaryFormSubmit"],
button[kind="secondaryFormSubmit"] {
    height: 48px !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 14px !important;
    letter-spacing: 0.2px !important;
    transition: all 0.2s ease !important;
}
button[kind="primaryFormSubmit"] {
    background: linear-gradient(135deg, #0ea5e9, #2563eb) !important;
    border: none !important;
    box-shadow: 0 4px 15px rgba(14,165,233,0.25) !important;
}
button[kind="primaryFormSubmit"]:hover {
    box-shadow: 0 6px 20px rgba(14,165,233,0.35) !important;
    transform: translateY(-1px) !important;
}

/* ── Sidebar ─────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #070d1a 0%, #060b18 100%) !important;
    border-right: 1px solid rgba(148,163,184,0.07) !important;
}
[data-testid="stSidebar"] .stMarkdown p {
    font-family: 'DM Sans', sans-serif !important;
    color: #475569 !important;
    font-size: 13px !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] > div > label {
    border: 1px solid transparent !important;
    border-radius: 10px !important;
    padding: 9px 14px !important;
    margin-bottom: 3px !important;
    color: #475569 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 14px !important;
    font-weight: 400 !important;
    transition: all 0.15s ease !important;
    letter-spacing: 0.1px !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] > div > label:hover {
    border-color: rgba(56,189,248,0.15) !important;
    color: #94a3b8 !important;
    background: rgba(56,189,248,0.04) !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] > div > label:has(input:checked) {
    border-color: rgba(56,189,248,0.25) !important;
    background: rgba(56,189,248,0.08) !important;
    color: #e2e8f0 !important;
    font-weight: 500 !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] > div > label > div:first-child {
    display: none !important;
}

/* ── Number input step buttons ──────────────────────────── */
button[data-testid="stNumberInputStepDown"],
button[data-testid="stNumberInputStepUp"] { display: none !important; }
div[data-baseweb="input"] > div:not(:has(input)):not(:has(button)):not(:has(svg)) {
    display: none !important;
}

/* ── Hide input instructions ────────────────────────────── */
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

/* ── Cursor ─────────────────────────────────────────────── */
button, [data-testid="stPopover"] button,
div[data-baseweb="select"],
div[data-baseweb="select"] *,
div[data-testid="stDateInput"],
[data-testid="stSelectbox"] * { cursor: pointer !important; }

/* ── Dialogs ─────────────────────────────────────────────── */
div[data-testid="stDialog"] > div,
div[role="dialog"] {
    position: fixed !important;
    top: 50% !important;
    left: 50% !important;
    transform: translate(-50%, -50%) !important;
    margin: 0 !important;
    max-height: 90vh !important;
    overflow-y: auto !important;
    background: linear-gradient(145deg, #0d1729, #0a1020) !important;
    border: 1px solid rgba(148,163,184,0.1) !important;
    border-radius: 18px !important;
    box-shadow: 0 40px 80px rgba(0,0,0,0.6) !important;
}
div[data-testid="stDialog"] {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

/* ── Divider ─────────────────────────────────────────────── */
hr {
    border-color: rgba(148,163,184,0.08) !important;
    margin: 24px 0 !important;
}

/* ── Subheader ───────────────────────────────────────────── */
[data-testid="stMarkdownContainer"] h3 {
    font-size: 15px !important;
    font-weight: 600 !important;
    color: #64748b !important;
    letter-spacing: 0.5px !important;
    text-transform: uppercase !important;
}

/* ── Success / Error messages ───────────────────────────── */
[data-testid="stAlert"] {
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 14px !important;
}

/* ── Popover ─────────────────────────────────────────────── */
[data-testid="stPopover"] > div {
    background: #0d1729 !important;
    border: 1px solid rgba(148,163,184,0.1) !important;
    border-radius: 12px !important;
    box-shadow: 0 20px 40px rgba(0,0,0,0.5) !important;
}

/* ── Expander ─────────────────────────────────────────────── */
[data-testid="stExpander"] {
    border: 1px solid rgba(148,163,184,0.08) !important;
    border-radius: 12px !important;
    background: rgba(10,16,32,0.5) !important;
}
</style>
""", unsafe_allow_html=True)


# ============================================================
#  Session State initialisieren
# ============================================================

DEFAULT_CATS = {
    "Einnahme": ["💼 Gehalt", "🎁 Bonus", "🛒 Verkauf", "📈 Investitionen", "🏠 Miete (Einnahme)"],
    "Ausgabe":  ["🍔 Essen", "🏠 Miete", "🎮 Freizeit", "🚗 Transport", "🛍️ Shopping",
                 "💊 Gesundheit", "📚 Bildung", "⚡ Strom & Gas"],
}

defaults = {
    'logged_in':       False,
    'user_name':       "",
    'auth_mode':       'login',
    't_type':          'Ausgabe',
    'pending_user':    {},
    'verify_code':     "",
    'verify_expiry':   None,
    'reset_email':     "",
    'reset_code':      "",
    'reset_expiry':    None,
    'edit_idx':        None,
    'show_new_cat':    False,
    'new_cat_typ':     'Ausgabe',
    '_last_menu':      "",
    'edit_cat_data':      None,
    'delete_cat_data':    None,
    'dash_month_offset':  0,
    'dash_selected_aus':  None,
    'dash_selected_ein':  None,
    'dash_selected_cat':  None,
    'dash_selected_typ':  None,
    'dash_selected_color': None,
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

conn = st.connection("gsheets", type=GSheetsConnection)


def load_custom_cats(user: str, typ: str) -> list:
    try:
        df = conn.read(worksheet="categories", ttl="0")
        if df.empty or 'user' not in df.columns:
            return []
        rows = df[(df['user'] == user) & (df['typ'] == typ)]
        return rows['kategorie'].tolist()
    except Exception:
        return []


def save_custom_cat(user: str, typ: str, kategorie: str):
    try:
        df = conn.read(worksheet="categories", ttl="0")
    except Exception:
        df = pd.DataFrame(columns=['user', 'typ', 'kategorie'])
    new_row = pd.DataFrame([{'user': user, 'typ': typ, 'kategorie': kategorie}])
    conn.update(worksheet="categories", data=pd.concat([df, new_row], ignore_index=True))


def delete_custom_cat(user: str, typ: str, kategorie: str):
    try:
        df = conn.read(worksheet="categories", ttl="0")
        df = df[~((df['user'] == user) & (df['typ'] == typ) & (df['kategorie'] == kategorie))]
        conn.update(worksheet="categories", data=df)
    except Exception:
        pass


def update_custom_cat(user: str, typ: str, old_label: str, new_label: str):
    try:
        df = conn.read(worksheet="categories", ttl="0")
        mask = (df['user'] == user) & (df['typ'] == typ) & (df['kategorie'] == old_label)
        df.loc[mask, 'kategorie'] = new_label
        conn.update(worksheet="categories", data=df)
    except Exception:
        pass


@st.dialog("➕ Neue Kategorie")
def new_category_dialog():
    typ = st.session_state.get('new_cat_typ', 'Ausgabe')
    st.markdown(
        f"<p style='color:#64748b;font-size:13px;margin-bottom:20px;font-family:DM Sans,sans-serif;'>"
        f"Für Typ: <span style='color:#38bdf8;font-weight:500;'>{typ}</span></p>",
        unsafe_allow_html=True
    )
    nc1, nc2 = st.columns([1, 3])
    with nc1:
        new_emoji = st.text_input("Emoji", placeholder="🎵", max_chars=4,
                                  help="Windows: **Win + .** | Mac: **Ctrl+Cmd+Space**")
    with nc2:
        new_name = st.text_input("Name", placeholder="z.B. Musik")
    nc_typ = st.selectbox("Typ", ["Ausgabe", "Einnahme"],
                          index=0 if typ == "Ausgabe" else 1)
    col_save, col_cancel = st.columns(2)
    with col_save:
        if st.button("Speichern", use_container_width=True, type="primary"):
            if not new_name.strip():
                st.error("Bitte einen Namen eingeben.")
            else:
                label    = f"{new_emoji.strip()} {new_name.strip()}" \
                           if new_emoji.strip() else new_name.strip()
                existing = load_custom_cats(st.session_state['user_name'], nc_typ) \
                           + DEFAULT_CATS[nc_typ]
                if label in existing:
                    st.error("Diese Kategorie existiert bereits.")
                else:
                    save_custom_cat(st.session_state['user_name'], nc_typ, label)
                    st.session_state['show_new_cat'] = False
                    st.rerun()
    with col_cancel:
        if st.button("Abbrechen", use_container_width=True):
            st.session_state['show_new_cat'] = False
            st.rerun()


@st.dialog("✏️ Kategorie bearbeiten")
def edit_category_dialog():
    data = st.session_state.get('edit_cat_data')
    if not data:
        st.rerun()
        return
    old_label = data['old_label']
    typ       = data['typ']
    user      = data['user']
    parts = old_label.split(' ', 1)
    if len(parts) == 2 and len(parts[0]) <= 4:
        init_emoji, init_name = parts[0], parts[1]
    else:
        init_emoji, init_name = '', old_label
    st.markdown(
        f"<p style='color:#64748b;font-size:13px;margin-bottom:16px;font-family:DM Sans,sans-serif;'>"
        f"Aktuell: <span style='color:#38bdf8;'>{old_label}</span></p>",
        unsafe_allow_html=True
    )
    nc1, nc2 = st.columns([1, 3])
    with nc1:
        new_emoji = st.text_input("Emoji", value=init_emoji, max_chars=4, placeholder="🎵",
                                  help="Windows: **Win + .** | Mac: **Ctrl+Cmd+Space**")
    with nc2:
        new_name = st.text_input("Name", value=init_name, placeholder="z.B. Musik")
    new_typ = st.selectbox("Typ", ["Ausgabe", "Einnahme"],
                           index=0 if typ == "Ausgabe" else 1)
    col_save, col_cancel = st.columns(2)
    with col_save:
        if st.button("Speichern", use_container_width=True, type="primary"):
            if not new_name.strip():
                st.error("Bitte einen Namen eingeben.")
            else:
                new_label = f"{new_emoji.strip()} {new_name.strip()}" \
                            if new_emoji.strip() else new_name.strip()
                existing = load_custom_cats(user, new_typ) + DEFAULT_CATS[new_typ]
                if new_label != old_label and new_label in existing:
                    st.error("Diese Kategorie existiert bereits.")
                else:
                    if new_typ != typ:
                        delete_custom_cat(user, typ, old_label)
                        save_custom_cat(user, new_typ, new_label)
                    else:
                        update_custom_cat(user, typ, old_label, new_label)
                    st.session_state['edit_cat_data'] = None
                    st.rerun()
    with col_cancel:
        if st.button("Abbrechen", use_container_width=True):
            st.session_state['edit_cat_data'] = None
            st.rerun()


@st.dialog("Kategorie löschen")
def confirm_delete_cat():
    data = st.session_state.get('delete_cat_data')
    if not data:
        st.rerun()
        return
    st.markdown(
        f"<p style='color:#e2e8f0;font-size:15px;margin-bottom:8px;font-family:DM Sans,sans-serif;'>"
        f"Kategorie wirklich löschen?</p>"
        f"<p style='color:#64748b;font-size:14px;'>{data['label']}</p>",
        unsafe_allow_html=True
    )
    col_ja, col_nein = st.columns(2)
    with col_ja:
        if st.button("Löschen", use_container_width=True, type="primary"):
            delete_custom_cat(data['user'], data['typ'], data['label'])
            st.session_state['delete_cat_data'] = None
            st.rerun()
    with col_nein:
        if st.button("Abbrechen", use_container_width=True):
            st.session_state['delete_cat_data'] = None
            st.rerun()


@st.dialog("Eintrag löschen")
def confirm_delete(row_data):
    st.markdown(
        f"<p style='color:#e2e8f0;font-size:15px;margin-bottom:6px;font-family:DM Sans,sans-serif;'>"
        f"Eintrag wirklich löschen?</p>"
        f"<p style='color:#475569;font-size:13px;'>"
        f"{row_data['datum']} · {row_data['betrag_anzeige']} · {row_data['kategorie']}</p>",
        unsafe_allow_html=True
    )
    col_ja, col_nein = st.columns(2)
    with col_ja:
        if st.button("Löschen", use_container_width=True, type="primary"):
            df_all = conn.read(worksheet="transactions", ttl="0")
            if 'deleted' not in df_all.columns:
                df_all['deleted'] = ''
            mask = (
                (df_all['user'] == row_data['user']) &
                (df_all['datum'].astype(str) == str(row_data['datum'])) &
                (pd.to_numeric(df_all['betrag'], errors='coerce') ==
                 pd.to_numeric(row_data['betrag'], errors='coerce')) &
                (df_all['kategorie'] == row_data['kategorie']) &
                (~df_all['deleted'].astype(str).str.strip().str.lower()
                 .isin(['true', '1', '1.0']))
            )
            match_idx = df_all[mask].index
            if len(match_idx) > 0:
                df_all.loc[match_idx[0], 'deleted'] = 'True'
                conn.update(worksheet="transactions", data=df_all)
                st.session_state['edit_idx'] = None
                st.rerun()
            else:
                st.error("Eintrag nicht gefunden.")
    with col_nein:
        if st.button("Abbrechen", use_container_width=True):
            st.rerun()


# ============================================================
#  APP — Eingeloggt
# ============================================================

if st.session_state['logged_in']:

    # ── Sidebar ─────────────────────────────────────────────
    with st.sidebar:
        st.markdown(
            "<div style='padding:8px 0 24px 0;'>"
            "<span style='font-family:DM Sans,sans-serif;font-size:20px;font-weight:600;"
            "color:#e2e8f0;letter-spacing:-0.5px;'>Balancely</span>"
            "<span style='color:#38bdf8;font-size:20px;'> ⚖️</span>"
            "</div>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<div style='font-family:DM Sans,sans-serif;font-size:12px;color:#334155;"
            f"margin-bottom:20px;letter-spacing:0.3px;'>"
            f"<span style='color:#475569;'>Eingeloggt als</span><br>"
            f"<span style='color:#64748b;font-weight:500;'>{st.session_state['user_name']}</span>"
            f"</div>",
            unsafe_allow_html=True
        )
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        menu = st.radio(
            "Navigation",
            ["📈 Dashboard", "💸 Transaktionen", "📂 Analysen", "⚙️ Einstellungen"],
            label_visibility="collapsed"
        )
        st.markdown("<div style='height:28vh;'></div>", unsafe_allow_html=True)
        if st.button("Logout ➜", use_container_width=True, type="secondary"):
            st.session_state['logged_in'] = False
            st.rerun()

    # Dialog-State Management
    if st.session_state.pop('_dialog_just_opened', False):
        pass
    else:
        st.session_state['show_new_cat']    = False
        st.session_state['edit_cat_data']   = None
        st.session_state['delete_cat_data'] = None
    st.session_state['_last_menu'] = menu

    # ── Dashboard ────────────────────────────────────────────
    if menu == "📈 Dashboard":
        import plotly.graph_objects as go

        now = datetime.datetime.now()

        # Page header
        st.markdown(
            f"<div style='margin-bottom:36px;margin-top:16px;'>"
            f"<h1 style='font-family:DM Sans,sans-serif;font-size:40px;font-weight:700;"
            f"color:#e2e8f0;margin:0 0 6px 0;letter-spacing:-1px;'>"
            f"Deine Übersicht, {st.session_state['user_name']}! ⚖️</h1>"
            f"<p style='font-family:DM Sans,sans-serif;color:#475569;font-size:15px;margin:0;'>"
            f"Monatliche Finanzübersicht</p>"
            f"</div>",
            unsafe_allow_html=True
        )

        # ── Monats-Selektor ──────────────────────────────────
        if 'dash_month_offset' not in st.session_state:
            st.session_state['dash_month_offset'] = 0
        offset = st.session_state['dash_month_offset']
        y, m   = now.year, now.month
        m_total = y * 12 + (m - 1) + offset
        t_year, t_month = divmod(m_total, 12)
        t_month += 1
        monat_label = datetime.date(t_year, t_month, 1).strftime("%B %Y")

        nav1, nav2, nav3 = st.columns([1, 5, 1])
        with nav1:
            if st.button("‹", use_container_width=True, key="dash_prev"):
                st.session_state['dash_month_offset'] -= 1
                st.session_state['dash_selected_cat']   = None
                st.session_state['dash_selected_typ']   = None
                st.session_state['dash_selected_color'] = None
                st.rerun()
        with nav2:
            st.markdown(
                f"<div style='text-align:center;font-family:DM Sans,sans-serif;"
                f"font-size:14px;font-weight:500;color:#64748b;padding:6px 0;'>"
                f"{monat_label}</div>",
                unsafe_allow_html=True
            )
        with nav3:
            if st.button("›", use_container_width=True, key="dash_next",
                         disabled=(offset >= 0)):
                st.session_state['dash_month_offset'] += 1
                st.session_state['dash_selected_cat']   = None
                st.session_state['dash_selected_typ']   = None
                st.session_state['dash_selected_color'] = None
                st.rerun()

        try:
            df_t = conn.read(worksheet="transactions", ttl="0")
            if "user" not in df_t.columns:
                st.info("Noch keine Daten vorhanden.")
            else:
                alle = df_t[df_t["user"] == st.session_state["user_name"]].copy()
                if "deleted" in alle.columns:
                    alle = alle[~alle["deleted"].astype(str).str.strip().str.lower()
                                .isin(["true", "1", "1.0"])]

                alle["datum_dt"] = pd.to_datetime(alle["datum"], errors="coerce")
                monat_df = alle[
                    (alle["datum_dt"].dt.year  == t_year) &
                    (alle["datum_dt"].dt.month == t_month)
                ].copy()

                if monat_df.empty:
                    st.markdown(
                        f"<div style='text-align:center;padding:60px 20px;color:#334155;"
                        f"font-family:DM Sans,sans-serif;font-size:15px;'>"
                        f"Keine Buchungen im {monat_label}</div>",
                        unsafe_allow_html=True
                    )
                else:
                    monat_df["betrag_num"] = pd.to_numeric(monat_df["betrag"], errors="coerce")
                    ein = monat_df[monat_df["typ"] == "Einnahme"]["betrag_num"].sum()
                    aus = abs(monat_df[monat_df["typ"] == "Ausgabe"]["betrag_num"].sum())
                    bal = ein - aus
                    bal_color = "#4ade80" if bal >= 0 else "#f87171"
                    bal_sign  = "+" if bal >= 0 else ""

                    # ── KPI Cards ─────────────────────────────
                    st.markdown(
                        f"<div style='display:flex;gap:14px;margin:0 0 28px 0;'>"
                        # Kontostand
                        f"<div style='flex:1;background:linear-gradient(145deg,rgba(14,22,38,0.9),rgba(10,16,30,0.95));"
                        f"border:1px solid rgba(148,163,184,0.08);border-radius:16px;padding:20px 22px;"
                        f"box-shadow:0 4px 20px rgba(0,0,0,0.2);'>"
                        f"<div style='font-family:DM Mono,monospace;font-size:10px;color:#334155;"
                        f"letter-spacing:1.5px;text-transform:uppercase;margin-bottom:10px;'>Kontostand</div>"
                        f"<div style='font-family:DM Sans,sans-serif;color:{bal_color};font-size:24px;"
                        f"font-weight:600;letter-spacing:-0.5px;'>{bal_sign}{bal:,.2f} €</div>"
                        f"</div>"
                        # Einnahmen
                        f"<div style='flex:1;background:linear-gradient(145deg,rgba(14,22,38,0.9),rgba(10,16,30,0.95));"
                        f"border:1px solid rgba(148,163,184,0.08);border-radius:16px;padding:20px 22px;"
                        f"box-shadow:0 4px 20px rgba(0,0,0,0.2);'>"
                        f"<div style='font-family:DM Mono,monospace;font-size:10px;color:#334155;"
                        f"letter-spacing:1.5px;text-transform:uppercase;margin-bottom:10px;'>Einnahmen</div>"
                        f"<div style='font-family:DM Sans,sans-serif;color:#4ade80;font-size:24px;"
                        f"font-weight:600;letter-spacing:-0.5px;'>+{ein:,.2f} €</div>"
                        f"</div>"
                        # Ausgaben
                        f"<div style='flex:1;background:linear-gradient(145deg,rgba(14,22,38,0.9),rgba(10,16,30,0.95));"
                        f"border:1px solid rgba(148,163,184,0.08);border-radius:16px;padding:20px 22px;"
                        f"box-shadow:0 4px 20px rgba(0,0,0,0.2);'>"
                        f"<div style='font-family:DM Mono,monospace;font-size:10px;color:#334155;"
                        f"letter-spacing:1.5px;text-transform:uppercase;margin-bottom:10px;'>Ausgaben</div>"
                        f"<div style='font-family:DM Sans,sans-serif;color:#f87171;font-size:24px;"
                        f"font-weight:600;letter-spacing:-0.5px;'>-{aus:,.2f} €</div>"
                        f"</div>"
                        f"</div>",
                        unsafe_allow_html=True
                    )

                    # ── Kategorie-Daten aufbereiten ────────────
                    ausg_df = monat_df[monat_df["typ"] == "Ausgabe"].copy()
                    ausg_df["betrag_num"] = ausg_df["betrag_num"].abs()
                    ausg_grp = (ausg_df.groupby("kategorie")["betrag_num"]
                                .sum().reset_index()
                                .sort_values("betrag_num", ascending=False))

                    ein_df  = monat_df[monat_df["typ"] == "Einnahme"].copy()
                    ein_grp = (ein_df.groupby("kategorie")["betrag_num"]
                               .sum().reset_index()
                               .sort_values("betrag_num", ascending=False))

                    PALETTE_AUS = ["#ef4444","#f97316","#f59e0b","#dc2626",
                                   "#ea580c","#d97706","#b91c1c","#c2410c",
                                   "#92400e","#e11d48"]
                    PALETTE_EIN = ["#22c55e","#34d399","#86efac","#16a34a",
                                   "#6ee7b7","#4ade80","#bbf7d0","#10b981",
                                   "#a7f3d0","#059669"]

                    all_cats, all_vals, all_colors, all_types = [], [], [], []
                    for i, (_, row) in enumerate(ausg_grp.iterrows()):
                        all_cats.append(row["kategorie"])
                        all_vals.append(float(row["betrag_num"]))
                        all_colors.append(PALETTE_AUS[i % len(PALETTE_AUS)])
                        all_types.append("Ausgabe")
                    for i, (_, row) in enumerate(ein_grp.iterrows()):
                        all_cats.append(row["kategorie"])
                        all_vals.append(float(row["betrag_num"]))
                        all_colors.append(PALETTE_EIN[i % len(PALETTE_EIN)])
                        all_types.append("Einnahme")

                    total_sum = sum(all_vals) if sum(all_vals) > 0 else 1

                    # ── FIX: customdata als separate Listen für korrektes Plotly-Mapping ──
                    # customdata muss ein 2D-Array sein: [[typ, pct], [typ, pct], ...]
                    customdata_list = [
                        [typ, val / total_sum * 100]
                        for typ, val in zip(all_types, all_vals)
                    ]

                    fig = go.Figure(go.Pie(
                        labels=all_cats,
                        values=all_vals,
                        hole=0.62,
                        marker=dict(
                            colors=all_colors,
                            line=dict(color="rgba(5,10,20,0.8)", width=2),
                        ),
                        textinfo="none",
                        hoverinfo="none",   # Kein Hover-Tooltip
                        direction="clockwise",
                        sort=False,
                        rotation=90,
                    ))

                    fig.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        showlegend=False,
                        margin=dict(t=20, b=20, l=20, r=20),
                        height=380,
                        autosize=True,
                        hoverlabel=dict(
                            bgcolor="#0d1729",
                            bordercolor="rgba(56,189,248,0.4)",
                            font=dict(
                                color="#e2e8f0",
                                size=13,
                                family="DM Sans, sans-serif",
                            ),
                            namelength=-1,
                            align="left",
                        ),
                        annotations=[
                            dict(
                                text="<span style='font-size:11px'>KONTOSTAND</span>",
                                x=0.5, y=0.62, showarrow=False,
                                font=dict(size=10, color="#334155", family="DM Mono, monospace"),
                                xref="paper", yref="paper",
                            ),
                            dict(
                                text=f"<b>{bal_sign}{bal:,.2f} €</b>",
                                x=0.5, y=0.50, showarrow=False,
                                font=dict(size=22, color=bal_color, family="DM Sans, sans-serif"),
                                xref="paper", yref="paper",
                            ),
                            dict(
                                text=f"<span style='color:#22c55e'>+{ein:,.0f}</span>"
                                     f"<span style='color:#334155'>  /  </span>"
                                     f"<span style='color:#f87171'>-{aus:,.0f} €</span>",
                                x=0.5, y=0.38, showarrow=False,
                                font=dict(size=11, color="#475569", family="DM Sans, sans-serif"),
                                xref="paper", yref="paper",
                            ),
                        ],
                    )

                    # ── Layout: Chart + Legende ───────────────
                    chart_col, legend_col = st.columns([2, 2])

                    with chart_col:
                        # Kein on_select — Interaktion läuft über Legende-Buttons
                        st.plotly_chart(
                            fig, use_container_width=True,
                            key="donut_combined",
                        )

                    with legend_col:
                        # Aktive Auswahl aus session_state lesen
                        sel_cat   = st.session_state.get('dash_selected_cat')
                        sel_typ   = st.session_state.get('dash_selected_typ')
                        sel_color = st.session_state.get('dash_selected_color')

                        if sel_cat and sel_typ:
                            src_df  = ausg_df if sel_typ == "Ausgabe" else ein_df
                            detail  = src_df[src_df["kategorie"] == sel_cat]
                            total_d = detail["betrag_num"].sum()
                            sign    = "−" if sel_typ == "Ausgabe" else "+"
                            rows_html = ""
                            for _, tr in detail.sort_values("datum_dt", ascending=False).iterrows():
                                notiz_tr = str(tr.get("notiz", ""))
                                notiz_tr = "" if notiz_tr.lower() == "nan" else notiz_tr
                                rows_html += (
                                    f"<div style='display:flex;justify-content:space-between;"
                                    f"align-items:center;padding:10px 0;"
                                    f"border-bottom:1px solid rgba(255,255,255,0.05);'>"
                                    f"<div style='min-width:0;display:flex;align-items:center;gap:10px;'>"
                                    f"<span style='font-family:DM Mono,monospace;color:#64748b;"
                                    f"font-size:12px;flex-shrink:0;'>{tr['datum_dt'].strftime('%d.%m.')}</span>"
                                    + (f"<span style='color:#94a3b8;font-size:13px;"
                                       f"font-family:DM Sans,sans-serif;overflow:hidden;"
                                       f"text-overflow:ellipsis;white-space:nowrap;'>"
                                       f"{notiz_tr}</span>" if notiz_tr else "")
                                    + f"</div>"
                                    f"<span style='color:{sel_color};font-weight:600;"
                                    f"font-size:13px;font-family:DM Mono,monospace;"
                                    f"flex-shrink:0;margin-left:12px;'>"
                                    f"{sign}{tr['betrag_num']:,.2f} €</span>"
                                    f"</div>"
                                )
                            # Zurück-Button + Detail-Card
                            if st.button("← Alle Kategorien", key="dash_back_btn"):
                                st.session_state['dash_selected_cat']   = None
                                st.session_state['dash_selected_typ']   = None
                                st.session_state['dash_selected_color'] = None
                                st.rerun()
                            st.markdown(
                                f"<div style='background:linear-gradient(145deg,rgba(13,23,41,0.95),rgba(10,16,30,0.98));"
                                f"border:1px solid {sel_color}30;"
                                f"border-top:2px solid {sel_color};"
                                f"border-radius:14px;padding:18px 20px;margin-top:10px;"
                                f"box-shadow:0 8px 30px rgba(0,0,0,0.3);'>"
                                f"<div style='font-family:DM Mono,monospace;color:{sel_color};"
                                f"font-size:9px;font-weight:500;letter-spacing:2px;"
                                f"text-transform:uppercase;margin-bottom:6px;'>{sel_typ}</div>"
                                f"<div style='font-family:DM Sans,sans-serif;color:#e2e8f0;"
                                f"font-weight:600;font-size:16px;margin-bottom:4px;"
                                f"letter-spacing:-0.3px;'>{sel_cat}</div>"
                                f"<div style='font-family:DM Mono,monospace;color:{sel_color};"
                                f"font-size:22px;font-weight:500;margin-bottom:18px;"
                                f"letter-spacing:-0.5px;'>"
                                f"{sign}{total_d:,.2f} €</div>"
                                f"{rows_html}</div>",
                                unsafe_allow_html=True
                            )
                        else:
                            # Legende als klickbare Buttons
                            st.markdown(
                                f"<div style='font-family:DM Mono,monospace;color:#334155;"
                                f"font-size:9px;font-weight:500;letter-spacing:2px;"
                                f"text-transform:uppercase;margin-bottom:10px;padding:0 4px;'>"
                                f"Kategorien</div>",
                                unsafe_allow_html=True
                            )
                            for cat, val, color, typ in zip(
                                    all_cats, all_vals, all_colors, all_types):
                                pct  = val / total_sum * 100
                                sign = "−" if typ == "Ausgabe" else "+"
                                # Jede Zeile als klickbarer Button
                                btn_key = f"legend_btn_{cat}_{typ}"
                                # Render als custom HTML-Button via Streamlit button
                                col_legend, col_btn = st.columns([10, 1])
                                with col_legend:
                                    st.markdown(
                                        f"<div style='display:flex;align-items:center;"
                                        f"justify-content:space-between;"
                                        f"padding:7px 8px;border-radius:8px;"
                                        f"border:1px solid transparent;"
                                        f"cursor:pointer;'>"
                                        f"<div style='display:flex;align-items:center;gap:10px;min-width:0;'>"
                                        f"<div style='width:7px;height:7px;border-radius:50%;"
                                        f"background:{color};flex-shrink:0;'></div>"
                                        f"<span style='font-family:DM Sans,sans-serif;color:#94a3b8;"
                                        f"font-size:13px;overflow:hidden;text-overflow:ellipsis;"
                                        f"white-space:nowrap;'>{cat}</span>"
                                        f"</div>"
                                        f"<div style='display:flex;align-items:center;gap:8px;flex-shrink:0;margin-left:8px;'>"
                                        f"<span style='font-family:DM Mono,monospace;color:{color};"
                                        f"font-weight:500;font-size:12px;'>{sign}{val:,.2f} €</span>"
                                        f"<span style='font-family:DM Mono,monospace;color:#334155;"
                                        f"font-size:11px;min-width:28px;text-align:right;'>{pct:.0f}%</span>"
                                        f"</div></div>",
                                        unsafe_allow_html=True
                                    )
                                with col_btn:
                                    if st.button("›", key=btn_key):
                                        st.session_state['dash_selected_cat']   = cat
                                        st.session_state['dash_selected_typ']   = typ
                                        st.session_state['dash_selected_color'] = color
                                        st.rerun()

        except Exception as e:
            st.warning(f"Verbindung wird hergestellt... ({e})")

    # ── Transaktionen ────────────────────────────────────────
    elif menu == "💸 Transaktionen":
        user_name   = st.session_state['user_name']
        t_type      = st.session_state['t_type']
        std_cats    = DEFAULT_CATS[t_type]
        custom_cats = load_custom_cats(user_name, t_type)
        all_cats    = std_cats + custom_cats

        if st.session_state.get('show_new_cat') is True:
            new_category_dialog()
        if st.session_state.get('edit_cat_data') is not None:
            edit_category_dialog()
        if st.session_state.get('delete_cat_data') is not None:
            confirm_delete_cat()

        # Header
        st.markdown(
            "<div style='margin-bottom:28px;'>"
            "<h1 style='font-family:DM Sans,sans-serif;font-size:28px;font-weight:600;"
            "color:#e2e8f0;margin:0 0 4px 0;letter-spacing:-0.5px;'>Neue Buchung</h1>"
            "<p style='font-family:DM Sans,sans-serif;color:#334155;font-size:14px;margin:0;'>"
            "Erfasse Einnahmen und Ausgaben</p>"
            "</div>",
            unsafe_allow_html=True
        )

        # Typ-Toggle
        st.markdown(
            "<p style='font-family:DM Mono,monospace;color:#334155;font-size:10px;"
            "font-weight:500;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:10px;'>"
            "Typ</p>",
            unsafe_allow_html=True
        )
        ta, te, _ = st.columns([1, 1, 3])
        with ta:
            if st.button(
                "↗ Ausgabe" + (" ✓" if t_type == "Ausgabe" else ""),
                key="btn_ausgabe", use_container_width=True,
                type="primary" if t_type == "Ausgabe" else "secondary"
            ):
                st.session_state['t_type'] = "Ausgabe"
                st.rerun()
        with te:
            if st.button(
                "↙ Einnahme" + (" ✓" if t_type == "Einnahme" else ""),
                key="btn_einnahme", use_container_width=True,
                type="primary" if t_type == "Einnahme" else "secondary"
            ):
                st.session_state['t_type'] = "Einnahme"
                st.rerun()

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

        # Buchungsformular
        with st.form("t_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                t_amount = st.number_input("Betrag in €", min_value=0.01, step=0.01, format="%.2f")
                t_date   = st.date_input("Datum", datetime.date.today())
            with col2:
                st.markdown(
                    "<div style='font-family:DM Sans,sans-serif;font-size:14px;"
                    "color:#e2e8f0;margin-bottom:4px;'>Kategorie</div>",
                    unsafe_allow_html=True
                )
                t_cat  = st.selectbox("Kategorie", all_cats, label_visibility="collapsed")
                t_note = st.text_input("Notiz (optional)", placeholder="z.B. Supermarkt, Tankstelle...")

            saved = st.form_submit_button("Speichern", use_container_width=True)
            if saved:
                new_row = pd.DataFrame([{
                    "user":      user_name,
                    "datum":     str(t_date),
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "typ":       t_type,
                    "kategorie": t_cat,
                    "betrag":    t_amount if t_type == "Einnahme" else -t_amount,
                    "notiz":     t_note,
                }])
                df_old = conn.read(worksheet="transactions", ttl="0")
                conn.update(worksheet="transactions",
                            data=pd.concat([df_old, new_row], ignore_index=True))
                st.success(f"✅ {t_type} über {t_amount:.2f} € gespeichert!")
                st.balloons()

        # Neue Kategorie + Verwaltung
        cat_btn_col, manage_col = st.columns([1, 1])
        with cat_btn_col:
            if st.button("+ Neue Kategorie", use_container_width=True, type="secondary"):
                st.session_state['show_new_cat']      = True
                st.session_state['new_cat_typ']       = t_type
                st.session_state['_dialog_just_opened'] = True
                st.rerun()
        if custom_cats:
            with manage_col:
                with st.expander(f"Eigene {t_type}-Kategorien"):
                    for cat in custom_cats:
                        cc1, cc2 = st.columns([5, 1])
                        cc1.markdown(
                            f"<span style='font-family:DM Sans,sans-serif;color:#94a3b8;"
                            f"font-size:14px;'>{cat}</span>",
                            unsafe_allow_html=True
                        )
                        with cc2:
                            with st.popover("⋯", use_container_width=True):
                                if st.button("✏️ Bearbeiten", key=f"editcat_btn_{cat}",
                                             use_container_width=True):
                                    st.session_state['edit_cat_data'] = {
                                        'user':      user_name,
                                        'typ':       t_type,
                                        'old_label': cat,
                                    }
                                    st.session_state['_dialog_just_opened'] = True
                                    st.rerun()
                                if st.button("🗑️ Löschen", key=f"delcat_btn_{cat}",
                                             use_container_width=True):
                                    st.session_state['delete_cat_data'] = {
                                        'user':  user_name,
                                        'typ':   t_type,
                                        'label': cat,
                                    }
                                    st.session_state['_dialog_just_opened'] = True
                                    st.rerun()

        # Buchungstabelle
        st.markdown(
            "<div style='height:8px'></div>"
            "<div style='font-family:DM Mono,monospace;color:#334155;font-size:10px;"
            "font-weight:500;letter-spacing:1.5px;text-transform:uppercase;"
            "margin:20px 0 16px 0;'>Meine Buchungen</div>",
            unsafe_allow_html=True
        )
        try:
            df_t = conn.read(worksheet="transactions", ttl="0")
            if 'user' not in df_t.columns:
                st.info("Noch keine Buchungen vorhanden.")
            else:
                user_mask = df_t['user'] == st.session_state['user_name']
                del_mask  = (
                    ~df_t['deleted'].astype(str).str.strip().str.lower()
                    .isin(['true', '1', '1.0'])
                    if 'deleted' in df_t.columns
                    else pd.Series([True] * len(df_t), index=df_t.index)
                )
                user_df = df_t[user_mask & del_mask].copy()

                if user_df.empty:
                    st.info("Noch keine Buchungen vorhanden.")
                else:
                    user_df['betrag_anzeige'] = pd.to_numeric(user_df['betrag']).apply(
                        lambda x: f"+{x:.2f} €" if x > 0 else f"{x:.2f} €"
                    )
                    if 'timestamp' in user_df.columns:
                        user_df = user_df.sort_values('timestamp', ascending=False)
                    else:
                        user_df = user_df.sort_values('datum', ascending=False)

                    for orig_idx, row in user_df.iterrows():
                        notiz      = str(row.get('notiz', ''))
                        notiz      = '' if notiz.lower() == 'nan' else notiz
                        betrag_num = pd.to_numeric(row['betrag'], errors='coerce')
                        farbe      = '#4ade80' if row['typ'] == 'Einnahme' else '#f87171'
                        zeit_label = format_timestamp(
                            row.get('timestamp', ''), row.get('datum', '')
                        )

                        c1, c2, c3, c4, c5 = st.columns([2.5, 2, 2.5, 3, 1])
                        c1.markdown(
                            f"<span style='font-family:DM Mono,monospace;color:#334155;"
                            f"font-size:12px;line-height:2.4;display:block;'>{zeit_label}</span>",
                            unsafe_allow_html=True
                        )
                        c2.markdown(
                            f"<span style='font-family:DM Mono,monospace;color:{farbe};"
                            f"font-weight:500;font-size:13px;line-height:2.4;display:block;'>"
                            f"{row['betrag_anzeige']}</span>",
                            unsafe_allow_html=True
                        )
                        c3.markdown(
                            f"<span style='font-family:DM Sans,sans-serif;color:#64748b;"
                            f"font-size:13px;line-height:2.4;display:block;'>{row['kategorie']}</span>",
                            unsafe_allow_html=True
                        )
                        c4.markdown(
                            f"<span style='font-family:DM Sans,sans-serif;color:#334155;"
                            f"font-size:13px;line-height:2.4;display:block;'>{notiz}</span>",
                            unsafe_allow_html=True
                        )

                        with c5:
                            with st.popover("⋯", use_container_width=True):
                                if st.button("✏️ Bearbeiten", key=f"edit_btn_{orig_idx}",
                                             use_container_width=True):
                                    # Wenn gleicher Eintrag nochmal geklickt → zuklappen
                                    if st.session_state['edit_idx'] == orig_idx:
                                        st.session_state['edit_idx'] = None
                                    else:
                                        st.session_state['edit_idx'] = orig_idx
                                    st.session_state['show_new_cat'] = False
                                    st.rerun()
                                if st.button("🗑️ Löschen", key=f"del_btn_{orig_idx}",
                                             use_container_width=True):
                                    confirm_delete({
                                        "user":           row['user'],
                                        "datum":          row['datum'],
                                        "betrag":         row['betrag'],
                                        "betrag_anzeige": row['betrag_anzeige'],
                                        "kategorie":      row['kategorie'],
                                    })

                        if st.session_state['edit_idx'] == orig_idx:
                            with st.form(key=f"edit_form_{orig_idx}"):
                                st.markdown(
                                    "<p style='font-family:DM Sans,sans-serif;color:#38bdf8;"
                                    "font-weight:500;font-size:14px;margin-bottom:12px;'>"
                                    "Eintrag bearbeiten</p>",
                                    unsafe_allow_html=True
                                )
                                ec1, ec2 = st.columns(2)
                                with ec1:
                                    e_betrag = st.number_input(
                                        "Betrag in €", value=abs(float(betrag_num)),
                                        min_value=0.01, step=0.01, format="%.2f"
                                    )
                                    e_datum = st.date_input(
                                        "Datum",
                                        value=datetime.date.fromisoformat(str(row['datum']))
                                    )
                                with ec2:
                                    e_typ  = st.selectbox(
                                        "Typ", ["Einnahme", "Ausgabe"],
                                        index=0 if row['typ'] == "Einnahme" else 1
                                    )
                                    # FIX: Volle Kategorienliste mit Emojis + eigene Kategorien
                                    e_std_cats    = DEFAULT_CATS[e_typ]
                                    e_custom_cats = load_custom_cats(user_name, e_typ)
                                    e_all_cats    = e_std_cats + e_custom_cats
                                    # Aktuelle Kategorie vorauswählen — auch wenn Typ geändert
                                    curr_cat = row['kategorie']
                                    if curr_cat in e_all_cats:
                                        e_cat_idx = e_all_cats.index(curr_cat)
                                    else:
                                        e_cat_idx = 0
                                    e_cat = st.selectbox(
                                        "Kategorie", e_all_cats, index=e_cat_idx
                                    )
                                e_notiz = st.text_input(
                                    "Notiz (optional)", value=notiz,
                                    placeholder="z.B. Supermarkt, Tankstelle..."
                                )
                                col_save, col_cancel = st.columns(2)
                                with col_save:
                                    saved = st.form_submit_button(
                                        "Speichern", use_container_width=True, type="primary"
                                    )
                                with col_cancel:
                                    cancelled = st.form_submit_button(
                                        "Abbrechen", use_container_width=True
                                    )

                                if saved:
                                    df_all = conn.read(worksheet="transactions", ttl="0")
                                    if 'deleted' not in df_all.columns:
                                        df_all['deleted'] = ''
                                    match_idx = df_all[find_row_mask(df_all, row)].index
                                    if len(match_idx) > 0:
                                        neuer_betrag = e_betrag if e_typ == "Einnahme" else -e_betrag
                                        df_all.loc[match_idx[0], 'datum']     = str(e_datum)
                                        df_all.loc[match_idx[0], 'typ']       = e_typ
                                        df_all.loc[match_idx[0], 'kategorie'] = e_cat
                                        df_all.loc[match_idx[0], 'betrag']    = neuer_betrag
                                        df_all.loc[match_idx[0], 'notiz']     = e_notiz
                                        conn.update(worksheet="transactions", data=df_all)
                                        st.session_state['edit_idx'] = None
                                        st.success("✅ Eintrag gespeichert!")
                                        st.rerun()
                                    else:
                                        st.error("❌ Eintrag nicht gefunden.")

                                if cancelled:
                                    st.session_state['edit_idx'] = None
                                    st.rerun()

        except Exception as e:
            st.warning(f"Fehler beim Laden: {e}")

    # ── Einstellungen ────────────────────────────────────────
    elif menu == "⚙️ Einstellungen":
        st.markdown(
            "<div style='margin-bottom:28px;'>"
            "<h1 style='font-family:DM Sans,sans-serif;font-size:28px;font-weight:600;"
            "color:#e2e8f0;margin:0 0 4px 0;letter-spacing:-0.5px;'>Einstellungen</h1>"
            "<p style='font-family:DM Sans,sans-serif;color:#334155;font-size:14px;margin:0;'>"
            "Konto und Sicherheit</p>"
            "</div>",
            unsafe_allow_html=True
        )
        st.markdown(
            "<p style='font-family:DM Mono,monospace;color:#334155;font-size:10px;"
            "font-weight:500;letter-spacing:1.5px;text-transform:uppercase;"
            "margin-bottom:16px;'>Passwort ändern</p>",
            unsafe_allow_html=True
        )
        with st.form("pw_form"):
            pw_alt  = st.text_input("Aktuelles Passwort", type="password")
            pw_neu  = st.text_input("Neues Passwort", type="password")
            pw_neu2 = st.text_input("Neues Passwort wiederholen", type="password")

            if st.form_submit_button("Passwort ändern", use_container_width=True):
                df_u = conn.read(worksheet="users", ttl="0")
                idx  = df_u[df_u['username'] == st.session_state['user_name']].index
                if idx.empty:
                    st.error("❌ Benutzer nicht gefunden.")
                elif make_hashes(pw_alt) != str(df_u.loc[idx[0], 'password']):
                    st.error("❌ Aktuelles Passwort ist falsch.")
                elif pw_neu == pw_alt:
                    st.error("❌ Das neue Passwort darf nicht dem alten entsprechen.")
                else:
                    ok, msg = check_password_strength(pw_neu)
                    if not ok:
                        st.error(f"❌ {msg}")
                    elif pw_neu != pw_neu2:
                        st.error("❌ Die neuen Passwörter stimmen nicht überein.")
                    else:
                        df_u.loc[idx[0], 'password'] = make_hashes(pw_neu)
                        conn.update(worksheet="users", data=df_u)
                        st.success("✅ Passwort erfolgreich geändert!")


# ============================================================
#  APP — Nicht eingeloggt (Auth)
# ============================================================

else:
    st.markdown("<div style='height:10vh;'></div>", unsafe_allow_html=True)
    st.markdown("<h1 class='main-title'>Balancely</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p class='sub-title'>Verwalte deine Finanzen mit Klarheit</p>",
        unsafe_allow_html=True
    )

    _, center_col, _ = st.columns([1, 1.2, 1])
    with center_col:
        mode = st.session_state['auth_mode']

        # ── Login ────────────────────────────────────────────
        if mode == 'login':
            with st.form("login_form"):
                st.markdown(
                    "<h3 style='text-align:center;color:#e2e8f0;font-family:DM Sans,sans-serif;"
                    "font-weight:600;font-size:22px;letter-spacing:-0.5px;margin-bottom:24px;'>"
                    "Anmelden</h3>",
                    unsafe_allow_html=True
                )
                u_in = st.text_input("Username", placeholder="Benutzername")
                p_in = st.text_input("Passwort", type="password")

                if st.form_submit_button("Anmelden", use_container_width=True):
                    time.sleep(1)
                    df_u     = conn.read(worksheet="users", ttl="0")
                    matching = df_u[df_u['username'] == u_in]
                    user_row = matching.iloc[[-1]] if not matching.empty else matching

                    if not user_row.empty and \
                       make_hashes(p_in) == str(user_row.iloc[0]['password']):
                        if not is_verified(user_row.iloc[0].get('verified', 'True')):
                            st.error("❌ Bitte verifiziere zuerst deine E-Mail-Adresse.")
                        else:
                            st.session_state['logged_in'] = True
                            st.session_state['user_name'] = u_in
                            st.rerun()
                    else:
                        st.error("❌ Login ungültig.")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Konto erstellen", use_container_width=True):
                    st.session_state['auth_mode'] = 'signup'
                    st.rerun()
            with col2:
                if st.button("Passwort vergessen?", use_container_width=True, type="secondary"):
                    st.session_state['auth_mode'] = 'forgot'
                    st.rerun()

        # ── Registrierung ────────────────────────────────────
        elif mode == 'signup':
            with st.form("signup_form"):
                st.markdown(
                    "<h3 style='text-align:center;color:#e2e8f0;font-family:DM Sans,sans-serif;"
                    "font-weight:600;font-size:22px;letter-spacing:-0.5px;margin-bottom:24px;'>"
                    "Registrierung</h3>",
                    unsafe_allow_html=True
                )
                s_name  = st.text_input("Name",     placeholder="Max Mustermann")
                s_user  = st.text_input("Username", placeholder="max123")
                s_email = st.text_input("E-Mail",   placeholder="max@beispiel.de")
                s_pass  = st.text_input("Passwort", type="password")
                c_pass  = st.text_input("Passwort wiederholen", type="password")

                if st.form_submit_button("Konto erstellen", use_container_width=True):
                    if not all([s_name, s_user, s_email, s_pass]):
                        st.error("❌ Bitte fülle alle Felder aus!")
                    elif len(s_name.strip().split()) < 2:
                        st.error("❌ Bitte gib deinen vollständigen Vor- und Nachnamen an.")
                    elif not is_valid_email(s_email):
                        st.error("❌ Bitte gib eine gültige E-Mail-Adresse ein.")
                    else:
                        ok, msg = check_password_strength(s_pass)
                        if not ok:
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
                                code   = generate_code()
                                expiry = datetime.datetime.now() + datetime.timedelta(minutes=10)
                                html   = email_html(
                                    "Willkommen bei Balancely! Dein Verifizierungscode lautet:",
                                    code
                                )
                                if send_email(s_email.strip().lower(),
                                              "Balancely – E-Mail verifizieren", html):
                                    st.session_state['pending_user'] = {
                                        "name":     make_hashes(s_name.strip()),
                                        "username": s_user,
                                        "email":    s_email.strip().lower(),
                                        "password": make_hashes(s_pass),
                                    }
                                    st.session_state['verify_code']   = code
                                    st.session_state['verify_expiry'] = expiry
                                    st.session_state['auth_mode']     = 'verify_email'
                                    st.rerun()
                                else:
                                    st.error("❌ E-Mail konnte nicht gesendet werden.")

            if st.button("Zurück zum Login", use_container_width=True):
                st.session_state['auth_mode'] = 'login'
                st.rerun()

        # ── E-Mail verifizieren ──────────────────────────────
        elif mode == 'verify_email':
            pending_email = st.session_state['pending_user'].get('email', '')
            with st.form("verify_form"):
                st.markdown(
                    "<h3 style='text-align:center;color:#e2e8f0;font-family:DM Sans,sans-serif;"
                    "font-weight:600;font-size:22px;letter-spacing:-0.5px;margin-bottom:12px;'>"
                    "E-Mail verifizieren</h3>",
                    unsafe_allow_html=True
                )
                st.markdown(
                    f"<p style='text-align:center;color:#475569;font-family:DM Sans,sans-serif;"
                    f"font-size:14px;margin-bottom:20px;'>Code gesendet an "
                    f"<span style='color:#38bdf8;'>{pending_email}</span></p>",
                    unsafe_allow_html=True
                )
                code_input = st.text_input("Code eingeben", placeholder="123456", max_chars=6)

                if st.form_submit_button("Bestätigen", use_container_width=True):
                    if st.session_state['verify_expiry'] and \
                       datetime.datetime.now() > st.session_state['verify_expiry']:
                        st.error("⏰ Code abgelaufen. Bitte erneut registrieren.")
                        st.session_state['auth_mode'] = 'signup'
                        st.rerun()
                    elif code_input.strip() != st.session_state['verify_code']:
                        st.error("❌ Falscher Code.")
                    else:
                        df_u  = conn.read(worksheet="users", ttl="0")
                        new_u = pd.DataFrame([{
                            **st.session_state['pending_user'],
                            "verified":     "True",
                            "token":        "",
                            "token_expiry": "",
                        }])
                        conn.update(worksheet="users",
                                    data=pd.concat([df_u, new_u], ignore_index=True))
                        st.session_state['pending_user']  = {}
                        st.session_state['verify_code']   = ""
                        st.session_state['verify_expiry'] = None
                        st.session_state['auth_mode']     = 'login'
                        st.success("✅ E-Mail verifiziert! Du kannst dich jetzt einloggen.")

            if st.button("Zum Login", use_container_width=True, type="primary"):
                st.session_state['auth_mode'] = 'login'
                st.rerun()

        # ── Passwort vergessen ───────────────────────────────
        elif mode == 'forgot':
            with st.form("forgot_form"):
                st.markdown(
                    "<h3 style='text-align:center;color:#e2e8f0;font-family:DM Sans,sans-serif;"
                    "font-weight:600;font-size:22px;letter-spacing:-0.5px;margin-bottom:12px;'>"
                    "Passwort vergessen</h3>",
                    unsafe_allow_html=True
                )
                st.markdown(
                    "<p style='text-align:center;color:#475569;font-family:DM Sans,sans-serif;"
                    "font-size:14px;margin-bottom:20px;'>Gib deine E-Mail-Adresse ein.</p>",
                    unsafe_allow_html=True
                )
                forgot_email = st.text_input("E-Mail", placeholder="deine@email.de")

                if st.form_submit_button("Code senden", use_container_width=True):
                    if not is_valid_email(forgot_email):
                        st.error("❌ Bitte gib eine gültige E-Mail-Adresse ein.")
                    else:
                        df_u = conn.read(worksheet="users", ttl="0")
                        idx  = df_u[df_u['email'] == forgot_email.strip().lower()].index
                        if idx.empty:
                            st.success("✅ Falls diese E-Mail registriert ist, wurde ein Code gesendet.")
                        else:
                            code   = generate_code()
                            expiry = datetime.datetime.now() + datetime.timedelta(minutes=10)
                            html   = email_html(
                                "Dein Code zum Zurücksetzen des Passworts lautet:", code
                            )
                            if send_email(forgot_email.strip().lower(),
                                          "Balancely – Passwort zurücksetzen", html):
                                st.session_state['reset_email']  = forgot_email.strip().lower()
                                st.session_state['reset_code']   = code
                                st.session_state['reset_expiry'] = expiry
                                st.session_state['auth_mode']    = 'reset_password'
                                st.rerun()

            if st.button("Zurück zum Login", use_container_width=True):
                st.session_state['auth_mode'] = 'login'
                st.rerun()

        # ── Passwort zurücksetzen ────────────────────────────
        elif mode == 'reset_password':
            with st.form("reset_form"):
                st.markdown(
                    "<h3 style='text-align:center;color:#e2e8f0;font-family:DM Sans,sans-serif;"
                    "font-weight:600;font-size:22px;letter-spacing:-0.5px;margin-bottom:12px;'>"
                    "Passwort zurücksetzen</h3>",
                    unsafe_allow_html=True
                )
                st.markdown(
                    f"<p style='text-align:center;color:#475569;font-family:DM Sans,sans-serif;"
                    f"font-size:14px;margin-bottom:20px;'>Code gesendet an "
                    f"<span style='color:#38bdf8;'>{st.session_state['reset_email']}</span></p>",
                    unsafe_allow_html=True
                )
                code_input = st.text_input("6-stelliger Code", placeholder="123456", max_chars=6)
                pw_neu     = st.text_input("Neues Passwort", type="password")
                pw_neu2    = st.text_input("Passwort wiederholen", type="password")

                if st.form_submit_button("Passwort speichern", use_container_width=True):
                    if st.session_state['reset_expiry'] and \
                       datetime.datetime.now() > st.session_state['reset_expiry']:
                        st.error("⏰ Code abgelaufen. Bitte neu anfordern.")
                        st.session_state['auth_mode'] = 'forgot'
                        st.rerun()
                    elif code_input.strip() != st.session_state['reset_code']:
                        st.error("❌ Falscher Code.")
                    else:
                        ok, msg = check_password_strength(pw_neu)
                        if not ok:
                            st.error(f"❌ {msg}")
                        elif pw_neu != pw_neu2:
                            st.error("❌ Die neuen Passwörter stimmen nicht überein.")
                        else:
                            df_u = conn.read(worksheet="users", ttl="0")
                            idx  = df_u[df_u['email'] == st.session_state['reset_email']].index
                            if not idx.empty:
                                df_u.loc[idx[0], 'password'] = make_hashes(pw_neu)
                                conn.update(worksheet="users", data=df_u)
                                st.session_state['reset_email']  = ""
                                st.session_state['reset_code']   = ""
                                st.session_state['reset_expiry'] = None
                                st.session_state['auth_mode']    = 'login'
                                st.success("✅ Passwort geändert! Du kannst dich jetzt einloggen.")
                                st.rerun()

            if st.button("Zurück zum Login", use_container_width=True):
                st.session_state['auth_mode'] = 'login'
                st.rerun()
