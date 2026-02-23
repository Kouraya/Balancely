import streamlit as st
st.set_page_config(page_title="Dashboard · Balancely", page_icon="⚖️", layout="wide")

from shared import setup
user_settings, t, currency_sym = setup()
if user_settings is None:
    st.stop()

page_dashboard.render(st.session_state['user_name'], user_settings, t, currency_sym)
