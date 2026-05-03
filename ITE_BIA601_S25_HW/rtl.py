
# rtl.py - Display Direction and Style Loader
# This file does not add any recommendation logic.
# Its job is to configure the page direction (LTR) and rename
# the default "App" label in the sidebar to "Home Page".
# It also loads the custom CSS file for consistent styling

import streamlit as st
import streamlit.components.v1 as components

def apply_rtl():
    """
    Set the page direction to LTR and rename the sidebar navigation label.
    Also loads the custom styles.css file for the visual theme.
    """
    # Inject JavaScript to set the document direction and rename the nav link
    components.html(
        """
        <script>
            try {
                window.parent.document.documentElement.dir = "ltr";
                window.parent.document.body.dir = "ltr";
                
                // Find the default 'App' label in the sidebar and rename it to 'Home Page'
                const navLinks = window.parent.document.querySelectorAll('[data-testid="stSidebarNav"] span');
                navLinks.forEach(link => {
                    if (link.textContent.trim().toLowerCase() === 'app' || link.textContent.trim() === 'App') {
                        link.textContent = '🏠 Home Page';
                    }
                });
            } catch (e) {}
        </script>
        """,
        height=0,
        width=0,
    )
    
    # Load the external CSS stylesheet for the visual theme (colors, cards, sidebar, etc.)
    try:
        with open('assets/styles.css') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except:
        pass
