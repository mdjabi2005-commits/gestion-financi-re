"""
Overview Tab

This module implements Tab 3 of the portfolio interface:
- Monthly budget overview
- Expense breakdown by category
- Budget vs actual visualization
- Monthly metrics and statistics
"""

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import plotly.graph_objects as go
from modules.ui.helpers import load_transactions
from config import DB_PATH


def render_overview_tab(conn: sqlite3.Connection, cursor: sqlite3.Cursor) -> None:
    """
    Render the overview tab.

    Features:
    - Monthly budget statistics
    - Expense breakdown by category
    - Budget vs actual comparison
    - Visual representations with charts

    Args:
        conn: Database connection
        cursor: Database cursor
    """
    st.subheader("📊 Vue d'ensemble du mois")

    # Charger les budgets et transactions
    df_budgets = pd.read_sql_query(
        "SELECT * FROM budgets_categories",
        conn
    )
    df_transactions = load_transactions()

    if df_budgets.empty:
        st.info("💡 Définissez des budgets pour voir les statistiques")
    else:
        # Calculer les totaux
        budget_total = df_budgets["budget_mensuel"].sum()

        # Calculer les dépenses du mois
        today = datetime.now()
        premier_jour_mois = today.replace(day=1).date()

        if not df_transactions.empty:
            depenses_mois_total = df_transactions[
                (df_transactions["type"] == "dépense") &
                (pd.to_datetime(df_transactions["date"]).dt.date >= premier_jour_mois)
            ]["montant"].sum()
        else:
            depenses_mois_total = 0.0

        reste_total = budget_total - depenses_mois_total
        pourcentage_total = (depenses_mois_total / budget_total * 100) if budget_total > 0 else 0

        # Afficher les métriques
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("💰 Budget total", f"{budget_total:.0f} €")

        with col2:
            st.metric("💸 Dépensé", f"{depenses_mois_total:.0f} €")

        with col3:
            delta_color = "normal" if reste_total >= 0 else "inverse"
            st.metric("💵 Reste", f"{reste_total:.0f} €", delta_color=delta_color)

        with col4:
            st.metric("📊 % utilisé", f"{pourcentage_total:.1f}%")

        # Graphique de répartition
        st.markdown("---")
        st.markdown("#### 📊 Répartition des dépenses par catégorie")

        if not df_transactions.empty:
            depenses_par_cat = []

            for _, budget in df_budgets.iterrows():
                categorie = budget["categorie"]
                budget_mensuel = budget["budget_mensuel"]

                depenses = df_transactions[
                    (df_transactions["type"] == "dépense") &
                    (df_transactions["categorie"] == categorie) &
                    (pd.to_datetime(df_transactions["date"]).dt.date >= premier_jour_mois)
                ]["montant"].sum()

                depenses_par_cat.append({
                    "Catégorie": categorie,
                    "Dépensé": depenses,
                    "Budget": budget_mensuel,
                    "% du budget": (depenses / budget_mensuel * 100) if budget_mensuel > 0 else 0
                })

            df_depenses = pd.DataFrame(depenses_par_cat)

            if not df_depenses.empty:
                # Graphique en barres
                fig = go.Figure()

                fig.add_trace(go.Bar(
                    name='Budget',
                    x=df_depenses['Catégorie'],
                    y=df_depenses['Budget'],
                    marker_color='lightblue'
                ))

                fig.add_trace(go.Bar(
                    name='Dépensé',
                    x=df_depenses['Catégorie'],
                    y=df_depenses['Dépensé'],
                    marker_color='salmon'
                ))

                fig.update_layout(
                    barmode='group',
                    title='Budget vs Dépenses par catégorie',
                    xaxis_title='Catégorie',
                    yaxis_title='Montant (€)',
                    height=400
                )

                st.plotly_chart(fig, use_container_width=True)
