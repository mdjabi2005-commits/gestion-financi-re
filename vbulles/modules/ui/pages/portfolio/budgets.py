"""
Budget Management Tab

This module implements Tab 1 of the portfolio interface:
- Budget management by category
- Period analysis (current month, last 2/3/6 months, all time)
- Budget visualization and analysis
- Exceptional expenses tracking
"""

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
from modules.ui.helpers import load_transactions, refresh_and_rerun
from modules.ui.components import toast_success, toast_warning, toast_error
from .helpers import (
    get_period_start_date,
    calculate_months_in_period,
    analyze_exceptional_expenses
)
from config import DB_PATH


def render_budgets_tab(conn: sqlite3.Connection, cursor: sqlite3.Cursor) -> None:
    """
    Render the budgets by category tab.

    Features:
    - Add/modify budgets per category
    - Delete budgets
    - View and analyze current budgets
    - Budget vs actual comparison
    - Period-based analysis

    Args:
        conn: Database connection
        cursor: Database cursor
    """
    st.subheader("💰 Gérer les budgets par catégorie")

    # Sélecteur de période
    st.markdown("#### ⏰ Période d'analyse")
    period = st.selectbox(
        "Visualiser la période:",
        ["Ce mois", "2 derniers mois", "3 derniers mois", "6 derniers mois", "Depuis le début"],
        index=4,  # Par défaut "Depuis le début"
        key="period_selector"
    )
    period_start_date = get_period_start_date(period)
    st.markdown(f"*Affichage depuis: **{period_start_date.strftime('%d/%m/%Y') if period_start_date else 'le début'}***")
    st.markdown("---")

    # Charger les catégories de dépenses existantes
    df_transactions = load_transactions()
    if not df_transactions.empty:
        categories_depenses = sorted(
            df_transactions[df_transactions["type"] == "dépense"]["categorie"]
            .dropna()
            .unique()
            .tolist()
        )
    else:
        categories_depenses = []

    # Charger les budgets existants
    df_budgets = pd.read_sql_query(
        "SELECT * FROM budgets_categories ORDER BY categorie",
        conn
    )

    # ===== AJOUTER/MODIFIER UN BUDGET =====
    st.markdown("#### ➕ Ajouter/Modifier un budget")

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        # Choix entre catégorie existante ou nouvelle
        mode_ajout = st.radio(
            "Mode",
            ["Catégorie existante", "Nouvelle catégorie"],
            horizontal=True,
            key="mode_budget"
        )

        if mode_ajout == "Catégorie existante":
            if categories_depenses:
                categorie_budget = st.selectbox(
                    "Catégorie",
                    categories_depenses,
                    key="cat_budget_existante"
                )
            else:
                st.warning("Aucune catégorie de dépense trouvée")
                categorie_budget = None
        else:
            categorie_budget = st.text_input(
                "Nom de la catégorie",
                key="cat_budget_nouvelle"
            )

    with col2:
        montant_budget = st.number_input(
            "Budget mensuel (€)",
            min_value=0.0,
            step=10.0,
            value=100.0,
            key="montant_budget"
        )

    with col3:
        st.write("")  # Espacement
        st.write("")  # Espacement
        if st.button("💾 Enregistrer", type="primary", key="save_budget"):
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

    # ===== SUPPRIMER UN BUDGET =====
    if not df_budgets.empty:
        st.markdown("---")
        st.markdown("#### 🗑️ Supprimer un budget")

        col1, col2 = st.columns([2, 1])

        with col1:
            budget_to_delete = st.selectbox(
                "Catégorie à supprimer",
                df_budgets["categorie"].tolist(),
                key="budget_delete"
            )

        with col2:
            st.write("")  # Espacement
            st.write("")  # Espacement
            if st.button("🗑️ Supprimer", type="secondary", key="delete_budget"):
                cursor.execute(
                    "DELETE FROM budgets_categories WHERE categorie = ?",
                    (budget_to_delete,)
                )
                conn.commit()
                toast_success(f"Budget '{budget_to_delete}' supprimé")
                refresh_and_rerun()

    st.markdown("---")
    st.markdown("#### 📌 Budgets actuels")

    if df_budgets.empty:
        st.info("💡 Aucun budget défini. Commencez par en ajouter ci-dessous !")
    else:
        # Déterminer la date de début du filtre
        if period_start_date is None:
            # "Depuis le début" - utiliser la première transaction
            if not df_transactions.empty:
                start_date = pd.to_datetime(df_transactions["date"]).min().date()
            else:
                start_date = date.today().replace(day=1)
        else:
            start_date = period_start_date

        # Calculer le nombre de mois dans la période
        nb_mois = calculate_months_in_period(start_date)
        if nb_mois is None:
            nb_mois = 1

        # Préparer l'affichage avec pourcentages
        budgets_display = []

        for _, budget in df_budgets.iterrows():
            categorie = budget["categorie"]
            budget_mensuel = budget["budget_mensuel"]

            # Budget pour toute la période
            budget_periode = budget_mensuel * nb_mois

            # Calculer les dépenses pour la période sélectionnée
            if not df_transactions.empty:
                # Dépenses pour cette période
                depenses_periode = df_transactions[
                    (df_transactions["type"] == "dépense") &
                    (df_transactions["categorie"] == categorie) &
                    (pd.to_datetime(df_transactions["date"]).dt.date >= start_date)
                ]["montant"].sum()

                # Total dépenses
                depenses_mois = depenses_periode
            else:
                depenses_mois = 0.0

            # Calculer le pourcentage utilisé (par rapport au budget de la période)
            if budget_periode > 0:
                pourcentage = (depenses_mois / budget_periode) * 100
            else:
                pourcentage = 0

            # Déterminer la couleur
            if pourcentage >= 100:
                couleur = "🔴"
                status = "Dépassé"
            elif pourcentage >= 80:
                couleur = "🟠"
                status = "Attention"
            elif pourcentage >= 50:
                couleur = "🟡"
                status = "Bon"
            else:
                couleur = "🟢"
                status = "Excellent"

            budgets_display.append({
                "Catégorie": f"{couleur} {categorie}",
                "Budget (€)": f"{budget_periode:.2f}",
                "Dépensé (€)": f"{depenses_mois:.2f}",
                "Reste (€)": f"{budget_periode - depenses_mois:.2f}",
                "% utilisé": f"{pourcentage:.1f}%",
                "État": status
            })

        # Afficher le tableau
        st.dataframe(
            pd.DataFrame(budgets_display),
            use_container_width=True,
            hide_index=True
        )

    st.markdown("---")
    st.markdown("#### 💰 Analyse Solde - Vue d'ensemble")

    metrics = analyze_exceptional_expenses(period_start_date)

    # Section 1: Revenus
    st.markdown("**1️⃣ Revenus**")
    col1 = st.columns(1)[0]
    with col1:
        st.metric("💵 Revenus totaux (SRR)", f"{metrics['SRR']:.2f} €")

    st.markdown("")

    # Section 2: Décomposition des dépenses et budgets
    st.markdown("**2️⃣ Budgets vs Dépenses réelles**")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("📊 Budgets planifiés (SBT)", f"{metrics['SBT']:.2f} €")

    with col2:
        st.metric("💸 Dépenses budgétées (SRB)", f"{metrics['SRB']:.2f} €")

    with col3:
        # Écart = SRB - SBT
        ecart = metrics['ecart_budgets']
        if ecart > 0:
            st.metric("📈 Dépassement budgets", f"{ecart:.2f} €", delta=f"⚠️ +{ecart:.2f} €")
        elif ecart < 0:
            st.metric("📉 Économies budgets", f"{abs(ecart):.2f} €", delta=f"✅ -{abs(ecart):.2f} €")
        else:
            st.metric("✅ Budgets respectés", "0.00 €", delta="Parfait!")

    st.markdown("")

    # Section 3: Dépenses exceptionnelles
    st.markdown("**3️⃣ Dépenses exceptionnelles**")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("⚠️ Dépenses sans budget (SE)", f"{metrics['SE']:.2f} €")

    with col2:
        st.metric("📌 Total dépenses (SDR)", f"{metrics['SDR']:.2f} €")

    with col3:
        if metrics['SDR'] > 0:
            pct_exceptional = (metrics['SE'] / metrics['SDR'] * 100)
            st.metric("% exceptionnel", f"{pct_exceptional:.1f}%")
        else:
            st.metric("% exceptionnel", "0.0%")

    st.markdown("")

    # Section 4: Capacité de gestion
    st.markdown("**4️⃣ Capacité et réalité**")
    col1, col2 = st.columns(2)

    with col1:
        # Capacité théorique = SRR - SBT
        capacite = metrics['capacite_theorique']
        if capacite > 0:
            st.metric("🎯 Marge pour exceptions (SRR-SBT)", f"{capacite:.2f} €",
                     delta="✅ Marge positive")
        elif capacite < 0:
            st.metric("🎯 Déficit théorique (SRR-SBT)", f"{capacite:.2f} €",
                     delta="⚠️ Déficit")
        else:
            st.metric("🎯 Équilibre théorique", "0.00 €")

    with col2:
        # Réalité = SRR - SDR
        solde = metrics['realite']
        if solde > 0:
            st.metric("💰 Solde réel final (SRR-SDR)", f"{solde:.2f} €",
                     delta="✅ Surplus")
        elif solde < 0:
            st.metric("💰 Solde réel final (SRR-SDR)", f"{solde:.2f} €",
                     delta="⚠️ Déficit")
        else:
            st.metric("💰 Solde réel final", "0.00 €")
