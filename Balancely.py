import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import streamlit_authenticator as stauth

# --- 1. SEITEN-KONFIGURATION ---
st.set_page_config(page_title="Balancely", page_icon="⚖️", layout="wide")

# --- 2. CSS FÜR ABSOLUTE ZENTRIERUNG & GLEICHE ZEILENGRÖSSE ---
st.markdown("""
    <style>
    /* Hintergrund & Font */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #0e1117 !important;
    }

    /* Zentriert den gesamten Inhalt horizontal und vertikal */
    [data-testid="stVerticalBlock"] {
        display: flex;
        align-items: center;
        justify-content: center;
        flex-direction: column;
    }

    /* Die Form-Box fixieren */
    [data-testid="stForm"] {
        background-color: #161b22 !important;
        padding: 3rem !important;
        border-radius: 10px !important;
        border: 1px solid #30363d !important;
        width: 380px !important;
        margin: 0 auto !important;
    }

    /* FIX: Gleiche Höhe für alle Eingabefelder (Text & Passwort) */
    div[data-baseweb="input"] {
        height: 45px !important;
        background-color: #0d1117 !important;
        border-radius: 5px !important;
    }
    
    input {
        height: 45px !important;
        font-size: 16px !important;
        background-color: transparent !important;
        color: white !important;
    }

    /* Fokus-Farbe (Dashboard-Blau statt Gelb) */
    input:focus, div[data-baseweb="input"]:focus-within {
        border-color: #1f6feb !important;
        box-shadow: 0 0 0 1px #1f6feb !important;
    }

    /* Button Styling */
    button[kind="primaryFormSubmit"] {
        background-color: #1f6feb !important;
        height: 45px !important;
        border: none !important;
        width: 100% !important;
        color: white !important;
        font-weight: bold !important;
        margin-top: 10px !important;
    }

    /* Footer Bereich (Noch kein Konto?) */
    .auth-footer {
        text-align: center;
        width: 380px;
        margin-top: 20px;
    }
    
    .footer-text {
        color: #8b949e;
        font-size: 14px;
        margin-bottom: 0px;
    }

    /* Umschalt-Link-Button zentrieren */
    div.stButton > button {
        background: none !important;
        border: none !important;
        color: #58a6ff !important;
        font-weight: 600 !important;
        margin: 0 auto !important;
        display: block !important;
    }

    /* Versteckt das Streamlit Branding & Menü für cleanen Look */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 3. VERBINDUNG & DATEN ---
conn = st.connection("gsheets", type=GSheetsConnection)
user_db = conn.read(worksheet="users", ttl="0")

credentials = {'usernames': {}}
for _, row in user_db.iterrows():
    credentials['usernames'][str(row['username'])] = {
        'name': str(row['name']),
        'password': str(row['password']) 
    }

authenticator = stauth.Authenticate(credentials, 'balancely_cookie', 'auth_key', cookie_expiry_days=30)

if 'auth_mode' not in st.session_state:
    st.session_state['auth_mode'] = 'login'

# --- 4. INTERFACE ---
# Vertikaler Abstandhalter, um es in die echte Mitte zu schieben
st.markdown("<div style='height: 15vh;'></div>", unsafe_allow_html=True)

if not st.session_state.get("authentication_status"):
    
    st.markdown("<h1 style='text-align: center; color: white; margin-bottom: 0px;'>Balancely</h1>", unsafe_allow_html=True)

    if st.session_state['auth_mode'] == 'login':
        # Login
        authenticator.login(location='main')
        
        st.markdown('<div class="auth-footer"><p class="footer-text">Du hast noch kein Konto?</p></div>', unsafe_allow_html=True)
        if st.button("Registrieren"):
            st.session_state['auth_mode'] = 'signup'
            st.rerun()

    else:
        # Registrierung
        with st.form("reg_form"):
            st.markdown("<h3 style='text-align:center; color:white; margin-top:0;'>Konto erstellen</h3>", unsafe_allow_html=True)
            st.text_input("Name", key="reg_name")
            st.text_input("Benutzername", key="reg_user")
            st.text_input("Passwort", type="password", key="reg_pass")
            if st.form_submit_button("Registrieren"):
                # (Hier kommt deine Speicher-Logik rein wie zuvor)
                st.success("Erfolgreich!")
                st.session_state['auth_mode'] = 'login'
                st.rerun()
        
        st.markdown('<div class="auth-footer"><p class="footer-text">Bereits ein Konto?</p></div>', unsafe_allow_html=True)
        if st.button("Anmelden"):
            st.session_state['auth_mode'] = 'login'
            st.rerun()

# --- 5. DASHBOARD ---
else:
    authenticator.logout('Abmelden', 'sidebar')
    st.title(f"Willkommen zurück!")
