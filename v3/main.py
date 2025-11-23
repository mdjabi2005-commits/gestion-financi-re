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
from modules.ui.components import toast_success

# ==============================
# IMPORTS - Pages
# ==============================
from modules.ui.pages import (
    interface_accueil,
    interface_transactions_simplifiee,
    interface_voir_transactions_v3,
    interface_portefeuille,
    interface_ocr_analysis_complete,
    render_problematic_tickets_page
)

# ==============================
# IMPORTS - Triangle & Table Pages
# ==============================
from modules.ui.pages.triangle_table_demo import show_demo
from modules.ui.pages.triangle_table_v1 import interface_triangle_table_v1
from modules.ui.pages.triangle_table_v2 import interface_triangle_table_v2

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

        # Navigation menu
        page = st.sidebar.radio(
            "Navigation",
            [
                "🏠 Accueil",
                "💳 Transactions",
                "📊 Voir Transactions",
                "💼 Portefeuille",
                "🔍 Analyse OCR",
                "🔧 Tickets Problématiques",
                "---",
                "📊 Triangle & Table Demo",
                "📊 Triangle & Table V1",
                "📊 Triangle & Table V2"
            ]
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
            interface_voir_transactions_v3()

        elif page == "💼 Portefeuille":
            interface_portefeuille()

        elif page == "🔍 Analyse OCR":
            interface_ocr_analysis_complete()

        elif page == "🔧 Tickets Problématiques":
            render_problematic_tickets_page()

        elif page == "📊 Triangle & Table Demo":
            show_demo()

        elif page == "📊 Triangle & Table V1":
            interface_triangle_table_v1()

        elif page == "📊 Triangle & Table V2":
            interface_triangle_table_v2()

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
