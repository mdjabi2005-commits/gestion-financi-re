# -*- coding: utf-8 -*-
"""
Script de migration et nettoyage des recurrences

Ce script resout les problemes de doublons causes par la migration
en nettoyant les transactions en double et en migrant proprement vers
le nouveau schema.
"""

import sqlite3
import sys
import os
from datetime import date

# Force UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DB_PATH

def clean_duplicate_recurrent_transactions():
    """
    Nettoie les transactions récurrentes en double.
    
    Stratégie:
    - Pour chaque (catégorie, sous_catégorie, date), garder UNE SEULE transaction
    - Priorité: 'récurrente' (manuelle) > 'récurrente_auto' (auto-générée)
    - Si montants différents, on garde la première trouvée
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("=" * 70)
    print("NETTOYAGE DES DOUBLONS DE TRANSACTIONS RECURRENTES")
    print("=" * 70)
    
    # 1. Identifier tous les doublons
    print("\n[INFO] Identification des doublons...")
    duplicates = cursor.execute("""
        SELECT categorie, sous_categorie, date, COUNT(*) as cnt
        FROM transactions
        WHERE source IN ('récurrente', 'récurrente_auto')
        GROUP BY categorie, sous_categorie, date
        HAVING cnt > 1
    """).fetchall()
    
    if not duplicates:
        print("[OK] Aucun doublon trouve !")
        conn.close()
        return 0
    
    print(f"[!] {len(duplicates)} groupe(s) de doublons trouves")
    
    deleted_count = 0
    
    for cat, sous_cat, trans_date, count in duplicates:
        # Récupérer toutes les transactions de ce groupe
        transactions = cursor.execute("""
            SELECT id, montant, source, description
            FROM transactions
            WHERE categorie = ? AND sous_categorie = ? AND date = ?
              AND source IN ('récurrente', 'récurrente_auto')
            ORDER BY 
                CASE WHEN source = 'récurrente' THEN 0 ELSE 1 END,  -- Priorité aux manuelles
                id ASC  -- Puis par ordre d'insertion
        """, (cat, sous_cat or '', trans_date)).fetchall()
        
        if len(transactions) <= 1:
            continue
        
        # Garder la première (priorité manuelle), supprimer les autres
        to_keep = transactions[0]
        to_delete = transactions[1:]
        
        sous_display = f" > {sous_cat}" if sous_cat else ""
        print(f"\n   [DATE] {trans_date} | {cat}{sous_display}")
        print(f"      [KEEP] Conservation: ID={to_keep[0]}, source={to_keep[2]}, montant={to_keep[1]}")
        
        for trans in to_delete:
            trans_id, montant, source, desc = trans
            cursor.execute("DELETE FROM transactions WHERE id = ?", (trans_id,))
            deleted_count += 1
            print(f"      [DEL] Suppression: ID={trans_id}, source={source}, montant={montant}")
    
    conn.commit()
    
    print(f"\n" + "=" * 70)
    print(f"[OK] NETTOYAGE TERMINE: {deleted_count} transaction(s) en double supprimee(s)")
    print("=" * 70)
    
    conn.close()
    return deleted_count


def ensure_recurrences_table_populated():
    """
    S'assure que la table recurrences contient les définitions
    pour toutes les transactions récurrentes existantes.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("\n" + "=" * 70)
    print("VERIFICATION DE LA TABLE RECURRENCES")
    print("=" * 70)
    
    # Vérifier que la table existe
    table_exists = cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='recurrences'
    """).fetchone()
    
    if not table_exists:
        print("[!] La table recurrences n'existe pas encore")
        print("   Veuillez d'abord executer create_recurrences_table.py")
        conn.close()
        return False
    
    # Trouver les catégories récurrentes sans définition
    orphans = cursor.execute("""
        SELECT DISTINCT 
            t.type,
            t.categorie, 
            t.sous_categorie,
            t.montant,
            MIN(t.date) as premiere_date
        FROM transactions t
        WHERE t.source IN ('récurrente', 'récurrente_auto')
        AND NOT EXISTS (
            SELECT 1 FROM recurrences r
            WHERE r.categorie = t.categorie
            AND (r.sous_categorie = t.sous_categorie OR (r.sous_categorie IS NULL AND t.sous_categorie = ''))
            AND r.statut = 'active'
        )
        GROUP BY t.type, t.categorie, t.sous_categorie, t.montant
    """).fetchall()
    
    if not orphans:
        print("[OK] Toutes les transactions recurrentes ont une definition")
        conn.close()
        return True
    
    print(f"\n[!] {len(orphans)} categorie(s) recurrente(s) sans definition trouvee(s)")
    print("\nCreation des definitions de recurrence manquantes...")
    
    created = 0
    for type_trans, cat, sous_cat, montant, premiere_date in orphans:
        sous_display = f" > {sous_cat}" if sous_cat else ""
        print(f"\n   [NEW] {cat}{sous_display}")
        print(f"      Type: {type_trans}, Montant: {montant}, Debut: {premiere_date}")
        
        # Demander la fréquence (par défaut: mensuelle)
        # En mode automatique, on suppose mensuelle
        frequence = 'mensuelle'
        
        try:
            cursor.execute("""
                INSERT INTO recurrences
                (type, categorie, sous_categorie, montant, date_debut, date_fin, 
                 frequence, description, statut, date_creation)
                VALUES (?, ?, ?, ?, ?, NULL, ?, ?, 'active', ?)
            """, (
                type_trans,
                cat,
                sous_cat or '',
                montant,
                premiere_date,
                frequence,
                f"Recurrence auto-creee lors de la migration",
                date.today().isoformat()
            ))
            created += 1
            print(f"      [OK] Recurrence creee (frequence: {frequence})")
        except Exception as e:
            print(f"      [ERR] Erreur: {e}")
    
    conn.commit()
    print(f"\n[OK] {created} definition(s) de recurrence creee(s)")
    
    conn.close()
    return True


def update_transaction_sources():
    """
    Met à jour les sources des transactions pour correspondre au nouveau schéma:
    - La première occurrence de chaque récurrence → source='récurrente'
    - Les occurrences suivantes → source='récurrente_auto'
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("\n" + "=" * 70)
    print("MISE A JOUR DES SOURCES DES TRANSACTIONS")
    print("=" * 70)
    
    # Pour chaque récurrence active
    recurrences = cursor.execute("""
        SELECT id, categorie, sous_categorie, date_debut
        FROM recurrences
        WHERE statut = 'active'
    """).fetchall()
    
    updated = 0
    
    for rec_id, cat, sous_cat, date_debut in recurrences:
        # Récupérer toutes les transactions de cette récurrence, triées par date
        transactions = cursor.execute("""
            SELECT id, date
            FROM transactions
            WHERE categorie = ? 
              AND sous_categorie = ?
              AND source IN ('récurrente', 'récurrente_auto', 'manuelle')
            ORDER BY date ASC
        """, (cat, sous_cat or '')).fetchall()
        
        if not transactions:
            continue
        
        # La première transaction → source='récurrente'
        first_id = transactions[0][0]
        cursor.execute("""
            UPDATE transactions
            SET source = 'récurrente'
            WHERE id = ?
        """, (first_id,))
        
        # Les suivantes → source='récurrente_auto'
        for trans_id, trans_date in transactions[1:]:
            cursor.execute("""
                UPDATE transactions
                SET source = 'récurrente_auto'
                WHERE id = ?
            """, (trans_id,))
            updated += 1
    
    conn.commit()
    
    print(f"[OK] {updated} transaction(s) mise(s) a jour vers 'recurrente_auto'")
    
    conn.close()
    return updated


def main():
    """Exécution complète de la migration"""
    print("\n" + "=" * 70)
    print("MIGRATION COMPLETE DES RECURRENCES")
    print("=" * 70)
    
    print("\n[!] ATTENTION: Cette operation va modifier votre base de donnees")
    print("   Il est recommande de faire une sauvegarde avant de continuer")
    print("\n   Appuyez sur Entrée pour continuer ou Ctrl+C pour annuler...")
    
    try:
        input()
    except KeyboardInterrupt:
        print("\n\n[CANCEL] Migration annulee par l'utilisateur")
        return
    
    # Étape 1: Nettoyer les doublons
    deleted = clean_duplicate_recurrent_transactions()
    
    # Etape 2: Verifier/creer les definitions de recurrence
    if not ensure_recurrences_table_populated():
        print("\n[ERR] Migration interrompue")
        return
    
    # Etape 3: Mettre a jour les sources
    update_transaction_sources()
    
    print("\n" + "=" * 70)
    print("MIGRATION TERMINEE AVEC SUCCES !")
    print("=" * 70)
    print("\n[OK] Votre base de donnees est maintenant compatible avec le nouveau schema")
    print("[OK] Les doublons ont ete supprimes")
    print("[OK] Les sources sont correctement definies")
    print("\n[INFO] Vous pouvez maintenant relancer l'application")


if __name__ == "__main__":
    main()
