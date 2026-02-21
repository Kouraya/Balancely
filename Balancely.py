import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

# --- KONFIGURATION ---
DB_FILE = "balancely_data.csv"

st.set_page_config(page_title="Balancely ⚖️", page_icon="💰", layout="wide")

# Styling für ein schickes Dashboard
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- DATEN-FUNKTIONEN ---
def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        df['Datum'] = pd.to_datetime(df['Datum']).dt.date
        return df
    return pd.DataFrame(columns=["Datum", "Kategorie", "Typ", "Betrag", "Notiz"])

def save_data(df):
    df.to_csv(DB_FILE, index=False)

# Initialisierung des Speichers
if 'data' not in st.session_state:
    st.session_state.data = load_data()

# --- SIDEBAR: EINGABE ---
st.sidebar.image("https://img.icons8.com/fluency/96/000000/scales.png", width=80)
st.sidebar.title("Balancely")
st.sidebar.subheader("Neue Buchung")

with st.sidebar.form("entry_form", clear_on_submit=True):
    datum = st.date_input("Wann?", datetime.now())
    typ = st.selectbox("Was ist es?", ["Ausgabe", "Einnahme"])
    kat = st.selectbox("Kategorie", ["Gehalt", "Essen", "Miete", "Freizeit", "Transport", "Shopping", "Abo"])
    betrag = st.number_input("Betrag in €", min_value=0.01, step=0.50)
    notiz = st.text_input("Notiz (optional)")
    
    if st.form_submit_button("Speichern"):
        new_entry = pd.DataFrame([[datum, kat, typ, betrag, notiz]], 
                                columns=st.session_state.data.columns)
        st.session_state.data = pd.concat([st.session_state.data, new_entry], ignore_index=True)
        save_data(st.session_state.data)
        st.sidebar.success("Gebucht!")
        st.rerun()

# --- HAUPTBEREICH: DASHBOARD ---
st.title("⚖️ Balancely: Dein Finanz-Dashboard")

if not st.session_state.data.empty:
    # Berechnung der Kennzahlen
    df = st.session_state.data
    ein = df[df["Typ"] == "Einnahme"]["Betrag"].sum()
    aus = df[df["Typ"] == "Ausgabe"]["Betrag"].sum()
    kontostand = ein - aus

    # Metriken Anzeigen
    m1, m2, m3 = st.columns(3)
    m1.metric("Gesamt-Einnahmen", f"{ein:,.2f} €")
    m2.metric("Gesamt-Ausgaben", f"-{aus:,.2f} €", delta_color="inverse")
    m3.metric("Aktuelle Balance", f"{kontostand:,.2f} €")

    st.divider()

    # Visualisierungen
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Ausgaben nach Kategorien")
        ausgaben_df = df[df["Typ"] == "Ausgabe"]
        if not ausgaben_df.empty:
            fig_pie = px.pie(ausgaben_df, values='Betrag', names='Kategorie', 
                            hole=0.5, color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Noch keine Ausgaben für Statistiken.")

    with c2:
        st.subheader("Einnahmen vs. Ausgaben")
        fig_bar = px.bar(df.groupby("Typ")["Betrag"].sum().reset_index(), 
                        x="Typ", y="Betrag", color="Typ", 
                        color_discrete_map={"Einnahme": "#00CC96", "Ausgabe": "#EF553B"})
        st.plotly_chart(fig_bar, use_container_width=True)

    # Historie
    st.subheader("Letzte Transaktionen")
    st.dataframe(df.sort_values(by="Datum", ascending=False), use_container_width=True)
    
    if st.button("Alle Daten löschen (Reset)"):
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
        st.session_state.data = pd.DataFrame(columns=["Datum", "Kategorie", "Typ", "Betrag", "Notiz"])
        st.rerun()

else:
    st.info("Willkommen bei Balancely! Füge links deine erste Einnahme oder Ausgabe hinzu.")