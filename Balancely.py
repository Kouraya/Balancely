import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import re

# --- 1. SEITEN-KONFIGURATION ---
st.set_page_config(page_title="Balancely", page_icon="⚖️", layout="wide")

# --- 2. CSS (Zentrierung & Clean Eye) ---
st.markdown("""
    <style>
    html, body, [data-testid="stAppViewContainer"] { background-color: #0e1117 !important; }
    [data-testid="InputInstructions"] { display: none !important; }
    [data-testid="stForm"] {
        background-color: #161b22 !important;
        padding: 40px !important;
        border-radius: 12px !important;
        border: 1px solid #30363d !important;
        min-width: 380px !important;
        margin: 0 auto !important;
    }
    div[data-baseweb="input"] { height: 45px !important; background-color: #0d1117 !important; border-radius: 8px !important; }
    input { color: white !important; }
    button[aria-label="Show password"] { background-color: transparent !important; border: none !important; box-shadow: none !important; color: #8b949e !important; }
    button[aria-label="Show password"]:hover { background-color: transparent !important; color: white !important; }
    button[kind="primaryFormSubmit"] { background-color: #1f6feb !important; height: 45px !important; width: 100% !important; font-weight: bold !important; border-radius: 8px !important; }
    div.stButton > button { background: none !important; border: none !important; color: #58a6ff !important; font-weight: 600 !important; padding: 0 !important; margin: 0 !important; }
    .main-title { text-align: center; color: white; font-size: 45px; font-weight: bold; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOGIK-FUNKTIONEN ---
def check_password_strength(pwd):
    if len(pwd) < 6:
        return False, "Passwort muss mind. 6 Zeichen lang sein."
    if not re.search(r"[a-z]", pwd) or not re.search(r"[A-Z]", pwd):
        return False, "Passwort braucht Groß- und Kleinbuchstaben."
    return True, ""

# --- 4. DATENBANK & NAVIGATION ---
conn = st.connection("gsheets", type=GSheetsConnection)

if 'auth_mode' not in st.session_state:
    st.session_state['auth_mode'] = 'login'

# --- 5. INTERFACE ---
st.markdown("<div style='height: 8vh;'></div>", unsafe_allow_html=True)
_, center_col, _ = st.columns([1, 1.1, 1])

with center_col:
    st.markdown("<p class='main-title'>Balancely</p>", unsafe_allow_html=True)

    if st.session_state['auth_mode'] == 'login':
        with st.form("login_form"):
            st.markdown("<h3 style='text-align:center; color:white; margin-top:0;'>Anmelden</h3>", unsafe_allow_html=True)
            user_input = st.text_input("Username")
            pass_input = st.text_input("Password", type="password")
            
            if st.form_submit_button("Login"):
                # Aktuelle Nutzer laden
                df = conn.read(worksheet="users", ttl="0")
                # Prüfen, ob Username und Passwort übereinstimmen
                user_match = df[(df['username'] == user_input) & (df['password'] == pass_input)]
                
                if not user_match.empty:
                    st.success(f"Willkommen zurück, {user_match.iloc[0]['name']}!")
                    # Hier könntest du st.session_state['logged_in'] = True setzen
                else:
                    st.error("Falscher Benutzername oder Passwort.")

        f_left, f_right = st.columns([0.61, 0.39])
        with f_left: st.markdown("<p style='text-align:right; color:#8b949e; font-size:14px; margin-top:8px;'>Du hast noch kein Konto?</p>", unsafe_allow_html=True)
        with f_right:
            if st.button("Registrieren"):
                st.session_state['auth_mode'] = 'signup'
                st.rerun()

    else:
        with st.form("signup_form"):
            st.markdown("<h3 style='text-align:center; color:white; margin-top:0;'>Registrieren</h3>", unsafe_allow_html=True)
            new_name = st.text_input("Dein Name")
            new_user = st.text_input("Benutzername")
            new_pass = st.text_input("Passwort", type="password")
            confirm_pass = st.text_input("Passwort wiederholen", type="password")
            
            if st.form_submit_button("Konto erstellen"):
                # Validierung
                is_strong, msg = check_password_strength(new_pass)
                df_existing = conn.read(worksheet="users", ttl="0")
                
                if new_pass != confirm_pass:
                    st.error("Passwörter stimmen nicht überein!")
                elif not is_strong:
                    st.error(msg)
                elif new_user in df_existing['username'].values:
                    st.error("Dieser Benutzername ist bereits vergeben.")
                else:
                    # DATEN IN GSHEETS SCHREIBEN
                    new_data = pd.DataFrame([{"name": new_name, "username": new_user, "password": new_pass}])
                    updated_df = pd.concat([df_existing, new_data], ignore_index=True)
                    conn.update(worksheet="users", data=updated_df)
                    
                    st.success("Konto erfolgreich erstellt! Du kannst dich jetzt anmelden.")
                    st.balloons()

        f_left, f_right = st.columns([0.58, 0.42])
        with f_left: st.markdown("<p style='text-align:right; color:#8b949e; font-size:14px; margin-top:8px;'>Bereits ein Konto?</p>", unsafe_allow_html=True)
        with f_right:
            if st.button("Anmelden"):
                st.session_state['auth_mode'] = 'login'
                st.rerun()
