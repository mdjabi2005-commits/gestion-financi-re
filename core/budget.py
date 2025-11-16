# -*- coding: utf-8 -*-
"""
Module budget - Partie de l'application gestiov4
Généré automatiquement par migrate_to_modular.py
"""

import pandas as pd
import sqlite3
from datetime import date
from dateutil.relativedelta import relativedelta
from config import DB_PATH
from core.transactions import load_transactions


def analyze_exceptional_expenses(period_start_date=None):
    """
    Analyse complète des dépenses avec décomposition par budgets et exceptions.

    Métriques calculées:
    - SRR: Solde Revenus Réelle = somme de tous les revenus
    - SBT: Solde Budget Théorique = somme de tous les budgets planifiés
    - SRB: Solde Réel Budget = somme des dépenses pour catégories avec budget
    - SE: Solde Exceptionnel = somme des dépenses sans budget
    - SDR: Solde Dépense Réelle = SRB + SE (total dépenses)

    Comparaisons:
    - Écart budgets = SRB - SBT (positif = dépassement, négatif = économies)
    - Capacité théorique = SRR - SBT (si positif, marge pour exceptions)
    - Réalité = SRR - SDR (solde final réel)

    Args:
        period_start_date: date or None - Date de début du filtre (None = depuis le début)
    """
    df_transactions = load_transactions()

    # Filtrer par période si fournie
    if period_start_date is not None:
        df_transactions["date"] = pd.to_datetime(df_transactions["date"])
        df_transactions = df_transactions[df_transactions["date"].dt.date >= period_start_date]

    conn = sqlite3.connect(DB_PATH)
    df_budgets = pd.read_sql_query("SELECT categorie, budget_mensuel FROM budgets_categories", conn)
    conn.close()

    if df_transactions.empty:
        return {
            "SRR": 0.0,  # Solde Revenus Réelle
            "SBT": 0.0,  # Solde Budget Théorique
            "SRB": 0.0,  # Solde Réel Budget
            "SE": 0.0,   # Solde Exceptionnel
            "SDR": 0.0,  # Solde Dépense Réelle
            "ecart_budgets": 0.0,
            "capacite_theorique": 0.0,
            "realite": 0.0
        }

    # Calculer le nombre de mois dans la période
    if period_start_date is None:
        # "Depuis le début" - calculer depuis la première transaction
        first_transaction_date = pd.to_datetime(df_transactions["date"]).min().date()
        nb_mois = calculate_months_in_period(first_transaction_date)
        if nb_mois is None:
            nb_mois = 1
    else:
        nb_mois = calculate_months_in_period(period_start_date)
        if nb_mois is None:
            nb_mois = 1

    # SRR: Total revenus
    SRR = df_transactions[df_transactions["type"] == "revenu"]["montant"].sum()

    # SBT: Total budgets théoriques (multiplié par le nombre de mois)
    SBT_mensuel = df_budgets["budget_mensuel"].sum() if not df_budgets.empty else 0.0
    SBT = SBT_mensuel * nb_mois

    # Récupérer les catégories avec budget
    categories_avec_budget = set(df_budgets["categorie"].tolist()) if not df_budgets.empty else set()

    # SRB: Dépenses réelles pour catégories avec budget
    if categories_avec_budget:
        SRB = df_transactions[
            (df_transactions["type"] == "dépense") &
            (df_transactions["categorie"].isin(categories_avec_budget))
        ]["montant"].sum()
    else:
        SRB = 0.0

    # SE: Dépenses exceptionnelles (sans budget)
    SE = df_transactions[
        (df_transactions["type"] == "dépense") &
        (~df_transactions["categorie"].isin(categories_avec_budget))
    ]["montant"].sum()

    # SDR: Total dépenses réelles = SRB + SE
    SDR = SRB + SE

    # Écart budgets = SRB - SBT
    ecart_budgets = SRB - SBT

    # Capacité théorique = SRR - SBT
    capacite_theorique = SRR - SBT

    # Réalité = SRR - SDR
    realite = SRR - SDR

    return {
        "SRR": SRR,
        "SBT": SBT,
        "SRB": SRB,
        "SE": SE,
        "SDR": SDR,
        "ecart_budgets": ecart_budgets,
        "capacite_theorique": capacite_theorique,
        "realite": realite
    }


def analyze_budget_history():
    """
    Analyse l'historique des budgets depuis le début (première transaction).
    Retourne un DataFrame avec:
    - Dépenses totales par catégorie
    - Nombre de mois écoulés
    - Respect du budget historique
    - Montant restant/dépassé pour respecter le budget
    """
    df_transactions = load_transactions()

    conn = sqlite3.connect(DB_PATH)
    df_budgets = pd.read_sql_query("SELECT * FROM budgets_categories", conn)
    conn.close()

    if df_budgets.empty or df_transactions.empty:
        return pd.DataFrame(), 0

    analysis = []

    # Calculer le nombre de mois depuis le début
    if not df_transactions.empty:
        first_date = pd.to_datetime(df_transactions["date"]).min().date()
        last_date = pd.to_datetime(df_transactions["date"]).max().date()
        months_elapsed = max(1, (last_date.year - first_date.year) * 12 + (last_date.month - first_date.month) + 1)
    else:
        months_elapsed = 1

    for _, budget in df_budgets.iterrows():
        categorie = budget["categorie"]
        budget_mensuel = budget["budget_mensuel"]

        # Calculer les dépenses totales pour cette catégorie (inclut les récurrences backfill)
        depenses_totales = df_transactions[
            (df_transactions["type"] == "dépense") &
            (df_transactions["categorie"] == categorie)
        ]["montant"].sum()

        # Budget total pour la période
        budget_total_periode = budget_mensuel * months_elapsed

        # Moyenne par mois réellement dépensée
        moyenne_par_mois = depenses_totales / months_elapsed if months_elapsed > 0 else 0

        # Montant restant ou dépassé
        reste = budget_total_periode - depenses_totales

        # Déterminer le statut
        if reste >= 0:
            status = "🟢 Respecté"
            reste_display = f"{reste:.2f}"
        else:
            status = "🔴 Dépassé"
            reste_display = f"{abs(reste):.2f}"  # Afficher la valeur positive mais avec le statut dépassé

        analysis.append({
            "Catégorie": categorie,
            "Budget mensuel (€)": f"{budget_mensuel:.2f}",
            "Budget total {m} mois (€)".format(m=months_elapsed): f"{budget_total_periode:.2f}",
            "Dépensé total (€)": f"{depenses_totales:.2f}",
            "Moy/mois (€)": f"{moyenne_par_mois:.2f}",
            "Reste (€)": reste_display,
            "Statut": status
        })

    return pd.DataFrame(analysis), months_elapsed


def analyze_monthly_budget_coverage():
    """
    Analyse la couverture budgétaire mois par mois.
    Pour chaque mois avec des transactions, affiche:
    - Revenus du mois
    - Budget total du mois
    - Dépenses réelles du mois
    - Status: Revenus suffisants ou insuffisants
    """
    df_transactions = load_transactions()

    conn = sqlite3.connect(DB_PATH)
    df_budgets = pd.read_sql_query("SELECT * FROM budgets_categories", conn)
    conn.close()

    if df_transactions.empty or df_budgets.empty:
        return pd.DataFrame()

    # Convertir les dates
    df_transactions["date"] = pd.to_datetime(df_transactions["date"])

    # Créer une colonne année-mois
    df_transactions["year_month"] = df_transactions["date"].dt.to_period("M")

    # Récupérer tous les mois uniques avec transactions
    mois_uniques = sorted(df_transactions["year_month"].unique())

    analysis = []
    budget_total = df_budgets["budget_mensuel"].sum()

    for year_month in mois_uniques:
        # Filtrer les transactions du mois
        df_mois = df_transactions[df_transactions["year_month"] == year_month]

        # Revenus du mois
        revenus = df_mois[df_mois["type"] == "revenu"]["montant"].sum()

        # Dépenses du mois
        depenses = df_mois[df_mois["type"] == "dépense"]["montant"].sum()

        # Déterminer le status
        if revenus >= budget_total:
            status = "✅ Revenus suffisants"
            couleur = "green"
        else:
            status = "⚠️ Revenus insuffisants"
            couleur = "red"

        # Calculer le solde
        solde = revenus - depenses

        analysis.append({
            "Mois": str(year_month),
            "Revenus (€)": f"{revenus:.2f}",
            "Budget total (€)": f"{budget_total:.2f}",
            "Dépenses (€)": f"{depenses:.2f}",
            "Solde (€)": f"{solde:.2f}",
            "Status": status
        })

    return pd.DataFrame(analysis)


def get_period_start_date(period):
    """
    Calcule la date de début selon la période sélectionnée.

    Args:
        period: str - "Ce mois", "2 derniers mois", "3 derniers mois", "Depuis le début"

    Returns:
        date or None - Date de début (None = depuis le début)
    """
    today = date.today()

    if period == "Ce mois":
        return today.replace(day=1)
    elif period == "2 derniers mois":
        return (today.replace(day=1) - relativedelta(months=1)).replace(day=1)
    elif period == "3 derniers mois":
        return (today.replace(day=1) - relativedelta(months=2)).replace(day=1)
    elif period == "6 derniers mois":
        return (today.replace(day=1) - relativedelta(months=5)).replace(day=1)
    elif period == "Depuis le début":
        return None
    else:
        return None


def calculate_months_in_period(start_date, end_date=None):
    """
    Calcule le nombre de mois dans une période.

    Args:
        start_date: date or None - Date de début (None = retourne 1)
        end_date: date or None - Date de fin (None = aujourd'hui)

    Returns:
        int - Nombre de mois dans la période (minimum 1)
    """
    if start_date is None:
        # Si pas de date de début (depuis le début), on ne peut pas calculer
        # On retournera le nombre de mois depuis la première transaction
        return None

    if end_date is None:
        end_date = date.today()

    # Calculer la différence en mois
    # On utilise relativedelta pour une différence précise en mois
    delta = relativedelta(end_date, start_date)
    months = delta.years * 12 + delta.months + 1  # +1 pour inclure le mois de début

    return max(1, months)  # Au minimum 1 mois


