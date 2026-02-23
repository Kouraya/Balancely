import pandas as pd
import streamlit as st

from constants import DEFAULT_CATS
from database import (
    _gs_read, _gs_update,
    load_custom_cats, save_custom_cat, delete_custom_cat, update_custom_cat,
)


@st.dialog("➕ Neue Kategorie")
def new_category_dialog():
    typ = st.session_state.get('new_cat_typ', 'Ausgabe')
    st.markdown(
        f"<p style='color:#64748b;font-size:13px;margin-bottom:20px;font-family:DM Sans,sans-serif;'>"
        f"Für Typ: <span style='color:#38bdf8;font-weight:500;'>{typ}</span></p>",
        unsafe_allow_html=True,
    )
    nc1, nc2 = st.columns([1, 3])
    with nc1:
        new_emoji = st.text_input("Emoji", placeholder="🎵", max_chars=4)
    with nc2:
        new_name = st.text_input("Name", placeholder="z.B. Musik")
    nc_typ = st.selectbox(
        "Typ", ["Ausgabe", "Einnahme", "Depot"],
        index=["Ausgabe", "Einnahme", "Depot"].index(typ) if typ in ["Ausgabe", "Einnahme", "Depot"] else 0,
    )
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Speichern", use_container_width=True, type="primary"):
            if not new_name.strip():
                st.error("Bitte einen Namen eingeben.")
            else:
                label = f"{new_emoji.strip()} {new_name.strip()}" if new_emoji.strip() else new_name.strip()
                existing = load_custom_cats(st.session_state['user_name'], nc_typ) + DEFAULT_CATS.get(nc_typ, [])
                if label in existing:
                    st.error("Kategorie existiert bereits.")
                else:
                    save_custom_cat(st.session_state['user_name'], nc_typ, label)
                    st.session_state['show_new_cat'] = False
                    st.rerun()
    with c2:
        if st.button("Abbrechen", use_container_width=True):
            st.session_state['show_new_cat'] = False
            st.rerun()


@st.dialog("✏️ Kategorie bearbeiten")
def edit_category_dialog():
    data = st.session_state.get('edit_cat_data')
    if not data:
        st.rerun()
        return
    old_label, typ, user = data['old_label'], data['typ'], data['user']
    parts = old_label.split(' ', 1)
    init_emoji = parts[0] if len(parts) == 2 and len(parts[0]) <= 4 else ''
    init_name  = parts[1] if len(parts) == 2 and len(parts[0]) <= 4 else old_label
    nc1, nc2 = st.columns([1, 3])
    with nc1:
        new_emoji = st.text_input("Emoji", value=init_emoji, max_chars=4)
    with nc2:
        new_name = st.text_input("Name", value=init_name)
    new_typ = st.selectbox(
        "Typ", ["Ausgabe", "Einnahme", "Depot"],
        index=["Ausgabe", "Einnahme", "Depot"].index(typ) if typ in ["Ausgabe", "Einnahme", "Depot"] else 0,
    )
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Speichern", use_container_width=True, type="primary"):
            if not new_name.strip():
                st.error("Bitte einen Namen eingeben.")
            else:
                new_label = f"{new_emoji.strip()} {new_name.strip()}" if new_emoji.strip() else new_name.strip()
                existing  = load_custom_cats(user, new_typ) + DEFAULT_CATS.get(new_typ, [])
                if new_label != old_label and new_label in existing:
                    st.error("Kategorie existiert bereits.")
                else:
                    if new_typ != typ:
                        delete_custom_cat(user, typ, old_label)
                        save_custom_cat(user, new_typ, new_label)
                    else:
                        update_custom_cat(user, typ, old_label, new_label)
                    st.session_state['edit_cat_data'] = None
                    st.rerun()
    with c2:
        if st.button("Abbrechen", use_container_width=True):
            st.session_state['edit_cat_data'] = None
            st.rerun()


@st.dialog("Kategorie löschen")
def confirm_delete_cat():
    data = st.session_state.get('delete_cat_data')
    if not data:
        st.rerun()
        return
    st.markdown(
        f"<p style='color:#e2e8f0;font-size:15px;margin-bottom:8px;'>Kategorie wirklich löschen?</p>"
        f"<p style='color:#64748b;font-size:14px;'>{data['label']}</p>",
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Löschen", use_container_width=True, type="primary"):
            delete_custom_cat(data['user'], data['typ'], data['label'])
            st.session_state['delete_cat_data'] = None
            st.rerun()
    with c2:
        if st.button("Abbrechen", use_container_width=True):
            st.session_state['delete_cat_data'] = None
            st.rerun()


@st.dialog("Eintrag löschen")
def confirm_delete(row_data):
    st.markdown(
        f"<p style='color:#e2e8f0;font-size:15px;margin-bottom:6px;'>Eintrag wirklich löschen?</p>"
        f"<p style='color:#475569;font-size:13px;'>{row_data['datum']} · {row_data['betrag_anzeige']} · {row_data['kategorie']}</p>",
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Löschen", use_container_width=True, type="primary"):
            df_all = _gs_read("transactions")
            if 'deleted' not in df_all.columns:
                df_all['deleted'] = ''
            mask = (
                (df_all['user'] == row_data['user']) &
                (df_all['datum'].astype(str) == str(row_data['datum'])) &
                (pd.to_numeric(df_all['betrag'], errors='coerce') == pd.to_numeric(row_data['betrag'], errors='coerce')) &
                (df_all['kategorie'] == row_data['kategorie']) &
                (~df_all['deleted'].astype(str).str.strip().str.lower().isin(['true', '1', '1.0']))
            )
            idx = df_all[mask].index
            if len(idx) > 0:
                df_all.loc[idx[0], 'deleted'] = 'True'
                _gs_update("transactions", df_all)
                st.session_state['edit_idx'] = None
                st.rerun()
            else:
                st.error("Eintrag nicht gefunden.")
    with c2:
        if st.button("Abbrechen", use_container_width=True):
            st.rerun()
