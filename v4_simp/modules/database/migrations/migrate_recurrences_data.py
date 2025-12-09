"""
Migration script - Migrate existing recurrence data to new schema

This script migrates data from écheances (where type_echeance='récurrente')
to the new recurrences table.
"""

import sqlite3
from config import DB_PATH
from modules.database.connection import get_db_connection


def migrate_recurrences_data():
    """Migrer les données de récurrences existantes"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("🔄 Début de la migration des récurrences...")
    
    # Récupérer les récurrences existantes dans echeances
    old_recurrences = cursor.execute("""
        SELECT type, categorie, sous_categorie, montant, date_echeance, 
               recurrence, description, statut, date_creation, date_modification
        FROM echeances
        WHERE type_echeance = 'récurrente'
    """).fetchall()
    
    if not old_recurrences:
        print("✅ Aucune donnée à migrer")
        conn.close()
        return
    
    print(f"📦 {len(old_recurrences)} récurrence(s) à migrer")
    
    # Insérer dans la nouvelle table
    migrated = 0
    for rec in old_recurrences:
        try:
            cursor.execute("""
                INSERT INTO recurrences
                (type, categorie, sous_categorie, montant, date_debut, date_fin, 
                 frequence, description, statut, date_creation, date_modification)
                VALUES (?, ?, ?, ?, ?, NULL, ?, ?, ?, ?, ?)
            """, (
                rec[0],  # type
                rec[1],  # categorie
                rec[2],  # sous_categorie
                rec[3],  # montant
                rec[4],  # date_echeance -> date_debut
                rec[5],  # recurrence -> frequence
                rec[6],  # description
                rec[7],  # statut
                rec[8],  # date_creation
                rec[9]   # date_modification
            ))
            migrated += 1
        except Exception as e:
            print(f"⚠️ Erreur lors de la migration d'une récurrence: {e}")
    
    # Supprimer les anciennes entrées
    cursor.execute("""
        DELETE FROM echeances
        WHERE type_echeance = 'récurrente'
    """)
    
    conn.commit()
    print(f"✅ Migration terminée: {migrated} récurrence(s) migrée(s)")
    print(f"🗑️ Anciennes données nettoyées")
    
    conn.close()


if __name__ == "__main__":
    migrate_recurrences_data()
