"""
Portfolio Page Module

Main portfolio interface with tabs for budget management, financial objectives,
overview, and forecasts.

The original interface_portefeuille() was 1391 lines and has been refactored
into separate modules for better maintainability.

Structure:
- interface_portefeuille(): Main router creating tabs
- portfolio/helpers.py: Utility functions
- portfolio/budgets.py: Budget management tab
- portfolio/objectives.py: Financial objectives tab
- portfolio/overview.py: Overview with charts
- portfolio/forecasts.py: Forecasts and predictions tab
"""

import streamlit as st
import sqlite3
from config import DB_PATH
from modules.database.connection import get_db_connection
from modules.services.recurrence_service import backfill_recurrences_to_today
from modules.ui.pages.portfolio.helpers import normalize_recurrence_column
from modules.ui.pages.portfolio.budgets import render_budgets_tab
from modules.ui.pages.portfolio.objectives import render_objectives_tab
from modules.ui.pages.portfolio.overview import render_overview_tab
from modules.ui.pages.portfolio.forecasts import render_forecasts_tab


def interface_portefeuille() -> None:
    """
    Main portfolio interface - router function creating tabs.

    Features:
    - Budget management by category
    - Financial goals tracking
    - Overview with charts
    - Forecasts and predictions

    Structure:
    - Tab 1: Budgets par catégorie
    - Tab 2: Objectifs financiers
    - Tab 3: Vue d'ensemble
    - Tab 4: Prévisions

    Returns:
        None

    Note:
        This is a refactored version of the original 1391-line function.
        Each tab is now a separate sub-function for better maintainability.
    """
    st.title("💼 Mon Portefeuille")

    # Initialiser les tables si elles n'existent pas
    conn = get_db_connection()
    cursor = conn.cursor()

    # Table budgets par catégorie
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS budgets_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            categorie TEXT UNIQUE NOT NULL,
            budget_mensuel REAL NOT NULL,
            date_creation TEXT,
            date_modification TEXT
        )
    """)

    # Table objectifs financiers (remplace les notes)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS objectifs_financiers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type_objectif TEXT NOT NULL,
            titre TEXT NOT NULL,
            montant_cible REAL,
            date_limite TEXT,
            periodicite TEXT,
            statut TEXT DEFAULT 'en_cours',
            date_creation TEXT,
            date_modification TEXT,
            date_atteint TEXT
        )
    """)

    # Table échéances pour gérer les prévisions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS echeances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            categorie TEXT NOT NULL,
            sous_categorie TEXT,
            montant REAL NOT NULL,
            date_echeance TEXT NOT NULL,
            recurrence TEXT,
            statut TEXT DEFAULT 'active',
            type_echeance TEXT DEFAULT 'prévue',
            description TEXT,
            date_creation TEXT,
            date_modification TEXT
        )
    """)

    # Migration : Ajouter la colonne type_echeance si elle n'existe pas
    try:
        cursor.execute("SELECT type_echeance FROM echeances LIMIT 1")
    except:
        cursor.execute("ALTER TABLE echeances ADD COLUMN type_echeance TEXT DEFAULT 'prévue'")
        conn.commit()

    conn.commit()

    # Normaliser la colonne recurrence pour la cohérence des données
    normalize_recurrence_column()

    # Backfill les transactions récurrentes jusqu'à aujourd'hui
    # IMPORTANT: Cela doit être fait AVANT de charger les transactions
    backfill_recurrences_to_today(DB_PATH)

    # Onglets principaux
    tab1, tab2, tab3, tab4 = st.tabs(["💰 Budgets par catégorie", "🎯 Objectifs", "📊 Vue d'ensemble", "📅 Prévisions"])

    # Route to tab functions
    with tab1:
        render_budgets_tab(conn, cursor)

    with tab2:
        render_objectives_tab(conn, cursor)

    with tab3:
        render_overview_tab(conn, cursor)

    with tab4:
        render_forecasts_tab(conn, cursor)

    conn.close()
