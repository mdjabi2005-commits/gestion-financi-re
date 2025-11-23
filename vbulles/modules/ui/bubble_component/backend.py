"""
Bubble Navigation Custom Component Backend

Composant Streamlit personnalisé pour la navigation par bulles animées.
"""

import streamlit.components.v1 as components
import os
from pathlib import Path

# ============================================
# Configuration du composant
# ============================================

# Déterminer si c'est en mode de développement
_RELEASE = False

# Obtenir le chemin du répertoire frontend
_parent_dir = Path(__file__).parent
_build_dir = _parent_dir / "frontend"

# Vérifier que les fichiers existent
_index_path = _build_dir / "index.html"
_css_path = _build_dir / "bubble.css"
_js_path = _build_dir / "bubble.js"

if not _index_path.exists():
    raise FileNotFoundError(f"index.html not found at {_index_path}")
if not _css_path.exists():
    raise FileNotFoundError(f"bubble.css not found at {_css_path}")
if not _js_path.exists():
    raise FileNotFoundError(f"bubble.js not found at {_js_path}")

# ============================================
# Déclarer le composant
# ============================================

_bubble_navigation = components.declare_component(
    "bubble_navigation",
    url="http://localhost:3001" if _RELEASE == False else None,
    path=str(_build_dir) if _RELEASE else None,
)

# ============================================
# Interface publique
# ============================================

def bubble_navigation(data, key=None):
    """
    Composant de navigation par bulles animées avec D3.js.

    Ce composant permet une navigation hiérarchique à travers des transactions
    en utilisant des animations fluides et des transitions visuelles.

    Args:
        data (dict): Dictionnaire contenant les données à afficher
            - level (str): 'main', 'categories', ou 'subcategories'
            - total (float): Montant total (pour le niveau 'main')
            - categoriesCount (int): Nombre de catégories (pour le niveau 'main')
            - transactionsCount (int): Nombre de transactions (pour le niveau 'main')
            - categories (list): Liste des catégories avec structures:
                {
                    'name': str,        # Nom de la catégorie
                    'amount': float,    # Montant dépensé
                    'count': int        # Nombre de transactions
                }
            - selected_category (str): Catégorie sélectionnée
            - subcategoriesCount (int): Nombre de sous-catégories
            - transactionsCount (int): Nombre de transactions filtrées

        key (str, optional): Clé unique pour Streamlit. Par défaut None.

    Returns:
        dict or None: Événement retourné par le composant avec la structure:
            {
                'action': str,              # 'navigate', 'select', 'back'
                'level': str,               # Niveau cible
                'category': str (optionnel) # Pour l'action 'select'
            }
            Retourne None si aucune action n'a été effectuée.

    Example:
        >>> import streamlit as st
        >>> from modules.ui.bubble_component import bubble_navigation
        >>>
        >>> data = {
        ...     'level': 'main',
        ...     'total': 1250.50,
        ...     'categoriesCount': 7,
        ...     'transactionsCount': 45,
        ...     'categories': [
        ...         {'name': 'Alimentation', 'amount': 450, 'count': 23},
        ...         {'name': 'Transport', 'amount': 320, 'count': 12},
        ...     ]
        ... }
        >>>
        >>> result = bubble_navigation(data)
        >>> if result:
        ...     if result['action'] == 'navigate':
        ...         st.session_state.level = result['level']
        ...         st.rerun()
    """
    component_value = _bubble_navigation(
        data=data,
        key=key,
        default=None
    )

    return component_value


__all__ = ['bubble_navigation']
