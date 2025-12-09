# -*- coding: utf-8 -*-
"""
Script de diagnostic pour les problemes de recurrences et doublons
"""

import sqlite3
import sys
import os

# Force UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DB_PATH

def diagnose_recurrences():
    """Diagnostic complet de la situation des récurrences"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("=" * 70)
    print("DIAGNOSTIC DES RECURRENCES")
    print("=" * 70)
    
    # 1. Verifier les sources dans transactions
    print("\n[1] SOURCES DANS LA TABLE TRANSACTIONS:")
    print("-" * 70)
    result = cursor.execute("""
        SELECT source, COUNT(*) as count
        FROM transactions
        GROUP BY source
        ORDER BY count DESC
    """).fetchall()
    
    for source, count in result:
        print(f"   {source or '(NULL)'}: {count} transactions")
    
    # 2. Recurrences actives
    print("\n[2] RECURRENCES DANS LA TABLE RECURRENCES:")
    print("-" * 70)
    result = cursor.execute("""
        SELECT statut, COUNT(*) as count
        FROM recurrences
        GROUP BY statut
    """).fetchall()
    
    if result:
        for statut, count in result:
            print(f"   {statut}: {count} recurrences")
    else:
        print("   [!] Aucune recurrence trouvee dans la table recurrences")
    
    # 3. Detection de doublons
    print("\n[3] DOUBLONS POTENTIELS (meme categorie + date):")
    print("-" * 70)
    result = cursor.execute("""
        SELECT categorie, date, source, COUNT(*) as cnt
        FROM transactions
        WHERE source IN ('récurrente', 'récurrente_auto')
        GROUP BY categorie, date
        HAVING cnt > 1
        ORDER BY date DESC
        LIMIT 20
    """).fetchall()
    
    if result:
        print(f"   [!] {len(result)} doublons trouves (premiers 20):")
        for cat, date, source, cnt in result:
            print(f"      - {date} | {cat} | source={source} | {cnt}x")
    else:
        print("   [OK] Aucun doublon detecte")
    
    # 4. Transactions recurrentes sans recurrence dans la table
    print("\n[4] TRANSACTIONS RECURRENTES SANS DEFINITION:")
    print("-" * 70)
    result = cursor.execute("""
        SELECT DISTINCT t.categorie, t.sous_categorie
        FROM transactions t
        WHERE t.source IN ('récurrente', 'récurrente_auto')
        AND NOT EXISTS (
            SELECT 1 FROM recurrences r
            WHERE r.categorie = t.categorie
            AND r.statut = 'active'
        )
        LIMIT 10
    """).fetchall()
    
    if result:
        print(f"   [!] {len(result)} categories trouvees sans definition de recurrence:")
        for cat, sous_cat in result:
            sous = f" > {sous_cat}" if sous_cat else ""
            print(f"      - {cat}{sous}")
    else:
        print("   [OK] Toutes les transactions recurrentes ont une definition")
    
    # 5. Statistiques detaillees sur les doublons
    print("\n[5] DETAIL DES DOUBLONS PAR CATEGORIE:")
    print("-" * 70)
    result = cursor.execute("""
        SELECT 
            categorie,
            COUNT(DISTINCT date) as dates_dupliquees,
            SUM(CASE WHEN source = 'récurrente' THEN 1 ELSE 0 END) as manuelles,
            SUM(CASE WHEN source = 'récurrente_auto' THEN 1 ELSE 0 END) as auto
        FROM transactions
        WHERE source IN ('récurrente', 'récurrente_auto')
        GROUP BY categorie
        HAVING COUNT(*) > (
            SELECT COUNT(DISTINCT date)
            FROM transactions t2
            WHERE t2.categorie = transactions.categorie
            AND t2.source IN ('récurrente', 'récurrente_auto')
        )
    """).fetchall()
    
    if result:
        print(f"   [!] Categories avec doublons:")
        for cat, dates, manuelles, auto in result:
            print(f"      - {cat}: {dates} dates dupliquees | {manuelles} manuelles | {auto} auto")
    else:
        print("   [OK] Aucune categorie avec doublons")
    
    conn.close()
    
    print("\n" + "=" * 70)
    print("FIN DU DIAGNOSTIC")
    print("=" * 70)


if __name__ == "__main__":
    diagnose_recurrences()
