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

# --- 2. DESIGN-OPTIMIERUNG (CSS) ---
st.markdown("""
    <style>
    /* Hintergrund und Karten-Design */
    .stApp { background-color: #0e1117; }
    
    /* Eingabefelder in Spalten optimieren */
    div[data-testid="stNumberInput"] {
        background-color: #161b22;
        border-radius: 8px;
        padding: 2px;
    }
    
    /* Verhindert das "Rote Leuchten" bei Startwert 0.00 */
    input[aria-invalid="true"] {
        border-color: rgba(255, 255, 255, 0.1) !important;
        box-shadow: none !important;
    }

    /* Hilfstext unter Eingabefeldern ausblenden (vermeidet Quetschen) */
    div[data-testid="stMarkdownContainer"] p {
        font-size: 0.85rem !important;
        margin-bottom: 0px !important;
    }

    /* Metriken (KPIs) verschönern */
    [data-testid="stMetric"] {
        background-color: #1f2937;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #374151;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATEN-LOGIK ---
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

# --- 4. HEADER & NAVIGATION ---
st.title("⚖️ Balancely")
st.write("Dein Weg zur finanziellen Übersicht.")

# --- 5. EINGABE-BEREICH (HORIZONTAL) ---
with st.expander("➕ Neue Buchung erfassen", expanded=True):
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
            # Fix: Startwert 0.0 verhindert rote Fehlermarkierung
            betrag = st.number_input("Betrag in €", min_value=0.0, step=0.01, format="%.2f")
        
        notiz = st.text_input("Notiz (optional)")
        
        submit = st.form_submit_button("Buchung speichern", use_container_width=True)
        
        if submit:
            if betrag > 0:
                new_entry = pd.DataFrame([[datum, kat, typ, betrag, notiz]], 
                                        columns=st.session_state.data.columns)
                st.session_state.data = pd.concat([st.session_state.data, new_entry], ignore_index=True)
                save_data(st.session_state.data)
                st.success(f"Erfolgreich hinzugefügt: {betrag:.2f} €")
                st.rerun()
            else:
                st.warning("Bitte gib einen Betrag ein.")

st.divider()

# --- 6. DASHBOARD & STATISTIKEN ---
if not st.session_state.data.empty:
    df = st.session_state.data
    
    # Berechnungen
    ein = df[df["Typ"] == "Einnahme"]["Betrag"].sum()
    aus = df[df["Typ"] == "Ausgabe"]["Betrag"].sum()
    bilanz = ein - aus

    # Info-Karten
    m1, m2, m3 = st.columns(3)
    m1.metric("Einnahmen", f"{ein:,.2f} €")
    m2.metric("Ausgaben", f"-{aus:,.2f} €", delta_color="inverse")
    m3.metric("Balance", f"{bilanz:,.2f} €")

    st.write("### Analyse")
    c1, c2 = st.columns([1, 1])

    with c1:
        ausgaben_df = df[df["Typ"] == "Ausgabe"]
        if not ausgaben_df.empty:
            fig_pie = px.pie(ausgaben_df, values='Betrag', names='Kategorie', 
                            title="Ausgaben nach Kategorie", hole=0.5,
                            color_discrete_sequence=px.colors.qualitative.Safe)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Noch keine Ausgaben für Statistik verfügbar.")

    with c2:
        df_sorted = df.sort_values("Datum")
        fig_bar = px.bar(df_sorted, x="Datum", y="Betrag", color="Typ", 
                        title="Verlauf der Buchungen", barmode="group",
                        color_discrete_map={"Einnahme": "#00CC96", "Ausgabe": "#EF553B"})
        st.plotly_chart(fig_bar, use_container_width=True)

    # Transaktionsliste
    st.subheader("Letzte Buchungen")
    st.dataframe(df.sort_values(by="Datum", ascending=False), use_container_width=True, hide_index=True)
    
    # Reset in der Sidebar
    if st.sidebar.button("🗑️ Alle Daten löschen"):
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
        st.session_state.data = pd.DataFrame(columns=["Datum", "Kategorie", "Typ", "Betrag", "Notiz"])
        st.rerun()

else:
    st.info("Willkommen bei Balancely! Erfasse oben deine erste Buchung, um das Dashboard zu aktivieren.")
