import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import streamlit_authenticator as stauth

# --- 1. SEITEN-KONFIGURATION ---
st.set_page_config(page_title="Balancely", page_icon="⚖️", layout="wide")

# --- 2. DAS ULTIMATIVE ZENTRIERUNGS- & DESIGN-CSS ---
st.markdown("""
    <style>
    /* 1. Hintergrund & Font-Zwang */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #0e1117 !important;
        font-family: 'Source Sans Pro', sans-serif !important;
    }

    /* 2. Zentrierung des Haupt-Containers */
    [data-testid="stVerticalBlock"] > div {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }

    /* 3. Die Form-Box (Card) */
    [data-testid="stForm"] {
        background-color: #161b22 !important;
        padding: 2.5rem !important;
        border-radius: 10px !important;
        border: 1px solid #30363d !important;
        width: 350px !important;
        margin: 0 auto !important;
    }

    /* 4. FIX: KEIN GELB, KEIN ROT - NUR BLAU */
    input {
        background-color: #0d1117 !important;
        border: 1px solid #30363d !important;
        border-radius: 5px !important;
        color: white !important;
    }
    
    /* Entfernt den gelben Streamlit-Fokus komplett */
    input:focus, .st-ae:focus {
        border-color: #1f6feb !important;
        box-shadow: 0 0 0 1px #1f6feb !important;
        outline: none !important;
    }

    /* 5. Button Styling (Dashboard Blau) */
    button[kind="primaryFormSubmit"] {
        background-color: #1f6feb !important;
        border: none !important;
        width: 100% !important;
        color: white !important;
        font-weight: bold !important;
    }

    /* 6. Text & Links unter der Box */
    .auth-footer {
        text-align: center;
        width: 350px;
        margin-top: 20px;
    }
    
    .footer-text {
        color: #8b949e;
        font-size: 14px;
        margin-bottom: 5px;
    }

    /* Stylt den Umschalt-Button als Link */
    div.stButton > button {
        background: none !important;
        border: none !important;
        color: #58a6ff !important;
        text-decoration: none !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        margin: 0 auto !important;
        display: block !important;
    }
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
if not st.session_state.get("authentication_status"):
    
    # Unsichtbarer Platzhalter für vertikale Zentrierung
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; color: white;'>Balancely</h1>", unsafe_allow_html=True)

    if st.session_state['auth_mode'] == 'login':
        # Das Login-Formular (Breite wird durch CSS auf 350px gesetzt)
        authenticator.login(location='main')
        
        # Footer exakt darunter
        st.markdown('<div class="auth-footer"><p class="footer-text">Du hast noch kein Konto?</p></div>', unsafe_allow_html=True)
        if st.button("Registrieren"):
            st.session_state['auth_mode'] = 'signup'
            st.rerun()

    else:
        with st.form("reg_form"):
            st.markdown("<h3 style='text-align:center; color:white;'>Registrieren</h3>", unsafe_allow_html=True)
            new_name = st.text_input("Name")
            new_user = st.text_input("Benutzername")
            new_pw = st.text_input("Passwort", type="password")
            if st.form_submit_button("Konto erstellen"):
                if new_name and new_user and new_pw:
                    # Registrierungs-Logik...
                    new_row = pd.DataFrame([{"name": new_name, "username": new_user, "password": new_pw}])
                    updated = pd.concat([user_db, new_row], ignore_index=True)
                    conn.update(worksheet="users", data=updated)
                    st.success("Konto erstellt!")
                    st.session_state['auth_mode'] = 'login'
                    st.rerun()
        
        st.markdown('<div class="auth-footer"><p class="footer-text">Bereits ein Konto?</p></div>', unsafe_allow_html=True)
        if st.button("Anmelden"):
            st.session_state['auth_mode'] = 'login'
            st.rerun()

# --- 5. DASHBOARD ---
else:
    # Hier startet dein eigentliches Dashboard mit den gleichen Farben
    authenticator.logout('Abmelden', 'sidebar')
    st.title(f"Willkommen, {st.session_state['name']}")
    # ... Rest des Codes
