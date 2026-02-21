import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import re
import hashlib  # Für die Verschlüsselung

# --- 1. HILFSFUNKTIONEN FÜR SICHERHEIT ---
def make_hashes(password):
    """Erstellt einen unleserlichen SHA256-Hash aus dem Passwort."""
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    """Vergleicht das eingegebene Passwort mit dem gespeicherten Hash."""
    if make_hashes(password) == hashed_text:
        return True
    return False

def check_password_strength(pwd):
    if len(pwd) < 6: return False, "Passwort zu kurz (min. 6)."
    if not re.search(r"[a-z]", pwd) or not re.search(r"[A-Z]", pwd): 
        return False, "Braucht Groß/Kleinbuchstaben."
    return True, ""

# --- 2. SEITEN-KONFIGURATION & CSS ---
st.set_page_config(page_title="Balancely", page_icon="⚖️", layout="wide")
st.markdown("""
    <style>
    html, body, [data-testid="stAppViewContainer"] { background-color: #0e1117 !important; }
    [data-testid="stForm"] {
        background-color: #161b22 !important;
        padding: 40px !important;
        border-radius: 12px !important;
        border: 1px solid #30363d !important;
        min-width: 380px !important;
        margin: 0 auto !important;
    }
    input { color: white !important; }
    div[data-baseweb="input"] { background-color: #0d1117 !important; border-radius: 8px !important; }
    button[aria-label="Show password"] { background-color: transparent !important; border: none !important; color: #8b949e !important; }
    button[kind="primaryFormSubmit"] { background-color: #1f6feb !important; width: 100% !important; border-radius: 8px !important; }
    div.stButton > button { background: none !important; border: none !important; color: #58a6ff !important; font-weight: 600 !important; }
    .main-title { text-align: center; color: white; font-size: 45px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SESSION STATE ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'user_name' not in st.session_state: st.session_state['user_name'] = ""
if 'auth_mode' not in st.session_state: st.session_state['auth_mode'] = 'login'

conn = st.connection("gsheets", type=GSheetsConnection)

# --- 4. HAUPT-LOGIK ---

if st.session_state['logged_in']:
    # DASHBOARD
    st.markdown(f"## Willkommen im Dashboard, {st.session_state['user_name']}! ⚖️")
    if st.button("Abmelden"):
        st.session_state['logged_in'] = False
        st.rerun()
else:
    # AUTHENTIFIZIERUNG
    st.markdown("<div style='height: 8vh;'></div>", unsafe_allow_html=True)
    _, center_col, _ = st.columns([1, 1.1, 1])

    with center_col:
        st.markdown("<p class='main-title'>Balancely</p>", unsafe_allow_html=True)

        if st.session_state['auth_mode'] == 'login':
            with st.form("login_form"):
                st.markdown("<h3 style='text-align:center; color:white;'>Anmelden</h3>", unsafe_allow_html=True)
                user_input = st.text_input("Username")
                pass_input = st.text_input("Password", type="password")
                if st.form_submit_button("Login"):
                    df = conn.read(worksheet="users", ttl="0")
                    # Filtere nach Username
                    user_data = df[df['username'] == user_input]
                    
                    if not user_data.empty:
                        # Vergleiche Hash aus GSheet mit Hash der Eingabe
                        stored_password_hash = user_data.iloc[0]['password']
                        if check_hashes(pass_input, stored_password_hash):
                            st.session_state['logged_in'] = True
                            st.session_state['user_name'] = user_data.iloc[0]['name']
                            st.rerun()
                        else:
                            st.error("Passwort falsch.")
                    else:
                        st.error("Benutzer nicht gefunden.")

            if st.button("Noch kein Konto? Registrieren"):
                st.session_state['auth_mode'] = 'signup'
                st.rerun()

        else:
            with st.form("signup_form"):
                st.markdown("<h3 style='text-align:center; color:white;'>Registrieren</h3>", unsafe_allow_html=True)
                n_name = st.text_input("Name")
                n_user = st.text_input("Username")
                n_pass = st.text_input("Passwort", type="password")
                c_pass = st.text_input("Wiederholen", type="password")
                
                if st.form_submit_button("Konto erstellen"):
                    is_strong, msg = check_password_strength(n_pass)
                    df_ex = conn.read(worksheet="users", ttl="0")
                    
                    if n_pass != c_pass: st.error("Passwörter ungleich!")
                    elif not is_strong: st.error(msg)
                    elif n_user in df_ex['username'].values: st.error("Username vergeben.")
                    else:
                        # HASH ERSTELLEN BEVOR ES INS SHEET GEHT
                        hashed_password = make_hashes(n_pass)
                        new_row = pd.DataFrame([{"name": n_name, "username": n_user, "password": hashed_password}])
                        conn.update(worksheet="users", data=pd.concat([df_ex, new_row], ignore_index=True))
                        st.success("Erfolg! Bitte einloggen.")
            
            if st.button("Zurück zum Login"):
                st.session_state['auth_mode'] = 'login'
                st.rerun()
