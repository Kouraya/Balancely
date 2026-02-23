"""
Onboarding-Dialog für neue Nutzer nach der ersten Anmeldung.
Wird in Balancely.py aufgerufen, wenn 'show_onboarding' in session_state True ist.
"""

import streamlit as st
from constants import THEMES, CURRENCY_SYMBOLS
from database import save_user_settings, _gs_read, _gs_update


@st.dialog("👋 Willkommen bei Balancely!", width="large")
def onboarding_dialog(user_name: str):
    step = st.session_state.get("onboarding_step", 1)

    # ── Fortschrittsanzeige ───────────────────────────────────
    st.markdown(
        f"""
        <div style='display:flex;align-items:center;gap:0;margin-bottom:28px;'>
            <div style='display:flex;align-items:center;gap:8px;flex:1;'>
                <div style='width:28px;height:28px;border-radius:50%;
                    background:{"#38bdf8" if step >= 1 else "rgba(30,41,59,0.8)"};
                    display:flex;align-items:center;justify-content:center;
                    font-family:DM Mono,monospace;font-size:12px;font-weight:600;
                    color:{"#020617" if step >= 1 else "#334155"};flex-shrink:0;'>1</div>
                <span style='font-family:DM Sans,sans-serif;font-size:13px;
                    color:{"#e2e8f0" if step == 1 else "#475569"};'>Farbschema</span>
            </div>
            <div style='flex:1;height:1px;background:{"#38bdf8" if step >= 2 else "rgba(51,65,85,0.5)"};margin:0 8px;'></div>
            <div style='display:flex;align-items:center;gap:8px;flex:1;'>
                <div style='width:28px;height:28px;border-radius:50%;
                    background:{"#38bdf8" if step >= 2 else "rgba(30,41,59,0.8)"};
                    display:flex;align-items:center;justify-content:center;
                    font-family:DM Mono,monospace;font-size:12px;font-weight:600;
                    color:{"#020617" if step >= 2 else "#334155"};flex-shrink:0;'>2</div>
                <span style='font-family:DM Sans,sans-serif;font-size:13px;
                    color:{"#e2e8f0" if step == 2 else "#475569"};'>Währung</span>
            </div>
            <div style='flex:1;height:1px;background:{"#38bdf8" if step >= 3 else "rgba(51,65,85,0.5)"};margin:0 8px;'></div>
            <div style='display:flex;align-items:center;gap:8px;flex:1;'>
                <div style='width:28px;height:28px;border-radius:50%;
                    background:{"#38bdf8" if step >= 3 else "rgba(30,41,59,0.8)"};
                    display:flex;align-items:center;justify-content:center;
                    font-family:DM Mono,monospace;font-size:12px;font-weight:600;
                    color:{"#020617" if step >= 3 else "#334155"};flex-shrink:0;'>✓</div>
                <span style='font-family:DM Sans,sans-serif;font-size:13px;
                    color:{"#e2e8f0" if step == 3 else "#475569"};'>Fertig</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Schritt 1: Theme ──────────────────────────────────────
    if step == 1:
        st.markdown(
            "<h3 style='font-family:DM Sans,sans-serif;color:#e2e8f0;font-size:20px;"
            "font-weight:600;margin:0 0 6px 0;'>Wähle dein Farbschema</h3>"
            "<p style='font-family:DM Sans,sans-serif;color:#475569;font-size:14px;margin:0 0 24px 0;'>"
            "Du kannst das Farbschema jederzeit unter <b style='color:#64748b;'>Einstellungen → Design</b> ändern.</p>",
            unsafe_allow_html=True,
        )

        selected_theme = st.session_state.get("onboarding_theme", "Ocean Blue")
        theme_icons = {"Ocean Blue": "🌊", "Emerald Green": "🌿", "Deep Purple": "🔮"}
        theme_descs = {
            "Ocean Blue":    "Dunkles Marineblau mit Sky-Akzenten",
            "Emerald Green": "Tiefes Waldgrün mit Smaragd-Akzenten",
            "Deep Purple":   "Samtiges Dunkelviolett mit Amethyst-Akzenten",
        }

        cols = st.columns(3)
        for i, (tname, tdata) in enumerate(THEMES.items()):
            is_active = selected_theme == tname
            with cols[i]:
                border_col = tdata['primary'] if is_active else tdata['primary'] + "30"
                badge = f"<div style='margin-top:6px;font-family:DM Mono,monospace;color:{tdata['primary']};font-size:9px;letter-spacing:1.5px;'>✓ GEWÄHLT</div>" if is_active else ""
                st.markdown(
                    f"<div style='background:linear-gradient(135deg,{tdata['bg1']},{tdata['bg2']});"
                    f"border:2px solid {border_col};border-radius:14px;padding:16px;text-align:center;margin-bottom:8px;'>"
                    f"<div style='font-size:26px;margin-bottom:8px;'>{theme_icons[tname]}</div>"
                    f"<div style='display:flex;justify-content:center;gap:5px;margin-bottom:10px;'>"
                    f"<div style='width:14px;height:14px;border-radius:50%;background:{tdata['primary']};'></div>"
                    f"<div style='width:14px;height:14px;border-radius:50%;background:{tdata['accent']};'></div>"
                    f"<div style='width:14px;height:14px;border-radius:50%;background:{tdata['accent2']};'></div></div>"
                    f"<div style='font-family:DM Sans,sans-serif;color:#e2e8f0;font-size:13px;font-weight:600;margin-bottom:3px;'>{tname}</div>"
                    f"<div style='font-family:DM Sans,sans-serif;color:#475569;font-size:11px;'>{theme_descs[tname]}</div>"
                    f"{badge}</div>",
                    unsafe_allow_html=True,
                )
                btn_label = "✓ Gewählt" if is_active else "Auswählen"
                if st.button(btn_label, key=f"ob_theme_{tname}", use_container_width=True,
                             type="primary" if is_active else "secondary"):
                    st.session_state["onboarding_theme"] = tname
                    st.rerun()

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        if st.button("Weiter →", use_container_width=True, type="primary"):
            st.session_state["onboarding_step"] = 2
            st.rerun()

    # ── Schritt 2: Währung ────────────────────────────────────
    elif step == 2:
        st.markdown(
            "<h3 style='font-family:DM Sans,sans-serif;color:#e2e8f0;font-size:20px;"
            "font-weight:600;margin:0 0 6px 0;'>Wähle deine Währung</h3>"
            "<p style='font-family:DM Sans,sans-serif;color:#475569;font-size:14px;margin:0 0 24px 0;'>"
            "Du kannst die Währung jederzeit unter <b style='color:#64748b;'>Einstellungen → Finanzen</b> ändern.</p>",
            unsafe_allow_html=True,
        )

        selected_currency = st.session_state.get("onboarding_currency", "EUR")

        currency_info = {
            "EUR": ("🇪🇺", "Euro",           "Eurozone"),
            "CHF": ("🇨🇭", "Franken",        "Schweiz"),
            "USD": ("🇺🇸", "US-Dollar",      "USA"),
            "GBP": ("🇬🇧", "Pfund Sterling", "Großbritannien"),
            "JPY": ("🇯🇵", "Yen",            "Japan"),
            "SEK": ("🇸🇪", "Schwedische Krone", "Schweden"),
            "NOK": ("🇳🇴", "Norwegische Krone", "Norwegen"),
            "DKK": ("🇩🇰", "Dänische Krone", "Dänemark"),
        }

        cols_a = st.columns(4)
        cols_b = st.columns(4)
        all_cols = cols_a + cols_b

        for i, (code, sym) in enumerate(CURRENCY_SYMBOLS.items()):
            flag, name, region = currency_info.get(code, ("💱", code, ""))
            is_active = selected_currency == code
            with all_cols[i]:
                border_col = "#38bdf8" if is_active else "rgba(148,163,184,0.1)"
                bg_col     = "rgba(56,189,248,0.07)" if is_active else "rgba(15,23,42,0.5)"
                badge      = f"<div style='font-family:DM Mono,monospace;color:#38bdf8;font-size:9px;margin-top:4px;'>✓</div>" if is_active else ""
                st.markdown(
                    f"<div style='background:{bg_col};border:1.5px solid {border_col};"
                    f"border-radius:12px;padding:12px 8px;text-align:center;margin-bottom:8px;'>"
                    f"<div style='font-size:22px;'>{flag}</div>"
                    f"<div style='font-family:DM Mono,monospace;color:#38bdf8;font-size:14px;font-weight:600;margin:4px 0 2px;'>{sym}</div>"
                    f"<div style='font-family:DM Sans,sans-serif;color:#e2e8f0;font-size:11px;font-weight:500;'>{code}</div>"
                    f"<div style='font-family:DM Sans,sans-serif;color:#475569;font-size:10px;'>{region}</div>"
                    f"{badge}</div>",
                    unsafe_allow_html=True,
                )
                if st.button(code, key=f"ob_curr_{code}", use_container_width=True,
                             type="primary" if is_active else "secondary"):
                    st.session_state["onboarding_currency"] = code
                    st.rerun()

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        back_col, next_col = st.columns(2)
        with back_col:
            if st.button("← Zurück", use_container_width=True, type="secondary"):
                st.session_state["onboarding_step"] = 1
                st.rerun()
        with next_col:
            if st.button("Fertigstellen ✓", use_container_width=True, type="primary"):
                # Einstellungen speichern
                chosen_theme    = st.session_state.get("onboarding_theme", "Ocean Blue")
                chosen_currency = st.session_state.get("onboarding_currency", "EUR")
                save_user_settings(user_name, theme=chosen_theme, currency=chosen_currency)

                # Onboarding als abgeschlossen markieren
                try:
                    df_u = _gs_read("users")
                    if "onboarding_done" not in df_u.columns:
                        df_u["onboarding_done"] = ""
                    idx = df_u[df_u["username"] == user_name].index
                    if not idx.empty:
                        df_u.loc[idx[0], "onboarding_done"] = "True"
                        _gs_update("users", df_u)
                except Exception:
                    pass

                st.session_state["theme"]            = chosen_theme
                st.session_state["show_onboarding"]  = False
                st.session_state["onboarding_step"]  = 1
                st.rerun()

    # ── Schritt 3 wird nicht mehr angezeigt (direkt rerun nach Fertigstellen)
