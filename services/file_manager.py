# -*- coding: utf-8 -*-
"""
Module file_manager - Partie de l'application gestiov4
Généré automatiquement par migrate_to_modular.py
"""

import os
import shutil
from pathlib import Path
from config import SORTED_DIR, REVENUS_TRAITES


def trouver_fichiers_associes(transaction, base_dirs=[SORTED_DIR, REVENUS_TRAITES]):
    """
    Trouve les fichiers (images/PDF) associés à une transaction basée sur:
    - Catégorie et sous-catégorie
    - Date (approximative)
    - Montant (approximatif)
    """
    fichiers_trouves = []
    
    categorie = transaction.get("categorie", "").strip()
    sous_categorie = transaction.get("sous_categorie", "").strip()
    date_transaction = transaction.get("date", "")
    montant = transaction.get("montant", 0.0)
    source = transaction.get("source", "")
    
    # Déterminer le dossier de recherche selon la source
    if source in ["OCR", "import_csv"] and "dépense" in transaction.get("type", ""):
        dossiers_recherche = [SORTED_DIR]
    elif source in ["PDF", "import_csv"] and "revenu" in transaction.get("type", ""):
        dossiers_recherche = [REVENUS_TRAITES]
    else:
        dossiers_recherche = base_dirs
    
    for base_dir in dossiers_recherche:
        if not os.path.exists(base_dir):
            continue
            
        # Construire le chemin attendu : base/categorie/sous_categorie/
        chemin_attendu = os.path.join(base_dir, categorie, sous_categorie)
        
        if os.path.exists(chemin_attendu):
            # Rechercher tous les fichiers dans le dossier
            for fichier in os.listdir(chemin_attendu):
                if fichier.lower().endswith(('.jpg', '.jpeg', '.png', '.pdf')):
                    chemin_complet = os.path.join(chemin_attendu, fichier)
                    
                    # Vérification supplémentaire par date (optionnelle)
                    if date_transaction:
                        try:
                            # Extraire la date du nom de fichier si possible
                            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', fichier)
                            if date_match:
                                date_fichier = date_match.group(1)
                                if date_fichier in date_transaction:
                                    fichiers_trouves.append(chemin_complet)
                                    continue
                        except:
                            pass
                    
                    # Si pas de correspondance par date, on l'ajoute quand même
                    fichiers_trouves.append(chemin_complet)
    
    return fichiers_trouves[:5]  # Limiter à 5 fichiers maximum


def supprimer_fichiers_associes(transaction):
    """
    Supprime les fichiers PDF/OCR associés à une transaction
    Retourne le nombre de fichiers supprimés
    """
    fichiers = trouver_fichiers_associes(transaction)
    nb_supprimes = 0

    for fichier in fichiers:
        try:
            if os.path.exists(fichier):
                os.remove(fichier)
                nb_supprimes += 1
                logger.info(f"Fichier supprimé : {fichier}")

                # Supprimer le dossier parent s'il est vide
                parent_dir = os.path.dirname(fichier)
                if os.path.exists(parent_dir) and not os.listdir(parent_dir):
                    os.rmdir(parent_dir)
                    logger.info(f"Dossier vide supprimé : {parent_dir}")

                    # Supprimer le dossier catégorie s'il est vide
                    cat_dir = os.path.dirname(parent_dir)
                    if os.path.exists(cat_dir) and not os.listdir(cat_dir):
                        os.rmdir(cat_dir)
                        logger.info(f"Dossier catégorie vide supprimé : {cat_dir}")
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de {fichier} : {e}")

    return nb_supprimes


def deplacer_fichiers_associes(transaction_old, transaction_new):
    """
    Déplace les fichiers associés si la catégorie, sous-catégorie ou date a changé
    Retourne le nombre de fichiers déplacés
    """
    # Vérifier si un déplacement est nécessaire
    cat_changed = transaction_old.get("categorie") != transaction_new.get("categorie")
    souscat_changed = transaction_old.get("sous_categorie") != transaction_new.get("sous_categorie")

    if not (cat_changed or souscat_changed):
        return 0  # Pas de déplacement nécessaire

    source = transaction_old.get("source", "")
    if source not in ["OCR", "PDF"]:
        return 0  # Pas de fichiers à déplacer

    # Trouver les fichiers de l'ancienne transaction
    fichiers = trouver_fichiers_associes(transaction_old)
    nb_deplaces = 0

    # Déterminer le dossier de base selon la source
    if source == "OCR":
        base_dir = SORTED_DIR
    else:  # PDF
        base_dir = REVENUS_TRAITES

    # Créer le nouveau chemin
    nouveau_chemin = os.path.join(
        base_dir,
        transaction_new.get("categorie", "").strip(),
        transaction_new.get("sous_categorie", "").strip()
    )

    # Créer le dossier de destination si nécessaire
    os.makedirs(nouveau_chemin, exist_ok=True)

    for fichier in fichiers:
        try:
            if os.path.exists(fichier):
                nom_fichier = os.path.basename(fichier)
                nouveau_fichier = os.path.join(nouveau_chemin, nom_fichier)

                # Déplacer le fichier
                shutil.move(fichier, nouveau_fichier)
                nb_deplaces += 1
                logger.info(f"Fichier déplacé : {fichier} -> {nouveau_fichier}")

                # Nettoyer les dossiers vides
                ancien_dir = os.path.dirname(fichier)
                if os.path.exists(ancien_dir) and not os.listdir(ancien_dir):
                    os.rmdir(ancien_dir)
                    logger.info(f"Dossier vide supprimé : {ancien_dir}")

                    # Supprimer le dossier catégorie s'il est vide
                    cat_dir = os.path.dirname(ancien_dir)
                    if os.path.exists(cat_dir) and not os.listdir(cat_dir):
                        os.rmdir(cat_dir)
                        logger.info(f"Dossier catégorie vide supprimé : {cat_dir}")
        except Exception as e:
            logger.error(f"Erreur lors du déplacement de {fichier} : {e}")

    return nb_deplaces


def move_ticket_to_sorted(ticket_path, categorie, sous_categorie):
    """Déplace un ticket traité vers le dossier 'tickets_scannes' classé par catégorie/sous-catégorie.
       Gère automatiquement les doublons en renommant les fichiers si nécessaire."""
    cat_dir = os.path.join(SORTED_DIR, categorie.strip())
    souscat_dir = os.path.join(cat_dir, sous_categorie.strip())
    os.makedirs(souscat_dir, exist_ok=True)

    base_name = os.path.basename(ticket_path)
    dest_path = os.path.join(souscat_dir, base_name)

    # 🔁 Si un fichier du même nom existe déjà, on crée un nom unique
    if os.path.exists(dest_path):
        name, ext = os.path.splitext(base_name)
        counter = 1
        while os.path.exists(dest_path):
            new_name = f"{name}_{counter}{ext}"
            dest_path = os.path.join(souscat_dir, new_name)
            counter += 1

    shutil.move(ticket_path, dest_path)
    toast_success("Ticket déplacé vers : {dest_path}")


