import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- 1. SEITEN-KONFIGURATION ---
st.set_page_config(page_title="Balancely", page_icon="⚖️", layout="wide")

# --- 2. CSS FÜR ABSOLUTE ZENTRIERUNG ---
st.markdown("""
    <style>
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #0e1117 !important;
    }

    /* Versteckt "Press Enter" */
    [data-testid="InputInstructions"] {
        display: none !important;
    }

    /* Zentriert den Inhalt der mittleren Spalte */
    [data-testid="column"] {
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
    }

    /* Die Form-Box */
    [data-testid="stForm"] {
        background-color: #161b22 !important;
        padding: 40px !important;
        border-radius: 12px !important;
        border: 1px solid #30363d !important;
        width: 400px !important;
    }

    /* Input Styling */
    div[data-baseweb="input"] {
        height: 45px !important;
        background-color: #0d1117 !important;
        border-radius: 8px !important;
    }
    
    input:focus {
        border-color: #1f6feb !important;
        box-shadow: 0 0 0 1px #1f6feb !important;
    }

    /* Der "Echte" Zentrierungs-Trick für den Footer */
    .centered-footer {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 400px; /* Exakt Box-Breite */
        margin-top: 20px;
        color: #8b949e;
        font-size: 14px;
        white-space: nowrap;
    }

    /* Button als Link-Style */
    div.stButton > button {
        background: none !important;
        border: none !important;
        color: #58a6ff !important;
        font-weight: 600 !important;
        padding: 0 0 0 5px !important; /* Nur links kleiner Abstand zum Text */
        margin: 0 !important;
        font-size: 14px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATEN ---
conn = st.connection("gsheets", type=GSheetsConnection)

if 'auth_mode' not in st.session_state:
    st.session_state['auth_mode'] = 'login'

# --- 4. INTERFACE ---
st.markdown("<div style='height: 10vh;'></div>", unsafe_allow_html=True)

# Wir nutzen Spalten nur für die grobe Positionierung (Box in die Mitte)
_, center_col, _ = st.columns([1, 1.2, 1])

with center_col:
    st.markdown("<h1 style='text-align: center; color: white;'>Balancely</h1>", unsafe_allow_html=True)

    if st.session_state['auth_mode'] == 'login':
        with st.form("login_form"):
            st.markdown("<h3 style='text-align:center; color:white;'>Login</h3>", unsafe_allow_html=True)
            st.text_input("Username")
            st.text_input("Password", type="password")
            st.form_submit_button("Anmelden")

        # DER FIX: Ein flacher Container für Text + Button
        st.markdown('<div class="centered-footer">Du hast noch kein Konto?</div>', unsafe_allow_html=True)
        # Der Button wird durch das CSS automatisch unter dem div zentriert, 
        # oder wir rücken ihn optisch direkt dran:
        if st.button("Registrieren"):
            st.session_state['auth_mode'] = 'signup'
            st.rerun()

    else:
        with st.form("signup_form"):
            st.markdown("<h3 style='text-align:center; color:white;'>Registrieren</h3>", unsafe_allow_html=True)
            st.text_input("Dein Name")
            st.text_input("Username")
            st.text_input("Passwort", type="password")
            st.form_submit_button("Konto erstellen")
        
        st.markdown('<div class="centered-footer">Bereits ein Konto?</div>', unsafe_allow_html=True)
        if st.button("Anmelden"):
            st.session_state['auth_mode'] = 'login'
            st.rerun()
