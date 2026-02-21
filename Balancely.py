import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import hashlib
import numpy as np

# --- 1. SEITEN-KONFIGURATION ---
st.set_page_config(page_title="Balancely", page_icon="⚖️", layout="wide")

# --- 2. HILFSFUNKTIONEN ---
def make_hashes(text):
    return hashlib.sha256(str.encode(text)).hexdigest()

# --- 3. CSS (DESIGN-FIXES) ---
st.markdown("""
    <style>
    /* Hintergrund & Titel */
    [data-testid="stAppViewContainer"] {
        background: radial-gradient(circle at top right, #1e293b, #0f172a, #020617) !important;
    }
    .main-title {
        text-align: center; color: #f8fafc; font-size: 64px; font-weight: 800;
        letter-spacing: -2px; margin-bottom: 0px;
        text-shadow: 0 0 30px rgba(56, 189, 248, 0.4);
    }

    /* Zentrierung des Login-Formulars */
    [data-testid="stForm"] {
        background-color: rgba(30, 41, 59, 0.7) !important;
        backdrop-filter: blur(15px);
        padding: 50px !important;
        border-radius: 24px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7) !important;
        width: 100% !important;
    }

    /* Input & Enter-Text entfernen */
    div[data-testid="InputInstructions"] { display: none !important; }
    
    div[data-baseweb="input"] {
        background-color: rgba(15, 23, 42, 0.8) !important;
        border: 1px solid #334155 !important;
        border-radius: 12px !important;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #0b0f1a !important;
        border-right: 1px solid #1e293b !important;
    }
    
    /* Buttons */
    button[kind="primaryFormSubmit"] {
        background: linear-gradient(135deg, #38bdf8, #1d4ed8) !important;
        border: none !important; height: 50px !important; width: 100% !important;
        border-radius: 12px !important; font-weight: 700 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. SESSION STATE ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'user_name' not in st.session_state: st.session_state['user_name'] = ""
if 'auth_mode' not in st.session_state: st.session_state['auth_mode'] = 'login'

conn = st.connection("gsheets", type=GSheetsConnection)

# --- 5. HAUPT-LOGIK ---

if st.session_state['logged_in']:
    # --- SIDEBAR UI ---
    with st.sidebar:
        st.markdown("<h1 style='color:white; font-size: 28px;'>Balancely ⚖️</h1>", unsafe_allow_html=True)
        st.markdown(f"👤 **{st.session_state['user_name']}**")
        st.markdown("---")
        
        # Verbessertes Menü mit Emojis als Icon-Ersatz
        menu = st.radio(
            "Navigation",
            ["📈 Dashboard", "📂 Analysen", "⚙️ Einstellungen"],
            label_visibility="collapsed"
        )
        
        st.sidebar.container() # Spacer
        st.markdown("---")
        if st.button("🚪 Abmelden", use_container_width=True):
            st.session_state['logged_in'] = False
            st.rerun()

    # --- CONTENT ---
    if "Dashboard" in menu:
        st.title(f"Willkommen, {st.session_state['user_name']}! ⚖️")
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Gesamtbilanz", "2.840 €", "12%")
        m2.metric("Sparquote", "30%", "2%")
        m3.metric("Monatsbudget", "1.200 €")
        
        # Beispiel-Grafik
        st.area_chart(pd.DataFrame(np.random.randn(20, 2), columns=['Einnahmen', 'Ausgaben']))

    elif "Einstellungen" in menu:
        st.title("Einstellungen ⚙️")
        st.subheader("Account-Verwaltung")
        with st.expander("Gefahrenzone"):
            st.warning("Dein Account wird sofort gelöscht.")
            if st.button("Konto unwiderruflich löschen"):
                df = conn.read(worksheet="users", ttl="0")
                df_new = df[df['username'] != st.session_state['user_name']]
                conn.update(worksheet="users", data=df_new)
                st.session_state['logged_in'] = False
                st.rerun()

else:
    # --- LOGIN ZENTRIERT ---
    st.markdown("<div style='height: 12vh;'></div>", unsafe_allow_html=True)
    st.markdown("<h1 class='main-title'>Balancely</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#94a3b8; margin-bottom:40px;'>Manage your finances with clarity</p>", unsafe_allow_html=True)

    # Die Spalten sorgen für die Zentrierung des Formulars
    _, center_col, _ = st.columns([1, 1.2, 1])

    with center_col:
        if st.session_state['auth_mode'] == 'login':
            with st.form("login_form"):
                st.markdown("<h3 style='text-align:center; color:white;'>Anmelden</h3>", unsafe_allow_html=True)
                u_input = st.text_input("Username", placeholder="Dein Benutzername")
                p_input = st.text_input("Password", type="password", placeholder="••••••••")
                
                if st.form_submit_button("Anmelden"):
                    df = conn.read(worksheet="users", ttl="0")
                    user_row = df[df['username'] == u_input]
                    if not user_row.empty and make_hashes(p_input) == user_row.iloc[0]['password']:
                        st.session_state['logged_in'] = True
                        st.session_state['user_name'] = u_input
                        st.rerun()
                    else: st.error("Daten inkorrekt.")
            
            # Button außerhalb des Forms für Registrierung
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Neu hier? Konto erstellen", use_container_width=True):
                st.session_state['auth_mode'] = 'signup'
                st.rerun()

        else:
            with st.form("signup_form"):
                st.markdown("<h3 style='text-align:center; color:white;'>Registrierung</h3>", unsafe_allow_html=True)
                n_name = st.text_input("Vor- und Nachname")
                n_user = st.text_input("Wunsch-Username")
                n_pass = st.text_input("Passwort", type="password")
                c_pass = st.text_input("Wiederholen", type="password")
                
                if st.form_submit_button("Konto erstellen"):
                    # (Hier bliebe deine Validierungs-Logik von oben)
                    pass 
            
            if st.button("Zurück zum Login", use_container_width=True):
                st.session_state['auth_mode'] = 'login'
                st.rerun()
