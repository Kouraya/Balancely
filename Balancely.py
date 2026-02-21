import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import streamlit_authenticator as stauth

# --- 1. SEITEN-KONFIGURATION ---
st.set_page_config(page_title="Balancely", page_icon="⚖️", layout="wide")

# --- 2. DAS ULTIMATIVE CSS (ZENTRIERT & GLEICHMÄSSIG) ---
st.markdown("""
    <style>
    /* Hintergrund & Font */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #0e1117 !important;
    }

    /* 1. Alles vertikal und horizontal zentrieren */
    [data-testid="stMain"] [data-testid="stVerticalBlock"] {
        align-items: center !important;
        justify-content: center !important;
    }

    /* 2. Die Login-Box fixieren */
    [data-testid="stForm"] {
        background-color: #161b22 !important;
        padding: 40px !important;
        border-radius: 12px !important;
        border: 1px solid #30363d !important;
        width: 380px !important;
        margin: 0 auto !important;
    }

    /* 3. Zeilenhöhe für alle Felder erzwingen */
    div[data-baseweb="input"] {
        height: 45px !important;
        border-radius: 6px !important;
        background-color: #0d1117 !important;
    }
    
    input {
        height: 45px !important;
        color: white !important;
    }

    /* 4. Kein Gelb! Nur Dashboard-Blau */
    div[data-baseweb="input"]:focus-within {
        border-color: #1f6feb !important;
        box-shadow: 0 0 0 1px #1f6feb !important;
    }

    /* 5. Buttons Stylen */
    button[kind="primaryFormSubmit"] {
        background-color: #1f6feb !important;
        height: 45px !important;
        width: 100% !important;
        border: none !important;
        font-weight: bold !important;
        margin-top: 10px !important;
    }

    /* 6. Footer (Noch kein Konto?) */
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

    /* Registrieren-Link */
    div.stButton > button {
        background: none !important;
        border: none !important;
        color: #58a6ff !important;
        margin: 0 auto !important;
        display: block !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATEN & AUTH ---
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

# --- 4. DAS INTERFACE ---
# Spacer für vertikale Mitte
st.write("##") 
st.write("##")

if not st.session_state.get("authentication_status"):
    
    st.markdown("<h1 style='text-align: center; color: white;'>Balancely</h1>", unsafe_allow_html=True)

    # Wir nutzen EINE zentrale Spalte für die Box
    col_main = st.columns([1, 2, 1])[1]

    with col_main:
        if st.session_state['auth_mode'] == 'login':
            # Das Login-Feld vom Authenticator (bereits stabil gebaut)
            authenticator.login(location='main')
            
            st.markdown('<div class="auth-footer"><p class="footer-text">Du hast noch kein Konto?</p></div>', unsafe_allow_html=True)
            if st.button("Registrieren"):
                st.session_state['auth_mode'] = 'signup'
                st.rerun()

        else:
            with st.form("signup_form"):
                st.markdown("<h3 style='text-align:center; color:white;'>Registrieren</h3>", unsafe_allow_html=True)
                # Die Keys müssen eindeutig sein, um Fehler zu vermeiden
                name = st.text_input("Name", key="reg_name")
                user = st.text_input("Benutzername", key="reg_user")
                pw = st.text_input("Passwort", type="password", key="reg_pass")
                
                if st.form_submit_button("Konto erstellen"):
                    if name and user and pw:
                        new_row = pd.DataFrame([{"name": name, "username": user, "password": pw}])
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
    authenticator.logout('Abmelden', 'sidebar')
    st.title("⚖️ Dashboard")
    # Hier dein Finanz-Code...
