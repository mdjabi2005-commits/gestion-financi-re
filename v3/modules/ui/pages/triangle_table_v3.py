"""
Triangle & Table - Approach 3: Multi-Filter with Interactive Triangles

This module implements a multi-filter approach where users can click directly on triangles
to select multiple categories. The table filters using AND logic (all selected categories).

Features:
- Interactive triangle selection (click to select/deselect)
- Multi-category filtering (AND logic)
- Visual feedback (color change on selection)
- Real-time statistics with breakdown
- Efficient filtering

@author: djabi
@version: 1.0
@date: 2025-11-23
"""

import streamlit as st
import pandas as pd
from typing import Optional, Dict, Any, List, Set
import json

from modules.services.fractal_service import build_fractal_hierarchy
from modules.ui.fractal_component import fractal_navigation
from modules.ui.helpers import load_transactions
from modules.utils.converters import safe_convert


def init_session_state():
    """Initialize session state for multi-filter approach."""
    if 'selected_categories_v3' not in st.session_state:
        st.session_state.selected_categories_v3 = set()  # Store as set for O(1) lookup


def get_category_code_from_label(hierarchy: Dict[str, Any], label: str) -> Optional[str]:
    """Find category code by label in hierarchy."""
    for code, node in hierarchy.items():
        if node.get('label') == label:
            return code
    return None


def get_all_categories_from_hierarchy(hierarchy: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Extract all category nodes (CAT_* and SUBCAT_*) from hierarchy.

    Returns dict: {code: node_data, ...}
    """
    categories = {}

    for code, node in hierarchy.items():
        # Include both categories and subcategories, but not types or root
        if code.startswith('CAT_') or code.startswith('SUBCAT_'):
            categories[code] = node

    return categories


def filter_transactions_by_categories(df: pd.DataFrame, selected_codes: Set[str],
                                      hierarchy: Dict[str, Any]) -> pd.DataFrame:
    """
    Filter transactions using AND logic:
    Only include if ALL selected categories match.

    Args:
        df: Complete transactions dataframe
        selected_codes: Set of selected category codes
        hierarchy: Hierarchy data for code-to-label mapping

    Returns:
        Filtered dataframe
    """
    if not selected_codes or df.empty:
        return df.copy()

    # Start with all rows
    result_df = df.copy()

    # Apply AND filter: row must match ALL selected categories
    for code in selected_codes:
        node = hierarchy.get(code, {})

        if code.startswith('CAT_'):
            # Extract category name from code
            category = code[4:].replace('_', ' ').title()
            result_df = result_df[result_df['categorie'].str.lower() == category.lower()]

        elif code.startswith('SUBCAT_'):
            # Extract category and subcategory from code
            parts = code[7:].split('_', 1)
            if len(parts) == 2:
                category = parts[0].title()
                subcategory = parts[1].replace('_', ' ').title()
                result_df = result_df[
                    (result_df['categorie'].str.lower() == category.lower()) &
                    (result_df['sous_categorie'].str.lower() == subcategory.lower())
                ]

    return result_df


def display_interactive_triangles(hierarchy: Dict[str, Any],
                                  selected_codes: Set[str]) -> Dict[str, Any]:
    """
    Display triangles as interactive buttons with visual feedback.

    Returns:
        Updated selected_codes after user interactions
    """
    st.markdown("### 🔺 Sélectionnez les catégories (Cliquez sur les triangles)")

    # Get all categories
    categories = get_all_categories_from_hierarchy(hierarchy)

    if not categories:
        st.info("Aucune catégorie disponible")
        return selected_codes

    # Group by parent for better organization
    categories_by_parent = {}
    for code, node in categories.items():
        parent = node.get('parent', 'root')
        if parent not in categories_by_parent:
            categories_by_parent[parent] = []
        categories_by_parent[parent].append((code, node))

    # Display categories grouped
    for parent_code in sorted(categories_by_parent.keys()):
        cat_group = categories_by_parent[parent_code]

        # Show parent label if available
        if parent_code != 'root':
            parent_node = hierarchy.get(parent_code, {})
            parent_label = parent_node.get('label', parent_code)
            st.markdown(f"#### 📂 {parent_label}")

        # Display category buttons in grid
        cols = st.columns(min(4, len(cat_group)))

        for idx, (code, node) in enumerate(cat_group):
            is_selected = code in selected_codes
            label = node.get('label', code)
            color = "background-color: #10b981;" if is_selected else ""

            col_idx = idx % len(cols)
            with cols[col_idx]:
                # Create a button with visual feedback
                button_style = "✅ " if is_selected else "⭕ "
                button_text = f"{button_style}{label}"

                if st.button(
                    button_text,
                    key=f"triangle_{code}",
                    use_container_width=True,
                    type="primary" if is_selected else "secondary"
                ):
                    # Toggle selection
                    if code in selected_codes:
                        selected_codes.discard(code)
                    else:
                        selected_codes.add(code)

                    st.rerun()

    return selected_codes


def display_selection_summary(selected_codes: Set[str], hierarchy: Dict[str, Any]):
    """Display summary of selected categories."""
    if not selected_codes:
        st.info("👆 Cliquez sur les triangles pour sélectionner des catégories")
        return

    selected_labels = []
    for code in sorted(selected_codes):
        node = hierarchy.get(code, {})
        label = node.get('label', code)
        selected_labels.append(f"• {label}")

    col1, col2 = st.columns([3, 1])

    with col1:
        st.success(f"✅ **{len(selected_codes)} catégorie(s) sélectionnée(s):**\n\n" +
                   "\n".join(selected_labels))

    with col2:
        if st.button("❌ Réinitialiser", key="reset_v3", use_container_width=True):
            st.session_state.selected_categories_v3 = set()
            st.rerun()


def calculate_stats_by_category(df: pd.DataFrame, selected_codes: Set[str],
                                hierarchy: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Calculate statistics for each selected category.

    Returns:
        Dict with stats per category
    """
    stats = {}

    for code in selected_codes:
        node = hierarchy.get(code, {})
        label = node.get('label', code)

        # Filter for this category
        if code.startswith('CAT_'):
            category = code[4:].replace('_', ' ').title()
            cat_df = df[df['categorie'].str.lower() == category.lower()]

        elif code.startswith('SUBCAT_'):
            parts = code[7:].split('_', 1)
            if len(parts) == 2:
                category = parts[0].title()
                subcategory = parts[1].replace('_', ' ').title()
                cat_df = df[
                    (df['categorie'].str.lower() == category.lower()) &
                    (df['sous_categorie'].str.lower() == subcategory.lower())
                ]

        if not cat_df.empty:
            revenus = cat_df[cat_df['type'].str.lower() == 'revenu']['montant'].sum()
            depenses = cat_df[cat_df['type'].str.lower() == 'dépense']['montant'].sum()

            stats[label] = {
                'count': len(cat_df),
                'revenus': revenus,
                'depenses': depenses,
                'solde': revenus - depenses
            }

    return stats


def display_stats_breakdown(stats: Dict[str, Dict[str, Any]]):
    """Display statistics breakdown by selected category."""
    if not stats:
        st.info("Aucune statistique à afficher")
        return

    st.markdown("### 📊 Statistiques par Catégorie")

    # Create columns for each category
    cols = st.columns(min(3, len(stats)))

    for idx, (category, cat_stats) in enumerate(stats.items()):
        col_idx = idx % len(cols)
        with cols[col_idx]:
            st.metric(
                category,
                f"{cat_stats['count']} trans.",
                f"Solde: {cat_stats['solde']:,.0f}€"
            )

    # Overall stats
    st.markdown("### 📈 Totaux Globaux")

    total_count = sum(s['count'] for s in stats.values())
    total_revenus = sum(s['revenus'] for s in stats.values())
    total_depenses = sum(s['depenses'] for s in stats.values())
    total_solde = total_revenus - total_depenses

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("📊 Total Transactions", total_count)

    with col2:
        st.metric("💹 Revenus", f"{total_revenus:,.0f}€")

    with col3:
        st.metric("💸 Dépenses", f"{total_depenses:,.0f}€")

    with col4:
        st.metric("📈 Solde", f"{total_solde:,.0f}€")


def display_filtered_table(df: pd.DataFrame):
    """Display the filtered transactions table."""
    if df.empty:
        st.warning("📭 Aucune transaction ne correspond à tous les critères sélectionnés")
        return

    # Prepare display dataframe
    df_display = df.copy()
    df_display["montant"] = df_display["montant"].apply(lambda x: safe_convert(x, float, 0.0))

    # Add type icon
    df_display["Type"] = df_display["type"].apply(lambda x: "💹" if x.lower() == "revenu" else "💸")

    # Format date
    df_display["Date"] = pd.to_datetime(df_display["date"]).dt.strftime("%d/%m/%Y")

    # Signed amount
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


def interface_triangle_table_v3() -> None:
    """
    Main interface for Approach 3: Multi-Filter with Interactive Triangles.

    Layout:
    ┌─────────────────────────────────────┐
    │   🔺 Interactive Triangles          │
    │   - Click to select multiple        │
    │   - Color change on select          │
    └─────────────────────────────────────┘
            ↓
    ┌─────────────────────────────────────┐
    │   📊 Statistics Breakdown           │
    │   - Per category stats              │
    │   - Overall totals                  │
    └─────────────────────────────────────┘
            ↓
    ┌─────────────────────────────────────┐
    │   📋 Filtered Transactions          │
    │   - AND logic filtering             │
    └─────────────────────────────────────┘
    """

    # Initialize session state
    init_session_state()

    st.set_page_config(page_title="📊 Triangle & Table V3 (Multi-Filter)", layout="wide")
    st.title("📊 Triangle & Table - Multi-Filter avec Triangles Cliquables")

    # Help section
    with st.expander("ℹ️ Comment utiliser ?", expanded=False):
        st.markdown("""
        ### Approach 3: Multi-Filter avec Triangles Cliquables 🎯

        Sélectionnez PLUSIEURS catégories en cliquant sur les triangles.
        La table s'affiche avec les transactions qui match TOUTES les catégories.

        1. **Cliquez sur les triangles** pour les sélectionner
        2. **Changement de couleur** indique la sélection (✅ vert)
        3. **Cliquez à nouveau** pour désélectionner
        4. **La table se filtre** avec logique AND (toutes les catégories)
        5. **Statistiques se mettent à jour** pour chaque sélection
        6. **Cliquez "Réinitialiser"** pour tout effacer

        #### Avantages:
        - ✅ Multi-sélection intuitive
        - ✅ Feedback visuel immédiat
        - ✅ Logique AND puissante
        - ✅ Voir tous les triangles à la fois
        - ✅ Statistiques détaillées par catégorie

        #### Cas d'usage:
        - Analyser transactions communes à plusieurs catégories
        - Comparaison croisée de catégories
        - Données complexes avec filtres multiples
        """)

    st.markdown("---")

    # === LOAD DATA ===
    df_all = load_transactions()
    hierarchy = build_fractal_hierarchy()

    if df_all.empty:
        st.warning("📭 Aucune transaction dans la base de données")
        return

    # === DISPLAY TRIANGLES FOR SELECTION ===
    selected_codes = st.session_state.selected_categories_v3.copy()
    selected_codes = display_interactive_triangles(hierarchy, selected_codes)
    st.session_state.selected_categories_v3 = selected_codes

    st.markdown("---")

    # === DISPLAY SELECTION SUMMARY ===
    display_selection_summary(selected_codes, hierarchy)

    st.markdown("---")

    # === FILTER DATA ===
    df_filtered = filter_transactions_by_categories(df_all, selected_codes, hierarchy)

    # === DISPLAY STATISTICS ===
    if selected_codes:
        stats = calculate_stats_by_category(df_all, selected_codes, hierarchy)
        display_stats_breakdown(stats)

        st.markdown("---")

    # === DISPLAY TABLE ===
    st.subheader("📋 Transactions Filtrées")
    display_filtered_table(df_filtered)

    # === DEBUG SECTION ===
    with st.expander("🔧 Déboguer l'état", expanded=False):
        col1, col2, col3 = st.columns(3)

        with col1:
            st.write("**Catégories sélectionnées:**")
            st.code(str(list(selected_codes)) if selected_codes else "[]")

        with col2:
            st.write("**Nombre de sélections:**")
            st.code(str(len(selected_codes)))

        with col3:
            st.write("**Transactions filtrées:**")
            st.code(f"{len(df_filtered)} / {len(df_all)}")

        st.write("**Catégories disponibles:**")
        categories = get_all_categories_from_hierarchy(hierarchy)
        for code, node in sorted(categories.items()):
            label = node.get('label', code)
            is_sel = "✅" if code in selected_codes else "⭕"
            st.caption(f"{is_sel} {code}: {label}")


if __name__ == "__main__":
    interface_triangle_table_v3()
