import streamlit as st

from database import load_toepfe, save_topf, update_topf_gespart, delete_topf, update_topf_meta


def render(user_name, currency_sym):
    st.markdown(
        "<div style='margin-bottom:36px;margin-top:16px;'>"
        "<h1 style='font-family:DM Sans,sans-serif;font-size:40px;font-weight:700;color:#e2e8f0;"
        "margin:0 0 6px 0;letter-spacing:-1px;'>Spartöpfe 🪣</h1>"
        "<p style='font-family:DM Sans,sans-serif;color:#475569;font-size:15px;margin:0;'>"
        "Virtuelle Töpfe für deine Sparziele</p></div>",
        unsafe_allow_html=True,
    )

    toepfe = load_toepfe(user_name)
    if toepfe:
        total_gespart = sum(t['gespart'] for t in toepfe)
        total_ziel    = sum(t['ziel'] for t in toepfe if t['ziel'] > 0)
        st.markdown(
            f"<div style='display:flex;gap:12px;margin-bottom:24px;flex-wrap:wrap;'>"
            f"<div style='flex:1;min-width:140px;background:linear-gradient(145deg,rgba(14,22,38,0.9),rgba(10,16,30,0.95));"
            f"border:1px solid rgba(56,189,248,0.12);border-radius:14px;padding:16px 18px;'>"
            f"<div style='font-family:DM Mono,monospace;font-size:9px;color:#1e40af;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:6px;'>Gesamt gespart</div>"
            f"<div style='font-family:DM Sans,sans-serif;color:#38bdf8;font-size:22px;font-weight:600;'>{total_gespart:,.2f} {currency_sym}</div></div>"
            f"<div style='flex:1;min-width:140px;background:linear-gradient(145deg,rgba(14,22,38,0.9),rgba(10,16,30,0.95));"
            f"border:1px solid rgba(148,163,184,0.08);border-radius:14px;padding:16px 18px;'>"
            f"<div style='font-family:DM Mono,monospace;font-size:9px;color:#334155;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:6px;'>Anzahl Töpfe</div>"
            f"<div style='font-family:DM Sans,sans-serif;color:#e2e8f0;font-size:22px;font-weight:600;'>{len(toepfe)}</div></div>"
            + (f"<div style='flex:1;min-width:140px;background:linear-gradient(145deg,rgba(14,22,38,0.9),rgba(10,16,30,0.95));"
               f"border:1px solid rgba(148,163,184,0.08);border-radius:14px;padding:16px 18px;'>"
               f"<div style='font-family:DM Mono,monospace;font-size:9px;color:#334155;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:6px;'>Gesamt-Ziel</div>"
               f"<div style='font-family:DM Sans,sans-serif;color:#64748b;font-size:22px;font-weight:600;'>{total_ziel:,.2f} {currency_sym}</div></div>" if total_ziel > 0 else "")
            + "</div>",
            unsafe_allow_html=True,
        )

        col_a, col_b = st.columns(2)
        for i, topf in enumerate(toepfe):
            col     = col_a if i % 2 == 0 else col_b
            farbe   = topf.get('farbe', '#38bdf8')
            gespart = topf['gespart']
            ziel    = topf['ziel']
            emoji   = topf.get('emoji', '🪣')
            topf_id = topf['id']

            with col:
                if ziel > 0:
                    pct = min(gespart / ziel * 100, 100)
                    ziel_html = (
                        f"<div style='display:flex;justify-content:space-between;margin-bottom:6px;margin-top:10px;'>"
                        f"<span style='font-family:DM Mono,monospace;color:#334155;font-size:10px;'>{gespart:,.2f} / {ziel:,.2f} {currency_sym}</span>"
                        f"<span style='font-family:DM Mono,monospace;color:{farbe};font-size:10px;font-weight:600;'>{pct:.0f}%</span></div>"
                        f"<div style='background:rgba(30,41,59,0.8);border-radius:99px;height:5px;overflow:hidden;'>"
                        f"<div style='width:{pct:.0f}%;height:100%;background:{farbe};border-radius:99px;'></div></div>"
                    )
                    badge_html = (
                        f"<span style='background:rgba(74,222,128,0.1);color:#4ade80;font-family:DM Mono,monospace;font-size:9px;padding:2px 8px;border-radius:99px;border:1px solid rgba(74,222,128,0.2);'>✓ ERREICHT</span>"
                        if pct >= 100 else
                        f"<span style='font-family:DM Mono,monospace;color:#334155;font-size:10px;'>noch {ziel - gespart:,.2f} {currency_sym} fehlen</span>"
                    )
                else:
                    ziel_html  = ""
                    badge_html = f"<span style='font-family:DM Mono,monospace;color:#334155;font-size:10px;'>kein Ziel gesetzt</span>"

                st.markdown(
                    f"<div style='background:linear-gradient(145deg,rgba(14,22,38,0.9),rgba(10,16,30,0.95));"
                    f"border:1px solid {farbe}20;border-top:2px solid {farbe};border-radius:16px;padding:18px 20px;margin-bottom:14px;'>"
                    f"<div style='display:flex;justify-content:space-between;align-items:flex-start;'>"
                    f"<div><div style='font-size:22px;margin-bottom:4px;'>{emoji}</div>"
                    f"<div style='font-family:DM Sans,sans-serif;color:#e2e8f0;font-weight:600;font-size:16px;'>{topf['name']}</div></div>"
                    f"<div style='font-family:DM Sans,sans-serif;color:{farbe};font-size:22px;font-weight:600;'>{gespart:,.2f} {currency_sym}</div></div>"
                    f"{ziel_html}<div style='margin-top:10px;'>{badge_html}</div></div>",
                    unsafe_allow_html=True,
                )

                with st.expander(f"💰 Ein/Auszahlen — {topf['name']}"):
                    tz1, tz2 = st.columns(2)
                    with tz1:
                        einzahl_val = st.number_input(f"Einzahlen ({currency_sym})", min_value=0.01, step=1.0, format="%.2f", key=f"einzahl_{topf_id}")
                        if st.button("+ Einzahlen", key=f"do_einzahl_{topf_id}", use_container_width=True, type="primary"):
                            update_topf_gespart(user_name, topf_id, topf['name'], einzahl_val)
                            st.rerun()
                    with tz2:
                        auszahl_val = st.number_input(f"Auszahlen ({currency_sym})", min_value=0.01, step=1.0, format="%.2f", key=f"auszahl_{topf_id}")
                        if st.button("− Auszahlen", key=f"do_auszahl_{topf_id}", use_container_width=True, type="secondary"):
                            update_topf_gespart(user_name, topf_id, topf['name'], -auszahl_val)
                            st.rerun()

                te1, te2 = st.columns(2)
                with te1:
                    if st.button("✏️", key=f"edit_topf_{topf_id}", use_container_width=True, type="secondary"):
                        st.session_state['topf_edit_data'] = topf
                        st.session_state['_dialog_just_opened'] = True
                        st.rerun()
                with te2:
                    if st.button("🗑️", key=f"del_topf_{topf_id}", use_container_width=True, type="secondary"):
                        st.session_state['topf_delete_id']   = topf_id
                        st.session_state['topf_delete_name'] = topf['name']
                        st.session_state['_dialog_just_opened'] = True
                        st.rerun()
    else:
        st.markdown(
            "<div style='text-align:center;padding:60px 20px;'>"
            "<div style='font-size:48px;margin-bottom:16px;'>🪣</div>"
            "<p style='font-family:DM Sans,sans-serif;color:#334155;font-size:15px;'>Noch keine Spartöpfe. Erstelle deinen ersten Topf!</p></div>",
            unsafe_allow_html=True,
        )

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(
        "<p style='font-family:DM Mono,monospace;color:#334155;font-size:10px;font-weight:500;"
        "letter-spacing:1.5px;text-transform:uppercase;margin-bottom:16px;'>Neuen Topf erstellen</p>",
        unsafe_allow_html=True,
    )
    with st.form("neuer_topf_form", clear_on_submit=True):
        nt1, nt2, nt3 = st.columns([1, 3, 2])
        with nt1: nt_emoji = st.text_input("Emoji", placeholder="✈️", max_chars=4)
        with nt2: nt_name  = st.text_input("Name", placeholder="z.B. Urlaub, Neues Auto, Laptop...")
        with nt3: nt_ziel  = st.number_input(f"Sparziel ({currency_sym}, optional)", min_value=0.0, step=50.0, format="%.2f", value=0.0)
        if st.form_submit_button("Topf erstellen", use_container_width=True, type="primary"):
            if not nt_name.strip():
                st.error("Bitte einen Namen eingeben.")
            else:
                save_topf(user=user_name, name=nt_name.strip(), ziel=nt_ziel, emoji=nt_emoji.strip() if nt_emoji.strip() else "🪣")
                st.success(f"✅ Topf '{nt_name.strip()}' erstellt!")
                st.rerun()

    # ── Edit-Dialog ───────────────────────────────────────────
    if st.session_state.get('topf_edit_data'):
        @st.dialog("✏️ Topf bearbeiten")
        def topf_edit_dialog():
            t = st.session_state['topf_edit_data']
            e1, e2 = st.columns([1, 3])
            with e1: new_emoji = st.text_input("Emoji", value=t['emoji'], max_chars=4)
            with e2: new_name  = st.text_input("Name", value=t['name'])
            new_ziel = st.number_input(f"Sparziel ({currency_sym})", min_value=0.0, value=float(t['ziel']), step=50.0, format="%.2f")
            cs, cc = st.columns(2)
            with cs:
                if st.button("Speichern", use_container_width=True, type="primary"):
                    update_topf_meta(user_name, t['id'], new_name.strip() or t['name'], new_ziel, new_emoji.strip() or t['emoji'])
                    st.session_state['topf_edit_data'] = None
                    st.rerun()
            with cc:
                if st.button("Abbrechen", use_container_width=True):
                    st.session_state['topf_edit_data'] = None
                    st.rerun()
        topf_edit_dialog()

    # ── Delete-Dialog ─────────────────────────────────────────
    if st.session_state.get('topf_delete_id'):
        @st.dialog("Topf löschen")
        def topf_delete_dialog():
            name = st.session_state.get('topf_delete_name', '')
            st.markdown(f"<p style='color:#e2e8f0;font-size:15px;'>Topf <b>'{name}'</b> wirklich löschen?</p>", unsafe_allow_html=True)
            d1, d2 = st.columns(2)
            with d1:
                if st.button("Löschen", use_container_width=True, type="primary"):
                    delete_topf(user_name, st.session_state['topf_delete_id'])
                    st.session_state['topf_delete_id']   = None
                    st.session_state['topf_delete_name'] = None
                    st.rerun()
            with d2:
                if st.button("Abbrechen", use_container_width=True):
                    st.session_state['topf_delete_id']   = None
                    st.session_state['topf_delete_name'] = None
                    st.rerun()
        topf_delete_dialog()
