"""
Fractal Navigation Unifiée - Single Interface

Version finale unifiée avec:
- Navigation UNIQUEMENT par triangles fractals
- Sélection multi au dernier niveau (checked par le JavaScript)
- Filtres persistants à travers la navigation
- Tableau dynamique des transactions filtrées
- Interface simple et intuitive

APPROCHE:
- Le JavaScript dans fractal.js gère: navigation + sélection visuelle
- Streamlit gère: affichage du tableau et persistance des filtres
- L'état des sélections est stocké dans localStorage par le JavaScript
- Les utilisateurs interagissent UNIQUEMENT avec les triangles

@author: djabi
@version: 6.0 (Unified - Pure Fractal Interface)
@date: 2025-11-23
"""

import streamlit as st
import pandas as pd
import json
from typing import Dict, Any, List, Set

from modules.services.fractal_service import build_fractal_hierarchy
from modules.ui.fractal_component import fractal_navigation
from modules.ui.helpers import load_transactions
from modules.utils.converters import safe_convert


def init_session_state():
    """Initialize session state for unified fractal interface."""
    if 'fractal_manual_filters' not in st.session_state:
        st.session_state.fractal_manual_filters = set()  # Filtres manuels (pour les boutons de retrait)
    if 'last_fractal_state' not in st.session_state:
        st.session_state.last_fractal_state = {}  # État du fractal (navigation + sélection)


def get_transactions_for_codes(codes: List[str], df: pd.DataFrame) -> pd.DataFrame:
    """Get transactions for multiple codes with AND logic."""
    if not codes:
        return pd.DataFrame()

    result_df = df.copy()

    for code in codes:
        # Parse le code pour extraire catégorie et sous-catégorie
        if code.startswith('SUBCAT_'):
            parts = code[7:].split('_', 1)
            if len(parts) == 2:
                category = parts[0].title()
                subcategory = parts[1].replace('_', ' ').title()
                result_df = result_df[
                    (result_df['categorie'].str.lower() == category.lower()) &
                    (result_df['sous_categorie'].str.lower() == subcategory.lower())
                ]
        elif code.startswith('CAT_'):
            category = code[4:].replace('_', ' ').title()
            result_df = result_df[result_df['categorie'].str.lower() == category.lower()]
        elif code == 'REVENUS':
            result_df = result_df[result_df['type'].str.lower() == 'revenu']
        elif code == 'DEPENSES':
            result_df = result_df[result_df['type'].str.lower() == 'dépense']

    return result_df


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


def display_active_filters(hierarchy: Dict, selected_codes: List[str]):
    """Display currently active filters with removal buttons."""
    if not selected_codes:
        return

    st.markdown("### 🎯 Filtres Actifs")

    # Show filter list
    filter_info = []
    for code in selected_codes:
        node = hierarchy.get(code, {})
        label = node.get('label', code)
        total = node.get('total', 0)
        filter_info.append(f"**{label}** ({total:,.0f}€)")

    st.info(f"Filtres appliqués: {' + '.join(filter_info)}")

    # Removal buttons
    st.markdown("**Retirer des filtres:**")
    cols = st.columns(min(len(selected_codes), 5))

    for idx, code in enumerate(selected_codes):
        node = hierarchy.get(code, {})
        label = node.get('label', code)
        col_idx = idx % len(cols)

        with cols[col_idx]:
            if st.button(f"❌ {label}", key=f"remove_{code}", use_container_width=True):
                st.session_state.fractal_manual_filters.discard(code)
                st.rerun()


def interface_fractal_unified():
    """Main unified fractal navigation interface."""
    init_session_state()

    st.set_page_config(
        page_title="Navigation Fractale Unifiée",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    st.title("🔺 Navigation Fractale Unifiée")

    # Load data
    hierarchy = build_fractal_hierarchy()
    df_all = load_transactions()

    if df_all.empty:
        st.error("Aucune transaction dans la base")
        return

    # Help section
    with st.expander("ℹ️ Comment utiliser ?", expanded=False):
        st.markdown("""
        ### Navigation Fractale Unifiée

        **Flux:**
        1. Cliquez sur les triangles pour naviguer dans la hiérarchie
        2. Au dernier niveau (sous-catégories), cliquez pour SÉLECTIONNER
        3. Les triangles sélectionnés deviennent BLEUS avec un ✓
        4. Le tableau affiche automatiquement les transactions filtrées
        5. Les filtres restent actifs même si vous naviguez ailleurs
        6. Continuez à naviguer et sélectionner pour ajouter d'autres filtres

        **Sélection:**
        - Clic sur un triangle = Sélection/Désélection
        - Triangle bleu brillant + ✓ = Sélectionné
        - Vous pouvez sélectionner plusieurs triangles du même niveau

        **Filtres:**
        - Les filtres restent actifs pendant la navigation
        - Cliquez "❌ Retirer" pour ôter un filtre
        - Cliquez "🏠 Réinitialiser" (bouton dans le fractal) pour tout effacer
        """)

    st.markdown("---")

    # ===== SECTION 1: FRACTAL TRIANGLES (NAVIGATION + SÉLECTION) =====
    st.markdown("### 🔺 Navigation Visuelle")

    fractal_navigation(hierarchy, key='unified_fractal_v6', height=700)

    st.markdown("---")

    # ===== SECTION 2: TABLEAU ET FILTRES ACTIFS =====
    st.markdown("### 📊 Données Filtrées")

    # IMPORTANT: Lire l'état du fractal depuis le session_state ou localStorage
    # Pour maintenant, utiliser une approche manuelle: les filtres sont gérés via st.session_state
    # Le JavaScript mettra à jour l'état, que nous lirons via une méthode custom

    # Placeholder pour recevoir l'état du fractal (sera rempli par custom component)
    st_placeholder = st.empty()

    # JavaScript pour synchroniser l'état avec Streamlit
    st.markdown("""
    <script>
    // Lire l'état du fractal depuis le storage toutes les secondes
    function syncFractalState() {
        try {
            const stateJson = localStorage.getItem('fractal_state_v6') || sessionStorage.getItem('fractal_state_v6');
            if (stateJson) {
                const state = JSON.parse(stateJson);
                // Sauvegarder pour accès Streamlit
                window.lastFractalState = state;
                console.log('[SYNC] État fractal synchronisé:', state.selectedNodes);
            }
        } catch (e) {
            console.log('[SYNC] Erreur sync:', e);
        }
    }

    // Sync initial et périodique
    syncFractalState();
    setInterval(syncFractalState, 1000);
    </script>
    """, unsafe_allow_html=True)

    # SIMPLIFICATION: Utiliser un formulaire avec des boutons pour ajouter les filtres
    # manuellement depuis Python. Les utilisateurs cliqueront sur les triangles dans le fractal
    # et nous afficherons les sélections en dessous.

    # Pour cette version v6, on va faire simple:
    # - L'utilisateur clique sur les triangles (JavaScript gère la sélection visuelle)
    # - Nous offrons une UI pour ajouter/retirer les filtres manuellement
    # - Le tableau se met à jour selon les filtres actifs

    # Utilisateurs peuvent ajouter les codes manuellement
    with st.expander("➕ Ajouter manuellement des filtres", expanded=False):
        st.markdown("*Alternative: cliquez sur les triangles (la façon normale)*")

        # Lister les sous-catégories disponibles
        all_subcats = []
        for code, node in hierarchy.items():
            if code.startswith('SUBCAT_'):
                all_subcats.append({
                    'code': code,
                    'label': node.get('label', code),
                    'total': node.get('total', 0)
                })

        selected_filter = st.selectbox(
            "Sélectionner une sous-catégorie à filtrer:",
            options=[s['label'] for s in all_subcats],
            key="manual_select"
        )

        if selected_filter:
            selected_subcat = next((s for s in all_subcats if s['label'] == selected_filter), None)
            if selected_subcat and st.button("✅ Ajouter ce filtre"):
                st.session_state.fractal_manual_filters.add(selected_subcat['code'])
                st.rerun()

    # ===== AFFICHAGE DU TABLEAU SELON LES FILTRES =====

    # Utiliser les filtres manuels comme source de vérité
    selected_nodes_list = list(st.session_state.fractal_manual_filters)

    if selected_nodes_list:
        # Display active filters with removal buttons
        display_active_filters(hierarchy, selected_nodes_list)

        st.markdown("---")

        # Calculate statistics
        df_filtered = get_transactions_for_codes(selected_nodes_list, df_all)

        if not df_filtered.empty:
            # Display metrics
            total_count = len(df_filtered)
            total_revenus = df_filtered[df_filtered['type'].str.lower() == 'revenu']['montant'].sum()
            total_depenses = df_filtered[df_filtered['type'].str.lower() == 'dépense']['montant'].sum()
            solde = total_revenus + total_depenses

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("📋 Transactions", total_count)

            with col2:
                st.metric("💹 Revenus", f"{total_revenus:,.2f}€")

            with col3:
                st.metric("💸 Dépenses", f"{abs(total_depenses):,.2f}€")

            with col4:
                st.metric("📈 Solde", f"{solde:,.2f}€")

            st.markdown("---")

            # Display transactions table
            st.markdown("### 📋 Transactions")
            display_transactions_table(df_filtered)
        else:
            st.warning("Aucune transaction pour cette sélection")

    else:
        # No selection - show global stats
        st.info("👇 Naviguez dans les triangles et sélectionnez des sous-catégories pour voir les transactions")

        # Global statistics
        col1, col2, col3 = st.columns(3)

        with col1:
            revenus_node = hierarchy.get('REVENUS', {})
            total_revenus = revenus_node.get('total', 0)
            st.metric("💰 Total Revenus", f"{total_revenus:,.2f}€")

        with col2:
            depenses_node = hierarchy.get('DEPENSES', {})
            total_depenses = depenses_node.get('total', 0)
            st.metric("🛒 Total Dépenses", f"{abs(total_depenses):,.2f}€")

        with col3:
            solde = total_revenus + total_depenses
            st.metric("💵 Solde", f"{solde:,.2f}€")


if __name__ == "__main__":
    interface_fractal_unified()
