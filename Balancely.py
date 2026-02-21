import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

# --- 1. SEITEN-KONFIGURATION ---
st.set_page_config(
    page_title="Balancely ⚖️", 
    page_icon="💰", 
    layout="wide"
)

DB_FILE = "balancely_data.csv"

# --- 2. ERWEITERTES CSS FÜR DESIGN-FIXES ---
st.markdown("""
    <style>
    /* Hintergrundfarbe der App */
    .stApp { background-color: #0e1117; }
    
    /* Eingabefelder stylen und vergrößern */
    div[data-testid="stNumberInput"] {
        background-color: #161b22;
        border-radius: 10px;
        padding: 5px;
    }
    
    /* Den roten Rahmen bei 0.00 Euro unterdrücken */
    input[aria-invalid="true"] {
        border-color: rgba(255, 255, 255, 0.1) !important;
        box-shadow: none !important;
    }

    /* Metriken schöner anzeigen */
    [data-testid="stMetric"] {
        background-color: #1f2937;
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #374151;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATEN-FUNKTIONEN ---
def load_data():
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            df['Datum'] = pd.to_datetime(df['Datum']).dt.date
            return df
        except:
            return pd.DataFrame(columns=["Datum", "Kategorie", "Typ", "Betrag", "Notiz"])
    return pd.DataFrame(columns=["Datum", "Kategorie", "Typ", "Betrag", "Notiz"])

def save_data(df):
    df.to_csv(DB_FILE, index=False)

if 'data' not in st.session_state:
    st.session_state.data = load_data()

# --- 4. HEADER ---
st.title("⚖️ Balancely")
st.write("Dein intelligentes Finanz-Dashboard")

# --- 5. EINGABE-BEREICH (JETZT OBEN IM HAUPTFENSTER) ---
with st.expander("➕ Neue Transaktion hinzufügen", expanded=True):
    with st.form("main_form", clear_on_submit=True):
        col_date, col_type, col_kat, col_amt = st.columns(4)
        
        with col_date:
            datum = st.date_input("Datum", datetime.now())
        with col_type:
            typ = st.selectbox("Typ", ["Ausgabe", "Einnahme"])
        with col_kat:
            kat = st.selectbox("Kategorie", [
                "Gehalt", "Essen & Trinken", "Miete", "Freizeit", 
                "Transport", "Shopping", "Abo & Verträge", "Sonstiges"
            ])
        with col_amt:
            # Fix: Startwert auf 0.00 und explizites Format
            betrag = st.number_input("Betrag in €", min_value=0.0, step=0.01, format="%.2f")
        
        notiz = st.text_input("Notiz / Beschreibung (optional)")
        
        submit = st.form_submit_button("Buchung speichern", use_container_width=True)
        
        if submit:
            if betrag > 0:
                new_entry = pd.DataFrame([[datum, kat, typ, betrag, notiz]], 
                                        columns=st.session_state.data.columns)
                st.session_state.data = pd.concat([st.session_state.data, new_entry], ignore_index=True)
                save_data(st.session_state.data)
                st.success(f"Gespeichert: {betrag:.2f} € für {kat}")
                st.rerun()
            else:
                st.warning("Bitte gib einen Betrag größer als 0 ein.")

st.divider()

# --- 6. DASHBOARD-ANZEIGE ---
if not st.session_state.data.empty:
    df = st.session_state.data
    ein = df[df["Typ"] == "Einnahme"]["Betrag"].sum()
    aus = df[df["Typ"] == "Ausgabe"]["Betrag"].sum()
    bilanz = ein - aus

    # Kennzahlen
    m1, m2, m3 = st.columns(3)
    m1.metric("Einnahmen", f"{ein:,.2f} €")
    m2.metric("Ausgaben", f"-{aus:,.2f} €", delta_color="inverse")
    m3.metric("Kontostand", f"{bilanz:,.2f} €")

    st.write("### Statistiken & Verlauf")
    c1, c2 = st.columns([1, 1])

    with c1:
        ausgaben_df = df[df["Typ"] == "
