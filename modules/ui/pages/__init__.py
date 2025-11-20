"""
UI Pages Module

This module exports all page interface functions for the financial management application.

Available Pages:
- home: Main dashboard with financial overview
- transactions: Transaction management (view, add, edit, delete)
- revenues: Revenue management and PDF scanning
- recurrences: Recurring transaction management
- portfolio: Portfolio management with budgets and goals
- scanning: Ticket scanning with OCR
- ocr_page: OCR analysis and diagnostics
"""

# Import all page functions
from .home import interface_accueil
from .transactions import (
    interface_transactions_simplifiee,
    interface_voir_transactions_v3,
    interface_ajouter_depenses_fusionnee
)
from .revenues import interface_process_all_revenues_in_folder
from .recurrences import (
    interface_transaction_recurrente,
    interface_gerer_recurrences
)
from .portfeuille import interface_portefeuille
from .scanning import process_all_tickets_in_folder
from .ocr_page import interface_ocr_analysis_complete
from .problematic_tickets import render_problematic_tickets_page

# Export all functions
__all__ = [
    # Home page
    'interface_accueil',

    # Transaction pages
    'interface_transactions_simplifiee',
    'interface_voir_transactions_v3',
    'interface_ajouter_depenses_fusionnee',

    # Revenue pages
    'interface_process_all_revenues_in_folder',

    # Recurrence pages
    'interface_transaction_recurrente',
    'interface_gerer_recurrences',

    # Portfolio page
    'interface_portefeuille',

    # Scanning page
    'process_all_tickets_in_folder',

    # OCR analysis page
    'interface_ocr_analysis_complete',

    # Problematic tickets page
    'render_problematic_tickets_page',
]
