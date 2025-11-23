"""
Triangle & Table - UNIFIED FINAL INTERFACE

Version finale unifiée avec:
- Navigation UNIQUEMENT par triangles fractals animés
- Affichage du tableau seulement au dernier niveau
- Filtres persistants même à la racine
- Multi-sélection avec ajout/suppression de sous-catégories
- Un seul ensemble cohérent

@author: djabi
@version: 5.0 (Unified Final)
@date: 2025-11-23
"""

import streamlit as st
import pandas as pd
from typing import Optional, Dict, Any, List

from modules.services.fractal_service import build_fractal_hierarchy
from modules.ui.fractal_component import fractal_navigation
from modules.ui.helpers import load_transactions
from modules.utils.converters import safe_convert


# ===== CONFIGURATION =====
FRACTAL_HEIGHT = 700  # Height of fractal visualization


def init_state():
    """Initialize session state for unified interface."""
    if 'nav_stack' not in st.session_state:
        st.session_state.nav_stack = ['TR']  # Navigation stack
    if 'selected_subcats' not in st.session_state:
        st.session_state.selected_subcats = set()  # Persistent filters
    if 'show_help' not in st.session_state:
        st.session_state.show_help = True


def get_current_node(hierarchy: Dict) -> Dict[str, Any]:
    """Get the current node based on navigation stack."""
    current_code = st.session_state.nav_stack[-1]
    return hierarchy.get(current_code, {})


def get_children_nodes(hierarchy: Dict, node: Dict) -> List[tuple]:
    """Get children of current node as list of (code, node_data)."""
    children_codes = node.get('children', [])
    children = []
    for code in children_codes:
        child = hierarchy.get(code, {})
        children.append((code, child))
    return children


def is_last_level(hierarchy: Dict, node: Dict) -> bool:
    """Check if this is the last navigable level."""
    children = get_children_nodes(hierarchy, node)
    if not children:
        return False

    # Last level if ALL children have no children
    for _, child in children:
        if child.get('children'):
            return False
    return True


def get_transactions_for_category(df: pd.DataFrame, code: str) -> pd.DataFrame:
    """Get transactions for a specific code."""
    if code.startswith('SUBCAT_'):
        parts = code[7:].split('_', 1)
        if len(parts) == 2:
            category = parts[0].title()
            subcategory = parts[1].replace('_', ' ').title()
            return df[
                (df['categorie'].str.lower() == category.lower()) &
                (df['sous_categorie'].str.lower() == subcategory.lower())
            ]
    elif code.startswith('CAT_'):
        category = code[4:].replace('_', ' ').title()
        return df[df['categorie'].str.lower() == category.lower()]
    elif code == 'REVENUS':
        return df[df['type'].str.lower() == 'revenu']
    elif code == 'DEPENSES':
        return df[df['type'].str.lower() == 'dépense']

    return pd.DataFrame()


def navigate_to(code: str):
    """Navigate to a specific node."""
    st.session_state.nav_stack.append(code)


def go_back():
    """Go back one level."""
    if len(st.session_state.nav_stack) > 1:
        st.session_state.nav_stack.pop()
    st.rerun()


def reset_filters():
    """Reset filters only (keep navigation at root)."""
    st.session_state.nav_stack = ['TR']
    st.session_state.selected_subcats = set()
    st.rerun()


def toggle_subcat(code: str):
    """Toggle subcategory selection."""
    if code in st.session_state.selected_subcats:
        st.session_state.selected_subcats.discard(code)
    else:
        st.session_state.selected_subcats.add(code)
    st.rerun()


def display_table(df: pd.DataFrame):
    """Display filtered transactions."""
    if df.empty:
        st.info("📭 Aucune transaction")
        return

    # Prepare
    df_display = df.copy()
    df_display["montant"] = df_display["montant"].apply(lambda x: safe_convert(x, float, 0.0))
    df_display["Type"] = df_display["type"].apply(lambda x: "💹" if x.lower() == "revenu" else "💸")
    df_display["Date"] = pd.to_datetime(df_display["date"]).dt.strftime("%d/%m/%Y")
    df_display["Montant"] = df_display.apply(
        lambda row: row["montant"] if row["type"].lower() == "revenu" else -row["montant"],
        axis=1
    )

    # Display
    st.dataframe(
        df_display[["Type", "Date", "categorie", "sous_categorie", "Montant"]].rename(
            columns={
                "categorie": "Catégorie",
                "sous_categorie": "Sous-catégorie"
            }
        ),
        use_container_width=True,
        height=400,
        hide_index=True,
        column_config={
            "Montant": st.column_config.NumberColumn("Montant (€)", format="%.2f €")
        }
    )

    # Export
    csv = df_display.to_csv(index=False).encode('utf-8')
    st.download_button(
        "💾 Exporter CSV",
        csv,
        "transactions.csv",
        "text/csv",
        use_container_width=True
    )


def display_active_filters(hierarchy: Dict):
    """Display active filters as badges."""
    if not st.session_state.selected_subcats:
        return

    st.markdown("### 🎯 Filtres Actifs")

    filter_labels = []
    for code in st.session_state.selected_subcats:
        node = hierarchy.get(code, {})
        label = node.get('label', code)
        filter_labels.append(f"**{label}**")

    st.info(f"📊 Filtres appliqués: {', '.join(filter_labels)}")

    # Remove individual filters
    st.markdown("**Gérer les filtres:**")
    cols = st.columns(len(st.session_state.selected_subcats) + 1)

    for idx, code in enumerate(sorted(st.session_state.selected_subcats)):
        node = hierarchy.get(code, {})
        label = node.get('label', code)

        with cols[idx]:
            if st.button(f"❌ {label}", use_container_width=True, key=f"remove_{code}"):
                toggle_subcat(code)

    # Global reset
    with cols[len(st.session_state.selected_subcats)]:
        if st.button("🔄 Réinitialiser tout", use_container_width=True):
            reset_filters()


def interface_triangle_table_unified_final():
    """Main unified interface with fractal triangles and persistent filters."""
    init_state()

    st.set_page_config(
        page_title="Navigation Fractale Unifiée",
        layout="wide"
    )

    st.title("🔺 Navigation Fractale Unifiée")

    # Load data
    hierarchy = build_fractal_hierarchy()
    df_all = load_transactions()

    if df_all.empty:
        st.error("Aucune transaction dans la base")
        return

    # Get current node
    current_code = st.session_state.nav_stack[-1]
    current_node = get_current_node(hierarchy)
    level = len(st.session_state.nav_stack)
    children = get_children_nodes(hierarchy, current_node)
    is_last = is_last_level(hierarchy, current_node)

    # ===== HELP =====
    if st.session_state.show_help:
        with st.expander("ℹ️ Comment utiliser ?", expanded=True):
            st.markdown("""
            ### Navigation Fractale Unifiée

            **Flux:**
            1. Observez les triangles fractals qui changent en naviguant
            2. Cliquez sur les triangles pour naviguer en profondeur
            3. Au dernier niveau, cliquez pour SÉLECTIONNER des sous-catégories
            4. Le tableau affiche les transactions filtrées (logique AND)
            5. Les filtres restent actifs même si vous remontez à la racine
            6. Continuez à naviguer pour ajouter ou retirer des filtres

            **Interactions:**
            - Clic triangle: Naviguer ou sélectionner (selon le niveau)
            - Tableau: Visible seulement au dernier niveau
            - Filtres: Persistent, modifiables via les triangles
            - Export: CSV des données filtrées
            """)
            st.session_state.show_help = False

    st.markdown("---")

    # ===== SECTION 1: NAVIGATION CONTROLS =====
    col1, col2, col3 = st.columns([4, 1, 1])

    with col1:
        st.write(f"**Niveau {level}:** {current_node.get('label', current_code)}")

    with col2:
        if level > 1:
            if st.button("← Retour", use_container_width=True):
                go_back()

    with col3:
        if st.session_state.selected_subcats:
            if st.button("❌ Filtres", use_container_width=True):
                reset_filters()

    st.markdown("---")

    # ===== SECTION 2: ANIMATED FRACTAL TRIANGLES (FULL WIDTH) =====
    st.markdown("### 🔺 Navigation Visuelle")

    with st.container():
        fractal_navigation(hierarchy, key='unified_fractal', height=FRACTAL_HEIGHT)

    st.markdown("**Mode:** " + ("🎯 Sélection (cliquez pour ajouter/retirer des filtres)" if is_last else "➡️ Navigation (cliquez pour explorer)"))

    # ===== SECTION 2B: INTERACTION BUTTONS (SYNCHRONIZED WITH TRIANGLES) =====
    if children:
        st.markdown(f"### Catégories: {current_node.get('label', 'Options')}")

        cols = st.columns(min(3, len(children)))

        for idx, (code, child) in enumerate(children):
            label = child.get('label', code)
            col_idx = idx % len(cols)
            amount = child.get('total', 0)

            with cols[col_idx]:
                if is_last:
                    # Selection mode
                    is_selected = code in st.session_state.selected_subcats
                    button_style = "✓" if is_selected else "○"
                    button_label = f"{button_style} {label}"

                    if st.button(
                        button_label,
                        key=f"btn_{code}",
                        use_container_width=True,
                        type="primary" if is_selected else "secondary"
                    ):
                        toggle_subcat(code)
                else:
                    # Navigation mode
                    if st.button(
                        f"➡️ {label}",
                        key=f"btn_{code}",
                        use_container_width=True,
                        type="primary"
                    ):
                        navigate_to(code)

                st.caption(f"💰 {amount:,.0f}€")

    st.markdown("---")

    # ===== SECTION 3: DYNAMIC CONTENT =====
    st.markdown("## 📊 Données")

    # Case 1: Root without filters - Show global stats
    if current_code == 'TR' and not st.session_state.selected_subcats:
        st.info("👇 Naviguez dans les triangles et sélectionnez pour filtrer")

        col1, col2 = st.columns(2)
        with col1:
            revenus = hierarchy.get('REVENUS', {}).get('total', 0)
            st.metric("💰 Revenus", f"{revenus:,.0f}€")
        with col2:
            depenses = hierarchy.get('DEPENSES', {}).get('total', 0)
            st.metric("💸 Dépenses", f"{depenses:,.0f}€")

    # Case 2: With active filters - Show filtered data
    elif st.session_state.selected_subcats:
        display_active_filters(hierarchy)

        st.markdown("---")

        # Calculate stats
        selected_dfs = []
        total_count = 0
        total_revenus = 0
        total_depenses = 0

        for subcat_code in st.session_state.selected_subcats:
            cat_df = get_transactions_for_category(df_all, subcat_code)
            if not cat_df.empty:
                selected_dfs.append(cat_df)
                total_count += len(cat_df)
                total_revenus += cat_df[cat_df['type'].str.lower() == 'revenu']['montant'].sum()
                total_depenses += cat_df[cat_df['type'].str.lower() == 'dépense']['montant'].sum()

        # Display metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("📋 Transactions", total_count)

        with col2:
            st.metric("💹 Revenus", f"{total_revenus:,.0f}€")

        with col3:
            st.metric("💸 Dépenses", f"{abs(total_depenses):,.0f}€")

        with col4:
            solde = total_revenus + total_depenses
            st.metric("📈 Solde", f"{solde:,.0f}€")

        st.markdown("---")

        # Display table
        if selected_dfs:
            df_combined = pd.concat(selected_dfs, ignore_index=True)
            st.markdown("### 📋 Transactions Filtrées")
            display_table(df_combined)

    # Case 3: At last level without selection
    elif is_last:
        st.info("👆 Cliquez sur les triangles pour sélectionner des sous-catégories")

        col1, col2 = st.columns(2)
        with col1:
            total = current_node.get('total', 0)
            st.metric("💰 Montant total", f"{total:,.0f}€")
        with col2:
            children_count = len(children)
            st.metric("📂 Sous-catégories", children_count)

    # Case 4: Intermediate level
    else:
        st.info("👇 Continuez à naviguer dans les triangles")

        col1, col2 = st.columns(2)
        with col1:
            total = current_node.get('total', 0)
            st.metric("💰 Montant total", f"{total:,.0f}€")
        with col2:
            children_count = len(children)
            st.metric("📂 Catégories", children_count)


if __name__ == "__main__":
    interface_triangle_table_unified_final()
