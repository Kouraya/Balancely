import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import re
import hashlib
import numpy as np

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
    return len(parts) >= 2, "Bitte gib deinen vollständigen Vor- und Nachnamen ein."

# --- 3. EXKLUSIVES DESIGN (Hintergrund, Titel & Fixes) ---
st.markdown("""
    <style>
    /* 1. Edler Hintergrund-Gradient */
    [data-testid="stAppViewContainer"] {
        background: radial-gradient(circle at top right, #1e293b, #0f172a, #020617) !important;
    }

    /* 2. Titel-Styling (Glow & Font) */
    .main-title {
        text-align: center;
        font-family: 'Inter', sans-serif;
        color: #f8fafc;
        font-size: 58px;
        font-weight: 800;
        letter-spacing: -2px;
        margin-bottom: 0px;
        text-shadow: 0 0 20px rgba(56, 189, 248, 0.3);
    }
    .sub-title {
        text-align: center;
        color: #94a3b8;
        font-size: 16px;
        margin-bottom: 40px;
    }

    /* 3. Formular-Container */
    [data-testid="stForm"] {
        background-color: rgba(30, 41, 59, 0.7) !important;
        backdrop-filter: blur(10px);
        padding: 50px !important;
        border-radius: 20px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5) !important;
        max-width: 450px !important;
        margin: 0 auto !important;
    }

    /* 4. Password-Auge Fix (Lücke schließen) */
    div[data-baseweb="input"] {
        background-color: rgba(15, 23, 42, 0.6) !important;
        border: 1px solid #334155 !important;
        border-radius: 10px !important;
        padding-right: 0px !important; /* Fixes the gap */
    }
    
    /* Input Text fix */
    input { color: #f1f5f9 !important; }

    /* Button Styling */
    button[kind="primaryFormSubmit"] {
        background: linear-gradient(135deg, #38bdf8, #1d4ed8) !important;
        border: none !important;
        color: white !important;
        font-weight: 700 !important;
        height: 48px !important;
        transition: all 0.3s ease !important;
    }
    button[kind="primaryFormSubmit"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px -5px rgba(56, 189, 248, 0.5) !important;
    }

    /* Sidebar Navigation */
    [data-testid="stSidebar"] {
        background-color: #0f172a !important;
        border-right: 1px solid #1e293b !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. SESSION STATE & CONNECTION ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'user_name' not in st.session_state: st.session_state['user_name'] = ""
if 'auth_mode' not in st.session_state: st.session_state['auth_mode'] = 'login'

conn = st.connection("gsheets", type=GSheetsConnection)

# --- 5. HAUPT-LOGIK ---

if st.session_state['logged_in']:
    # --- DASHBOARD NAVIGATION ---
    with st.sidebar:
        st.markdown("<h2 style='color:white;'>Balancely</h2>", unsafe_allow_html=True)
        menu = st.radio("Navigation", ["Übersicht", "Analysen", "Einstellungen"])
        st.markdown("---")
        if st.button("Abmelden"):
            st.session_state['logged_in'] = False
            st.rerun()

    if menu == "Übersicht":
        st.title(f"Willkommen, {st.session_state['user_name']}")
        m1, m2, m3 = st.columns(3)
        m1.metric("Gesamtbilanz", "2.840 €", "12%")
        m2.metric("Sparquote", "30%", "2%")
        m3.metric("Monatsbudget", "1.200 €")
        
        chart_data = pd.DataFrame(np.random.randn(20, 2), columns=['Einnahmen', 'Ausgaben'])
        st.area_chart(chart_data)

    elif menu == "Einstellungen":
        st.title("Einstellungen")
        with st.expander("Konto löschen"):
            st.error("Diese Aktion kann nicht rückgängig gemacht werden.")
            if st.button("Mein Konto jetzt dauerhaft löschen"):
                df = conn.read(worksheet="users", ttl="0")
                df_new = df[df['username'] != st.session_state['user_name']]
                conn.update(worksheet="users", data=df_new)
                st.session_state['logged_in'] = False
                st.rerun()

else:
    # --- AUTHENTIFIZIERUNG (Login & Register) ---
    st.markdown("<div style='height: 10vh;'></div>", unsafe_allow_html=True)
    st.markdown("<h1 class='main-title'>Balancely</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>Manage your finances with clarity</p>", unsafe_allow_html=True)

    _, center_col, _ = st.columns([1, 1.2, 1])

    with center_col:
        if st.session_state['auth_mode'] == 'login':
            with st.form("login_form"):
                st.markdown("<h3 style='text-align:center; color:white; margin-top:0;'>Anmelden</h3>", unsafe_allow_html=True)
                u_input = st.text_input("Username")
                p_input = st.text_input("Password", type="password")
                
                if st.form_submit_button("Anmelden"):
                    df = conn.read(worksheet="users", ttl="0")
                    user_row = df[df['username'] == u_input]
                    if not user_row.empty and make_hashes(p_input) == user_row.iloc[0]['password']:
                        st.session_state['logged_in'] = True
                        st.session_state['user_name'] = u_input
                        st.rerun()
                    else: st.error("Login fehlgeschlagen.")
            
            st.markdown("<div style='text-align:center; margin-top:15px;'>", unsafe_allow_html=True)
            if st.button("Noch kein Konto? Registrieren"):
                st.session_state['auth_mode'] = 'signup'
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        else:
            with st.form("signup_form"):
                st.markdown("<h3 style='text-align:center; color:white; margin-top:0;'>Registrieren</h3>", unsafe_allow_html=True)
                n_name = st.text_input("Vor- und Nachname")
                n_user = st.text_input("Username")
                n_pass = st.text_input("Passwort", type="password")
                c_pass = st.text_input("Passwort wiederholen", type="password")
                
                if st.form_submit_button("Konto erstellen"):
                    name_ok, name_msg = validate_full_name(n_name)
                    pwd_ok, pwd_msg = check_password_strength(n_pass)
                    df_ex = conn.read(worksheet="users", ttl="0")
                    
                    if not name_ok: st.error(name_msg)
                    elif n_pass != c_pass: st.error("Passwörter ungleich!")
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
