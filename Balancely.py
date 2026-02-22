# ============================================================
#  Balancely — Persönliche Finanzverwaltung
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
    """Prüft ob ein deleted-Wert als gelöscht gilt (True / 1 / 1.0)."""
    try:
        return float(value) >= 1.0
    except (ValueError, TypeError):
        return str(value).strip().lower() in ('true', '1', 'yes')


def is_verified(value) -> bool:
    """Prüft ob ein verified-Wert als verifiziert gilt."""
    try:
        return float(value) >= 1.0
    except (ValueError, TypeError):
        return str(value).strip().lower() in ('true', '1', 'yes')


def format_timestamp(ts_str, datum_str) -> str:
    """Zeigt 'heute HH:MM', 'gestern HH:MM' oder 'DD.MM.YYYY HH:MM'."""
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
        # Kein Timestamp vorhanden — nur Datum anzeigen
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
    """Findet die passende (nicht-gelöschte) Zeile im DataFrame anhand von Inhalt."""
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
#  Globales CSS
# ============================================================

st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
    background: radial-gradient(circle at top right, #1e293b, #0f172a, #020617) !important;
}
.main-title {
    text-align: center; color: #f8fafc; font-size: 64px; font-weight: 800;
    letter-spacing: -2px; margin-bottom: 0;
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
div[data-testid="stTextInputRootElement"] { background-color: transparent !important; }
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
input { padding-left: 15px !important; color: #f1f5f9 !important; }
div[data-testid="stDateInput"] > div {
    background-color: transparent !important;
    border: 1px solid #1e293b !important;
    border-radius: 8px !important;
    box-shadow: none !important;
    min-height: 42px !important;
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
button[data-testid="stNumberInputStepUp"] { display: none !important; }
div[data-baseweb="input"] > div:not(:has(input)):not(:has(button)):not(:has(svg)) {
    display: none !important;
}
[data-testid="InputInstructions"],
[data-testid="stInputInstructions"],
div[class*="InputInstructions"],
div[class*="stInputInstructions"] {
    display: none !important; visibility: hidden !important;
    height: 0 !important; overflow: hidden !important; position: absolute !important;
}
[data-testid="stSidebar"] {
    background-color: #0b0f1a !important;
    border-right: 1px solid #1e293b !important;
}
/* Cursor pointer auf allen klickbaren Elementen */
button, [data-testid="stPopover"] button,
div[data-baseweb="select"],
div[data-baseweb="select"] *,
div[data-testid="stDateInput"],
[data-testid="stSelectbox"] * {
    cursor: pointer !important;
}
/* Verhindert dass Date-Input Hitbox über andere Elemente ragt */
div[data-testid="stDateInput"] {
    overflow: hidden !important;
}
div[data-testid="stDateInput"] > div {
    overflow: hidden !important;
}
button[kind="primaryFormSubmit"],
button[kind="secondaryFormSubmit"] {
    height: 50px !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
}
button[kind="primaryFormSubmit"] {
    background: linear-gradient(135deg, #38bdf8, #1d4ed8) !important;
    border: none !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] > div > label {
    border: 1px solid #1e293b !important; border-radius: 10px !important;
    padding: 8px 12px !important; margin-bottom: 4px !important;
    color: #94a3b8 !important; transition: all 0.15s ease !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] > div > label:hover {
    border-color: #38bdf8 !important; color: #f1f5f9 !important;
    background: rgba(56, 189, 248, 0.08) !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] > div > label:has(input:checked) {
    border-color: #38bdf8 !important; background: rgba(56, 189, 248, 0.15) !important;
    color: #f1f5f9 !important; font-weight: 600 !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] > div > label > div:first-child {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)


# ============================================================
#  Session State initialisieren
# ============================================================

# Standard-Kategorien mit Emojis
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
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

conn = st.connection("gsheets", type=GSheetsConnection)

def load_custom_cats(user: str, typ: str) -> list:
    """Lädt eigene Kategorien des Users aus Google Sheets."""
    try:
        df = conn.read(worksheet="categories", ttl="0")
        if df.empty or 'user' not in df.columns:
            return []
        rows = df[(df['user'] == user) & (df['typ'] == typ)]
        return rows['kategorie'].tolist()
    except Exception:
        return []

def save_custom_cat(user: str, typ: str, kategorie: str):
    """Speichert eine neue Kategorie in Google Sheets."""
    try:
        df = conn.read(worksheet="categories", ttl="0")
    except Exception:
        df = pd.DataFrame(columns=['user', 'typ', 'kategorie'])
    new_row = pd.DataFrame([{'user': user, 'typ': typ, 'kategorie': kategorie}])
    conn.update(worksheet="categories", data=pd.concat([df, new_row], ignore_index=True))

def delete_custom_cat(user: str, typ: str, kategorie: str):
    """Löscht eine eigene Kategorie aus Google Sheets."""
    try:
        df = conn.read(worksheet="categories", ttl="0")
        df = df[~((df['user'] == user) & (df['typ'] == typ) & (df['kategorie'] == kategorie))]
        conn.update(worksheet="categories", data=df)
    except Exception:
        pass

@st.dialog("➕ Neue Kategorie erstellen")
def new_category_dialog():
    typ = st.session_state.get('new_cat_typ', 'Ausgabe')
    st.markdown(
        f"<p style='color:#94a3b8;font-size:13px;'>Für: <b style='color:#38bdf8;'>{typ}</b></p>",
        unsafe_allow_html=True
    )
    nc1, nc2 = st.columns([1, 3])
    with nc1:
        new_emoji = st.text_input("Emoji", placeholder="🎵", max_chars=4)
    with nc2:
        new_name = st.text_input("Name", placeholder="z.B. Musik")

    nc_typ = st.selectbox("Typ", ["Ausgabe", "Einnahme"],
                          index=0 if typ == "Ausgabe" else 1)

    col_save, col_cancel = st.columns(2)
    with col_save:
        if st.button("✅ Speichern", use_container_width=True, type="primary"):
            if not new_name.strip():
                st.error("❌ Bitte einen Namen eingeben.")
            else:
                label    = f"{new_emoji.strip()} {new_name.strip()}"                            if new_emoji.strip() else new_name.strip()
                existing = load_custom_cats(st.session_state['user_name'], nc_typ)                            + DEFAULT_CATS[nc_typ]
                if label in existing:
                    st.error("⚠️ Diese Kategorie existiert bereits.")
                else:
                    save_custom_cat(st.session_state['user_name'], nc_typ, label)
                    st.session_state['show_new_cat'] = False
                    st.rerun()
    with col_cancel:
        if st.button("❌ Abbrechen", use_container_width=True):
            st.session_state['show_new_cat'] = False
            st.rerun()


@st.dialog("Eintrag löschen")
def confirm_delete(row_data):
    st.markdown(
        "<p style='color:#f1f5f9;font-size:16px;'>Wollen Sie diesen Eintrag wirklich löschen?</p>",
        unsafe_allow_html=True
    )
    st.markdown(
        f"<p style='color:#94a3b8;font-size:13px;'>"
        f"{row_data['datum']} · {row_data['betrag_anzeige']} · {row_data['kategorie']}</p>",
        unsafe_allow_html=True
    )
    col_ja, col_nein = st.columns(2)
    with col_ja:
        if st.button("✅ Ja, löschen", use_container_width=True, type="primary"):
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
                st.error("❌ Eintrag nicht gefunden.")
    with col_nein:
        if st.button("❌ Abbrechen", use_container_width=True):
            st.rerun()


# ============================================================
#  APP — Eingeloggt
# ============================================================

if st.session_state['logged_in']:

    # ── Sidebar ─────────────────────────────────────────────
    with st.sidebar:
        st.markdown("<h2 style='color:white;'>Balancely ⚖️</h2>", unsafe_allow_html=True)
        st.markdown(f"👤 Eingeloggt: **{st.session_state['user_name']}**")
        st.markdown("---")
        menu = st.radio(
            "Navigation",
            ["📈 Dashboard", "💸 Transaktionen", "📂 Analysen", "⚙️ Einstellungen"],
            label_visibility="collapsed"
        )
        st.markdown("<div style='height:30vh;'></div>", unsafe_allow_html=True)
        if st.button("Logout ➜", use_container_width=True, type="secondary"):
            st.session_state['logged_in'] = False
            st.rerun()

    # ── Dashboard ────────────────────────────────────────────
    if menu == "📈 Dashboard":
        st.title(f"Deine Übersicht, {st.session_state['user_name']}! ⚖️")
        try:
            df_t = conn.read(worksheet="transactions", ttl="0")
            if 'user' in df_t.columns:
                alle = df_t[df_t['user'] == st.session_state['user_name']].copy()
                if 'deleted' in alle.columns:
                    user_df = alle[~alle['deleted'].astype(str).str.strip().str.lower()
                                   .isin(['true', '1', '1.0'])]
                else:
                    user_df = alle

                if not user_df.empty:
                    ein = pd.to_numeric(user_df[user_df['typ'] == "Einnahme"]['betrag']).sum()
                    aus = abs(pd.to_numeric(user_df[user_df['typ'] == "Ausgabe"]['betrag']).sum())
                    bal = ein - aus
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Kontostand", f"{bal:,.2f} €")
                    c2.metric("Einnahmen",  f"{ein:,.2f} €")
                    c3.metric("Ausgaben",   f"{aus:,.2f} €", delta_color="inverse")
                    st.subheader("Ausgaben nach Kategorie")
                    ausg_df = user_df[user_df['typ'] == "Ausgabe"].copy()
                    ausg_df['betrag'] = abs(pd.to_numeric(ausg_df['betrag']))
                    st.bar_chart(data=ausg_df, x="kategorie", y="betrag", color="kategorie")
                else:
                    st.info("Noch keine Daten vorhanden.")
        except Exception:
            st.warning("Verbindung wird hergestellt...")

    # ── Transaktionen ────────────────────────────────────────
    elif menu == "💸 Transaktionen":
        user_name   = st.session_state['user_name']
        t_type      = st.session_state['t_type']
        std_cats    = DEFAULT_CATS[t_type]
        custom_cats = load_custom_cats(user_name, t_type)
        all_cats    = std_cats + custom_cats

        # Dialog VOR allem rendern
        if st.session_state.get('show_new_cat'):
            new_category_dialog()

        # ── Header ──────────────────────────────────────────
        st.markdown(
            "<h1 style='margin-bottom:4px;'>Neue Buchung</h1>"
            "<p style='color:#64748b;font-size:14px;margin-bottom:24px;'>"
            "Erfasse Einnahmen und Ausgaben</p>",
            unsafe_allow_html=True
        )

        # ── Typ-Toggle als schicke Card-Buttons ─────────────
        st.markdown(
            "<p style='color:#64748b;font-size:12px;font-weight:600;"
            "letter-spacing:1px;text-transform:uppercase;margin-bottom:8px;'>"
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

        # ── Buchungsformular ─────────────────────────────────
        with st.form("t_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                t_amount = st.number_input("Betrag in €", min_value=0.01, step=0.01, format="%.2f")
                t_date   = st.date_input("Datum", datetime.date.today())
            with col2:
                # Kategorie-Label mit "+ Neue" Link daneben
                st.markdown(
                    "<div style='display:flex;justify-content:space-between;"
                    "align-items:center;margin-bottom:4px;'>"
                    "<span style='font-size:14px;color:#f1f5f9;'>Kategorie</span>"
                    "</div>",
                    unsafe_allow_html=True
                )
                t_cat  = st.selectbox("Kategorie", all_cats, label_visibility="collapsed")
                t_note = st.text_input("Notiz (optional)", placeholder="z.B. Supermarkt, Tankstelle...")

            saved = st.form_submit_button("💾 Speichern", use_container_width=True)
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

        # ── Neue Kategorie + Verwaltung ──────────────────────
        cat_btn_col, manage_col = st.columns([1, 1])
        with cat_btn_col:
            if st.button("➕ Neue Kategorie erstellen", use_container_width=True, type="secondary"):
                st.session_state['show_new_cat'] = True
                st.session_state['new_cat_typ']  = t_type
                st.rerun()
        if custom_cats:
            with manage_col:
                with st.expander(f"🗂️ Eigene {t_type}-Kategorien"):
                    for cat in custom_cats:
                        cc1, cc2 = st.columns([5, 1])
                        cc1.markdown(
                            f"<span style='color:#cbd5e1;font-size:14px;'>{cat}</span>",
                            unsafe_allow_html=True
                        )
                        if cc2.button("🗑️", key=f"delcat_{cat}", use_container_width=True):
                            delete_custom_cat(user_name, t_type, cat)
                            st.rerun()

        # ── Neue Kategorie erstellen ─────────────────────────
        if t_cat == "➕ Neue Kategorie erstellen" or st.session_state['show_new_cat']:
            st.markdown("---")
            st.subheader("➕ Neue Kategorie erstellen")
            with st.form("new_cat_form", clear_on_submit=True):
                nc1, nc2 = st.columns([1, 3])
                with nc1:
                    new_emoji = st.text_input("Emoji", placeholder="z.B. 🎵", max_chars=4)
                with nc2:
                    new_name  = st.text_input("Name", placeholder="z.B. Musik")
                nc_typ = st.selectbox("Für welchen Typ?", ["Ausgabe", "Einnahme"])
                if st.form_submit_button("Kategorie speichern", use_container_width=True, type="primary"):
                    if not new_name.strip():
                        st.error("❌ Bitte einen Namen eingeben.")
                    else:
                        label = f"{new_emoji.strip()} {new_name.strip()}" if new_emoji.strip()                                 else new_name.strip()
                        existing = load_custom_cats(user_name, nc_typ) + DEFAULT_CATS[nc_typ]
                        if label in existing:
                            st.error("⚠️ Diese Kategorie existiert bereits.")
                        else:
                            save_custom_cat(user_name, nc_typ, label)
                            st.session_state['show_new_cat'] = False
                            st.success(f"✅ Kategorie '{label}' gespeichert!")
                            st.rerun()

        # ── Neue Kategorie Dialog ────────────────────────────
        if st.session_state.get('show_new_cat'):
            new_category_dialog()

        # Eigene Kategorien verwalten
        if custom_cats:
            with st.expander(f"🗂️ Eigene {t_type}-Kategorien verwalten"):
                for cat in custom_cats:
                    cc1, cc2 = st.columns([5, 1])
                    cc1.markdown(f"<span style='color:#cbd5e1'>{cat}</span>", unsafe_allow_html=True)
                    if cc2.button("🗑️", key=f"delcat_{cat}", help="Löschen",
                                  use_container_width=True):
                        delete_custom_cat(user_name, t_type, cat)
                        st.rerun()

        # ── Buchungstabelle ──────────────────────────────────
        st.markdown("---")
        st.subheader("📋 Meine Buchungen")
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
                    # Neueste zuerst — nach Timestamp, dann nach Datum
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

                        c1, c2, c3, c4, c5 = st.columns([2.5, 2, 2, 3, 1.5])
                        c1.markdown(
                            f"<span style='color:#94a3b8'>{zeit_label}</span>",
                            unsafe_allow_html=True
                        )
                        c2.markdown(
                            f"<span style='color:{farbe};font-weight:700'>"
                            f"{row['betrag_anzeige']}</span>",
                            unsafe_allow_html=True
                        )
                        c3.markdown(
                            f"<span style='color:#cbd5e1'>{row['kategorie']}</span>",
                            unsafe_allow_html=True
                        )
                        c4.markdown(
                            f"<span style='color:#64748b'>{notiz}</span>",
                            unsafe_allow_html=True
                        )

                        with c5:
                            with st.popover("⋯", use_container_width=True):
                                if st.button("✏️ Bearbeiten", key=f"edit_btn_{orig_idx}",
                                             use_container_width=True):
                                    st.session_state['edit_idx'] = orig_idx
                                    st.rerun()
                                if st.button("🗑️ Löschen", key=f"del_btn_{orig_idx}",
                                             use_container_width=True):
                                    confirm_delete({
                                        "user":          row['user'],
                                        "datum":         row['datum'],
                                        "betrag":        row['betrag'],
                                        "betrag_anzeige": row['betrag_anzeige'],
                                        "kategorie":     row['kategorie'],
                                    })

                        # Bearbeitungsformular
                        if st.session_state['edit_idx'] == orig_idx:
                            with st.form(key=f"edit_form_{orig_idx}"):
                                st.markdown(
                                    "<p style='color:#38bdf8;font-weight:600;margin-bottom:8px;'>"
                                    "✏️ Eintrag bearbeiten</p>",
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
                                    cats_e   = ["Gehalt", "Bonus", "Verkauf"] \
                                               if e_typ == "Einnahme" \
                                               else ["Essen", "Miete", "Freizeit",
                                                     "Transport", "Shopping"]
                                    curr_cat = row['kategorie'] \
                                               if row['kategorie'] in cats_e else cats_e[0]
                                    e_cat  = st.selectbox(
                                        "Kategorie", cats_e, index=cats_e.index(curr_cat)
                                    )
                                e_notiz = st.text_input(
                                    "Notiz (optional)", value=notiz,
                                    placeholder="z.B. Supermarkt, Tankstelle..."
                                )
                                col_save, col_cancel = st.columns(2)
                                with col_save:
                                    saved = st.form_submit_button(
                                        "💾 Speichern", use_container_width=True, type="primary"
                                    )
                                with col_cancel:
                                    cancelled = st.form_submit_button(
                                        "🚫 Abbrechen", use_container_width=True
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
        st.title("Einstellungen ⚙️")
        st.subheader("Passwort ändern")
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
    st.markdown("<div style='height:8vh;'></div>", unsafe_allow_html=True)
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
                    "<h3 style='text-align:center;color:white;'>Anmelden</h3>",
                    unsafe_allow_html=True
                )
                u_in = st.text_input("Username", placeholder="Benutzername")
                p_in = st.text_input("Passwort", type="password")

                if st.form_submit_button("Anmelden"):
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
                    "<h3 style='text-align:center;color:white;'>Registrierung</h3>",
                    unsafe_allow_html=True
                )
                s_name  = st.text_input("Name",     placeholder="Max Mustermann")
                s_user  = st.text_input("Username", placeholder="max123")
                s_email = st.text_input("E-Mail",   placeholder="max@beispiel.de")
                s_pass  = st.text_input("Passwort", type="password")
                c_pass  = st.text_input("Passwort wiederholen", type="password")

                if st.form_submit_button("Konto erstellen"):
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
                    "<h3 style='text-align:center;color:white;'>E-Mail verifizieren</h3>",
                    unsafe_allow_html=True
                )
                st.markdown(
                    f"<p style='text-align:center;color:#94a3b8;'>Wir haben einen 6-stelligen "
                    f"Code an <b style='color:#38bdf8;'>{pending_email}</b> gesendet.</p>",
                    unsafe_allow_html=True
                )
                code_input = st.text_input("Code eingeben", placeholder="123456", max_chars=6)

                if st.form_submit_button("Bestätigen", use_container_width=True):
                    if st.session_state['verify_expiry'] and \
                       datetime.datetime.now() > st.session_state['verify_expiry']:
                        st.error("⏰ Der Code ist abgelaufen. Bitte registriere dich erneut.")
                        st.session_state['auth_mode'] = 'signup'
                        st.rerun()
                    elif code_input.strip() != st.session_state['verify_code']:
                        st.error("❌ Falscher Code. Bitte versuche es erneut.")
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

            if st.button("➡️ Zum Login", use_container_width=True, type="primary"):
                st.session_state['auth_mode'] = 'login'
                st.rerun()

        # ── Passwort vergessen ───────────────────────────────
        elif mode == 'forgot':
            with st.form("forgot_form"):
                st.markdown(
                    "<h3 style='text-align:center;color:white;'>Passwort vergessen</h3>",
                    unsafe_allow_html=True
                )
                st.markdown(
                    "<p style='text-align:center;color:#94a3b8;'>Gib deine E-Mail-Adresse ein.</p>",
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
                    "<h3 style='text-align:center;color:white;'>Passwort zurücksetzen</h3>",
                    unsafe_allow_html=True
                )
                st.markdown(
                    f"<p style='text-align:center;color:#94a3b8;'>Code wurde an "
                    f"<b style='color:#38bdf8;'>{st.session_state['reset_email']}</b>"
                    f" gesendet.</p>",
                    unsafe_allow_html=True
                )
                code_input = st.text_input("6-stelliger Code", placeholder="123456", max_chars=6)
                pw_neu     = st.text_input("Neues Passwort", type="password")
                pw_neu2    = st.text_input("Passwort wiederholen", type="password")

                if st.form_submit_button("Passwort speichern", use_container_width=True):
                    if st.session_state['reset_expiry'] and \
                       datetime.datetime.now() > st.session_state['reset_expiry']:
                        st.error("⏰ Der Code ist abgelaufen. Bitte fordere einen neuen an.")
                        st.session_state['auth_mode'] = 'forgot'
                        st.rerun()
                    elif code_input.strip() != st.session_state['reset_code']:
                        st.error("❌ Falscher Code.")
                    else:
                        ok, msg = check_password_strength(pw_neu)
                        if not ok:
                            st.error(f"❌ {msg}")
                        elif pw_neu != pw_neu2:
                            st.error("❌ Die Passwörter stimmen nicht überein.")
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
