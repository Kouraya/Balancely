import datetime
import io
import pandas as pd
import streamlit as st

from constants import THEMES, CURRENCY_SYMBOLS
from database import (
    _gs_read, _gs_update, _gs_invalidate,
    load_user_settings, save_user_settings,
)
from styling import section_header, inject_theme
from utils import make_hashes, check_password_strength, is_valid_email, generate_code, send_email, email_html


def render(user_name, user_settings, theme_name, theme, currency_sym):
    st.markdown(
        "<div style='margin-bottom:28px;margin-top:16px;'>"
        "<h1 style='font-family:DM Sans,sans-serif;font-size:36px;font-weight:700;color:#e2e8f0;"
        "margin:0 0 4px 0;letter-spacing:-1px;'>Einstellungen ⚙️</h1>"
        "<p style='font-family:DM Sans,sans-serif;color:#475569;font-size:14px;margin:0;'>"
        "Profil, Finanzen, Design und Konto</p></div>",
        unsafe_allow_html=True,
    )

    SETTINGS_TABS = [("👤", "Profil"), ("💰", "Finanzen"), ("🎨", "Design"), ("🔐", "Sicherheit"), ("📦", "Daten")]
    active_tab = st.session_state.get('settings_tab', 'Profil')
    tab_cols = st.columns(len(SETTINGS_TABS))
    for i, (icon, label) in enumerate(SETTINGS_TABS):
        with tab_cols[i]:
            if st.button(f"{icon} {label}", key=f"stab_{label}", use_container_width=True,
                         type="primary" if active_tab == label else "secondary"):
                st.session_state['settings_tab'] = label
                st.rerun()
    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    if active_tab == "Profil":
        _render_profil(user_name, user_settings, theme)

    elif active_tab == "Finanzen":
        _render_finanzen(user_name, user_settings, currency_sym)

    elif active_tab == "Design":
        _render_design(user_name, theme_name)

    elif active_tab == "Sicherheit":
        _render_sicherheit(user_name, user_settings, theme)

    elif active_tab == "Daten":
        _render_daten(user_name, currency_sym)


# ── Sub-Tabs ──────────────────────────────────────────────────

def _render_profil(user_name, user_settings, theme):
    col_main, col_preview = st.columns([2, 1])
    with col_main:
        section_header("Profilbild", "URL zu einem öffentlich zugänglichen Bild")
        with st.form("avatar_form"):
            new_avatar = st.text_input("Bild-URL", value=user_settings.get('avatar_url', ''), placeholder="https://beispiel.de/foto.jpg")
            if st.form_submit_button("Profilbild speichern", use_container_width=True, type="primary"):
                save_user_settings(user_name, avatar_url=new_avatar.strip())
                st.success("✅ Profilbild gespeichert!")
                st.rerun()
    with col_preview:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        _av = user_settings.get('avatar_url', '')
        if _av and _av.startswith('http'):
            st.markdown(
                f"<div style='text-align:center;'><img src='{_av}' style='width:80px;height:80px;border-radius:50%;object-fit:cover;border:3px solid {theme['primary']}60;'>"
                f"<p style='font-family:DM Sans,sans-serif;color:#475569;font-size:12px;margin-top:8px;'>Aktuelles Profilbild</p></div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"<div style='text-align:center;'><div style='width:80px;height:80px;border-radius:50%;background:linear-gradient(135deg,{theme['accent']},{theme['accent2']});"
                f"display:flex;align-items:center;justify-content:center;font-size:28px;font-weight:600;color:#fff;margin:0 auto;'>{user_name[:2].upper()}</div>"
                f"<p style='font-family:DM Sans,sans-serif;color:#475569;font-size:12px;margin-top:8px;'>Initialen-Avatar</p></div>",
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    section_header("Benutzername ändern", "Kann nur alle 30 Tage geändert werden")
    try:
        df_u_name = _gs_read("users")
        idx_un    = df_u_name[df_u_name['username'] == user_name].index
        last_change_raw = str(df_u_name.loc[idx_un[0], 'username_changed_at']) if (not idx_un.empty and 'username_changed_at' in df_u_name.columns) else ''
        last_change = None
        try:
            last_change = datetime.date.fromisoformat(last_change_raw.strip()) if last_change_raw.strip() not in ('', 'nan', 'None') else None
        except:
            pass
        days_since = (datetime.date.today() - last_change).days if last_change else 999
        can_change = days_since >= 30
        days_left  = max(0, 30 - days_since)
        st.markdown(
            f"<div style='background:rgba(10,16,30,0.5);border:1px solid rgba(148,163,184,0.06);border-radius:10px;"
            f"padding:12px 16px;display:inline-block;margin-bottom:12px;'>"
            f"<span style='font-family:DM Mono,monospace;color:{theme['primary']};font-size:15px;font-weight:500;'>@{user_name}</span></div>",
            unsafe_allow_html=True,
        )
        if not can_change:
            st.markdown(
                f"<div style='background:rgba(250,204,21,0.06);border:1px solid rgba(250,204,21,0.15);border-radius:10px;padding:10px 14px;'>"
                f"<span style='font-family:DM Sans,sans-serif;color:#fbbf24;font-size:13px;'>⏳ Nächste Änderung möglich in <b>{days_left}</b> Tag{'en' if days_left != 1 else ''}.</span></div>",
                unsafe_allow_html=True,
            )
        else:
            with st.form("username_change_form"):
                new_uname = st.text_input("Neuer Benutzername", placeholder="Mindestens 3 Zeichen, keine Leerzeichen")
                if st.form_submit_button("Benutzername ändern", use_container_width=True, type="primary"):
                    new_uname = new_uname.strip()
                    if len(new_uname) < 3:          st.error("❌ Mindestens 3 Zeichen erforderlich.")
                    elif ' ' in new_uname:           st.error("❌ Keine Leerzeichen erlaubt.")
                    elif new_uname == user_name:     st.error("❌ Das ist bereits dein Benutzername.")
                    elif not df_u_name[df_u_name['username'] == new_uname].empty: st.error("❌ Benutzername bereits vergeben.")
                    else:
                        df_u_name.loc[idx_un[0], 'username'] = new_uname
                        if 'username_changed_at' not in df_u_name.columns:
                            df_u_name['username_changed_at'] = ''
                        df_u_name.loc[idx_un[0], 'username_changed_at'] = str(datetime.date.today())
                        _gs_update("users", df_u_name)
                        for ws, col in [("transactions", "user"), ("toepfe", "user"), ("goals", "user"), ("settings", "user"), ("dauerauftraege", "user")]:
                            try:
                                df_ws = _gs_read(ws)
                                if col in df_ws.columns:
                                    df_ws.loc[df_ws[col] == user_name, col] = new_uname
                                    _gs_update(ws, df_ws)
                            except:
                                pass
                        for k in [k for k in st.session_state if k.startswith("_gs_cache_")]:
                            del st.session_state[k]
                        st.session_state['user_name'] = new_uname
                        st.success(f"✅ Benutzername geändert zu @{new_uname}!")
                        st.rerun()
    except Exception as e:
        st.error(f"Fehler: {e}")


def _render_finanzen(user_name, user_settings, currency_sym):
    col_l, col_r = st.columns(2)
    with col_l:
        section_header("Monatliches Budget-Limit")
        with st.form("budget_form"):
            new_budget = st.number_input(f"Budget ({currency_sym})", min_value=0.0, value=float(user_settings.get('budget', 0.0)), step=50.0, format="%.2f")
            if st.form_submit_button("Budget speichern", use_container_width=True, type="primary"):
                save_user_settings(user_name, budget=new_budget)
                st.success("✅ Budget-Limit gespeichert!")
                st.rerun()
    with col_r:
        section_header("Währung")
        with st.form("currency_form"):
            curr_options = list(CURRENCY_SYMBOLS.keys())
            curr_current = user_settings.get('currency', 'EUR')
            curr_idx     = curr_options.index(curr_current) if curr_current in curr_options else 0
            curr_labels  = [f"{sym} ({CURRENCY_SYMBOLS[sym]})" for sym in curr_options]
            new_curr_lbl = st.selectbox("Währung wählen", curr_labels, index=curr_idx)
            new_currency = curr_options[curr_labels.index(new_curr_lbl)]
            if st.form_submit_button("Währung speichern", use_container_width=True, type="primary"):
                save_user_settings(user_name, currency=new_currency)
                _gs_invalidate("settings")
                st.success(f"✅ Währung auf {new_currency} gesetzt!")
                st.rerun()


def _render_design(user_name, theme_name):
    section_header("Farbschema")
    theme_icons = {"Ocean Blue": "🌊", "Emerald Green": "🌿", "Deep Purple": "🔮"}
    theme_descs = {
        "Ocean Blue":    "Dunkles Marineblau mit Sky-Akzenten",
        "Emerald Green": "Tiefes Waldgrün mit Smaragd-Akzenten",
        "Deep Purple":   "Samtiges Dunkelviolett mit Amethyst-Akzenten",
    }
    theme_cols = st.columns(3)
    for i, tname in enumerate(THEMES.keys()):
        t_data    = THEMES[tname]
        is_active = (theme_name == tname)
        with theme_cols[i]:
            _tc_bor = t_data['primary'] + 'ff' if is_active else t_data['primary'] + '30'
            # Kein box-shadow mehr – verhindert Überlappung zwischen den Cards
            _tc_badge = (
                f"<div style='margin-top:8px;font-family:DM Mono,monospace;color:{t_data['primary']};font-size:9px;letter-spacing:1.5px;'>✓ AKTIV</div>"
                if is_active else ""
            )
            st.markdown(
                f"<div style='background:linear-gradient(135deg,{t_data['bg1']},{t_data['bg2']});border:2px solid {_tc_bor};"
                f"border-radius:14px;padding:16px;margin-bottom:10px;text-align:center;'>"
                f"<div style='font-size:24px;margin-bottom:8px;'>{theme_icons[tname]}</div>"
                f"<div style='display:flex;justify-content:center;gap:6px;margin-bottom:10px;'>"
                f"<div style='width:16px;height:16px;border-radius:50%;background:{t_data['primary']};'></div>"
                f"<div style='width:16px;height:16px;border-radius:50%;background:{t_data['accent']};'></div>"
                f"<div style='width:16px;height:16px;border-radius:50%;background:{t_data['accent2']};'></div></div>"
                f"<div style='font-family:DM Sans,sans-serif;color:#e2e8f0;font-size:13px;font-weight:600;margin-bottom:4px;'>{tname}</div>"
                f"<div style='font-family:DM Sans,sans-serif;color:#475569;font-size:11px;'>{theme_descs[tname]}</div>"
                f"{_tc_badge}</div>",
                unsafe_allow_html=True,
            )
            if st.button(
                "Auswählen" if not is_active else "✓ Aktiv",
                key=f"theme_btn_{tname}", use_container_width=True,
                type="primary" if is_active else "secondary", disabled=is_active,
            ):
                st.session_state['theme'] = tname
                save_user_settings(user_name, theme=tname)
                st.rerun()


def _render_sicherheit(user_name, user_settings, theme):
    col_l, col_r = st.columns(2)
    with col_l:
        section_header("Passwort ändern")
        with st.form("pw_form"):
            pw_alt  = st.text_input("Aktuelles Passwort", type="password")
            pw_neu  = st.text_input("Neues Passwort", type="password")
            pw_neu2 = st.text_input("Neues Passwort wiederholen", type="password")
            if st.form_submit_button("Passwort ändern", use_container_width=True, type="primary"):
                df_u = _gs_read("users")
                idx  = df_u[df_u['username'] == user_name].index
                if idx.empty:                                         st.error("❌ Benutzer nicht gefunden.")
                elif make_hashes(pw_alt) != str(df_u.loc[idx[0], 'password']): st.error("❌ Aktuelles Passwort ist falsch.")
                elif pw_neu == pw_alt:                                st.error("❌ Das neue Passwort darf nicht dem alten entsprechen.")
                else:
                    ok, msg = check_password_strength(pw_neu)
                    if not ok:            st.error(f"❌ {msg}")
                    elif pw_neu != pw_neu2: st.error("❌ Die neuen Passwörter stimmen nicht überein.")
                    else:
                        df_u.loc[idx[0], 'password'] = make_hashes(pw_neu)
                        _gs_update("users", df_u)
                        st.success("✅ Passwort erfolgreich geändert!")

    with col_r:
        section_header("E-Mail-Adresse ändern")
        try:
            df_u_em = _gs_read("users")
            idx_em  = df_u_em[df_u_em['username'] == user_name].index
            curr_email = str(df_u_em.loc[idx_em[0], 'email']) if not idx_em.empty else "–"
        except:
            curr_email = "–"
        st.markdown(
            f"<div style='background:rgba(10,16,30,0.5);border:1px solid rgba(148,163,184,0.06);border-radius:10px;"
            f"padding:10px 14px;margin-bottom:14px;'>"
            f"<span style='font-family:DM Mono,monospace;color:#475569;font-size:11px;'>Aktuell: </span>"
            f"<span style='font-family:DM Mono,monospace;color:{theme['primary']};font-size:12px;'>{curr_email}</span></div>",
            unsafe_allow_html=True,
        )
        if not st.session_state.get('email_verify_code'):
            with st.form("email_change_form"):
                new_email_input = st.text_input("Neue E-Mail-Adresse", placeholder="neu@beispiel.de")
                if st.form_submit_button("Code senden", use_container_width=True, type="primary"):
                    if not is_valid_email(new_email_input.strip()):                       st.error("❌ Bitte gib eine gültige E-Mail ein.")
                    elif new_email_input.strip().lower() == curr_email.lower():           st.error("❌ Das ist bereits deine E-Mail-Adresse.")
                    else:
                        code   = generate_code()
                        expiry = datetime.datetime.now() + datetime.timedelta(minutes=10)
                        if send_email(new_email_input.strip().lower(), "Balancely – E-Mail-Adresse bestätigen", email_html("Dein Code zum Ändern der E-Mail-Adresse lautet:", code)):
                            st.session_state.update({'email_verify_code': code, 'email_verify_expiry': expiry, 'email_verify_new': new_email_input.strip().lower()})
                            st.rerun()
                        else:
                            st.error("❌ E-Mail konnte nicht gesendet werden.")
        else:
            st.markdown(f"<p style='font-family:DM Sans,sans-serif;color:#64748b;font-size:13px;margin-bottom:12px;'>Code gesendet an <span style='color:{theme['primary']};'>{st.session_state['email_verify_new']}</span></p>", unsafe_allow_html=True)
            with st.form("email_verify_form"):
                code_in = st.text_input("6-stelliger Code", placeholder="123456", max_chars=6)
                cv1, cv2 = st.columns(2)
                with cv1: confirm = st.form_submit_button("Bestätigen", use_container_width=True, type="primary")
                with cv2: cancel  = st.form_submit_button("Abbrechen",  use_container_width=True)
                if confirm:
                    if st.session_state['email_verify_expiry'] and datetime.datetime.now() > st.session_state['email_verify_expiry']:
                        st.error("⏰ Code abgelaufen.")
                        st.session_state['email_verify_code'] = ""
                        st.rerun()
                    elif code_in.strip() != st.session_state['email_verify_code']:
                        st.error("❌ Falscher Code.")
                    else:
                        df_u2 = _gs_read("users")
                        idx2  = df_u2[df_u2['username'] == user_name].index
                        if not idx2.empty:
                            df_u2.loc[idx2[0], 'email'] = st.session_state['email_verify_new']
                            _gs_update("users", df_u2)
                        st.session_state.update({'email_verify_code': "", 'email_verify_expiry': None, 'email_verify_new': ""})
                        st.success("✅ E-Mail-Adresse erfolgreich geändert!")
                        st.rerun()
                if cancel:
                    st.session_state.update({'email_verify_code': "", 'email_verify_new': ""})
                    st.rerun()


def _render_daten(user_name, currency_sym):
    # Export
    section_header("Excel-Export")
    try:
        df_export = _gs_read("transactions")
        if 'user' in df_export.columns:
            df_export = df_export[df_export['user'] == user_name]
            if 'deleted' in df_export.columns:
                df_export = df_export[~df_export['deleted'].astype(str).str.strip().str.lower().isin(['true', '1', '1.0'])]
            df_export = df_export.drop(columns=['deleted', 'user'], errors='ignore')
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_export.to_excel(writer, index=False, sheet_name='Transaktionen')
        excel_bytes = buffer.getvalue()
        st.markdown(f"<p style='font-family:DM Sans,sans-serif;color:#64748b;font-size:13px;margin-bottom:12px;'>{len(df_export)} Transaktionen bereit</p>", unsafe_allow_html=True)
        _, dl_col, _ = st.columns([1, 2, 1])
        with dl_col:
            st.download_button(
                label="⬇️ Transaktionen exportieren (Excel)",
                data=excel_bytes,
                file_name=f"balancely_{user_name}_{datetime.date.today()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True, type="primary",
            )
    except Exception as e:
        st.error(f"Export fehlgeschlagen: {e}")

    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)

    # Reset
    section_header("Daten zurücksetzen")
    if not st.session_state['confirm_reset']:
        _, rst_col, _ = st.columns([1, 2, 1])
        with rst_col:
            if st.button("🔄 Alle Transaktionen löschen", use_container_width=True, type="secondary"):
                st.session_state['confirm_reset'] = True
                st.rerun()
    else:
        st.markdown(
            "<div style='background:rgba(248,113,113,0.06);border:1px solid rgba(248,113,113,0.2);border-radius:10px;padding:14px;margin-bottom:10px;'>"
            "<p style='font-family:DM Sans,sans-serif;color:#fca5a5;font-size:14px;font-weight:500;margin:0 0 4px 0;'>⚠️ Wirklich alle Transaktionen löschen?</p>"
            "<p style='font-family:DM Sans,sans-serif;color:#64748b;font-size:13px;margin:0;'>Diese Aktion kann nicht rückgängig gemacht werden.</p></div>",
            unsafe_allow_html=True,
        )
        _, rc1, rc2, _ = st.columns([1, 1, 1, 1])
        with rc1:
            if st.button("Ja, löschen", use_container_width=True, type="primary"):
                try:
                    df_all_t = _gs_read("transactions")
                    if 'deleted' not in df_all_t.columns: df_all_t['deleted'] = ''
                    df_all_t.loc[df_all_t['user'] == user_name, 'deleted'] = 'True'
                    _gs_update("transactions", df_all_t)
                    st.session_state['confirm_reset'] = False
                    st.success("✅ Alle Transaktionen gelöscht.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Fehler: {e}")
        with rc2:
            if st.button("Abbrechen", use_container_width=True):
                st.session_state['confirm_reset'] = False
                st.rerun()

    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)

    # Delete account
    section_header("Account löschen")
    if not st.session_state['confirm_delete_account']:
        _, del_col, _ = st.columns([1, 2, 1])
        with del_col:
            if st.button("🗑️ Account und alle Daten löschen", use_container_width=True, type="secondary"):
                st.session_state['confirm_delete_account'] = True
                st.rerun()
    else:
        st.markdown(
            "<div style='background:rgba(248,113,113,0.08);border:1px solid rgba(248,113,113,0.25);border-left:3px solid #f87171;border-radius:10px;padding:14px;margin-bottom:10px;'>"
            "<p style='font-family:DM Sans,sans-serif;color:#fca5a5;font-size:14px;font-weight:600;margin:0 0 4px 0;'>🔴 Account unwiderruflich löschen?</p>"
            "<p style='font-family:DM Sans,sans-serif;color:#64748b;font-size:13px;margin:0;'>Alle Transaktionen, Spartöpfe, Sparziele und Einstellungen werden gelöscht.</p></div>",
            unsafe_allow_html=True,
        )
        _, da1, da2, _ = st.columns([1, 1, 1, 1])
        with da1:
            if st.button("Ja, Account löschen", use_container_width=True, type="primary"):
                try:
                    for ws, col_name in [("transactions", "user"), ("toepfe", "user")]:
                        df_ws = _gs_read(ws)
                        if 'deleted' not in df_ws.columns: df_ws['deleted'] = ''
                        df_ws.loc[df_ws[col_name] == user_name, 'deleted'] = 'True'
                        _gs_update(ws, df_ws)
                    for ws in ["goals", "settings"]:
                        df_ws = _gs_read(ws)
                        _gs_update(ws, df_ws[df_ws['user'] != user_name])
                    df_u3 = _gs_read("users")
                    if 'deleted' not in df_u3.columns: df_u3['deleted'] = ''
                    df_u3.loc[df_u3['username'] == user_name, 'deleted'] = 'True'
                    _gs_update("users", df_u3)
                    for k in [k for k in st.session_state if k.startswith("_gs_cache_")]:
                        del st.session_state[k]
                    st.session_state.update({'logged_in': False, 'user_name': '', 'confirm_delete_account': False})
                    st.rerun()
                except Exception as e:
                    st.error(f"Fehler beim Löschen: {e}")
        with da2:
            if st.button("Abbrechen", use_container_width=True, key="cancel_del_acc"):
                st.session_state['confirm_delete_account'] = False
                st.rerun()
