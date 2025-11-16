# -*- coding: utf-8 -*-
"""
Module database - Partie de l'application gestiov4
Généré automatiquement par migrate_to_modular.py
"""

import sqlite3
import logger
from config import DB_PATH
from ui.component import toast_error


def get_db_connection():
    """Retourne une connexion SQLite cohérente avec DB_PATH."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON")  #Bloquer les clès étrangères
        return conn
    except sqlite3.Error as e:
        logger.error(f"Database connection failed: {e}")
        toast_error("Erreur de connexion à la base de données")
        raise


def init_db():
    """Initialise ou met à jour la base de données SQLite avec la table 'transactions'."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Créer la table avec le bon schéma
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            categorie TEXT,
            sous_categorie TEXT,
            description TEXT,
            montant REAL,
            date TEXT,
            source TEXT,
            recurrence TEXT,
            date_fin TEXT
        )
    """)
    
    # 🔄 Mettre à jour la table si elle existe avec l'ancien schéma
    try:
        cursor.execute("ALTER TABLE transactions ADD COLUMN source TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass  # La colonne existe déjà
    
    try:
        cursor.execute("ALTER TABLE transactions ADD COLUMN recurrence TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute("ALTER TABLE transactions ADD COLUMN date_fin TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass
    
    conn.commit()
    conn.close()


def migrate_database_schema():
    """Migre le schéma de la base de données vers les nouveaux noms de colonnes"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Vérifier si la table existe avec l'ancien schéma
        cursor.execute("PRAGMA table_info(transactions)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Si les anciennes colonnes existent, on migre
        if "Catégorie" in columns or "Sous-catégorie" in columns:
            logger.info("Migration du schema de la base de donnees...")
            
            # Créer une nouvelle table avec le bon schéma
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT,
                    categorie TEXT,
                    sous_categorie TEXT,
                    description TEXT,
                    montant REAL,
                    date TEXT,
                    source TEXT,
                    recurrence TEXT,
                    date_fin TEXT
                )
            """)
            
            # Copier les données en mappant les anciens noms vers les nouveaux
            cursor.execute("""
                INSERT INTO transactions_new 
                (id, type, categorie, sous_categorie, description, montant, date, source, recurrence, date_fin)
                SELECT 
                id, 
                type, 
                "Catégorie" AS categorie, 
                "Sous-catégorie" AS sous_categorie, 
                description, 
                montant, 
                "Date" AS date, 
                "Source" AS source, 
                "Récurrence" AS recurrence, 
                date_fin
                FROM transactions
            """)
            
            # Supprimer l'ancienne table
            cursor.execute("DROP TABLE transactions")
            
            # Renommer la nouvelle table
            cursor.execute("ALTER TABLE transactions_new RENAME TO transactions")

            logger.info("Migration terminee avec succes!")
        else:
            logger.info("Le schema est deja a jour")
            
    except Exception as e:
        logger.error(f"Erreur lors de la migration: {e}")
    finally:
        conn.commit()
        conn.close()

# Appeler la migration au démarrage


