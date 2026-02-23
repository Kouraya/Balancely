import streamlit as st
from shared import setup
import pages.analytics as page_analytics

user_settings, t, currency_sym = setup("Analysen · Balancely")
if user_settings is None:
    st.stop()

page_analytics.render(st.session_state['user_name'], currency_sym)
