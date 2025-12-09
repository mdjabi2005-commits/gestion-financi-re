"""
UI Pages Module

This module exports all page interface functions for the financial management application.

Available Pages:
- home: Main dashboard with financial overview
- transactions: Transaction management (view, add, edit)
- revenues: Revenue management and PDF scanning
- portfolio: Portfolio management with budgets and goals (includes recurrences)
- scanning: Ticket scanning with OCR
- ocr_page: OCR analysis and diagnostics
- problematic_tickets: Problematic tickets management
"""

# Import all page functions
from .home import interface_accueil
from .transactions import interface_transactions_simplifiee, interface_voir_transactions
from .revenues import interface_process_all_revenues_in_folder
from .portefeuille import interface_portefeuille
from .scanning import process_all_tickets_in_folder
from .ocr_page import interface_ocr_analysis_complete
from .problematic_tickets import render_problematic_tickets_page
from .dynamic_tree import interface_arbre_financier_dynamique

# Export all functions
__all__ = [
    # Home page
    'interface_accueil',

    # Transaction pages
    'interface_transactions_simplifiee',
    'interface_voir_transactions',

    # Revenue pages
    'interface_process_all_revenues_in_folder',

    # Portfolio page (includes recurrence management)
    'interface_portefeuille',

    # Scanning page
    'process_all_tickets_in_folder',

    # OCR analysis page
    'interface_ocr_analysis_complete',

    # Problematic tickets page
    'render_problematic_tickets_page',
    
    # Dynamic tree page
    'interface_arbre_financier_dynamique',
]
