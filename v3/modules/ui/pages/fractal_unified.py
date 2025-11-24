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
        st.session_state.fractal_manual_filters = set()  # Filtres persistants
    if 'last_fractal_state' not in st.session_state:
        st.session_state.last_fractal_state = {}  # État du fractal
    if 'fractal_auto_selections' not in st.session_state:
        st.session_state.fractal_auto_selections = []  # Auto-sync des sélections du Niveau 3


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


def sync_fractal_selections_from_js():
    """
    Synchronize selections from JavaScript to Streamlit using URL query parameters.
    JavaScript periodically updates the URL, and Streamlit reads it via st.query_params.
    """
    import json

    # JavaScript code that syncs fractal state to URL query parameters
    sync_script = """
    <script>
    console.log('[SYNC-INIT] Initializing URL-based synchronization...');

    // Function to get current fractal state from localStorage
    function getFractalState() {
        try {
            const stateJson = localStorage.getItem('fractal_state_v6') ||
                             sessionStorage.getItem('fractal_state_v6');
            if (stateJson) {
                return JSON.parse(stateJson);
            }
        } catch (e) {
            console.log('[SYNC-ERROR] Parse error:', e);
        }
        return { selectedNodes: [], action: 'navigation', level: 1 };
    }

    // Update URL query parameters with current selections
    function syncStateToURL() {
        const state = getFractalState();
        const selections = state.selectedNodes || [];

        console.log('[SYNC-URL] syncStateToURL called');
        console.log('[SYNC-URL]   selections:', selections);
        console.log('[SYNC-URL]   state:', state);

        // Build query string
        const params = new URLSearchParams();
        if (selections.length > 0) {
            // Encode selections as comma-separated list
            params.set('fractal_selections', selections.join(','));
        }
        params.set('fractal_level', state.level || 1);
        params.set('fractal_node', state.currentNode || 'TR');

        const newUrl = window.location.pathname + '?' + params.toString();

        console.log('[SYNC-URL] Prepared URL:', newUrl);
        console.log('[SYNC-URL] window.history exists:', !!window.history);
        console.log('[SYNC-URL] replaceState exists:', !!(window.history && window.history.replaceState));

        // Update URL without full page reload
        try {
            if (window.history && window.history.replaceState) {
                window.history.replaceState({ state }, '', newUrl);
                console.log('[SYNC-URL] ✅ replaceState SUCCESS');
                console.log('[SYNC-URL] Current URL now:', window.location.href);
            } else {
                console.log('[SYNC-URL] ❌ replaceState not available');
                // Fallback: try to update hash
                window.location.hash = '?' + params.toString();
                console.log('[SYNC-URL] Fallback: updated hash');
            }
        } catch (e) {
            console.log('[SYNC-URL] ❌ Error during replaceState:', e);
        }
    }

    // Sync on fractal state changes
    document.addEventListener('fractalStateChanged', function(e) {
        console.log('[SYNC-EVENT] Fractal state changed, updating URL');
        syncStateToURL();
    });

    // Also sync periodically (every 500ms) in case of direct localStorage changes
    setInterval(syncStateToURL, 500);

    // Initial sync
    syncStateToURL();

    console.log('[SYNC-INIT] ✅ URL synchronization ready');
    </script>
    """

    # Display the synchronization script
    st.markdown(sync_script, unsafe_allow_html=True)


def interface_fractal_unified():
    """Main unified fractal navigation interface - Pure Fractal Only."""
    init_session_state()

    st.set_page_config(
        page_title="🔺 Navigation Fractale Unifiée",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    st.title("🔺 Navigation Fractale Unifiée")

    # ===== JAVASCRIPT: Mettre à jour l'URL quand sélections changent =====
    # Système ROBUSTE avec double surveillance pour assurer la synchronisation
    st.markdown("""
    <script>
    console.log('[SYNC-SYSTEM] 🚀 Démarrage du système de synchronisation');


    let lastUrlUpdate = 0;
    const URL_UPDATE_DELAY = 200; // Limiter les updates (200ms throttle)

    // Fonction principale de mise à jour de l'URL
    function updateURLWithSelections() {
        const now = Date.now();
        if (now - lastUrlUpdate < URL_UPDATE_DELAY) return; // Throttle
        lastUrlUpdate = now;

        try {
            // Essayer localStorage d'abord (source de vérité)
            let state = null;
            try {
                const stateJson = localStorage.getItem('fractal_state_v6');
                if (stateJson) {
                    state = JSON.parse(stateJson);
                }
            } catch (e) {
                console.log('[SYNC-SYSTEM] ⚠️ localStorage read error:', e);
            }

            // Fallback à sessionStorage
            if (!state) {
                try {
                    const stateJson = sessionStorage.getItem('fractal_state_v6');
                    if (stateJson) {
                        state = JSON.parse(stateJson);
                    }
                } catch (e) {
                    console.log('[SYNC-SYSTEM] ⚠️ sessionStorage read error:', e);
                }
            }

            if (!state) {
                console.log('[SYNC-SYSTEM] ℹ️ Pas d\'état trouvé');
                return;
            }

            const selections = state.selectedNodes || [];
            console.log('[SYNC-SYSTEM] 📍 État lu:', { selections, currentNode: state.currentNode });

            if (selections.length > 0) {
                const selectionsStr = selections.join(',');
                const urlParams = new URLSearchParams(window.location.search);
                const currentSelections = urlParams.get('fractal_selections') || '';

                if (selectionsStr !== currentSelections) {
                    // Les sélections ont changé, mettre à jour l'URL
                    const newUrl = window.location.pathname +
                                  '?fractal_selections=' + encodeURIComponent(selectionsStr);

                    console.log('[SYNC-SYSTEM] 📤 Changement de sélections détecté');
                    console.log('[SYNC-SYSTEM]   Ancien selections:', currentSelections || '(aucun)');
                    console.log('[SYNC-SYSTEM]   Nouveau selections:', selectionsStr);
                    console.log('[SYNC-SYSTEM]   Nouvelle URL:', newUrl);

                    try {
                        // Naviguer vers la nouvelle URL pour causer un rerun de Streamlit
                        console.log('[SYNC-SYSTEM] 🔄 Navigation vers nouvelle URL...');
                        window.location.href = newUrl;

                        // Note: window.location.href causera:
                        // 1. Rechargement de la page (reload)
                        // 2. Réexécution du Python côté serveur
                        // 3. Streamlit relira l'URL via st.query_params
                        // 4. Le tableau s'affichera avec les filtres appliqués
                        // C'est NORMAL et ATTENDU - c'est la façon que Streamlit fonctionne
                    } catch (e) {
                        console.log('[SYNC-SYSTEM] ❌ Navigation ERROR:', e);
                    }
                } else {
                    console.log('[SYNC-SYSTEM] ℹ️ Sélections inchangées, pas de navigation');
                }
            } else {
                console.log('[SYNC-SYSTEM] ℹ️ Aucune sélection');
            }
        } catch (e) {
            console.log('[SYNC-SYSTEM] ❌ ERREUR CRITIQUE:', e);
        }
    }

    // STRATÉGIE 1: Écouter les changements d'état du Fractal
    console.log('[SYNC-SYSTEM] 📍 Enregistrement listener fractalStateChanged');
    document.addEventListener('fractalStateChanged', function(e) {
        console.log('[SYNC-SYSTEM] 🔔 EVENT fractalStateChanged reçu');
        updateURLWithSelections();
    });

    // STRATÉGIE 2: Polling périodique du localStorage (fallback robuste)
    let lastStoredSelections = '';
    setInterval(function() {
        try {
            const state = JSON.parse(localStorage.getItem('fractal_state_v6') || '{}');
            const selections = (state.selectedNodes || []).join(',');

            if (selections !== lastStoredSelections) {
                console.log('[SYNC-SYSTEM] 📍 Changement détecté via polling');
                console.log('[SYNC-SYSTEM]   Avant:', lastStoredSelections);
                console.log('[SYNC-SYSTEM]   Après:', selections);
                lastStoredSelections = selections;
                updateURLWithSelections();
            }
        } catch (e) {
            // Ignorer les erreurs du polling
        }
    }, 200); // Check every 200ms

    // STRATÉGIE 3: Sync initiale au chargement
    console.log('[SYNC-SYSTEM] 🚀 Sync initiale');
    setTimeout(updateURLWithSelections, 500);

    console.log('[SYNC-SYSTEM] ✅ Tous les listeners installés');
    </script>
    """)

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

    # ===== UNIFIED LAYOUT: 60% FRACTAL + 40% TABLE =====
    col_left, col_right = st.columns([60, 40])

    # LEFT: FRACTAL TRIANGLES (NAVIGATION + SÉLECTION)
    with col_left:
        st.markdown("### 🔺 Navigation Visuelle")
        st.markdown("**Mode:** Cliquez sur les triangles pour sélectionner/désélectionner")
        st.markdown("**Les filtres s'appliquent automatiquement au Niveau 3!**")
        fractal_navigation(hierarchy, key='unified_fractal_v6', height=700)

    # RIGHT: TABLE DYNAMIQUE ET FILTRES
    with col_right:
        st.markdown("### 📊 Transactions Filtrées")

        # ===== LIRE LES SÉLECTIONS DEPUIS L'URL =====
        # Quand JavaScript change une sélection:
        # 1. JavaScript met à jour le localStorage
        # 2. JavaScript envoie un event 'fractalStateChanged'
        # 3. Notre code JavaScript détecte le changement via polling du localStorage
        # 4. JavaScript met à jour l'URL via window.location.href
        # 5. Streamlit recharge et reexecute ce code Python
        # 6. Streamlit relit l'URL via st.query_params

        selections_from_url = st.query_params.get('fractal_selections', '')

        if selections_from_url:
            # Parser les sélections depuis l'URL
            selected_nodes_list = [code.strip() for code in selections_from_url.split(',') if code.strip()]
            # Sauvegarder dans session state pour persistance
            st.session_state.fractal_manual_filters = set(selected_nodes_list)
        else:
            # Utiliser session state si l'URL est vide (backward compat)
            selected_nodes_list = list(st.session_state.fractal_manual_filters)

        # ===== AFFICHAGE CONDITIONNEL DANS LA COLONNE DROITE =====
        if selected_nodes_list:
            # ✅ AVEC SÉLECTIONS
            st.markdown("**Filtres actifs:**")

            # Afficher les filtres comme badges avec boutons de suppression
            for code in selected_nodes_list:
                node = hierarchy.get(code, {})
                label = node.get('label', code)
                col_badge, col_remove = st.columns([4, 1])

                with col_badge:
                    st.write(f"🔹 {label}")

                with col_remove:
                    if st.button("❌", key=f"remove_{code}"):
                        st.session_state.fractal_manual_filters.discard(code)
                        st.rerun()

            st.markdown("---")

            # Calculate statistics
            df_filtered = get_transactions_for_codes(selected_nodes_list, df_all)

            if not df_filtered.empty:
                # Display metrics (compacts pour la droite)
                total_count = len(df_filtered)
                total_revenus = df_filtered[df_filtered['type'].str.lower() == 'revenu']['montant'].sum()
                total_depenses = df_filtered[df_filtered['type'].str.lower() == 'dépense']['montant'].sum()
                solde = total_revenus + total_depenses

                # Deux colonnes pour les métriques
                m1, m2 = st.columns(2)
                with m1:
                    st.metric("📋 Trans.", total_count)
                with m2:
                    st.metric("💹 Rev.", f"{total_revenus:,.0f}€")

                m3, m4 = st.columns(2)
                with m3:
                    st.metric("💸 Dép.", f"{abs(total_depenses):,.0f}€")
                with m4:
                    st.metric("📈 Solde", f"{solde:,.0f}€")

                st.markdown("---")

                # Display transactions table
                st.markdown("**Transactions:**", help="Cliquez sur les triangles pour filtrer")
                display_transactions_table(df_filtered)
            else:
                st.warning("Aucune transaction pour cette sélection")

        else:
            # ❌ SANS SÉLECTIONS
            st.info("👇 Cliquez sur les triangles pour sélectionner")

            # Global statistics (simples)
            revenus_node = hierarchy.get('REVENUS', {})
            total_revenus = revenus_node.get('total', 0)

            depenses_node = hierarchy.get('DEPENSES', {})
            total_depenses = depenses_node.get('total', 0)

            solde = total_revenus + total_depenses

            st.metric("💰 Revenus", f"{total_revenus:,.0f}€")
            st.metric("💸 Dépenses", f"{abs(total_depenses):,.0f}€")
            st.metric("💵 Solde", f"{solde:,.0f}€")


if __name__ == "__main__":
    interface_fractal_unified()
