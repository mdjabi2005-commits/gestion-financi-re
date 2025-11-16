# -*- coding: utf-8 -*-
"""
Module uber_tax - Partie de l'application gestiov4
Généré automatiquement par migrate_to_modular.py
"""

from datetime import datetime


def apply_uber_tax(categorie, montant_brut, description=""):
    """
    Applique automatiquement la réduction de 21% pour les revenus Uber
    """
    categorie_lower = str(categorie).lower().strip()
    description_lower = str(description).lower().strip()
    
    uber_keywords = ['uber', 'uber eats', 'livraison', 'driver', 'delivery']
    is_uber_revenu = any(keyword in categorie_lower for keyword in uber_keywords) or \
                    any(keyword in description_lower for keyword in uber_keywords)
    
    if is_uber_revenu and montant_brut > 0:
        montant_net = round(montant_brut * 0.79, 2)
        tax_amount = round(montant_brut - montant_net, 2)
        
        message = f"""
        🚗 **Revenu Uber détecté** - Application automatique de la fiscalité :
        - Montant brut : {montant_brut:.2f}€
        - Prélèvement fiscal (21%) : -{tax_amount:.2f}€  
        - **Montant net : {montant_net:.2f}€**
        """
        
        logger.info(f"Uber tax applied: {montant_brut}€ → {montant_net}€")
        return montant_net, message
    
    return montant_brut, ""


def process_uber_revenue(transaction):
    """
    Traitement spécialisé pour les revenus Uber
    """
    montant_initial = safe_convert(transaction.get('montant', 0))
    categorie = transaction.get('categorie', '')
    
    montant_final, tax_message = apply_uber_tax(categorie, montant_initial, 
                                              transaction.get('description', ''))
    
    transaction['montant'] = montant_final
    
    if 'uber' not in categorie.lower():
        transaction['categorie'] = 'Uber Eats'
    
    return transaction, tax_message


