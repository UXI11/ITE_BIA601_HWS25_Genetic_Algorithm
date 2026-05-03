
# 1_Data_General.py - Data Overview Page
# This page shows general statistics about the loaded data.
# It displays the total number of users, products, and behavior
# records, then previews the first 50 rows of the behavior log.
# Its purpose is purely informational — no algorithm runs here.

import streamlit as st

# Page setup with a descriptive title
st.set_page_config(page_title="Data Overview", layout="wide")

# Apply direction fix and load custom stylesheet
from rtl import apply_rtl
apply_rtl()

st.title("📊 Data Overview and Analysis")

# Only show content if data has been loaded from the Home Page
if st.session_state.get('data_loaded'):
    # Display three summary metric cards for quick overview
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Users", len(st.session_state['users']))
    c2.metric("Available Products", len(st.session_state['products']))
    c3.metric("Behavior Records", len(st.session_state['behavior']))

    # Show a preview of the behavior interaction log
    st.markdown("### User Interaction Log (Behavior Data)")
    # Show first 50 records only so the page doesn't become slow
    df_to_show = st.session_state['behavior'].head(50).copy()
    # Change index to start from 1 instead of 0 for better readability
    df_to_show.index = df_to_show.index + 1
    st.dataframe(df_to_show, use_container_width=True)
else:
    st.warning("Please visit the Home Page first to prepare and load the database.")
