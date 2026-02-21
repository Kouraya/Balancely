import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import streamlit_authenticator as stauth

# --- 1. SEITEN-KONFIGURATION ---
st.set_page_config(page_title="Balancely", page_icon="⚖️", layout="wide")

# --- 2. DAS OPTIMIERTE CSS (ZENTRIERUNG & CLEAN LOOK) ---
st.markdown("""
    <style>
    /* Hintergrundfarbe der App */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #0e1117 !important;
    }

    /* "Press Enter to submit" Instruktion komplett ausblenden */
    [data-testid="InputInstructions"] {
        display: none !important;
    }

    /* Die Form-Box (Login/Registrieren) */
    [data-testid="stForm"] {
        background-color: #161b22 !important;
        padding: 40px !important;
        border-radius: 12px !important;
        border: 1px solid #30363d !important;
        min-width: 380px !important;
        margin: 0 auto !important;
    }

    /* Einheitliche Höhe für alle Eingabefelder */
    div[data-baseweb="input"] {
        height: 45px !important;
        background-color: #0d1117 !important;
        border-radius: 8px !important;
    }
    
    input {
        color: white !important;
        font-family: 'Source Sans Pro', sans-serif !important;
    }

    /* Fokus-Rahmen in Dashboard-Blau */
    div[data-baseweb="input"]:focus-within {
        border-color: #1f6feb !important;
        box-shadow: 0 0 0 1px #1f6feb !important;
    }

    /* Haupt-Button Styling */
    button[kind="primaryFormSubmit"] {
        background-color: #1f6feb !important;
        height: 45px !important;
        width: 100% !important;
        border: none !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        color: white !important;
    }

    /* Footer-Link Button Styling (Umschalten) */
    div.stButton > button {
        background: none !important;
        border: none !important;
        color: #58a6ff !important;
        font-weight: 600 !important;
        padding: 0 !important;
        margin: 0 !important;
        line-height: 1.2 !important;
        vertical-align: baseline !important;
        text-align: left !important;
    }

    /* Titel Styling */
    .main-title {
        text-align: center;
        color: white;
        font-size: 45px;
        font-weight: bold;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATENBANK-ANBINDUNG ---
conn = st.connection("gsheets", type=GSheetsConnection)
user_db = conn.read(worksheet="users", ttl="0")

# Navigation zwischen Login und Registrierung
if 'auth_mode' not in st.session_state:
    st.session_state['auth_mode'] = 'login'

# --- 4. INTERFACE ---
# Vertikaler Abstand für die optische Mitte
st.markdown("<div style='height: 10vh;'></div>", unsafe_allow_html=True)

# Spalten-Layout für die Zentrierung der gesamten Box
_, center_col, _ = st.columns([1, 1.1, 1])

with center_col:
    st.markdown("<p class='main-title'>Balancely</p>", unsafe_allow_html=True)

    if st.session_state['auth_mode'] == 'login':
        # LOGIN FORMULAR
        with st.form("login_form"):
            st.markdown("<h3 style='text-align:center; color:white; margin-top:0;'>Anmelden</h3>", unsafe_allow_html=True)
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                # Hier Login-Prüflogik einfügen
                pass

        # FOOTER: Text und Link nebeneinander zentrieren
        # Verhältnis leicht angepasst (0.61), um den Link perfekt mittig zu rücken
        f_left, f_right = st.columns([0.61, 0.39])
        with f_left:
            st.markdown("<p style='text-align:right; color:#8b949e; font-size:14px; margin-top:8px;'>Du hast noch kein Konto?</p>", unsafe_allow_html=True)
        with f_right:
            if st.button("Registrieren"):
                st.session_state['auth_mode'] = 'signup'
                st.rerun()

    else:
        # REGISTRIEREN FORMULAR
        with st.form("signup_form"):
            st.markdown("<h3 style='text-align:center; color:white; margin-top:0;'>Registrieren</h3>", unsafe_allow_html=True)
            st.text_input("Dein Name", key="reg_name")
            st.text_input("Benutzername", key="reg_user")
            st.text_input("Passwort", type="password", key="reg_pass")
            if st.form_submit_button("Konto erstellen"):
                # Hier Registrierungs-Logik einfügen
                pass
        
        # FOOTER: Text und Link nebeneinander zentrieren
        f_left, f_right = st.columns([0.58, 0.42])
        with f_left:
            st.markdown("<p style='text-align:right; color:#8b949e; font-size:14px; margin-top:8px;'>Bereits ein Konto?</p>", unsafe_allow_html=True)
        with f_right:
            if st.button("Anmelden"):
                st.session_state['auth_mode'] = 'login'
                st.rerun()
