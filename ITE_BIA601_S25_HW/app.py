
# app.py - Main Home Page
# This is the entry point of the Streamlit application.
# It loads and prepares data, displays user info, runs the
# Genetic Algorithm, and shows the recommendation results

import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Import the core backend functions we built for data processing and GA optimization
from backend import load_data, clean_data, create_features, cluster_users, ga_optimize

# Set up the Streamlit page configuration (title, layout, and icon)
st.set_page_config(page_title="Intelligent RecSys", layout="wide", page_icon="💡")

# Apply the RTL/LTR direction fix and load the custom CSS stylesheet
from rtl import apply_rtl
apply_rtl()

# Sidebar navigation for the multi-page app
st.sidebar.title("Navigation Menu")
st.sidebar.success("Please select a section from the menu")

# ---- Data Initialization with Caching ----
# We use @st.cache_data so the system only loads and processes Excel files once.
# This avoids reloading data every time the user interacts with the page.
@st.cache_data
def initialize_system():
    """
    Load raw data from Excel files, clean missing values,
    build user/product feature tables, and apply K-Means clustering.
    Returns all processed DataFrames needed by the app.
    """
    users, products, ratings, behavior = load_data('data')
    users, products, ratings, behavior = clean_data(users, products, ratings, behavior)
    u_feat, p_feat, beh = create_features(users, products, ratings, behavior)
    u_feat, kmeans = cluster_users(u_feat)
    return u_feat, p_feat, beh, ratings, users, products

# ---- Session State Setup ----
# On first visit, load and store all processed data into session_state.
# This shared memory lets other pages access the same data without reloading.
if 'data_loaded' not in st.session_state:
    try:
        u_feat, p_feat, beh, ratings, users, products = initialize_system()
        st.session_state.update({
            'users': users, 'products': products, 'ratings': ratings, 'behavior': beh,
            'u_feat': u_feat, 'p_feat': p_feat, 'data_loaded': True
        })
    except Exception as e:
        st.error(f"Error loading data! Please make sure Excel files are in the data folder. Error: {e}")

# ---- Page Header ----
st.title("💡 Intelligent Recommendation System")
st.markdown("### Intelligent Algorithms Course | BIA601 - S25")
st.markdown("This system is based on scientific foundations documented in (Chapter 3: Genetic Algorithms), where recommendations are optimized by simulating natural evolution.")

# ---- Main Content (only if data is loaded successfully) ----
if st.session_state.get('data_loaded'):
    u_feat = st.session_state['u_feat']
    p_feat = st.session_state['p_feat']
    
    # Handle stale cache: if 'country' column is missing, the old data structure
    # is still cached. We need to clear and rebuild the session to fix it.
    if 'country' not in u_feat.columns:
        st.cache_data.clear()
        st.session_state.clear()
        st.rerun()
        
    # ---- User Selection ----
    # The sidebar lets the user pick an ID to view their profile and get recommendations
    st.sidebar.markdown("---")
    user_id = st.sidebar.selectbox("User ID:", u_feat['user_id'].unique())
    user_info = u_feat[u_feat['user_id'] == user_id].iloc[0]
    
    # Display the selected user's basic profile info using metric cards
    c1, c2, c3 = st.columns(3)
    c1.metric("Age", int(user_info['age']))
    c2.metric("Country", user_info['country'])
    c3.metric("Top Category", user_info['top_category'])
    
    st.markdown("---")
    st.markdown("### 🏆 Recommendation Generation & Optimization Phase")
    
    # ---- GA Parameters ----
    # Read the algorithm parameters from session_state (set by the Settings page).
    # If not set, use default values.
    pop_size = st.session_state.get('pop_size', 20)
    gens = st.session_state.get('generations', 15)
    mut_rate = st.session_state.get('mutation_rate', 0.1)
    
    # ---- Run Genetic Algorithm ----
    # Call ga_optimize to evolve the best product list for this user.
    # It returns the best chromosome (product IDs), fitness score, and history.
    with st.spinner("Processing data and loading smart recommendations..."):
        best_chrom, best_fit, history = ga_optimize(
            user_id, u_feat, p_feat, st.session_state['behavior'],
            pop_size=pop_size, generations=gens, mutation_rate=mut_rate, top_n=5
        )
    
    # ---- Display Recommendation Cards ----
    # Show 5 product cards in columns. Each card has category, price, rating,
    # and a reason tag (e.g., "Matches your interests!" if category matches).
    cols = st.columns(5)
    for i, pid in enumerate(best_chrom):
        p_info = p_feat[p_feat['product_id'] == pid].iloc[0]
        reason = "Smart Recommendation"
        if p_info['category'] == user_info['top_category']: reason = "Matches your interests!"
        
        with cols[i]:
            st.markdown(f'''
            <div class="product-card">
                <h4 style="color:var(--success)">Product: {pid}</h4>
                <p><b>Category:</b> {p_info['category']}</p>
                <p><b>Price:</b> ${p_info['price']}</p>
                <p><b>Rating:</b> {round(p_info['prod_avg_rating'], 1)} ⭐</p>
                <p style="color:var(--warning); font-size:0.8em">📌 {reason}</p>
            </div>
            ''', unsafe_allow_html=True)
            
    # ---- Fitness Evolution Chart ----
    # This line chart shows how the best fitness value improved over generations.
    # It helps visualize the GA optimization progress across the evolution process.
    st.markdown("---")
    st.markdown("### 📈 Fitness Evolution Curve Across Generations")
    fig = px.line(x=list(range(1, gens+1)), y=history, markers=True, 
                  labels={'x': 'Generations', 'y': 'Fitness'})
    fig.update_layout(plot_bgcolor='#1A0B2E', paper_bgcolor='#1A0B2E', font_color='#FFFFFF')
    st.plotly_chart(fig, use_container_width=True)
    

    st.markdown("---")
    st.markdown("<p style='text-align: center; color: var(--text-sec);'>Course Assignment: BIA601 supported by scientific research attached in the report</p>", unsafe_allow_html=True)
