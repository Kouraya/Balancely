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

# --- 3. CSS (DESIGN-UPGRADE) ---
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] {
        background: radial-gradient(circle at top right, #1e293b, #0f172a, #020617) !important;
    }
    /* Formular & Input Felder */
    [data-testid="stForm"] {
        background-color: rgba(30, 41, 59, 0.7) !important;
        backdrop-filter: blur(15px);
        padding: 30px !important;
        border-radius: 20px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    /* Entfernt die hässlichen Stepper-Buttons im Number-Input */
    input[type=number]::-webkit-inner-spin-button, 
    input[type=number]::-webkit-outer-spin-button { 
        -webkit-appearance: none; margin: 0; 
    }
    
    /* Input Style Fixes */
    div[data-baseweb="input"] {
        background-color: rgba(15, 23, 42, 0.9) !important;
        border: 1px solid #334155 !important;
        border-radius: 10px !important;
    }
    
    /* Sidebar & Logout */
    [data-testid="stSidebar"] { background-color: #0b0f1a !important; }
    
    .stMetric {
        background-color: rgba(255, 255, 255, 0.05);
        padding: 15px;
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
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
        st.markdown(f"## Balancely ⚖️")
        st.info(f"👤 **{st.session_state['user_name']}**")
        st.markdown("---")
        menu = st.radio("Navigation", ["📈 Dashboard", "💸 Neue Buchung", "⚙️ Einstellungen"])
        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("Abmelden ➔", use_container_width=True):
            st.session_state['logged_in'] = False
            st.rerun()

    if menu == "📈 Dashboard":
        st.title(f"Deine Finanzen im Blick")
        
        try:
            df_t = conn.read(worksheet="transactions", ttl="0")
            user_df = df_t[df_t['user'] == st.session_state['user_name']]
            
            if not user_df.empty:
                # Mathematische Berechnung
                user_df['betrag'] = pd.to_numeric(user_df['betrag'])
                einnahmen = user_df[user_df['betrag'] > 0]['betrag'].sum()
                ausgaben = abs(user_df[user_df['betrag'] < 0]['betrag'].sum())
                kontostand = einnahmen - ausgaben
                
                # Metriken oben
                col1, col2, col3 = st.columns(3)
                col1.metric("Gesamt-Saldo", f"{kontostand:,.2f} €", delta=f"{kontostand:,.2f} €")
                col2.metric("Einnahmen", f"{einnahmen:,.2f} €", delta_color="normal")
                col3.metric("Ausgaben", f"-{ausgaben:,.2f} €", delta_color="inverse")

                st.markdown("---")
                
                # Grafiken
                g1, g2 = st.columns(2)
                
                with g1:
                    st.subheader("Ausgaben nach Kategorie")
                    ausg_df = user_df[user_df['betrag'] < 0].copy()
                    ausg_df['betrag'] = abs(ausg_df['betrag'])
                    if not ausg_df.empty:
                        fig = px.pie(ausg_df, values='betrag', names='kategorie', hole=0.5, 
                                     color_discrete_sequence=px.colors.sequential.RdBu)
                        fig.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0))
                        st.plotly_chart(fig, use_container_width=True)
                
                with g2:
                    st.subheader("Verlauf")
                    st.area_chart(user_df.set_index('datum')['betrag'].cumsum())

            else:
                st.info("Noch keine Buchungen vorhanden.")
        except:
            st.error("Bitte stelle sicher, dass die Tabelle 'transactions' die Spalten 'user' und 'betrag' hat.")

    elif menu == "💸 Neue Buchung":
        st.title("Buchung erfassen ✍️")
        with st.form("new_trans", clear_on_submit=True):
            t_type = st.segmented_control("Typ", ["Ausgabe", "Einnahme"], default="Ausgabe")
            
            c1, c2 = st.columns(2)
            with c1:
                # Number input ohne Stepper
                t_amount = st.number_input("Betrag in €", min_value=0.0, step=0.01, format="%.2f")
            with c2:
                cats = ["Essen", "Miete", "Freizeit", "Transport", "Shopping", "Fixkosten"] if t_type == "Ausgabe" else ["Gehalt", "Nebenjob", "Geschenk"]
                t_cat = st.selectbox("Kategorie", cats)
            
            t_date = st.date_input("Datum", datetime.date.today())
            t_note = st.text_input("Notiz (optional)")
            
            if st.form_submit_button("Speichern", use_container_width=True):
                if t_amount > 0:
                    final_amount = t_amount if t_type == "Einnahme" else -t_amount
                    new_data = pd.DataFrame([{"user": st.session_state['user_name'], "datum": str(t_date), "typ": t_type, "kategorie": t_cat, "betrag": final_amount, "notiz": t_note}])
                    
                    df_old = conn.read(worksheet="transactions", ttl="0")
                    df_new = pd.concat([df_old, new_data], ignore_index=True)
                    conn.update(worksheet="transactions", data=df_new)
                    st.success("Buchung gespeichert!")
                    st.balloons()
                else:
                    st.warning("Bitte einen Betrag größer als 0 eingeben.")

else:
    # (Login/Signup Bereich bleibt wie gehabt, aber mit dem CSS-Fix für das Auge von oben)
    st.markdown("<h1 style='text-align:center; color:white;'>Balancely</h1>", unsafe_allow_html=True)
    _, center_col, _ = st.columns([1, 1.2, 1])
    with center_col:
        if st.session_state['auth_mode'] == 'login':
            with st.form("l_f"):
                u_in = st.text_input("Username")
                p_in = st.text_input("Passwort", type="password")
                if st.form_submit_button("Anmelden", use_container_width=True):
                    df_u = conn.read(worksheet="users", ttl="0")
                    user_row = df_u[df_u['username'] == u_in]
                    if not user_row.empty and make_hashes(p_in) == str(user_row.iloc[0]['password']):
                        st.session_state['logged_in'] = True
                        st.session_state['user_name'] = u_in
                        st.rerun()
                    else: st.error("Login ungültig.")
            if st.button("Konto erstellen"): st.session_state['auth_mode'] = 'signup'; st.rerun()
        else:
            # Signup Form...
            if st.button("Zurück zum Login"): st.session_state['auth_mode'] = 'login'; st.rerun()
