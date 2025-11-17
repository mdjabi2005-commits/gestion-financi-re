"""
Portfolio Page Module

This module contains the portfolio interface split into manageable sub-functions.
The original interface_portefeuille() was 1391 lines - now split into separate tab functions.

Structure:
- interface_portefeuille(): Main router creating tabs
- _tab_budgets_categories(): Budget management by category
- _tab_objectifs(): Financial goals management
- _tab_vue_ensemble(): Overview with charts and summaries
- _tab_previsions(): Forecasts and predictions
"""

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
from typing import Optional, Dict, Any

from config import DB_PATH, logger
from modules.database.connection import get_db_connection
from modules.ui.helpers import load_transactions, refresh_and_rerun
from modules.ui.components import toast_success, toast_error, toast_warning
from modules.services.recurrence_service import backfill_recurrences_to_today


def normalize_recurrence_column() -> None:
    """Normalize recurrence column by converting 'ponctuelle' to NULL."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Compter avant migration
        cursor.execute("SELECT COUNT(*) FROM transactions WHERE recurrence = 'ponctuelle'")
        count_before = cursor.fetchone()[0]

        if count_before > 0:
            # Remplacer 'ponctuelle' par NULL
            cursor.execute("UPDATE transactions SET recurrence = NULL WHERE recurrence = 'ponctuelle'")
            conn.commit()
            logger.info(f"✅ Normalisation recurrence: {count_before} transactions 'ponctuelle' converties à NULL")

        conn.close()
    except Exception as e:
        logger.warning(f"⚠️ Normalisation recurrence: {str(e)}")


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
        This is a refactored version of the original 1391-line monster function.
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
        _tab_budgets_categories(conn, cursor)

    with tab2:
        _tab_objectifs(conn, cursor)

    with tab3:
        _tab_vue_ensemble(conn, cursor)

    with tab4:
        _tab_previsions(conn, cursor)

    conn.close()


def _tab_budgets_categories(conn: sqlite3.Connection, cursor: sqlite3.Cursor) -> None:
    """
    Budget management by category tab.

    Features:
    - Add/modify budgets per category
    - Delete budgets
    - View current budgets
    - Period analysis
    - Budget vs actual comparison

    Args:
        conn: Database connection
        cursor: Database cursor

    Returns:
        None
    """
    st.subheader("💰 Gérer les budgets par catégorie")

    st.info("""
    **Tab 1: Budgets par catégorie**

    Cette section contient la gestion des budgets par catégorie.

    Fonctionnalités:
    - Ajouter/Modifier des budgets mensuels par catégorie
    - Supprimer des budgets
    - Visualiser les budgets actuels
    - Analyser les dépenses par rapport aux budgets
    - Sélection de période d'analyse

    📝 **Note:** Cette fonction est en cours de refactorisation depuis l'original (288 lignes).
    Pour l'instant, veuillez utiliser l'interface principale dans gestiov4.py.
    """)


def _tab_objectifs(conn: sqlite3.Connection, cursor: sqlite3.Cursor) -> None:
    """
    Financial goals management tab.

    Features:
    - Create financial goals (savings, debt reduction, etc.)
    - Track goal progress
    - Mark goals as completed
    - Delete goals

    Args:
        conn: Database connection
        cursor: Database cursor

    Returns:
        None
    """
    st.subheader("🎯 Objectifs Financiers")

    st.info("""
    **Tab 2: Objectifs Financiers**

    Gestion de vos objectifs financiers.

    Fonctionnalités:
    - Créer des objectifs d'épargne
    - Suivre la progression
    - Marquer comme atteints
    - Gérer les objectifs actifs et archivés

    📝 **Note:** Cette fonction est en cours de refactorisation depuis l'original (423 lignes).
    Pour l'instant, veuillez utiliser l'interface principale dans gestiov4.py.
    """)


def _tab_vue_ensemble(conn: sqlite3.Connection, cursor: sqlite3.Cursor) -> None:
    """
    Overview tab with charts and summaries.

    Features:
    - Financial summary metrics
    - Budget coverage analysis
    - Expense breakdown charts
    - Monthly evolution
    - Budget adherence tracking

    Args:
        conn: Database connection
        cursor: Database cursor

    Returns:
        None
    """
    st.subheader("📊 Vue d'Ensemble")

    st.info("""
    **Tab 3: Vue d'Ensemble**

    Vue synthétique de votre situation financière.

    Fonctionnalités:
    - Métriques financières principales
    - Analyse de couverture budgétaire
    - Graphiques de répartition
    - Évolution mensuelle
    - Respect des budgets

    📝 **Note:** Cette fonction est en cours de refactorisation depuis l'original (95 lignes).
    Pour l'instant, veuillez utiliser l'interface principale dans gestiov4.py.
    """)


def _tab_previsions(conn: sqlite3.Connection, cursor: sqlite3.Cursor) -> None:
    """
    Forecasts and predictions tab.

    Features:
    - Add upcoming expenses/revenues
    - Manage recurring forecasts
    - View upcoming due dates
    - Budget projections
    - Cash flow forecasting

    Args:
        conn: Database connection
        cursor: Database cursor

    Returns:
        None
    """
    st.subheader("📅 Prévisions & Échéances")

    st.info("""
    **Tab 4: Prévisions & Échéances**

    Gestion des prévisions et échéances futures.

    Fonctionnalités:
    - Ajouter des dépenses/revenus prévus
    - Gérer les échéances récurrentes
    - Visualiser le calendrier
    - Projections budgétaires
    - Prévision de trésorerie

    📝 **Note:** Cette fonction est en cours de refactorisation depuis l'original (585 lignes).
    Pour l'instant, veuillez utiliser l'interface principale dans gestiov4.py.
    """)


# Note: The original interface_portefeuille() was 1391 lines long!
# This refactored version provides a cleaner structure with separate functions for each tab.
# The full implementation of each tab is preserved in gestiov4.py until this refactoring is complete.
#
# Original line counts:
# - Tab 1 (Budgets): ~288 lines
# - Tab 2 (Objectifs): ~423 lines
# - Tab 3 (Vue d'ensemble): ~95 lines
# - Tab 4 (Prévisions): ~585 lines
# - Total: 1391 lines
#
# TODO: Complete the full implementation of each tab function by extracting the code
# from gestiov4.py lines 3868-5259
