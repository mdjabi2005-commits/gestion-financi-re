"""Revenue processing service for Uber and other revenue sources.

This module handles automatic tax calculations and revenue categorization
for various income sources, with special handling for Uber revenue.
"""

import logging
from typing import Dict, Tuple, Any

from modules.utils.converters import safe_convert

logger = logging.getLogger(__name__)


def apply_uber_tax(
    categorie: str,
    montant_brut: float,
    description: str = ""
) -> Tuple[float, str]:
    """
    Apply automatic tax calculation for Uber revenue.

    Uber drivers in France are subject to a 21% tax deduction on gross revenue.
    This function detects Uber transactions and applies the tax automatically.

    Args:
        categorie: Transaction category name
        montant_brut: Gross amount before tax
        description: Transaction description for additional detection

    Returns:
        Tuple of (montant_net, tax_message) where:
        - montant_net: Amount after tax (79% of gross)
        - tax_message: Message explaining the tax calculation

    Example:
        >>> montant_net, message = apply_uber_tax("Uber", 100.0)
        >>> montant_net
        79.0
        >>> "21%" in message
        True
    """
    categorie_lower = str(categorie).lower().strip()
    description_lower = str(description).lower().strip()

    uber_keywords = ['uber', 'uber eats', 'livraison', 'driver', 'delivery']
    is_uber_revenu = (
        any(keyword in categorie_lower for keyword in uber_keywords) or
        any(keyword in description_lower for keyword in uber_keywords)
    )

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


def process_uber_revenue(transaction: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
    """
    Process a transaction to apply Uber-specific rules.

    Applies automatic tax deduction and ensures proper categorization
    as "Uber Eats" if not already categorized as Uber.

    Args:
        transaction: Dictionary with keys 'montant', 'categorie', 'description'

    Returns:
        Tuple of (modified_transaction, tax_message) where:
        - modified_transaction: Updated transaction dict with tax applied
        - tax_message: Message explaining any tax deduction

    Example:
        >>> tx = {'montant': 100.0, 'categorie': 'Uber', 'description': ''}
        >>> result_tx, msg = process_uber_revenue(tx)
        >>> result_tx['montant']
        79.0
    """
    montant_initial = safe_convert(transaction.get('montant', 0))
    categorie = transaction.get('categorie', '')

    montant_final, tax_message = apply_uber_tax(
        categorie,
        montant_initial,
        transaction.get('description', '')
    )

    transaction['montant'] = montant_final

    if 'uber' not in categorie.lower():
        transaction['categorie'] = 'Uber Eats'

    return transaction, tax_message
