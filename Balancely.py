"""
Balancely — Persönliche Finanzverwaltung v4
Entry point: orchestrates auth, sidebar, and page routing.
"""

import datetime
import time
import pandas as pd
import streamlit as st

from constants import THEMES, CURRENCY_SYMBOLS
from database import (
    _gs_read, _gs_update, _gs_invalidate,
    load_user_settings, apply_dauerauftraege,
)
from styling import inject_base_css, inject_theme
from utils import make_hashes, check_password_strength, is_valid_email, generate_code, send_email, email_html, is_verified

import pages.dashboard    as page_dashboard
import pages.transactions as page_transactions
import pages.analytics    as page_analytics
import pages.savings_pots as page_savings_pots
import pages.settings     as page_settings

# ── Page config ───────────────────────────────────────────────
st.set_page_config(page_title="Balancely", page_icon="⚖️", layout="wide")

# ── Session State Init ────────────────────────────────────────
_DEFAULTS = {
    'logged_in': False, 'user_name': "", 'auth_mode': 'login', 't_type': 'Ausgabe',
    'pending_user': {}, 'verify_code': "", 'verify_expiry': None,
    'reset_email': "", 'reset_code': "", 'reset_expiry': None,
    'edit_idx': None, 'show_new_cat': False, 'new_cat_typ': 'Ausgabe', '_last_menu': "",
    'edit_cat_data': None, 'delete_cat_data': None,
    'dash_month_offset': 0, 'dash_selected_aus': None, 'dash_selected_ein': None,
    'dash_selected_cat': None, 'dash_selected_typ': None, 'dash_selected_color': None,
    'analysen_zeitraum': 'Monatlich', 'analysen_month_offset': 0,
    'heatmap_month_offset': 0,
    'topf_edit_data': None, 'topf_delete_id': None, 'topf_delete_name': None,
    'settings_tab': 'Profil',
    'email_verify_code': "", 'email_verify_expiry': None, 'email_verify_new': "",
    'theme': 'Ocean Blue',
    'confirm_reset': False, 'confirm_delete_account': False,
    'tx_page': 0, 'tx_search': "",
}
for k, v in _DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

inject_base_css()

# ── Authenticated app ─────────────────────────────────────────
if st.session_state['logged_in']:
    _theme_name    = st.session_state.get('theme', 'Ocean Blue')
    _t             = THEMES.get(_theme_name, THEMES['Ocean Blue'])
    _user_settings = load_user_settings(st.session_state['user_name'])
    _currency_sym  = CURRENCY_SYMBOLS.get(_user_settings.get('currency', 'EUR'), '€')

    inject_theme(_t)


    if _user_settings.get('theme') and _user_settings['theme'] != st.session_state.get('theme'):
        st.session_state['theme'] = _user_settings['theme']

    if datetime.date.today().day == 1:
        booked = apply_dauerauftraege(st.session_state['user_name'])
        if booked > 0:
            _gs_invalidate("transactions")
            st.toast(f"✅ {booked} Dauerauftrag/-aufträge gebucht", icon="⚙️")

    # ── Sidebar ───────────────────────────────────────────────
    with st.sidebar:
        st.markdown(
            f"<div style='padding:8px 0 16px 0;'>"
            f"<span style='font-family:DM Sans,sans-serif;font-size:20px;font-weight:600;color:#e2e8f0;letter-spacing:-0.5px;'>Balancely</span>"
            f"<span style='color:{_t['primary']};font-size:20px;'> ⚖️</span></div>",
            unsafe_allow_html=True,
        )

        _avatar   = _user_settings.get('avatar_url', '')
        _initials = st.session_state['user_name'][:2].upper()
        if _avatar and _avatar.startswith('http'):
            avatar_html = (
                f"<img src='{_avatar}' style='width:36px;height:36px;border-radius:50%;"
                f"object-fit:cover;border:2px solid {_t['primary']}40;'>"
            )
        else:
            avatar_html = (
                f"<div style='width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,{_t['accent']},{_t['accent2']});"
                f"display:flex;align-items:center;justify-content:center;font-family:DM Sans,sans-serif;"
                f"font-size:13px;font-weight:600;color:#fff;flex-shrink:0;'>{_initials}</div>"
            )
        st.markdown(
            f"<div style='display:flex;align-items:center;gap:10px;margin-bottom:20px;'>{avatar_html}"
            f"<div><div style='font-family:DM Sans,sans-serif;font-size:13px;color:#e2e8f0;font-weight:500;'>{st.session_state['user_name']}</div>"
            f"<div style='font-family:DM Mono,monospace;font-size:10px;color:#334155;'>{_user_settings.get('currency', 'EUR')} · {_theme_name}</div></div></div>",
            unsafe_allow_html=True,
        )

        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        menu = st.radio(
            "Navigation",
            ["📈 Dashboard", "💸 Transaktionen", "📂 Analysen", "🪣 Spartöpfe", "⚙️ Einstellungen"],
            label_visibility="collapsed",
        )
        st.markdown("<div style='height:28vh;'></div>", unsafe_allow_html=True)
        if st.button("Logout ➜", use_container_width=True, type="secondary"):
            for k in [k for k in st.session_state if k.startswith("_gs_cache_")]:
                del st.session_state[k]
            st.session_state['logged_in'] = False
            st.rerun()

    if not st.session_state.pop('_dialog_just_opened', False):
        st.session_state['show_new_cat']    = False
        st.session_state['edit_cat_data']   = None
        st.session_state['delete_cat_data'] = None

    if menu != st.session_state.get('_last_menu', menu):
        st.session_state['edit_idx'] = None
        # Query-Param ändern → Browser scrollt automatisch nach oben (echter Navigation-Reset)
        st.query_params["page"] = menu.split(" ")[1] if " " in menu else menu
    st.session_state['_last_menu'] = menu

    # ── Page routing ──────────────────────────────────────────
    user_name = st.session_state['user_name']
    if menu == "📈 Dashboard":
        page_dashboard.render(user_name, _user_settings, _t, _currency_sym)
    elif menu == "💸 Transaktionen":
        page_transactions.render(user_name, _currency_sym)
    elif menu == "📂 Analysen":
        page_analytics.render(user_name, _currency_sym)
    elif menu == "🪣 Spartöpfe":
        page_savings_pots.render(user_name, _currency_sym)
    elif menu == "⚙️ Einstellungen":
        page_settings.render(user_name, _user_settings, _theme_name, _t, _currency_sym)

# ── Auth ──────────────────────────────────────────────────────
else:
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
                            st.rerun()
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
                        st.session_state['auth_mode'] = 'signup'
                        st.rerun()
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
                        st.session_state['auth_mode'] = 'forgot'
                        st.rerun()
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
