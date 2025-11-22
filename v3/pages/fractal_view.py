"""
Fractal Navigation Demo Page - Test and showcase of the fractal component.

@author: djabi
@version: 1.0
@date: 2025-11-22
"""

import streamlit as st
from datetime import datetime, timedelta
import logging
import pandas as pd

from modules.services.fractal_service import (
    build_fractal_hierarchy,
    get_transactions_for_node,
    get_node_info
)
from modules.ui.fractal_component import fractal_navigation
from modules.database.repositories import TransactionRepository

logger = logging.getLogger(__name__)

# ==============================
# PAGE CONFIGURATION
# ==============================

st.set_page_config(
    page_title="Navigation Fractale",
    page_icon="🔺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================
# STYLING
# ==============================

st.markdown("""
<style>
    /* Custom styling for fractal page */
    .main-title {
        text-align: center;
        margin-bottom: 20px;
    }

    .info-box {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(59, 130, 246, 0.1) 100%);
        border-left: 4px solid #10b981;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 20px;
    }

    .transaction-card {
        background: rgba(30, 41, 59, 0.5);
        border-left: 3px solid #10b981;
        padding: 12px;
        border-radius: 6px;
        margin-bottom: 10px;
    }

    .stats-card {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(20, 184, 166, 0.1) 100%);
        border: 1px solid rgba(16, 185, 129, 0.2);
        padding: 15px;
        border-radius: 8px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ==============================
# SIDEBAR CONFIGURATION
# ==============================

st.sidebar.title("⚙️ Configuration")

# Date range filters
col1, col2 = st.sidebar.columns(2)
with col1:
    date_debut = st.date_input(
        "📅 Date début",
        value=datetime.now() - timedelta(days=90)
    )
with col2:
    date_fin = st.date_input(
        "📅 Date fin",
        value=datetime.now()
    )

# Refresh button
if st.sidebar.button("🔄 Actualiser", use_container_width=True):
    st.rerun()

st.sidebar.markdown("---")

# Info panel
st.sidebar.markdown("### ℹ️ À propos")
st.sidebar.info("""
**Navigation Fractale** 🔺

Explorez votre hiérarchie financière avec un système de navigation basé sur les fractales de Sierpiński.

**Comment ça marche :**
1. Cliquez sur un triangle pour zoomer
2. Explorez les catégories et sous-catégories
3. Utilisez les boutons pour revenir en arrière

**Niveaux :**
- Niveau 1: Types (Revenus/Dépenses)
- Niveau 2: Catégories
- Niveau 3: Sous-catégories
""")

# ==============================
# MAIN PAGE
# ==============================

st.markdown("""
<h1 style="text-align: center; margin-bottom: 10px;">🔺 Navigation Fractale</h1>
<p style="text-align: center; color: #94a3b8; margin-bottom: 30px;">
    Explorez votre univers financier avec les fractales de Sierpiński
</p>
""", unsafe_allow_html=True)

# Build hierarchy
try:
    with st.spinner("🔄 Construction de la hiérarchie fractale..."):
        fractal_data = build_fractal_hierarchy(
            date_debut=date_debut.isoformat() if date_debut else None,
            date_fin=date_fin.isoformat() if date_fin else None
        )

    if not fractal_data or len(fractal_data) <= 1:
        st.warning("⚠️ Pas de données disponibles pour la période sélectionnée")
        st.stop()

    # Display statistics
    root_node = fractal_data['TR']
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="stats-card">
            <div style="font-size: 28px; color: #10b981; font-weight: bold;">
                {len([k for k in fractal_data.keys() if k.startswith('CAT_')])}
            </div>
            <div style="font-size: 12px; color: #94a3b8;">Catégories</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="stats-card">
            <div style="font-size: 28px; color: #f59e0b; font-weight: bold;">
                {len([k for k in fractal_data.keys() if k.startswith('SUBCAT_')])}
            </div>
            <div style="font-size: 12px; color: #94a3b8;">Sous-catégories</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        total = root_node.get('total', 0)
        st.markdown(f"""
        <div class="stats-card">
            <div style="font-size: 28px; color: #06b6d4; font-weight: bold;">
                {total:,.0f}€
            </div>
            <div style="font-size: 12px; color: #94a3b8;">Total</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        # Count transactions
        df_all = TransactionRepository.get_all()
        if date_debut or date_fin:
            df_all['date'] = pd.to_datetime(df_all['date'])
            if date_debut:
                df_all = df_all[df_all['date'] >= pd.Timestamp(date_debut)]
            if date_fin:
                df_all = df_all[df_all['date'] <= pd.Timestamp(date_fin)]

        tx_count = len(df_all) if not df_all.empty else 0

        st.markdown(f"""
        <div class="stats-card">
            <div style="font-size: 28px; color: #6366f1; font-weight: bold;">
                {tx_count}
            </div>
            <div style="font-size: 12px; color: #94a3b8;">Transactions</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Main fractal component
    st.markdown("### 🔺 Navigateur Fractal")
    st.info("""
    💡 **Interactions :**
    - Cliquez sur un triangle pour explorer
    - Survolez pour voir les détails
    - Utilisez les boutons pour naviguer
    """)

    # Initialize session state for navigation
    if 'fractal_result' not in st.session_state:
        st.session_state.fractal_result = None

    # Render the fractal component
    result = fractal_navigation(
        data=fractal_data,
        key='main_fractal_component',
        height=800
    )

    # Handle navigation results
    if result:
        st.session_state.fractal_result = result
        st.session_state.last_action = result.get('action', 'none')
        st.session_state.current_node = result.get('code', 'TR')

    # Display current node details
    if st.session_state.get('current_node'):
        current_code = st.session_state.current_node
        current_node_data = fractal_data.get(current_code)

        if current_node_data:
            st.markdown("---")
            st.markdown(f"### 📊 Détails: {current_node_data.get('label', current_code)}")

            # Node information
            info_col1, info_col2, info_col3 = st.columns(3)

            with info_col1:
                if 'amount' in current_node_data:
                    st.metric(
                        "💰 Montant",
                        f"{current_node_data['amount']:,.0f}€"
                    )
                elif 'total' in current_node_data:
                    st.metric(
                        "💰 Total",
                        f"{current_node_data['total']:,.0f}€"
                    )

            with info_col2:
                if 'transactions' in current_node_data:
                    st.metric(
                        "📋 Transactions",
                        current_node_data['transactions']
                    )
                elif 'children' in current_node_data:
                    st.metric(
                        "📁 Enfants",
                        len(current_node_data['children'])
                    )

            with info_col3:
                if 'percentage' in current_node_data:
                    st.metric(
                        "📈 Pourcentage",
                        f"{current_node_data['percentage']:.1f}%"
                    )
                else:
                    st.metric(
                        "🎯 Niveau",
                        current_node_data.get('level', 0)
                    )

            # Display transactions for leaf nodes
            if current_code.startswith('SUBCAT_'):
                st.markdown("### 📋 Transactions")

                transactions_df = get_transactions_for_node(
                    current_code,
                    fractal_data,
                    date_debut.isoformat() if date_debut else None,
                    date_fin.isoformat() if date_fin else None
                )

                if not transactions_df.empty:
                    # Display transactions
                    for idx, tx in transactions_df.iterrows():
                        with st.container():
                            col1, col2, col3 = st.columns([3, 1, 1])

                            with col1:
                                st.write(f"**{tx.get('description', 'Sans description')}**")
                                st.caption(tx.get('date', ''))

                            with col2:
                                st.write(f"{tx.get('montant', 0):,.0f}€")

                            with col3:
                                st.write(f"{tx.get('source', 'Manuel')}")

                    st.markdown("---")

                    # Export option
                    csv = transactions_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Télécharger CSV",
                        data=csv,
                        file_name=f"transactions_{current_node_data['label'].replace(' ', '_')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("Aucune transaction trouvée pour cette sélection")

except Exception as e:
    logger.error(f"Error in fractal_view: {e}", exc_info=True)
    st.error(f"""
    ❌ Une erreur s'est produite: {str(e)}

    **Solutions possibles :**
    1. Vérifiez que la base de données contient des données
    2. Vérifiez la plage de dates
    3. Rafraîchissez la page
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #94a3b8; font-size: 12px;">
    <p>🔺 Navigation Fractale v1.0 | Gestio V4 Financier</p>
    <p>Explorez votre univers financier avec les fractales de Sierpiński</p>
</div>
""", unsafe_allow_html=True)
