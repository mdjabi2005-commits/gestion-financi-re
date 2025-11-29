"""
Home Page Module - Modern Dashboard Interface

This module contains the modernized main dashboard displaying financial metrics
with an "essential-first" approach: most important information visible immediately.

Structure:
1. Period selector (compact)
2. Hero section: Main balance with visual indicator
3. Key metrics cards (4 main metrics)
4. Monthly evolution chart (OPEN by default, Plotly)
5. Detailed sections (CLOSED expanders)
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import date
from dateutil.relativedelta import relativedelta
from typing import Optional
import logging
from modules.ui.helpers import load_transactions, refresh_and_rerun
from modules.ui.components import toast_error, toast_warning

logger = logging.getLogger(__name__)


def interface_accueil() -> None:
    """
    Modern dashboard interface with essential-first design.
    
    Features:
    - Compact period selection
    - Hero balance section with visual indicator
    - 4 key metrics in colored cards
    - Interactive Plotly charts (monthly evolution OPEN by default)
    - Detailed sections in closed expanders
    
    Returns:
        None
    """
    st.title("🏠 Tableau de Bord Financier")

    # Load data with error handling
    try:
        df = load_transactions()
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        toast_error("Erreur lors du chargement des données")
        return

    if df.empty:
        st.info("💰 Aucune transaction enregistrée. Commencez par ajouter vos premières transactions !")
        return

    # ===== COMPACT PERIOD SELECTOR =====
    premiere_date = df["date"].min().date()
    derniere_date = df["date"].max().date()

    col1, col2 = st.columns([4, 1])

    with col1:
        periode_options = {
            "Ce mois": 1,
            "3 derniers mois": 3,
            "6 derniers mois": 6,
            "12 derniers mois": 12,
            "Depuis le début": "debut"
        }
        periode_choice = st.selectbox(
            "📅 Période",
            list(periode_options.keys()),
            key="periode_accueil",
            label_visibility="collapsed"
        )

        if periode_choice == "Depuis le début":
            date_debut = premiere_date
            date_fin = derniere_date
        else:
            mois_retour = periode_options[periode_choice]
            date_debut = max(premiere_date, date.today() - relativedelta(months=mois_retour))
            date_fin = derniere_date

        st.caption(f"📆 Du {date_debut.strftime('%d/%m/%Y')} au {date_fin.strftime('%d/%m/%Y')}")

    with col2:
        if st.button("🔄 Actualiser", key="refresh_accueil", use_container_width=True):
            refresh_and_rerun()

    # Filter data
    df_periode = df[(df["date"] >= pd.Timestamp(date_debut)) & (df["date"] <= pd.Timestamp(date_fin))].copy()
    
    # Round amounts to 2 decimal places to avoid floating point issues globally
    df_periode["montant"] = df_periode["montant"].round(2)

    if df_periode.empty:
        toast_warning("Aucune transaction dans la période sélectionnée.")
        return

    # Calculate key values
    total_revenus = round(df_periode[df_periode["type"] == "revenu"]["montant"].sum(), 2)
    total_depenses = round(df_periode[df_periode["type"] == "dépense"]["montant"].sum(), 2)
    solde_periode = round(total_revenus - total_depenses, 2)
    nb_transactions = len(df_periode)

    st.markdown("---")

    # ===== HERO SECTION: MAIN BALANCE =====
    st.markdown("### 💰 Votre situation financière")
    
    # Determine color based on balance
    if solde_periode > 0:
        color = "#00D4AA"
        status = "positif"
        emoji = "✅"
    elif solde_periode < 0:
        color = "#FF6B6B"
        status = "négatif"
        emoji = "⚠️"
    else:
        color = "#FFD93D"
        status = "équilibré"
        emoji = "➖"

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        # Big balance card
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, {color}20 0%, {color}10 100%);
            border-left: 5px solid {color};
            padding: 25px;
            border-radius: 10px;
            margin-bottom: 10px;
        ">
            <p style="margin: 0; color: gray; font-size: 14px;">Solde de la période</p>
            <h1 style="margin: 10px 0; color: {color}; font-size: 48px;">{emoji} {solde_periode:+,.2f} €</h1>
            <p style="margin: 0; color: gray; font-size: 16px;">Situation {status}</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.metric(
            "💹 Revenus",
            f"{total_revenus:,.2f} €",
            delta=f"{len(df_periode[df_periode['type'] == 'revenu'])} transactions",
            help="Total des revenus sur la période"
        )

    with col3:
        st.metric(
            "💸 Dépenses", 
            f"{total_depenses:,.2f} €",
            delta=f"{len(df_periode[df_periode['type'] == 'dépense'])} transactions",
            delta_color="inverse",
            help="Total des dépenses sur la période"
        )

    st.markdown("")



    # ===== MONTHLY EVOLUTION - OPEN BY DEFAULT =====
    with st.expander("📈 Évolution mensuelle", expanded=True):
        df_mensuel = df_periode.copy()
        df_mensuel["mois"] = df_mensuel["date"].dt.to_period("M")
        df_mensuel["mois_str"] = df_mensuel["date"].dt.strftime("%b %Y")

        # Prepare data
        df_evolution = df_mensuel.groupby(["mois_str", "type"])["montant"].sum().unstack(fill_value=0)
        df_evolution = df_evolution.reindex(sorted(df_evolution.index, key=lambda x: pd.to_datetime(x, format='%b %Y')))

        if not df_evolution.empty:
            # Ensure both columns exist
            if "dépense" not in df_evolution.columns:
                df_evolution["dépense"] = 0
            if "revenu" not in df_evolution.columns:
                df_evolution["revenu"] = 0

            # Round values for display
            df_evolution["dépense"] = df_evolution["dépense"].round(2)
            df_evolution["revenu"] = df_evolution["revenu"].round(2)

            # Calculate balance
            solde = (df_evolution["revenu"] - df_evolution["dépense"]).round(2)

            # Create Plotly chart
            fig = go.Figure()

            # Revenue bars
            fig.add_trace(go.Bar(
                name='💹 Revenus',
                x=df_evolution.index,
                y=df_evolution["revenu"],
                marker_color='#00D4AA',
                marker_line_color='#00A87E',
                marker_line_width=1.5,
                hovertemplate='<b>%{x}</b><br>Revenus: %{y:,.0f} €<extra></extra>'
            ))

            # Expense bars
            fig.add_trace(go.Bar(
                name='💸 Dépenses',
                x=df_evolution.index,
                y=df_evolution["dépense"],
                marker_color='#FF6B6B',
                marker_line_color='#CC5555',
                marker_line_width=1.5,
                hovertemplate='<b>%{x}</b><br>Dépenses: %{y:,.0f} €<extra></extra>'
            ))

            # Balance line
            fig.add_trace(go.Scatter(
                name='💰 Solde',
                x=df_evolution.index,
                y=solde,
                mode='lines+markers',
                line=dict(color='#4A90E2', width=3),
                marker=dict(size=8, color='#4A90E2', line=dict(color='white', width=2)),
                hovertemplate='<b>%{x}</b><br>Solde: %{y:+,.0f} €<extra></extra>'
            ))

            fig.update_layout(
                title=dict(
                    text='Évolution Revenus, Dépenses et Solde',
                    font=dict(size=18, color='white')
                ),
                xaxis_title='Mois',
                yaxis_title='Montant (€)',
                height=450,
                hovermode='x unified',
                barmode='group',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.25,
                    xanchor="center",
                    x=0.5,
                    font=dict(size=12, color="white"),
                    bgcolor="rgba(0,0,0,0)",
                    bordercolor="white",
                    borderwidth=1
                ),
                margin=dict(t=40, b=80, l=40, r=40),
                paper_bgcolor='#1E1E1E',
                plot_bgcolor='#1E1E1E',
                font=dict(color='white'),
                xaxis=dict(showgrid=False, color='white'),
                yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', zeroline=True, zerolinewidth=2, zerolinecolor='rgba(255,255,255,0.3)', color='white')
            )

            st.plotly_chart(fig, use_container_width=True)

    # ===== DETAILED METRICS (HIDDEN BY DEFAULT) =====
    
    # 1. CATEGORY BREAKDOWN
    with st.expander("🥧 Répartition par catégories"):
        col1, col2 = st.columns(2)

        # Common layout settings for clarity
        layout_settings = dict(
            height=450,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5,
                font=dict(size=12, color="white"),
                bgcolor="rgba(0,0,0,0)",
                bordercolor="white",
                borderwidth=1
            ),
            margin=dict(t=30, b=80, l=40, r=40),
            paper_bgcolor="#1E1E1E",
            plot_bgcolor="#1E1E1E",
            font=dict(color="white")
        )

        # REVENUS FIRST (Left Column)
        with col1:
            st.markdown("**💹 Revenus par catégorie**")
            revenus_df = df_periode[df_periode["type"] == "revenu"]
            if not revenus_df.empty:
                categories_revenus = revenus_df.groupby("categorie", dropna=False)["montant"].sum().sort_values(ascending=False)
                total_revenus_cat = categories_revenus.sum()

                seuil = total_revenus_cat * 0.05
                grandes_categories = categories_revenus[categories_revenus >= seuil]
                petites_categories = categories_revenus[categories_revenus < seuil]
                
                if len(petites_categories) > 0:
                    autres_montant = petites_categories.sum()
                    categories_finales = pd.concat([grandes_categories, pd.Series({'Autres': autres_montant})])
                else:
                    categories_finales = grandes_categories

                colors_palette = [
                    '#00D4AA', '#4ECDC4', '#45B7D1', '#26DE81',
                    '#20BF6B', '#0FB9B1', '#2C3A47', '#A8E6CF',
                    '#26C6DA', '#00ACC1', '#00897B', '#43A047'
                ]
                
                fig = go.Figure(data=[go.Pie(
                    labels=categories_finales.index,
                    values=categories_finales.values,
                    marker=dict(
                        colors=colors_palette[:len(categories_finales)], 
                        line=dict(color='white', width=1)
                    ),
                    hovertemplate='<b>%{label}</b><br>Montant: %{value:,.0f} €<br>Part: %{percent}<extra></extra>',
                    textinfo='label+percent',
                    textposition='outside',
                    textfont=dict(size=13, family='Arial Black', color='white'),
                    pull=[0.05 if cat == 'Autres' else 0 for cat in categories_finales.index]
                )])

                fig.update_layout(**layout_settings)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Aucun revenu")

        # DEPENSES SECOND (Right Column)
        with col2:
            st.markdown("**💸 Dépenses par catégorie**")
            depenses_df = df_periode[df_periode["type"] == "dépense"]
            if not depenses_df.empty:
                categories_depenses = depenses_df.groupby("categorie")["montant"].sum().sort_values(ascending=False)
                total_depenses_cat = categories_depenses.sum()

                seuil = total_depenses_cat * 0.05
                grandes_categories = categories_depenses[categories_depenses >= seuil]
                petites_categories = categories_depenses[categories_depenses < seuil]
                
                if len(petites_categories) > 0:
                    autres_montant = petites_categories.sum()
                    categories_finales = pd.concat([grandes_categories, pd.Series({'Autres': autres_montant})])
                else:
                    categories_finales = grandes_categories

                colors_palette = [
                    '#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', 
                    '#98D8C8', '#FFD93D', '#6C5CE7', '#A8E6CF',
                    '#FF8B94', '#C7CEEA', '#FFDAC1', '#B4A7D6'
                ]
                
                fig = go.Figure(data=[go.Pie(
                    labels=categories_finales.index,
                    values=categories_finales.values,
                    marker=dict(
                        colors=colors_palette[:len(categories_finales)], 
                        line=dict(color='white', width=1)
                    ),
                    hovertemplate='<b>%{label}</b><br>Montant: %{value:,.0f} €<br>Part: %{percent}<extra></extra>',
                    textinfo='label+percent',
                    textposition='outside',
                    textfont=dict(size=13, family='Arial Black', color='white'),
                    pull=[0.05 if cat == 'Autres' else 0 for cat in categories_finales.index]
                )])

                fig.update_layout(**layout_settings)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Aucune dépense")

    # ===== TOP TRANSACTIONS - CLOSED =====
    with st.expander("🎯 Tops transactions"):
        col1, col2 = st.columns([1, 3])

        with col1:
            type_top = st.radio("Type", ["💸 Dépenses", "💹 Revenus"], key="type_top")
            nombre_top = st.selectbox("Nombre", [5, 10, 15, 20], key="nb_top")

        with col2:
            if type_top == "💸 Dépenses":
                top_trans = df_periode[df_periode["type"] == "dépense"].nlargest(nombre_top, "montant")
                couleur = "#FF6B6B"
            else:
                top_trans = df_periode[df_periode["type"] == "revenu"].nlargest(nombre_top, "montant")
                couleur = "#00D4AA"

            if not top_trans.empty:
                # Plotly horizontal bar chart
                labels = [f"{row['categorie']}" for _, row in top_trans.iterrows()]
                dates = [row['date'].strftime('%d/%m/%y') for _, row in top_trans.iterrows()]

                fig = go.Figure()

                fig.add_trace(go.Bar(
                    y=labels,
                    x=top_trans["montant"],
                    orientation='h',
                    marker_color=couleur,
                    marker_line_color='white',
                    marker_line_width=1,
                    text=top_trans["montant"].apply(lambda x: f"{x:.0f}€"),
                    textposition='outside',
                    textfont=dict(color='white'),
                    hovertemplate='<b>%{y}</b><br>Montant: %{x:,.0f} €<br>Date: %{customdata}<extra></extra>',
                    customdata=dates
                ))

                fig.update_layout(
                    title=dict(
                        text=f'Top {nombre_top} {type_top}',
                        font=dict(size=16, color='white')
                    ),
                    xaxis_title='Montant (€)',
                    height=max(400, nombre_top * 40),
                    showlegend=False,
                    yaxis=dict(autorange="reversed", color='white'),
                    paper_bgcolor='#1E1E1E',
                    plot_bgcolor='#1E1E1E',
                    xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', color='white'),
                    yaxis_showgrid=False,
                    font=dict(color='white')
                )

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Aucune transaction")

    # ===== RECENT TRANSACTIONS - CLOSED =====
    with st.expander("🕒 Dernières transactions"):
        nb_dernieres = st.slider("Nombre de transactions", 5, 20, 10, key="nb_dernieres")
        dernieres = df_periode.sort_values("date", ascending=False).head(nb_dernieres)

        if not dernieres.empty:
            for idx, trans in dernieres.iterrows():
                col1, col2, col3 = st.columns([1, 3, 1])

                with col1:
                    icone = "💸" if trans["type"] == "dépense" else "💹"
                    st.write(f"{icone}")

                with col2:
                    st.write(f"**{trans['categorie']}** → {trans['sous_categorie']}")
                    st.caption(f"📅 {trans['date'].strftime('%d/%m/%Y')}")

                with col3:
                    couleur = "#FF6B6B" if trans["type"] == "dépense" else "#00D4AA"
                    signe = "-" if trans["type"] == "dépense" else "+"
                    st.markdown(f"<p style='color: {couleur}; text-align: right; font-weight: bold;'>{signe}{trans['montant']:.2f} €</p>", unsafe_allow_html=True)

                st.markdown("---")
        else:
            st.info("Aucune transaction")
