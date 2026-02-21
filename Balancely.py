import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

# --- KONFIGURATION & CSS ---
DB_FILE = "balancely_data.csv"

st.set_page_config(page_title="Balancely ⚖️", page_icon="💰", layout="wide")

# CSS zur Verbesserung der Optik der Eingabefelder
st.markdown("""
    <style>
    .stNumberInput input {
        color: #ffffff !important;
        background-color: #262730 !important;
    }
    div[data-baseweb="input"] {
        border-color: #4b4b4b !important;
    }
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

# Initialisierung
if 'data' not in st.session_state:
    st.session_state.data = load_data()

# --- SIDEBAR: EINGABE ---
st.sidebar.title("Balancely ⚖️")
st.sidebar.subheader("Neue Buchung")

with st.sidebar.form("entry_form", clear_on_submit=True):
    datum = st.date_input("Datum", datetime.now())
    typ = st.selectbox("Typ", ["Ausgabe", "Einnahme"])
    kat = st.selectbox("Kategorie", ["Gehalt", "Essen", "Miete", "Freizeit", "Transport", "Shopping", "Abo"])
    betrag = st.number_input("Betrag in €", min_value=0.0, step=0.01, format="%.2f")
    notiz = st.text_input("Notiz")
    
    if st.form_submit_button("Speichern"):
        new_entry = pd.DataFrame([[datum, kat, typ, betrag, notiz]], 
                                columns=st.session_state.data.columns)
        st.session_state.data = pd.concat([st.session_state.data, new_entry], ignore_index=True)
        save_data(st.session_state.data)
        st.success("Erfolgreich gebucht!")
        st.rerun()

# --- HAUPTBEREICH: DASHBOARD ---
st.title("💰 Balancely Finanz-Übersicht")

if not st.session_state.data.empty:
    df = st.session_state.data
    ein = df[df["Typ"] == "Einnahme"]["Betrag"].sum()
    aus = df[df["Typ"] == "Ausgabe"]["Betrag"].sum()
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Einnahmen", f"{ein:,.2f} €")
    m2.metric("Ausgaben", f"-{aus:,.2f} €")
    m3.metric("Saldo", f"{ein - aus:,.2f} €")

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Ausgaben nach Kategorie")
        ausgaben_df = df[df["Typ"] == "Ausgabe"]
        if not ausgaben_df.empty:
            fig_pie = px.pie(ausgaben_df, values='Betrag', names='Kategorie', hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        st.subheader("Übersicht")
        fig_bar = px.bar(df.groupby("Typ")["Betrag"].sum().reset_index(), x="Typ", y="Betrag", color="Typ")
        st.plotly_chart(fig_bar, use_container_width=True)

    st.subheader("Transaktionsverlauf")
    st.dataframe(df.sort_values(by="Datum", ascending=False), use_container_width=True)

else:
    st.info("Noch keine Daten vorhanden. Nutze die Seitenleiste für deinen ersten Eintrag!")

# Optional: Reset-Button
if st.sidebar.button("Daten zurücksetzen"):
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    st.session_state.data = pd.DataFrame(columns=["Datum", "Kategorie", "Typ", "Betrag", "Notiz"])
    st.rerun()
