# -*- coding: utf-8 -*-
"""
Application de Gestion Financière v4
Point d'entrée principal

Architecture modulaire :
- core/       : Logique métier (database, transactions, budget, recurrences)
- ocr/        : OCR et parsing de documents
- services/   : Services métier (file_manager, uber_tax)
- ui/         : Interface utilisateur (components, pages)
- utils/      : Utilitaires (converters, validators)
"""

import streamlit as st
from core.database import init_db, migrate_database_schema
from ui.pages import (
    accueil,
    transactions,
    portefeuille,
    scan_tickets,
    scan_revenus,
    recurrences,
    analytics,
    investissements,
)


# Configuration Streamlit
st.set_page_config(layout="wide", page_title="Gestion Financière v4")

st.markdown("""
    <style>
    div[data-testid="stDataFrame"] div[role="gridcell"] {
        font-size: 16px !important;
        padding: 8px !important;
    }
    </style>
""", unsafe_allow_html=True)


def main():
    """Point d'entrée principal de l'application."""

    # Initialiser la base de données
    init_db()
    migrate_database_schema()

    # Menu de navigation
    st.sidebar.title("🏦 Gestion Financière")

    menu = st.sidebar.radio(
        "Navigation",
        [
            "🏠 Accueil",
            "💸 Ajouter Dépense (Scan)",
            "💵 Ajouter Revenu",
            "📊 Voir Transactions",
            "🔄 Transactions Récurrentes",
            "💼 Portefeuille",
            "📈 Investissements",
            "🔍 Analyses OCR",
        ]
    )

    # Routage vers les pages
    if menu == "🏠 Accueil":
        accueil.interface_accueil()

    elif menu == "💸 Ajouter Dépense (Scan)":
        scan_tickets.interface_ajouter_depenses_fusionnee()

    elif menu == "💵 Ajouter Revenu":
        scan_revenus.interface_ajouter_revenu()

    elif menu == "📊 Voir Transactions":
        transactions.interface_transactions_unifiee()

    elif menu == "🔄 Transactions Récurrentes":
        recurrences.interface_gerer_recurrences()

    elif menu == "💼 Portefeuille":
        portefeuille.interface_portefeuille()

    elif menu == "📈 Investissements":
        investissements.interface_voir_investissements_alpha()

    elif menu == "🔍 Analyses OCR":
        analytics.interface_ocr_analysis_complete()


if __name__ == "__main__":
    main()
