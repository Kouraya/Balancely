import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import hashlib
import numpy as np
import datetime

# --- 1. SEITEN-KONFIGURATION ---
st.set_page_config(page_title="Balancely", page_icon="⚖️", layout="wide")

# --- 2. HILFSFUNKTIONEN ---
def make_hashes(text):
    return hashlib.sha256(str.encode(text)).hexdigest()

# --- 3. CSS (DESIGN & BUG-FIXES) ---
st.markdown("""
    <style>
    /* Hintergrund & Globales Design */
    [data-testid="stAppViewContainer"] {
        background: radial-gradient(circle at top right, #1e293b, #0f172a, #020617) !important;
    }
    .main-title {
        text-align: center; color: #f8fafc; font-size: 64px; font-weight: 800;
        letter-spacing: -2px; margin-bottom: 0px;
        text-shadow: 0 0 30px rgba(56, 189, 248, 0.4);
    }
    .sub-title {
        text-align: center; color: #94a3b8; font-size: 18px; margin-bottom: 40px;
    }

    /* Formular-Zentrierung & Glassmorphism */
    [data-testid="stForm"] {
        background-color: rgba(30, 41, 59, 0.7) !important;
        backdrop-filter: blur(15px);
        padding: 40px !important;
        border-radius: 24px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7) !important;
    }

    /* BUG-FIX: PASSWORT-AUGE & RECHTE LÜCKE */
    div[data-baseweb="input"] {
        background-color: rgba(15, 23, 42, 0.8) !important;
        border: 1px solid #334155 !important;
        border-radius: 12px !important;
        padding-right: 0px !important; 
    }
    input { padding-left: 15px !important; color: #f1f5f9 !important; }
    div[data-baseweb="input"] > div:last-child { margin-right: 0px !important; padding-right: 0px !important; }
    
    /* Entfernt "Press Enter to submit" */
    div[data-testid="InputInstructions"] { display: none !important; }

    /* Sidebar Design */
    [data-testid="stSidebar"] {
        background-color: #0b0f1a !important;
        border-right: 1px solid #1e293b !important;
    }
    
    /* Buttons */
    button[kind="primaryFormSubmit"] {
        background: linear-gradient(135deg, #38bdf8, #1d4ed8) !important;
        border: none !important; height: 50px !important;
        border-radius: 12px !important; font-weight: 700 !important;
        width: 100% !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. SESSION STATE & DATENBANK ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'user_name' not in st.session_state: st.session_state['user_name'] = ""
if 'auth_mode' not in st.session_state: st.session_state['auth_mode'] = 'login'

conn = st.connection("gsheets", type=GSheetsConnection)

# --- 5. HAUPTLOGIK ---

if st.session_state['logged_in']:
    # --- DASHBOARD NAVIGATION ---
    with st.sidebar:
        st.markdown("<h1 style='color:white; font-size: 28px;'>Balancely ⚖️</h1>", unsafe_allow_html=True)
        st.markdown(f"👤 Eingeloggt: **{st.session_state['user_name']}**")
        st.markdown("---")
        menu = st.radio("Navigation", ["📈 Dashboard", "💸 Transaktion", "📂 Analysen", "⚙️ Einstellungen"], label_visibility="collapsed")
        
        st.markdown("<div style='height: 35vh;'></div>", unsafe_allow_html=True)
        st.markdown("---")
        if st.button("🚪 Abmelden", use_container_width=True):
            st.session_state['logged_in'] = False
            st.rerun()

    # --- MENU: DASHBOARD ---
    if menu == "📈 Dashboard":
        st.title(f"Deine Übersicht, {st.session_state['user_name']}! ⚖️")
        
        try:
            df_t = conn.read(worksheet="transactions", ttl="0")
            user_df = df_t[df_t['user'] == st.session_state['user_name']]
            
            if not user_df.empty:
                # Metriken
                ein = user_df[user_df['typ'] == "Einnahme"]['betrag'].sum()
                aus = abs(user_df[user_df['typ'] == "Ausgabe"]['betrag'].sum())
                bal = ein - aus
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Kontostand", f"{bal:,.2f} €")
                c2.metric("Einnahmen", f"{ein:,.2f} €")
                c3.metric("Ausgaben", f"{aus:,.2f} €", delta_color="inverse")

                st.markdown("---")
                
                # Grafik: Ausgaben nach Kategorie
                st.subheader("Ausgaben nach Kategorie")
                ausg_df = user_df[user_df['typ'] == "Ausgabe"].copy()
                ausg_df['betrag'] = abs(ausg_df['betrag'])
                if not ausg_df.empty:
                    st.bar_chart(data=ausg_df, x="kategorie", y="betrag", color="kategorie")
                else:
                    st.info("Noch keine Ausgaben erfasst.")

                # Liste
                with st.expander("Letzte Transaktionen"):
                    st.dataframe(user_df.sort_values("datum", ascending=False), use_container_width=True)
            else:
                st.info("Willkommen! Erfasse unter '💸 Transaktion' deine ersten Daten.")
        except Exception as e:
            st.error(f"Datenbankfehler: {e}")

    # --- MENU: TRANSAKTION ---
    elif menu == "💸 Transaktion":
        st.title("Buchung hinzufügen ✍️")
        with st.form("t_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                t_type = st.selectbox("Typ", ["Ausgabe", "Einnahme"])
                t_amount = st.number_input("Betrag in €", min_value=0.01, step=0.01)
            with col2:
                cats = ["Gehalt", "Bonus", "Verkauf"] if t_type == "Einnahme" else ["Essen", "Miete", "Freizeit", "Transport", "Fixkosten"]
                t_cat = st.selectbox("Kategorie", cats)
                t_date = st.date_input("Datum", datetime.date.today())
            
            t_note = st.text_input("Notiz (optional)")
            
            if st.form_submit_button("Speichern"):
                new_row = pd.DataFrame([{
                    "user": st.session_state['user_name'],
                    "datum": str(t_date),
                    "typ": t_type,
                    "kategorie": t_cat,
                    "betrag": t_amount if t_type == "Einnahme" else -t_amount,
                    "notiz": t_note
                }])
                df_old = conn.read(worksheet="transactions", ttl="0")
                df_new = pd.concat([df_old, new_row], ignore_index=True)
                conn.update(worksheet="transactions", data=df_new)
                st.success("Erfolgreich gespeichert!")

    # --- MENU: EINSTELLUNGEN ---
    elif menu == "⚙️ Einstellungen":
        st.title("Einstellungen ⚙️")
        if st.button("Alle meine Transaktionen löschen"):
            df_t = conn.read(worksheet="transactions", ttl="0")
            df_t = df_t[df_t['user'] != st.session_state['user_name']]
            conn.update(worksheet="transactions", data=df_t)
            st.warning("Daten gelöscht.")

else:
    # --- LOGIN / REGISTRIERUNG ---
    st.markdown("<div style='height: 8vh;'></div>", unsafe_allow_html=True)
    st.markdown("<h1 class='main-title'>Balancely</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>Verwalte deine Finanzen mit Klarheit</p>", unsafe_allow_html=True)

    _, center_col, _ = st.columns([1, 1.2, 1])

    with center_col:
        if st.session_state['auth_mode'] == 'login':
            with st.form("login_f"):
                st.markdown("<h3 style='text-align:center; color:white;'>Anmelden</h3>", unsafe_allow_html=True)
                u_in = st.text_input("Username", placeholder="Benutzername")
                p_in = st.text_input("Passwort", type="password", placeholder="••••••••")
                
                if st.form_submit_button("Anmelden"):
                    df_u = conn.read(worksheet="users", ttl="0")
                    user_row = df_u[df_u['username'] == u_in]
                    if not user_row.empty and make_hashes(p_in) == str(user_row.iloc[0]['password']):
                        st.session_state['logged_in'] = True
                        st.session_state['user_name'] = u_in
                        st.rerun()
                    else: st.error("Login ungültig.")
            
            if st.button("Neu hier? Konto erstellen", use_container_width=True):
                st.session_state['auth_mode'] = 'signup'
                st.rerun()

        else:
            with st.form("signup_f"):
                st.markdown("<h3 style='text-align:center; color:white;'>Registrierung</h3>", unsafe_allow_html=True)
                s_name = st.text_input("Vor- und Nachname", placeholder="Max Mustermann")
                s_user = st.text_input("Username", placeholder="max123")
                s_pass = st.text_input("Passwort", type="password")
                c_pass = st.text_input("Passwort wiederholen", type="password")
                
                if st.form_submit_button("Konto erstellen"):
                    df_u = conn.read(worksheet="users", ttl="0")
                    if s_pass != c_pass: st.error("Passwörter ungleich.")
                    elif s_user in df_u['username'].values: st.error("Username vergeben.")
                    else:
                        new_u = pd.DataFrame([{"name": s_name, "username": s_user, "password": make_hashes(s_pass)}])
                        conn.update(worksheet="users", data=pd.concat([df_u, new_u], ignore_index=True))
                        st.success("Konto erstellt! Bitte einloggen.")
            
            if st.button("Zurück zum Login", use_container_width=True):
                st.session_state['auth_mode'] = 'login'
                st.rerun()
