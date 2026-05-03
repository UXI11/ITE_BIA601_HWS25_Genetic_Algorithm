
# 5_Purchase_History.py - Purchase History Page
# This page completes the simulation loop by showing the effect
# of purchases made in the Store page. It reads purchase_history
# from session_state, converts it to a DataFrame, adds icons,
# calculates the total cost, and allows clearing the history.
# The algorithm can improve recommendations if the user makes
# a new purchase, because the behavior log gets updated

import streamlit as st
import pandas as pd

st.set_page_config(page_title="Purchase History", layout="wide")

from rtl import apply_rtl
apply_rtl()

st.title("📦 My Purchase History")
st.markdown("---")

# Initialize purchase history list if it doesn't exist yet
if 'purchase_history' not in st.session_state:
    st.session_state['purchase_history'] = []

history = st.session_state['purchase_history']

if len(history) == 0:
    # No purchases yet — show a helpful message
    st.info("You haven't made any purchases yet in the current session. 🛒")
    st.markdown("You can go to the **Store Products** page, add items to the cart, and complete the purchase to see them recorded here.")
else:
    st.success(f"You have purchased {len(history)} product(s) in total!")
    
    # Convert the list of purchase dictionaries into a structured DataFrame
    df = pd.DataFrame(history)
    
    # Fetch product icons from the icon_map created by the Store page
    icon_map = st.session_state.get('icon_map', {})
    df['Product Image 🖼️'] = df['id'].apply(lambda x: icon_map.get(x, '🛍️'))
    
    # Rename columns for a cleaner display
    df = df.rename(columns={'id': 'Product Code', 'price': 'Price ($)', 'date': 'Purchase Time'})
    
    # Rearrange columns so the image icon appears first in the table
    if 'Product Code' in df.columns:
        df = df[['Product Image 🖼️', 'Product Code', 'Price ($)', 'Purchase Time']]
        
    # Change index to start from 1 instead of 0 for better readability
    df.index = df.index + 1
        
    st.dataframe(df, use_container_width=True)
    
    # Show the total cost of all purchases in this session
    st.markdown("---")
    st.markdown(f"### 💰 Total Purchase Value: ${df['Price ($)'].sum():.2f}")
    
    # Option to clear the entire purchase history
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🗑️ Clear Purchase History", type="secondary", use_container_width=True):
        st.session_state['purchase_history'] = []
        st.rerun()
