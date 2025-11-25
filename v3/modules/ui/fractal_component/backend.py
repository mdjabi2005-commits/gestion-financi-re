"""
Streamlit Component Backend for Fractal Navigation.

Provides interactive Sierpinski triangle-based fractal visualization.
Uses HTML/Canvas with Streamlit's components.html()

@author: djabi
@version: 2.0
@date: 2025-11-23
"""

import streamlit as st
import streamlit.components.v1 as components
import logging
from typing import Dict, Any, Optional
import os
import json
from modules.ui.components import toast_warning

logger = logging.getLogger(__name__)

# Get the directory where this component is located
_COMPONENT_DIR = os.path.dirname(os.path.abspath(__file__))


def fractal_navigation(
    data: Dict[str, Any],
    key: Optional[str] = None,
    height: int = 800
) -> None:
    """
    Fractal Navigation Component - Simple hierarchical selector using Streamlit buttons.

    Renders an interactive interface for exploring hierarchical financial data.
    Users can navigate and select categories to filter transactions.

    Args:
        data: Complete fractal hierarchy from build_fractal_hierarchy()
        key: Unique key for this component instance (required by Streamlit)
        height: Height parameter (kept for compatibility)

    Example:
        >>> from modules.services.fractal_service import build_fractal_hierarchy
        >>> from modules.ui.fractal_component import fractal_navigation
        >>>
        >>> hierarchy = build_fractal_hierarchy()
        >>> fractal_navigation(hierarchy, key='main_fractal')
    """
    try:
        if not data or 'TR' not in data:
            st.error("Structure de hiérarchie invalide")
            return

        # Initialize state
        if f'{key}_current_node' not in st.session_state:
            st.session_state[f'{key}_current_node'] = 'TR'
        if f'{key}_nav_stack' not in st.session_state:
            st.session_state[f'{key}_nav_stack'] = ['TR']

        current_node = st.session_state[f'{key}_current_node']
        nav_stack = st.session_state[f'{key}_nav_stack']

        # Get current node info
        node = data.get(current_node, {})
        label = node.get('label', current_node)
        total = node.get('amount') or node.get('total') or 0
        children_codes = node.get('children', [])

        # Display current node info
        st.markdown(f"### 📍 {label} ({total:,.0f}€)")

        # Afficher les métriques (comme cap8)
        # On a besoin du nombre de transactions du nœud courant
        tx_count = node.get('transactions', 0)
        if tx_count > 0:
            # Importer la fonction pour récupérer les transactions du nœud
            from modules.services.fractal_service import get_transactions_for_node
            from modules.database.repositories import TransactionRepository

            # Récupérer les transactions réelles pour ce nœud
            df_node_transactions = get_transactions_for_node(current_node, data)

            # Calculer revenus et dépenses
            total_revenus = 0
            total_depenses = 0

            if not df_node_transactions.empty:
                total_revenus = df_node_transactions[df_node_transactions['type'].str.lower() == 'revenu']['montant'].sum()
                total_depenses = df_node_transactions[df_node_transactions['type'].str.lower() == 'dépense']['montant'].sum()

            # Solde = Revenus - Dépenses (dépenses sont négatives)
            solde = total_revenus + total_depenses

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Transactions", tx_count)
            with col2:
                st.metric("Revenus", f"{total_revenus:,.0f}€")
            with col3:
                st.metric("Dépenses", f"{abs(total_depenses):,.0f}€")
            with col4:
                st.metric("Solde", f"{solde:,.0f}€")
            st.markdown("---")

        # Navigation buttons
        col1, col2 = st.columns([1, 1])
        with col1:
            if len(nav_stack) > 1:
                nav_depth = '_'.join(nav_stack)
                if st.button("← Retour", key=f"{key}_back_{nav_depth}", use_container_width=True):
                    nav_stack.pop()
                    st.session_state[f'{key}_current_node'] = nav_stack[-1]
                    st.session_state[f'{key}_nav_stack'] = nav_stack
                    st.rerun()
        with col2:
            if current_node != 'TR':
                nav_depth = '_'.join(nav_stack)
                if st.button("🏠 Vue d'ensemble", key=f"{key}_reset_{nav_depth}", use_container_width=True):
                    st.session_state[f'{key}_current_node'] = 'TR'
                    st.session_state[f'{key}_nav_stack'] = ['TR']
                    st.rerun()

        st.markdown("---")

        # Display children
        if children_codes:
            st.markdown("**Sous-niveaux:**")

            for idx, child_code in enumerate(children_codes):
                child_node = data.get(child_code, {})
                child_label = child_node.get('label', child_code)
                # Pour les niveaux 1-2: 'total' ou 'amount', pour le niveau 3: 'amount'
                child_total = child_node.get('amount') or child_node.get('total') or 0

                child_level = child_node.get('level', 0)

                # Get sub-children count
                sub_children = child_node.get('children', [])
                has_children = len(sub_children) > 0

                # Create button text
                if has_children:
                    btn_text = f"📂 {child_label} ({child_total:,.0f}€)"
                else:
                    btn_text = f"📋 {child_label} ({child_total:,.0f}€)"

                # Create unique key including navigation path
                unique_key = f"{key}_nav_{'_'.join(nav_stack)}_{idx}_{child_code}"

                # Button to navigate or select
                if st.button(btn_text, key=unique_key, use_container_width=True):
                    if has_children:
                        # Navigate deeper
                        nav_stack.append(child_code)
                        st.session_state[f'{key}_current_node'] = child_code
                        st.session_state[f'{key}_nav_stack'] = nav_stack
                        st.rerun()
                    else:
                        # Leaf node: select for filtering
                        if 'fractal_selections' not in st.session_state:
                            st.session_state.fractal_selections = set()

                        if child_code in st.session_state.fractal_selections:
                            st.session_state.fractal_selections.discard(child_code)
                            st.rerun()
                        else:
                            # Vérifier si c'est une sous-catégorie (niveau 3) et si son parent est déjà sélectionné
                            child_level = child_node.get('level', 0)
                            if child_level == 3:
                                parent_code = child_node.get('parent', '')
                                if parent_code in st.session_state.fractal_selections:
                                    # Parent est déjà sélectionné, afficher un warning
                                    toast_warning(f"{child_label} est déjà incluse dans {data.get(parent_code, {}).get('label', parent_code)}", duration=10000)
                                else:
                                    st.session_state.fractal_selections.add(child_code)
                                    st.rerun()
                            else:
                                st.session_state.fractal_selections.add(child_code)
                                st.rerun()

                # Pour les niveaux 2 (catégories), ajouter aussi un bouton de sélection directe
                child_level = child_node.get('level', 0)
                if child_level == 2 and has_children:
                    # Ajouter un bouton "Ajouter filtre" pour les catégories
                    nav_depth = '_'.join(nav_stack)
                    add_filter_key = f"add_filter_{nav_depth}_{idx}_{child_code}"
                    if st.button(f"➕ Ajouter le filtre '{child_label}'", key=add_filter_key, use_container_width=True):
                        if 'fractal_selections' not in st.session_state:
                            st.session_state.fractal_selections = set()

                        # Vérifier si c'est déjà sélectionné
                        if child_code in st.session_state.fractal_selections:
                            toast_warning(f"{child_label} est déjà sélectionnée", duration=10000)
                        else:
                            st.session_state.fractal_selections.add(child_code)
                            st.rerun()

        else:
            # Leaf node info
            st.info("✅ Cliquez sur ce bouton pour sélectionner")
            unique_key = f"{key}_select_{'_'.join(nav_stack)}"
            if st.button(f"✓ Sélectionner {label}", key=unique_key, use_container_width=True):
                if 'fractal_selections' not in st.session_state:
                    st.session_state.fractal_selections = set()

                if current_node in st.session_state.fractal_selections:
                    st.session_state.fractal_selections.discard(current_node)
                    st.rerun()
                else:
                    # Vérifier si c'est une sous-catégorie et si son parent est déjà sélectionné
                    current_level = node.get('level', 0)
                    if current_level == 3:
                        parent_code = node.get('parent', '')
                        if parent_code in st.session_state.fractal_selections:
                            toast_warning(f"{label} est déjà incluse dans {data.get(parent_code, {}).get('label', parent_code)}", duration=10000)
                        else:
                            st.session_state.fractal_selections.add(current_node)
                            st.rerun()
                    else:
                        st.session_state.fractal_selections.add(current_node)
                        st.rerun()

    except Exception as e:
        logger.error(f"Error in fractal_navigation component: {e}", exc_info=True)
        st.error(f"Erreur dans la visualisation fractale: {str(e)}")
