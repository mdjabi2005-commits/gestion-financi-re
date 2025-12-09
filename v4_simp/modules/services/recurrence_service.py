"""Recurrence management service for recurring transactions.

Ce module gère la génération automatique des transactions récurrentes
à partir de la table recurrences (nouveau système).
"""

import sqlite3
import logging
from datetime import date
from typing import Optional

from config import DB_PATH
from modules.services.recurrence_generation import backfill_all_recurrences

logger = logging.getLogger(__name__)


def get_db_connection() -> sqlite3.Connection:
    """
    Get a SQLite database connection with proper configuration.

    Returns:
        SQLite connection object with foreign keys enabled

    Raises:
        sqlite3.Error: If database connection fails
    """
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30.0)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA busy_timeout = 30000")
        return conn
    except sqlite3.Error as e:
        logger.error(f"Database connection failed: {e}")
        raise
        raise


def backfill_recurrences_to_today(db_path: Optional[str] = None) -> None:
    """
    Génère automatiquement toutes les transactions récurrentes jusqu'à aujourd'hui.
    
    Utilise la nouvelle table recurrences et génère des transactions avec
    source='recurrence_auto'.
    
    Args:
        db_path: Chemin optionnel de la base de données

    Returns:
        None

    Side effects:
        - Insère de nouveaux enregistrements de transactions
        - Logs toutes les transactions insérées
    """
    if db_path is None:
        db_path = DB_PATH

    # Utiliser la nouvelle fonction backfill
    count = backfill_all_recurrences()
    logger.info(f"Recurrence backfill completed: {count} transactions created")
