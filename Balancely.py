"""
Balancely — Entry point: Auth only.
"""
import datetime
import time
import pandas as pd
import streamlit as st

from database import _gs_read, _gs_update
from styling import inject_base_css
from utils import make_hashes, check_password_strength, is_valid_email, generate_code, send_email, email_html, is_verified
from shared import init_session

st.set_page_config(page_title="Balancely", page_icon="⚖️", layout="wide")
init_session()
inject_base_css()

# Bereits eingeloggt → zum Dashboard
if st.session_state['logged_in']:
    # Kleiner Buffer damit Streamlit Pages vollständig registriert sind
    if st.session_state.get('_switch_ready'):
        st.session_state.pop('_switch_ready', None)
        st.switch_page("pages/1_Dashboard.py")
    else:
        st.session_state['_switch_ready'] = True
        st.rerun()
    st.stop()

# ── Auth ──────────────────────────────────────────────────────
st.markdown("<div style='height:10vh;'></div>", unsafe_allow_html=True)
st.markdown("<h1 class='main-title'>Balancely</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-title'>Verwalte deine Finanzen mit Klarheit</p>", unsafe_allow_html=True)

_, center_col, _ = st.columns([1, 1.2, 1])
with center_col:
    mode = st.session_state['auth_mode']

    if mode == 'login':
        with st.form("login_form"):
            st.markdown("<h3 style='text-align:center;color:#e2e8f0;font-family:DM Sans,sans-serif;font-weight:600;font-size:22px;letter-spacing:-0.5px;margin-bottom:24px;'>Anmelden</h3>", unsafe_allow_html=True)
            u_in = st.text_input("Username", placeholder="Benutzername")
            p_in = st.text_input("Passwort", type="password")
            if st.form_submit_button("Anmelden", use_container_width=True):
                time.sleep(1)
                df_u     = _gs_read("users")
                matching = df_u[df_u['username'] == u_in]
                user_row = matching.iloc[[-1]] if not matching.empty else matching
                if not user_row.empty and make_hashes(p_in) == str(user_row.iloc[0]['password']):
                    if not is_verified(user_row.iloc[0].get('verified', 'True')):
                        st.error("❌ Bitte verifiziere zuerst deine E-Mail-Adresse.")
                    else:
                        st.session_state.update({'logged_in': True, 'user_name': u_in})
                else:
                    st.error("❌ Login ungültig.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Konto erstellen", use_container_width=True):
                st.session_state['auth_mode'] = 'signup'; st.rerun()
        with col2:
            if st.button("Passwort vergessen?", use_container_width=True, type="secondary"):
                st.session_state['auth_mode'] = 'forgot'; st.rerun()

    elif mode == 'signup':
        with st.form("signup_form"):
            st.markdown("<h3 style='text-align:center;color:#e2e8f0;font-family:DM Sans,sans-serif;font-weight:600;font-size:22px;letter-spacing:-0.5px;margin-bottom:24px;'>Registrierung</h3>", unsafe_allow_html=True)
            s_name  = st.text_input("Name", placeholder="Max Mustermann")
            s_user  = st.text_input("Username", placeholder="max123")
            s_email = st.text_input("E-Mail", placeholder="max@beispiel.de")
            s_pass  = st.text_input("Passwort", type="password")
            c_pass  = st.text_input("Passwort wiederholen", type="password")
            if st.form_submit_button("Konto erstellen", use_container_width=True):
                if not all([s_name, s_user, s_email, s_pass]):   st.error("❌ Bitte fülle alle Felder aus!")
                elif len(s_name.strip().split()) < 2:             st.error("❌ Bitte gib deinen vollständigen Vor- und Nachnamen an.")
                elif not is_valid_email(s_email):                 st.error("❌ Bitte gib eine gültige E-Mail-Adresse ein.")
                else:
                    ok, msg = check_password_strength(s_pass)
                    if not ok:            st.error(f"❌ {msg}")
                    elif s_pass != c_pass: st.error("❌ Die Passwörter stimmen nicht überein.")
                    else:
                        df_u = _gs_read("users")
                        if s_user in df_u['username'].values:                 st.error("⚠️ Dieser Username ist bereits vergeben.")
                        elif s_email.strip().lower() in df_u['email'].values: st.error("⚠️ Diese E-Mail ist bereits registriert.")
                        else:
                            code   = generate_code()
                            expiry = datetime.datetime.now() + datetime.timedelta(minutes=10)
                            if send_email(s_email.strip().lower(), "Balancely – E-Mail verifizieren", email_html("Willkommen bei Balancely! Dein Verifizierungscode lautet:", code)):
                                st.session_state.update({
                                    'pending_user': {"name": make_hashes(s_name.strip()), "username": s_user, "email": s_email.strip().lower(), "password": make_hashes(s_pass)},
                                    'verify_code': code, 'verify_expiry': expiry, 'auth_mode': 'verify_email',
                                })
                                st.rerun()
                            else:
                                st.error("❌ E-Mail konnte nicht gesendet werden.")
        if st.button("Zurück zum Login", use_container_width=True):
            st.session_state['auth_mode'] = 'login'; st.rerun()

    elif mode == 'verify_email':
        pending_email = st.session_state['pending_user'].get('email', '')
        with st.form("verify_form"):
            st.markdown(
                f"<h3 style='text-align:center;color:#e2e8f0;font-size:22px;font-weight:600;margin-bottom:12px;'>E-Mail verifizieren</h3>"
                f"<p style='text-align:center;color:#475569;font-size:14px;margin-bottom:20px;'>Code gesendet an <span style='color:#38bdf8;'>{pending_email}</span></p>",
                unsafe_allow_html=True,
            )
            code_input = st.text_input("Code eingeben", placeholder="123456", max_chars=6)
            if st.form_submit_button("Bestätigen", use_container_width=True):
                if st.session_state['verify_expiry'] and datetime.datetime.now() > st.session_state['verify_expiry']:
                    st.error("⏰ Code abgelaufen.")
                    st.session_state['auth_mode'] = 'signup'; st.rerun()
                elif code_input.strip() != st.session_state['verify_code']:
                    st.error("❌ Falscher Code.")
                else:
                    df_u  = _gs_read("users")
                    new_u = pd.DataFrame([{**st.session_state['pending_user'], "verified": "True", "token": "", "token_expiry": ""}])
                    _gs_update("users", pd.concat([df_u, new_u], ignore_index=True))
                    st.session_state.update({'pending_user': {}, 'verify_code': "", 'verify_expiry': None, 'auth_mode': 'login'})
                    st.success("✅ E-Mail verifiziert! Du kannst dich jetzt einloggen.")
        if st.button("Zum Login", use_container_width=True, type="primary"):
            st.session_state['auth_mode'] = 'login'; st.rerun()

    elif mode == 'forgot':
        with st.form("forgot_form"):
            st.markdown("<h3 style='text-align:center;color:#e2e8f0;font-size:22px;font-weight:600;margin-bottom:12px;'>Passwort vergessen</h3>", unsafe_allow_html=True)
            forgot_email = st.text_input("E-Mail", placeholder="deine@email.de")
            if st.form_submit_button("Code senden", use_container_width=True):
                if not is_valid_email(forgot_email):
                    st.error("❌ Bitte gib eine gültige E-Mail-Adresse ein.")
                else:
                    df_u = _gs_read("users")
                    idx  = df_u[df_u['email'] == forgot_email.strip().lower()].index
                    if idx.empty:
                        st.success("✅ Falls diese E-Mail registriert ist, wurde ein Code gesendet.")
                    else:
                        code   = generate_code()
                        expiry = datetime.datetime.now() + datetime.timedelta(minutes=10)
                        if send_email(forgot_email.strip().lower(), "Balancely – Passwort zurücksetzen", email_html("Dein Code zum Zurücksetzen des Passworts lautet:", code)):
                            st.session_state.update({'reset_email': forgot_email.strip().lower(), 'reset_code': code, 'reset_expiry': expiry, 'auth_mode': 'reset_password'})
                            st.rerun()
        if st.button("Zurück zum Login", use_container_width=True):
            st.session_state['auth_mode'] = 'login'; st.rerun()

    elif mode == 'reset_password':
        with st.form("reset_form"):
            st.markdown(
                f"<h3 style='text-align:center;color:#e2e8f0;font-size:22px;font-weight:600;margin-bottom:12px;'>Passwort zurücksetzen</h3>"
                f"<p style='text-align:center;color:#475569;font-size:14px;margin-bottom:20px;'>Code gesendet an <span style='color:#38bdf8;'>{st.session_state['reset_email']}</span></p>",
                unsafe_allow_html=True,
            )
            code_input = st.text_input("6-stelliger Code", placeholder="123456", max_chars=6)
            pw_neu     = st.text_input("Neues Passwort", type="password")
            pw_neu2    = st.text_input("Passwort wiederholen", type="password")
            if st.form_submit_button("Passwort speichern", use_container_width=True):
                if st.session_state['reset_expiry'] and datetime.datetime.now() > st.session_state['reset_expiry']:
                    st.error("⏰ Code abgelaufen.")
                    st.session_state['auth_mode'] = 'forgot'; st.rerun()
                elif code_input.strip() != st.session_state['reset_code']:
                    st.error("❌ Falscher Code.")
                else:
                    ok, msg = check_password_strength(pw_neu)
                    if not ok:             st.error(f"❌ {msg}")
                    elif pw_neu != pw_neu2: st.error("❌ Die neuen Passwörter stimmen nicht überein.")
                    else:
                        df_u = _gs_read("users")
                        idx  = df_u[df_u['email'] == st.session_state['reset_email']].index
                        if not idx.empty:
                            df_u.loc[idx[0], 'password'] = make_hashes(pw_neu)
                            _gs_update("users", df_u)
                        st.session_state.update({'reset_email': "", 'reset_code': "", 'reset_expiry': None, 'auth_mode': 'login'})
                        st.success("✅ Passwort geändert! Du kannst dich jetzt einloggen.")
                        st.rerun()
        if st.button("Zurück zum Login", use_container_width=True):
            st.session_state['auth_mode'] = 'login'; st.rerun()
