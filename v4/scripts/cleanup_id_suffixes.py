"""
Script pour nettoyer les fichiers renommés avec le suffixe _1, _2, etc.
et les renommer au format simple {id}.extension

Usage:
    python scripts/cleanup_id_suffixes.py [--dry-run]
"""

import os
import sys
import logging
from pathlib import Path
import re

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import SORTED_DIR, REVENUS_TRAITES

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cleanup_id_suffixes.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def cleanup_id_suffixes(base_dir: str, dry_run: bool = False) -> int:
    """
    Nettoie les suffixes _1, _2, etc. des fichiers nommés avec des IDs.
    
    Renomme {id}_1.ext en {id}.ext
    
    Args:
        base_dir: Répertoire de base à parcourir
        dry_run: Si True, simule sans modifier
        
    Returns:
        Nombre de fichiers renommés
    """
    nb_renommes = 0
    conflits = 0
    
    # Pattern pour détecter les fichiers avec suffixe: {id}_{index}.{ext}
    pattern = re.compile(r'^(\d+)_(\d+)(\.\w+)$')
    
    for root, dirs, files in os.walk(base_dir):
        for fichier in files:
            match = pattern.match(fichier)
            
            if match:
                transaction_id = match.group(1)
                index = match.group(2)
                extension = match.group(3)
                
                ancien_chemin = os.path.join(root, fichier)
                
                # Si c'est le premier fichier (_1), renommer en {id}.ext
                if index == "1":
                    nouveau_nom = f"{transaction_id}{extension}"
                    nouveau_chemin = os.path.join(root, nouveau_nom)
                    
                    # Vérifier si le fichier cible existe déjà
                    if os.path.exists(nouveau_chemin) and ancien_chemin != nouveau_chemin:
                        logger.error(f"❌ CONFLIT: {nouveau_nom} existe déjà dans {root}")
                        conflits += 1
                        continue
                    
                    if dry_run:
                        logger.info(f"[DRY-RUN] {fichier} -> {nouveau_nom}")
                    else:
                        os.rename(ancien_chemin, nouveau_chemin)
                        logger.info(f"✅ {fichier} -> {nouveau_nom}")
                    
                    nb_renommes += 1
                
                else:
                    # Fichiers avec index > 1 : ce sont des doublons potentiels
                    logger.warning(f"⚠️  DOUBLON DÉTECTÉ: {fichier} (transaction #{transaction_id} a plusieurs fichiers!)")
                    logger.warning(f"   Chemin: {root}")
    
    return nb_renommes, conflits


def main(dry_run: bool = False):
    """Fonction principale."""
    logger.info("=" * 80)
    logger.info("NETTOYAGE DES SUFFIXES _1, _2, etc.")
    logger.info("=" * 80)
    
    if dry_run:
        logger.info("MODE DRY-RUN ACTIVÉ")
    
    logger.info(f"\nRecherche dans: {SORTED_DIR}")
    nb_sorted, conflits_sorted = cleanup_id_suffixes(SORTED_DIR, dry_run)
    
    logger.info(f"\nRecherche dans: {REVENUS_TRAITES}")
    nb_revenus, conflits_revenus = cleanup_id_suffixes(REVENUS_TRAITES, dry_run)
    
    total_renommes = nb_sorted + nb_revenus
    total_conflits = conflits_sorted + conflits_revenus
    
    logger.info("=" * 80)
    logger.info("RÉSUMÉ")
    logger.info("=" * 80)
    logger.info(f"Fichiers renommés: {total_renommes}")
    logger.info(f"Conflits détectés: {total_conflits}")
    
    if dry_run:
        logger.info("\nMODE DRY-RUN: Pour effectuer le nettoyage, exécutez sans --dry-run")
    else:
        logger.info("\nNETTOYAGE TERMINÉ!")


if __name__ == "__main__":
    dry_run_mode = "--dry-run" in sys.argv
    
    if dry_run_mode:
        print("\nMODE DRY-RUN ACTIVÉ\n")
    
    try:
        main(dry_run=dry_run_mode)
    except KeyboardInterrupt:
        logger.warning("\nNettoyage interrompu")
        sys.exit(1)
