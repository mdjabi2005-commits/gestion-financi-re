#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestio V4 - Financial Management Application
Refactored modular version

@author: djabi
@version: 4.0 (Refactored)
@date: 2025-11-17
"""

import streamlit as st
import logging

# ==============================
# STREAMLIT CONFIGURATION
# ==============================
st.set_page_config(
    page_title="Gestio V4 - Gestion Financière",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================
# IMPORTS - Configuration
# ==============================
from config import (
    DATA_DIR, DB_PATH, TO_SCAN_DIR, SORTED_DIR,
    REVENUS_A_TRAITER, REVENUS_TRAITES
)

# ==============================
# IMPORTS - Database
# ==============================
from modules.database import (
    init_db,
    migrate_database_schema,
    TransactionRepository
)

# ==============================
# IMPORTS - UI
# ==============================
from modules.ui.styles import load_all_styles
from modules.ui.helpers import refresh_and_rerun
from modules.ui.toast_components import toast_success

# ==============================
# IMPORTS - Pages
# ==============================
from modules.ui.pages import (
    interface_accueil,
    interface_transactions_simplifiee,
    interface_voir_transactions,
    interface_portefeuille
)

# ==============================
# LOGGING CONFIGURATION
# ==============================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gestio_app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==============================
# DATABASE INITIALIZATION
# ==============================
try:
    init_db()
    migrate_database_schema()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Database initialization failed: {e}")
    st.error(f"⚠️ Erreur d'initialisation de la base de données : {e}")

# ==============================
# LOAD STYLES
# ==============================
load_all_styles()

# ==============================
# MAIN APPLICATION
# ==============================
def main():
    """Main application router."""
    try:
        # Sidebar navigation
        st.sidebar.title("💰 Gestio V4")
        st.sidebar.markdown("---")

        # Initialize session state for navigation
        if "requested_page" not in st.session_state:
            st.session_state.requested_page = None
        
        # Navigation menu
        pages = [
            "🏠 Accueil",
            "💳 Transactions",
            "📊 Voir Transactions",
            "💼 Portefeuille"
        ]
        
        # If a page was requested programmatically, set the radio value directly
        if st.session_state.requested_page and st.session_state.requested_page in pages:
            st.session_state.nav_radio = st.session_state.requested_page
            st.session_state.requested_page = None  # Reset after use
        
        # Initialize radio state if not exists
        if "nav_radio" not in st.session_state:
            st.session_state.nav_radio = "🏠 Accueil"
        
        page = st.sidebar.radio(
            "Navigation",
            pages,
            key="nav_radio"
        )

        st.sidebar.markdown("---")

        # Info section
        st.sidebar.markdown("### ℹ️ Informations")
        st.sidebar.info(f"""
        **Version:** 4.0 (Refactored)

        **Base de données :**
        `{DB_PATH}`

        **Dossiers :**
        - Tickets : `{TO_SCAN_DIR}`
        - Revenus : `{REVENUS_A_TRAITER}`
        """)

        # Refresh button
        if st.sidebar.button("🔄 Rafraîchir", use_container_width=True):
            refresh_and_rerun()

        # Page routing
        if page == "🏠 Accueil":
            interface_accueil()

        elif page == "💳 Transactions":
            interface_transactions_simplifiee()

        elif page == "📊 Voir Transactions":
            interface_voir_transactions()  # Redirect to main transaction page

        elif page == "💼 Portefeuille":
            interface_portefeuille()



    except Exception as e:
        logger.critical(f"Application V4 failed: {e}", exc_info=True)
        st.error(f"""
        ❌ L'application V4 a rencontré une erreur critique: {e}

        **Solutions possibles :**
        1. Vérifiez les logs (gestio_app.log)
        2. Redémarrez l'application
        3. Contactez le support si le problème persiste
        """)

# ==============================
# APPLICATION ENTRY POINT
# ==============================
if __name__ == "__main__":
    main()
