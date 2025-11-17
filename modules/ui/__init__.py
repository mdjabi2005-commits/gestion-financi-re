"""UI components and helpers for the financial management application.

This module provides reusable UI components including:
- Toast notifications (success, warning, error)
- Badge rendering for transaction sources
- Transaction card displays
- Data loading utilities
- CSS style loaders
"""

from .components import (
    show_toast,
    toast_success,
    toast_warning,
    toast_error,
    get_badge_html,
    get_badge_icon,
    afficher_carte_transaction,
    afficher_documents_associes,
)

from .helpers import (
    load_transactions,
    load_recurrent_transactions,
    refresh_and_rerun,
    insert_transaction_batch,
)

from .styles import load_css

__all__ = [
    # Toast notifications
    'show_toast',
    'toast_success',
    'toast_warning',
    'toast_error',
    # Badges
    'get_badge_html',
    'get_badge_icon',
    # Transaction display
    'afficher_carte_transaction',
    'afficher_documents_associes',
    # Data loading
    'load_transactions',
    'load_recurrent_transactions',
    'refresh_and_rerun',
    'insert_transaction_batch',
    # Styles
    'load_css',
]
