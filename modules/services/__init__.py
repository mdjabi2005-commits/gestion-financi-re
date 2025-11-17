"""Business logic services for financial management.

This package contains service modules that encapsulate business logic for:
- Revenue processing (Uber tax calculations)
- Recurrence management (recurring transactions)
- File operations (managing transaction-associated files)
"""

from modules.services.revenue_service import (
    apply_uber_tax,
    process_uber_revenue,
)
from modules.services.recurrence_service import (
    backfill_recurrences_to_today,
    _inc,
    get_db_connection,
)
from modules.services.file_service import (
    trouver_fichiers_associes,
    supprimer_fichiers_associes,
    deplacer_fichiers_associes,
)

__all__ = [
    # Revenue service
    "apply_uber_tax",
    "process_uber_revenue",
    # Recurrence service
    "backfill_recurrences_to_today",
    "_inc",
    "get_db_connection",
    # File service
    "trouver_fichiers_associes",
    "supprimer_fichiers_associes",
    "deplacer_fichiers_associes",
]
