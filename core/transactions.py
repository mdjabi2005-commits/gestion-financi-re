# -*- coding: utf-8 -*-
"""
Module transactions - Partie de l'application gestiov4
Généré automatiquement par migrate_to_modular.py
"""

import pandas as pd
import sqlite3
from datetime import datetime, date
from config import DB_PATH
from core.database import get_db_connection


def load_transactions(sort_by="date", ascending=False):
    """
    Charge toutes les transactions depuis la base SQLite avec tri et conversions sécurisées.
    
    Args:
        sort_by (str): Colonne de tri ('date' ou 'montant')
        ascending (bool): Ordre croissant (True) ou décroissant (False)
    
    Returns:
        pd.DataFrame: DataFrame trié avec conversions sécurisées appliquées
    """
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM transactions", conn)
    conn.close()
    
    if df.empty:
        return df
    
    # 🔥 CONVERSIONS SÉCURISÉES
    df["montant"] = df["montant"].apply(lambda x: safe_convert(x, float, 0.0))
    df["date"] = df["date"].apply(lambda x: safe_date_convert(x))
    
    # Conversion pour pandas
    df["date"] = pd.to_datetime(df["date"])
    
    # 🔥 TRI PAR DÉFAUT : Plus récent en premier
    df = df.sort_values(by=sort_by, ascending=ascending)
    
    return df


def load_recurrent_transactions():
    """
    Charge uniquement les transactions récurrentes automatiques avec conversions sécurisées.
    
    Returns:
        pd.DataFrame: DataFrame des récurrences trié par date (plus récent en premier)
    """
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM transactions WHERE source='récurrente_auto'", conn)
    conn.close()
    
    if df.empty:
        return df
    
    # 🔥 CONVERSIONS SÉCURISÉES
    df["montant"] = df["montant"].apply(lambda x: safe_convert(x, float, 0.0))
    df["date"] = df["date"].apply(lambda x: safe_date_convert(x))
    
    # Conversion pour pandas
    df["date"] = pd.to_datetime(df["date"])
    
    # Tri par date décroissante
    df = df.sort_values(by="date", ascending=False)
    
    return df


def insert_transaction_batch(transactions):
    """
    Insère plusieurs transactions dans la base SQLite.
    Évite les doublons basés sur (type, categorie, sous_categorie, montant, date).
    Version V2 avec validation et traitement Uber.
    """
    if not transactions:
        return
    conn = get_db_connection()
    cur = conn.cursor()

    inserted, skipped, uber_processed = 0, 0, 0
    uber_messages = []

    for t in transactions:
        try:
            # Validation des données
            errors = validate_transaction_data(t)
            if errors:
                logger.warning(f"Transaction validation failed: {errors}")
                skipped += 1
                continue

            # Nettoyage des données
            clean_t = {
                "type": str(t["type"]).strip().lower(),
                "categorie": str(t.get("categorie", "")).strip(),
                "sous_categorie": str(t.get("sous_categorie", "")).strip(),
                "description": str(t.get("description", "")).strip(),
                "montant": safe_convert(t["montant"]),
                "date": safe_date_convert(t["date"]).isoformat(),
                "source": str(t.get("source", "manuel")).strip(),
                "recurrence": str(t.get("recurrence", "")).strip(),
                "date_fin": safe_date_convert(t.get("date_fin")).isoformat() if t.get("date_fin") else ""
            }

            # Traitement Uber pour les revenus
            if clean_t["type"] == "revenu":
                clean_t, uber_msg = process_uber_revenue(clean_t)
                if uber_msg:
                    uber_processed += 1
                    uber_messages.append(uber_msg)

            cur.execute("""
                SELECT COUNT(*) FROM transactions
                WHERE type = ? AND categorie = ? AND sous_categorie = ?
                      AND montant = ? AND date = ?
            """, (
                clean_t["type"],
                clean_t.get("categorie", ""),
                clean_t.get("sous_categorie", ""),
                float(clean_t["montant"]),
                clean_t["date"]
            ))

            if cur.fetchone()[0] > 0:
                skipped += 1
                continue

            cur.execute("""
                INSERT INTO transactions
                (type, categorie, sous_categorie, description, montant, date, source, recurrence, date_fin)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                clean_t["type"],
                clean_t.get("categorie", ""),
                clean_t.get("sous_categorie", ""),
                clean_t.get("description", ""),
                float(clean_t["montant"]),
                clean_t["date"],
                clean_t.get("source", "manuel"),
                clean_t.get("recurrence", ""),
                clean_t.get("date_fin", "")
            ))
            inserted += 1

        except Exception as e:
            logger.error(f"Erreur lors de l'insertion de {t}: {e}")

    conn.commit()
    conn.close()
    
    # Affichage des résultats
    if inserted > 0:
        toast_success("{inserted} transaction(s) insérée(s).")
        if uber_processed > 0:
            st.info(f"🚗 {uber_processed} revenu(s) Uber traité(s) avec application de la fiscalité (79%)")
            for msg in uber_messages:
                st.success(msg)
    if skipped > 0:
        st.info(f"ℹ️ {skipped} doublon(s) détecté(s) et ignoré(s).")


def validate_transaction_data(transaction):
    """
    Validation complète des données transaction
    """
    errors = []
    
    if transaction.get('type') not in ['revenu', 'dépense']:
        errors.append("Type must be 'revenu' or 'dépense'")
    
    if not transaction.get('categorie') or not str(transaction['categorie']).strip():
        errors.append("Catégorie is required")
    
    montant = safe_convert(transaction.get('montant', 0))
    if montant <= 0:
        errors.append("Montant must be positive")
    
    date_val = safe_date_convert(transaction.get('date'))
    if date_val > datetime.now().date():
        errors.append("Date cannot be in the future")
    
    return errors
#faire une fonction générique quip permet d'appliquer une taxe


