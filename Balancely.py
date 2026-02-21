import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import re

# --- 1. SEITEN-KONFIGURATION ---
st.set_page_config(page_title="Balancely", page_icon="⚖️", layout="wide")

# --- 2. CSS (Inklusive des "reinen" Auges und Zentrierung) ---
st.markdown("""
    <style>
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #0e1117 !important;
    }

    [data-testid="InputInstructions"] {
        display: none !important;
    }

    [data-testid="stForm"] {
        background-color: #161b22 !important;
        padding: 40px !important;
        border-radius: 12px !important;
        border: 1px solid #30363d !important;
        min-width: 380px !important;
        margin: 0 auto !important;
    }

    div[data-baseweb="input"] {
        height: 45px !important;
        background-color: #0d1117 !important;
        border-radius: 8px !important;
    }
    
    input {
        color: white !important;
    }

    /* Das "reine" Auge ohne graue Box */
    button[aria-label="Show password"] {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        color: #8b949e !important;
    }

    button[aria-label="Show password"]:hover {
        background-color: transparent !important;
        color: white !important;
    }

    button[kind="primaryFormSubmit"] {
        background-color: #1f6feb !important;
        height: 45px !important;
        width: 100% !important;
        font-weight: bold !important;
        border-radius: 8px !important;
    }

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

# --- 3. HELFER-FUNKTION FÜR PASSWORT-CHECK ---
def check_password_strength(pwd):
    if len(pwd) < 6:
        return False, "Das Passwort muss mindestens 6 Zeichen lang sein."
    if not re.search(r"[a-z]", pwd):
        return False, "Das Passwort muss mindestens einen Kleinbuchstaben enthalten."
    if not re.search(r"[A-Z]", pwd):
        return False, "Das Passwort muss mindestens einen Großbuchstaben enthalten."
    return True, ""

# --- 4. DATEN & NAVIGATION ---
conn = st.connection("gsheets", type=GSheetsConnection)

if 'auth_mode' not in st.session_state:
    st.session_state['auth_mode'] = 'login'

# --- 5. INTERFACE ---
st.markdown("<div style='height: 8vh;'></div>", unsafe_allow_html=True)

_, center_col, _ = st.columns([1, 1.1, 1])

with center_col:
    st.markdown("<p class='main-title'>Balancely</p>", unsafe_allow_html=True)

    if st.session_state['auth_mode'] == 'login':
        # (Login-Formular bleibt wie gehabt)
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
        # ERWEITERTES REGISTRIERUNGS-FORMULAR
        with st.form("signup_form"):
            st.markdown("<h3 style='text-align:center; color:white; margin-top:0;'>Registrieren</h3>", unsafe_allow_html=True)
            new_name = st.text_input("Dein Name", key="reg_name")
            new_user = st.text_input("Benutzername", key="reg_user")
            
            # Die beiden Passwortfelder
            new_pass = st.text_input("Passwort", type="password", key="reg_pass", help="Mind. 6 Zeichen, Groß- & Kleinbuchstaben")
            confirm_pass = st.text_input("Passwort wiederholen", type="password", key="reg_pass_confirm")
            
            if st.form_submit_button("Konto erstellen"):
                # 1. Check: Stimmen sie überein?
                if new_pass != confirm_pass:
                    st.error("Die Passwörter stimmen nicht überein!")
                else:
                    # 2. Check: Erfüllt es die Kriterien?
                    is_strong, message = check_password_strength(new_pass)
                    if not is_strong:
                        st.error(message)
                    else:
                        st.success("Konto wird erstellt...")
                        # Hier würde dann der GSheets-Upload folgen
        
        f_left, f_right = st.columns([0.58, 0.42])
        with f_left:
            st.markdown("<p style='text-align:right; color:#8b949e; font-size:14px; margin-top:8px;'>Bereits ein Konto?</p>", unsafe_allow_html=True)
        with f_right:
            if st.button("Anmelden"):
                st.session_state['auth_mode'] = 'login'
                st.rerun()
