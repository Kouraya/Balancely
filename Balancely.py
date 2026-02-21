import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- 1. SEITEN-KONFIGURATION ---
st.set_page_config(page_title="Balancely", page_icon="⚖️", layout="wide")

# --- 2. CSS FÜR ZENTRIERUNG & DAS "REINE" AUGE ---
st.markdown("""
    <style>
    /* Hintergrund */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #0e1117 !important;
    }

    /* "Press Enter" entfernen */
    [data-testid="InputInstructions"] {
        display: none !important;
    }

    /* Die Form-Box */
    [data-testid="stForm"] {
        background-color: #161b22 !important;
        padding: 40px !important;
        border-radius: 12px !important;
        border: 1px solid #30363d !important;
        min-width: 380px !important;
        margin: 0 auto !important;
    }

    /* Input Felder */
    div[data-baseweb="input"] {
        height: 45px !important;
        background-color: #0d1117 !important;
        border-radius: 8px !important;
    }
    
    input {
        color: white !important;
    }

    /* --- DER AUGE-FIX --- */
    /* Macht die Hitbox/Hintergrund des Auge-Buttons komplett unsichtbar */
    button[aria-label="Show password"] {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        color: #8b949e !important; /* Dezentes Grau für das Auge selbst */
    }

    /* Entfernt den grauen Kreis beim Drüberfahren (Hover) */
    button[aria-label="Show password"]:hover {
        background-color: transparent !important;
        color: white !important; /* Auge wird weiß beim Hover, aber ohne Kasten */
    }
    
    /* Entfernt den Effekt beim Anklicken */
    button[aria-label="Show password"]:active {
        background-color: transparent !important;
    }

    /* Login-Button */
    button[kind="primaryFormSubmit"] {
        background-color: #1f6feb !important;
        height: 45px !important;
        width: 100% !important;
        font-weight: bold !important;
        border-radius: 8px !important;
    }

    /* Footer Zentrierung */
    div.stButton > button {
        background: none !important;
        border: none !important;
        color: #58a6ff !important;
        font-weight: 600 !important;
        padding: 0 !important;
        margin: 0 !important;
    }

    .main-title {
        text-align: center;
        color: white;
        font-size: 45px;
        font-weight: bold;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATEN ---
conn = st.connection("gsheets", type=GSheetsConnection)

if 'auth_mode' not in st.session_state:
    st.session_state['auth_mode'] = 'login'

# --- 4. INTERFACE ---
st.markdown("<div style='height: 10vh;'></div>", unsafe_allow_html=True)

_, center_col, _ = st.columns([1, 1.1, 1])

with center_col:
    st.markdown("<p class='main-title'>Balancely</p>", unsafe_allow_html=True)

    if st.session_state['auth_mode'] == 'login':
        with st.form("login_form"):
            st.markdown("<h3 style='text-align:center; color:white; margin-top:0;'>Anmelden</h3>", unsafe_allow_html=True)
            st.text_input("Username")
            st.text_input("Password", type="password")
            st.form_submit_button("Login")

        f_left, f_right = st.columns([0.61, 0.39])
        with f_left:
            st.markdown("<p style='text-align:right; color:#8b949e; font-size:14px; margin-top:8px;'>Du hast noch kein Konto?</p>", unsafe_allow_html=True)
        with f_right:
            if st.button("Registrieren"):
                st.session_state['auth_mode'] = 'signup'
                st.rerun()

    else:
        with st.form("signup_form"):
            st.markdown("<h3 style='text-align:center; color:white; margin-top:0;'>Registrieren</h3>", unsafe_allow_html=True)
            st.text_input("Dein Name", key="reg_name")
            st.text_input("Benutzername", key="reg_user")
            st.text_input("Passwort", type="password", key="reg_pass")
            st.form_submit_button("Konto erstellen")
        
        f_left, f_right = st.columns([0.58, 0.42])
        with f_left:
            st.markdown("<p style='text-align:right; color:#8b949e; font-size:14px; margin-top:8px;'>Bereits ein Konto?</p>", unsafe_allow_html=True)
        with f_right:
            if st.button("Anmelden"):
                st.session_state['auth_mode'] = 'login'
                st.rerun()
