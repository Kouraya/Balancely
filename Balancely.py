import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import hashlib
import numpy as np
import datetime
import re

# --- 1. SEITEN-KONFIGURATION ---
st.set_page_config(page_title="Balancely", page_icon="⚖️", layout="wide")

# --- 2. HILFSFUNKTIONEN ---
def make_hashes(text):
    return hashlib.sha256(str.encode(text)).hexdigest()

def check_password_strength(password):
    # Mindestens 6 Zeichen, ein Großbuchstabe, ein Kleinbuchstabe
    if len(password) < 6:
        return False, "Das Passwort muss mindestens 6 Zeichen lang sein."
    if not re.search(r"[a-z]", password):
        return False, "Das Passwort muss mindestens einen Kleinbuchstaben enthalten."
    if not re.search(r"[A-Z]", password):
        return False, "Das Passwort muss mindestens einen Großbuchstaben enthalten."
    return True, ""

# --- 3. CSS (OPTIMIERTES DESIGN) ---
st.markdown("""
    <style>
    /* Grundstyling für Segmented Control Buttons */
    div[data-testid="stSegmentedControl"] button {
        border: 1px solid #334155 !important;
    }

    /* Styling wenn 'Ausgabe' ausgewählt ist (Rot) */
    div[data-testid="stSegmentedControl"] button[aria-checked="true"] div[data-testid="stMarkdownContainer"] p:contains("Ausgabe") {
        color: white !important;
    }
    div[data-testid="stSegmentedControl"] button[aria-checked="true"]:has(p:contains("Ausgabe")) {
        background-color: #ef4444 !important; /* Rot */
        border-color: #ef4444 !important;
    }

    /* Styling wenn 'Einnahme' ausgewählt ist (Grün) */
    div[data-testid="stSegmentedControl"] button[aria-checked="true"] div[data-testid="stMarkdownContainer"] p:contains("Einnahme") {
        color: white !important;
    }
    div[data-testid="stSegmentedControl"] button[aria-checked="true"]:has(p:contains("Einnahme")) {
        background-color: #10b981 !important; /* Grün */
        border-color: #10b981 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. SESSION STATE ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'user_name' not in st.session_state: st.session_state['user_name'] = ""
if 'auth_mode' not in st.session_state: st.session_state['auth_mode'] = 'login'

conn = st.connection("gsheets", type=GSheetsConnection)

# --- 5. LOGIK ---

if st.session_state['logged_in']:
    with st.sidebar:
        st.markdown(f"<h2 style='color:white;'>Balancely ⚖️</h2>", unsafe_allow_html=True)
        st.markdown(f"👤 Eingeloggt: **{st.session_state['user_name']}**")
        st.markdown("---")
        menu = st.radio("Navigation", ["📈 Dashboard", "💸 Transaktion", "📂 Analysen", "⚙️ Einstellungen"], label_visibility="collapsed")
        
        st.markdown("<div style='height: 30vh;'></div>", unsafe_allow_html=True)
        if st.button("Logout ➜", use_container_width=True, type="secondary"):
            st.session_state['logged_in'] = False
            st.rerun()

    if menu == "📈 Dashboard":
        st.title(f"Deine Übersicht, {st.session_state['user_name']}! ⚖️")
        try:
            df_t = conn.read(worksheet="transactions", ttl="0")
            if 'user' in df_t.columns:
                user_df = df_t[df_t['user'] == st.session_state['user_name']]
                if not user_df.empty:
                    ein = pd.to_numeric(user_df[user_df['typ'] == "Einnahme"]['betrag']).sum()
                    aus = abs(pd.to_numeric(user_df[user_df['typ'] == "Ausgabe"]['betrag']).sum())
                    bal = ein - aus
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Kontostand", f"{bal:,.2f} €")
                    c2.metric("Einnahmen", f"{ein:,.2f} €")
                    c3.metric("Ausgaben", f"{aus:,.2f} €", delta_color="inverse")
                    st.subheader("Ausgaben nach Kategorie")
                    ausg_df = user_df[user_df['typ'] == "Ausgabe"].copy()
                    ausg_df['betrag'] = abs(pd.to_numeric(ausg_df['betrag']))
                    st.bar_chart(data=ausg_df, x="kategorie", y="betrag", color="kategorie")
                else:
                    st.info("Noch keine Daten. Klicke links auf '💸 Transaktion'.")
        except:
            st.warning("Warte auf Datenverbindung...")

    elif menu == "💸 Transaktion":
        st.title("Buchung hinzufügen ✍️")
        with st.form("t_form", clear_on_submit=True):
            t_type = st.segmented_control("Typ wählen", ["Ausgabe", "Einnahme"], default="Ausgabe")
            
            col1, col2 = st.columns(2)
            with col1:
                t_amount = st.number_input("Betrag in €", min_value=0.01, step=0.01)
                t_date = st.date_input("Datum", datetime.date.today())
            with col2:
                cats = ["Gehalt", "Bonus", "Verkauf"] if t_type == "Einnahme" else ["Essen", "Miete", "Freizeit", "Transport", "Shopping"]
                t_cat = st.selectbox("Kategorie", cats)
                t_note = st.text_input("Notiz")
            
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
                st.success(f"{t_type} erfolgreich gespeichert!")
                st.balloons()

else:
    # --- LOGIN / SIGNUP ---
    st.markdown("<div style='height: 8vh;'></div>", unsafe_allow_html=True)
    st.markdown("<h1 class='main-title'>Balancely</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>Verwalte deine Finanzen mit Klarheit</p>", unsafe_allow_html=True)
    _, center_col, _ = st.columns([1, 1.2, 1])
    with center_col:
        if st.session_state['auth_mode'] == 'login':
            with st.form("l_f"):
                st.markdown("<h3 style='text-align:center; color:white;'>Anmelden</h3>", unsafe_allow_html=True)
                u_in = st.text_input("Username", placeholder="Benutzername")
                p_in = st.text_input("Passwort", type="password")
                if st.form_submit_button("Anmelden"):
                    df_u = conn.read(worksheet="users", ttl="0")
                    user_row = df_u[df_u['username'] == u_in]
                    if not user_row.empty and make_hashes(p_in) == str(user_row.iloc[0]['password']):
                        st.session_state['logged_in'] = True
                        st.session_state['user_name'] = u_in
                        st.rerun()
                    else: st.error("Login ungültig.")
            if st.button("Konto erstellen", use_container_width=True):
                st.session_state['auth_mode'] = 'signup'; st.rerun()
        else:
            with st.form("s_f"):
                st.markdown("<h3 style='text-align:center; color:white;'>Registrierung</h3>", unsafe_allow_html=True)
                s_name = st.text_input("Name", placeholder="Max Mustermann")
                s_user = st.text_input("Username", placeholder="max123")
                s_pass = st.text_input("Passwort", type="password")
                c_pass = st.text_input("Passwort wiederholen", type="password")
                
                if st.form_submit_button("Konto erstellen"):
                    # 1. Schritt: Alle Felder ausgefüllt?
                    if not s_name or not s_user or not s_pass:
                        st.error("❌ Bitte fülle alle Felder aus!")
                    # 2. Schritt: Vor- und Nachname Prüfung
                    elif len(s_name.strip().split()) < 2:
                        st.error("❌ Bitte gib deinen vollständigen Vor- und Nachnamen an.")
                    # 3. Schritt: Passwort-Stärke Prüfung
                    is_strong, msg = check_password_strength(s_pass)
                    if not is_strong:
                        st.error(f"❌ {msg}")
                    # 4. Schritt: Passwort Übereinstimmung
                    elif s_pass != c_pass:
                        st.error("❌ Die Passwörter stimmen nicht überein.")
                    else:
                        df_u = conn.read(worksheet="users", ttl="0")
                        if s_user in df_u['username'].values:
                            st.error("⚠️ Dieser Username ist bereits vergeben.")
                        else:
                            new_u = pd.DataFrame([{"name": s_name.strip(), "username": s_user, "password": make_hashes(s_pass)}])
                            conn.update(worksheet="users", data=pd.concat([df_u, new_u], ignore_index=True))
                            st.success("✅ Konto erstellt! Bitte logge dich ein.")
                            st.balloons()
                            st.session_state['auth_mode'] = 'login'
            
            if st.button("Zurück zum Login", use_container_width=True):
                st.session_state['auth_mode'] = 'login'; st.rerun()

