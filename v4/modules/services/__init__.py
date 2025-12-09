"""Business logic services for financial management.

This package contains service modules that encapsulate business logic for:
- Revenue processing (Uber tax calculations)
- Recurrence management (recurring transactions)
- File operations (managing transaction-associated files)
"""

from modules.services.revenue_service import (
    is_uber_transaction,
    apply_uber_tax,
    process_uber_revenue,
)
from modules.services.recurrence_service import (
    backfill_recurrences_to_today,
    get_db_connection,
)
from modules.services.recurrence_generation import (
    refresh_echeances,
    sync_recurrences_to_echeances,
    cleanup_past_echeances,
)
from modules.services.file_service import (
    trouver_fichiers_associes,
    supprimer_fichiers_associes,
    deplacer_fichiers_associes,
)

__all__ = [
    # Revenue service
    "is_uber_transaction",
    "apply_uber_tax",
    "process_uber_revenue",
    # Recurrence service
    "backfill_recurrences_to_today",
    "get_db_connection",
    "refresh_echeances",
    "sync_recurrences_to_echeances",
    "cleanup_past_echeances",
    # File service
    "trouver_fichiers_associes",
    "supprimer_fichiers_associes",
    "deplacer_fichiers_associes",
]
