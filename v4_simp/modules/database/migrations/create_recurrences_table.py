"""
Database schema migration - Add recurrences table

Table pour stocker les transactions récurrentes.
Les occurrences générées auront source='récurrente' dans la table transactions.
"""

import sqlite3
from config import DB_PATH
from modules.database.connection import get_db_connection


def create_recurrences_table():
    """Créer la table recurrences si elle n'existe pas"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recurrences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            categorie TEXT NOT NULL,
            sous_categorie TEXT,
            montant REAL NOT NULL,
            date_debut TEXT NOT NULL,
            date_fin TEXT,
            frequence TEXT NOT NULL,
            description TEXT,
            statut TEXT DEFAULT 'active',
            date_creation TEXT,
            date_modification TEXT
        )
    """)
    
    conn.commit()
    conn.close()
    print("✅ Table recurrences créée avec succès")


if __name__ == "__main__":
    create_recurrences_table()
