import datetime
import re as _re
import pandas as pd
import streamlit as st

from constants import DEFAULT_CATS, TYPE_COLORS
from database import (
    _gs_read, _gs_update,
    load_custom_cats, save_custom_cat,
    load_dauerauftraege, save_dauerauftrag, delete_dauerauftrag,
)
from dialogs import new_category_dialog, edit_category_dialog, confirm_delete_cat, confirm_delete
from utils import format_timestamp, find_row_mask


def render(user_name, currency_sym):
    st.markdown(
        "<div style='margin-bottom:36px;margin-top:16px;'>"
        "<h1 style='font-family:DM Sans,sans-serif;font-size:40px;font-weight:700;color:#e2e8f0;"
        "margin:0 0 6px 0;letter-spacing:-1px;'>Buchungen &amp; Verlauf 🧾</h1>"
        "<p style='font-family:DM Sans,sans-serif;color:#475569;font-size:15px;margin:0;'>"
        "Buchungen erfassen &amp; verwalten</p></div>",
        unsafe_allow_html=True,
    )

    if st.session_state.get('show_new_cat'):    new_category_dialog()
    if st.session_state.get('edit_cat_data'):   edit_category_dialog()
    if st.session_state.get('delete_cat_data'): confirm_delete_cat()

    tabs = st.tabs(["💸 Neue Buchung", "⚙️ Daueraufträge"])

    # ── Tab 1: Neue Buchung ───────────────────────────────────
    with tabs[0]:
        t_type   = st.session_state['t_type']
        all_cats = DEFAULT_CATS[t_type] + load_custom_cats(user_name, t_type)

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        st.markdown(
            "<p style='font-family:DM Mono,monospace;color:#334155;font-size:10px;font-weight:500;"
            "letter-spacing:1.5px;text-transform:uppercase;margin-bottom:10px;'>Typ</p>",
            unsafe_allow_html=True,
        )
        ta, te, td, _ = st.columns([1, 1, 1, 2])
        for label, val, col in [("↗ Ausgabe", "Ausgabe", ta), ("↙ Einnahme", "Einnahme", te), ("📦 Depot", "Depot", td)]:
            with col:
                if st.button(
                    label + (" ✓" if t_type == val else ""),
                    key=f"btn_{val.lower()}",
                    use_container_width=True,
                    type="primary" if t_type == val else "secondary",
                ):
                    st.session_state['t_type'] = val
                    st.session_state['tx_page'] = 0
                    st.rerun()

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        with st.form("t_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                t_amount = st.number_input(f"Betrag in {currency_sym}", min_value=0.01, step=0.01, format="%.2f")
                t_date   = st.date_input("Datum", datetime.date.today())
            with col2:
                st.markdown(
                    "<div style='font-family:DM Sans,sans-serif;font-size:14px;color:#e2e8f0;margin-bottom:4px;'>Kategorie</div>",
                    unsafe_allow_html=True,
                )
                t_cat  = st.selectbox("Kategorie", all_cats, label_visibility="collapsed")
                t_note = st.text_input("Notiz (optional)", placeholder="z.B. Supermarkt, Tankstelle...")
            if st.form_submit_button("Speichern", use_container_width=True):
                betrag_save = t_amount if t_type in ("Depot", "Einnahme") else -t_amount
                new_row = pd.DataFrame([{
                    "user": user_name, "datum": str(t_date),
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "typ": t_type, "kategorie": t_cat, "betrag": betrag_save,
                    "notiz": t_note, "deleted": "",
                }])
                _gs_update("transactions", pd.concat([_gs_read("transactions"), new_row], ignore_index=True))
                st.session_state['tx_page'] = 0
                st.success(f"✅ {t_type} über {t_amount:.2f} {currency_sym} gespeichert!")
                st.balloons()

        cat_btn_col, manage_col = st.columns([1, 1])
        with cat_btn_col:
            if st.button("+ Neue Kategorie", use_container_width=True, type="secondary"):
                st.session_state.update({'show_new_cat': True, 'new_cat_typ': t_type, '_dialog_just_opened': True})
                st.rerun()
        custom_cats = load_custom_cats(user_name, t_type)
        if custom_cats:
            with manage_col:
                with st.expander(f"Eigene {t_type}-Kategorien"):
                    for cat in custom_cats:
                        cc1, cc2 = st.columns([5, 1])
                        cc1.markdown(
                            f"<span style='font-family:DM Sans,sans-serif;color:#94a3b8;font-size:14px;'>{cat}</span>",
                            unsafe_allow_html=True,
                        )
                        with cc2:
                            with st.popover("⋯", use_container_width=True):
                                if st.button("✏️ Bearbeiten", key=f"editcat_{cat}", use_container_width=True):
                                    st.session_state.update({'edit_cat_data': {'user': user_name, 'typ': t_type, 'old_label': cat}, '_dialog_just_opened': True})
                                    st.rerun()
                                if st.button("🗑️ Löschen", key=f"delcat_{cat}", use_container_width=True):
                                    st.session_state.update({'delete_cat_data': {'user': user_name, 'typ': t_type, 'label': cat}, '_dialog_just_opened': True})
                                    st.rerun()

        st.markdown(
            "<div style='height:8px'></div>"
            "<div style='font-family:DM Mono,monospace;color:#334155;font-size:10px;font-weight:500;"
            "letter-spacing:1.5px;text-transform:uppercase;margin:20px 0 10px 0;'>Meine Buchungen</div>",
            unsafe_allow_html=True,
        )

        search_col, _ = st.columns([2, 3])
        with search_col:
            search_val = st.text_input(
                "🔍 Suchen...", value=st.session_state.get('tx_search', ''),
                placeholder="Kategorie, Notiz, Betrag...", label_visibility="collapsed", key="tx_search_input",
            )
            if search_val != st.session_state.get('tx_search', ''):
                st.session_state['tx_search'] = search_val
                st.session_state['tx_page'] = 0
                st.rerun()

        try:
            df_t = _gs_read("transactions")
            if 'user' not in df_t.columns:
                st.info("Noch keine Buchungen vorhanden.")
            else:
                del_mask = (~df_t['deleted'].astype(str).str.strip().str.lower().isin(['true', '1', '1.0'])
                            if 'deleted' in df_t.columns
                            else pd.Series([True] * len(df_t), index=df_t.index))
                user_df = df_t[(df_t['user'] == user_name) & del_mask].copy()
                if user_df.empty:
                    st.info("Noch keine Buchungen vorhanden.")
                else:
                    def betrag_anzeige(row, sym=currency_sym):
                        x = pd.to_numeric(row['betrag'], errors='coerce')
                        if row.get('typ') == 'Depot':    return f"📦 {abs(x):.2f} {sym}"
                        if row.get('typ') == 'Spartopf': return f"🪣 {abs(x):.2f} {sym}" if x < 0 else f"🪣 +{abs(x):.2f} {sym}"
                        return f"+{x:.2f} {sym}" if x > 0 else f"{x:.2f} {sym}"

                    user_df['betrag_anzeige'] = user_df.apply(betrag_anzeige, axis=1)
                    sort_col = 'timestamp' if 'timestamp' in user_df.columns else 'datum'
                    user_df  = user_df.sort_values(sort_col, ascending=False)

                    search_q = st.session_state.get('tx_search', '').strip().lower()
                    if search_q:
                        _pat = _re.escape(search_q)
                        betrag_match = user_df['betrag_anzeige'].str.lower().str.contains(
                            r'(?<!\d)' + _pat + r'(?!\d)', na=False, regex=True)
                        mask_s = (
                            user_df['kategorie'].str.lower().str.contains(search_q, na=False) |
                            user_df['notiz'].astype(str).str.lower().str.contains(search_q, na=False) |
                            betrag_match |
                            user_df['typ'].str.lower().str.contains(search_q, na=False)
                        )
                        user_df = user_df[mask_s]

                    PAGE_SIZE = 10
                    total    = len(user_df)
                    page     = st.session_state.get('tx_page', 0)
                    max_page = max(0, (total - 1) // PAGE_SIZE)
                    page     = min(page, max_page)
                    st.session_state['tx_page'] = page
                    start    = page * PAGE_SIZE
                    page_df  = user_df.iloc[start:start + PAGE_SIZE]

                    if page_df.empty:
                        st.info("Keine Buchungen gefunden.")
                    else:
                        for orig_idx, row in page_df.iterrows():
                            notiz      = str(row.get('notiz', ''))
                            notiz      = '' if notiz.lower() == 'nan' else notiz
                            betrag_num = pd.to_numeric(row['betrag'], errors='coerce')
                            farbe      = TYPE_COLORS.get(row['typ'], '#f87171')
                            zeit_label = format_timestamp(row.get('timestamp', ''), row.get('datum', ''))

                            c1, c2, c3, c4, c5 = st.columns([2.5, 2, 2.5, 3, 1])
                            c1.markdown(f"<span style='font-family:DM Mono,monospace;color:#334155;font-size:12px;line-height:2.4;display:block;'>{zeit_label}</span>", unsafe_allow_html=True)
                            c2.markdown(f"<span style='font-family:DM Mono,monospace;color:{farbe};font-weight:500;font-size:13px;line-height:2.4;display:block;'>{row['betrag_anzeige']}</span>", unsafe_allow_html=True)
                            c3.markdown(f"<span style='font-family:DM Sans,sans-serif;color:#64748b;font-size:13px;line-height:2.4;display:block;'>{row['kategorie']}</span>", unsafe_allow_html=True)
                            c4.markdown(f"<span style='font-family:DM Sans,sans-serif;color:#334155;font-size:13px;line-height:2.4;display:block;'>{notiz}</span>", unsafe_allow_html=True)
                            with c5:
                                with st.popover("⋯", use_container_width=True):
                                    if st.button("✏️ Bearbeiten", key=f"edit_btn_{orig_idx}", use_container_width=True):
                                        st.session_state['edit_idx'] = None if st.session_state['edit_idx'] == orig_idx else orig_idx
                                        st.session_state['show_new_cat'] = False
                                        st.rerun()
                                    if st.button("🗑️ Löschen", key=f"del_btn_{orig_idx}", use_container_width=True):
                                        confirm_delete({"user": row['user'], "datum": row['datum'], "betrag": row['betrag'],
                                                        "betrag_anzeige": row['betrag_anzeige'], "kategorie": row['kategorie']})

                            if st.session_state['edit_idx'] == orig_idx:
                                with st.form(key=f"edit_form_{orig_idx}"):
                                    st.markdown(
                                        "<p style='font-family:DM Sans,sans-serif;color:#38bdf8;font-weight:500;font-size:14px;margin-bottom:12px;'>Eintrag bearbeiten</p>",
                                        unsafe_allow_html=True,
                                    )
                                    ec1, ec2 = st.columns(2)
                                    with ec1:
                                        e_betrag = st.number_input(f"Betrag in {currency_sym}", value=abs(float(betrag_num)), min_value=0.01, step=0.01, format="%.2f")
                                        e_datum  = st.date_input("Datum", value=datetime.date.fromisoformat(str(row['datum'])))
                                    with ec2:
                                        e_typ = st.selectbox("Typ", ["Einnahme", "Ausgabe", "Depot"],
                                                             index=["Einnahme", "Ausgabe", "Depot"].index(row['typ']) if row['typ'] in ["Einnahme", "Ausgabe", "Depot"] else 1)
                                        e_all_cats = DEFAULT_CATS[e_typ] + load_custom_cats(user_name, e_typ)
                                        e_cat = st.selectbox("Kategorie", e_all_cats,
                                                             index=e_all_cats.index(row['kategorie']) if row['kategorie'] in e_all_cats else 0)
                                    e_notiz = st.text_input("Notiz (optional)", value=notiz)
                                    cs, cc = st.columns(2)
                                    with cs: saved     = st.form_submit_button("Speichern", use_container_width=True, type="primary")
                                    with cc: cancelled = st.form_submit_button("Abbrechen", use_container_width=True)
                                    if saved:
                                        df_all = _gs_read("transactions")
                                        if 'deleted' not in df_all.columns: df_all['deleted'] = ''
                                        match_idx = df_all[find_row_mask(df_all, row)].index
                                        if len(match_idx) > 0:
                                            neuer_betrag = e_betrag if e_typ == "Einnahme" else -e_betrag
                                            df_all.loc[match_idx[0], ['datum', 'typ', 'kategorie', 'betrag', 'notiz']] = [str(e_datum), e_typ, e_cat, neuer_betrag, e_notiz]
                                            _gs_update("transactions", df_all)
                                            st.session_state['edit_idx'] = None
                                            st.success("✅ Gespeichert!")
                                            st.rerun()
                                        else:
                                            st.error("❌ Eintrag nicht gefunden.")
                                    if cancelled:
                                        st.session_state['edit_idx'] = None
                                        st.rerun()

                    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                    p1, p2, p3 = st.columns([1, 4, 1])
                    with p1:
                        if st.button("‹ Neuer", use_container_width=True, disabled=(page <= 0)):
                            st.session_state['tx_page'] = page - 1; st.rerun()
                    with p2:
                        st.markdown(
                            f"<div style='text-align:center;font-family:DM Mono,monospace;color:#334155;font-size:12px;padding:8px 0;'>"
                            f"Seite {page + 1} von {max_page + 1} · {total} Einträge</div>",
                            unsafe_allow_html=True,
                        )
                    with p3:
                        if st.button("Älter ›", use_container_width=True, disabled=(page >= max_page)):
                            st.session_state['tx_page'] = page + 1; st.rerun()
        except Exception as e:
            st.warning(f"Fehler beim Laden: {e}")

    # ── Tab 2: Daueraufträge ──────────────────────────────────
    with tabs[1]:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        das = load_dauerauftraege(user_name)

        if das:
            st.markdown(
                "<div style='font-family:DM Mono,monospace;color:#334155;font-size:10px;font-weight:500;"
                "letter-spacing:1.5px;text-transform:uppercase;margin-bottom:14px;'>Aktive Daueraufträge</div>",
                unsafe_allow_html=True,
            )
            for da in das:
                farbe_da = '#4ade80' if da['typ'] == 'Einnahme' else ('#38bdf8' if da['typ'] == 'Depot' else '#f87171')
                sign_da  = '+' if da['typ'] == 'Einnahme' else '-'
                dc1, dc2, dc3, dc4, dc5 = st.columns([3, 2, 2, 2, 1])
                dc1.markdown(f"<span style='font-family:DM Sans,sans-serif;color:#e2e8f0;font-size:13px;line-height:2.4;display:block;'>⚙️ {da['name']}</span>", unsafe_allow_html=True)
                dc2.markdown(f"<span style='font-family:DM Mono,monospace;color:{farbe_da};font-size:13px;line-height:2.4;display:block;'>{sign_da}{da['betrag']:,.2f} {currency_sym}</span>", unsafe_allow_html=True)
                dc3.markdown(f"<span style='font-family:DM Sans,sans-serif;color:#64748b;font-size:12px;line-height:2.4;display:block;'>{da['typ']}</span>", unsafe_allow_html=True)
                dc4.markdown(f"<span style='font-family:DM Sans,sans-serif;color:#334155;font-size:12px;line-height:2.4;display:block;'>{da['kategorie']}</span>", unsafe_allow_html=True)
                with dc5:
                    if st.button("🗑️", key=f"del_da_{da['id']}", use_container_width=True, type="secondary"):
                        delete_dauerauftrag(user_name, da['id']); st.rerun()
            st.markdown("<hr>", unsafe_allow_html=True)

        st.markdown(
            "<div style='font-family:DM Mono,monospace;color:#334155;font-size:10px;font-weight:500;"
            "letter-spacing:1.5px;text-transform:uppercase;margin-bottom:14px;'>Neuen Dauerauftrag erstellen</div>"
            "<p style='font-family:DM Sans,sans-serif;color:#475569;font-size:13px;margin-bottom:16px;'>"
            "Daueraufträge werden automatisch am 1. jedes Monats gebucht.</p>",
            unsafe_allow_html=True,
        )
        with st.form("da_form", clear_on_submit=True):
            da1, da2 = st.columns(2)
            with da1:
                da_name   = st.text_input("Name", placeholder="z.B. Miete, Netflix, Fitnessstudio")
                da_betrag = st.number_input(f"Betrag ({currency_sym})", min_value=0.01, step=0.01, format="%.2f")
            with da2:
                da_typ      = st.selectbox("Typ", ["Ausgabe", "Einnahme", "Depot"])
                da_all_cats = DEFAULT_CATS[da_typ] + load_custom_cats(user_name, da_typ)
                da_kat      = st.selectbox("Kategorie", da_all_cats)
            if st.form_submit_button("Dauerauftrag erstellen", use_container_width=True, type="primary"):
                if not da_name.strip():
                    st.error("Bitte einen Namen eingeben.")
                else:
                    save_dauerauftrag(user_name, da_name.strip(), da_betrag, da_typ, da_kat)
                    st.success(f"✅ Dauerauftrag '{da_name.strip()}' erstellt!")
                    st.rerun()

        if not das:
            st.markdown(
                "<div style='text-align:center;padding:30px 20px;'>"
                "<div style='font-size:36px;margin-bottom:12px;'>⚙️</div>"
                "<p style='font-family:DM Sans,sans-serif;color:#334155;font-size:14px;'>"
                "Noch keine Daueraufträge. Erstelle deinen ersten Dauerauftrag!</p></div>",
                unsafe_allow_html=True,
            )
