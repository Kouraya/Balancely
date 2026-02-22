# ============================================================
#  Balancely — Persönliche Finanzverwaltung  v3
#  Neue Features: Kalender-Heatmap, End-of-Month Forecast,
#  Spar-Potenzial, Spartöpfe, Dashboard-Sparziel-Warnung
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

h1, h2, h3, h4 { font-family: 'DM Sans', sans-serif !important; letter-spacing: -0.5px; }

[data-testid="stMain"] .block-container {
    padding-top: 2rem !important;
    max-width: 1200px !important;
}

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

[data-testid="stForm"] {
    background: linear-gradient(145deg, rgba(15,23,42,0.9) 0%, rgba(10,16,32,0.95) 100%) !important;
    backdrop-filter: blur(20px) !important;
    padding: 40px !important;
    border-radius: 20px !important;
    border: 1px solid rgba(148,163,184,0.08) !important;
    box-shadow: 0 25px 50px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.04) !important;
}

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

button[data-testid="stNumberInputStepDown"],
button[data-testid="stNumberInputStepUp"] { display: none !important; }
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

button, [data-testid="stPopover"] button,
div[data-baseweb="select"],
div[data-baseweb="select"] *,
div[data-testid="stDateInput"],
[data-testid="stSelectbox"] * { cursor: pointer !important; }

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

hr {
    border-color: rgba(148,163,184,0.08) !important;
    margin: 24px 0 !important;
}

[data-testid="stMarkdownContainer"] h3 {
    font-size: 15px !important;
    font-weight: 600 !important;
    color: #64748b !important;
    letter-spacing: 0.5px !important;
    text-transform: uppercase !important;
}

[data-testid="stAlert"] {
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 14px !important;
}

[data-testid="stPopover"] > div {
    background: #0d1729 !important;
    border: 1px solid rgba(148,163,184,0.1) !important;
    border-radius: 12px !important;
    box-shadow: none !important;
}

[data-testid="stExpander"] {
    border: 1px solid rgba(148,163,184,0.08) !important;
    border-radius: 12px !important;
    background: rgba(10,16,32,0.5) !important;
}

/* ── Spartöpfe progress bars ─────────────────────────────── */
.topf-progress-bg {
    background: rgba(30,41,59,0.8);
    border-radius: 99px;
    height: 5px;
    overflow: hidden;
    margin-top: 8px;
}
.topf-progress-fill {
    height: 100%;
    border-radius: 99px;
    transition: width 0.6s ease;
}

/* ── Heatmap calendar cells ──────────────────────────────── */
.heatmap-cell {
    display: inline-block;
    width: 36px;
    height: 36px;
    border-radius: 8px;
    text-align: center;
    line-height: 36px;
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    font-weight: 500;
    transition: transform 0.15s ease;
    cursor: default;
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
    "Depot":    ["📦 ETF", "📊 Aktien", "🪙 Krypto", "🏦 Tagesgeld", "💎 Sonstiges"],
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
    'analysen_zeitraum':  'Monatlich',
    # Spartöpfe
    'topf_edit_idx':    None,
    'topf_delete_idx':  None,
    'show_new_topf':    False,
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

conn = st.connection("gsheets", type=GSheetsConnection)


# ============================================================
#  Daten-Hilfsfunktionen
# ============================================================

def load_custom_cats(user: str, typ: str) -> list:
    try:
        df = conn.read(worksheet="categories", ttl="5")
        if df.empty or 'user' not in df.columns:
            return []
        rows = df[(df['user'] == user) & (df['typ'] == typ)]
        return rows['kategorie'].tolist()
    except Exception:
        return []


def save_custom_cat(user: str, typ: str, kategorie: str):
    try:
        df = conn.read(worksheet="categories", ttl="5")
    except Exception:
        df = pd.DataFrame(columns=['user', 'typ', 'kategorie'])
    new_row = pd.DataFrame([{'user': user, 'typ': typ, 'kategorie': kategorie}])
    conn.update(worksheet="categories", data=pd.concat([df, new_row], ignore_index=True))


def delete_custom_cat(user: str, typ: str, kategorie: str):
    try:
        df = conn.read(worksheet="categories", ttl="5")
        df = df[~((df['user'] == user) & (df['typ'] == typ) & (df['kategorie'] == kategorie))]
        conn.update(worksheet="categories", data=df)
    except Exception:
        pass


def update_custom_cat(user: str, typ: str, old_label: str, new_label: str):
    try:
        df = conn.read(worksheet="categories", ttl="5")
        mask = (df['user'] == user) & (df['typ'] == typ) & (df['kategorie'] == old_label)
        df.loc[mask, 'kategorie'] = new_label
        conn.update(worksheet="categories", data=df)
    except Exception:
        pass


def load_goal(user: str) -> float:
    try:
        df_g = conn.read(worksheet="goals", ttl="5")
        if df_g.empty or 'user' not in df_g.columns:
            return 0.0
        row = df_g[df_g['user'] == user]
        if row.empty:
            return 0.0
        return float(row.iloc[-1].get('sparziel', 0) or 0)
    except Exception:
        return 0.0


def save_goal(user: str, goal: float):
    try:
        df_g = conn.read(worksheet="goals", ttl="5")
    except Exception:
        df_g = pd.DataFrame(columns=['user', 'sparziel'])
    if 'user' not in df_g.columns:
        df_g = pd.DataFrame(columns=['user', 'sparziel'])
    mask = df_g['user'] == user
    if mask.any():
        df_g.loc[mask, 'sparziel'] = goal
    else:
        df_g = pd.concat([df_g, pd.DataFrame([{'user': user, 'sparziel': goal}])],
                         ignore_index=True)
    conn.update(worksheet="goals", data=df_g)


# ── Spartöpfe ────────────────────────────────────────────────

def load_toepfe(user: str) -> list:
    """Load all Spartöpfe for a user from 'toepfe' worksheet."""
    try:
        df = conn.read(worksheet="toepfe", ttl="5")
        if df.empty or 'user' not in df.columns:
            return []
        rows = df[df['user'] == user]
        result = []
        for _, r in rows.iterrows():
            deleted = str(r.get('deleted', '')).strip().lower()
            if deleted in ('true', '1', '1.0'):
                continue
            result.append({
                'id':       str(r.get('id', '')),
                'name':     str(r.get('name', '')),
                'ziel':     float(r.get('ziel', 0) or 0),
                'gespart':  float(r.get('gespart', 0) or 0),
                'emoji':    str(r.get('emoji', '🪣')),
                'farbe':    str(r.get('farbe', '#38bdf8')),
            })
        return result
    except Exception:
        return []


TOPF_PALETTE = [
    "#38bdf8", "#4ade80", "#a78bfa", "#fb923c",
    "#f472b6", "#34d399", "#facc15", "#60a5fa",
]

def save_topf(user: str, name: str, ziel: float, emoji: str):
    try:
        df = conn.read(worksheet="toepfe", ttl="5")
    except Exception:
        df = pd.DataFrame(columns=['user', 'id', 'name', 'ziel', 'gespart', 'emoji', 'farbe', 'deleted'])
    # Auto-Farbe basierend auf Anzahl vorhandener Töpfe
    existing_count = len(df[df['user'] == user]) if not df.empty and 'user' in df.columns else 0
    auto_farbe = TOPF_PALETTE[existing_count % len(TOPF_PALETTE)]
    topf_id = f"{user}_{int(time.time())}"
    new_row = pd.DataFrame([{
        'user': user, 'id': topf_id, 'name': name,
        'ziel': ziel, 'gespart': 0, 'emoji': emoji,
        'farbe': auto_farbe, 'deleted': '',
    }])
    conn.update(worksheet="toepfe", data=pd.concat([df, new_row], ignore_index=True))
    return topf_id


def update_topf_gespart(user: str, topf_id: str, topf_name: str, delta: float):
    """Update gespart in toepfe AND write a Spartopf transaction."""
    # 1. Topf-Guthaben aktualisieren
    try:
        df = conn.read(worksheet="toepfe", ttl="5")
        mask = (df['user'] == user) & (df['id'] == topf_id)
        if mask.any():
            current = float(df.loc[mask, 'gespart'].values[0] or 0)
            df.loc[mask, 'gespart'] = max(0, current + delta)
            conn.update(worksheet="toepfe", data=df)
    except Exception:
        pass
    # 2. Transaktion schreiben (Spartopf-Typ, negativ = Geld geht weg vom Konto)
    try:
        df_t = conn.read(worksheet="transactions", ttl="5")
        sign = -1 if delta > 0 else 1  # Einzahlung = vom Konto weg; Auszahlung = zurück aufs Konto
        notiz = f"{'↓' if delta > 0 else '↑'} {topf_name}"
        new_row = pd.DataFrame([{
            "user":      user,
            "datum":     str(datetime.date.today()),
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "typ":       "Spartopf",
            "kategorie": f"🪣 {topf_name}",
            "betrag":    sign * abs(delta),
            "notiz":     notiz,
        }])
        conn.update(worksheet="transactions", data=pd.concat([df_t, new_row], ignore_index=True))
    except Exception:
        pass


def delete_topf(user: str, topf_id: str):
    try:
        df = conn.read(worksheet="toepfe", ttl="5")
        mask = (df['user'] == user) & (df['id'] == topf_id)
        df.loc[mask, 'deleted'] = 'True'
        conn.update(worksheet="toepfe", data=df)
    except Exception:
        pass


def update_topf_meta(user: str, topf_id: str, name: str, ziel: float, emoji: str):
    try:
        df = conn.read(worksheet="toepfe", ttl="5")
        mask = (df['user'] == user) & (df['id'] == topf_id)
        if mask.any():
            df.loc[mask, 'name']  = name
            df.loc[mask, 'ziel']  = ziel
            df.loc[mask, 'emoji'] = emoji
            conn.update(worksheet="toepfe", data=df)
    except Exception:
        pass


# ============================================================
#  Dialog-Funktionen
# ============================================================

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
            df_all = conn.read(worksheet="transactions", ttl="5")
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
            ["📈 Dashboard", "💸 Transaktionen", "📂 Analysen", "🪣 Spartöpfe", "⚙️ Einstellungen"],
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

    if menu != st.session_state.get('_last_menu', menu):
        st.session_state['edit_idx'] = None

    st.session_state['_last_menu'] = menu

    # ── Dashboard ────────────────────────────────────────────
    if menu == "📈 Dashboard":
        import plotly.graph_objects as go

        now = datetime.datetime.now()

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
            df_t = conn.read(worksheet="transactions", ttl="5")
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
                    alle["betrag_num"]     = pd.to_numeric(alle["betrag"],     errors="coerce")

                    ein       = monat_df[monat_df["typ"] == "Einnahme"]["betrag_num"].sum()
                    aus       = monat_df[monat_df["typ"] == "Ausgabe"]["betrag_num"].abs().sum()
                    dep_monat = monat_df[monat_df["typ"] == "Depot"]["betrag_num"].abs().sum()
                    # Spartopf: negativ = Einzahlung (Konto ↓), positiv = Auszahlung (Konto ↑)
                    spartopf_netto = monat_df[monat_df["typ"] == "Spartopf"]["betrag_num"].sum()

                    bank = ein - aus - dep_monat + spartopf_netto  # spartopf_netto ist bereits negativ bei Einzahlung
                    dep_gesamt = alle[alle["typ"] == "Depot"]["betrag_num"].abs().sum()
                    # Spartöpfe gesamt (alle Töpfe des Users)
                    toepfe_gesamt = load_toepfe(st.session_state["user_name"])
                    topf_gesamt_val = sum(t['gespart'] for t in toepfe_gesamt)
                    networth = bank + dep_gesamt + topf_gesamt_val

                    bank_color = "#e2e8f0" if bank >= 0 else "#f87171"
                    bank_str   = f"{bank:,.2f} €" if bank >= 0 else f"-{abs(bank):,.2f} €"
                    nw_color   = "#4ade80" if networth >= 0 else "#f87171"
                    nw_str     = f"{networth:,.2f} €" if networth >= 0 else f"-{abs(networth):,.2f} €"

                    # ── NEU: Sparziel-Warnung auf dem Dashboard ──────
                    # Nur für aktuellen Monat anzeigen
                    if offset == 0:
                        current_goal_dash = load_goal(st.session_state["user_name"])
                        if current_goal_dash > 0:
                            # Spartopf-Einzahlungen diesen Monat zählen als gespartes Geld
                            spartopf_einzahl_monat = abs(monat_df[
                                (monat_df["typ"] == "Spartopf") & (monat_df["betrag_num"] < 0)
                            ]["betrag_num"].sum())
                            # "Effektiv gespart" = verfügbares Bankgeld + was in Töpfe geflossen ist
                            effektiv_gespart = bank + spartopf_einzahl_monat

                            if effektiv_gespart < current_goal_dash:
                                fehl = current_goal_dash - effektiv_gespart
                                topf_hint = f" · davon {spartopf_einzahl_monat:,.2f} € in Töpfen" if spartopf_einzahl_monat > 0 else ""
                                st.markdown(
                                    f"<div style='background:linear-gradient(135deg,rgba(251,113,133,0.08),rgba(239,68,68,0.05));"
                                    f"border:1px solid rgba(248,113,113,0.25);border-left:3px solid #f87171;"
                                    f"border-radius:14px;padding:14px 18px;margin-bottom:20px;"
                                    f"display:flex;align-items:center;gap:14px;'>"
                                    f"<span style='font-size:22px;'>⚠️</span>"
                                    f"<div>"
                                    f"<div style='font-family:DM Sans,sans-serif;color:#fca5a5;"
                                    f"font-weight:600;font-size:14px;margin-bottom:2px;'>"
                                    f"Du liegst {fehl:,.2f} € unter deinem Sparziel</div>"
                                    f"<div style='font-family:DM Sans,sans-serif;color:#64748b;"
                                    f"font-size:13px;'>Ziel: {current_goal_dash:,.2f} € · "
                                    f"Gespart: {effektiv_gespart:,.2f} €{topf_hint}</div>"
                                    f"</div>"
                                    f"</div>",
                                    unsafe_allow_html=True
                                )
                            else:
                                ueber = effektiv_gespart - current_goal_dash
                                topf_hint = f" · {spartopf_einzahl_monat:,.2f} € davon in Töpfen" if spartopf_einzahl_monat > 0 else ""
                                st.markdown(
                                    f"<div style='background:linear-gradient(135deg,rgba(74,222,128,0.05),rgba(34,197,94,0.03));"
                                    f"border:1px solid rgba(74,222,128,0.2);border-left:3px solid #4ade80;"
                                    f"border-radius:14px;padding:14px 18px;margin-bottom:20px;"
                                    f"display:flex;align-items:center;gap:14px;'>"
                                    f"<span style='font-size:22px;'>✅</span>"
                                    f"<div>"
                                    f"<div style='font-family:DM Sans,sans-serif;color:#86efac;"
                                    f"font-weight:600;font-size:14px;margin-bottom:2px;'>"
                                    f"Sparziel erreicht! +{ueber:,.2f} € Puffer</div>"
                                    f"<div style='font-family:DM Sans,sans-serif;color:#64748b;"
                                    f"font-size:13px;'>Gespart: {effektiv_gespart:,.2f} €{topf_hint}</div>"
                                    f"</div>"
                                    f"</div>",
                                    unsafe_allow_html=True
                                )

                    row1 = (
                        f"<div style='display:flex;gap:14px;margin:0 0 12px 0;flex-wrap:wrap;'>"
                        f"<div style='flex:1;min-width:160px;background:linear-gradient(145deg,rgba(14,22,38,0.9),rgba(10,16,30,0.95));"
                        f"border:1px solid rgba(148,163,184,0.08);border-radius:16px;padding:20px 22px;'>"
                        f"<div style='font-family:DM Mono,monospace;font-size:10px;color:#334155;"
                        f"letter-spacing:1.5px;text-transform:uppercase;margin-bottom:6px;'>Bankkontostand</div>"
                        f"<div style='font-family:DM Mono,monospace;font-size:10px;color:#1e293b;margin-bottom:10px;'>"
                        f"diesen Monat</div>"
                        f"<div style='font-family:DM Sans,sans-serif;color:{bank_color};font-size:24px;"
                        f"font-weight:600;letter-spacing:-0.5px;'>{bank_str}</div>"
                        f"</div>"
                        f"<div style='flex:1;min-width:160px;background:linear-gradient(145deg,rgba(14,22,38,0.9),rgba(10,16,30,0.95));"
                        f"border:1px solid rgba(56,189,248,0.12);border-radius:16px;padding:20px 22px;'>"
                        f"<div style='font-family:DM Mono,monospace;font-size:10px;color:#1e40af;"
                        f"letter-spacing:1.5px;text-transform:uppercase;margin-bottom:6px;'>Gesamtvermögen</div>"
                        f"<div style='font-family:DM Mono,monospace;font-size:10px;color:#1e293b;margin-bottom:10px;'>"
                        f"Bank + Depot + Töpfe</div>"
                        f"<div style='font-family:DM Sans,sans-serif;color:{nw_color};font-size:24px;"
                        f"font-weight:600;letter-spacing:-0.5px;'>{nw_str}</div>"
                        f"</div>"
                        f"</div>"
                    )
                    spartopf_einzahl_monat = abs(monat_df[
                        (monat_df["typ"] == "Spartopf") & (monat_df["betrag_num"] < 0)
                    ]["betrag_num"].sum())
                    dep_html = (
                        f"<div style='flex:1;min-width:160px;background:linear-gradient(145deg,rgba(14,22,38,0.9),rgba(10,16,30,0.95));"
                        f"border:1px solid rgba(56,189,248,0.15);border-radius:16px;padding:20px 22px;'>"
                        f"<div style='font-family:DM Mono,monospace;font-size:10px;color:#1e40af;"
                        f"letter-spacing:1.5px;text-transform:uppercase;margin-bottom:6px;'>Depot</div>"
                        f"<div style='font-family:DM Mono,monospace;font-size:10px;color:#1e293b;margin-bottom:10px;'>"
                        f"diesen Monat eingezahlt</div>"
                        f"<div style='font-family:DM Sans,sans-serif;color:#38bdf8;font-size:24px;"
                        f"font-weight:600;letter-spacing:-0.5px;'>{dep_monat:,.2f} €</div>"
                        f"</div>"
                        if dep_monat > 0 else ""
                    )
                    topf_html = (
                        f"<div style='flex:1;min-width:160px;background:linear-gradient(145deg,rgba(14,22,38,0.9),rgba(10,16,30,0.95));"
                        f"border:1px solid rgba(167,139,250,0.2);border-radius:16px;padding:20px 22px;'>"
                        f"<div style='font-family:DM Mono,monospace;font-size:10px;color:#7c3aed;"
                        f"letter-spacing:1.5px;text-transform:uppercase;margin-bottom:6px;'>Spartöpfe</div>"
                        f"<div style='font-family:DM Mono,monospace;font-size:10px;color:#1e293b;margin-bottom:10px;'>"
                        f"diesen Monat eingelegt</div>"
                        f"<div style='font-family:DM Sans,sans-serif;color:#a78bfa;font-size:24px;"
                        f"font-weight:600;letter-spacing:-0.5px;'>{spartopf_einzahl_monat:,.2f} €</div>"
                        f"</div>"
                        if spartopf_einzahl_monat > 0 else ""
                    )
                    row2 = (
                        f"<div style='display:flex;gap:14px;margin:0 0 28px 0;flex-wrap:wrap;'>"
                        f"<div style='flex:1;min-width:160px;background:linear-gradient(145deg,rgba(14,22,38,0.9),rgba(10,16,30,0.95));"
                        f"border:1px solid rgba(148,163,184,0.08);border-radius:16px;padding:20px 22px;'>"
                        f"<div style='font-family:DM Mono,monospace;font-size:10px;color:#334155;"
                        f"letter-spacing:1.5px;text-transform:uppercase;margin-bottom:10px;'>Einnahmen</div>"
                        f"<div style='font-family:DM Sans,sans-serif;color:#4ade80;font-size:24px;"
                        f"font-weight:600;letter-spacing:-0.5px;'>+{ein:,.2f} €</div>"
                        f"</div>"
                        f"<div style='flex:1;min-width:160px;background:linear-gradient(145deg,rgba(14,22,38,0.9),rgba(10,16,30,0.95));"
                        f"border:1px solid rgba(148,163,184,0.08);border-radius:16px;padding:20px 22px;'>"
                        f"<div style='font-family:DM Mono,monospace;font-size:10px;color:#334155;"
                        f"letter-spacing:1.5px;text-transform:uppercase;margin-bottom:10px;'>Ausgaben</div>"
                        f"<div style='font-family:DM Sans,sans-serif;color:#f87171;font-size:24px;"
                        f"font-weight:600;letter-spacing:-0.5px;'>-{aus:,.2f} €</div>"
                        f"</div>"
                        + dep_html
                        + topf_html
                        + f"</div>"
                    )
                    st.markdown(row1 + row2, unsafe_allow_html=True)

                    ausg_df = monat_df[monat_df["typ"] == "Ausgabe"].copy()
                    ausg_df["betrag_num"] = ausg_df["betrag_num"].abs()
                    ausg_grp = (ausg_df.groupby("kategorie")["betrag_num"]
                                .sum().reset_index()
                                .sort_values("betrag_num", ascending=False))

                    ein_df  = monat_df[monat_df["typ"] == "Einnahme"].copy()
                    ein_grp = (ein_df.groupby("kategorie")["betrag_num"]
                               .sum().reset_index()
                               .sort_values("betrag_num", ascending=False))

                    dep_df  = monat_df[monat_df["typ"] == "Depot"].copy()
                    dep_df["betrag_num"] = pd.to_numeric(dep_df["betrag_num"], errors="coerce").abs()
                    dep_grp = (dep_df.groupby("kategorie")["betrag_num"]
                               .sum().reset_index()
                               .sort_values("betrag_num", ascending=False))

                    PALETTE_AUS = [
                        "#ff0000","#ff5232","#ff7b5a","#ff9e81",
                        "#ffbfaa","#ffdfd4","#dc2626","#b91c1c",
                        "#991b1b","#7f1d1d",
                    ]
                    PALETTE_EIN = [
                        "#008000","#469536","#6eaa5e","#93bf85",
                        "#b7d5ac","#dbead5","#2d7a2d","#4a9e4a",
                        "#5cb85c","#80c780",
                    ]
                    PALETTE_DEP = [
                        "#0000ff","#1e0bd0","#2510a3","#241178",
                        "#1f104f","#19092e","#2563eb","#1d4ed8",
                        "#1e40af","#1e3a8a",
                    ]

                    all_cats, all_vals, all_colors, all_types = [], [], [], []
                    for i, (_, row) in enumerate(ein_grp.iterrows()):
                        all_cats.append(row["kategorie"])
                        all_vals.append(float(row["betrag_num"]))
                        all_colors.append(PALETTE_EIN[i % len(PALETTE_EIN)])
                        all_types.append("Einnahme")
                    for i, (_, row) in enumerate(ausg_grp.iterrows()):
                        all_cats.append(row["kategorie"])
                        all_vals.append(float(row["betrag_num"]))
                        all_colors.append(PALETTE_AUS[i % len(PALETTE_AUS)])
                        all_types.append("Ausgabe")
                    for i, (_, row) in enumerate(dep_grp.iterrows()):
                        all_cats.append(row["kategorie"])
                        all_vals.append(float(row["betrag_num"]))
                        all_colors.append(PALETTE_DEP[i % len(PALETTE_DEP)])
                        all_types.append("Depot")

                    total_sum = sum(all_vals) if sum(all_vals) > 0 else 1

                    fig = go.Figure(go.Pie(
                        labels=all_cats,
                        values=all_vals,
                        hole=0.62,
                        marker=dict(
                            colors=all_colors,
                            line=dict(color="rgba(5,10,20,0.8)", width=2),
                        ),
                        textinfo="none",
                        hoverinfo="none",
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
                            font=dict(color="#e2e8f0", size=13, family="DM Sans, sans-serif"),
                            namelength=-1,
                            align="left",
                        ),
                        annotations=[
                            dict(text="BANK", x=0.5, y=0.62, showarrow=False,
                                 font=dict(size=10, color="#334155", family="DM Mono, monospace"),
                                 xref="paper", yref="paper"),
                            dict(text=f"<b>{bank_str}</b>", x=0.5, y=0.50, showarrow=False,
                                 font=dict(size=22, color=bank_color, family="DM Sans, sans-serif"),
                                 xref="paper", yref="paper"),
                            dict(text=f"+{ein:,.0f}  /  -{aus:,.0f} €", x=0.5, y=0.38,
                                 showarrow=False,
                                 font=dict(size=11, color="#334155", family="DM Sans, sans-serif"),
                                 xref="paper", yref="paper"),
                        ],
                    )

                    chart_col, legend_col = st.columns([2, 2])

                    with chart_col:
                        st.plotly_chart(fig, use_container_width=True, key="donut_combined")

                    with legend_col:
                        sel_cat   = st.session_state.get('dash_selected_cat')
                        sel_typ   = st.session_state.get('dash_selected_typ')
                        sel_color = st.session_state.get('dash_selected_color')

                        if sel_cat and sel_typ:
                            if sel_typ == "Ausgabe":
                                src_df = ausg_df
                            elif sel_typ == "Einnahme":
                                src_df = ein_df
                            else:
                                src_df = dep_df
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
                            TYP_CONFIG = {
                                "Einnahme": ("EINNAHMEN", "#2b961f", "+"),
                                "Ausgabe":  ("AUSGABEN",  "#ff5232", "−"),
                                "Depot":    ("DEPOT",     "#2510a3", ""),
                            }
                            available_types = list(dict.fromkeys(all_types))

                            if 'dash_legend_tab' not in st.session_state or \
                               st.session_state['dash_legend_tab'] not in available_types:
                                st.session_state['dash_legend_tab'] = available_types[0] if available_types else "Ausgabe"

                            active_tab = st.session_state['dash_legend_tab']

                            tab_cols = st.columns(len(available_types))
                            for i, typ in enumerate(available_types):
                                lbl, col_active, _ = TYP_CONFIG.get(typ, (typ.upper(), "#64748b", ""))
                                is_active = (typ == active_tab)
                                with tab_cols[i]:
                                    btn_style = "primary" if is_active else "secondary"
                                    if st.button(lbl, key=f"dash_tab_{typ}",
                                                 use_container_width=True, type=btn_style):
                                        st.session_state['dash_legend_tab'] = typ
                                        st.rerun()

                            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

                            lbl_active, color_active, sign_active = TYP_CONFIG.get(active_tab, (active_tab, "#64748b", ""))
                            for cat, val, color, typ in zip(all_cats, all_vals, all_colors, all_types):
                                if typ != active_tab:
                                    continue
                                pct     = val / total_sum * 100
                                btn_key = f"legend_btn_{cat}_{typ}"
                                col_legend, col_btn = st.columns([10, 1])
                                with col_legend:
                                    st.markdown(
                                        f"<div style='display:flex;align-items:center;"
                                        f"justify-content:space-between;"
                                        f"padding:7px 8px;border-radius:8px;"
                                        f"border:1px solid transparent;cursor:pointer;'>"
                                        f"<div style='display:flex;align-items:center;gap:10px;min-width:0;'>"
                                        f"<div style='width:7px;height:7px;border-radius:50%;"
                                        f"background:{color};flex-shrink:0;'></div>"
                                        f"<span style='font-family:DM Sans,sans-serif;color:#94a3b8;"
                                        f"font-size:13px;overflow:hidden;text-overflow:ellipsis;"
                                        f"white-space:nowrap;'>{cat}</span>"
                                        f"</div>"
                                        f"<div style='display:flex;align-items:center;gap:8px;flex-shrink:0;margin-left:8px;'>"
                                        f"<span style='font-family:DM Mono,monospace;color:{color};"
                                        f"font-weight:500;font-size:12px;'>{sign_active}{val:,.2f} €</span>"
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

        st.markdown(
            "<div style='margin-bottom:28px;'>"
            "<h1 style='font-family:DM Sans,sans-serif;font-size:28px;font-weight:600;"
            "color:#e2e8f0;margin:0 0 4px 0;letter-spacing:-0.5px;'>Neue Buchung</h1>"
            "<p style='font-family:DM Sans,sans-serif;color:#334155;font-size:14px;margin:0;'>"
            "Erfasse Einnahmen und Ausgaben</p>"
            "</div>",
            unsafe_allow_html=True
        )

        st.markdown(
            "<p style='font-family:DM Mono,monospace;color:#334155;font-size:10px;"
            "font-weight:500;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:10px;'>"
            "Typ</p>",
            unsafe_allow_html=True
        )
        ta, te, td, _ = st.columns([1, 1, 1, 2])
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
        with td:
            if st.button(
                "📦 Depot" + (" ✓" if t_type == "Depot" else ""),
                key="btn_depot", use_container_width=True,
                type="primary" if t_type == "Depot" else "secondary"
            ):
                st.session_state['t_type'] = "Depot"
                st.rerun()

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

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
                if t_type == "Depot":
                    betrag_save = t_amount
                elif t_type == "Einnahme":
                    betrag_save = t_amount
                else:
                    betrag_save = -t_amount
                new_row = pd.DataFrame([{
                    "user":      user_name,
                    "datum":     str(t_date),
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "typ":       t_type,
                    "kategorie": t_cat,
                    "betrag":    betrag_save,
                    "notiz":     t_note,
                }])
                df_old = conn.read(worksheet="transactions", ttl="5")
                if st.form_submit_button("Speichern", use_container_width=True):
                    new_row = pd.DataFrame([{ ... }]) # Deine Logik zum Erstellen der Zeile
                    df_old = conn.read(worksheet="transactions", ttl="600")
                    df_new = pd.concat([df_old, new_row], ignore_index=True)
                    conn.update(worksheet="transactions", data=df_new)
                    st.cache_data.clear()  # <-- Diese Zeile muss genau unter conn.update stehen
                    st.success("✅ Gespeichert!")
                    st.balloons()

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

        st.markdown(
            "<div style='height:8px'></div>"
            "<div style='font-family:DM Mono,monospace;color:#334155;font-size:10px;"
            "font-weight:500;letter-spacing:1.5px;text-transform:uppercase;"
            "margin:20px 0 16px 0;'>Meine Buchungen</div>",
            unsafe_allow_html=True
        )
        try:
            df_t = conn.read(worksheet="transactions", ttl="5")
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
                    def betrag_anzeige(row):
                        x = pd.to_numeric(row['betrag'], errors='coerce')
                        if row.get('typ') == 'Depot':
                            return f"📦 {abs(x):.2f} €"
                        if row.get('typ') == 'Spartopf':
                            return f"🪣 {abs(x):.2f} €" if x < 0 else f"🪣 +{abs(x):.2f} €"
                        return f"+{x:.2f} €" if x > 0 else f"{x:.2f} €"
                    user_df['betrag_anzeige'] = user_df.apply(betrag_anzeige, axis=1)
                    if 'timestamp' in user_df.columns:
                        user_df = user_df.sort_values('timestamp', ascending=False)
                    else:
                        user_df = user_df.sort_values('datum', ascending=False)

                    for orig_idx, row in user_df.iterrows():
                        notiz      = str(row.get('notiz', ''))
                        notiz      = '' if notiz.lower() == 'nan' else notiz
                        betrag_num = pd.to_numeric(row['betrag'], errors='coerce')
                        if row['typ'] == 'Einnahme':
                            farbe = '#4ade80'
                        elif row['typ'] == 'Depot':
                            farbe = '#38bdf8'
                        elif row['typ'] == 'Spartopf':
                            farbe = '#a78bfa'
                        else:
                            farbe = '#f87171'
                        zeit_label = format_timestamp(row.get('timestamp', ''), row.get('datum', ''))

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
                                        "Typ", ["Einnahme", "Ausgabe", "Depot"],
                                        index=["Einnahme", "Ausgabe", "Depot"].index(row['typ'])
                                              if row['typ'] in ["Einnahme", "Ausgabe", "Depot"]
                                              else 1
                                    )
                                    e_std_cats    = DEFAULT_CATS[e_typ]
                                    e_custom_cats = load_custom_cats(user_name, e_typ)
                                    e_all_cats    = e_std_cats + e_custom_cats
                                    curr_cat = row['kategorie']
                                    if curr_cat in e_all_cats:
                                        e_cat_idx = e_all_cats.index(curr_cat)
                                    else:
                                        e_cat_idx = 0
                                    e_cat = st.selectbox("Kategorie", e_all_cats, index=e_cat_idx)
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
                                    cancelled = st.form_submit_button("Abbrechen", use_container_width=True)

                                if saved:
                                    df_all = conn.read(worksheet="transactions", ttl="5")
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

    # ── Analysen ─────────────────────────────────────────────
    elif menu == "📂 Analysen":
        import plotly.graph_objects as go
        import calendar

        user_name = st.session_state['user_name']

        st.markdown(
            "<div style='margin-bottom:36px;margin-top:16px;'>"
            "<h1 style='font-family:DM Sans,sans-serif;font-size:40px;font-weight:700;"
            "color:#e2e8f0;margin:0 0 6px 0;letter-spacing:-1px;'>"
            "Analysen &amp; Trends 📊</h1>"
            "<p style='font-family:DM Sans,sans-serif;color:#475569;font-size:15px;margin:0;'>"
            "Kaufverhalten, Zeitraumübersicht &amp; Sparziele</p>"
            "</div>",
            unsafe_allow_html=True
        )

        try:
            df_raw = conn.read(worksheet="transactions", ttl="5")
        except Exception as e:
            st.warning(f"Verbindung wird hergestellt... ({e})")
            df_raw = pd.DataFrame()

        if df_raw.empty or 'user' not in df_raw.columns:
            st.info("Noch keine Buchungen vorhanden. Füge zuerst Transaktionen hinzu.")
        else:
            df_all = df_raw[df_raw['user'] == user_name].copy()
            if 'deleted' in df_all.columns:
                df_all = df_all[~df_all['deleted'].astype(str).str.strip().str.lower()
                                .isin(['true', '1', '1.0'])]
            df_all['datum_dt']   = pd.to_datetime(df_all['datum'], errors='coerce')
            df_all['betrag_num'] = pd.to_numeric(df_all['betrag'], errors='coerce')
            df_all = df_all.dropna(subset=['datum_dt'])

            if df_all.empty:
                st.info("Noch keine Buchungen vorhanden.")
            else:
                PALETTE_AUS = ["#ff0000","#ff5232","#ff7b5a","#ff9e81","#ffbfaa",
                               "#ffdfd4","#dc2626","#b91c1c","#991b1b","#7f1d1d"]
                PALETTE_EIN = ["#008000","#469536","#6eaa5e","#93bf85","#b7d5ac",
                               "#dbead5","#2d7a2d","#4a9e4a","#5cb85c","#80c780"]
                PALETTE_DEP = ["#0000ff","#1e0bd0","#2510a3","#241178","#1f104f",
                               "#19092e","#2563eb","#1d4ed8","#1e40af","#1e3a8a"]

                now   = datetime.datetime.now()
                today = now.date()

                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                # SECTION 1 — ZEITRAUM KREISDIAGRAMME
                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                st.markdown(
                    "<p style='font-family:DM Mono,monospace;color:#334155;font-size:10px;"
                    "font-weight:500;letter-spacing:1.5px;text-transform:uppercase;"
                    "margin-bottom:14px;'>Zeitraum</p>",
                    unsafe_allow_html=True
                )

                zeitraum = st.session_state['analysen_zeitraum']
                zt_col1, zt_col2, zt_col3, zt_rest = st.columns([1, 1, 1, 3])
                with zt_col1:
                    if st.button(
                        "Wöchentlich" + (" ✓" if zeitraum == "Wöchentlich" else ""),
                        key="zt_weekly", use_container_width=True,
                        type="primary" if zeitraum == "Wöchentlich" else "secondary"
                    ):
                        st.session_state['analysen_zeitraum'] = "Wöchentlich"
                        st.rerun()
                with zt_col2:
                    if st.button(
                        "Monatlich" + (" ✓" if zeitraum == "Monatlich" else ""),
                        key="zt_monthly", use_container_width=True,
                        type="primary" if zeitraum == "Monatlich" else "secondary"
                    ):
                        st.session_state['analysen_zeitraum'] = "Monatlich"
                        st.rerun()
                with zt_col3:
                    if st.button(
                        "Jährlich" + (" ✓" if zeitraum == "Jährlich" else ""),
                        key="zt_yearly", use_container_width=True,
                        type="primary" if zeitraum == "Jährlich" else "secondary"
                    ):
                        st.session_state['analysen_zeitraum'] = "Jährlich"
                        st.rerun()

                st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

                if zeitraum == "Wöchentlich":
                    week_start   = today - datetime.timedelta(days=today.weekday())
                    week_end     = week_start + datetime.timedelta(days=6)
                    period_mask  = (
                        (df_all['datum_dt'].dt.date >= week_start) &
                        (df_all['datum_dt'].dt.date <= week_end)
                    )
                    period_label = f"{week_start.strftime('%d.%m.')} – {week_end.strftime('%d.%m.%Y')}"
                elif zeitraum == "Monatlich":
                    period_mask  = (
                        (df_all['datum_dt'].dt.year  == now.year) &
                        (df_all['datum_dt'].dt.month == now.month)
                    )
                    period_label = now.strftime("%B %Y")
                else:
                    period_mask  = df_all['datum_dt'].dt.year == now.year
                    period_label = str(now.year)

                period_df = df_all[period_mask].copy()

                st.markdown(
                    f"<div style='font-family:DM Mono,monospace;color:#475569;"
                    f"font-size:11px;letter-spacing:1px;margin-bottom:18px;'>"
                    f"{period_label}</div>",
                    unsafe_allow_html=True
                )

                def make_donut(grp, palette, label, sign, center_color, key_suffix):
                    if grp.empty:
                        return
                    cats   = grp['kategorie'].tolist()
                    vals   = grp['betrag_num'].abs().tolist()
                    colors = [palette[i % len(palette)] for i in range(len(cats))]
                    total  = sum(vals) if sum(vals) > 0 else 1
                    center_str = f"{sign}{total:,.2f} €"

                    fig = go.Figure(go.Pie(
                        labels=cats, values=vals, hole=0.60,
                        marker=dict(colors=colors, line=dict(color="rgba(5,10,20,0.9)", width=2)),
                        textinfo="none", hoverinfo="none",
                        direction="clockwise", sort=False, rotation=90,
                    ))
                    fig.update_traces(hovertemplate=None)
                    fig.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                        showlegend=False, margin=dict(t=10, b=10, l=10, r=10),
                        height=240, autosize=True, dragmode=False,
                        annotations=[dict(
                            text=f"<b>{center_str}</b>", x=0.5, y=0.5, showarrow=False,
                            font=dict(size=15, color=center_color, family="DM Sans, sans-serif"),
                            xref="paper", yref="paper",
                        )],
                    )

                    rows = ""
                    for cat, val, col in zip(cats, vals, colors):
                        pct = val / total * 100
                        rows += (
                            f"<div style='display:flex;align-items:center;"
                            f"justify-content:space-between;padding:5px 0;"
                            f"border-bottom:1px solid rgba(255,255,255,0.04);'>"
                            f"<div style='display:flex;align-items:center;gap:8px;min-width:0;flex:1;'>"
                            f"<div style='width:7px;height:7px;border-radius:50%;"
                            f"background:{col};flex-shrink:0;'></div>"
                            f"<span style='font-family:DM Sans,sans-serif;color:#94a3b8;"
                            f"font-size:12px;overflow:hidden;text-overflow:ellipsis;"
                            f"white-space:nowrap;'>{cat}</span>"
                            f"</div>"
                            f"<div style='display:flex;align-items:center;gap:6px;"
                            f"flex-shrink:0;margin-left:10px;'>"
                            f"<span style='font-family:DM Mono,monospace;color:{col};"
                            f"font-size:11px;font-weight:500;white-space:nowrap;'>"
                            f"{sign}{val:,.2f} €</span>"
                            f"<span style='font-family:DM Mono,monospace;color:#334155;"
                            f"font-size:11px;min-width:26px;text-align:right;'>"
                            f"{pct:.0f}%</span>"
                            f"</div></div>"
                        )

                    st.markdown(
                        f"<div style='background:linear-gradient(145deg,rgba(14,22,38,0.9),"
                        f"rgba(10,16,30,0.95));border:1px solid rgba(148,163,184,0.08);"
                        f"border-radius:16px;padding:18px 22px;margin-bottom:16px;'>"
                        f"<div style='font-family:DM Mono,monospace;font-size:9px;"
                        f"color:#334155;letter-spacing:1.5px;text-transform:uppercase;"
                        f"margin-bottom:14px;'>{label}</div>",
                        unsafe_allow_html=True
                    )
                    pie_col, leg_col = st.columns([1, 1])
                    with pie_col:
                        st.plotly_chart(
                            fig, use_container_width=True,
                            key=f"donut_{key_suffix}_{zeitraum}",
                            config={"displayModeBar": False, "staticPlot": True}
                        )
                    with leg_col:
                        st.markdown(f"<div style='padding:4px 0;'>{rows}</div>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

                if period_df.empty:
                    st.markdown(
                        f"<div style='text-align:center;padding:40px 20px;color:#334155;"
                        f"font-family:DM Sans,sans-serif;font-size:15px;'>"
                        f"Keine Buchungen im gewählten Zeitraum.</div>",
                        unsafe_allow_html=True
                    )
                else:
                    aus_p = period_df[period_df['typ'] == 'Ausgabe'].copy()
                    aus_p['betrag_num'] = aus_p['betrag_num'].abs()
                    aus_grp_p = aus_p.groupby('kategorie')['betrag_num'].sum().reset_index().sort_values('betrag_num', ascending=False)
                    make_donut(aus_grp_p, PALETTE_AUS, "Ausgaben", "−", "#f87171", "aus")

                    ein_p = period_df[period_df['typ'] == 'Einnahme'].copy()
                    ein_grp_p = ein_p.groupby('kategorie')['betrag_num'].sum().reset_index().sort_values('betrag_num', ascending=False)
                    make_donut(ein_grp_p, PALETTE_EIN, "Einnahmen", "+", "#4ade80", "ein")

                    dep_p = period_df[period_df['typ'] == 'Depot'].copy()
                    dep_p['betrag_num'] = dep_p['betrag_num'].abs()
                    dep_grp_p = dep_p.groupby('kategorie')['betrag_num'].sum().reset_index().sort_values('betrag_num', ascending=False)
                    make_donut(dep_grp_p, PALETTE_DEP, "Depot", "", "#38bdf8", "dep")

                st.markdown("<hr>", unsafe_allow_html=True)

                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                # SECTION 2 — KAUFVERHALTEN
                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                st.markdown(
                    "<p style='font-family:DM Mono,monospace;color:#334155;font-size:10px;"
                    "font-weight:500;letter-spacing:1.5px;text-transform:uppercase;"
                    "margin-bottom:14px;'>Kaufverhalten</p>",
                    unsafe_allow_html=True
                )

                kv_col_l, kv_col_r = st.columns(2)

                with kv_col_l:
                    aus_all = df_all[df_all['typ'] == 'Ausgabe'].copy()
                    aus_all['betrag_num'] = aus_all['betrag_num'].abs()
                    kat_grp = (aus_all.groupby('kategorie')['betrag_num']
                               .sum().reset_index()
                               .sort_values('betrag_num', ascending=True)
                               .tail(8))

                    if not kat_grp.empty:
                        REDS = ['#7f1d1d','#991b1b','#b91c1c','#dc2626',
                                '#ef4444','#f87171','#fca5a5','#fecaca']
                        colors_bar = REDS[:len(kat_grp)]

                        fig_kat = go.Figure(go.Bar(
                            x=kat_grp['betrag_num'],
                            y=kat_grp['kategorie'],
                            orientation='h',
                            marker=dict(color=colors_bar, cornerradius=6),
                            text=[f"{v:,.0f} €" for v in kat_grp['betrag_num']],
                            textposition='outside',
                            textfont=dict(size=11, color='#64748b', family='DM Mono, monospace'),
                            hovertemplate=None,
                        ))
                        fig_kat.update_traces(hovertemplate=None)
                        fig_kat.update_layout(
                            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                            height=280, margin=dict(t=0, b=0, l=0, r=60), dragmode=False,
                            xaxis=dict(showgrid=False, showticklabels=False, showline=False, fixedrange=True),
                            yaxis=dict(tickfont=dict(size=12, color='#94a3b8', family='DM Sans, sans-serif'),
                                       showgrid=False, showline=False, fixedrange=True, automargin=True),
                        )
                        st.markdown(
                            "<p style='font-family:DM Sans,sans-serif;color:#475569;"
                            "font-size:13px;margin-bottom:8px;'>Top Ausgabe-Kategorien (gesamt)</p>",
                            unsafe_allow_html=True
                        )
                        st.plotly_chart(fig_kat, use_container_width=True, key="kat_chart",
                                        config={"displayModeBar": False, "staticPlot": True})
                    else:
                        st.info("Keine Ausgaben vorhanden.")

                with kv_col_r:
                    aus_all2 = df_all[df_all['typ'] == 'Ausgabe'].copy()
                    aus_all2['betrag_num'] = aus_all2['betrag_num'].abs()
                    aus_all2['wochentag']  = aus_all2['datum_dt'].dt.day_name()

                    wt_order = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
                    wt_de    = {'Monday':'Mo','Tuesday':'Di','Wednesday':'Mi',
                                'Thursday':'Do','Friday':'Fr','Saturday':'Sa','Sunday':'So'}

                    if not aus_all2.empty:
                        heat = (aus_all2.groupby('wochentag')['betrag_num']
                                .mean().reindex(wt_order).fillna(0))
                        heat_labels = [wt_de.get(d, d) for d in heat.index]

                        fig_heat = go.Figure(go.Bar(
                            x=heat_labels, y=heat.values,
                            marker=dict(
                                color=heat.values,
                                colorscale=[[0, '#1a0505'], [0.5, '#dc2626'], [1, '#ff5232']],
                                showscale=False, cornerradius=6,
                            ),
                            text=[f"{v:,.0f} €" if v > 0 else "" for v in heat.values],
                            textposition='inside', insidetextanchor='middle',
                            textfont=dict(size=10, color='rgba(255,255,255,0.7)', family='DM Mono, monospace'),
                            hovertemplate=None,
                        ))
                        fig_heat.update_traces(hovertemplate=None)
                        fig_heat.update_layout(
                            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                            height=280, margin=dict(t=0, b=0, l=0, r=0), dragmode=False,
                            xaxis=dict(tickfont=dict(size=13, color='#94a3b8', family='DM Sans, sans-serif'),
                                       showgrid=False, showline=False, fixedrange=True),
                            yaxis=dict(showgrid=False, showticklabels=False, showline=False, fixedrange=True),
                        )
                        st.markdown(
                            "<p style='font-family:DM Sans,sans-serif;color:#475569;"
                            "font-size:13px;margin-bottom:8px;'>Ø Ausgaben nach Wochentag</p>",
                            unsafe_allow_html=True
                        )
                        st.plotly_chart(fig_heat, use_container_width=True, key="heat_chart",
                                        config={"displayModeBar": False, "staticPlot": True})

                st.markdown("<hr>", unsafe_allow_html=True)

                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                # NEU: SECTION 2b — KALENDER-HEATMAP
                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                st.markdown(
                    "<p style='font-family:DM Mono,monospace;color:#334155;font-size:10px;"
                    "font-weight:500;letter-spacing:1.5px;text-transform:uppercase;"
                    "margin-bottom:14px;'>Kalender-Heatmap</p>",
                    unsafe_allow_html=True
                )

                # Monatsselektor für Heatmap
                if 'heatmap_month_offset' not in st.session_state:
                    st.session_state['heatmap_month_offset'] = 0
                hm_offset = st.session_state['heatmap_month_offset']
                hm_m_total = now.year * 12 + (now.month - 1) + hm_offset
                hm_year, hm_month_idx = divmod(hm_m_total, 12)
                hm_month = hm_month_idx + 1
                hm_label = datetime.date(hm_year, hm_month, 1).strftime("%B %Y")

                hn1, hn2, hn3 = st.columns([1, 5, 1])
                with hn1:
                    if st.button("‹", key="hm_prev", use_container_width=True):
                        st.session_state['heatmap_month_offset'] -= 1
                        st.rerun()
                with hn2:
                    st.markdown(
                        f"<div style='text-align:center;font-family:DM Sans,sans-serif;"
                        f"font-size:13px;color:#64748b;padding:6px 0;'>{hm_label}</div>",
                        unsafe_allow_html=True
                    )
                with hn3:
                    if st.button("›", key="hm_next", use_container_width=True,
                                 disabled=(hm_offset >= 0)):
                        st.session_state['heatmap_month_offset'] += 1
                        st.rerun()

                # Ausgaben pro Tag berechnen
                hm_df = df_all[
                    (df_all['datum_dt'].dt.year  == hm_year) &
                    (df_all['datum_dt'].dt.month == hm_month) &
                    (df_all['typ'] == 'Ausgabe')
                ].copy()
                hm_df['betrag_num'] = hm_df['betrag_num'].abs()
                tages_summen = hm_df.groupby(hm_df['datum_dt'].dt.day)['betrag_num'].sum()

                max_val = tages_summen.max() if not tages_summen.empty else 1
                max_val = max(max_val, 1)

                # Kalender aufbauen
                days_in_month = calendar.monthrange(hm_year, hm_month)[1]
                first_weekday = calendar.monthrange(hm_year, hm_month)[0]  # 0=Mo

                wt_labels = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So']
                header_html = "".join([
                    f"<div style='width:42px;text-align:center;font-family:DM Mono,monospace;"
                    f"font-size:10px;color:#334155;letter-spacing:0.5px;padding-bottom:4px;'>{d}</div>"
                    for d in wt_labels
                ])

                cal_cells = ""
                # Leere Zellen vor dem 1.
                for _ in range(first_weekday):
                    cal_cells += "<div style='width:42px;height:42px;'></div>"

                for day in range(1, days_in_month + 1):
                    val = tages_summen.get(day, 0)
                    intensity = val / max_val if max_val > 0 else 0
                    is_today = (hm_year == now.year and hm_month == now.month and day == now.day)

                    # Farbe interpolieren: dunkel → rot
                    if val == 0:
                        bg = "rgba(15,23,42,0.6)"
                        text_color = "#1e293b"
                    else:
                        r = int(20 + intensity * 235)
                        g = int(5 + (1 - intensity) * 30)
                        b = int(5 + (1 - intensity) * 10)
                        bg = f"rgba({r},{g},{b},0.85)"
                        text_color = "#ffffff" if intensity > 0.3 else "#94a3b8"

                    border = "2px solid #38bdf8" if is_today else "1px solid rgba(148,163,184,0.06)"
                    title_str = f"{val:.0f} €" if val > 0 else ""
                    tooltip = f"title='{day}. {hm_label}: {val:.2f} €'"

                    cal_cells += (
                        f"<div {tooltip} style='width:42px;height:42px;border-radius:8px;"
                        f"background:{bg};border:{border};display:flex;flex-direction:column;"
                        f"align-items:center;justify-content:center;cursor:default;'>"
                        f"<span style='font-family:DM Mono,monospace;font-size:11px;"
                        f"color:#334155;line-height:1;'>{day}</span>"
                        + (f"<span style='font-family:DM Mono,monospace;font-size:8px;"
                           f"color:{text_color};line-height:1;margin-top:2px;'>{val:.0f}€</span>"
                           if val > 0 else "")
                        + f"</div>"
                    )

                st.markdown(
                    f"<div style='background:linear-gradient(145deg,rgba(14,22,38,0.9),"
                    f"rgba(10,16,30,0.95));border:1px solid rgba(148,163,184,0.08);"
                    f"border-radius:16px;padding:20px 22px;'>"
                    f"<div style='font-family:DM Sans,sans-serif;color:#475569;font-size:13px;"
                    f"margin-bottom:14px;'>Ausgaben pro Tag — dunklere Felder = höhere Ausgaben</div>"
                    f"<div style='display:flex;gap:6px;margin-bottom:6px;flex-wrap:nowrap;'>"
                    f"{header_html}</div>"
                    f"<div style='display:flex;flex-wrap:wrap;gap:6px;'>"
                    f"{cal_cells}</div>"
                    f"<div style='display:flex;align-items:center;gap:8px;margin-top:14px;'>"
                    f"<span style='font-family:DM Mono,monospace;font-size:10px;color:#334155;'>0 €</span>"
                    f"<div style='height:6px;flex:1;max-width:120px;border-radius:3px;"
                    f"background:linear-gradient(to right,rgba(15,23,42,0.6),#ff0000);'></div>"
                    f"<span style='font-family:DM Mono,monospace;font-size:10px;color:#64748b;'>"
                    f"{max_val:.0f} €</span>"
                    f"</div>"
                    f"</div>",
                    unsafe_allow_html=True
                )

                st.markdown("<hr>", unsafe_allow_html=True)

                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                # NEU: SECTION 3 — END-OF-MONTH FORECAST
                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                st.markdown(
                    "<p style='font-family:DM Mono,monospace;color:#334155;font-size:10px;"
                    "font-weight:500;letter-spacing:1.5px;text-transform:uppercase;"
                    "margin-bottom:14px;'>Monatsende-Prognose</p>",
                    unsafe_allow_html=True
                )

                curr_month_df = df_all[
                    (df_all['datum_dt'].dt.year  == now.year) &
                    (df_all['datum_dt'].dt.month == now.month)
                ].copy()

                today_day   = now.day
                days_in_cur = calendar.monthrange(now.year, now.month)[1]
                days_left   = days_in_cur - today_day

                curr_ein = curr_month_df[curr_month_df['typ'] == 'Einnahme']['betrag_num'].sum()
                curr_aus = curr_month_df[curr_month_df['typ'] == 'Ausgabe']['betrag_num'].abs().sum()
                curr_dep = curr_month_df[curr_month_df['typ'] == 'Depot']['betrag_num'].abs().sum()
                # Spartopf-Netto (negativ = eingezahlt, positiv = ausgezahlt)
                curr_spartopf_netto = curr_month_df[curr_month_df['typ'] == 'Spartopf']['betrag_num'].sum()
                curr_spartopf_einzahl = abs(curr_month_df[
                    (curr_month_df['typ'] == 'Spartopf') & (curr_month_df['betrag_num'] < 0)
                ]['betrag_num'].sum())

                # Tägliche Ausgaben-Rate hochrechnen (nur echte Ausgaben, nicht Spartopf)
                daily_rate = curr_aus / today_day if today_day > 0 else 0
                forecast_aus_total = daily_rate * days_in_cur
                forecast_remaining = daily_rate * days_left
                forecast_bank = curr_ein - forecast_aus_total - curr_dep + curr_spartopf_netto
                current_bank  = curr_ein - curr_aus - curr_dep + curr_spartopf_netto

                fc_col_l, fc_col_r = st.columns([1, 1])

                with fc_col_l:
                    fc_color = "#4ade80" if forecast_bank >= 0 else "#f87171"
                    fc_str   = f"{forecast_bank:,.2f} €" if forecast_bank >= 0 else f"-{abs(forecast_bank):,.2f} €"

                    # Fortschrittsbalken: Monat-Verlauf
                    month_pct = today_day / days_in_cur * 100

                    st.markdown(
                        f"<div style='background:linear-gradient(145deg,rgba(14,22,38,0.9),"
                        f"rgba(10,16,30,0.95));border:1px solid rgba(148,163,184,0.08);"
                        f"border-radius:16px;padding:20px 22px;'>"
                        f"<div style='font-family:DM Mono,monospace;font-size:9px;color:#334155;"
                        f"letter-spacing:1.5px;text-transform:uppercase;margin-bottom:12px;'>"
                        f"Prognose für {now.strftime('%B %Y')}</div>"
                        # Monats-Fortschrittsbalken
                        f"<div style='display:flex;justify-content:space-between;margin-bottom:4px;'>"
                        f"<span style='font-family:DM Sans,sans-serif;color:#475569;font-size:12px;'>Monatsverlauf</span>"
                        f"<span style='font-family:DM Mono,monospace;color:#64748b;font-size:12px;'>Tag {today_day}/{days_in_cur}</span>"
                        f"</div>"
                        f"<div style='background:rgba(30,41,59,0.8);border-radius:99px;height:5px;margin-bottom:16px;'>"
                        f"<div style='width:{month_pct:.0f}%;height:100%;background:#475569;border-radius:99px;'></div>"
                        f"</div>"
                        # Kennzahlen
                        f"<div style='display:flex;flex-direction:column;gap:8px;'>"
                        f"<div style='display:flex;justify-content:space-between;'>"
                        f"<span style='font-family:DM Sans,sans-serif;color:#475569;font-size:12px;'>Ø Tagesausgaben</span>"
                        f"<span style='font-family:DM Mono,monospace;color:#f87171;font-size:12px;'>{daily_rate:,.2f} €/Tag</span>"
                        f"</div>"
                        f"<div style='display:flex;justify-content:space-between;'>"
                        f"<span style='font-family:DM Sans,sans-serif;color:#475569;font-size:12px;'>Noch {days_left} Tage → ca.</span>"
                        f"<span style='font-family:DM Mono,monospace;color:#f87171;font-size:12px;'>-{forecast_remaining:,.2f} €</span>"
                        f"</div>"
                        f"<div style='border-top:1px solid rgba(148,163,184,0.08);padding-top:10px;"
                        f"display:flex;justify-content:space-between;align-items:baseline;'>"
                        f"<span style='font-family:DM Sans,sans-serif;color:#64748b;font-size:13px;font-weight:500;'>Prognose Monatsende</span>"
                        f"<span style='font-family:DM Mono,monospace;color:{fc_color};font-size:18px;font-weight:600;'>{fc_str}</span>"
                        f"</div></div></div>",
                        unsafe_allow_html=True
                    )

                with fc_col_r:
                    # Visueller Verlauf: Ist vs. Prognose
                    curr_color = "#4ade80" if current_bank >= 0 else "#f87171"
                    curr_str   = f"{current_bank:,.2f} €" if current_bank >= 0 else f"-{abs(current_bank):,.2f} €"

                    # Sparziel Vergleich
                    goal_fc = load_goal(user_name)
                    if goal_fc > 0:
                        diff_to_goal = forecast_bank - goal_fc
                        on_track = forecast_bank >= goal_fc
                        goal_html = (
                            f"<div style='margin-top:12px;padding:10px 14px;"
                            f"border-radius:10px;background:{'rgba(74,222,128,0.06)' if on_track else 'rgba(248,113,113,0.06)'};"
                            f"border:1px solid {'rgba(74,222,128,0.15)' if on_track else 'rgba(248,113,113,0.15)'};"
                            f"display:flex;align-items:center;gap:10px;'>"
                            f"<span style='font-size:16px;'>{'✅' if on_track else '⚠️'}</span>"
                            f"<div>"
                            f"<div style='font-family:DM Sans,sans-serif;color:{'#4ade80' if on_track else '#fca5a5'};"
                            f"font-size:13px;font-weight:500;'>{'Sparziel erreichbar!' if on_track else 'Sparziel in Gefahr'}</div>"
                            f"<div style='font-family:DM Mono,monospace;color:#475569;font-size:11px;'>"
                            f"{'Puffer: +' if diff_to_goal >= 0 else 'Fehlbetrag: '}{abs(diff_to_goal):,.2f} € vs. Ziel {goal_fc:,.2f} €"
                            f"</div></div></div>"
                        )
                    else:
                        goal_html = ""

                    st.markdown(
                        f"<div style='background:linear-gradient(145deg,rgba(14,22,38,0.9),"
                        f"rgba(10,16,30,0.95));border:1px solid rgba(148,163,184,0.08);"
                        f"border-radius:16px;padding:20px 22px;'>"
                        f"<div style='font-family:DM Mono,monospace;font-size:9px;color:#334155;"
                        f"letter-spacing:1.5px;text-transform:uppercase;margin-bottom:16px;'>Jetzt vs. Prognose</div>"
                        f"<div style='display:flex;gap:12px;'>"
                        f"<div style='flex:1;background:rgba(10,16,30,0.5);border-radius:12px;"
                        f"padding:14px;border:1px solid rgba(148,163,184,0.06);text-align:center;'>"
                        f"<div style='font-family:DM Mono,monospace;font-size:9px;color:#334155;"
                        f"letter-spacing:1px;text-transform:uppercase;margin-bottom:6px;'>Aktuell</div>"
                        f"<div style='font-family:DM Sans,sans-serif;color:{curr_color};"
                        f"font-size:20px;font-weight:600;'>{curr_str}</div>"
                        f"<div style='font-family:DM Mono,monospace;color:#334155;font-size:10px;"
                        f"margin-top:4px;'>Tag {today_day}</div>"
                        f"</div>"
                        f"<div style='display:flex;align-items:center;color:#334155;font-size:18px;'>→</div>"
                        f"<div style='flex:1;background:rgba(10,16,30,0.5);border-radius:12px;"
                        f"padding:14px;border:1px solid rgba(148,163,184,0.06);text-align:center;'>"
                        f"<div style='font-family:DM Mono,monospace;font-size:9px;color:#334155;"
                        f"letter-spacing:1px;text-transform:uppercase;margin-bottom:6px;'>Prognose</div>"
                        f"<div style='font-family:DM Sans,sans-serif;color:{fc_color};"
                        f"font-size:20px;font-weight:600;'>{fc_str}</div>"
                        f"<div style='font-family:DM Mono,monospace;color:#334155;font-size:10px;"
                        f"margin-top:4px;'>Tag {days_in_cur}</div>"
                        f"</div></div>"
                        f"{goal_html}"
                        f"</div>",
                        unsafe_allow_html=True
                    )

                st.markdown("<hr>", unsafe_allow_html=True)

                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                # NEU: SECTION 4 — SPAR-POTENZIAL
                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                st.markdown(
                    "<p style='font-family:DM Mono,monospace;color:#334155;font-size:10px;"
                    "font-weight:500;letter-spacing:1.5px;text-transform:uppercase;"
                    "margin-bottom:14px;'>Spar-Potenzial</p>",
                    unsafe_allow_html=True
                )

                # Durchschnitt der letzten 3 Monate pro Kategorie berechnen (exkl. aktueller Monat)
                hist_df = df_all[
                    ~(
                        (df_all['datum_dt'].dt.year  == now.year) &
                        (df_all['datum_dt'].dt.month == now.month)
                    ) &
                    (df_all['typ'] == 'Ausgabe')
                ].copy()
                hist_df['betrag_num'] = hist_df['betrag_num'].abs()

                # Letzten 3 Monate
                three_months_ago = now - datetime.timedelta(days=90)
                hist_df = hist_df[hist_df['datum_dt'] >= three_months_ago]

                if not hist_df.empty and not curr_month_df.empty:
                    # Anzahl Monate in hist (mind. 1)
                    hist_months = hist_df['datum_dt'].dt.to_period('M').nunique()
                    hist_months = max(hist_months, 1)

                    avg_per_kat = hist_df.groupby('kategorie')['betrag_num'].sum() / hist_months

                    curr_aus_df = curr_month_df[curr_month_df['typ'] == 'Ausgabe'].copy()
                    curr_aus_df['betrag_num'] = curr_aus_df['betrag_num'].abs()
                    curr_per_kat = curr_aus_df.groupby('kategorie')['betrag_num'].sum()

                    potenzial_rows = []
                    for kat in curr_per_kat.index:
                        curr_val = curr_per_kat.get(kat, 0)
                        avg_val  = avg_per_kat.get(kat, 0)
                        if avg_val > 0 and curr_val > avg_val * 1.1:  # Mindestens 10% mehr
                            diff_pct  = (curr_val - avg_val) / avg_val * 100
                            diff_eur  = curr_val - avg_val
                            potenzial_rows.append({
                                'kategorie': kat,
                                'aktuell':   curr_val,
                                'durchschn': avg_val,
                                'diff_pct':  diff_pct,
                                'diff_eur':  diff_eur,
                            })

                    if potenzial_rows:
                        potenzial_rows.sort(key=lambda x: x['diff_eur'], reverse=True)
                        total_potenzial = sum(r['diff_eur'] for r in potenzial_rows)

                        st.markdown(
                            f"<div style='background:linear-gradient(145deg,rgba(14,22,38,0.9),"
                            f"rgba(10,16,30,0.95));border:1px solid rgba(148,163,184,0.08);"
                            f"border-radius:16px;padding:20px 22px;margin-bottom:12px;'>"
                            f"<div style='font-family:DM Sans,sans-serif;color:#94a3b8;"
                            f"font-size:14px;margin-bottom:16px;'>"
                            f"Diesen Monat hast du in <b style='color:#e2e8f0;'>{len(potenzial_rows)} {'Kategorie' if len(potenzial_rows)==1 else 'Kategorien'}</b> "
                            f"mehr ausgegeben als im Durchschnitt. "
                            f"Spar-Potenzial: <span style='color:#4ade80;font-weight:600;'>{total_potenzial:,.2f} €</span></div>",
                            unsafe_allow_html=True
                        )
                        for r in potenzial_rows:
                            bar_pct = min(r['diff_pct'], 200) / 200 * 100
                            st.markdown(
                                f"<div style='margin-bottom:14px;'>"
                                f"<div style='display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px;'>"
                                f"<span style='font-family:DM Sans,sans-serif;color:#94a3b8;font-size:13px;'>{r['kategorie']}</span>"
                                f"<div style='display:flex;gap:14px;align-items:baseline;'>"
                                f"<span style='font-family:DM Mono,monospace;color:#f87171;font-size:12px;'>"
                                f"{r['aktuell']:,.2f} €</span>"
                                f"<span style='font-family:DM Mono,monospace;color:#334155;font-size:11px;'>"
                                f"Ø {r['durchschn']:,.2f} €</span>"
                                f"<span style='font-family:DM Mono,monospace;color:#facc15;"
                                f"font-size:12px;font-weight:600;'>+{r['diff_pct']:.0f}%</span>"
                                f"</div></div>"
                                f"<div style='background:rgba(30,41,59,0.6);border-radius:99px;height:4px;'>"
                                f"<div style='width:{bar_pct:.0f}%;height:100%;border-radius:99px;"
                                f"background:linear-gradient(to right,#facc15,#f87171);'></div></div>"
                                f"<div style='font-family:DM Sans,sans-serif;color:#475569;font-size:12px;margin-top:4px;'>"
                                f"Da könntest du ca. <span style='color:#4ade80;font-weight:500;'>{r['diff_eur']:,.2f} €</span> sparen</div>"
                                f"</div>",
                                unsafe_allow_html=True
                            )
                        st.markdown("</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(
                            "<div style='background:linear-gradient(145deg,rgba(14,22,38,0.9),"
                            "rgba(10,16,30,0.95));border:1px solid rgba(74,222,128,0.12);"
                            "border-left:3px solid #4ade80;border-radius:16px;padding:18px 22px;'>"
                            "<div style='font-family:DM Sans,sans-serif;color:#4ade80;"
                            "font-size:14px;font-weight:500;'>🎉 Alles im grünen Bereich!</div>"
                            "<div style='font-family:DM Sans,sans-serif;color:#475569;"
                            "font-size:13px;margin-top:6px;'>Deine Ausgaben liegen diesen Monat "
                            "im normalen Rahmen.</div>"
                            "</div>",
                            unsafe_allow_html=True
                        )
                else:
                    st.markdown(
                        "<div style='color:#334155;font-family:DM Sans,sans-serif;font-size:14px;"
                        "padding:16px;'>Zu wenig Daten für Vergleich. Buche mehrere Monate, "
                        "um Spar-Potenziale zu sehen.</div>",
                        unsafe_allow_html=True
                    )

                st.markdown("<hr>", unsafe_allow_html=True)

                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                # SECTION 5 — SPARZIEL (unverändert)
                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                st.markdown(
                    "<p style='font-family:DM Mono,monospace;color:#334155;font-size:10px;"
                    "font-weight:500;letter-spacing:1.5px;text-transform:uppercase;"
                    "margin-bottom:14px;'>Sparziel</p>",
                    unsafe_allow_html=True
                )

                current_goal = load_goal(user_name)

                df_month = df_all[
                    (df_all['datum_dt'].dt.year  == now.year) &
                    (df_all['datum_dt'].dt.month == now.month)
                ].copy()
                df_month['betrag_num'] = pd.to_numeric(df_month['betrag'], errors='coerce')

                monat_ein = df_month[df_month['typ'] == 'Einnahme']['betrag_num'].sum()
                monat_aus = df_month[df_month['typ'] == 'Ausgabe']['betrag_num'].abs().sum()
                monat_dep = df_month[df_month['typ'] == 'Depot']['betrag_num'].abs().sum()
                # Spartopf-Einzahlungen zählen als "gespartes Geld" (nicht als Ausgabe)
                monat_spartopf_einzahl = abs(df_month[
                    (df_month['typ'] == 'Spartopf') & (df_month['betrag_num'] < 0)
                ]['betrag_num'].sum())
                monat_spartopf_netto = df_month[df_month['typ'] == 'Spartopf']['betrag_num'].sum()
                # Verfügbares Geld auf dem Konto (Spartopf geht weg vom Konto)
                bank_aktuell = monat_ein - monat_aus - monat_dep + monat_spartopf_netto
                # "Effektiv gespart" = Bankkonto + was in Töpfe geflossen ist (Geld ist noch da)
                akt_spar = bank_aktuell + monat_spartopf_einzahl

                sg_col_l, sg_col_r = st.columns([1, 1])

                with sg_col_l:
                    with st.form("sparziel_form"):
                        goal_input = st.number_input(
                            "Monatliches Sparziel (€)", min_value=0.0,
                            value=float(current_goal), step=50.0, format="%.2f",
                            help="Wie viel möchtest du pro Monat zurücklegen?"
                        )
                        if st.form_submit_button("Sparziel speichern",
                                                  use_container_width=True, type="primary"):
                            save_goal(user_name, goal_input)
                            st.success("✅ Sparziel gespeichert!")
                            st.rerun()

                    monat_name = now.strftime("%B %Y")
                    spar_color = '#4ade80' if akt_spar >= 0 else '#f87171'
                    spar_str   = f"{akt_spar:,.2f} €" if akt_spar >= 0 else f"-{abs(akt_spar):,.2f} €"
                    bank_str_small = f"{bank_aktuell:,.2f} €" if bank_aktuell >= 0 else f"-{abs(bank_aktuell):,.2f} €"
                    st.markdown(
                        f"<div style='background:linear-gradient(145deg,rgba(14,22,38,0.8),"
                        f"rgba(10,16,30,0.9));border:1px solid rgba(148,163,184,0.06);"
                        f"border-radius:12px;padding:16px 18px;margin-top:10px;'>"
                        f"<div style='font-family:DM Mono,monospace;font-size:9px;color:#334155;"
                        f"letter-spacing:1.5px;text-transform:uppercase;margin-bottom:8px;'>"
                        f"{monat_name}</div>"
                        f"<div style='display:flex;justify-content:space-between;'>"
                        f"<div style='font-family:DM Sans,sans-serif;color:#475569;font-size:12px;'>Einnahmen</div>"
                        f"<div style='font-family:DM Mono,monospace;color:#4ade80;font-size:12px;'>+{monat_ein:,.2f} €</div>"
                        f"</div>"
                        f"<div style='display:flex;justify-content:space-between;'>"
                        f"<div style='font-family:DM Sans,sans-serif;color:#475569;font-size:12px;'>Ausgaben</div>"
                        f"<div style='font-family:DM Mono,monospace;color:#f87171;font-size:12px;'>-{monat_aus:,.2f} €</div>"
                        f"</div>"
                        + (
                            f"<div style='display:flex;justify-content:space-between;'>"
                            f"<div style='font-family:DM Sans,sans-serif;color:#475569;font-size:12px;'>Depot</div>"
                            f"<div style='font-family:DM Mono,monospace;color:#38bdf8;font-size:12px;'>-{monat_dep:,.2f} €</div>"
                            f"</div>" if monat_dep > 0 else ""
                        )
                        + (
                            f"<div style='display:flex;justify-content:space-between;'>"
                            f"<div style='font-family:DM Sans,sans-serif;color:#475569;font-size:12px;'>Spartöpfe</div>"
                            f"<div style='font-family:DM Mono,monospace;color:#a78bfa;font-size:12px;'>🪣 {monat_spartopf_einzahl:,.2f} €</div>"
                            f"</div>" if monat_spartopf_einzahl > 0 else ""
                        )
                        + f"<div style='border-top:1px solid rgba(148,163,184,0.08);margin-top:8px;padding-top:8px;"
                        f"display:flex;justify-content:space-between;'>"
                        f"<div style='font-family:DM Sans,sans-serif;color:#64748b;font-size:12px;font-weight:500;'>Gespart (inkl. Töpfe)</div>"
                        f"<div style='font-family:DM Mono,monospace;color:{spar_color};font-size:13px;font-weight:600;'>{spar_str}</div>"
                        f"</div></div>",
                        unsafe_allow_html=True
                    )

                with sg_col_r:
                    goal = current_goal
                    if goal > 0:
                        fehlbetrag  = goal - akt_spar
                        erreicht    = akt_spar >= goal
                        pct         = min(akt_spar / goal * 100, 100) if goal > 0 else 0
                        pct_display = max(0, pct)
                        bar_color   = '#4ade80' if erreicht else ('#facc15' if pct >= 60 else '#f87171')
                        spar_color2 = '#4ade80' if akt_spar >= 0 else '#f87171'
                        spar_str2   = f"{akt_spar:,.2f} €" if akt_spar >= 0 else f"-{abs(akt_spar):,.2f} €"

                        st.markdown(
                            f"<div style='background:linear-gradient(145deg,rgba(14,22,38,0.9),"
                            f"rgba(10,16,30,0.95));border:1px solid rgba(148,163,184,0.08);"
                            f"border-radius:16px;padding:20px 22px;'>"
                            f"<div style='display:flex;justify-content:space-between;"
                            f"align-items:baseline;margin-bottom:8px;'>"
                            f"<span style='font-family:DM Mono,monospace;font-size:10px;"
                            f"color:#334155;letter-spacing:1.5px;text-transform:uppercase;'>Fortschritt</span>"
                            f"<span style='font-family:DM Mono,monospace;font-size:13px;"
                            f"color:{bar_color};font-weight:600;'>{pct_display:.0f}%</span>"
                            f"</div>"
                            f"<div style='background:rgba(30,41,59,0.8);border-radius:99px;"
                            f"height:6px;overflow:hidden;margin-bottom:16px;'>"
                            f"<div style='height:100%;width:{pct_display}%;background:{bar_color};"
                            f"border-radius:99px;'></div>"
                            f"</div>"
                            f"<div style='display:flex;justify-content:space-between;'>"
                            f"<div>"
                            f"<div style='font-family:DM Mono,monospace;font-size:9px;"
                            f"color:#334155;letter-spacing:1px;text-transform:uppercase;"
                            f"margin-bottom:3px;'>Aktuell gespart</div>"
                            f"<div style='font-family:DM Sans,sans-serif;color:{spar_color2};"
                            f"font-size:18px;font-weight:600;'>{spar_str2}</div>"
                            f"</div>"
                            f"<div style='text-align:right;'>"
                            f"<div style='font-family:DM Mono,monospace;font-size:9px;"
                            f"color:#334155;letter-spacing:1px;text-transform:uppercase;"
                            f"margin-bottom:3px;'>Ziel</div>"
                            f"<div style='font-family:DM Sans,sans-serif;color:#e2e8f0;"
                            f"font-size:18px;font-weight:600;'>{goal:,.2f} €</div>"
                            f"</div></div></div>",
                            unsafe_allow_html=True
                        )

                        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

                        if not erreicht and fehlbetrag > 0:
                            aus_monat = df_month[df_month['typ'] == 'Ausgabe'].copy()
                            aus_monat['betrag_num'] = aus_monat['betrag_num'].abs()
                            kat_monat = (aus_monat.groupby('kategorie')['betrag_num']
                                         .sum().reset_index()
                                         .sort_values('betrag_num', ascending=False))

                            if not kat_monat.empty:
                                remaining = fehlbetrag
                                rows_html = ""
                                for _, kr in kat_monat.iterrows():
                                    if remaining <= 0:
                                        break
                                    cut     = min(kr['betrag_num'], remaining)
                                    pct_cut = cut / kr['betrag_num'] * 100 if kr['betrag_num'] > 0 else 0
                                    remaining -= cut
                                    rows_html += (
                                        f"<div style='display:flex;justify-content:space-between;"
                                        f"align-items:center;padding:9px 0;"
                                        f"border-bottom:1px solid rgba(255,255,255,0.04);'>"
                                        f"<span style='font-family:DM Sans,sans-serif;color:#94a3b8;"
                                        f"font-size:13px;'>{kr['kategorie']}</span>"
                                        f"<div style='display:flex;align-items:center;gap:10px;'>"
                                        f"<span style='font-family:DM Mono,monospace;color:#f87171;"
                                        f"font-size:12px;'>−{cut:,.2f} €</span>"
                                        f"<span style='font-family:DM Mono,monospace;color:#334155;"
                                        f"font-size:11px;'>({pct_cut:.0f}%)</span>"
                                        f"</div></div>"
                                    )
                                st.markdown(
                                    f"<div style='background:linear-gradient(145deg,rgba(14,22,38,0.9),"
                                    f"rgba(10,16,30,0.95));border:1px solid rgba(248,113,113,0.1);"
                                    f"border-left:3px solid #f87171;border-radius:16px;"
                                    f"padding:18px 20px;'>"
                                    f"<div style='font-family:DM Mono,monospace;font-size:9px;"
                                    f"color:#ef4444;letter-spacing:1.5px;text-transform:uppercase;"
                                    f"margin-bottom:10px;'>Noch {fehlbetrag:,.2f} € bis zum Ziel</div>"
                                    f"<div style='font-family:DM Sans,sans-serif;color:#64748b;"
                                    f"font-size:13px;margin-bottom:12px;'>"
                                    f"Diese Kategorien könntest du reduzieren:</div>"
                                    f"{rows_html}</div>",
                                    unsafe_allow_html=True
                                )
                        elif erreicht:
                            st.markdown(
                                f"<div style='background:linear-gradient(145deg,rgba(14,22,38,0.9),"
                                f"rgba(10,16,30,0.95));border:1px solid rgba(74,222,128,0.15);"
                                f"border-left:3px solid #4ade80;border-radius:16px;padding:18px 20px;'>"
                                f"<div style='font-family:DM Sans,sans-serif;color:#4ade80;"
                                f"font-size:14px;font-weight:500;'>🎉 Sparziel diesen Monat erreicht!</div>"
                                f"<div style='font-family:DM Sans,sans-serif;color:#475569;"
                                f"font-size:13px;margin-top:6px;'>"
                                f"Du hast {akt_spar - goal:,.2f} € mehr gespart als geplant.</div>"
                                f"</div>",
                                unsafe_allow_html=True
                            )
                    else:
                        st.markdown(
                            "<div style='background:rgba(15,23,42,0.5);border:1px solid "
                            "rgba(148,163,184,0.06);border-radius:12px;padding:20px 22px;"
                            "color:#334155;font-family:DM Sans,sans-serif;font-size:14px;'>"
                            "Trage links ein Sparziel ein, um Empfehlungen zu erhalten."
                            "</div>",
                            unsafe_allow_html=True
                        )

    # ── NEU: Spartöpfe ───────────────────────────────────────
    elif menu == "🪣 Spartöpfe":
        user_name = st.session_state['user_name']

        st.markdown(
            "<div style='margin-bottom:36px;margin-top:16px;'>"
            "<h1 style='font-family:DM Sans,sans-serif;font-size:40px;font-weight:700;"
            "color:#e2e8f0;margin:0 0 6px 0;letter-spacing:-1px;'>Spartöpfe 🪣</h1>"
            "<p style='font-family:DM Sans,sans-serif;color:#475569;font-size:15px;margin:0;'>"
            "Virtuelle Töpfe für deine Sparziele</p>"
            "</div>",
            unsafe_allow_html=True
        )

        toepfe = load_toepfe(user_name)

        # ── Übersicht ────────────────────────────────────────
        if toepfe:
            # Gesamtübersicht
            total_gespart = sum(t['gespart'] for t in toepfe)
            total_ziel    = sum(t['ziel'] for t in toepfe if t['ziel'] > 0)

            st.markdown(
                f"<div style='display:flex;gap:12px;margin-bottom:24px;flex-wrap:wrap;'>"
                f"<div style='flex:1;min-width:140px;background:linear-gradient(145deg,rgba(14,22,38,0.9),rgba(10,16,30,0.95));"
                f"border:1px solid rgba(56,189,248,0.12);border-radius:14px;padding:16px 18px;'>"
                f"<div style='font-family:DM Mono,monospace;font-size:9px;color:#1e40af;"
                f"letter-spacing:1.5px;text-transform:uppercase;margin-bottom:6px;'>Gesamt gespart</div>"
                f"<div style='font-family:DM Sans,sans-serif;color:#38bdf8;font-size:22px;"
                f"font-weight:600;'>{total_gespart:,.2f} €</div>"
                f"</div>"
                f"<div style='flex:1;min-width:140px;background:linear-gradient(145deg,rgba(14,22,38,0.9),rgba(10,16,30,0.95));"
                f"border:1px solid rgba(148,163,184,0.08);border-radius:14px;padding:16px 18px;'>"
                f"<div style='font-family:DM Mono,monospace;font-size:9px;color:#334155;"
                f"letter-spacing:1.5px;text-transform:uppercase;margin-bottom:6px;'>Anzahl Töpfe</div>"
                f"<div style='font-family:DM Sans,sans-serif;color:#e2e8f0;font-size:22px;"
                f"font-weight:600;'>{len(toepfe)}</div>"
                f"</div>"
                + (
                    f"<div style='flex:1;min-width:140px;background:linear-gradient(145deg,rgba(14,22,38,0.9),rgba(10,16,30,0.95));"
                    f"border:1px solid rgba(148,163,184,0.08);border-radius:14px;padding:16px 18px;'>"
                    f"<div style='font-family:DM Mono,monospace;font-size:9px;color:#334155;"
                    f"letter-spacing:1.5px;text-transform:uppercase;margin-bottom:6px;'>Gesamt-Ziel</div>"
                    f"<div style='font-family:DM Sans,sans-serif;color:#64748b;font-size:22px;"
                    f"font-weight:600;'>{total_ziel:,.2f} €</div>"
                    f"</div>"
                    if total_ziel > 0 else ""
                )
                + f"</div>",
                unsafe_allow_html=True
            )

            # ── Topf-Karten ──────────────────────────────────
            col_a, col_b = st.columns(2)
            for i, topf in enumerate(toepfe):
                col = col_a if i % 2 == 0 else col_b
                with col:
                    farbe    = topf.get('farbe', '#38bdf8')
                    gespart  = topf['gespart']
                    ziel     = topf['ziel']
                    emoji    = topf.get('emoji', '🪣')
                    topf_id  = topf['id']

                    if ziel > 0:
                        pct = min(gespart / ziel * 100, 100)
                        ziel_html = (
                            f"<div style='display:flex;justify-content:space-between;"
                            f"margin-bottom:6px;margin-top:10px;'>"
                            f"<span style='font-family:DM Mono,monospace;color:#334155;"
                            f"font-size:10px;'>{gespart:,.2f} € von {ziel:,.2f} €</span>"
                            f"<span style='font-family:DM Mono,monospace;color:{farbe};"
                            f"font-size:10px;font-weight:600;'>{pct:.0f}%</span>"
                            f"</div>"
                            f"<div style='background:rgba(30,41,59,0.8);border-radius:99px;"
                            f"height:5px;overflow:hidden;'>"
                            f"<div style='width:{pct:.0f}%;height:100%;background:{farbe};"
                            f"border-radius:99px;'></div></div>"
                        )
                        if pct >= 100:
                            badge_html = (
                                f"<span style='background:rgba(74,222,128,0.1);color:#4ade80;"
                                f"font-family:DM Mono,monospace;font-size:9px;padding:2px 8px;"
                                f"border-radius:99px;border:1px solid rgba(74,222,128,0.2);'>"
                                f"✓ ERREICHT</span>"
                            )
                        else:
                            fehl = ziel - gespart
                            badge_html = (
                                f"<span style='font-family:DM Mono,monospace;color:#334155;"
                                f"font-size:10px;'>noch {fehl:,.2f} € fehlen</span>"
                            )
                    else:
                        ziel_html  = ""
                        badge_html = (
                            f"<span style='font-family:DM Mono,monospace;color:#334155;"
                            f"font-size:10px;'>kein Ziel gesetzt</span>"
                        )

                    st.markdown(
                        f"<div style='background:linear-gradient(145deg,rgba(14,22,38,0.9),"
                        f"rgba(10,16,30,0.95));border:1px solid {farbe}20;"
                        f"border-top:2px solid {farbe};border-radius:16px;"
                        f"padding:18px 20px;margin-bottom:14px;'>"
                        f"<div style='display:flex;justify-content:space-between;align-items:flex-start;'>"
                        f"<div>"
                        f"<div style='font-size:22px;margin-bottom:4px;'>{emoji}</div>"
                        f"<div style='font-family:DM Sans,sans-serif;color:#e2e8f0;"
                        f"font-weight:600;font-size:16px;letter-spacing:-0.3px;'>{topf['name']}</div>"
                        f"</div>"
                        f"<div style='font-family:DM Sans,sans-serif;color:{farbe};"
                        f"font-size:22px;font-weight:600;'>{gespart:,.2f} €</div>"
                        f"</div>"
                        f"{ziel_html}"
                        f"<div style='margin-top:10px;'>{badge_html}</div>"
                        f"</div>",
                        unsafe_allow_html=True
                    )

                    # Einzahlen / Auszahlen
                    with st.expander(f"💰 Ein/Auszahlen — {topf['name']}"):
                        st.markdown(
                            f"<div style='font-family:DM Sans,sans-serif;color:#475569;font-size:12px;"
                            f"margin-bottom:10px;'>Geld wird als <span style='color:#a78bfa;'>Spartopf-Buchung</span> "
                            f"erfasst und vom Kontostand abgezogen — zählt aber als gespartes Geld.</div>",
                            unsafe_allow_html=True
                        )
                        tz1, tz2 = st.columns(2)
                        with tz1:
                            einzahl_key = f"einzahl_{topf_id}"
                            einzahl_val = st.number_input(
                                "Einzahlen (€)", min_value=0.01, step=1.0,
                                format="%.2f", key=einzahl_key
                            )
                            if st.button("+ Einzahlen", key=f"do_einzahl_{topf_id}",
                                         use_container_width=True, type="primary"):
                                update_topf_gespart(user_name, topf_id, topf['name'], einzahl_val)
                                st.rerun()
                        with tz2:
                            auszahl_key = f"auszahl_{topf_id}"
                            auszahl_val = st.number_input(
                                "Auszahlen (€)", min_value=0.01, step=1.0,
                                format="%.2f", key=auszahl_key
                            )
                            if st.button("− Auszahlen", key=f"do_auszahl_{topf_id}",
                                         use_container_width=True, type="secondary"):
                                update_topf_gespart(user_name, topf_id, topf['name'], -auszahl_val)
                                st.rerun()

                    # Bearbeiten / Löschen
                    te1, te2 = st.columns(2)
                    with te1:
                        if st.button("✏️", key=f"edit_topf_{topf_id}",
                                     use_container_width=True, type="secondary"):
                            st.session_state['topf_edit_data'] = topf
                            st.session_state['_dialog_just_opened'] = True
                            st.rerun()
                    with te2:
                        if st.button("🗑️", key=f"del_topf_{topf_id}",
                                     use_container_width=True, type="secondary"):
                            st.session_state['topf_delete_id'] = topf_id
                            st.session_state['topf_delete_name'] = topf['name']
                            st.session_state['_dialog_just_opened'] = True
                            st.rerun()

        else:
            st.markdown(
                "<div style='text-align:center;padding:60px 20px;'>"
                "<div style='font-size:48px;margin-bottom:16px;'>🪣</div>"
                "<p style='font-family:DM Sans,sans-serif;color:#334155;font-size:15px;'>"
                "Noch keine Spartöpfe. Erstelle deinen ersten Topf!</p>"
                "</div>",
                unsafe_allow_html=True
            )

        # ── Neuen Topf erstellen ─────────────────────────────
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown(
            "<p style='font-family:DM Mono,monospace;color:#334155;font-size:10px;"
            "font-weight:500;letter-spacing:1.5px;text-transform:uppercase;"
            "margin-bottom:16px;'>Neuen Topf erstellen</p>",
            unsafe_allow_html=True
        )

        with st.form("neuer_topf_form", clear_on_submit=True):
            nt1, nt2, nt3 = st.columns([1, 3, 2])
            with nt1:
                nt_emoji = st.text_input("Emoji", placeholder="✈️", max_chars=4)
            with nt2:
                nt_name = st.text_input("Name", placeholder="z.B. Urlaub, Neues Auto, Laptop...")
            with nt3:
                nt_ziel = st.number_input("Sparziel (€, optional)", min_value=0.0,
                                          step=50.0, format="%.2f", value=0.0)
            if st.form_submit_button("Topf erstellen", use_container_width=True, type="primary"):
                if not nt_name.strip():
                    st.error("Bitte einen Namen eingeben.")
                else:
                    save_topf(
                        user=user_name,
                        name=nt_name.strip(),
                        ziel=nt_ziel,
                        emoji=nt_emoji.strip() if nt_emoji.strip() else "🪣",
                    )
                    st.success(f"✅ Topf '{nt_name.strip()}' erstellt!")
                    st.rerun()

        # ── Dialoge für Topf bearbeiten / löschen ───────────
        if st.session_state.get('topf_edit_data'):
            @st.dialog("✏️ Topf bearbeiten")
            def topf_edit_dialog():
                t = st.session_state['topf_edit_data']
                e1, e2 = st.columns([1, 3])
                with e1:
                    new_emoji = st.text_input("Emoji", value=t['emoji'], max_chars=4)
                with e2:
                    new_name = st.text_input("Name", value=t['name'])
                new_ziel  = st.number_input("Sparziel (€)", min_value=0.0,
                                             value=float(t['ziel']), step=50.0, format="%.2f")

                cs, cc = st.columns(2)
                with cs:
                    if st.button("Speichern", use_container_width=True, type="primary"):
                        update_topf_meta(
                            user=user_name, topf_id=t['id'],
                            name=new_name.strip() or t['name'],
                            ziel=new_ziel,
                            emoji=new_emoji.strip() if new_emoji.strip() else t['emoji'],
                        )
                        st.session_state['topf_edit_data'] = None
                        st.rerun()
                with cc:
                    if st.button("Abbrechen", use_container_width=True):
                        st.session_state['topf_edit_data'] = None
                        st.rerun()
            topf_edit_dialog()

        if st.session_state.get('topf_delete_id'):
            @st.dialog("Topf löschen")
            def topf_delete_dialog():
                name = st.session_state.get('topf_delete_name', '')
                st.markdown(
                    f"<p style='color:#e2e8f0;font-size:15px;'>"
                    f"Topf <b>'{name}'</b> wirklich löschen?</p>",
                    unsafe_allow_html=True
                )
                d1, d2 = st.columns(2)
                with d1:
                    if st.button("Löschen", use_container_width=True, type="primary"):
                        delete_topf(user_name, st.session_state['topf_delete_id'])
                        st.session_state['topf_delete_id']   = None
                        st.session_state['topf_delete_name'] = None
                        st.rerun()
                with d2:
                    if st.button("Abbrechen", use_container_width=True):
                        st.session_state['topf_delete_id']   = None
                        st.session_state['topf_delete_name'] = None
                        st.rerun()
            topf_delete_dialog()

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
                df_u = conn.read(worksheet="users", ttl="5")
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
                    df_u     = conn.read(worksheet="users", ttl="5")
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
                            df_u = conn.read(worksheet="users", ttl="5")
                            if s_user in df_u['username'].values:
                                st.error("⚠️ Dieser Username ist bereits vergeben.")
                            elif s_email.strip().lower() in df_u['email'].values:
                                st.error("⚠️ Diese E-Mail ist bereits registriert.")
                            else:
                                code   = generate_code()
                                expiry = datetime.datetime.now() + datetime.timedelta(minutes=10)
                                html   = email_html(
                                    "Willkommen bei Balancely! Dein Verifizierungscode lautet:", code
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
                        df_u  = conn.read(worksheet="users", ttl="5")
                        new_u = pd.DataFrame([{
                            **st.session_state['pending_user'],
                            "verified": "True", "token": "", "token_expiry": "",
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
                        df_u = conn.read(worksheet="users", ttl="5")
                        idx  = df_u[df_u['email'] == forgot_email.strip().lower()].index
                        if idx.empty:
                            st.success("✅ Falls diese E-Mail registriert ist, wurde ein Code gesendet.")
                        else:
                            code   = generate_code()
                            expiry = datetime.datetime.now() + datetime.timedelta(minutes=10)
                            html   = email_html("Dein Code zum Zurücksetzen des Passworts lautet:", code)
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
                            df_u = conn.read(worksheet="users", ttl="5")
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



