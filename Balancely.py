import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import streamlit_authenticator as stauth

# --- 1. SEITEN-KONFIGURATION ---
st.set_page_config(page_title="Balancely", page_icon="⚖️", layout="wide")

# --- 2. CSS FÜR ABSOLUTE ZENTRIERUNG & CLEAN LOOK ---
st.markdown("""
    <style>
    /* Hintergrundfarbe */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #0e1117 !important;
    }

    /* 1. Haupt-Container auf volle Höhe und Zentrierung zwingen */
    [data-testid="stMain"] [data-testid="stVerticalBlock"] {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        width: 100% !important;
    }

    /* 2. "Press Enter to submit" & Hilfstexte verstecken */
    [data-testid="InputInstructions"] {
        display: none !important;
    }

    /* 3. Die Login-Box Stylen (Kein Margin-Left nötig durch Flex) */
    [data-testid="stForm"] {
        background-color: #161b22 !important;
        padding: 40px !important;
        border-radius: 12px !important;
        border: 1px solid #30363d !important;
        width: 400px !important;
        display: flex !important;
        flex-direction: column !important;
    }

    /* 4. Einheitliche Felder & Dashboard-Farben */
    div[data-baseweb="input"] {
        height: 48px !important;
        background-color: #0d1117 !important;
        border-radius: 8px !important;
    }
    
    input {
        color: white !important;
    }

    /* Fokus-Farbe (Blau statt Gelb) */
    div[data-baseweb="input"]:focus-within {
        border-color: #1f6feb !important;
        box-shadow: 0 0 0 1px #1f6feb !important;
    }

    /* Button Styling (Dashboard Blau) */
    button[kind="primaryFormSubmit"] {
        background-color: #1f6feb !important;
        height: 45px !important;
        width: 100% !important;
        border: none !important;
        font-weight: bold !important;
        border-radius: 8px !important;
    }

    /* 5. Footer (Zentrierter Text unter der Box) */
    .auth-footer {
        text-align: center !important;
        width: 400px !important; /* Exakt so breit wie die Form */
        margin-top: 25px !important;
    }
    
    .footer-text {
        color: #8b949e !important;
        font-size: 14px !important;
        margin-bottom: 5px !important;
    }

    /* Registrieren-Link als cleaner Button */
    div.stButton > button {
        background: none !important;
        border: none !important;
        color: #58a6ff !important;
        font-weight: 600 !important;
        margin: 0 auto !important;
        display: block !important;
        padding: 0 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATEN & LOGIK ---
conn = st.connection("gsheets", type=GSheetsConnection)
user_db = conn.read(worksheet="users", ttl="0")

if 'auth_mode' not in st.session_state:
    st.session_state['auth_mode'] = 'login'

# --- 4. INTERFACE ---
# Vertikaler Abstand für die "echte" Mitte
st.markdown("<div style='height: 12vh;'></div>", unsafe_allow_html=True)

# Überschrift zentriert
st.markdown("<h1 style='text-align: center; color: white; font-size: 45px; margin-bottom: 30px;'>Balancely</h1>", unsafe_allow_html=True)

# Hier nutzen wir jetzt keine Spalten mehr im Python-Code, 
# da das CSS die Zentrierung übernimmt!
if st.session_state['auth_mode'] == 'login':
    with st.form("login_form"):
        st.markdown("<h3 style='text-align:center; color:white; margin-top:0;'>Anmelden</h3>", unsafe_allow_html=True)
        st.text_input("Username")
        st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            # Login Logik hier
            pass

    # Der Footer-Bereich ist durch die CSS-Klasse "auth-footer" und 
    # die Breite von 400px perfekt unter der Box ausgerichtet.
    st.markdown('<div class="auth-footer"><p class="footer-text">Du hast noch kein Konto?</p></div>', unsafe_allow_html=True)
    if st.button("Jetzt registrieren"):
        st.session_state['auth_mode'] = 'signup'
        st.rerun()

else:
    with st.form("signup_form"):
        st.markdown("<h3 style='text-align:center; color:white; margin-top:0;'>Konto erstellen</h3>", unsafe_allow_html=True)
        st.text_input("Dein Name", key="s_name")
        st.text_input("Benutzername", key="s_user")
        st.text_input("Passwort", type="password", key="s_pw")
        if st.form_submit_button("Registrieren"):
            # Registrierungs-Logik hier
            pass
    
    st.markdown('<div class="auth-footer"><p class="footer-text">Bereits ein Konto?</p></div>', unsafe_allow_html=True)
    if st.button("Zum Login"):
        st.session_state['auth_mode'] = 'login'
        st.rerun()
