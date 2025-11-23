"""
Streamlit Component Backend for Fractal Navigation.

Provides interactive fractal visualization using Streamlit-native rendering.
Since custom components require build setup, this uses Streamlit's graphviz
and plotly for visualization fallback, or native rendering.

@author: djabi
@version: 1.0
@date: 2025-11-22
"""

import streamlit as st
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def fractal_navigation(
    data: Dict[str, Any],
    key: Optional[str] = None,
    height: int = 800
) -> Optional[Dict[str, Any]]:
    """
    Fractal Navigation Component - Interactive hierarchical data visualization.

    Renders an interactive interface for hierarchical data exploration using Streamlit.
    Users can click on buttons to navigate the hierarchy interactively.

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
            'current_node': 'REVENUS'
        }
        Returns None if no data provided.

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

        # Initialize session state for navigation
        if f'{key}_current_node' not in st.session_state:
            st.session_state[f'{key}_current_node'] = 'TR'
        if f'{key}_nav_stack' not in st.session_state:
            st.session_state[f'{key}_nav_stack'] = ['TR']

        current_code = st.session_state[f'{key}_current_node']
        nav_stack = st.session_state[f'{key}_nav_stack']

        if current_code not in data:
            current_code = 'TR'
            st.session_state[f'{key}_current_node'] = 'TR'

        current_node = data[current_code]

        # Create layout with two columns
        col_nav, col_main = st.columns([1, 4])

        # Left column: Navigation buttons
        with col_nav:
            st.markdown("### Navigateur")

            # Back button
            if len(nav_stack) > 1:
                if st.button("← Retour", key=f'{key}_back', use_container_width=True):
                    nav_stack.pop()
                    st.session_state[f'{key}_current_node'] = nav_stack[-1]
                    st.session_state[f'{key}_nav_stack'] = nav_stack
                    st.rerun()

            # Reset button
            if current_code != 'TR':
                if st.button("🏠 Vue d'ensemble", key=f'{key}_reset', use_container_width=True):
                    st.session_state[f'{key}_current_node'] = 'TR'
                    st.session_state[f'{key}_nav_stack'] = ['TR']
                    st.rerun()

            # Children navigation
            if current_node.get('children'):
                st.markdown("#### Catégories")

                for child_code in current_node['children']:
                    if child_code not in data:
                        continue

                    child = data[child_code]
                    label = child.get('label', child_code)
                    emoji = _get_emoji_for_node(child)

                    # Create button with info
                    amount = child.get('amount', child.get('total', 0))
                    display_text = f"{emoji} {label}\n{amount:,.0f}€"

                    if st.button(display_text, key=f'{key}_{child_code}', use_container_width=True):
                        nav_stack.append(child_code)
                        st.session_state[f'{key}_current_node'] = child_code
                        st.session_state[f'{key}_nav_stack'] = nav_stack
                        st.rerun()

        # Right column: Details
        with col_main:
            # Breadcrumb
            breadcrumb_path = " → ".join([
                data[code].get('label', code) for code in nav_stack if code in data
            ])
            st.markdown(f"**{breadcrumb_path}**")

            # Display current node
            st.markdown(f"### {_get_emoji_for_node(current_node)} {current_node.get('label', current_code)}")

            # Metrics
            col1, col2, col3 = st.columns(3)

            with col1:
                amount = current_node.get('amount', current_node.get('total', 0))
                st.metric("💰 Montant", f"{amount:,.0f}€")

            with col2:
                children_count = len(current_node.get('children', []))
                label = "Enfants" if children_count else "Transactions"
                st.metric(label, children_count if children_count else current_node.get('transactions', 0))

            with col3:
                pct = current_node.get('percentage', 100)
                st.metric("📈 %", f"{pct:.1f}%")

            # Display children as cards if they exist
            if current_node.get('children'):
                st.markdown("#### Exploration")

                # Create columns for children
                children_codes = current_node['children']
                cols = st.columns(min(3, len(children_codes)))

                for idx, child_code in enumerate(children_codes):
                    if child_code not in data:
                        continue

                    child = data[child_code]
                    col = cols[idx % len(cols)]

                    with col:
                        with st.container(border=True):
                            emoji = _get_emoji_for_node(child)
                            label = child.get('label', child_code)
                            amount = child.get('amount', child.get('total', 0))
                            pct = child.get('percentage', 0)

                            st.markdown(f"### {emoji} {label}")
                            st.markdown(f"**{amount:,.0f}€** ({pct:.1f}%)")

                            if child.get('children'):
                                st.caption(f"{len(child['children'])} catégories")
                            else:
                                txs = child.get('transactions', 0)
                                st.caption(f"{txs} transaction{'s' if txs != 1 else ''}")

                            # Navigate button
                            if st.button("Voir →", key=f'{key}_{child_code}_view'):
                                nav_stack.append(child_code)
                                st.session_state[f'{key}_current_node'] = child_code
                                st.session_state[f'{key}_nav_stack'] = nav_stack
                                st.rerun()

        # Return current state
        return {
            'code': current_code,
            'label': current_node.get('label', current_code),
            'level': len(nav_stack),
            'current_node': current_code
        }

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
