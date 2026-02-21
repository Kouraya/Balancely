import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import streamlit_authenticator as stauth

# --- 1. SEITEN-KONFIGURATION ---
st.set_page_config(page_title="Balancely ⚖️", page_icon="💰", layout="wide")

# CSS für ein schickes, zentriertes Interface
st.markdown("""
    <style>
    /* Hintergrund und allgemeine Schrift */
    .stApp { background-color: #0e1117; }
    
    /* Formulare zentrieren und stylen */
    [data-testid="stForm"] {
        max-width: 450px;
        margin: 0 auto;
        padding: 30px;
        border: 1px solid #374151;
        border-radius: 15px;
        background-color: #161b22;
    }
    
    /* Input Felder stylen */
    div[data-baseweb="input"] {
        border-radius: 8px !important;
    }
    
    /* Titel zentrieren */
    .centered-title {
        text-align: center;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. VERBINDUNG ZU GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. DATEN-FUNKTIONEN ---
def get_user_data():
    return conn.read(worksheet="users", ttl="1m")

def save_new_user(all_users_df):
    conn.update(worksheet="users", data=all_users_df)

def get_transactions(username):
    all_trans = conn.read(worksheet="transactions", ttl="0")
    # Sicherstellen, dass die Spalte 'username' existiert
    if 'username' in all_trans.columns:
        return all_trans[all_trans['username'] == username]
    return pd.DataFrame()

# --- 4. AUTHENTIFIZIERUNG VORBEREITEN ---
user_db = get_user_data()

credentials = {'usernames': {}}
for _, row in user_db.iterrows():
    credentials['usernames'][str(row['username'])] = {
        'name': str(row['name']),
        'password': str(row['password']) 
    }

authenticator = stauth.Authenticate(
    credentials,
    'balancely_cookie',
    'auth_key',
    cookie_expiry_days=30
)

# --- 5. LOGIK: LOGIN ODER REGISTRIERUNG ---
if not st.session_state.get("authentication_status"):
    # Navigation in der Sidebar für Nicht-Eingeloggte
    st.sidebar.title("Willkommen")
    auth_mode = st.sidebar.radio("Was möchtest du tun?", ["Login", "Konto erstellen"])

    if auth_mode == "Login":
        st.markdown("<h1 class='centered-title'>Anmelden bei Balancely</h1>", unsafe_allow_html=True)
        authenticator.login(location='main')
        
        if st.session_state["authentication_status"] is False:
            st.error('Benutzername oder Passwort falsch.')
        elif st.session_state["authentication_status"] is None:
            st.info("Bitte gib deine Zugangsdaten ein.")

    elif auth_mode == "Konto erstellen":
        st.markdown("<h1 class='centered-title'>Neues Konto erstellen</h1>", unsafe_allow_html=True)
        with st.form("registration_form"):
            new_name = st.text_input("Dein voller Name")
            new_user = st.text_input("Wunsch-Benutzername")
            new_pw = st.text_input("Passwort", type="password")
            confirm_pw = st.text_input("Passwort wiederholen", type="password")
            
            reg_submit = st.form_submit_button("Registrieren")
            
            if reg_submit:
                if new_pw != confirm_pw:
                    st.error("Die Passwörter stimmen nicht überein.")
                elif new_user in user_db['username'].astype(str).values:
                    st.error("Dieser Benutzername ist bereits vergeben.")
                elif new_name and new_user and new_pw:
                    new_user_row = pd.DataFrame([{"name": new_name, "username": new_user, "password": new_pw}])
                    updated_users = pd.concat([user_db, new_user_row], ignore_index=True)
                    save_new_user(updated_users)
                    st.success("Erfolg! Du kannst dich jetzt über das Menü links einloggen.")
                else:
                    st.warning("Bitte alle Felder ausfüllen.")

# --- 6. DAS DASHBOARD (Wenn eingeloggt) ---
else:
    # Logout in die Sidebar verschieben
    authenticator.logout('Abmelden', 'sidebar')
    
    username = st.session_state["username"]
    name = st.session_state["name"]
    
    st.sidebar.markdown(f"Eingeloggt als: **{name}**")
    st.title(f"Dein Budget, {name} ⚖️")

    # Transaktionen laden
    df_user = get_transactions(username)

    # Formular für neue Buchungen
    with st.expander("➕ Neue Buchung erfassen"):
        with st.form("transaction_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                datum = st.date_input("Datum", datetime.now())
                typ = st.selectbox("Typ", ["Ausgabe", "Einnahme"])
            with col2:
                kat = st.selectbox("Kategorie", ["Essen", "Miete", "Gehalt", "Freizeit", "Transport", "Shopping"])
                betrag = st.number_input("Betrag in €", min_value=0.0, step=0.01)
            
            notiz = st.text_input("Notiz (optional)")
            if st.form_submit_button("Buchung speichern"):
                if betrag > 0:
                    new_entry = pd.DataFrame([{
                        "username": username,
                        "Datum": str(datum),
                        "Kategorie": kat,
                        "Typ": typ,
                        "Betrag": betrag,
                        "Notiz": notiz
                    }])
                    all_trans = conn.read(worksheet="transactions")
                    updated_all = pd.concat([all_trans, new_entry], ignore_index=True)
                    conn.update(worksheet="transactions", data=updated_all)
                    st.success("Buchung gespeichert!")
                    st.rerun()

    # Statistik-Bereich
    if not df_user.empty:
        # Sicherstellen, dass Betrag eine Zahl ist
        df_user['Betrag'] = pd.to_numeric(df_user['Betrag'], errors='coerce')
        
        einnahmen = df_user[df_user["Typ"] == "Einnahme"]["Betrag"].sum()
        ausgaben = df_user[df_user["Typ"] == "Ausgabe"]["Betrag"].sum()
        balance = einnahmen - ausgaben
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Einnahmen", f"{einnahmen:,.2f} €")
        m2.metric("Ausgaben", f"-{ausgaben:,.2f} €")
        m3.metric("Kontostand", f"{balance:,.2f} €")
        
        st.subheader("Deine letzten Buchungen")
        st.dataframe(df_user.sort_values("Datum", ascending=False), use_container_width=True, hide_index=True)
    else:
        st.info("Noch keine Daten vorhanden. Erfasse deine erste Buchung!")
