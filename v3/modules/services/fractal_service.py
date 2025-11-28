"""
Fractal Navigation Service - Builds hierarchical data structure for Sierpinski triangle navigation.

This service constructs the complete hierarchy needed by the fractal component:
- Level 1: Transaction types (Revenus, Dépenses)
- Level 2: Categories within each type
- Level 3: Sub-categories within each category

@author: djabi
@version: 1.0
@date: 2025-11-22
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import pandas as pd
from modules.database.repositories import TransactionRepository

logger = logging.getLogger(__name__)

# ==============================
# COLOR PALETTES
# ==============================

REVENUS_COLORS: Dict[str, str] = {
    'Salaire': '#059669',
    'Freelance': '#10b981',
    'Investissement': '#14b8a6',
    'Dividende': '#06b6d4',
    'Intérêt': '#0891b2',
    'Bonus': '#0d9488',
    'Autre': '#047857'
}

DEPENSES_COLORS: Dict[str, str] = {
    'Alimentation': '#ef4444',
    'Transport': '#8b5cf6',
    'Logement': '#d97706',
    'Santé': '#06b6d4',
    'Loisirs': '#ec4899',
    'Factures': '#3b82f6',
    'Vêtements': '#f97316',
    'Education': '#6366f1',
    'Autre': '#f59e0b'
}

# Default color for unknown categories
DEFAULT_CATEGORY_COLOR = '#6b7280'


# ==============================
# SERVICE FUNCTIONS
# ==============================

def get_category_color(category_name: str, category_type: str) -> str:
    """
    Get color for a category based on type and name.

    Args:
        category_name: Name of the category (e.g., 'Salaire', 'Alimentation')
        category_type: Type of transaction ('revenu' or 'dépense')

    Returns:
        Hex color code
    """
    if category_type.lower() == 'revenu':
        return REVENUS_COLORS.get(category_name, DEFAULT_CATEGORY_COLOR)
    else:
        return DEPENSES_COLORS.get(category_name, DEFAULT_CATEGORY_COLOR)


def get_type_color(transaction_type: str) -> str:
    """
    Get color for transaction type.

    Args:
        transaction_type: 'revenu' or 'dépense'

    Returns:
        Hex color code
    """
    if transaction_type.lower() == 'revenu':
        return '#10b981'  # Green
    else:
        return '#f59e0b'  # Orange


def build_fractal_hierarchy(
    date_debut: Optional[str] = None,
    date_fin: Optional[str] = None
) -> Dict[str, Any]:
    """
    Build complete hierarchical structure for fractal navigation.

    Constructs a 3-level hierarchy:
    1. Transaction types (TR root node)
    2. Categories within each type
    3. Sub-categories within each category

    Args:
        date_debut: Start date (ISO format, optional)
        date_fin: End date (ISO format, optional)

    Returns:
        Dictionary with structure:
        {
            'TR': {
                'code': 'TR',
                'label': 'Univers Financier',
                'total': 5650.00,
                'color': '#ffffff',
                'parent': None,
                'children': ['REVENUS', 'DEPENSES']
            },
            'REVENUS': {
                'code': 'REVENUS',
                'label': 'Revenus',
                'total': 3200.00,
                'color': '#10b981',
                'parent': 'TR',
                'children': ['CAT_SALAIRE', 'CAT_FREELANCE', ...],
                'level': 1
            },
            'CAT_SALAIRE': {
                'code': 'CAT_SALAIRE',
                'label': 'Salaire',
                'amount': 2500.00,
                'percentage': 78.1,
                'color': '#059669',
                'parent': 'REVENUS',
                'children': ['SUBCAT_SALAIRE_NET'],
                'transactions': 1,
                'level': 2
            },
            'SUBCAT_SALAIRE_NET': {
                'code': 'SUBCAT_SALAIRE_NET',
                'label': 'Salaire Net',
                'amount': 2500.00,
                'percentage': 100.0,
                'color': '#047857',
                'parent': 'CAT_SALAIRE',
                'transactions': 1,
                'level': 3
            }
        }
    """
    logger.info(f"Building fractal hierarchy (date_debut={date_debut}, date_fin={date_fin})")

    try:
        # Get all transactions
        df_all = TransactionRepository.get_all()

        if df_all.empty:
            logger.warning("No transactions found in database")
            return _get_empty_hierarchy()

        # Filter by date range if provided
        if date_debut or date_fin:
            df_all = _filter_by_date_range(df_all, date_debut, date_fin)
            if df_all.empty:
                logger.warning("No transactions found for the given date range")
                return _get_empty_hierarchy()

        # Initialize hierarchy
        hierarchy: Dict[str, Any] = {}

        # Calculate global totals
        total_all = df_all['montant'].sum()

        # ROOT NODE: TR (Transaction Root)
        hierarchy['TR'] = {
            'code': 'TR',
            'label': 'Univers Financier',
            'total': float(total_all),
            'color': '#ffffff',
            'parent': None,
            'children': [],
            'level': 0
        }

        # LEVEL 1: Types (Revenus, Dépenses)
        for tx_type in df_all['type'].unique():
            df_type = df_all[df_all['type'] == tx_type]
            type_total = df_type['montant'].sum()
            type_code = 'REVENUS' if tx_type.lower() == 'revenu' else 'DEPENSES'
            type_label = 'Revenus' if tx_type.lower() == 'revenu' else 'Dépenses'

            hierarchy[type_code] = {
                'code': type_code,
                'label': type_label,
                'total': float(type_total),
                'color': get_type_color(tx_type),
                'parent': 'TR',
                'children': [],
                'level': 1
            }

            # Add to root
            hierarchy['TR']['children'].append(type_code)

            # LEVEL 2: Categories
            categories = df_type.groupby('categorie').agg({
                'montant': ['sum', 'count'],
                'sous_categorie': lambda x: x.notna().sum()
            }).reset_index()

            categories.columns = ['categorie', 'montant', 'count', 'subcategories']
            categories = categories.sort_values('montant', ascending=False)

            for idx, (_, cat_row) in enumerate(categories.iterrows()):
                cat_name = cat_row['categorie']
                cat_amount = float(cat_row['montant'])
                cat_count = int(cat_row['count'])
                # Include type_code in category code to make it unique (avoid collisions if same category exists in REVENUS and DEPENSES)
                cat_code = f"CAT_{type_code}_{cat_name.upper().replace(' ', '_').replace('-', '_')}"
                cat_color = get_category_color(cat_name, tx_type)

                cat_percentage = (cat_amount / type_total * 100) if type_total > 0 else 0

                hierarchy[cat_code] = {
                    'code': cat_code,
                    'label': cat_name,
                    'amount': cat_amount,
                    'percentage': float(cat_percentage),
                    'color': cat_color,
                    'parent': type_code,
                    'children': [],
                    'transactions': cat_count,
                    'level': 2
                }

                # Add to parent type
                hierarchy[type_code]['children'].append(cat_code)

                # LEVEL 3: Sub-categories
                df_category = df_type[df_type['categorie'] == cat_name]

                subcategories = df_category[df_category['sous_categorie'].notna()].groupby('sous_categorie').agg({
                    'montant': ['sum', 'count']
                }).reset_index()

                subcategories.columns = ['sous_categorie', 'montant', 'count']
                subcategories = subcategories.sort_values('montant', ascending=False)

                for subcat_idx, (_, subcat_row) in enumerate(subcategories.iterrows()):
                    subcat_name = subcat_row['sous_categorie']
                    subcat_amount = float(subcat_row['montant'])
                    subcat_count = int(subcat_row['count'])
                    # Include type_code in subcategory code to make it unique (avoid collisions)
                    subcat_code = f"SUBCAT_{type_code}_{cat_name.upper().replace(' ', '_').replace('-', '_')}_" \
                                 f"{subcat_name.upper().replace(' ', '_').replace('-', '_')}"

                    # Use slightly darker shade of category color
                    subcat_color = _darken_color(cat_color, 0.85)

                    subcat_percentage = (subcat_amount / cat_amount * 100) if cat_amount > 0 else 0

                    hierarchy[subcat_code] = {
                        'code': subcat_code,
                        'label': subcat_name,
                        'amount': subcat_amount,
                        'percentage': float(subcat_percentage),
                        'color': subcat_color,
                        'parent': cat_code,
                        'children': [],
                        'transactions': subcat_count,
                        'level': 3
                    }

                    # Add to parent category
                    hierarchy[cat_code]['children'].append(subcat_code)

        logger.info(f"Fractal hierarchy built with {len(hierarchy)} nodes")
        return hierarchy

    except Exception as e:
        logger.error(f"Error building fractal hierarchy: {e}", exc_info=True)
        return _get_empty_hierarchy()


def get_transactions_for_node(
    node_code: str,
    hierarchy: Dict[str, Any],
    date_debut: Optional[str] = None,
    date_fin: Optional[str] = None
) -> pd.DataFrame:
    """
    Get all transactions for a specific node in the hierarchy.

    Args:
        node_code: Code of the node (e.g., 'CAT_SALAIRE')
        hierarchy: The fractal hierarchy
        date_debut: Start date (optional)
        date_fin: End date (optional)

    Returns:
        DataFrame with filtered transactions
    """
    if node_code not in hierarchy:
        logger.warning(f"Node {node_code} not found in hierarchy")
        return pd.DataFrame()

    try:
        df_all = TransactionRepository.get_all()

        if df_all.empty:
            return pd.DataFrame()

        # Filter by date range if provided
        if date_debut or date_fin:
            df_all = _filter_by_date_range(df_all, date_debut, date_fin)

        node = hierarchy[node_code]

        # Filter based on node type
        if node_code == 'TR':
            # Root: return all
            return df_all

        elif node_code in ['REVENUS', 'DEPENSES']:
            # Type level
            tx_type = 'revenu' if node_code == 'REVENUS' else 'dépense'
            return df_all[df_all['type'] == tx_type]

        elif node_code.startswith('CAT_'):
            # Category level
            parent_type = hierarchy[node_code]['parent']
            tx_type = 'revenu' if parent_type == 'REVENUS' else 'dépense'
            category_name = node['label']
            return df_all[(df_all['type'] == tx_type) & (df_all['categorie'] == category_name)]

        elif node_code.startswith('SUBCAT_'):
            # Sub-category level
            parent_category_code = hierarchy[node_code]['parent']
            parent_category = hierarchy[parent_category_code]['label']
            subcategory_name = node['label']

            return df_all[(df_all['categorie'] == parent_category) &
                         (df_all['sous_categorie'] == subcategory_name)]

        return pd.DataFrame()

    except Exception as e:
        logger.error(f"Error getting transactions for node {node_code}: {e}", exc_info=True)
        return pd.DataFrame()


def get_node_info(node_code: str, hierarchy: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Get information about a specific node.

    Args:
        node_code: Code of the node
        hierarchy: The fractal hierarchy

    Returns:
        Node information or None if not found
    """
    return hierarchy.get(node_code)


# ==============================
# HELPER FUNCTIONS
# ==============================

def _filter_by_date_range(df: pd.DataFrame, date_debut: Optional[str], date_fin: Optional[str]) -> pd.DataFrame:
    """
    Filter DataFrame by date range.

    Args:
        df: Input DataFrame
        date_debut: Start date (ISO format)
        date_fin: End date (ISO format)

    Returns:
        Filtered DataFrame
    """
    try:
        df = df.copy()
        df['date'] = pd.to_datetime(df['date'])

        if date_debut:
            df = df[df['date'] >= pd.to_datetime(date_debut)]

        if date_fin:
            df = df[df['date'] <= pd.to_datetime(date_fin)]

        return df
    except Exception as e:
        logger.error(f"Error filtering by date range: {e}")
        return df


def _darken_color(hex_color: str, factor: float = 0.8) -> str:
    """
    Darken a hex color.

    Args:
        hex_color: Hex color code (e.g., '#10b981')
        factor: Darkening factor (0-1, lower = darker)

    Returns:
        Darkened hex color
    """
    try:
        # Remove '#' if present
        hex_color = hex_color.lstrip('#')

        # Convert to RGB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        # Apply darkening factor
        r = int(r * factor)
        g = int(g * factor)
        b = int(b * factor)

        # Convert back to hex
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception as e:
        logger.error(f"Error darkening color: {e}")
        return hex_color


def _get_empty_hierarchy() -> Dict[str, Any]:
    """
    Return an empty hierarchy structure.

    Returns:
        Empty fractal hierarchy
    """
    return {
        'TR': {
            'code': 'TR',
            'label': 'Univers Financier',
            'total': 0.0,
            'color': '#ffffff',
            'parent': None,
            'children': [],
            'level': 0
        }
    }
