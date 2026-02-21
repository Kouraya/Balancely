import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import streamlit_authenticator as stauth

# --- 1. SEITEN-KONFIGURATION ---
st.set_page_config(page_title="Balancely", page_icon="⚖️", layout="wide")

# --- 2. CSS FÜR PERFEKTE ZENTRIERUNG & INLINE-FOOTER ---
st.markdown("""
    <style>
    /* Hintergrund */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #0e1117 !important;
    }

    /* FIX: "Press Enter" Instruktionen entfernen */
    [data-testid="InputInstructions"] {
        display: none !important;
    }

    /* Die Form-Box Stylen */
    [data-testid="stForm"] {
        background-color: #161b22 !important;
        padding: 40px !important;
        border-radius: 12px !important;
        border: 1px solid #30363d !important;
        min-width: 380px !important;
    }

    /* Eingabefelder glätten */
    div[data-baseweb="input"] {
        height: 45px !important;
        background-color: #0d1117 !important;
        border-radius: 8px !important;
    }
    
    input {
        color: white !important;
    }

    /* Button Styling */
    button[kind="primaryFormSubmit"] {
        background-color: #1f6feb !important;
        height: 45px !important;
        width: 100% !important;
        border: none !important;
        font-weight: bold !important;
        border-radius: 8px !important;
    }

    /* FOOTER FIX: Text und Button nebeneinander zentrieren */
    .auth-footer-container {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 8px; /* Abstand zwischen Text und Link */
        margin-top: 25px;
        color: #8b949e;
        font-size: 14px;
        width: 100%;
    }

    /* Stylt den Umschalt-Button als Link ohne Padding */
    div.stButton > button {
        background: none !important;
        border: none !important;
        color: #58a6ff !important;
        font-weight: 600 !important;
        padding: 0 !important;
        margin: 0 !important;
        line-height: 1.2 !important;
        vertical-align: baseline !important;
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
user_db = conn.read(worksheet="users", ttl="0")

if 'auth_mode' not in st.session_state:
    st.session_state['auth_mode'] = 'login'

# --- 4. INTERFACE ---
st.markdown("<div style='height: 12vh;'></div>", unsafe_allow_html=True)

# Zentrierung über Spalten
_, center_col, _ = st.columns([1, 1.2, 1])

with center_col:
    st.markdown("<p class='main-title'>Balancely</p>", unsafe_allow_html=True)

    if st.session_state['auth_mode'] == 'login':
        with st.form("login_form"):
            st.markdown("<h3 style='text-align:center; color:white; margin-top:0;'>Login</h3>", unsafe_allow_html=True)
            st.text_input("Username")
            st.text_input("Password", type="password")
            if st.form_submit_button("Anmelden"):
                pass

        # Hier ist der kombinierte Footer
        footer_col1, footer_col2 = st.columns([0.65, 0.35])
        with footer_col1:
            st.markdown("<p style='text-align:right; color:#8b949e; font-size:14px; margin-top:8px;'>Du hast noch kein Konto?</p>", unsafe_allow_html=True)
        with footer_col2:
            if st.button("Registrieren"):
                st.session_state['auth_mode'] = 'signup'
                st.rerun()

    else:
        with st.form("signup_form"):
            st.markdown("<h3 style='text-align:center; color:white; margin-top:0;'>Registrieren</h3>", unsafe_allow_html=True)
            st.text_input("Dein Name")
            st.text_input("Username")
            st.text_input("Passwort", type="password")
            if st.form_submit_button("Konto erstellen"):
                pass
        
        # Kombinierter Footer für Registrierung
        footer_col1, footer_col2 = st.columns([0.6, 0.4])
        with footer_col1:
            st.markdown("<p style='text-align:right; color:#8b949e; font-size:14px; margin-top:8px;'>Bereits ein Konto?</p>", unsafe_allow_html=True)
        with footer_col2:
            if st.button("Anmelden"):
                st.session_state['auth_mode'] = 'login'
                st.rerun()
