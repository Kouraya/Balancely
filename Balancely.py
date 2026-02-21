import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import re

# --- 1. SEITEN-KONFIGURATION ---
st.set_page_config(page_title="Balancely", page_icon="⚖️", layout="wide")

# --- 2. ERWEITERTES CSS FÜR DASHBOARD-LOOK ---
st.markdown("""
    <style>
    html, body, [data-testid="stAppViewContainer"] { background-color: #0e1117 !important; }
    [data-testid="InputInstructions"] { display: none !important; }
    
    /* Login-Box Styling */
    [data-testid="stForm"] {
        background-color: #161b22 !important;
        padding: 40px !important;
        border-radius: 12px !important;
        border: 1px solid #30363d !important;
        min-width: 380px !important;
        margin: 0 auto !important;
    }
    
    /* Dashboard Kacheln (Metrics) */
    [data-testid="stMetricValue"] { color: #58a6ff !important; font-weight: bold !important; }
    div[data-testid="metric-container"] {
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        padding: 15px !important;
        border-radius: 10px !important;
    }

    /* Input & Auge Fix */
    div[data-baseweb="input"] { height: 45px !important; background-color: #0d1117 !important; border-radius: 8px !important; }
    input { color: white !important; }
    button[aria-label="Show password"] { background-color: transparent !important; border: none !important; color: #8b949e !important; }
    
    /* Buttons */
    button[kind="primaryFormSubmit"] { background-color: #1f6feb !important; width: 100% !important; border-radius: 8px !important; }
    
    /* Logout & Footer Buttons */
    div.stButton > button {
        background: none !important; border: none !important; color: #58a6ff !important;
        font-weight: 600 !important; padding: 0 !important;
    }

    .main-title { text-align: center; color: white; font-size: 45px; font-weight: bold; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SESSION STATE ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'user_name' not in st.session_state: st.session_state['user_name'] = ""
if 'auth_mode' not in st.session_state: st.session_state['auth_mode'] = 'login'

# --- 4. FUNKTIONEN ---
def check_password_strength(pwd):
    if len(pwd) < 6: return False, "Passwort zu kurz (min. 6)."
    if not re.search(r"[a-z]", pwd) or not re.search(r"[A-Z]", pwd): return False, "Braucht Groß/Kleinbuchstaben."
    return True, ""

conn = st.connection("gsheets", type=GSheetsConnection)

# --- 5. HAUPT-LOGIK ---

if st.session_state['logged_in']:
    # --- DASHBOARD BEREICH ---
    col_title, col_logout = st.columns([0.9, 0.1])
    with col_title:
        st.markdown(f"## Willkommen, {st.session_state['user_name']}! ⚖️")
    with col_logout:
        if st.button("Abmelden"):
            st.session_state['logged_in'] = False
            st.rerun()

    st.markdown("---")

    # Beispiel-Inhalt für dein Dashboard
    st.subheader("Deine Übersicht")
    m1, m2, m3 = st.columns(3)
    m1.metric("Gesamtbilanz", "1.240 €", "+12%")
    m2.metric("Offene Posten", "3", "-1")
    m3.metric("Status", "Aktiv")

    st.markdown("### Letzte Aktivitäten")
    # Dummy Daten für die Tabelle
    data = pd.DataFrame({
        "Datum": ["21.02.2026", "20.02.2026", "19.02.2026"],
        "Kategorie": ["Einkauf", "Gehalt", "Freizeit"],
        "Betrag": ["-45,00 €", "+2.100,00 €", "-12,50 €"]
    })
    st.table(data)

else:
    # --- LOGIN / REGISTRIERUNG (wie bisher) ---
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
                    df = conn.read(worksheet="users", ttl="0")
                    match = df[(df['username'] == user_input) & (df['password'] == pass_input)]
                    if not match.empty:
                        st.session_state['logged_in'] = True
                        st.session_state['user_name'] = match.iloc[0]['name']
                        st.rerun()
                    else:
                        st.error("Daten inkorrekt.")

            f_left, f_right = st.columns([0.61, 0.39])
            with f_left: st.markdown("<p style='text-align:right; color:#8b949e; font-size:14px; margin-top:8px;'>Neu hier?</p>", unsafe_allow_html=True)
            with f_right:
                if st.button("Registrieren"):
                    st.session_state['auth_mode'] = 'signup'
                    st.rerun()

        else:
            with st.form("signup_form"):
                st.markdown("<h3 style='text-align:center; color:white; margin-top:0;'>Registrieren</h3>", unsafe_allow_html=True)
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
                        new_row = pd.DataFrame([{"name": n_name, "username": n_user, "password": n_pass}])
                        conn.update(worksheet="users", data=pd.concat([df_ex, new_row], ignore_index=True))
                        st.success("Erfolg! Bitte einloggen.")
            
            if st.button("Zurück zum Login"):
                st.session_state['auth_mode'] = 'login'
                st.rerun()
