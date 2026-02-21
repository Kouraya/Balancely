import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import streamlit_authenticator as stauth

# --- 1. SEITEN-KONFIGURATION ---
st.set_page_config(page_title="Balancely", page_icon="⚖️", layout="wide")

# --- 2. CSS FÜR PERFEKTE AUSRICHTUNG ---
st.markdown("""
    <style>
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #0e1117 !important;
    }

    /* Zentriert den gesamten Block auf der Seite */
    [data-testid="stMain"] > div {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        flex-direction: column !important;
    }

    /* Die Login/Register Box */
    [data-testid="stForm"] {
        background-color: #161b22 !important;
        padding: 3rem !important;
        border-radius: 12px !important;
        border: 1px solid #30363d !important;
        width: 400px !important;
        margin: 0 auto !important;
    }

    /* Gleiche Höhe für ALLE Eingabefelder */
    div[data-baseweb="input"], input {
        height: 48px !important;
        line-height: 48px !important;
        font-size: 16px !important;
        background-color: #0d1117 !important;
        color: white !important;
        border-radius: 6px !important;
    }

    /* Dashboard-Blau bei Klick */
    div[data-baseweb="input"]:focus-within {
        border-color: #1f6feb !important;
        box-shadow: 0 0 0 1px #1f6feb !important;
    }

    /* Button Styling */
    button[kind="primaryFormSubmit"] {
        background-color: #1f6feb !important;
        height: 48px !important;
        width: 100% !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        margin-top: 20px !important;
    }

    /* Zentrierter Footer-Bereich */
    .auth-footer {
        width: 400px;
        text-align: center;
        margin-top: 15px;
    }
    
    .footer-text {
        color: #8b949e;
        font-size: 14px;
        margin-bottom: 0px;
    }

    /* Switch-Link zentrieren */
    div.stButton > button {
        background: none !important;
        border: none !important;
        color: #58a6ff !important;
        margin: 0 auto !important;
        display: block !important;
        padding: 0 !important;
    }
    
    /* Entfernt den Standard-Auge-Button von Streamlit im Feld */
    button[aria-label="Show password"] {
        display: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATENBANK ---
conn = st.connection("gsheets", type=GSheetsConnection)
user_db = conn.read(worksheet="users", ttl="0")

# --- 4. NAVIGATION STATE ---
if 'auth_mode' not in st.session_state:
    st.session_state['auth_mode'] = 'login'
if 'show_pw' not in st.session_state:
    st.session_state['show_pw'] = False

# --- 5. INTERFACE ---
st.markdown("<div style='height: 10vh;'></div>", unsafe_allow_html=True)
st.markdown("<h1 style='text-align: center; color: white;'>Balancely</h1>", unsafe_allow_html=True)

# Container für die Box
with st.container():
    if st.session_state['auth_mode'] == 'login':
        with st.form("login_form"):
            st.markdown("<h3 style='text-align:center; color:white;'>Login</h3>", unsafe_allow_html=True)
            user = st.text_input("Username")
            
            # Passwort-Logik mit Auge daneben
            pw_col, eye_col = st.columns([0.85, 0.15])
            pw_type = "text" if st.session_state['show_pw'] else "password"
            
            with pw_col:
                pw = st.text_input("Password", type=pw_type)
            with eye_col:
                st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                if st.button("👁️", key="toggle_login"):
                    st.session_state['show_pw'] = not st.session_state['show_pw']
                    st.rerun()

            if st.form_submit_button("Login"):
                # Hier Login-Prüfung einfügen
                pass
        
        st.markdown('<div class="auth-footer"><p class="footer-text">Du hast noch kein Konto?</p></div>', unsafe_allow_html=True)
        if st.button("Registrieren"):
            st.session_state['auth_mode'] = 'signup'
            st.rerun()

    else:
        with st.form("signup_form"):
            st.markdown("<h3 style='text-align:center; color:white;'>Registrieren</h3>", unsafe_allow_html=True)
            st.text_input("Dein voller Name")
            st.text_input("Wunsch-Benutzername")
            
            # Passwort mit Auge daneben für Registrierung
            pw_col_reg, eye_col_reg = st.columns([0.85, 0.15])
            pw_type_reg = "text" if st.session_state['show_pw'] else "password"
            
            with pw_col_reg:
                new_pw = st.text_input("Passwort", type=pw_type_reg)
            with eye_col_reg:
                st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                if st.button("👁️", key="toggle_reg"):
                    st.session_state['show_pw'] = not st.session_state['show_pw']
                    st.rerun()

            if st.form_submit_button("Konto erstellen"):
                # Hier Speicher-Logik einfügen
                pass
        
        st.markdown('<div class="auth-footer"><p class="footer-text">Bereits ein Konto?</p></div>', unsafe_allow_html=True)
        if st.button("Anmelden"):
            st.session_state['auth_mode'] = 'login'
            st.rerun()
