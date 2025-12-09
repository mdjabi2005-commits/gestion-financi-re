"""
Script de migration pour renommer tous les fichiers existants avec l'ID de transaction.

Ce script:
1. Charge toutes les transactions de la base de données
2. Trouve les fichiers associés à chaque transaction
3. Renomme les fichiers au format: {transaction_id}_1.ext, {transaction_id}_2.ext, etc.
4. Gère les cas où plusieurs fichiers sont associés à une transaction
5. Log toutes les opérations et erreurs

Usage:
    python scripts/migrate_files_to_id.py [--dry-run]
"""

import os
import sys
import logging
import sqlite3
from pathlib import Path
from typing import List, Dict, Any

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DB_PATH, SORTED_DIR, REVENUS_TRAITES
from modules.database.connection import get_db_connection
from modules.services.file_service import trouver_fichiers_associes

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration_files_to_id.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def renommer_fichiers_transaction(transaction: Dict[str, Any], dry_run: bool = False) -> int:
    """
    Renomme tous les fichiers associés à une transaction avec son ID.
    
    Format: {id}.extension (un seul fichier par transaction attendu)
    
    Args:
        transaction: Dictionnaire de la transaction avec 'id', 'categorie', 'sous_categorie', etc.
        dry_run: Si True, affiche les opérations sans les exécuter
        
    Returns:
        Nombre de fichiers renommés
    """
    transaction_id = transaction['id']
    fichiers = trouver_fichiers_associes(transaction)
    
    if not fichiers:
        return 0
    
    # ALERTE : Plus d'un fichier trouvé pour une transaction
    if len(fichiers) > 1:
        logger.warning(f"⚠️  Transaction #{transaction_id}: {len(fichiers)} fichiers trouvés (attendu: 1)")
    
    nb_renommes = 0
    
    for fichier_path in fichiers:
        try:
            # Extraire l'extension du fichier
            _, extension = os.path.splitext(fichier_path)
            
            # Construire le nouveau nom: {id}.ext (un seul fichier par transaction)
            dossier = os.path.dirname(fichier_path)
            nouveau_nom = f"{transaction_id}{extension}"
            nouveau_chemin = os.path.join(dossier, nouveau_nom)
            
            # Vérifier si le fichier existe déjà
            if os.path.exists(nouveau_chemin) and fichier_path != nouveau_chemin:
                logger.error(f"❌ CONFLIT: Le fichier cible existe déjà: {nouveau_chemin}")
                logger.error(f"   Fichier actuel: {fichier_path}")
                logger.error(f"   → Transaction #{transaction_id} a probablement plusieurs fichiers!")
                # Ajouter un suffixe pour éviter l'écrasement
                base_nom = f"{transaction_id}_duplicate"
                nouveau_nom = f"{base_nom}{extension}"
                nouveau_chemin = os.path.join(dossier, nouveau_nom)
            
            if fichier_path == nouveau_chemin:
                logger.debug(f"Fichier déjà nommé correctement: {fichier_path}")
                continue
            
            if dry_run:
                logger.info(f"[DRY-RUN] Renommer: {os.path.basename(fichier_path)} -> {nouveau_nom}")
            else:
                os.rename(fichier_path, nouveau_chemin)
                logger.info(f"✅ Renommé: {os.path.basename(fichier_path)} -> {nouveau_nom}")
            
            nb_renommes += 1
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du renommage de {fichier_path}: {e}")
    
    return nb_renommes


def main(dry_run: bool = False):
    """
    Fonction principale de migration.
    
    Args:
        dry_run: Si True, simule les opérations sans les exécuter
    """
    logger.info("=" * 80)
    logger.info("DÉBUT DE LA MIGRATION DES FICHIERS VERS LE SYSTÈME D'ID")
    logger.info("=" * 80)
    
    if dry_run:
        logger.info("🔍 MODE DRY-RUN: Aucun fichier ne sera modifié")
    
    # Connexion à la base de données
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Récupérer toutes les transactions
        cursor.execute("""
            SELECT id, type, categorie, sous_categorie, description, 
                   montant, date, source
            FROM transactions
            ORDER BY id
        """)
        
        transactions = cursor.fetchall()
        total_transactions = len(transactions)
        
        logger.info(f"📊 {total_transactions} transactions trouvées dans la base de données")
        logger.info("-" * 80)
        
        total_fichiers_renommes = 0
        transactions_avec_fichiers = 0
        
        for row in transactions:
            transaction = {
                'id': row[0],
                'type': row[1],
                'categorie': row[2],
                'sous_categorie': row[3],
                'description': row[4],
                'montant': row[5],
                'date': row[6],
                'source': row[7]
            }
            
            nb_renommes = renommer_fichiers_transaction(transaction, dry_run)
            
            if nb_renommes > 0:
                transactions_avec_fichiers += 1
                total_fichiers_renommes += nb_renommes
                logger.info(f"  Transaction #{transaction['id']}: {nb_renommes} fichier(s) renommé(s)")
        
        logger.info("-" * 80)
        logger.info("=" * 80)
        logger.info("RÉSUMÉ DE LA MIGRATION")
        logger.info("=" * 80)
        logger.info(f"✅ Transactions analysées: {total_transactions}")
        logger.info(f"✅ Transactions avec fichiers: {transactions_avec_fichiers}")
        logger.info(f"✅ Total fichiers renommés: {total_fichiers_renommes}")
        
        if dry_run:
            logger.info("\n⚠️  MODE DRY-RUN: Pour effectuer la migration réelle, exécutez sans --dry-run")
        else:
            logger.info("\n✅ MIGRATION TERMINÉE AVEC SUCCÈS!")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"❌ Erreur fatale lors de la migration: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    # Vérifier les arguments
    dry_run_mode = "--dry-run" in sys.argv
    
    if dry_run_mode:
        print("\n🔍 MODE DRY-RUN ACTIVÉ")
        print("Les opérations seront simulées sans modifier les fichiers.\n")
    
    try:
        main(dry_run=dry_run_mode)
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Migration interrompue par l'utilisateur")
        sys.exit(1)
