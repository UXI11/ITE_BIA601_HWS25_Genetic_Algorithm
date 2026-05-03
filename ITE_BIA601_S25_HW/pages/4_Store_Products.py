l
# 4_Store_Products.py - Interactive Store Simulator
# This page creates a full shopping experience where the user can:
#   - View GA-powered product recommendations
#   - Browse all products with category filters
#   - Add items to a shopping cart
#   - Complete a purchase (which feeds back into the behavior log)
# The purchase feedback loop is important because it turns a visual
# action into data that the GA can use to improve future recommendations

import streamlit as st
from backend import get_recommendations

st.set_page_config(page_title="Store Simulator", layout="wide")

from rtl import apply_rtl
apply_rtl()

st.title("🛒 Shopping Platform")

import hashlib

# ---- Category Icons ----
# Each product category has a list of emoji icons.
# Products are assigned icons in order from their category list.
CATEGORY_ICONS = {
    'Electronics': ['💻', '📱', '🎧', '📸', '⌚', '📺', '🖥️', '🖱️', '🖨️', '⌨️', '🎮', '🕹️', '📻', '🎙️', '📹', '📼', '📽️', '🔋', '🔌', '💡'],
    'Books': ['📚', '📖', '📕', '📗', '📘', '📒', '📓', '📜', '📰', '📝', '🧾', '🔖', '📄', '📃', '📁', '📂'],
    'Clothes': ['👕', '👖', '👗', '🧥', '👚', '👟', '👔', '🧦', '🧣', '🧤', '🧢', '👒', '🎽', '🩳', '👞', '🥾', '👡', '👢', '🥿', '👜', '🎒'],
    'Home Appliances': ['🏠', '🛏️', '🛋️', '🪑', '🪴', '🛁', '🚪', '🖼️', '🧹', '🧺', '🧻', '🚽', '🪟', '🧊', '🍽️', '🥣', '🏺', '🛋'],
    'Toys': ['🧸', '🧩', '🪀', '🪁', '👾', '🏎️', '🚂', '🎲', '🎯', '🪄'],
    'Sports': ['⚽', '🏀', '🏈', '⚾', '🎾', '🏐', '🏉', '🏓', '🏸', '🥊', '🥋', '🎿', '🏂', '🏋️', '🚴'],
    'Perfumes': ['🧴', '⚗️', '🔮', '⚱️', '🌸', '✨'],
    'General': ['🛍️', '📦', '🎁', '🛒', '🏷️', '💎', '🪙', '✨', '🎈', '🎉']
}

# ---- Session State Initialization ----
# Set up session keys for the cart, purchase history, product detail toggles, and icon map
if 'cart' not in st.session_state:
    st.session_state['cart'] = []
if 'purchase_history' not in st.session_state:
    st.session_state['purchase_history'] = []
if 'show_details' not in st.session_state:
    st.session_state['show_details'] = {}
if 'icon_map' not in st.session_state:
    st.session_state['icon_map'] = {}

# ---- Helper Functions ----
# These are separated from the main page flow to keep the store logic organized.

def add_to_cart(pid, price):
    """Add a product to the shopping cart with its price."""
    st.session_state['cart'].append({'id': pid, 'price': price})
    st.toast(f"Product {pid} added to cart 🛒", icon="✅")

def toggle_details(pid):
    """Toggle the detail view for a specific product on/off."""
    if pid in st.session_state['show_details']:
        st.session_state['show_details'][pid] = not st.session_state['show_details'][pid]
    else:
        st.session_state['show_details'][pid] = True

# ---- Main Store Content ----
if st.session_state.get('data_loaded'):
    u_feat = st.session_state['u_feat']
    p_feat = st.session_state['p_feat']
    beh = st.session_state['behavior']
    
    # Build the icon map: assign a unique emoji to each product based on its category
    if not st.session_state['icon_map']:
        for cat in p_feat['category'].unique():
            cat_products = p_feat[p_feat['category'] == cat]['product_id'].tolist()
            cat_products.sort() # standard sorting
            icons_list = CATEGORY_ICONS.get(cat, CATEGORY_ICONS['General'])
            for idx, p_id in enumerate(cat_products):
                # Take icons in order and reset when finished
                st.session_state['icon_map'][p_id] = icons_list[idx % len(icons_list)]
                
    # ---- Sidebar: User Profile ----
    st.sidebar.markdown("### 👤 User Profile")
    user_id = st.sidebar.selectbox("View store as user:", u_feat['user_id'].unique())
    user_info = u_feat[u_feat['user_id'] == user_id].iloc[0]
    
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Age:** {int(user_info['age'])}")
    st.sidebar.markdown(f"**Top Category:** {user_info['top_category']}")
    
    # ---- Sidebar: Shopping Cart ----
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🛒 Shopping Cart")
    cart_items = st.session_state['cart']
    
    # Show success screen after a completed purchase and hide the rest of the store
    if st.session_state.get('purchase_success_msg'):
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("<div style='background-color:#1A202C; padding:50px; border-radius:15px; text-align:center; border: 2px solid #10B981;'>"
                    "<h1 style='font-size: 80px;'>✅</h1>"
                    "<h2 style='color:#10B981;'>Payment completed successfully!</h2>"
                    "<p style='font-size: 18px; color: #E2E8F0;'>Your order is saved and the system is updated. You can review your purchases in the Purchase History page.</p>"
                    "</div><br>", unsafe_allow_html=True)
        
        c_spacer1, c_btn, c_spacer2 = st.columns([1, 1, 1])
        with c_btn:
            if st.button("Return to shopping 🛍️", use_container_width=True, type="primary"):
                st.session_state['purchase_success_msg'] = False
                st.rerun()
                
        st.stop()

    if len(cart_items) == 0:
        st.sidebar.info("Cart is empty")
    else:
        st.sidebar.success(f"Count: {len(cart_items)} item(s)")
        total_price = sum(item['price'] for item in cart_items)
        st.sidebar.markdown(f"**Total Payable:** ${total_price:.2f}")
        
        sc1, sc2 = st.sidebar.columns(2)
        with sc1:
            if st.button("💳 Checkout", use_container_width=True, type="primary"):
                import datetime
                import pandas as pd
                new_behaviors = []
                for item in st.session_state['cart']:
                    item_copy = item.copy()
                    item_copy['date'] = datetime.datetime.now().strftime("%I:%M %p")
                    st.session_state['purchase_history'].append(item_copy)
                    
                    # ---- Feedback Loop ----
                    # Create a new behavior record for each purchased item.
                    # This is critical: it turns a purchase into feedback data
                    # that goes back into the behavior log, so the GA can learn
                    # from the user's new actions in future recommendations.
                    new_behaviors.append({
                        'user_id': user_id,               # Current User
                        'product_id': item['id'],         # Purchased Product
                        'viewed': 1, 'clicked': 1, 'purchased': 1,
                        'implicit_score': 8               # Max score (5 purchase + 2 click + 1 view)
                    })
                    
                # Append new behavior records to the session behavior table
                if new_behaviors:
                    new_b_df = pd.DataFrame(new_behaviors)
                    st.session_state['behavior'] = pd.concat([st.session_state['behavior'], new_b_df], ignore_index=True)

                # Clear the cart and show the success message
                st.session_state['cart'] = []
                st.session_state['purchase_success_msg'] = True
                st.rerun()
        with sc2:
            if st.button("🗑️ Clear", use_container_width=True):
                st.session_state['cart'] = []
                st.rerun()


    # ---- Personalized Recommendations Section ----
    # Use the GA to generate smart recommendations for the current user
    st.markdown("### 🌟 Recommendations carefully selected for you")
    with st.spinner("Analyzing your shopping pattern to provide the best..."):
        recommended_ids = get_recommendations(user_id, u_feat, p_feat, beh)
        
    # Display each recommended product as a card with icon, details, and add-to-cart button
    rec_cols = st.columns(len(recommended_ids))
    for i, pid in enumerate(recommended_ids):
        p_info = p_feat[p_feat['product_id'] == pid].iloc[0]
        with rec_cols[i]:
            with st.container(border=True):
                icon = st.session_state['icon_map'].get(pid, '🛍️')
                st.markdown(f"<div style='text-align:center; font-size:60px; padding:20px; background-color:#262730; border-radius:8px; margin-bottom:10px;'>{icon}</div>", unsafe_allow_html=True)
                st.markdown(f"<h4 style='color:#1E90FF; text-align:center;'>{pid} ✨</h4>", unsafe_allow_html=True)
                st.markdown(f"**Category:** {p_info['category']}<br>**Price:** ${p_info['price']}<br>**Rating:** {round(p_info['prod_avg_rating'], 1)} ⭐", unsafe_allow_html=True)
                
                st.button("Add to Cart 🛒", key=f"rec_add_{pid}", on_click=add_to_cart, args=(pid, p_info['price']), type="primary", use_container_width=True)

    st.markdown("---")
    

    # ---- General Product Browsing Section ----
    # This section lets the user filter and browse all available products freely
    st.markdown("### 🛍️ Available Products List")
    
    # Category filter dropdown
    selected_category = st.selectbox("Filter by Category:", ["All"] + list(p_feat['category'].unique()))
    
    if selected_category == "All":
        display_products = p_feat.head(20) # Limit to 20 products for performance
        st.caption("Showing first 20 products")
    else:
        display_products = p_feat[p_feat['category'] == selected_category].head(20)
    
    # Display products in a 4-column grid layout
    grid_cols = st.columns(4)
    for element_idx, (idx, row) in enumerate(display_products.iterrows()):
        col_idx = element_idx % 4
        pid = row['product_id']
        with grid_cols[col_idx]:
            with st.container(border=True):
                icon = st.session_state['icon_map'].get(pid, '🛍️')
                st.markdown(f"<div style='text-align:center; font-size:60px; padding:20px; background-color:#262730; border-radius:8px; margin-bottom:10px;'>{icon}</div>", unsafe_allow_html=True)
                st.markdown(f"<h4 style='text-align:center;'>{pid}</h4>", unsafe_allow_html=True)
                st.markdown(f"**Category:** {row['category']}<br>**Price:** ${row['price']}<br>**Rating:** {round(row['prod_avg_rating'], 1)} ⭐", unsafe_allow_html=True)
                
                # Show extra details if the user clicked the "Details" button for this product
                if st.session_state['show_details'].get(pid, False):
                    st.info(f"This product ({pid}) from category {row['category']} is considered one of the premium items on the platform at a great price!")

                c1, c2 = st.columns(2)
                with c1:
                    st.button("Details", key=f"details_{pid}_{idx}", on_click=toggle_details, args=(pid,), use_container_width=True)
                with c2:
                    st.button("Add", key=f"grid_add_{pid}_{idx}", on_click=add_to_cart, args=(pid, row['price']), type="primary", use_container_width=True)

else:
    st.warning("Please return to the Home Page to load the database first.")
