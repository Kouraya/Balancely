import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import streamlit_authenticator as stauth
import plotly.express as px

# --- 1. SEITEN-KONFIGURATION ---
st.set_page_config(page_title="Balancely", page_icon="⚖️", layout="centered")

# --- 2. INSTAGRAM-STYLE CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #000000; }
    [data-testid="stForm"] {
        background-color: #121212;
        padding: 40px;
        border-radius: 10px;
        border: 1px solid #363636;
        max-width: 350px;
        margin: 0 auto;
    }
    input {
        background-color: #121212 !important;
        border: 1px solid #363636 !important;
        border-radius: 3px !important;
        color: white !important;
    }
    button[kind="primaryFormSubmit"] {
        background-color: #0095f6 !important;
        border: none !important;
        width: 100% !important;
        border-radius: 8px !important;
        font-weight: bold !important;
    }
    .logo-font {
        font-family: 'Segoe UI', sans-serif;
        font-size: 50px;
        text-align: center;
        color: white;
        font-weight: bold;
        margin-bottom: 20px;
    }
    .switch-text { text-align: center; margin-top: 20px; font-size: 14px; color: #a8a8a8; }
    .stButton > button { background: none !important; border: none !important; color: #0095f6 !important; font-weight: bold !important; }
    
    /* Dashboard Styling */
    .metric-card { background-color: #121212; padding: 15px; border-radius: 10px; border: 1px solid #363636; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. VERBINDUNG & DATEN ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data(sheet_name):
    return conn.read(worksheet=sheet_name, ttl="0")

user_db = get_data("users")

# Credentials vorbereiten
credentials = {'usernames': {}}
for _, row in user_db.iterrows():
    credentials['usernames'][str(row['username'])] = {
        'name': str(row['name']),
        'password': str(row['password']) 
    }

authenticator = stauth.Authenticate(credentials, 'balancely_cookie', 'auth_key', cookie_expiry_days=30)

# Navigation State
if 'auth_mode' not in st.session_state:
    st.session_state['auth_mode'] = 'login'

# --- 4. LOGIN / REGISTRIERUNG ---
if not st.session_state.get("authentication_status"):
    st.markdown('<p class="logo-font">Balancely</p>', unsafe_allow_html=True)

    if st.session_state['auth_mode'] == 'login':
        authenticator.login(location='main')
        if st.session_state["authentication_status"] is False:
            st.error('Login fehlgeschlagen.')
        st.markdown('<p class="switch-text">Du hast noch kein Konto?</p>', unsafe_allow_html=True)
        if st.button("Registrieren"):
            st.session_state['auth_mode'] = 'signup'
            st.rerun()
    else:
        with st.form("reg_form"):
            st.markdown("<p style='text-align:center; color:#a8a8a8;'>Konto erstellen</p>", unsafe_allow_html=True)
            new_name = st.text_input("Vollständiger Name")
            new_user = st.text_input("Benutzername")
            new_pw = st.text_input("Passwort", type="password")
            if st.form_submit_button("Registrieren"):
                if new_name and new_user and new_pw:
                    if new_user in user_db['username'].astype(str).values:
                        st.error("Nutzername vergeben.")
                    else:
                        new_row = pd.DataFrame([{"name": new_name, "username": new_user, "password": new_pw}])
                        updated = pd.concat([user_db, new_row], ignore_index=True)
                        conn.update(worksheet="users", data=updated)
                        st.success("Konto erstellt!")
                        st.session_state['auth_mode'] = 'login'
                        st.rerun()
        if st.button("Zurück zum Login"):
            st.session_state['auth_mode'] = 'login'
            st.rerun()

# --- 5. DASHBOARD (VOLLSTÄNDIG) ---
else:
    # Sidebar für Logout & Info
    authenticator.logout('Abmelden', 'sidebar')
    username = st.session_state["username"]
    st.sidebar.write(f"Angemeldet als: **{st.session_state['name']}**")
    
    st.title("⚖️ Deine Finanzen")

    # Transaktionen laden & filtern
    all_trans = get_data("transactions")
    df_user = all_trans[all_trans['username'] == username].copy()

    # Eingabe-Sektion
    with st.expander("➕ Neue Buchung"):
        with st.form("add_transaction", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                datum = st.date_input("Datum", datetime.now())
                typ = st.selectbox("Typ", ["Ausgabe", "Einnahme"])
            with col2:
                kat = st.selectbox("Kategorie", ["Essen", "Miete", "Gehalt", "Freizeit", "Transport", "Shopping"])
                betrag = st.number_input("Betrag in €", min_value=0.0, step=0.01)
            notiz = st.text_input("Notiz")
            
            if st.form_submit_button("Speichern"):
                new_entry = pd.DataFrame([{"username": username, "Datum": str(datum), "Kategorie": kat, "Typ": typ, "Betrag": betrag, "Notiz": notiz}])
                updated_trans = pd.concat([all_trans, new_entry], ignore_index=True)
                conn.update(worksheet="transactions", data=updated_all)
                st.success("Gespeichert!")
                st.rerun()

    # Auswertung
    if not df_user.empty:
        df_user['Betrag'] = pd.to_numeric(df_user['Betrag'])
        ein = df_user[df_user["Typ"] == "Einnahme"]["Betrag"].sum()
        aus = df_user[df_user["Typ"] == "Ausgabe"]["Betrag"].sum()

        # Metriken anzeigen
        c1, c2, c3 = st.columns(3)
        c1.metric("Einnahmen", f"{ein:.2f} €")
        c2.metric("Ausgaben", f"-{aus:.2f} €")
        c3.metric("Kontostand", f"{ein-aus:.2f} €")

        # Visualisierung
        fig = px.pie(df_user[df_user["Typ"] == "Ausgabe"], values='Betrag', names='Kategorie', title="Ausgaben nach Kategorie", hole=0.4)
        fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Letzte Buchungen")
        st.dataframe(df_user.sort_values("Datum", ascending=False), use_container_width=True, hide_index=True)
    else:
        st.info("Noch keine Daten vorhanden.")
