"""
Gemeinsame Setup-Logik für alle Pages.
Jede Page ruft setup() auf – gibt (user_settings, theme, currency_sym) zurück
oder None wenn nicht eingeloggt (dann wird zur Login-Seite weitergeleitet).
"""
import datetime
import streamlit as st

from constants import THEMES, CURRENCY_SYMBOLS
from database import load_user_settings, apply_dauerauftraege, _gs_invalidate
from styling import inject_base_css, inject_theme

_DEFAULTS = {
    'logged_in': False, 'user_name': "", 'auth_mode': 'login', 't_type': 'Ausgabe',
    'pending_user': {}, 'verify_code': "", 'verify_expiry': None,
    'reset_email': "", 'reset_code': "", 'reset_expiry': None,
    'edit_idx': None, 'show_new_cat': False, 'new_cat_typ': 'Ausgabe',
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


def init_session():
    for k, v in _DEFAULTS.items():
        if k not in st.session_state:
            st.session_state[k] = v


def setup(page_title="Balancely"):
    """Initialisiert Session, CSS, Theme, Sidebar. Gibt user_settings etc. zurück."""
    st.set_page_config(page_title=page_title, page_icon="⚖️", layout="wide")
    init_session()
    inject_base_css()

    if not st.session_state['logged_in']:
        st.switch_page("Balancely.py")
        return None, None, None

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

    _render_sidebar(_t, _theme_name, _user_settings, _currency_sym)

    if not st.session_state.pop('_dialog_just_opened', False):
        st.session_state['show_new_cat']  = False
        st.session_state['edit_cat_data'] = None
        st.session_state['delete_cat_data'] = None

    return _user_settings, _t, _currency_sym


def _render_sidebar(t, theme_name, user_settings, currency_sym):
    with st.sidebar:
        st.markdown(
            f"<div style='padding:8px 0 16px 0;'>"
            f"<span style='font-family:DM Sans,sans-serif;font-size:20px;font-weight:600;color:#e2e8f0;letter-spacing:-0.5px;'>Balancely</span>"
            f"<span style='color:{t['primary']};font-size:20px;'> ⚖️</span></div>",
            unsafe_allow_html=True,
        )

        _avatar   = user_settings.get('avatar_url', '')
        _initials = st.session_state['user_name'][:2].upper()
        if _avatar and _avatar.startswith('http'):
            avatar_html = (
                f"<img src='{_avatar}' style='width:36px;height:36px;border-radius:50%;"
                f"object-fit:cover;border:2px solid {t['primary']}40;'>"
            )
        else:
            avatar_html = (
                f"<div style='width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,{t['accent']},{t['accent2']});"
                f"display:flex;align-items:center;justify-content:center;font-family:DM Sans,sans-serif;"
                f"font-size:13px;font-weight:600;color:#fff;flex-shrink:0;'>{_initials}</div>"
            )
        st.markdown(
            f"<div style='display:flex;align-items:center;gap:10px;margin-bottom:20px;'>{avatar_html}"
            f"<div><div style='font-family:DM Sans,sans-serif;font-size:13px;color:#e2e8f0;font-weight:500;'>{st.session_state['user_name']}</div>"
            f"<div style='font-family:DM Mono,monospace;font-size:10px;color:#334155;'>{user_settings.get('currency', 'EUR')} · {theme_name}</div></div></div>",
            unsafe_allow_html=True,
        )

        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

        # Navigation als echte Page-Links
        pages = [
            ("📈 Dashboard",      "pages/1_Dashboard.py"),
            ("💸 Transaktionen",  "pages/2_Transaktionen.py"),
            ("📂 Analysen",       "pages/3_Analysen.py"),
            ("🪣 Spartöpfe",      "pages/4_Spartoepfe.py"),
            ("⚙️ Einstellungen",  "pages/5_Einstellungen.py"),
        ]
        for label, page_path in pages:
            if st.button(label, use_container_width=True, key=f"nav_{label}"):
                st.switch_page(page_path)

        st.markdown("<div style='height:28vh;'></div>", unsafe_allow_html=True)

        if st.button("Logout ➜", use_container_width=True, type="secondary"):
            for k in [k for k in st.session_state if k.startswith("_gs_cache_")]:
                del st.session_state[k]
            st.session_state['logged_in'] = False
            st.switch_page("Balancely.py")
