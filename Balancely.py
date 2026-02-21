import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import streamlit_authenticator as stauth
import plotly.express as px

# --- 1. SEITEN-KONFIGURATION ---
st.set_page_config(page_title="Balancely", page_icon="⚖️", layout="centered")

# --- 2. INSTAGRAM-STYLE CSS (FIXED) ---
st.markdown("""
    <style>
    /* Hintergrund & Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #000000;
        font-family: 'Inter', sans-serif;
    }

    /* Die zentrale Box */
    [data-testid="stForm"] {
        background-color: #121212;
        padding: 40px;
        border-radius: 10px;
        border: 1px solid #363636;
        max-width: 350px;
        margin: 0 auto;
    }

    /* FIX: Kein Gelb mehr beim Klicken & Font Korrektur */
    input {
        background-color: #121212 !important;
        border: 1px solid #363636 !important;
        border-radius: 3px !important;
        color: white !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    /* Entfernt den gelben/roten Fokus-Rahmen */
    input:focus {
        border-color: #0095f6 !important;
        box-shadow: none !important;
    }

    /* Login Button */
    button[kind="primaryFormSubmit"] {
        background-color: #0095f6 !important;
        border: none !important;
        width: 100% !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        height: 35px;
    }

    /* Logo Styling */
    .logo-font {
        font-size: 45px;
        text-align: center;
        color: white;
        font-weight: 700;
        margin-bottom: 20px;
        letter-spacing: -1px;
    }

    /* Zentrierter Switch-Bereich */
    .auth-footer {
        text-align: center;
        margin-top: 25px;
    }
    
    .footer-text {
        font-size: 14px;
        color: #a8a8a8;
        margin-bottom: -10px;
    }

    /* Stylt den "Link" Button */
    div.stButton > button {
        background: none !important;
        border: none !important;
        color: #0095f6 !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        padding: 0 !important;
        display: inline-block !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. VERBINDUNG & DATEN ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data(sheet_name):
    return conn.read(worksheet=sheet_name, ttl="0")

user_db = get_data("users")

credentials = {'usernames': {}}
for _, row in user_db.iterrows():
    credentials['usernames'][str(row['username'])] = {
        'name': str(row['name']),
        'password': str(row['password']) 
    }

authenticator = stauth.Authenticate(credentials, 'balancely_cookie', 'auth_key', cookie_expiry_days=30)

if 'auth_mode' not in st.session_state:
    st.session_state['auth_mode'] = 'login'

# --- 4. AUTH-INTERFACE (LOGIN / REGISTRIERUNG) ---
if not st.session_state.get("authentication_status"):
    st.markdown('<p class="logo-font">Balancely</p>', unsafe_allow_html=True)

    if st.session_state['auth_mode'] == 'login':
        # Login Formular
        authenticator.login(location='main')
        
        # Footer unter dem Formular
        st.markdown('<div class="auth-footer"><p class="footer-text">Du hast noch kein Konto?</p></div>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2: # Zentriert den Button
            if st.button("Registrieren"):
                st.session_state['auth_mode'] = 'signup'
                st.rerun()

    else:
        # Registrierung Formular
        with st.form("reg_form"):
            st.markdown("<p style='text-align:center; color:#a8a8a8; font-size:14px;'>Melde dich an, um deine Finanzen zu verwalten.</p>", unsafe_allow_html=True)
            new_name = st.text_input("Vollständiger Name")
            new_user = st.text_input("Benutzername")
            new_pw = st.text_input("Passwort", type="password")
            if st.form_submit_button("Registrieren"):
                if new_name and new_user and new_pw:
                    if new_user in user_db['username'].astype(str).values:
                        st.error("Nutzername vergeben.")
                    else:
                        new_row = pd.DataFrame([{"name": new_name, "username": new_user, "password": new_pw}])
                        updated = pd.concat([user_db, new_row], ignore_index=True)
                        conn.update(worksheet="users", data=updated)
                        st.success("Konto erstellt!")
                        st.session_state['auth_mode'] = 'login'
                        st.rerun()
        
        st.markdown('<div class="auth-footer"><p class="footer-text">Du hast bereits ein Konto?</p></div>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("Anmelden"):
                st.session_state['auth_mode'] = 'login'
                st.rerun()

# --- 5. DASHBOARD ---
else:
    authenticator.logout('Abmelden', 'sidebar')
    st.title(f"Moin, {st.session_state['name']} ⚖️")
    
    # Hier folgen deine Charts und Tabellen...
    st.info("Dein Dashboard lädt...")
