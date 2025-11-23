"""
Triangle & Table - FINAL UNIFIED INTERFACE

Version finale et fonctionnelle avec navigation vraie + sélection + tableau.

Flow:
1. Afficher triangles au niveau actuel
2. Clic sur triangle = naviguer EN PROFONDEUR
3. Au dernier niveau = mode sélection (multi-select possible)
4. Afficher tableau avec transactions des sélections
5. Bouton "Retour" = réinitialiser tout

@author: djabi
@version: 3.0 (Final Working Version)
@date: 2025-11-23
"""

import streamlit as st
import pandas as pd
from typing import Optional, Dict, Any, List

from modules.services.fractal_service import build_fractal_hierarchy
from modules.ui.fractal_component import fractal_navigation
from modules.ui.helpers import load_transactions
from modules.utils.converters import safe_convert


def init_state():
    """Initialize navigation state."""
    if 'nav_stack' not in st.session_state:
        st.session_state.nav_stack = ['TR']  # Stack de navigation
    if 'selected_subcats' not in st.session_state:
        st.session_state.selected_subcats = set()  # Sous-catégories sélectionnées


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

    # Dernier niveau si TOUS les enfants n'ont pas d'enfants
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
    st.session_state.selected_subcats = set()  # Reset selections


def go_back():
    """Go back one level."""
    if len(st.session_state.nav_stack) > 1:
        st.session_state.nav_stack.pop()
        st.session_state.selected_subcats = set()
    st.rerun()


def reset():
    """Reset to root."""
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


def display_triangles_as_buttons(hierarchy: Dict, children: List[tuple],
                                  is_selection_mode: bool):
    """Display children as interactive buttons/triangles."""
    cols = st.columns(min(3, len(children)))

    for idx, (code, child) in enumerate(children):
        label = child.get('label', code)
        col_idx = idx % len(cols)

        with cols[col_idx]:
            is_selected = code in st.session_state.selected_subcats

            if is_selection_mode:
                # Mode sélection: button avec toggle
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
                # Mode navigation: button pour naviguer
                if st.button(
                    f"→ {label}",
                    key=f"btn_{code}",
                    use_container_width=True,
                    type="primary"
                ):
                    navigate_to(code)

            # Show amount
            amount = child.get('total', 0)
            st.caption(f"💰 {amount:,.0f}€")


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


def interface_triangle_table_final():
    """Main interface."""
    init_state()

    st.set_page_config(
        page_title="Navigation Fractale - Final",
        layout="wide"
    )

    st.title("🔺 Navigation Fractale avec Tableau")

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

    # ===== HAUT: TRIANGLES =====
    st.markdown("## 🔺 Navigation")

    col1, col2, col3 = st.columns([3, 1, 1])

    with col1:
        st.write(f"**Niveau {level}:** {current_node.get('label', current_code)}")

    with col2:
        if level > 1:
            if st.button("← Retour", use_container_width=True):
                go_back()

    with col3:
        if level > 1:
            if st.button("🏠 Racine", use_container_width=True):
                reset()

    # Afficher les boutons pour les enfants
    if children:
        st.markdown(f"### {current_node.get('label', 'Options')}")
        display_triangles_as_buttons(hierarchy, children, is_last)
    else:
        st.info("Aucune sous-catégorie")

    st.markdown("---")

    # ===== BAS: CONTENU DYNAMIQUE =====
    st.markdown("## 📊 Données")

    # Cas 1: Niveau racine
    if current_code == 'TR':
        st.info("👇 Cliquez sur une catégorie pour naviguer")

        col1, col2 = st.columns(2)
        with col1:
            revenus = hierarchy.get('REVENUS', {}).get('total', 0)
            st.metric("💰 Revenus", f"{revenus:,.0f}€")
        with col2:
            depenses = hierarchy.get('DEPENSES', {}).get('total', 0)
            st.metric("💸 Dépenses", f"{depenses:,.0f}€")

    # Cas 2: Niveau intermédiaire (pas de sélection)
    elif not is_last:
        st.info("👇 Continuez à naviguer")

        total = current_node.get('total', 0)
        children_count = len(children)

        col1, col2 = st.columns(2)
        with col1:
            st.metric("💰 Montant total", f"{total:,.0f}€")
        with col2:
            st.metric("📂 Catégories", children_count)

    # Cas 3: Dernier niveau (avec sélection)
    else:
        if not st.session_state.selected_subcats:
            st.info("👆 Sélectionnez des sous-catégories ci-dessus")
        else:
            # Calculer les stats
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

            # Afficher metrics
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

            # Afficher tableau
            if selected_dfs:
                df_combined = pd.concat(selected_dfs, ignore_index=True)
                st.markdown("### 📋 Transactions Sélectionnées")
                display_table(df_combined)


if __name__ == "__main__":
    interface_triangle_table_final()
