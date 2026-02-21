import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
from datetime import datetime
import streamlit_authenticator as stauth

# --- 1. SEITEN-KONFIGURATION ---
st.set_page_config(page_title="Balancely ⚖️", page_icon="💰", layout="wide")

# --- 2. VERBINDUNG ZU GOOGLE SHEETS ---
# Nutzt die Basis-URL aus den Secrets
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. DATEN-FUNKTIONEN ---
def get_user_data():
    return conn.read(worksheet="users", ttl="1m")

def save_new_user(all_users_df):
    conn.update(worksheet="users", data=all_users_df)

def get_transactions(username):
    all_trans = conn.read(worksheet="transactions", ttl="0")
    # Filtern nach dem eingeloggten Nutzer
    return all_trans[all_trans['username'] == username]

# --- 4. AUTHENTIFIZIERUNG ---
user_db = get_user_data()

# Vorbereiten der Nutzerdaten für den Authenticator
credentials = {'usernames': {}}
for _, row in user_db.iterrows():
    credentials['usernames'][row['username']] = {
        'name': row['name'],
        'password': row['password'] # Hinweis: In einer echten App sollten Passwörter gehasht sein!
    }

authenticator = stauth.Authenticate(
    credentials, 'balancely_cookie', 'auth_key', cookie_expiry_days=30
)

# Login-Maske anzeigen
name, authentication_status, username = authenticator.login('Login', 'main')

# --- 5. LOGIK FÜR NICHT-EINGELOGGTE NUTZER (REGISTRIERUNG) ---
if authentication_status is None or authentication_status is False:
    if authentication_status is False:
        st.error('Benutzername/Passwort falsch')
    
    st.divider()
    st.subheader("Neu hier? Konto erstellen")
    with st.form("reg_form"):
        new_name = st.text_input("Dein voller Name")
        new_user = st.text_input("Wunsch-Benutzername")
        new_pw = st.text_input("Passwort", type="password")
        reg_submit = st.form_submit_button("Registrieren")
        
        if reg_submit:
            if new_user in user_db['username'].values:
                st.error("Benutzername existiert bereits!")
            elif new_name and new_user and new_pw:
                # Neuen User zur Tabelle hinzufügen
                new_user_row = pd.DataFrame([{"name": new_name, "username": new_user, "password": new_pw}])
                updated_users = pd.concat([user_db, new_user_row], ignore_index=True)
                save_new_user(updated_users)
                st.success("Konto erstellt! Du kannst dich jetzt oben einloggen.")
                st.rerun()
            else:
                st.warning("Bitte alle Felder ausfüllen.")

# --- 6. DAS DASHBOARD (NUR FÜR EINGELOGGTE NUTZER) ---
elif authentication_status:
    # Logout in der Sidebar
    authenticator.logout('Logout', 'sidebar')
    st.sidebar.write(f"Angemeldet als: **{name}**")

    st.title("⚖️ Balancely Dashboard")

    # Transaktionen laden
    df_user = get_transactions(username)

    # Eingabe-Formular
    with st.expander("➕ Neue Buchung erfassen", expanded=True):
        with st.form("entry_form", clear_on_submit=True):
            c1, c2, c3, c4 = st.columns(4)
            with c1: datum = st.date_input("Datum", datetime.now())
            with c2: typ = st.selectbox("Typ", ["Ausgabe", "Einnahme"])
            with c3: kat = st.selectbox("Kategorie", ["Gehalt", "Essen", "Miete", "Freizeit", "Transport", "Shopping", "Fixkosten"])
            with c4: betrag = st.number_input("Betrag in €", min_value=0.0, format="%.2f")
            
            notiz = st.text_input("Notiz")
            if st.form_submit_button("Speichern"):
                if betrag > 0:
                    # Neue Transaktion
                    new_trans = pd.DataFrame([{
                        "username": username,
                        "Datum": str(datum),
                        "Kategorie": kat,
                        "Typ": typ,
                        "Betrag": betrag,
                        "Notiz": notiz
                    }])
                    # Gesamte Tabelle laden, neue Zeile dran, zurückschreiben
                    all_trans = conn.read(worksheet="transactions")
                    updated_all = pd.concat([all_trans, new_trans], ignore_index=True)
                    conn.update(worksheet="transactions", data=updated_all)
                    
                    st.success("Gespeichert!")
                    st.rerun()

    # Statistiken anzeigen
    if not df_user.empty:
        df_user['Betrag'] = pd.to_numeric(df_user['Betrag'])
        ein = df_user[df_user["Typ"] == "Einnahme"]["Betrag"].sum()
        aus = df_user[df_user["Typ"] == "Ausgabe"]["Betrag"].sum()
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Einnahmen", f"{ein:,.2f} €")
        col2.metric("Ausgaben", f"-{aus:,.2f} €")
        col3.metric("Balance", f"{ein-aus:,.2f} €")
        
        st.subheader("Verlauf")
        st.dataframe(df_user.sort_values("Datum", ascending=False), use_container_width=True, hide_index=True)
    else:
        st.info("Noch keine Transaktionen vorhanden.")
