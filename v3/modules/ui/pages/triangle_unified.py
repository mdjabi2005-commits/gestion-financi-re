"""
Triangle & Table - UNIFIED INTERFACE

Système de multi-filtrage unifié avec triangles cliquables et tableau dynamique.
Une seule interface cohérente: triangles en haut (60%), table en bas (40%).

Features:
- Navigation hiérarchique (niveaux 1-3)
- Multi-sélection au niveau 3 avec logique AND
- Visual feedback (bordure bleue + checkmark)
- Statistiques dynamiques par catégorie sélectionnée
- Export CSV des données filtrées

@author: djabi
@version: 2.0 (Unified Interface)
@date: 2025-11-23
"""

import streamlit as st
import pandas as pd
from typing import Optional, Dict, Any, List, Set

from modules.services.fractal_service import (
    build_fractal_hierarchy,
    get_transactions_for_node
)
from modules.ui.fractal_component import fractal_navigation
from modules.ui.helpers import load_transactions
from modules.utils.converters import safe_convert


def init_session_state():
    """Initialize session state for unified interface."""
    if 'unified_state' not in st.session_state:
        st.session_state.unified_state = {
            'current_node': 'TR',
            'selected_nodes': set(),
            'level': 1,
            'is_selection_mode': False
        }


def get_transactions_for_codes(codes: List[str], hierarchy: Dict[str, Any]) -> pd.DataFrame:
    """
    Récupérer les transactions pour plusieurs codes (avec logique AND).

    Returns:
        DataFrame avec transactions qui matchent TOUS les codes sélectionnés
    """
    if not codes:
        return load_transactions()

    df_all = load_transactions()
    if df_all.empty:
        return df_all

    # Appliquer AND logic: une transaction doit matcher TOUTES les catégories
    result_df = df_all.copy()

    for code in codes:
        node = hierarchy.get(code, {})

        if code.startswith('CAT_'):
            category = code[4:].replace('_', ' ').title()
            result_df = result_df[result_df['categorie'].str.lower() == category.lower()]

        elif code.startswith('SUBCAT_'):
            parts = code[7:].split('_', 1)
            if len(parts) == 2:
                category = parts[0].title()
                subcategory = parts[1].replace('_', ' ').title()
                result_df = result_df[
                    (result_df['categorie'].str.lower() == category.lower()) &
                    (result_df['sous_categorie'].str.lower() == subcategory.lower())
                ]

    return result_df


def calculate_stats(df: pd.DataFrame, selected_codes: List[str],
                   hierarchy: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Calculate statistics for each selected category."""
    stats = {}
    df_all = load_transactions()

    for code in selected_codes:
        node = hierarchy.get(code, {})
        label = node.get('label', code)

        # Filter for this code
        if code.startswith('CAT_'):
            category = code[4:].replace('_', ' ').title()
            cat_df = df_all[df_all['categorie'].str.lower() == category.lower()]

        elif code.startswith('SUBCAT_'):
            parts = code[7:].split('_', 1)
            if len(parts) == 2:
                category = parts[0].title()
                subcategory = parts[1].replace('_', ' ').title()
                cat_df = df_all[
                    (df_all['categorie'].str.lower() == category.lower()) &
                    (df_all['sous_categorie'].str.lower() == subcategory.lower())
                ]

        if not cat_df.empty:
            revenus = cat_df[cat_df['type'].str.lower() == 'revenu']['montant'].sum()
            depenses = cat_df[cat_df['type'].str.lower() == 'dépense']['montant'].sum()

            stats[label] = {
                'count': len(cat_df),
                'revenus': revenus,
                'depenses': depenses,
                'solde': revenus + depenses  # depenses est négatif
            }

    return stats


def display_table(df: pd.DataFrame, title: str = ""):
    """Display transactions table."""
    if df.empty:
        st.info("📭 Aucune transaction ne correspond à cette sélection")
        return

    # Prepare display
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
        df_display[["Type", "Date", "categorie", "sous_categorie", "Montant", "description"]].rename(
            columns={
                "categorie": "Catégorie",
                "sous_categorie": "Sous-catégorie",
                "description": "Description"
            }
        ),
        use_container_width=True,
        height=400,
        hide_index=True,
        column_config={
            "Montant": st.column_config.NumberColumn("Montant (€)", format="%.2f €")
        }
    )

    # Export button
    csv = df_display.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="💾 Exporter en CSV",
        data=csv,
        file_name="transactions_filtrees.csv",
        mime="text/csv",
        use_container_width=True
    )


def display_level1_content(hierarchy: Dict[str, Any]):
    """Display content for level 1 (Root)."""
    st.info("🔍 **Naviguez dans les triangles pour explorer vos finances**")

    # Global stats
    col1, col2, col3 = st.columns(3)

    with col1:
        revenus_node = hierarchy.get('REVENUS', {})
        total_revenus = revenus_node.get('total', 0)
        st.metric("💰 Total Revenus", f"{total_revenus:,.0f}€")

    with col2:
        depenses_node = hierarchy.get('DEPENSES', {})
        total_depenses = depenses_node.get('total', 0)
        st.metric("🛒 Total Dépenses", f"{total_depenses:,.0f}€")

    with col3:
        solde = total_revenus + total_depenses
        st.metric("💵 Solde", f"{solde:,.0f}€")


def display_level2_content(hierarchy: Dict[str, Any], current_node: str):
    """Display content for level 2 (Type)."""
    node = hierarchy.get(current_node, {})
    label = node.get('label', current_node)
    total = node.get('total', 0)
    children_count = len(node.get('children', []))

    st.info(f"📊 **{label}** • Montant total : {total:,.0f}€")
    st.write(f"**Catégories disponibles** : {children_count}")


def display_level3_content(hierarchy: Dict[str, Any], selected_codes: List[str]):
    """Display content for level 3 (Categories with selection)."""
    if not selected_codes:
        st.info("👆 **Cliquez sur les triangles pour sélectionner des sous-catégories**")
        st.write("Vous pouvez sélectionner plusieurs sous-catégories pour les comparer !")
        return

    # Stats breakdown
    st.markdown("### 📊 Statistiques par Catégorie Sélectionnée")

    stats = calculate_stats(pd.DataFrame(), selected_codes, hierarchy)

    if stats:
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
        total_solde = total_revenus + total_depenses

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("📋 Transactions", total_count)

        with col2:
            st.metric("💹 Revenus", f"{total_revenus:,.0f}€")

        with col3:
            st.metric("💸 Dépenses", f"{abs(total_depenses):,.0f}€")

        with col4:
            st.metric("📈 Solde", f"{total_solde:,.0f}€")


def interface_triangle_unified() -> None:
    """
    Main unified interface with triangles and table.

    Layout:
    ┌─────────────────────────────────────┐
    │   HAUT (60%): TRIANGLES             │
    │   - Navigation + Multi-sélection    │
    ├─────────────────────────────────────┤
    │   BAS (40%): TABLE                  │
    │   - Affichage dynamique             │
    └─────────────────────────────────────┘
    """

    init_session_state()

    st.set_page_config(
        page_title="Navigation Fractale Unifiée",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.title("🔺 Navigation Fractale Unifiée")

    # Help section
    with st.expander("ℹ️ Comment utiliser ?", expanded=False):
        st.markdown("""
        ### Système de Multi-Filtrage Unifié

        **Trois niveaux de navigation :**

        1. **Niveau 1 (Racine)** : Voir les totaux globaux
        2. **Niveau 2 (Type)** : Naviguer vers Revenus ou Dépenses
        3. **Niveau 3 (Catégories)** : Sélectionner plusieurs catégories

        **Au niveau 3 :**
        - Cliquez sur les triangles pour SÉLECTIONNER/DÉSÉLECTIONNER
        - Bordure bleue + ✓ indique la sélection
        - Logique AND : affiche transactions matchant TOUTES les sélections
        - Les stats se mettent à jour en temps réel

        **Boutons :**
        - ← Retour : Revenir au niveau précédent
        - 🏠 Vue d'ensemble : Revenir à la racine
        """)

    st.markdown("---")

    # ===== SECTION 1: TRIANGLES (60% HAUT) =====
    st.markdown("### 🔺 Navigation Hiérarchique")

    hierarchy = build_fractal_hierarchy()

    # Container pour les triangles
    with st.container():
        st.markdown("""
        <style>
        iframe[title="fractal_navigation.fractal_navigation"] {
            height: 500px !important;
        }
        </style>
        """, unsafe_allow_html=True)

        fractal_navigation(hierarchy, key='unified_fractal', height=500)

    st.markdown("---")

    # ===== SECTION 2: TABLE ET CONTENU (40% BAS) =====
    st.markdown("### 📊 Contenu Dynamique")

    # Récupérer l'état actuel (simulé - en production, on reçoit du composant)
    # Pour le moment, on utilise la session state
    current_node = st.session_state.unified_state.get('current_node', 'TR')
    selected_codes = list(st.session_state.unified_state.get('selected_nodes', set()))
    level = st.session_state.unified_state.get('level', 1)
    is_selection_mode = st.session_state.unified_state.get('is_selection_mode', False)

    # Afficher le contenu selon le niveau
    if level == 1:
        display_level1_content(hierarchy)

    elif level == 2:
        display_level2_content(hierarchy, current_node)
        st.write("")  # Spacer

    elif level == 3 and is_selection_mode:
        display_level3_content(hierarchy, selected_codes)
        st.markdown("---")

        # Display transactions table
        st.markdown("### 📋 Transactions Filtrées")

        if selected_codes:
            df_filtered = get_transactions_for_codes(selected_codes, hierarchy)
            display_table(df_filtered)
        else:
            st.info("👆 Cliquez sur les triangles pour voir les transactions correspondantes")

    else:
        st.info("Naviguez dans les triangles pour voir le contenu")

    # Debug section
    with st.expander("🔧 Déboguer l'état", expanded=False):
        col1, col2, col3 = st.columns(3)

        with col1:
            st.write("**Nœud actuel:**")
            st.code(current_node)

        with col2:
            st.write("**Niveau:**")
            st.code(str(level))

        with col3:
            st.write("**Mode sélection:**")
            st.code(str(is_selection_mode))

        st.write("**Nœuds sélectionnés:**")
        st.code(str(selected_codes) if selected_codes else "Aucun")


if __name__ == "__main__":
    interface_triangle_unified()
