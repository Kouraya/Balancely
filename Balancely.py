import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import re
import hashlib
import numpy as np # Für die Grafik-Beispieldaten

# --- 1. SEITEN-KONFIGURATION ---
st.set_page_config(page_title="Balancely", page_icon="⚖️", layout="wide")

# --- 2. HILFSFUNKTIONEN ---
def make_hashes(text):
    return hashlib.sha256(str.encode(text)).hexdigest()

def check_password_strength(pwd):
    if len(pwd) < 6: return False, "Passwort muss mind. 6 Zeichen lang sein."
    if not re.search(r"[a-z]", pwd) or not re.search(r"[A-Z]", pwd): 
        return False, "Passwort braucht Groß- und Kleinbuchstaben."
    return True, ""

def validate_full_name(name):
    parts = name.strip().split()
    if len(parts) < 2:
        return False, "Bitte gib deinen vollständigen Vor- und Nachnamen ein."
    return True, ""

# --- 3. CSS (Individuelles Styling) ---
st.markdown("""
    <style>
    html, body, [data-testid="stAppViewContainer"] { background-color: #0e1117 !important; }
    [data-testid="InputInstructions"] { display: none !important; }
    
    /* Login/Register Form */
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
    
    /* Das Auge ohne Hitbox */
    button[aria-label="Show password"] { background-color: transparent !important; border: none !important; color: #8b949e !important; }
    
    /* Buttons */
    button[kind="primaryFormSubmit"] { background-color: #1f6feb !important; width: 100% !important; border-radius: 8px !important; font-weight: bold !important; }
    
    /* Sidebar/Navigation Styling */
    [data-testid="stSidebar"] { background-color: #161b22 !important; }
    
    .main-title { text-align: center; color: white; font-size: 45px; font-weight: bold; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. SESSION STATE ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'user_name' not in st.session_state: st.session_state['user_name'] = ""
if 'auth_mode' not in st.session_state: st.session_state['auth_mode'] = 'login'

conn = st.connection("gsheets", type=GSheetsConnection)

# --- 5. HAUPT-LOGIK ---

if st.session_state['logged_in']:
    # --- DASHBOARD NAVIGATION (SIDEBAR) ---
    with st.sidebar:
        st.title("Balancely ⚖️")
        st.write(f"Angemeldet als: **{st.session_state['user_name']}**")
        menu = st.radio("Menü", ["Dashboard", "Statistiken", "Einstellungen"])
        
        if st.button("Abmelden"):
            st.session_state['logged_in'] = False
            st.rerun()

    # --- INHALT BASIEREND AUF AUSWAHL ---
    if menu == "Dashboard":
        st.title(f"Willkommen, {st.session_state['user_name']}!") # Ohne @
        
        # Metriken mit Grafiken
        m1, m2, m3 = st.columns(3)
        m1.metric("Bilanz", "1.450 €", "8%")
        m2.metric("Ausgaben", "420 €", "-2%")
        m3.metric("Sparrate", "25%", "1.5%")
        
        st.markdown("### Verlauf")
        chart_data = pd.DataFrame(np.random.randn(20, 3), columns=['Einnahmen', 'Ausgaben', 'Puffer'])
        st.line_chart(chart_data)

    elif menu == "Statistiken":
        st.title("Deine Analysen")
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.write("Verteilung der Kategorien")
            st.bar_chart(np.random.rand(5))
        
        with col_right:
            st.write("Monatliche Entwicklung")
            st.area_chart(np.random.randn(10, 2))

    elif menu == "Einstellungen":
        st.title("Kontoeinstellungen")
        st.subheader("Sicherheit")
        
        with st.expander("Gefahrenzone: Account löschen"):
            st.error("Achtung: Alle Daten werden dauerhaft aus dem Google Sheet entfernt.")
            if st.button("Meinen Account jetzt unwiderruflich löschen"):
                df_current = conn.read(worksheet="users", ttl="0")
                df_updated = df_current[df_current['username'] != st.session_state['user_name']]
                conn.update(worksheet="users", data=df_updated)
                
                st.session_state['logged_in'] = False
                st.rerun()

else:
    # --- LOGIN / REGISTRIERUNG ---
    st.markdown("<div style='height: 8vh;'></div>", unsafe_allow_html=True)
    _, center_col, _ = st.columns([1, 1.1, 1])

    with center_col:
        st.markdown("<p class='main-title'>Balancely</p>", unsafe_allow_html=True)

        if st.session_state['auth_mode'] == 'login':
            with st.form("login_form"):
                st.markdown("<h3 style='text-align:center; color:white;'>Anmelden</h3>", unsafe_allow_html=True)
                u_input = st.text_input("Username")
                p_input = st.text_input("Password", type="password")
                if st.form_submit_button("Anmelden"):
                    df = conn.read(worksheet="users", ttl="0")
                    user_data = df[df['username'] == u_input]
                    if not user_data.empty and make_hashes(p_input) == user_data.iloc[0]['password']:
                        st.session_state['logged_in'] = True
                        st.session_state['user_name'] = u_input
                        st.rerun()
                    else: st.error("Logindaten nicht korrekt.")

            if st.button("Registrieren"):
                st.session_state['auth_mode'] = 'signup'
                st.rerun()

        else:
            with st.form("signup_form"):
                st.markdown("<h3 style='text-align:center; color:white;'>Registrieren</h3>", unsafe_allow_html=True)
                n_name = st.text_input("Vor- und Nachname")
                n_user = st.text_input("Username")
                n_pass = st.text_input("Passwort", type="password")
                c_pass = st.text_input("Passwort wiederholen", type="password")
                
                if st.form_submit_button("Konto erstellen"):
                    name_ok, name_msg = validate_full_name(n_name)
                    pwd_ok, pwd_msg = check_password_strength(n_pass)
                    df_ex = conn.read(worksheet="users", ttl="0")
                    
                    if not name_ok: st.error(name_msg)
                    elif n_pass != c_pass: st.error("Die Passwörter stimmen nicht überein!")
                    elif not pwd_ok: st.error(pwd_msg)
                    elif n_user in df_ex['username'].values: st.error("Username vergeben.")
                    else:
                        new_row = pd.DataFrame([{
                            "name": make_hashes(n_name), 
                            "username": n_user, 
                            "password": make_hashes(n_pass)
                        }])
                        conn.update(worksheet="users", data=pd.concat([df_ex, new_row], ignore_index=True))
                        st.success("Erfolg! Bitte einloggen.")
            
            if st.button("Zurück zum Login"):
                st.session_state['auth_mode'] = 'login'
                st.rerun()
