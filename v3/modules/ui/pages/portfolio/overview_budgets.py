"""
Overview & Budgets Combined Tab

This module combines the former separate tabs for overview and budget management
into a single unified interface with vertical layout.

Structure:
1. Global period selector
2. Section 1: Visual Overview (graph + key metrics)
3. Section 2: Budget Management (add/modify/delete)
4. Section 3: Detailed Analysis (advanced metrics)
"""

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
import plotly.graph_objects as go
from modules.ui.helpers import load_transactions, refresh_and_rerun
from modules.ui.components import toast_success, toast_warning, toast_error
from .helpers import (
    get_period_start_date,
    calculate_months_in_period,
    analyze_exceptional_expenses
)


def render_overview_budgets_tab(conn: sqlite3.Connection, cursor: sqlite3.Cursor) -> None:
    """
    Render the combined overview and budgets tab.

    Features:
    - Global period selector
    - Visual overview with charts
    - Budget management (add/modify/delete)
    - Detailed financial analysis

    Args:
        conn: Database connection
        cursor: Database cursor
    """
    st.subheader("📊 Vue d'ensemble & Budgets")

    # ===== GLOBAL PERIOD SELECTOR =====
    st.markdown("#### ⏰ Période d'analyse")
    period = st.selectbox(
        "Visualiser la période:",
        ["Ce mois", "2 derniers mois", "3 derniers mois", "6 derniers mois", "Depuis le début"],
        index=0,  # Par défaut "Ce mois"
        key="period_selector_overview_budgets"
    )
    period_start_date = get_period_start_date(period)
    st.markdown(f"*Affichage depuis: **{period_start_date.strftime('%d/%m/%Y') if period_start_date else 'le début'}***")
    st.markdown("---")

    # Load data
    df_budgets = pd.read_sql_query(
        "SELECT * FROM budgets_categories ORDER BY categorie",
        conn
    )
    df_transactions = load_transactions()

    # Determine start date for filtering
    if period_start_date is None:
        # "Depuis le début" - use first transaction
        if not df_transactions.empty:
            start_date = pd.to_datetime(df_transactions["date"]).min().date()
        else:
            start_date = date.today().replace(day=1)
    else:
        start_date = period_start_date

    # Calculate number of months in period
    nb_mois = calculate_months_in_period(start_date)
    if nb_mois is None:
        nb_mois = 1

    # ===== CATEGORY FILTER =====
    st.markdown("#### 🏷️ Filtre par catégorie")
    
    # Get all budget categories for the filter
    if not df_budgets.empty:
        all_categories = sorted(df_budgets["categorie"].unique().tolist())
        
        selected_categories = st.multiselect(
            "Sélectionner les catégories à afficher :",
            options=all_categories,
            default=all_categories,  # All selected by default
            key="category_filter_overview",
            help="Sélectionnez une ou plusieurs catégories pour filtrer les graphiques et métriques. Par défaut, toutes les catégories sont affichées."
        )
        
        # Filter budgets by selected categories
        if selected_categories:
            df_budgets_filtered = df_budgets[df_budgets["categorie"].isin(selected_categories)]
        else:
            df_budgets_filtered = df_budgets.copy()
            st.warning("⚠️ Aucune catégorie sélectionnée - affichage de toutes les catégories")
    else:
        df_budgets_filtered = df_budgets.copy()
        selected_categories = []
    
    st.markdown("---")

    # ===== SECTION 1: VISUAL OVERVIEW =====
    st.markdown("### 📊 Vue d'ensemble")

    if df_budgets_filtered.empty:
        st.info("💡 Définissez des budgets pour voir les statistiques")
    else:
        # Calculate totals for the period (using filtered budgets)
        budget_total_periode = df_budgets_filtered["budget_mensuel"].sum() * nb_mois

        if not df_transactions.empty and selected_categories:
            # Filter transactions by selected categories
            depenses_periode_total = df_transactions[
                (df_transactions["type"] == "dépense") &
                (df_transactions["categorie"].isin(selected_categories)) &
                (pd.to_datetime(df_transactions["date"]).dt.date >= start_date)
            ]["montant"].sum()
        else:
            depenses_periode_total = 0.0

        reste_total = budget_total_periode - depenses_periode_total
        pourcentage_total = (depenses_periode_total / budget_total_periode * 100) if budget_total_periode > 0 else 0

        # Display key metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("💰 Budget total", f"{budget_total_periode:.0f} €")

        with col2:
            st.metric("💸 Dépensé", f"{depenses_periode_total:.0f} €")

        with col3:
            delta_color = "normal" if reste_total >= 0 else "inverse"
            st.metric("💵 Reste", f"{reste_total:.0f} €", delta_color=delta_color)

        with col4:
            st.metric("📊 % utilisé", f"{pourcentage_total:.1f}%")

        # Chart: Budget vs Expenses by category
        st.markdown("")
        st.markdown("#### 📊 Répartition par catégorie")

        if not df_transactions.empty:
            depenses_par_cat = []

            for _, budget in df_budgets_filtered.iterrows():
                categorie = budget["categorie"]
                budget_mensuel = budget["budget_mensuel"]
                budget_periode = budget_mensuel * nb_mois

                depenses = df_transactions[
                    (df_transactions["type"] == "dépense") &
                    (df_transactions["categorie"] == categorie) &
                    (pd.to_datetime(df_transactions["date"]).dt.date >= start_date)
                ]["montant"].sum()

                depenses_par_cat.append({
                    "Catégorie": categorie,
                    "Dépensé": depenses,
                    "Budget": budget_periode,
                    "% du budget": (depenses / budget_periode * 100) if budget_periode > 0 else 0
                })

            df_depenses = pd.DataFrame(depenses_par_cat)

            if not df_depenses.empty:
                # Layout en colonnes pour les deux graphiques
                col_chart1, col_chart2 = st.columns([3, 2])

                with col_chart1:
                    # Bar chart amélioré
                    fig_bar = go.Figure()

                    fig_bar.add_trace(go.Bar(
                        name='Budget prévu',
                        x=df_depenses['Catégorie'],
                        y=df_depenses['Budget'],
                        marker_color='lightblue',
                        marker_line_color='darkblue',
                        marker_line_width=1.5,
                        hovertemplate='<b>%{x}</b><br>Budget: %{y:.2f} €<extra></extra>'
                    ))

                    fig_bar.add_trace(go.Bar(
                        name='Montant dépensé',
                        x=df_depenses['Catégorie'],
                        y=df_depenses['Dépensé'],
                        marker_color='salmon',
                        marker_line_color='darkred',
                        marker_line_width=1.5,
                        hovertemplate='<b>%{x}</b><br>Dépensé: %{y:.2f} €<br>(%{text}% du budget)<extra></extra>',
                        text=df_depenses['% du budget'].round(1)
                    ))

                    fig_bar.update_layout(
                        barmode='group',
                        title=dict(
                            text=f'Budget vs Dépenses par catégorie ({period})',
                            font=dict(size=16)
                        ),
                        xaxis_title='Catégorie',
                        yaxis_title='Montant (€)',
                        height=400,
                        hovermode='x unified',
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1
                        ),
                        plot_bgcolor='rgba(0,0,0,0)',
                        xaxis=dict(showgrid=False),
                        yaxis=dict(showgrid=True, gridcolor='lightgray')
                    )

                    st.plotly_chart(fig_bar, use_container_width=True)

                with col_chart2:
                    # Pie chart pour la répartition des dépenses
                    fig_pie = go.Figure()

                    # Filtrer les catégories avec dépenses > 0
                    df_depenses_pie = df_depenses[df_depenses['Dépensé'] > 0].copy()

                    if not df_depenses_pie.empty:
                        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#FFD93D', '#6C5CE7']

                        fig_pie.add_trace(go.Pie(
                            labels=df_depenses_pie['Catégorie'],
                            values=df_depenses_pie['Dépensé'],
                            marker=dict(colors=colors[:len(df_depenses_pie)], line=dict(color='white', width=2)),
                            hovertemplate='<b>%{label}</b><br>Montant: %{value:.2f} €<br>%{percent}<extra></extra>',
                            textinfo='label+percent',
                            textposition='auto'
                        ))

                        fig_pie.update_layout(
                            title=dict(
                                text='Répartition des dépenses',
                                font=dict(size=14)
                            ),
                            height=400,
                            showlegend=False
                        )

                        st.plotly_chart(fig_pie, use_container_width=True)
                    else:
                        st.info("Aucune dépense à afficher pour cette période")

    st.markdown("---")

    # ===== SECTION 2: BUDGET MANAGEMENT =====
    st.markdown("### ⚙️ Gestion des budgets")

    # Load expense categories
    if not df_transactions.empty:
        categories_depenses = sorted(
            df_transactions[df_transactions["type"] == "dépense"]["categorie"]
            .dropna()
            .unique()
            .tolist()
        )
    else:
        categories_depenses = []

    # ===== ADD/MODIFY BUDGET =====
    st.markdown("#### ➕ Ajouter/Modifier un budget")

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        # Choice between existing or new category
        mode_ajout = st.radio(
            "Mode",
            ["Catégorie existante", "Nouvelle catégorie"],
            horizontal=True,
            key="mode_budget_overview"
        )

        if mode_ajout == "Catégorie existante":
            if categories_depenses:
                categorie_budget = st.selectbox(
                    "Catégorie",
                    categories_depenses,
                    key="cat_budget_existante_overview"
                )
            else:
                st.warning("Aucune catégorie de dépense trouvée")
                categorie_budget = None
        else:
            categorie_budget = st.text_input(
                "Nom de la catégorie",
                key="cat_budget_nouvelle_overview"
            )

    with col2:
        montant_budget = st.number_input(
            "Budget mensuel (€)",
            min_value=0.0,
            step=10.0,
            value=100.0,
            key="montant_budget_overview"
        )

    with col3:
        st.write("")  # Spacing
        st.write("")  # Spacing
        if st.button("💾 Enregistrer", type="primary", key="save_budget_overview"):
            if categorie_budget and categorie_budget.strip():
                try:
                    cursor.execute("""
                        INSERT INTO budgets_categories (categorie, budget_mensuel, date_creation, date_modification)
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT(categorie) DO UPDATE SET
                            budget_mensuel = excluded.budget_mensuel,
                            date_modification = excluded.date_modification
                    """, (
                        categorie_budget.strip(),
                        montant_budget,
                        datetime.now().isoformat(),
                        datetime.now().isoformat()
                    ))
                    conn.commit()
                    toast_success(f"Budget pour '{categorie_budget}' enregistré !")
                    refresh_and_rerun()
                except Exception as e:
                    toast_error(f"Erreur : {e}")
            else:
                toast_warning("Veuillez sélectionner ou saisir une catégorie")

    # ===== DELETE BUDGET =====
    if not df_budgets.empty:
        st.markdown("")
        st.markdown("#### 🗑️ Supprimer un budget")

        col1, col2 = st.columns([2, 1])

        with col1:
            budget_to_delete = st.selectbox(
                "Catégorie à supprimer",
                df_budgets["categorie"].tolist(),
                key="budget_delete_overview"
            )

        with col2:
            st.write("")  # Spacing
            st.write("")  # Spacing
            if st.button("🗑️ Supprimer", type="secondary", key="delete_budget_overview"):
                cursor.execute(
                    "DELETE FROM budgets_categories WHERE categorie = ?",
                    (budget_to_delete,)
                )
                conn.commit()
                toast_success(f"Budget '{budget_to_delete}' supprimé")
                refresh_and_rerun()

    # ===== CURRENT BUDGETS TABLE =====
    st.markdown("")
    
    # Header with export button
    col_header1, col_header2 = st.columns([3, 1])
    with col_header1:
        st.markdown("#### 📌 Budgets actuels")
    with col_header2:
        # Export CSV button
        if not df_budgets_filtered.empty:
            csv_data = df_budgets_filtered.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 Exporter CSV",
                data=csv_data,
                file_name=f"budgets_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                help="Télécharger les budgets au format CSV",
                key="export_budgets_csv"
            )

    if df_budgets_filtered.empty:
        if not df_budgets.empty:
            st.info("💡 Aucune catégorie sélectionnée dans le filtre")
        else:
            st.info("💡 Aucun budget défini. Commencez par en ajouter ci-dessus !")
    else:
        # Check for budgets near limit and create alerts
        budgets_alerts = []
        
        # Prepare display with percentages
        budgets_display = []

        for _, budget in df_budgets_filtered.iterrows():
            categorie = budget["categorie"]
            budget_mensuel = budget["budget_mensuel"]
            budget_periode = budget_mensuel * nb_mois

            # Calculate expenses for selected period
            if not df_transactions.empty:
                depenses_periode = df_transactions[
                    (df_transactions["type"] == "dépense") &
                    (df_transactions["categorie"] == categorie) &
                    (pd.to_datetime(df_transactions["date"]).dt.date >= start_date)
                ]["montant"].sum()
            else:
                depenses_periode = 0.0

            # Calculate percentage used
            if budget_periode > 0:
                pourcentage = (depenses_periode / budget_periode) * 100
            else:
                pourcentage = 0

            # Determine color
            if pourcentage >= 100:
                couleur = "🔴"
                status = "Dépassé"
            elif pourcentage >= 80:
                couleur = "🟠"
                status = "Attention"
                # Add to alerts
                budgets_alerts.append({
                    "categorie": categorie,
                    "pourcentage": pourcentage,
                    "reste": budget_periode - depenses_periode
                })
            elif pourcentage >= 50:
                couleur = "🟡"
                status = "Bon"
            else:
                couleur = "🟢"
                status = "Excellent"

            budgets_display.append({
                "Catégorie": f"{couleur} {categorie}",
                "Budget (€)": f"{budget_periode:.2f}",
                "Dépensé (€)": f"{depenses_periode:.2f}",
                "Reste (€)": f"{budget_periode - depenses_periode:.2f}",
                "% utilisé": f"{pourcentage:.1f}%",
                "État": status
            })

        # Display alerts if any
        if budgets_alerts:
            st.warning(f"⚠️ **{len(budgets_alerts)} budget(s)** proche(s) du dépassement (>80%):")
            alert_text = " • ".join([f"**{a['categorie']}** ({a['pourcentage']:.0f}% utilisé, reste {a['reste']:.0f}€)" for a in budgets_alerts])
            st.caption(alert_text)

        # Display table
        st.dataframe(
            pd.DataFrame(budgets_display),
            use_container_width=True,
            hide_index=True
        )

    st.markdown("---")

    # ===== SECTION 3: DETAILED ANALYSIS =====
    st.markdown("### 💰 Analyse financière détaillée")

    metrics = analyze_exceptional_expenses(period_start_date)

    # Section 1: Revenues
    st.markdown("**1️⃣ Vos revenus**")
    col1 = st.columns(1)[0]
    with col1:
        st.metric(
            "💵 Total de vos revenus",
            f"{metrics['SRR']:.2f} €",
            help="Somme de tous les revenus perçus sur la période sélectionnée (salaires, freelance, etc.)"
        )

    st.markdown("")

    # Section 2: Budget breakdown
    st.markdown("**2️⃣ Comparaison budgets et dépenses**")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "📊 Budgets prévus",
            f"{metrics['SBT']:.2f} €",
            help="Total des budgets que vous avez définis pour vos catégories de dépenses"
        )

    with col2:
        st.metric(
            "💸 Dépenses dans les budgets",
            f"{metrics['SRB']:.2f} €",
            help="Montant réellement dépensé dans les catégories pour lesquelles vous avez défini un budget"
        )

    with col3:
        # Gap = SRB - SBT
        ecart = metrics['ecart_budgets']
        if ecart > 0:
            st.metric(
                "📈 Dépassement de budget",
                f"{ecart:.2f} €",
                delta=f"⚠️ +{ecart:.2f} €",
                help="Vous avez dépensé plus que prévu dans vos budgets"
            )
        elif ecart < 0:
            st.metric(
                "📉 Économies réalisées",
                f"{abs(ecart):.2f} €",
                delta=f"✅ -{abs(ecart):.2f} €",
                help="Vous avez dépensé moins que prévu dans vos budgets - bien joué !"
            )
        else:
            st.metric(
                "✅ Budgets respectés",
                "0.00 €",
                delta="Parfait!",
                help="Vous avez dépensé exactement ce qui était prévu"
            )

    st.markdown("")

    # Section 3: Exceptional expenses
    st.markdown("**3️⃣ Dépenses hors budget**")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "⚠️ Dépenses non planifiées",
            f"{metrics['SE']:.2f} €",
            help="Dépenses dans des catégories pour lesquelles vous n'avez pas défini de budget (dépenses exceptionnelles)"
        )

    with col2:
        st.metric(
            "📌 Total de vos dépenses",
            f"{metrics['SDR']:.2f} €",
            help="Somme de toutes vos dépenses sur la période (budgétées + non planifiées)"
        )

    with col3:
        if metrics['SDR'] > 0:
            pct_exceptional = (metrics['SE'] / metrics['SDR'] * 100)
            st.metric(
                "% de dépenses imprévues",
                f"{pct_exceptional:.1f}%",
                help="Part des dépenses non planifiées par rapport au total des dépenses"
            )
        else:
            st.metric(
                "% de dépenses imprévues",
                "0.0%",
                help="Part des dépenses non planifiées par rapport au total des dépenses"
            )

    st.markdown("")

    # Section 4: Capacity and reality
    st.markdown("**4️⃣ Votre situation financière**")
    col1, col2 = st.columns(2)

    with col1:
        # Theoretical capacity = SRR - SBT
        capacite = metrics['capacite_theorique']
        if capacite > 0:
            st.metric(
                "🎯 Marge disponible",
                f"{capacite:.2f} €",
                delta="✅ Marge positive",
                help="Argent disponible après avoir couvert vos budgets prévus (Revenus - Budgets planifiés). C'est ce que vous pouvez dépenser en plus."
            )
        elif capacite < 0:
            st.metric(
                "🎯 Déficit prévu",
                f"{capacite:.2f} €",
                delta="⚠️ Déficit",
                help="Vos budgets planifiés dépassent vos revenus. Attention au découvert !"
            )
        else:
            st.metric(
                "🎯 Équilibre parfait",
                "0.00 €",
                help="Vos budgets planifiés correspondent exactement à vos revenus"
            )

    with col2:
        # Reality = SRR - SDR
        solde = metrics['realite']
        if solde > 0:
            st.metric(
                "💰 Votre solde final",
                f"{solde:.2f} €",
                delta="✅ Surplus",
                help="Ce qu'il vous reste réellement après toutes vos dépenses (Revenus - Dépenses totales). C'est votre épargne de la période."
            )
        elif solde < 0:
            st.metric(
                "💰 Votre solde final",
                f"{solde:.2f} €",
                delta="⚠️ Déficit",
                help="Vous êtes en déficit : vous avez plus dépensé que gagné sur cette période"
            )
        else:
            st.metric(
                "💰 Votre solde final",
                "0.00 €",
                help="Vous avez dépensé exactement ce que vous avez gagné"
            )
