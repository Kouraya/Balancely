import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import hashlib
import datetime
import re
import streamlit.components.v1 as components

st.set_page_config(page_title="Balancely", page_icon="⚖️", layout="wide")

def make_hashes(text):
    return hashlib.sha256(str.encode(text)).hexdigest()

def check_password_strength(password):
    if len(password) < 6:
        return False, "Das Passwort muss mindestens 6 Zeichen lang sein."
    if not re.search(r"[a-z]", password):
        return False, "Das Passwort muss mindestens einen Kleinbuchstaben enthalten."
    if not re.search(r"[A-Z]", password):
        return False, "Das Passwort muss mindestens einen Großbuchstaben enthalten."
    return True, ""

st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] {
        background: radial-gradient(circle at top right, #1e293b, #0f172a, #020617) !important;
    }
    .main-title {
        text-align: center; color: #f8fafc; font-size: 64px; font-weight: 800;
        letter-spacing: -2px; margin-bottom: 0px;
        text-shadow: 0 0 30px rgba(56, 189, 248, 0.4);
    }
    .sub-title {
        text-align: center; color: #94a3b8; font-size: 18px; margin-bottom: 40px;
    }
    [data-testid="stForm"] {
        background-color: rgba(30, 41, 59, 0.7) !important;
        backdrop-filter: blur(15px);
        padding: 40px !important;
        border-radius: 24px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    div[data-testid="stTextInputRootElement"] {
        background-color: transparent !important;
    }
    div[data-baseweb="input"],
    div[data-baseweb="base-input"] {
        background-color: transparent !important;
        border: 1px solid #1e293b !important;
        border-radius: 8px !important;
        padding-right: 0 !important;
        gap: 0 !important;
    }
    div[data-baseweb="input"]:focus-within,
    div[data-baseweb="base-input"]:focus-within {
        background-color: transparent !important;
        border-color: #38bdf8 !important;
    }
    div[data-testid="stDateInput"] > div {
        background-color: transparent !important;
        border: 1px solid #1e293b !important;
        border-radius: 8px !important;
    }
    div[data-baseweb="select"] > div:first-child {
        background-color: transparent !important;
        border: 1px solid #1e293b !important;
        border-radius: 8px !important;
    }
    div[data-baseweb="select"] > div:first-child:focus-within {
        border-color: #38bdf8 !important;
    }
    button[data-testid="stNumberInputStepDown"],
    button[data-testid="stNumberInputStepUp"] {
        display: none !important;
    }
    div[data-testid="stNumberInput"] div[data-baseweb="input"] {
        border-radius: 8px !important;
    }
    div[data-baseweb="input"] > div:not(:has(input)):not(:has(button)):not(:has(svg)) {
        display: none !important;
    }
    [data-testid="InputInstructions"],
    [data-testid="stInputInstructions"],
    div[class*="InputInstructions"],
    div[class*="stInputInstructions"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        max-height: 0 !important;
        height: 0 !important;
        width: 0 !important;
        overflow: hidden !important;
        position: absolute !important;
        pointer-events: none !important;
    }
    input { padding-left: 15px !important; color: #f1f5f9 !important; }
    [data-testid="stSidebar"] {
        background-color: #0b0f1a !important;
        border-right: 1px solid #1e293b !important;
    }
    button[kind="primaryFormSubmit"] {
        background: linear-gradient(135deg, #38bdf8, #1d4ed8) !important;
        border: none !important; height: 50px !important;
        border-radius: 12px !important; font-weight: 700 !important;
    }
    /* iframe für Toggle-Buttons rahmenlos */
    iframe[title="toggle_buttons"] {
        border: none !important;
        margin-bottom: -1rem !important;
    }
    </style>
""", unsafe_allow_html=True)

if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'user_name' not in st.session_state: st.session_state['user_name'] = ""
if 'auth_mode' not in st.session_state: st.session_state['auth_mode'] = 'login'
if 't_type' not in st.session_state: st.session_state['t_type'] = 'Ausgabe'

conn = st.connection("gsheets", type=GSheetsConnection)

def render_toggle(current_type):
    """Rendert die Toggle-Buttons als HTML-Komponente mit postMessage-Callback."""
    ausgabe_active = current_type == "Ausgabe"
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ background: transparent; display: flex; gap: 10px; padding: 4px 2px; }}
        .btn {{
            flex: 0 0 160px;
            height: 42px;
            border-radius: 10px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            border: 1px solid #334155;
            background: transparent;
            color: #94a3b8;
            font-family: "Source Sans 3 Variable", sans-serif;
            transition: all 0.15s ease;
        }}
        .btn:hover {{ filter: brightness(1.2); }}
        .btn-ausgabe-active {{
            background: rgba(239,68,68,0.25);
            border: 2px solid #ef4444;
            color: #fca5a5;
        }}
        .btn-einnahme-active {{
            background: rgba(16,185,129,0.25);
            border: 2px solid #10b981;
            color: #6ee7b7;
        }}
    </style>
    </head>
    <body>
        <button
            class="btn {'btn-ausgabe-active' if ausgabe_active else ''}"
            onclick="window.parent.postMessage({{type:'toggle', value:'Ausgabe'}}, '*')">
            ↗ Ausgabe {'✓' if ausgabe_active else ''}
        </button>
        <button
            class="btn {'btn-einnahme-active' if not ausgabe_active else ''}"
            onclick="window.parent.postMessage({{type:'toggle', value:'Einnahme'}}, '*')">
            ↙ Einnahme {'✓' if not ausgabe_active else ''}
        </button>
    </body>
    </html>
    """
    # components.html gibt den Rückgabewert via postMessage nicht direkt zurück,
    # daher nutzen wir einen Query-Parameter-Trick über st.query_params
    clicked = components.html(html, height=52, scrolling=False)
    return clicked

if st.session_state['logged_in']:
    with st.sidebar:
        st.markdown("<h2 style='color:white;'>Balancely ⚖️</h2>", unsafe_allow_html=True)
        st.markdown(f"👤 Eingeloggt: **{st.session_state['user_name']}**")
        st.markdown("---")
        menu = st.radio("Navigation", ["📈 Dashboard", "💸 Transaktion", "📂 Analysen", "⚙️ Einstellungen"], label_visibility="collapsed")
        st.markdown("<div style='height: 30vh;'></div>", unsafe_allow_html=True)
        if st.button("Logout ➜", use_container_width=True, type="secondary"):
            st.session_state['logged_in'] = False
            st.rerun()

    if menu == "📈 Dashboard":
        st.title(f"Deine Übersicht, {st.session_state['user_name']}! ⚖️")
        try:
            df_t = conn.read(worksheet="transactions", ttl="0")
            if 'user' in df_t.columns:
                user_df = df_t[df_t['user'] == st.session_state['user_name']]
                if not user_df.empty:
                    ein = pd.to_numeric(user_df[user_df['typ'] == "Einnahme"]['betrag']).sum()
                    aus = abs(pd.to_numeric(user_df[user_df['typ'] == "Ausgabe"]['betrag']).sum())
                    bal = ein - aus
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Kontostand", f"{bal:,.2f} €")
                    c2.metric("Einnahmen", f"{ein:,.2f} €")
                    c3.metric("Ausgaben", f"{aus:,.2f} €", delta_color="inverse")
                    st.subheader("Ausgaben nach Kategorie")
                    ausg_df = user_df[user_df['typ'] == "Ausgabe"].copy()
                    ausg_df['betrag'] = abs(pd.to_numeric(ausg_df['betrag']))
                    st.bar_chart(data=ausg_df, x="kategorie", y="betrag", color="kategorie")
                else:
                    st.info("Noch keine Daten vorhanden.")
        except:
            st.warning("Verbindung wird hergestellt...")

    elif menu == "💸 Transaktion":
        st.title("Buchung hinzufügen ✍️")
        t_type = st.session_state['t_type']

        st.markdown("<p style='color:#94a3b8; font-size:13px; margin-bottom:2px;'>Typ wählen</p>", unsafe_allow_html=True)

        # Toggle via bidirektionaler HTML-Komponente
        ausgabe_active = t_type == "Ausgabe"
        toggle_html = f"""
        <!DOCTYPE html><html><head>
        <style>
            * {{ margin:0; padding:0; box-sizing:border-box; }}
            body {{ background:transparent; display:flex; gap:10px; padding:4px 2px; }}
            .btn {{
                flex: 0 0 160px; height:42px; border-radius:10px;
                font-size:14px; font-weight:600; cursor:pointer;
                border:1px solid #334155; background:transparent; color:#94a3b8;
                font-family:"Source Sans 3 Variable",sans-serif;
                transition: all 0.15s ease;
            }}
            .btn:hover {{ filter:brightness(1.2); }}
            .a {{ background:rgba(239,68,68,0.25); border:2px solid #ef4444; color:#fca5a5; }}
            .e {{ background:rgba(16,185,129,0.25); border:2px solid #10b981; color:#6ee7b7; }}
        </style>
        </head><body>
        <button class="btn {'a' if ausgabe_active else ''}"
            onclick="window.parent.postMessage({{type:'streamlit:setComponentValue',value:'Ausgabe'}},'*')">
            ↗ Ausgabe {'✓' if ausgabe_active else ''}
        </button>
        <button class="btn {'e' if not ausgabe_active else ''}"
            onclick="window.parent.postMessage({{type:'streamlit:setComponentValue',value:'Einnahme'}},'*')">
            ↙ Einnahme {'✓' if not ausgabe_active else ''}
        </button>
        <script>
            window.addEventListener('message', function(e) {{
                if (e.data.type === 'streamlit:render') {{}}
            }});
            window.parent.postMessage({{type:'streamlit:componentReady',apiVersion:1}},'*');
        </script>
        </body></html>
        """

        clicked = components.html(toggle_html, height=54, scrolling=False)

        if clicked is not None and clicked != t_type:
            st.session_state['t_type'] = clicked
            st.rerun()

        st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)

        with st.form("t_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                t_amount = st.number_input("Betrag in €", min_value=0.01, step=0.01, format="%.2f")
                t_date = st.date_input("Datum", datetime.date.today())
            with col2:
                cats = ["Gehalt", "Bonus", "Verkauf"] if t_type == "Einnahme" else ["Essen", "Miete", "Freizeit", "Transport", "Shopping"]
                t_cat = st.selectbox("Kategorie", cats)
                t_note = st.text_input("Notiz")

            if st.form_submit_button("Speichern", use_container_width=True):
                new_row = pd.DataFrame([{
                    "user": st.session_state['user_name'],
                    "datum": str(t_date),
                    "typ": t_type,
                    "kategorie": t_cat,
                    "betrag": t_amount if t_type == "Einnahme" else -t_amount,
                    "notiz": t_note
                }])
                df_old = conn.read(worksheet="transactions", ttl="0")
                df_new = pd.concat([df_old, new_row], ignore_index=True)
                conn.update(worksheet="transactions", data=df_new)
                st.success(f"✅ {t_type} über {t_amount:.2f} € gespeichert!")
                st.balloons()

else:
    st.markdown("<div style='height: 8vh;'></div>", unsafe_allow_html=True)
    st.markdown("<h1 class='main-title'>Balancely</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>Verwalte deine Finanzen mit Klarheit</p>", unsafe_allow_html=True)

    _, center_col, _ = st.columns([1, 1.2, 1])

    with center_col:
        if st.session_state['auth_mode'] == 'login':
            with st.form("l_f"):
                st.markdown("<h3 style='text-align:center; color:white;'>Anmelden</h3>", unsafe_allow_html=True)
                u_in = st.text_input("Username", placeholder="Benutzername")
                p_in = st.text_input("Passwort", type="password")
                if st.form_submit_button("Anmelden"):
                    df_u = conn.read(worksheet="users", ttl="0")
                    user_row = df_u[df_u['username'] == u_in]
                    if not user_row.empty and make_hashes(p_in) == str(user_row.iloc[0]['password']):
                        st.session_state['logged_in'] = True
                        st.session_state['user_name'] = u_in
                        st.rerun()
                    else:
                        st.error("Login ungültig.")
            if st.button("Konto erstellen", use_container_width=True):
                st.session_state['auth_mode'] = 'signup'
                st.rerun()

        else:
            with st.form("s_f"):
                st.markdown("<h3 style='text-align:center; color:white;'>Registrierung</h3>", unsafe_allow_html=True)
                s_name = st.text_input("Name", placeholder="Max Mustermann")
                s_user = st.text_input("Username", placeholder="max123")
                s_pass = st.text_input("Passwort", type="password")
                c_pass = st.text_input("Passwort wiederholen", type="password")

                if st.form_submit_button("Konto erstellen"):
                    if not s_name or not s_user or not s_pass:
                        st.error("❌ Bitte fülle alle Felder aus!")
                    elif len(s_name.strip().split()) < 2:
                        st.error("❌ Bitte gib deinen vollständigen Vor- und Nachnamen an.")
                    else:
                        is_strong, msg = check_password_strength(s_pass)
                        if not is_strong:
                            st.error(f"❌ {msg}")
                        elif s_pass != c_pass:
                            st.error("❌ Die Passwörter stimmen nicht überein.")
                        else:
                            df_u = conn.read(worksheet="users", ttl="0")
                            if s_user in df_u['username'].values:
                                st.error("⚠️ Dieser Username ist bereits vergeben.")
                            else:
                                new_u = pd.DataFrame([{
                                    "name": make_hashes(s_name.strip()),
                                    "username": s_user,
                                    "password": make_hashes(s_pass)
                                }])
                                conn.update(worksheet="users", data=pd.concat([df_u, new_u], ignore_index=True))
                                st.success("✅ Konto erstellt! Bitte logge dich ein.")
                                st.balloons()
                                st.session_state['auth_mode'] = 'login'

            if st.button("Zurück zum Login", use_container_width=True):
                st.session_state['auth_mode'] = 'login'
                st.rerun()
