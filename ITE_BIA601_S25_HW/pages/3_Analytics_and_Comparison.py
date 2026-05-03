
# 3_Analytics_and_Comparison.py - Analytics and Comparison Dashboard
# This page combines charts and comparison analysis. It reads
# u_feat, p_feat, and behavior from session_state. It shows:
#   - Product distribution by category (pie chart)
#   - User cluster scatter plot (views vs purchases)
#   - Selected user vs cluster average comparison
# This page explains the group environment used by the Fitness
# Function in backend.py.

import streamlit as st
import plotly.express as px
from backend import get_recommendations

st.set_page_config(page_title="Analytics", layout="wide")

from rtl import apply_rtl
apply_rtl()

st.title("📈 Analytics and Comparison Dashboard")

if st.session_state.get('data_loaded'):
    # Load the processed data from session_state
    u_feat = st.session_state['u_feat']
    p_feat = st.session_state['p_feat']
    beh = st.session_state['behavior']
    
    # Let the user pick which user to analyze in detail
    st.sidebar.markdown("### 🔍 Analytics Options")
    sample_user = st.sidebar.selectbox("Select User for Analysis:", u_feat['user_id'].unique())
    st.markdown("---")

    # ---- Two-Column Chart Section ----
    c1, c2 = st.columns(2)
    with c1:
        # Pie chart: shows what percentage of products belong to each category
        st.markdown("### Product Distribution Analysis")
        fig1 = px.pie(p_feat, names='category', title="Product Distribution Ratio by Category", 
                      color_discrete_sequence=['#7C3AED', '#10B981', '#F59E0B', '#A0AEC0'])
        fig1.update_layout(paper_bgcolor='#0E1117', font_color='#FFF')
        st.plotly_chart(fig1, use_container_width=True)
        
    with c2:
        # Scatter plot: shows user positions based on views and purchases, colored by cluster
        st.markdown("### User Clusters")
        fig2 = px.scatter(u_feat, x='total_views', y='total_purchases', color=u_feat['cluster'].astype(str), 
                          title="User Distribution Inside Behavioral Clusters", hover_data=['user_id'],
                          color_discrete_sequence=['#7C3AED', '#10B981', '#F59E0B', '#3B82F6'])
                          
        # Highlight the selected user with a star marker so their position is clear
        selected_data = u_feat[u_feat['user_id'] == sample_user]
        fig2.add_scatter(x=selected_data['total_views'], y=selected_data['total_purchases'],
                         mode='markers', marker=dict(color='white', size=15, symbol='star', line=dict(color='#F59E0B', width=2)),
                         name='Selected User')
                         
        fig2.update_layout(paper_bgcolor='#0E1117', plot_bgcolor='#0E1117', font_color='#FFF')
        st.plotly_chart(fig2, use_container_width=True)

    # ---- User vs Cluster Comparison ----
    st.markdown("---")
    st.markdown(f"### 👤 Analytical Statistics for User: (`{sample_user}`)")
    user_info = u_feat[u_feat['user_id'] == sample_user].iloc[0]
    cluster_id = user_info['cluster']
    # Get all users in the same cluster for comparison
    cluster_users = u_feat[u_feat['cluster'] == cluster_id]
     
    # Show the user's stats side by side with the cluster average
    cc1, cc2, cc3, cc4 = st.columns(4)
    cc1.metric("Belongs to Cluster", f"Cluster {cluster_id}")
    cc2.metric("Total Purchases", int(user_info['total_purchases']), delta=f"Cluster Avg: {int(cluster_users['total_purchases'].mean())}", delta_color="off")
    cc3.metric("Total Clicks", int(user_info['total_clicks']), delta=f"Cluster Avg: {int(cluster_users['total_clicks'].mean())}", delta_color="off")
    cc4.metric("Total Views", int(user_info['total_views']), delta=f"Cluster Avg: {int(cluster_users['total_views'].mean())}", delta_color="off")
else:
    st.warning("Please start from the Home Page first to prepare data.")
