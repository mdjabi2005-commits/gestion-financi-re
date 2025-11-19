"""Recurrence management service for recurring transactions.

This module handles automatic generation of recurring transactions
(weekly, monthly, yearly) and backfilling them to the current date.
"""

import sqlite3
import logging
from datetime import date
from dateutil.relativedelta import relativedelta
from typing import Optional

from config import DB_PATH

logger = logging.getLogger(__name__)


def _inc(d: date, recurrence: str) -> date:
    """
    Increment a date based on the recurrence type.

    Args:
        d: Starting date
        recurrence: Recurrence type ('hebdomadaire', 'mensuelle', 'annuelle')

    Returns:
        Incremented date

    Example:
        >>> from datetime import date
        >>> d = date(2025, 1, 15)
        >>> _inc(d, 'mensuelle')
        datetime.date(2025, 2, 15)
        >>> _inc(d, 'hebdomadaire')
        datetime.date(2025, 1, 22)
    """
    if recurrence == "hebdomadaire":
        return d + relativedelta(weeks=1)
    if recurrence == "mensuelle":
        return d + relativedelta(months=1)
    if recurrence == "annuelle":
        return d + relativedelta(years=1)
    return d


def get_db_connection() -> sqlite3.Connection:
    """
    Get a SQLite database connection with proper configuration.

    Returns:
        SQLite connection object with foreign keys enabled

    Raises:
        sqlite3.Error: If database connection fails
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    except sqlite3.Error as e:
        logger.error(f"Database connection failed: {e}")
        raise


def backfill_recurrences_to_today(db_path: Optional[str] = None) -> None:
    """
    Automatically generate all recurring transactions up to today.

    Scans all transactions marked as 'récurrente' (recurring model) and
    generates new transactions of type 'récurrente_auto' for all dates
    between the last generated date and today, respecting end dates.

    The function:
    - Finds all recurring transaction models
    - Determines the last generated date for each recurrence
    - Generates missing transactions in batches
    - Respects end dates (date_fin)
    - Handles weekly, monthly, and yearly recurrences

    Args:
        db_path: Optional database path (defaults to config DB_PATH)

    Returns:
        None

    Side effects:
        - Inserts new transaction records into the database
        - Logs all inserted transactions

    Example:
        >>> backfill_recurrences_to_today()
        # This will generate all recurring transactions up to today
    """
    if db_path is None:
        db_path = DB_PATH

    today = date.today()

    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Fetch all recurring transaction models
    cur.execute("""
       SELECT id, type, categorie, sous_categorie, montant, date, source, recurrence, date_fin
       FROM transactions
       WHERE source='récurrente'
    """)
    models = cur.fetchall()

    for m in models:
        cat = (m["categorie"] or "").strip()
        sous = (m["sous_categorie"] or "").strip()
        rec = (m["recurrence"] or "").strip()
        if not rec:
            continue

        try:
            start = date.fromisoformat(m["date"])
        except Exception:
            continue

        end_limit = None
        if m["date_fin"]:
            try:
                end_limit = date.fromisoformat(m["date_fin"])
            except Exception:
                end_limit = None

        # Use the earlier of today or end_limit
        limit = min(today, end_limit) if end_limit else today

        if start > limit:
            continue

        # Find the last generated date for this recurrence
        cur.execute("""
            SELECT MAX(date) as last_date
            FROM transactions
            WHERE source='récurrente_auto'
              AND categorie=? AND sous_categorie=?
              AND recurrence=?
              AND type=?
        """, (cat, sous, rec, m["type"]))
        row = cur.fetchone()
        last = date.fromisoformat(row["last_date"]) if row and row["last_date"] else None

        if last:
            next_d = _inc(last, rec)
        else:
            next_d = start

        # Build list of transactions to insert
        to_insert = []
        while next_d <= limit:
            to_insert.append((
                m["type"], cat, sous, float(m["montant"]), next_d.isoformat(),
                "récurrente_auto", rec, m["date_fin"]
            ))
            next_d = _inc(next_d, rec)

        # Batch insert all new recurring transactions
        if to_insert:
            cur.executemany("""
                INSERT INTO transactions (type, categorie, sous_categorie, montant, date, source, recurrence, date_fin)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, to_insert)
            logger.info(f"Inserted {len(to_insert)} recurring transactions for {cat}/{sous}")

    conn.commit()
    conn.close()
    logger.info("Recurrence backfill completed")
