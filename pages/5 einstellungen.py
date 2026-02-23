import streamlit as st
from shared import setup
import pages.settings as page_settings
from constants import THEMES

user_settings, t, currency_sym = setup("Einstellungen · Balancely")
if user_settings is None:
    st.stop()

theme_name = st.session_state.get('theme', 'Ocean Blue')
page_settings.render(st.session_state['user_name'], user_settings, theme_name, t, currency_sym)
