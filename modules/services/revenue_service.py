"""Revenue processing service for Uber and other revenue sources.

This module handles automatic tax calculations and revenue categorization
for various income sources, with special handling for Uber revenue.

IMPORTANT: When Uber tax is applied (21%), do NOT include URSSAF related expenses
as they are already accounted for in the tax deduction.
"""

import logging
from typing import Dict, Tuple, Any, Optional

from modules.utils.converters import safe_convert
from config.ocr_config import UBER_TAX_RATE, UBER_NET_MULTIPLIER

logger = logging.getLogger(__name__)


def is_uber_transaction(categorie: str, description: str = "") -> bool:
    """
    Check if a transaction is Uber-related (strict detection).

    Only detects transactions with "uber" keyword (case-insensitive).
    This is strict to avoid false positives with other delivery services.

    Args:
        categorie: Transaction category name
        description: Transaction description

    Returns:
        True if transaction contains "uber" keyword

    Example:
        >>> is_uber_transaction("Uber Eats")
        True
        >>> is_uber_transaction("UBER")
        True
        >>> is_uber_transaction("Deliveroo")
        False
    """
    categorie_lower = str(categorie).lower().strip()
    description_lower = str(description).lower().strip()

    # Strict detection: only "uber" keyword
    return 'uber' in categorie_lower or 'uber' in description_lower


def apply_uber_tax(
    categorie: str,
    montant_brut: float,
    description: str = "",
    apply_tax: bool = True
) -> Tuple[float, str]:
    """
    Apply tax calculation for Uber revenue with optional user confirmation.

    Uber drivers in France are subject to a 21% tax deduction on gross revenue.

    IMPORTANT: When applying Uber tax, do NOT add URSSAF expenses separately
    as they are already included in the 21% tax deduction.

    Args:
        categorie: Transaction category name
        montant_brut: Gross amount before tax
        description: Transaction description for additional detection
        apply_tax: If True, apply the tax deduction (default: True)

    Returns:
        Tuple of (montant_net, tax_message) where:
        - montant_net: Amount after tax (79% of gross) or gross if not applied
        - tax_message: Message explaining the tax calculation or empty

    Example:
        >>> montant_net, message = apply_uber_tax("Uber", 100.0)
        >>> montant_net
        79.0
        >>> "21%" in message
        True
    """
    if not is_uber_transaction(categorie, description):
        return montant_brut, ""

    if not apply_tax or montant_brut <= 0:
        return montant_brut, ""

    montant_net = round(montant_brut * UBER_NET_MULTIPLIER, 2)
    tax_amount = round(montant_brut - montant_net, 2)

    message = f"""
    🚗 **Revenu Uber détecté** - Application de la fiscalité ({UBER_TAX_RATE*100:.0f}%) :
    - Montant brut : {montant_brut:.2f}€
    - Prélèvement fiscal ({UBER_TAX_RATE*100:.0f}%) : -{tax_amount:.2f}€
    - **Montant net : {montant_net:.2f}€**

    ⚠️ **Important** : Ne pas ajouter les dépenses URSSAF séparément,
    elles sont déjà incluses dans ce prélèvement de {UBER_TAX_RATE*100:.0f}%.
    """

    logger.info(f"Uber tax applied: {montant_brut}€ → {montant_net}€")
    return montant_net, message


def process_uber_revenue(
    transaction: Dict[str, Any],
    apply_tax: bool = True
) -> Tuple[Dict[str, Any], str]:
    """
    Process a transaction to apply Uber-specific rules.

    Applies optional tax deduction (21%) and ensures proper categorization
    as "Uber" if not already categorized as such.

    Args:
        transaction: Dictionary with keys 'montant', 'categorie', 'description'
        apply_tax: If True, apply the 21% tax deduction (default: True)

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
        transaction.get('description', ''),
        apply_tax=apply_tax
    )

    transaction['montant'] = montant_final

    # Ensure proper categorization
    if 'uber' not in categorie.lower():
        transaction['categorie'] = 'Uber'

    return transaction, tax_message
