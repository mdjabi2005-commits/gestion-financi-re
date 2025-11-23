"""
Streamlit Component Backend for Fractal Navigation.

Provides interactive Sierpinski triangle-based fractal visualization.
Uses custom Streamlit component compiled with Webpack.

@author: djabi
@version: 2.0
@date: 2025-11-23
"""

import streamlit as st
import streamlit.components.v1 as components
import logging
from typing import Dict, Any, Optional
import os

logger = logging.getLogger(__name__)

# Get the directory where this component is located
_COMPONENT_DIR = os.path.dirname(os.path.abspath(__file__))
_BUILD_DIR = os.path.join(_COMPONENT_DIR, "build")

# Declare the component
fractal_component = components.declare_component(
    name="fractal_navigation",
    path=_BUILD_DIR
)


def fractal_navigation(
    data: Dict[str, Any],
    key: Optional[str] = None,
    height: int = 800
) -> Optional[Dict[str, Any]]:
    """
    Fractal Navigation Component - Interactive hierarchical data visualization.

    Renders Sierpinski triangle-based interactive interface for hierarchical exploration.
    Users can click on triangles to navigate the hierarchy with smooth animations.

    Args:
        data: Complete fractal hierarchy from build_fractal_hierarchy()
              Expected structure:
              {
                  'TR': {...},
                  'REVENUS': {...},
                  'CAT_SALAIRE': {...},
                  'SUBCAT_SALAIRE_NET': {...}
              }

        key: Unique key for this component instance (required by Streamlit)

        height: Height of the component in pixels (default: 800)

    Returns:
        Dictionary with interaction result:
        {
            'code': 'CAT_INVESTISSEMENT',
            'label': 'Category Name',
            'level': 2,
            'action': 'zoom' | 'back' | 'reset'
        }
        Returns None if no data provided or error occurs.

    Example:
        >>> from modules.services.fractal_service import build_fractal_hierarchy
        >>> from modules.ui.fractal_component import fractal_navigation
        >>>
        >>> hierarchy = build_fractal_hierarchy()
        >>> result = fractal_navigation(hierarchy, key='main_fractal')
        >>> if result:
        >>>     st.info(f"Navigated to: {result['label']}")
    """

    try:
        # Validate input data
        if not data:
            logger.warning("No data provided to fractal_navigation component")
            st.warning("Aucune donnée disponible pour la visualisation fractale")
            return None

        if 'TR' not in data:
            logger.warning("Invalid hierarchy structure: missing 'TR' root node")
            st.error("Structure de hiérarchie invalide")
            return None

        # Call the custom Streamlit component
        result = fractal_component(
            data=data,
            key=key,
            height=height
        )

        return result

    except Exception as e:
        logger.error(f"Error in fractal_navigation component: {e}", exc_info=True)
        st.error(f"Erreur dans la visualisation fractale: {str(e)}")
        return None


def _get_emoji_for_node(node: Dict[str, Any]) -> str:
    """Get appropriate emoji for a node based on its label."""

    label = node.get('label', '').lower()
    code = node.get('code', '').lower()

    emoji_map = {
        'revenus': '💼',
        'dépenses': '🛒',
        'salaire': '💵',
        'freelance': '🖥️',
        'investissement': '📈',
        'alimentation': '🍔',
        'transport': '🚗',
        'logement': '🏠',
        'santé': '⚕️',
        'loisirs': '🎮',
        'factures': '📄',
        'vêtements': '👕',
        'education': '📚',
    }

    for key, emoji in emoji_map.items():
        if key in label or key in code:
            return emoji

    return '📁'
