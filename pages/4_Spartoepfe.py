import streamlit as st
from shared import setup
import pages.savings_pots as page_savings_pots

user_settings, t, currency_sym = setup("Spartöpfe · Balancely")
if user_settings is None:
    st.stop()

page_savings_pots.render(st.session_state['user_name'], currency_sym)
