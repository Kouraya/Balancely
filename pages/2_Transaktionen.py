import streamlit as st
from shared import setup
import pages.transactions as page_transactions

user_settings, t, currency_sym = setup("Transaktionen · Balancely")
if user_settings is None:
    st.stop()

page_transactions.render(st.session_state['user_name'], currency_sym)
