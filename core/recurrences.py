# -*- coding: utf-8 -*-
"""
Module recurrences - Partie de l'application gestiov4
Généré automatiquement par migrate_to_modular.py
"""

import sqlite3
import pandas as pd
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from config import DB_PATH
from core.database import get_db_connection


def backfill_recurrences_to_today(db_path):
    """
    Pour chaque modèle 'récurrente', génère toutes les occurrences manquantes
    (source='récurrente_auto') jusqu'à aujourd'hui (ou date_fin si elle existe).
    """
    today = date.today()

    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

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
        limit = min(today, end_limit) if end_limit else today

        if start > limit:
            continue

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

        to_insert = []
        while next_d <= limit:
            to_insert.append((
                m["type"], cat, sous, float(m["montant"]), next_d.isoformat(),
                "récurrente_auto", rec, m["date_fin"]
            ))
            next_d = _inc(next_d, rec)

        if to_insert:
            cur.executemany("""
                INSERT INTO transactions (type, categorie, sous_categorie, montant, date, source, recurrence, date_fin)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, to_insert)

    conn.commit()
    conn.close()


def normalize_recurrence_column():
    """
    Normalise la colonne recurrence en remplaçant 'ponctuelle' par NULL.
    Cela assure la cohérence avec la nouvelle approche où les transactions
    uniques ont une recurrence vide/NULL au lieu de 'ponctuelle'.
    """
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


def _inc(d, recurrence):
    if recurrence == "hebdomadaire":
        return d + relativedelta(weeks=1)
    if recurrence == "mensuelle":
        return d + relativedelta(months=1)
    if recurrence == "annuelle":
        return d + relativedelta(years=1)
    return d


