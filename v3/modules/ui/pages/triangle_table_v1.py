"""
Triangle & Table - Approach 1: Interactive Selection

This module implements Approach 1 for linking the triangle visualization with transaction table.
When user clicks on a triangle, the table below filters to show transactions for that category.

Features:
- Triangle navigation at the top
- Table filters automatically based on triangle selection
- Session state tracks current selection
- Immediate visual feedback

@author: djabi
@version: 1.0
@date: 2025-11-23
"""

import streamlit as st
import pandas as pd
from typing import Optional, Dict, Any
from datetime import datetime, date

from modules.services.fractal_service import build_fractal_hierarchy
from modules.ui.fractal_component import fractal_navigation
from modules.ui.helpers import load_transactions
from modules.utils.converters import safe_convert


def init_session_state():
    """Initialize session state variables for triangle-table interaction."""
    if 'triangle_selection' not in st.session_state:
        st.session_state.triangle_selection = None
    if 'triangle_level' not in st.session_state:
        st.session_state.triangle_level = None
    if 'triangle_label' not in st.session_state:
        st.session_state.triangle_label = None


def filter_transactions_by_selection(df: pd.DataFrame, selection: Optional[str]) -> pd.DataFrame:
    """
    Filter transactions dataframe based on triangle selection.

    Args:
        df: Complete transactions dataframe
        selection: Selected triangle code (e.g., 'REVENUS', 'CAT_SALAIRE')

    Returns:
        Filtered dataframe
    """
    if selection is None or df.empty:
        return df.copy()

    # Map selection code to filter conditions
    selection_lower = selection.lower()

    # Level 1: Transaction type (REVENUS or DEPENSES)
    if selection_lower == 'revenus':
        return df[df['type'].str.lower() == 'revenu'].copy()
    elif selection_lower == 'depenses':
        return df[df['type'].str.lower() == 'dépense'].copy()

    # Level 2 & 3: Category/Subcategory
    # Build the full category name from code
    # CAT_SALAIRE -> Salaire
    # CAT_ALIMENTATION -> Alimentation
    # SUBCAT_SALAIRE_NET -> Salaire (category) + Salaire Net (subcategory)

    if selection.startswith('CAT_'):
        category = selection[4:].replace('_', ' ').title()
        return df[df['categorie'].str.lower() == category.lower()].copy()

    if selection.startswith('SUBCAT_'):
        # Extract category and subcategory from code
        # SUBCAT_SALAIRE_NET -> SALAIRE (category), NET (subcategory)
        parts = selection[7:].split('_')
        if len(parts) >= 2:
            category = parts[0].title()
            subcategory = '_'.join(parts[1:]).replace('_', ' ').title()
            return df[
                (df['categorie'].str.lower() == category.lower()) &
                (df['sous_categorie'].str.lower() == subcategory.lower())
            ].copy()

    return df.copy()


def get_selection_from_code(code: str, hierarchy: Dict[str, Any]) -> tuple:
    """
    Extract readable label from hierarchy code.

    Args:
        code: Hierarchy node code
        hierarchy: Complete hierarchy dictionary

    Returns:
        Tuple of (code, label, type)
    """
    if code in hierarchy:
        node = hierarchy[code]
        return code, node.get('label', code), 'selection'
    return code, code, 'unknown'


def display_selection_info(selection: Optional[str], label: Optional[str]):
    """Display current selection info above the table."""
    if selection:
        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            st.info(f"🎯 **Sélection active:** {label}")

        with col3:
            if st.button("❌ Réinitialiser", key="reset_selection"):
                st.session_state.triangle_selection = None
                st.session_state.triangle_label = None
                st.session_state.triangle_level = None
                st.rerun()
    else:
        st.info("👆 Cliquez sur un triangle pour filtrer les transactions")


def display_stats(df: pd.DataFrame):
    """Display statistics about current filtered data."""
    if df.empty:
        st.warning("📭 Aucune transaction ne correspond à cette sélection")
        return

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("📊 Transactions", len(df))

    with col2:
        revenus = df[df['type'].str.lower() == 'revenu']['montant'].sum()
        st.metric("💹 Total Revenus", f"{revenus:,.2f}€")

    with col3:
        depenses = df[df['type'].str.lower() == 'dépense']['montant'].sum()
        st.metric("💸 Total Dépenses", f"{depenses:,.2f}€")

    with col4:
        solde = revenus - depenses
        st.metric("📈 Solde", f"{solde:,.2f}€")


def display_transactions_table(df: pd.DataFrame, selection: Optional[str]):
    """
    Display filtered transactions in a formatted table.

    Args:
        df: Filtered transactions dataframe
        selection: Current selection code
    """
    if df.empty:
        st.info("Aucune transaction à afficher")
        return

    # Prepare display dataframe
    df_display = df.copy()
    df_display["montant"] = df_display["montant"].apply(lambda x: safe_convert(x, float, 0.0))

    # Add type icon
    df_display["Type"] = df_display["type"].apply(lambda x: "💹" if x.lower() == "revenu" else "💸")

    # Format date
    df_display["Date"] = pd.to_datetime(df_display["date"]).dt.strftime("%d/%m/%Y")

    # Signed amount for display
    df_display["Montant"] = df_display.apply(
        lambda row: row["montant"] if row["type"].lower() == "revenu" else -row["montant"],
        axis=1
    )

    # Display table
    st.dataframe(
        df_display[["Type", "Date", "categorie", "sous_categorie", "Montant", "description"]].rename(
            columns={
                "categorie": "Catégorie",
                "sous_categorie": "Sous-catégorie",
                "description": "Description"
            }
        ),
        use_container_width=True,
        height=500,
        hide_index=True,
        column_config={
            "Montant": st.column_config.NumberColumn("Montant (€)", format="%.2f €")
        }
    )


def display_hierarchy_buttons(hierarchy: Dict[str, Any]):
    """
    Display interactive buttons for selecting categories from hierarchy.

    This provides an alternative way to select categories in addition to clicking triangles.
    """
    st.markdown("#### 📌 Ou sélectionnez directement une catégorie")

    # Get root node
    root = hierarchy.get('TR', {})
    children = root.get('children', [])

    if not children:
        return

    # Display type selection (Revenus / Dépenses)
    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "💼 Revenus",
            key="select_revenus",
            use_container_width=True,
            type="secondary" if st.session_state.triangle_selection != 'REVENUS' else "primary"
        ):
            st.session_state.triangle_selection = 'REVENUS'
            st.session_state.triangle_label = 'Revenus'
            st.session_state.triangle_level = 1
            st.rerun()

    with col2:
        if st.button(
            "🛒 Dépenses",
            key="select_depenses",
            use_container_width=True,
            type="secondary" if st.session_state.triangle_selection != 'DEPENSES' else "primary"
        ):
            st.session_state.triangle_selection = 'DEPENSES'
            st.session_state.triangle_label = 'Dépenses'
            st.session_state.triangle_level = 1
            st.rerun()


def display_category_buttons(hierarchy: Dict[str, Any], current_selection: Optional[str]):
    """Display category/subcategory buttons based on current selection."""

    if not current_selection or current_selection not in hierarchy:
        return

    node = hierarchy[current_selection]
    children_codes = node.get('children', [])

    if not children_codes:
        return

    st.markdown("#### 📂 Catégories disponibles")

    # Display category buttons in a grid
    cols = st.columns(min(3, len(children_codes)))

    for idx, child_code in enumerate(children_codes):
        child_node = hierarchy.get(child_code, {})
        child_label = child_node.get('label', child_code)

        col_idx = idx % len(cols)
        with cols[col_idx]:
            is_selected = st.session_state.triangle_selection == child_code

            if st.button(
                f"📁 {child_label}",
                key=f"select_{child_code}",
                use_container_width=True,
                type="primary" if is_selected else "secondary"
            ):
                st.session_state.triangle_selection = child_code
                st.session_state.triangle_label = child_label
                st.session_state.triangle_level = 2
                st.rerun()


def interface_triangle_table_v1() -> None:
    """
    Main interface for Approach 1: Interactive Selection.

    Layout:
    ┌─────────────────────────────────────┐
    │   Fractal Triangle (Top)            │
    │   - Visual hierarchical view        │
    └─────────────────────────────────────┘
    ┌─────────────────────────────────────┐
    │   Interactive Buttons               │
    │   - Click to filter                 │
    └─────────────────────────────────────┘
    ┌─────────────────────────────────────┐
    │   Selection Info & Stats            │
    └─────────────────────────────────────┘
    ┌─────────────────────────────────────┐
    │   Transaction Table (Below)         │
    │   - Auto-filters based on selection │
    └─────────────────────────────────────┘
    """

    # Initialize session state
    init_session_state()

    st.set_page_config(page_title="📊 Triangle & Table (Approach 1)", layout="wide")
    st.title("📊 Triangle & Table - Interactive Selection")

    # Help section
    with st.expander("ℹ️ Comment utiliser ?", expanded=False):
        st.markdown("""
        ### Approach 1: Interactive Selection ✨

        Cette approche permet une interaction intuitive entre les triangles et la table :

        1. **Visualisez la structure hiérarchique** avec les triangles fractals
        2. **Cliquez sur les boutons** pour sélectionner une catégorie
        3. **La table se filtre automatiquement** pour afficher les transactions correspondantes
        4. **Les statistiques se mettent à jour** en temps réel
        5. **Cliquez sur "Réinitialiser"** pour voir toutes les transactions

        #### Avantages:
        - ✅ Interface intuitive et fluide
        - ✅ Feedback visuel immédiat
        - ✅ Vue hiérarchique des données
        - ✅ Facile à comprendre
        - ✅ Boutons explicites pour la sélection

        #### Inconvénients:
        - ❌ Nécessite une interaction (clics)
        - ❌ Une seule sélection à la fois
        """)

    st.markdown("---")

    # === SECTION 1: FRACTAL TRIANGLES ===
    st.subheader("🔺 Visualisation hiérarchique (Triangle Fractal)")

    # Load hierarchy
    hierarchy = build_fractal_hierarchy()

    # Display triangle component
    fractal_navigation(hierarchy, key="fractal_v1_interactive", height=500)

    st.markdown("---")

    # === SECTION 2: SELECTION BUTTONS ===
    col1, col2 = st.columns([2, 1])

    with col1:
        display_hierarchy_buttons(hierarchy)

    # Display categories if a type is selected
    if st.session_state.triangle_selection in ['REVENUS', 'DEPENSES']:
        display_category_buttons(hierarchy, st.session_state.triangle_selection)

    st.markdown("---")

    # === SECTION 3: SELECTION INFO ===
    display_selection_info(
        st.session_state.triangle_selection,
        st.session_state.triangle_label
    )

    st.markdown("---")

    # === SECTION 4: LOAD DATA ===
    df_all = load_transactions()

    if df_all.empty:
        st.warning("📭 Aucune transaction dans la base de données")
        return

    # === SECTION 5: FILTER DATA ===
    df_filtered = filter_transactions_by_selection(
        df_all,
        st.session_state.triangle_selection
    )

    # === SECTION 6: DISPLAY STATS ===
    st.subheader("📈 Statistiques")
    display_stats(df_filtered)

    st.markdown("---")

    # === SECTION 7: DISPLAY TABLE ===
    st.subheader("📋 Transactions")
    display_transactions_table(df_filtered, st.session_state.triangle_selection)

    # === DEBUGGING: Show current state ===
    with st.expander("🔧 Déboguer l'état", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write("**Sélection actuelle:**")
            st.code(st.session_state.triangle_selection or "None")
        with col2:
            st.write("**Label:**")
            st.code(st.session_state.triangle_label or "None")
        with col3:
            st.write("**Niveau:**")
            st.code(str(st.session_state.triangle_level) if st.session_state.triangle_level else "None")

        st.write("**Transactions filtrées:**")
        st.write(f"Total: {len(df_filtered)} sur {len(df_all)}")

        st.write("**Codes disponibles dans la hiérarchie:**")
        st.code(", ".join(hierarchy.keys()))


if __name__ == "__main__":
    interface_triangle_table_v1()
