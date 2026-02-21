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

# --- 3. CSS (DER FINALE FIX FÜR DAS GRÜNE HIGHLIGHT) ---
st.markdown("""
    <style>
    /* Hintergrund */
    [data-testid="stAppViewContainer"] {
        background: radial-gradient(circle at top right, #1e293b, #0f172a, #020617) !important;
    }
    
    /* SEGMENTED CONTROL FIX */
    /* Wir erzwingen Grün für den ausgewählten Button und entfernen den roten Glow */
    div[data-testid="stSegmentedControl"] button[aria-checked="true"] {
        background-color: #10b981 !important; /* Emerald Green */
        color: white !important;
        border: 1px solid #10b981 !important;
    }
    
    /* Verhindert, dass Streamlit beim Hovern oder Klicken Rot anzeigt */
    div[data-testid="stSegmentedControl"] button[aria-checked="true"]:hover {
        border-color: #059669 !important;
        background-color: #059669 !important;
    }

    /* Entfernt die Plus/Minus Pfeile im Zahlenfeld */
    input[type=number]::-webkit-inner-spin-button, 
    input[type=number]::-webkit-outer-spin-button { 
        -webkit-appearance: none; margin: 0; 
    }
    input[type=number] { -moz-appearance: textfield; }

    /* Eingabefelder allgemein */
    div[data-baseweb="input"] {
        background-color: rgba(15, 23, 42, 0.9) !important;
        border: 1px solid #334155 !important;
        border-radius: 10px !important;
    }
    
    [data-testid="stSidebar"] { background-color: #0b0f1a !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. SESSION STATE ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'user_name' not in st.session_state: st.session_state['user_name'] = ""
if 'auth_mode' not in st.session_state: st.session_state['auth_mode'] = 'login'

conn = st.connection("gsheets", type=GSheetsConnection)

# --- 5. HAUPTLOGIK ---

if st.session_state['logged_in']:
    with st.sidebar:
        st.markdown(f"## Balancely ⚖️")
        st.write(f"👤 **{st.session_state['user_name']}**")
        st.markdown("---")
        menu = st.radio("Navigation", ["📈 Dashboard", "💸 Buchung erfassen", "⚙️ Einstellungen"])
        st.markdown("<div style='height: 30vh;'></div>", unsafe_allow_html=True)
        if st.button("Abmelden ➔", use_container_width=True):
            st.session_state['logged_in'] = False
            st.rerun()

    if menu == "📈 Dashboard":
        st.title("Finanz-Übersicht")
        try:
            df_t = conn.read(worksheet="transactions", ttl="0")
            user_df = df_t[df_t['user'] == st.session_state['user_name']]
            
            if not user_df.empty:
                user_df['betrag'] = pd.to_numeric(user_df['betrag'])
                ein = user_df[user_df['betrag'] > 0]['betrag'].sum()
                aus = abs(user_df[user_df['betrag'] < 0]['betrag'].sum())
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Saldo", f"{ein-aus:,.2f} €")
                c2.metric("Einnahmen", f"{ein:,.2f} €")
                c3.metric("Ausgaben", f"-{aus:,.2f} €", delta_color="inverse")
                
                ausg_df = user_df[user_df['betrag'] < 0].copy()
                ausg_df['betrag'] = abs(ausg_df['betrag'])
                if not ausg_df.empty:
                    fig = px.pie(ausg_df, names="kategorie", values="betrag", hole=0.4)
                    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="white")
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Noch keine Daten vorhanden.")
        except:
            st.warning("Verbindung wird aufgebaut...")

    elif menu == "💸 Buchung erfassen":
        st.title("Neue Buchung ✍️")
        
        with st.form("entry_form", clear_on_submit=True):
            # Typ-Auswahl (Jetzt garantiert grün durch CSS)
            t_type = st.segmented_control("Typ", ["Ausgabe", "Einnahme"], default="Ausgabe")
            
            col1, col2 = st.columns(2)
            with col1:
                t_amount = st.number_input("Betrag in €", min_value=0.0, step=0.01, format="%.2f")
                t_date = st.date_input("Datum", datetime.date.today())
            
            with col2:
                base_cats = ["Essen", "Miete", "Freizeit", "Transport"] if t_type == "Ausgabe" else ["Gehalt", "Geschenk"]
                t_cat_select = st.selectbox("Kategorie", base_cats + ["+ Eigene Kategorie..."])
                
                t_cat_custom = ""
                if t_cat_select == "+ Eigene Kategorie...":
                    t_cat_custom = st.text_input("Name der neuen Kategorie")
            
            t_note = st.text_input("Notiz (optional)")
            
            if st.form_submit_button("Speichern", use_container_width=True):
                final_cat = t_cat_custom if t_cat_select == "+ Eigene Kategorie..." else t_cat_select
                
                if t_amount > 0 and final_cat != "":
                    final_val = t_amount if t_type == "Einnahme" else -t_amount
                    new_entry = pd.DataFrame([{
                        "user": st.session_state['user_name'],
                        "datum": str(t_date),
                        "typ": t_type,
                        "kategorie": final_cat,
                        "betrag": final_val,
                        "notiz": t_note
                    }])
                    
                    old_df = conn.read(worksheet="transactions", ttl="0")
                    updated_df = pd.concat([old_df, new_entry], ignore_index=True)
                    conn.update(worksheet="transactions", data=updated_df)
                    st.success(f"Gebucht: {final_cat} ({final_val}€)")
                    st.balloons()
                else:
                    st.error("Bitte Betrag und Kategorie prüfen!")

else:
    # --- LOGIN BEREICH ---
    st.markdown("<h1 style='text-align:center;'>Balancely</h1>", unsafe_allow_html=True)
    _, center_col, _ = st.columns([1, 1.2, 1])
    
    with center_col:
        if st.session_state['auth_mode'] == 'login':
            with st.form("login_form"):
                u_in = st.text_input("Username")
                p_in = st.text_input("Passwort", type="password")
                if st.form_submit_button("Anmelden", use_container_width=True):
                    df_u = conn.read(worksheet="users", ttl="0")
                    user_row = df_u[df_u['username'] == u_in]
                    if not user_row.empty and make_hashes(p_in) == str(user_row.iloc[0]['password']):
                        st.session_state['logged_in'] = True
                        st.session_state['user_name'] = u_in
                        st.rerun()
                    else: st.error("Logindaten falsch.")
            if st.button("Neu hier? Registrieren"):
                st.session_state['auth_mode'] = 'signup'
                st.rerun()
        else:
            with st.form("signup_form"):
                s_user = st.text_input("Wunsch-Username")
                s_pass = st.text_input("Passwort", type="password")
                if st.form_submit_button("Konto erstellen", use_container_width=True):
                    df_u = conn.read(worksheet="users", ttl="0")
                    new_u = pd.DataFrame([{"username": s_user, "password": make_hashes(s_pass)}])
                    conn.update(worksheet="users", data=pd.concat([df_u, new_u], ignore_index=True))
                    st.success("Erstellt! Logge dich nun ein.")
                    st.session_state['auth_mode'] = 'login'
            if st.button("Zurück zum Login"):
                st.session_state['auth_mode'] = 'login'
                st.rerun()
