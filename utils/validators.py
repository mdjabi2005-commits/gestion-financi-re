# -*- coding: utf-8 -*-
"""
Module validators - Partie de l'application gestiov4
Généré automatiquement par migrate_to_modular.py
"""

from datetime import datetime


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


def correct_category_name(name):
    """Corrige les fautes simples dans les noms de catégorie/sous-catégorie."""
    if not name:
        return name
    name = name.lower().strip()
    matches = get_close_matches(name, KNOWN_CATEGORIES, n=1, cutoff=0.8)
    return matches[0] if matches else name


