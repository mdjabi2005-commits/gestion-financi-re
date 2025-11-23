"""
Triangle & Table - Approach 2: Side-by-Side Layout

This module implements Approach 2 for linking the triangle visualization with transaction table.
Triangles are on the left (40% width), table is on the right (60% width).
Both refresh together as the user navigates.

Features:
- Triangle navigation on the left side
- Transaction table on the right side
- Both views update simultaneously
- More screen space for each component

@author: djabi
@version: 1.0
@date: 2025-11-23
"""

import streamlit as st
import pandas as pd
from typing import Optional, Dict, Any

from modules.services.fractal_service import build_fractal_hierarchy
from modules.ui.fractal_component import fractal_navigation
from modules.ui.helpers import load_transactions
from modules.utils.converters import safe_convert


def init_session_state():
    """Initialize session state variables for side-by-side layout."""
    if 'triangle_selection_v2' not in st.session_state:
        st.session_state.triangle_selection_v2 = None
    if 'triangle_level_v2' not in st.session_state:
        st.session_state.triangle_level_v2 = None
    if 'triangle_label_v2' not in st.session_state:
        st.session_state.triangle_label_v2 = None


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

    selection_lower = selection.lower()

    # Level 1: Transaction type
    if selection_lower == 'revenus':
        return df[df['type'].str.lower() == 'revenu'].copy()
    elif selection_lower == 'depenses':
        return df[df['type'].str.lower() == 'dépense'].copy()

    # Level 2 & 3: Category/Subcategory
    if selection.startswith('CAT_'):
        category = selection[4:].replace('_', ' ').title()
        return df[df['categorie'].str.lower() == category.lower()].copy()

    if selection.startswith('SUBCAT_'):
        parts = selection[7:].split('_')
        if len(parts) >= 2:
            category = parts[0].title()
            subcategory = '_'.join(parts[1:]).replace('_', ' ').title()
            return df[
                (df['categorie'].str.lower() == category.lower()) &
                (df['sous_categorie'].str.lower() == subcategory.lower())
            ].copy()

    return df.copy()


def display_stats_compact(df: pd.DataFrame):
    """Display compact statistics for side-by-side layout."""
    if df.empty:
        st.info("📭 Aucune transaction")
        return

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("📊 Transactions", len(df))

    with col2:
        revenus = df[df['type'].str.lower() == 'revenu']['montant'].sum()
        st.metric("💹 Revenus", f"{revenus:,.0f}€")

    with col3:
        depenses = df[df['type'].str.lower() == 'dépense']['montant'].sum()
        st.metric("💸 Dépenses", f"{depenses:,.0f}€")


def display_transactions_table_compact(df: pd.DataFrame):
    """
    Display filtered transactions in compact format for side-by-side layout.

    Args:
        df: Filtered transactions dataframe
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

    # Signed amount
    df_display["Montant"] = df_display.apply(
        lambda row: row["montant"] if row["type"].lower() == "revenu" else -row["montant"],
        axis=1
    )

    # Display table (smaller height for side-by-side)
    st.dataframe(
        df_display[["Type", "Date", "categorie", "sous_categorie", "Montant"]].rename(
            columns={
                "categorie": "Catégorie",
                "sous_categorie": "Sous-cat.",
                "Montant": "Montant (€)"
            }
        ),
        use_container_width=True,
        height=400,
        hide_index=True,
        column_config={
            "Montant (€)": st.column_config.NumberColumn("Montant (€)", format="%.2f €")
        }
    )


def display_type_selector_v2():
    """Display transaction type selector for v2."""
    st.markdown("### 📁 Filtrer par Type")

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "💼 Revenus",
            key="select_type_revenus_v2",
            use_container_width=True,
            type="primary" if st.session_state.triangle_selection_v2 == 'REVENUS' else "secondary"
        ):
            st.session_state.triangle_selection_v2 = 'REVENUS'
            st.session_state.triangle_label_v2 = 'Revenus'
            st.session_state.triangle_level_v2 = 1
            st.rerun()

    with col2:
        if st.button(
            "🛒 Dépenses",
            key="select_type_depenses_v2",
            use_container_width=True,
            type="primary" if st.session_state.triangle_selection_v2 == 'DEPENSES' else "secondary"
        ):
            st.session_state.triangle_selection_v2 = 'DEPENSES'
            st.session_state.triangle_label_v2 = 'Dépenses'
            st.session_state.triangle_level_v2 = 1
            st.rerun()

    st.markdown("---")


def interface_triangle_table_v2() -> None:
    """
    Main interface for Approach 2: Side-by-Side Layout.

    Layout:
    ┌─────────────────────────────────────────────────────────────┐
    │ Title: Triangle & Table - Side-by-Side                      │
    ├──────────────────────┬──────────────────────────────────────┤
    │   LEFT (40%)         │   RIGHT (60%)                        │
    │   - Triangles        │   - Selection buttons (compact)      │
    │   - Navigation       │   - Statistics                       │
    │   - Info panel       │   - Transaction table                │
    │                      │   - Auto-updates                     │
    └──────────────────────┴──────────────────────────────────────┘
    """

    # Initialize session state
    init_session_state()

    st.set_page_config(page_title="📊 Triangle & Table (Approach 2)", layout="wide")
    st.title("📊 Triangle & Table - Side-by-Side Layout")

    # Help section
    with st.expander("ℹ️ Comment utiliser ?", expanded=False):
        st.markdown("""
        ### Approach 2: Side-by-Side Layout 📐

        Cette approche affiche les triangles et la table côte à côte :

        1. **Triangle à gauche** - Vue hiérarchique complète avec navigation
        2. **Table à droite** - Transactions correspondantes avec statistiques
        3. **Mise à jour automatique** - La table se rafraîchit selon votre sélection
        4. **Les deux vues se complètent** - Plus de contexte visible à la fois

        #### Avantages:
        - ✅ Voir triangles et table simultanément
        - ✅ Moins de scrolling vertical
        - ✅ Comparaison plus facile
        - ✅ Interface de tableau de bord

        #### Inconvénients:
        - ❌ Moins d'espace pour chaque composant
        - ❌ Peut être dense sur petits écrans
        """)

    st.markdown("---")

    # === LOAD DATA ONCE ===
    df_all = load_transactions()
    hierarchy = build_fractal_hierarchy()

    if df_all.empty:
        st.warning("📭 Aucune transaction dans la base de données")
        return

    # === MAIN LAYOUT: LEFT + RIGHT ===
    left_col, right_col = st.columns([2, 3], gap="medium")

    # === LEFT COLUMN: TRIANGLES + NAVIGATION ===
    with left_col:
        st.markdown("### 🔺 Hiérarchie Fractale")

        # Display triangle component (smaller height for side-by-side)
        fractal_navigation(hierarchy, key="fractal_v2_sidebyside", height=400)

        st.markdown("---")

        # Type selector
        display_type_selector_v2()

        # Show current selection
        if st.session_state.triangle_selection_v2:
            st.success(f"✅ Sélection: **{st.session_state.triangle_label_v2}**")

            if st.button("❌ Réinitialiser", key="reset_v2", use_container_width=True):
                st.session_state.triangle_selection_v2 = None
                st.session_state.triangle_label_v2 = None
                st.session_state.triangle_level_v2 = None
                st.rerun()
        else:
            st.info("👆 Sélectionnez une catégorie pour filtrer")

    # === RIGHT COLUMN: TABLE + STATS ===
    with right_col:
        # Filter data
        df_filtered = filter_transactions_by_selection(
            df_all,
            st.session_state.triangle_selection_v2
        )

        # Display statistics
        st.markdown("### 📈 Statistiques")
        display_stats_compact(df_filtered)

        st.markdown("---")

        # Display table
        st.markdown("### 📋 Transactions")
        display_transactions_table_compact(df_filtered)

        # Additional info
        with st.expander("ℹ️ Détails"):
            st.write(f"**Affichage:** {len(df_filtered)} transaction(s) sur {len(df_all)} total(s)")

            if st.session_state.triangle_selection_v2:
                st.write(f"**Filtre actif:** {st.session_state.triangle_label_v2}")
            else:
                st.write("**Filtre:** Aucun (toutes les transactions)")


if __name__ == "__main__":
    interface_triangle_table_v2()
