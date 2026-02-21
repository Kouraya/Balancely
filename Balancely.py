import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import hashlib
import datetime
import plotly.express as px

# --- 1. SEITEN-KONFIGURATION ---
st.set_page_config(page_title="Balancely", page_icon="⚖️", layout="wide")

# --- 2. HILFSFUNKTIONEN ---
def make_hashes(text):
    return hashlib.sha256(str.encode(text)).hexdigest()

# --- 3. CSS (FIX FÜR GRÜNE EINNAHME & CLEAN DESIGN) ---
st.markdown("""
    <style>
    /* Hintergrund-Gradient */
    [data-testid="stAppViewContainer"] {
        background: radial-gradient(circle at top right, #1e293b, #0f172a, #020617) !important;
    }
    
    /* SEGMENTED CONTROL: Einnahme grün, wenn ausgewählt */
    /* Wir zielen auf das Element ab, das den Text 'Einnahme' enthält */
    div[data-testid="stSegmentedControl"] button[aria-checked="true"] {
        background-color: #10b981 !important; /* Emerald Green */
        color: white !important;
        border-color: #10b981 !important;
        box-shadow: 0 0 10px rgba(16, 185, 129, 0.4) !important;
    }
    
    /* Verhindert den roten Standard-Glow von Streamlit */
    div[data-testid="stSegmentedControl"] button:focus {
        outline: none !important;
    }

    /* Entfernt die Stepper-Pfeile (Plus/Minus) im Number Input */
    input[type=number]::-webkit-inner-spin-button, 
    input[type=number]::-webkit-outer-spin-button { 
        -webkit-appearance: none; margin: 0; 
    }
    input[type=number] { -moz-appearance: textfield; }

    /* Eingabefelder Styling */
    div[data-baseweb="input"], div[data-baseweb="select"] {
        background-color: rgba(15, 23, 42, 0.9) !important;
        border: 1px solid #334155 !important;
        border-radius: 10px !important;
    }

    /* Sidebar & Logout Button */
    [data-testid="stSidebar"] { background-color: #0b0f1a !important; }
    
    .stMetric {
        background-color: rgba(255, 255, 255, 0.03);
        padding: 15px;
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. SESSION STATE & VERBINDUNG ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'user_name' not in st.session_state: st.session_state['user_name'] = ""
if 'auth_mode' not in st.session_state: st.session_state['auth_mode'] = 'login'

conn = st.connection("gsheets", type=GSheetsConnection)

# --- 5. HAUPTLOGIK ---

if st.session_state['logged_in']:
    # SIDEBAR NAVIGATION
    with st.sidebar:
        st.markdown(f"## Balancely ⚖️")
        st.info(f"👤 **{st.session_state['user_name']}**")
        st.markdown("---")
        menu = st.radio("Navigation", ["📈 Dashboard", "💸 Neue Buchung", "⚙️ Einstellungen"])
        st.markdown("<div style='height: 30vh;'></div>", unsafe_allow_html=True)
        if st.button("Abmelden ➔", use_container_width=True):
            st.session_state['logged_in'] = False
            st.rerun()

    # DASHBOARD
    if menu == "📈 Dashboard":
        st.title("Deine Übersicht")
        try:
            df_t = conn.read(worksheet="transactions", ttl="0")
            user_df = df_t[df_t['user'] == st.session_state['user_name']]
            
            if not user_df.empty:
                user_df['betrag'] = pd.to_numeric(user_df['betrag'])
                ein = user_df[user_df['betrag'] > 0]['betrag'].sum()
                aus = abs(user_df[user_df['betrag'] < 0]['betrag'].sum())
                saldo = ein - aus
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Kontostand", f"{saldo:,.2f} €", delta=f"{saldo:,.2f} €")
                c2.metric("Einnahmen", f"{ein:,.2f} €")
                c3.metric("Ausgaben", f"-{aus:,.2f} €", delta_color="inverse")
                
                st.markdown("---")
                
                # Grafik: Ausgabenverteilung
                ausg_df = user_df[user_df['betrag'] < 0].copy()
                ausg_df['betrag'] = abs(ausg_df['betrag'])
                
                if not ausg_df.empty:
                    fig = px.pie(ausg_df, values='betrag', names='kategorie', hole=0.5,
                                 color_discrete_sequence=px.colors.qualitative.Safe)
                    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="white")
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Noch keine Buchungen vorhanden. Leg los!")
        except:
            st.error("Fehler beim Laden der Daten. Spalten 'user' und 'betrag' vorhanden?")

    # BUCHUNG ERFASSEN
    elif menu == "💸 Neue Buchung":
        st.title("Buchung erfassen ✍️")
        with st.form("entry_form", clear_on_submit=True):
            # Der Typ-Schalter (Grün via CSS)
            t_type = st.segmented_control("Typ wählen", ["Ausgabe", "Einnahme"], default="Ausgabe")
            
            col1, col2 = st.columns(2)
            with col1:
                t_amount = st.number_input("Betrag in €", min_value=0.0, step=0.01, format="%.2f")
                t_date = st.date_input("Datum", datetime.date.today())
            
            with col2:
                # Kategorien Logik
                base_cats = ["Essen", "Miete", "Freizeit", "Transport", "Shopping"] if t_type == "Ausgabe" else ["Gehalt", "Nebenjob", "Geschenk"]
                t_cat_select = st.selectbox("Kategorie", base_cats + ["+ Eigene hinzufügen..."])
                
                t_cat_custom = ""
                if t_cat_select == "+ Eigene hinzufügen...":
                    t_cat_custom = st.text_input("Name der neuen Kategorie")

            t_note = st.text_input("Notiz (optional)")
            
            if st.form_submit_button("Buchung speichern", use_container_width=True):
                final_cat = t_cat_custom if t_cat_select == "+ Eigene hinzufügen..." else t_cat_select
                
                if t_amount > 0 and final_cat != "":
                    # Automatische Vorzeichen-Vergabe
                    final_val = t_amount if t_type == "Einnahme" else -t_amount
                    
                    new_data = pd.DataFrame([{
                        "user": st.session_state['user_name'],
                        "datum": str(t_date),
                        "typ": t_type,
                        "kategorie": final_cat,
                        "betrag": final_val,
                        "notiz": t_note
                    }])
                    
                    # Google Sheets Update
                    old_df = conn.read(worksheet="transactions", ttl="0")
                    updated_df = pd.concat([old_df, new_data], ignore_index=True)
                    conn.update(worksheet="transactions", data=updated_df)
                    
                    st.success(f"Gespeichert: {final_cat} ({final_val} €)")
                    st.balloons()
                else:
                    st.error("Bitte Betrag und Kategorie angeben.")

else:
    # LOGIN / SIGNUP BEREICH
    st.markdown("<div style='height: 10vh;'></div>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align:center;'>Balancely</h1>", unsafe_allow_html=True)
    
    _, center_col, _ = st.columns([1, 1.2, 1])
    with center_col:
        if st.session_state['auth_mode'] == 'login':
            with st.form("login"):
                st.subheader("Anmelden")
                u = st.text_input("Username")
                p = st.text_input("Passwort", type="password")
                if st.form_submit_button("Login", use_container_width=True):
                    df_u = conn.read(worksheet="users", ttl="0")
                    user_match = df_u[df_u['username'] == u]
                    if not user_match.empty and make_hashes(p) == str(user_match.iloc[0]['password']):
                        st.session_state['logged_in'] = True
                        st.session_state['user_name'] = u
                        st.rerun()
                    else: st.error("Daten ungültig.")
            if st.button("Konto erstellen"): 
                st.session_state['auth_mode'] = 'signup'
                st.rerun()
        else:
            with st.form("signup"):
                st.subheader("Registrierung")
                new_u = st.text_input("Username")
                new_p = st.text_input("Passwort", type="password")
                if st.form_submit_button("Registrieren", use_container_width=True):
                    df_u = conn.read(worksheet="users", ttl="0")
                    if new_u in df_u['username'].values: st.error("Username existiert bereits.")
                    else:
                        reg_df = pd.concat([df_u, pd.DataFrame([{"username": new_u, "password": make_hashes(new_p)}])], ignore_index=True)
                        conn.update(worksheet="users", data=reg_df)
                        st.success("Erfolg! Bitte einloggen.")
                        st.session_state['auth_mode'] = 'login'
            if st.button("Zurück zum Login"): 
                st.session_state['auth_mode'] = 'login'
                st.rerun()
