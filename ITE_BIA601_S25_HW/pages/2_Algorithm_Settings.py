l
# 2_Algorithm_Settings.py - GA Parameter Configuration Page
# This page lets the user adjust the Genetic Algorithm parameters.
# It does NOT run the algorithm — it only saves values to session_state.

import streamlit as st

st.set_page_config(page_title="GA Parameters", layout="wide")

from rtl import apply_rtl
apply_rtl()

st.title("⚙️ Algorithm Parameters Dashboard")

# Create a form so all parameter changes are submitted together
with st.form("ga_params_form"):
    # Slider for the number of generations (more = longer search, possibly better results)
    gens = st.slider("Number of Generations", 5, 100, st.session_state.get('generations', 15))
    # Slider for population size (more chromosomes = wider search per generation)
    pop_size = st.slider("Population Size", 10, 100, st.session_state.get('pop_size', 20))
    # Slider for mutation rate (higher = more exploration, lower = more exploitation)
    mut_rate = st.slider("Mutation Rate", 0.01, 1.0, float(st.session_state.get('mutation_rate', 0.1)), step=0.05)
    
    # Save the new values to session_state when submitted
    sub = st.form_submit_button("Save Settings & Update Model")
    if sub:
        st.session_state['generations'] = gens
        st.session_state['pop_size'] = pop_size
        st.session_state['mutation_rate'] = mut_rate
        st.success("Parameters updated successfully! You can now return to the Home Page to process results with new values.")
