"""
Onboarding-Dialog für neue Nutzer nach der ersten Anmeldung.
Wird in Balancely.py aufgerufen, wenn 'show_onboarding' in session_state True ist.
Schritt 1: Theme wählen
Schritt 2: Währung wählen
Schritt 3-7: App-Walkthrough (Dashboard, Transaktionen, Analysen, Spartöpfe, Einstellungen)
Schritt 8: Abschluss
"""

import streamlit as st
from constants import THEMES, CURRENCY_SYMBOLS
from database import save_user_settings, _gs_read, _gs_update


WALKTHROUGH_STEPS = [
    {
        "icon": "📈",
        "title": "Dashboard",
        "subtitle": "Deine Finanzübersicht auf einen Blick",
        "color": "#38bdf8",
        "features": [
            ("💳", "Bankkontostand", "Sieh deinen monatlichen Kontostand — Einnahmen — Ausgaben — Depot."),
            ("📊", "Donut-Chart", "Kreisdiagramm nach Kategorie — klicke auf einen Sektor für Details."),
            ("🎯", "Sparziel-Alarm", "Automatische Warnung wenn du dein Monatssparziel unterschreitest."),
            ("📅", "Monatsnavigation", "Blätter durch vergangene Monate mit den Pfeiltasten links & rechts."),
        ],
    },
    {
        "icon": "💸",
        "title": "Transaktionen",
        "subtitle": "Buchungen erfassen & verwalten",
        "color": "#f87171",
        "features": [
            ("➕", "Neue Buchung", "Erfasse Ausgaben, Einnahmen oder Depot-Käufe mit Betrag, Datum & Kategorie."),
            ("🔍", "Suche & Filter", "Finde Buchungen schnell per Stichwort — Kategorie, Notiz oder Betrag."),
            ("⚙️", "Daueraufträge", "Wiederkehrende Buchungen (Miete, Netflix ...) werden automatisch am 1. gebucht."),
            ("🏷️", "Eigene Kategorien", "Erstelle deine eigenen Kategorien mit Emoji & Name für jeden Typ."),
        ],
    },
    {
        "icon": "📂",
        "title": "Analysen",
        "subtitle": "Trends, Muster & Prognosen",
        "color": "#a78bfa",
        "features": [
            ("🍩", "Donut-Charts", "Ausgaben, Einnahmen & Depot im Zeitraum-Vergleich: wöchentlich, monatlich, jährlich."),
            ("🔥", "Kalender-Heatmap", "Visualisierung: An welchen Tagen gibst du am meisten aus?"),
            ("🔮", "Monatsende-Prognose", "KI-Hochrechnung: Wie viel wirst du bis Monatsende ausgeben?"),
            ("💡", "Spar-Potenzial", "Automatische Erkennung von Kategorien mit überdurchschnittlichen Ausgaben."),
        ],
    },
    {
        "icon": "🪣",
        "title": "Spartöpfe",
        "subtitle": "Virtuelle Töpfe für deine Ziele",
        "color": "#4ade80",
        "features": [
            ("🎯", "Sparziele setzen", "Erstelle Töpfe mit Zielbetrag — z.B. Urlaub, Neuer Laptop, Notgroschen."),
            ("💰", "Ein- & Auszahlen", "Zahle jederzeit in Töpfe ein oder entnehme Geld — wird als Transaktion erfasst."),
            ("📊", "Fortschrittsanzeige", "Jeder Topf zeigt deinen Fortschritt mit einem farbigen Balken."),
            ("🎉", "Ziel erreicht!", "Wenn ein Topf sein Ziel erreicht, erhältst du eine Erfolgsmeldung."),
        ],
    },
    {
        "icon": "⚙️",
        "title": "Einstellungen",
        "subtitle": "Personalisierung & Konto",
        "color": "#fb923c",
        "features": [
            ("👤", "Profil", "Profilbild-URL hinterlegen & Benutzernamen ändern (alle 30 Tage)."),
            ("💰", "Budget-Limit", "Setze ein monatliches Ausgaben-Budget — das Dashboard zeigt den Verbrauch."),
            ("🎨", "Design", "Wechsle jederzeit zwischen Ocean Blue, Emerald Green & Deep Purple."),
            ("📦", "Daten-Export", "Exportiere alle Transaktionen als Excel-Datei (.xlsx)."),
        ],
    },
]


def _progress_bar(step, total=8):
    """Renders a slim animated progress bar."""
    pct = int((step / total) * 100)
    return f"""
    <div style='margin-bottom:28px;'>
        <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;'>
            <span style='font-family:DM Mono,monospace;font-size:9px;color:#334155;letter-spacing:1.5px;text-transform:uppercase;'>
                Schritt {step} von {total}
            </span>
            <span style='font-family:DM Mono,monospace;font-size:9px;color:#38bdf8;'>{pct}%</span>
        </div>
        <div style='background:rgba(30,41,59,0.8);border-radius:99px;height:3px;overflow:hidden;'>
            <div style='width:{pct}%;height:100%;background:linear-gradient(to right,#0ea5e9,#38bdf8);
                        border-radius:99px;transition:width 0.4s ease;'></div>
        </div>
    </div>
    """


def _step_dots(step, total=8):
    """Dot indicators for steps."""
    dots = ""
    for i in range(1, total + 1):
        if i == step:
            col = "#38bdf8"
            w = "20px"
        elif i < step:
            col = "#1e40af"
            w = "6px"
        else:
            col = "rgba(30,41,59,0.8)"
            w = "6px"
        dots += f"<div style='width:{w};height:6px;border-radius:99px;background:{col};transition:all 0.3s ease;'></div>"
    return f"<div style='display:flex;gap:4px;align-items:center;justify-content:center;margin-top:20px;'>{dots}</div>"


@st.dialog("👋 Willkommen bei Balancely!", width="large")
def onboarding_dialog(user_name: str):
    step = st.session_state.get("onboarding_step", 1)

    # ── SCHRITT 1: Theme ──────────────────────────────────────
    if step == 1:
        st.markdown(_progress_bar(1), unsafe_allow_html=True)
        st.markdown(
            "<h3 style='font-family:DM Sans,sans-serif;color:#e2e8f0;font-size:22px;"
            "font-weight:700;margin:0 0 6px 0;letter-spacing:-0.5px;'>Wähle dein Farbschema</h3>"
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

        st.markdown(_step_dots(1), unsafe_allow_html=True)
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        if st.button("Weiter →", use_container_width=True, type="primary"):
            st.session_state["onboarding_step"] = 2
            st.rerun()

    # ── SCHRITT 2: Währung ────────────────────────────────────
    elif step == 2:
        st.markdown(_progress_bar(2), unsafe_allow_html=True)
        st.markdown(
            "<h3 style='font-family:DM Sans,sans-serif;color:#e2e8f0;font-size:22px;"
            "font-weight:700;margin:0 0 6px 0;letter-spacing:-0.5px;'>Wähle deine Währung</h3>"
            "<p style='font-family:DM Sans,sans-serif;color:#475569;font-size:14px;margin:0 0 24px 0;'>"
            "Du kannst die Währung jederzeit unter <b style='color:#64748b;'>Einstellungen → Finanzen</b> ändern.</p>",
            unsafe_allow_html=True,
        )

        selected_currency = st.session_state.get("onboarding_currency", "EUR")
        currency_info = {
            "EUR": ("🇪🇺", "Euro",               "Eurozone"),
            "CHF": ("🇨🇭", "Franken",            "Schweiz"),
            "USD": ("🇺🇸", "US-Dollar",          "USA"),
            "GBP": ("🇬🇧", "Pfund Sterling",     "Großbritannien"),
            "JPY": ("🇯🇵", "Yen",                "Japan"),
            "SEK": ("🇸🇪", "Schwedische Krone",  "Schweden"),
            "NOK": ("🇳🇴", "Norwegische Krone",  "Norwegen"),
            "DKK": ("🇩🇰", "Dänische Krone",     "Dänemark"),
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

        st.markdown(_step_dots(2), unsafe_allow_html=True)
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        back_col, next_col = st.columns(2)
        with back_col:
            if st.button("← Zurück", use_container_width=True, type="secondary"):
                st.session_state["onboarding_step"] = 1
                st.rerun()
        with next_col:
            if st.button("Weiter zur App-Tour →", use_container_width=True, type="primary"):
                chosen_theme    = st.session_state.get("onboarding_theme", "Ocean Blue")
                chosen_currency = st.session_state.get("onboarding_currency", "EUR")
                save_user_settings(user_name, theme=chosen_theme, currency=chosen_currency)
                st.session_state["theme"] = chosen_theme
                st.session_state["onboarding_step"] = 3
                st.rerun()

    # ── SCHRITTE 3–7: App-Walkthrough ─────────────────────────
    elif 3 <= step <= 7:
        wt_idx = step - 3  # 0..4
        info   = WALKTHROUGH_STEPS[wt_idx]
        color  = info["color"]

        st.markdown(_progress_bar(step), unsafe_allow_html=True)

        # Header mit großem Icon
        st.markdown(
            f"<div style='display:flex;align-items:center;gap:16px;margin-bottom:8px;'>"
            f"<div style='width:56px;height:56px;border-radius:16px;"
            f"background:linear-gradient(135deg,{color}20,{color}10);"
            f"border:1.5px solid {color}40;"
            f"display:flex;align-items:center;justify-content:center;font-size:28px;flex-shrink:0;'>"
            f"{info['icon']}</div>"
            f"<div>"
            f"<div style='font-family:DM Mono,monospace;font-size:9px;color:{color};letter-spacing:2px;text-transform:uppercase;margin-bottom:4px;'>"
            f"Feature {wt_idx + 1} von 5</div>"
            f"<h3 style='font-family:DM Sans,sans-serif;color:#e2e8f0;font-size:22px;font-weight:700;"
            f"margin:0;letter-spacing:-0.5px;'>{info['title']}</h3>"
            f"</div></div>"
            f"<p style='font-family:DM Sans,sans-serif;color:#475569;font-size:14px;margin:0 0 24px 0;'>{info['subtitle']}</p>",
            unsafe_allow_html=True,
        )

        # Feature-Karten
        cols_left  = st.columns(2)
        cols_right = st.columns(2)
        feature_cols = list(cols_left) + list(cols_right)

        for idx, (emoji, feat_title, feat_desc) in enumerate(info["features"]):
            with feature_cols[idx]:
                st.markdown(
                    f"<div style='background:linear-gradient(145deg,rgba(14,22,38,0.9),rgba(10,16,30,0.95));"
                    f"border:1px solid {color}20;border-top:2px solid {color}60;"
                    f"border-radius:14px;padding:16px 18px;height:100%;min-height:110px;margin-bottom:12px;'>"
                    f"<div style='font-size:20px;margin-bottom:8px;'>{emoji}</div>"
                    f"<div style='font-family:DM Sans,sans-serif;color:#e2e8f0;font-size:13px;font-weight:600;margin-bottom:4px;'>{feat_title}</div>"
                    f"<div style='font-family:DM Sans,sans-serif;color:#475569;font-size:12px;line-height:1.5;'>{feat_desc}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

        st.markdown(_step_dots(step), unsafe_allow_html=True)
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

        nav_l, nav_r = st.columns(2)
        with nav_l:
            if st.button("← Zurück", use_container_width=True, type="secondary"):
                st.session_state["onboarding_step"] = step - 1
                st.rerun()
        with nav_r:
            next_label = "Weiter →" if step < 7 else "Abschluss →"
            if st.button(next_label, use_container_width=True, type="primary"):
                st.session_state["onboarding_step"] = step + 1
                st.rerun()

    # ── SCHRITT 8: Abschluss ──────────────────────────────────
    elif step == 8:
        st.markdown(_progress_bar(8), unsafe_allow_html=True)

        chosen_theme    = st.session_state.get("onboarding_theme", "Ocean Blue")
        chosen_currency = st.session_state.get("onboarding_currency", "EUR")
        theme_icons     = {"Ocean Blue": "🌊", "Emerald Green": "🌿", "Deep Purple": "🔮"}

        st.markdown(
            f"<div style='text-align:center;padding:20px 0 8px;'>"
            f"<div style='font-size:52px;margin-bottom:12px;'>🎉</div>"
            f"<h3 style='font-family:DM Sans,sans-serif;color:#e2e8f0;font-size:26px;font-weight:700;"
            f"margin:0 0 8px 0;letter-spacing:-0.5px;'>Du bist startklar!</h3>"
            f"<p style='font-family:DM Sans,sans-serif;color:#475569;font-size:14px;margin:0 0 28px 0;'>"
            f"Balancely ist eingerichtet und wartet auf deine ersten Buchungen.</p></div>",
            unsafe_allow_html=True,
        )

        # Zusammenfassung der Einstellungen
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.markdown(
                f"<div style='background:linear-gradient(145deg,rgba(14,22,38,0.9),rgba(10,16,30,0.95));"
                f"border:1px solid rgba(56,189,248,0.15);border-radius:14px;padding:16px 18px;text-align:center;'>"
                f"<div style='font-size:24px;margin-bottom:8px;'>{theme_icons.get(chosen_theme,'🌊')}</div>"
                f"<div style='font-family:DM Mono,monospace;font-size:9px;color:#334155;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:4px;'>Farbschema</div>"
                f"<div style='font-family:DM Sans,sans-serif;color:#38bdf8;font-size:15px;font-weight:600;'>{chosen_theme}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
        with col_s2:
            curr_sym = CURRENCY_SYMBOLS.get(chosen_currency, "€")
            st.markdown(
                f"<div style='background:linear-gradient(145deg,rgba(14,22,38,0.9),rgba(10,16,30,0.95));"
                f"border:1px solid rgba(56,189,248,0.15);border-radius:14px;padding:16px 18px;text-align:center;'>"
                f"<div style='font-size:24px;margin-bottom:8px;'>💱</div>"
                f"<div style='font-family:DM Mono,monospace;font-size:9px;color:#334155;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:4px;'>Währung</div>"
                f"<div style='font-family:DM Sans,sans-serif;color:#38bdf8;font-size:15px;font-weight:600;'>{chosen_currency} ({curr_sym})</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

        # Quick-Start-Tipps
        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
        st.markdown(
            "<div style='background:linear-gradient(145deg,rgba(56,189,248,0.05),rgba(14,165,233,0.03));"
            "border:1px solid rgba(56,189,248,0.12);border-radius:14px;padding:18px 20px;'>"
            "<div style='font-family:DM Mono,monospace;font-size:9px;color:#1e40af;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:14px;'>Quick-Start</div>"
            "<div style='display:flex;flex-direction:column;gap:10px;'>"
            "<div style='display:flex;align-items:flex-start;gap:12px;'>"
            "<span style='font-size:16px;flex-shrink:0;'>1️⃣</span>"
            "<span style='font-family:DM Sans,sans-serif;color:#94a3b8;font-size:13px;'>Gehe zu <b style='color:#e2e8f0;'>💸 Transaktionen</b> und erfasse deine erste Buchung.</span>"
            "</div>"
            "<div style='display:flex;align-items:flex-start;gap:12px;'>"
            "<span style='font-size:16px;flex-shrink:0;'>2️⃣</span>"
            "<span style='font-family:DM Sans,sans-serif;color:#94a3b8;font-size:13px;'>Setze unter <b style='color:#e2e8f0;'>⚙️ Einstellungen → Finanzen</b> ein monatliches Budget-Limit.</span>"
            "</div>"
            "<div style='display:flex;align-items:flex-start;gap:12px;'>"
            "<span style='font-size:16px;flex-shrink:0;'>3️⃣</span>"
            "<span style='font-family:DM Sans,sans-serif;color:#94a3b8;font-size:13px;'>Erstelle einen <b style='color:#e2e8f0;'>🪣 Spartopf</b> für dein nächstes Sparziel.</span>"
            "</div>"
            "</div></div>",
            unsafe_allow_html=True,
        )

        st.markdown(_step_dots(8), unsafe_allow_html=True)
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

        col_back, col_start = st.columns([1, 2])
        with col_back:
            if st.button("← Zurück", use_container_width=True, type="secondary"):
                st.session_state["onboarding_step"] = 7
                st.rerun()
        with col_start:
            if st.button("🚀 Balancely starten!", use_container_width=True, type="primary"):
                # Einstellungen final speichern & Onboarding abschließen
                save_user_settings(user_name, theme=chosen_theme, currency=chosen_currency)
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

                st.session_state["theme"]           = chosen_theme
                st.session_state["show_onboarding"] = False
                st.session_state["onboarding_step"] = 1
                st.rerun()
