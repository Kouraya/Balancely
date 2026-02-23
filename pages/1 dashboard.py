import streamlit as st
from shared import setup
import pages.dashboard as page_dashboard

user_settings, t, currency_sym = setup("Dashboard · Balancely")
if user_settings is None:
    st.stop()

page_dashboard.render(st.session_state['user_name'], user_settings, t, currency_sym)
