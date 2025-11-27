"""
Navigation Fractale - Version Minimaliste

Une interface simple basée sur:
- Une hiérarchie de triangles fractals
- Sélection/désélection au niveau 3 (feuilles)
- Affichage des transactions filtrées
- Session state Streamlit (pas de complexité localStorage)

@author: djabi
@version: 1.0 (Minimal)
@date: 2025-11-25
"""

import streamlit as st
import pandas as pd
from typing import Dict, List

from modules.services.fractal_service import build_fractal_hierarchy
from modules.ui.fractal_component import fractal_navigation
from modules.ui.helpers import load_transactions
from modules.utils.converters import safe_convert


def init_session_state():
    """Initialize session state for fractal interface."""
    if 'fractal_selections' not in st.session_state:
        st.session_state.fractal_selections = set()  # Codes sélectionnés
    if 'show_warning' not in st.session_state:
        st.session_state.show_warning = False
    if 'warning_message' not in st.session_state:
        st.session_state.warning_message = ""


def remove_filter_and_children(code_to_remove: str, hierarchy: Dict, selections: set) -> set:
    """
    Enlever un filtre et toutes ses sous-catégories dépendantes.
    Si on enlève une catégorie, enlever aussi ses sous-catégories.
    """
    node = hierarchy.get(code_to_remove, {})
    level = node.get('level', 0)

    # Créer un nouveau set sans le code à enlever
    new_selections = selections.copy()
    new_selections.discard(code_to_remove)

    # Si c'est une catégorie (niveau 2), enlever aussi ses sous-catégories
    if level == 2:
        children_codes = node.get('children', [])
        for child_code in children_codes:
            new_selections.discard(child_code)

    return new_selections


def get_transactions_for_code(code: str, hierarchy: Dict, df: pd.DataFrame) -> pd.DataFrame:
    """Get transactions for a specific code (category or subcategory)."""
    if not code or code not in hierarchy:
        return pd.DataFrame()

    node = hierarchy[code]
    level = node.get('level', 0)

    # Niveau 3 (sous-catégories)
    if level == 3:
        subcategory_name = node.get('label', '')
        return df[df['sous_categorie'].str.lower() == subcategory_name.lower()]

    # Niveau 2 (catégories) - afficher toutes les sous-catégories de cette catégorie
    elif level == 2:
        category_name = node.get('label', '')
        return df[df['categorie'].str.lower() == category_name.lower()]

    # Niveau 1 (type: Revenus/Dépenses) - afficher toutes les transactions du type
    elif level == 1:
        transaction_type = 'revenu' if code == 'REVENUS' else 'dépense'
        return df[df['type'].str.lower() == transaction_type.lower()]

    # Niveau 0 (root) - afficher tout
    elif level == 0:
        return df

    return pd.DataFrame()


def display_transactions_table(df: pd.DataFrame):
    """Display filtered transactions in a table."""
    if df.empty:
        st.info("📭 Aucune transaction")
        return

    # Prepare display dataframe
    df_display = df.copy()
    df_display["montant"] = df_display["montant"].apply(lambda x: safe_convert(x, float, 0.0))
    df_display["Type"] = df_display["type"].apply(lambda x: "💹" if x.lower() == "revenu" else "💸")
    df_display["Date"] = pd.to_datetime(df_display["date"]).dt.strftime("%d/%m/%Y")
    df_display["Montant"] = df_display.apply(
        lambda row: row["montant"] if row["type"].lower() == "revenu" else -row["montant"],
        axis=1
    )

    # Display table
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

    # Export button
    csv = df_display.to_csv(index=False).encode('utf-8')
    st.download_button(
        "💾 Exporter CSV",
        csv,
        "transactions_filtrees.csv",
        "text/csv",
        use_container_width=True
    )




def interface_fractal_unified():
    """Navigation Fractale - Disposition haut/bas avec sélection catégories et sous-catégories."""
    init_session_state()

    st.title("🔺 Navigation Fractale")

    # Load data
    hierarchy = build_fractal_hierarchy()
    df_all = load_transactions()

    if df_all.empty:
        st.error("Aucune transaction dans la base de données")
        return

    # TOP: FRACTAL NAVIGATION CANVAS
    st.subheader("🔺 Navigation")
    fractal_navigation(hierarchy, key='fractal_minimal')

    st.markdown("---")

    # MIDDLE: FILTRES SÉLECTIONNÉS
    st.subheader("🔍 Filtres sélectionnés")

    if st.session_state.fractal_selections:
        # Éliminer les redondances pour l'affichage aussi
        selected_codes = list(st.session_state.fractal_selections)
        display_selections = set()

        for code in selected_codes:
            node = hierarchy.get(code, {})
            level = node.get('level', 0)

            if level == 2:
                display_selections.add(code)
            elif level == 3:
                parent_code = node.get('parent', '')
                if parent_code not in selected_codes:
                    display_selections.add(code)
            else:
                display_selections.add(code)

        # Afficher les badges des filtres actifs (non-redondants)
        cols = st.columns(4)
        for idx, code in enumerate(sorted(display_selections)):
            node = hierarchy.get(code, {})
            label = node.get('label', code)
            col_idx = idx % 4

            with cols[col_idx]:
                col_badge, col_remove = st.columns([4, 1])
                with col_badge:
                    st.write(f"📌 {label}")
                with col_remove:
                    if st.button("✕", key=f"remove_{code}", use_container_width=True):
                        # Enlever le code et toutes ses sous-catégories dépendantes
                        st.session_state.fractal_selections = remove_filter_and_children(code, hierarchy, st.session_state.fractal_selections)
                        st.rerun()

        # Bouton pour effacer toutes les sélections
        if st.button("❌ Effacer tous les filtres", use_container_width=True):
            st.session_state.fractal_selections.clear()
            st.rerun()
    else:
        st.info("👇 Cliquez sur une catégorie ou sous-catégorie pour ajouter un filtre")

    st.markdown("---")

    # BOTTOM: TABLEAU ET RÉSULTATS
    st.subheader("📊 Transactions")

    if st.session_state.fractal_selections:
        # Éliminer les sous-catégories redondantes
        # Si une catégorie est sélectionnée, enlever ses sous-catégories de la sélection
        selected_codes = list(st.session_state.fractal_selections)
        filtered_selections = set()

        # Parcourir les sélections et identifier les redondances
        for code in selected_codes:
            node = hierarchy.get(code, {})
            level = node.get('level', 0)

            # Si c'est une catégorie (niveau 2), ajouter directement
            if level == 2:
                filtered_selections.add(code)
            # Si c'est une sous-catégorie (niveau 3), vérifier si sa catégorie parent est déjà sélectionnée
            elif level == 3:
                parent_code = node.get('parent', '')
                # Si le parent n'est pas sélectionné, ajouter cette sous-catégorie
                if parent_code not in selected_codes:
                    filtered_selections.add(code)
            # Autres niveaux: ajouter directement
            else:
                filtered_selections.add(code)

        # Récupérer et combiner les transactions pour les codes filtrés
        df_filtered = pd.DataFrame()
        for code in sorted(filtered_selections):
            df_code = get_transactions_for_code(code, hierarchy, df_all)
            df_filtered = pd.concat([df_filtered, df_code], ignore_index=True)

        if not df_filtered.empty:
            # Statistiques (4 colonnes comme cap8)
            col1, col2, col3, col4 = st.columns(4)
            total_count = len(df_filtered)
            total_revenus = df_filtered[df_filtered['type'].str.lower() == 'revenu']['montant'].sum()
            total_depenses = df_filtered[df_filtered['type'].str.lower() == 'dépense']['montant'].sum()
            solde = total_revenus - total_depenses

            with col1:
                st.metric("Transactions", total_count)
            with col2:
                st.metric("Revenus", f"{total_revenus:,.0f}€")
            with col3:
                st.metric("Dépenses", f"{abs(total_depenses):,.0f}€")
            with col4:
                st.metric("Solde", f"{solde:,.0f}€")

            st.markdown("---")

            # Afficher le tableau
            display_transactions_table(df_filtered)
        else:
            st.warning("❌ Aucune transaction pour les sélections")

    else:
        # Afficher les statistiques globales
        revenus_total = df_all[df_all['type'].str.lower() == 'revenu']['montant'].sum()
        depenses_total = df_all[df_all['type'].str.lower() == 'dépense']['montant'].sum()
        solde_total = revenus_total + depenses_total

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("💹 Revenus Totaux", f"{revenus_total:,.0f}€")
        with col2:
            st.metric("💸 Dépenses Totales", f"{abs(depenses_total):,.0f}€")
        with col3:
            st.metric("💵 Solde Total", f"{solde_total:,.0f}€")

    st.markdown("---")

    # BOTTOM: HIDDEN BUTTONS (for JavaScript automation)
    st.subheader("🔧 Boutons cachés")

    # Re-render fractal_navigation WITHOUT canvas to get the hidden buttons
    # This will only show the expanders with hidden buttons
    with st.expander("", expanded=False):
        # This section contains the filter buttons for level 1 (Revenus/Dépenses)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("➕ Ajouter le filtre Revenus", key=f"bottom_add_filter_revenus", use_container_width=True):
                if 'fractal_selections' not in st.session_state:
                    st.session_state.fractal_selections = set()
                if 'REVENUS' not in st.session_state.fractal_selections:
                    st.session_state.fractal_selections.add('REVENUS')
                st.rerun()
            if st.button("💹 Revenus", key=f"bottom_filter_revenus", use_container_width=True):
                pass
        with col2:
            if st.button("➕ Ajouter le filtre Dépenses", key=f"bottom_add_filter_depenses", use_container_width=True):
                if 'fractal_selections' not in st.session_state:
                    st.session_state.fractal_selections = set()
                if 'DEPENSES' not in st.session_state.fractal_selections:
                    st.session_state.fractal_selections.add('DEPENSES')
                st.rerun()
            if st.button("💸 Dépenses", key=f"bottom_filter_depenses", use_container_width=True):
                pass

    # Navigation buttons expander
    current_node = st.session_state.get(f'fractal_minimal_current_node', 'TR')
    nav_stack = st.session_state.get(f'fractal_minimal_nav_stack', ['TR'])
    children_codes = hierarchy.get(current_node, {}).get('children', [])

    if children_codes:
        with st.expander("", expanded=False):
            for idx, child_code in enumerate(children_codes):
                child_node = hierarchy.get(child_code, {})
                child_label = child_node.get('label', child_code)
                child_total = child_node.get('amount') or child_node.get('total') or 0
                has_children = len(child_node.get('children', [])) > 0

                btn_text = f"📂 {child_label} ({child_total:,.0f}€)" if has_children else f"📋 {child_label} ({child_total:,.0f}€)"

                if st.button(btn_text, key=f"bottom_nav_{idx}_{child_code}", use_container_width=True):
                    pass


if __name__ == "__main__":
    interface_fractal_unified()
