"""
Script pour normaliser toutes les catégories et sous-catégories en base de données.

Applique la normalisation Title Case à toutes les transactions existantes.
Cela élimine les variations de casse et assure la cohérence.

Usage:
    python scripts/normalize_categories.py

@author: djabi
@date: 2025-11-25
"""

import sqlite3
import sys
from pathlib import Path

# Ajouter le module parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.services.normalization import normalize_category, normalize_subcategory
from modules.database.connection import get_db_connection, close_connection

def normalize_all_categories():
    """Normalise toutes les catégories et sous-catégories en base de données."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # D'abord, récupérer tous les doublons potentiels (même nom, casse différente)
        print("\n[STEP 1] Identification des doublons...")
        cursor.execute("""
            SELECT LOWER(categorie) as lower_cat, COUNT(DISTINCT categorie) as count, GROUP_CONCAT(DISTINCT categorie) as variants
            FROM transactions
            GROUP BY LOWER(categorie)
            HAVING COUNT(DISTINCT categorie) > 1
        """)

        category_duplicates = cursor.fetchall()
        total_updated = 0
        updated_categories = set()
        updated_subcategories = set()

        # Fixer les doublons de catégories
        if category_duplicates:
            print(f"   Found {len(category_duplicates)} category duplicates")
            for lower_cat, count, variants in category_duplicates:
                variant_list = variants.split(',')
                # Prendre la version normalisée (Title Case)
                normalized = normalize_category(variant_list[0])
                print(f"   [{count} variants] {variants} -> {normalized}")

                for variant in variant_list:
                    if variant != normalized:
                        cursor.execute("""
                            UPDATE transactions
                            SET categorie = ?
                            WHERE categorie = ?
                        """, (normalized, variant))
                        rows_affected = cursor.rowcount
                        total_updated += rows_affected
                        updated_categories.add(f"{variant} -> {normalized} ({rows_affected} rows)")
        else:
            print("   No category duplicates found")

        # Idem pour les sous-catégories
        print("[STEP 2] Normalisation des sous-categories...")
        cursor.execute("""
            SELECT LOWER(sous_categorie) as lower_subcat, COUNT(DISTINCT sous_categorie) as count, GROUP_CONCAT(DISTINCT sous_categorie) as variants
            FROM transactions
            GROUP BY LOWER(sous_categorie)
            HAVING COUNT(DISTINCT sous_categorie) > 1
        """)

        subcategory_duplicates = cursor.fetchall()

        if subcategory_duplicates:
            print(f"   Found {len(subcategory_duplicates)} subcategory duplicates")
            for lower_subcat, count, variants in subcategory_duplicates:
                variant_list = variants.split(',')
                # Prendre la version normalisée (Title Case)
                normalized = normalize_subcategory(variant_list[0])
                print(f"   [{count} variants] {variants} -> {normalized}")

                for variant in variant_list:
                    if variant != normalized:
                        cursor.execute("""
                            UPDATE transactions
                            SET sous_categorie = ?
                            WHERE sous_categorie = ?
                        """, (normalized, variant))
                        rows_affected = cursor.rowcount
                        total_updated += rows_affected
                        updated_subcategories.add(f"{variant} -> {normalized} ({rows_affected} rows)")
        else:
            print("   No subcategory duplicates found")

        conn.commit()

        # Afficher résumé
        print(f"\n[OK] Normalisation complétée!")
        print(f"   Total transactions mises à jour: {total_updated}")
        print(f"\n[CATEGORIES] Catégories normalisées:")
        for change in sorted(updated_categories):
            print(f"   {change}")

        print(f"\n[SUBCATEGORIES] Sous-catégories normalisées:")
        for change in sorted(updated_subcategories):
            print(f"   {change}")

        # Vérifier pour les vrais doublons (variantes de casse)
        cursor.execute("""
            SELECT LOWER(categorie) as lower_cat, COUNT(DISTINCT categorie) as variants
            FROM transactions
            GROUP BY LOWER(categorie)
            HAVING COUNT(DISTINCT categorie) > 1
        """)

        duplicates = cursor.fetchall()
        if duplicates:
            print(f"\n[WARNING] Vrais doublons détectés (même catégorie, casses différentes):")
            for cat, count in duplicates:
                print(f"   '{cat}' ({count} variantes)")
        else:
            print(f"\n[SUCCESS] Aucun vrai doublon détecté - base de données normalisée!")

        return total_updated

    except sqlite3.Error as e:
        print(f"❌ Erreur: {e}")
        if conn:
            conn.rollback()
        return 0
    finally:
        close_connection(conn)

if __name__ == "__main__":
    print("[STARTING] Normalisation des catégories et sous-catégories...")
    normalize_all_categories()
