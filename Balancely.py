import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import streamlit_authenticator as stauth

# --- 1. SEITEN-KONFIGURATION ---
st.set_page_config(page_title="Balancely", page_icon="⚖️", layout="wide")

# --- 2. DAS ULTIMATIVE CSS (KEIN OVERLAP, PERFEKT ZENTRIERT) ---
st.markdown("""
    <style>
    /* Hintergrund */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #0e1117 !important;
    }

    /* FIX: "Press Enter to submit form" verstecken */
    [data-testid="stForm"] div[data-testid="InputInstructions"] {
        display: none !important;
    }

    /* Die Form-Box Stylen */
    [data-testid="stForm"] {
        background-color: #161b22 !important;
        padding: 40px !important;
        border-radius: 12px !important;
        border: 1px solid #30363d !important;
        min-width: 350px !important;
    }

    /* Zeilenhöhe und Font-Zwang */
    div[data-baseweb="input"] {
        height: 45px !important;
        background-color: #0d1117 !important;
    }
    
    input {
        font-family: 'Source Sans Pro', sans-serif !important;
    }

    /* Button Styling */
    button[kind="primaryFormSubmit"] {
        background-color: #1f6feb !important;
        height: 45px !important;
        width: 100% !important;
        border: none !important;
        font-weight: bold !important;
    }

    /* Footer (Text und Link zentrieren) */
    .auth-footer {
        text-align: center;
        margin-top: 20px;
        color: #8b949e;
        font-size: 14px;
    }

    /* Den Registrieren-Link mittig setzen */
    div.stButton > button {
        background: none !important;
        border: none !important;
        color: #58a6ff !important;
        margin: 0 auto !important;
        display: block !important;
    }
    
    /* Zentriert den Titel über der Box */
    .main-title {
        text-align: center;
        color: white;
        font-size: 42px;
        font-weight: bold;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATEN & LOGIK ---
conn = st.connection("gsheets", type=GSheetsConnection)
user_db = conn.read(worksheet="users", ttl="0")

# Navigation State
if 'auth_mode' not in st.session_state:
    st.session_state['auth_mode'] = 'login'

# --- 4. DAS INTERFACE (MIT ECHTER ZENTRIERUNG) ---
# Erzeugt drei Spalten: Links und rechts leer, die Mitte (Index 1) bekommt die Box
_, center_col, _ = st.columns([1, 1.2, 1])

with center_col:
    st.markdown("<div style='height: 10vh;'></div>", unsafe_allow_html=True)
    st.markdown("<p class='main-title'>Balancely</p>", unsafe_allow_html=True)

    if st.session_state['auth_mode'] == 'login':
        with st.form("login_form"):
            st.markdown("<h3 style='text-align:center; color:white;'>Login</h3>", unsafe_allow_html=True)
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            # Hier nutzen wir den Streamlit-Authenticator Check oder deine eigene Logik
            if st.form_submit_button("Anmelden"):
                # Deine Login-Logik hier...
                pass

        st.markdown('<div class="auth-footer">Du hast noch kein Konto?</div>', unsafe_allow_html=True)
        if st.button("Registrieren"):
            st.session_state['auth_mode'] = 'signup'
            st.rerun()

    else:
        with st.form("signup_form"):
            st.markdown("<h3 style='text-align:center; color:white;'>Registrieren</h3>", unsafe_allow_html=True)
            st.text_input("Dein Name")
            st.text_input("Username")
            st.text_input("Passwort", type="password")
            
            if st.form_submit_button("Konto erstellen"):
                # Deine Registrierungs-Logik hier...
                pass
        
        st.markdown('<div class="auth-footer">Bereits ein Konto?</div>', unsafe_allow_html=True)
        if st.button("Anmelden"):
            st.session_state['auth_mode'] = 'login'
            st.rerun()
