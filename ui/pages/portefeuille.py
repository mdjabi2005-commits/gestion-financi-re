# -*- coding: utf-8 -*-
"""
Module portefeuille - Partie de l'application gestiov4
Généré automatiquement par migrate_to_modular.py
"""

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
from core.budget import analyze_exceptional_expenses, get_period_start_date, calculate_months_in_period
from core.transactions import load_transactions
from core.database import get_db_connection
from ui.components import toast_success, toast_warning, toast_error, refresh_and_rerun


def interface_portefeuille():
    """Interface de gestion du portefeuille : budgets, notes et statistiques"""
    st.title("💼 Mon Portefeuille")

    # Initialiser les tables si elles n'existent pas
    conn = get_db_connection()
    cursor = conn.cursor()

    # Table budgets par catégorie
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS budgets_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            categorie TEXT UNIQUE NOT NULL,
            budget_mensuel REAL NOT NULL,
            date_creation TEXT,
            date_modification TEXT
        )
    """)

    # Table objectifs financiers (remplace les notes)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS objectifs_financiers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type_objectif TEXT NOT NULL,
            titre TEXT NOT NULL,
            montant_cible REAL,
            date_limite TEXT,
            periodicite TEXT,
            statut TEXT DEFAULT 'en_cours',
            date_creation TEXT,
            date_modification TEXT,
            date_atteint TEXT
        )
    """)

    # Table échéances pour gérer les prévisions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS echeances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            categorie TEXT NOT NULL,
            sous_categorie TEXT,
            montant REAL NOT NULL,
            date_echeance TEXT NOT NULL,
            recurrence TEXT,
            statut TEXT DEFAULT 'active',
            type_echeance TEXT DEFAULT 'prévue',
            description TEXT,
            date_creation TEXT,
            date_modification TEXT
        )
    """)

    # Migration : Ajouter la colonne type_echeance si elle n'existe pas
    try:
        cursor.execute("SELECT type_echeance FROM echeances LIMIT 1")
    except:
        cursor.execute("ALTER TABLE echeances ADD COLUMN type_echeance TEXT DEFAULT 'prévue'")
        conn.commit()

    conn.commit()

    # Normaliser la colonne recurrence pour la cohérence des données
    normalize_recurrence_column()

    # Backfill les transactions récurrentes jusqu'à aujourd'hui
    # IMPORTANT: Cela doit être fait AVANT de charger les transactions
    backfill_recurrences_to_today(DB_PATH)

    # Onglets principaux
    tab1, tab2, tab3, tab4 = st.tabs(["💰 Budgets par catégorie", "🎯 Objectifs", "📊 Vue d'ensemble", "📅 Prévisions"])

    # ===== ONGLET 1: BUDGETS PAR CATÉGORIE =====
    with tab1:
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
                st.metric("✅ Budgets respectés", f"0.00 €", delta="Parfait!")

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
                st.metric("% exceptionnel", f"0.0%")

        st.markdown("")

        # Section 4: Capacité de gestion
        st.markdown("**4️⃣ Capacité et réalité**")
        col1, col2 = st.columns(2)

        with col1:
            # Capacité théorique = SRR - SBT
            capacite = metrics['capacite_theorique']
            if capacite > 0:
                st.metric("🎯 Marge pour exceptions (SRR-SBT)", f"{capacite:.2f} €",
                         delta=f"✅ Marge positive")
            elif capacite < 0:
                st.metric("🎯 Déficit théorique (SRR-SBT)", f"{capacite:.2f} €",
                         delta=f"⚠️ Déficit")
            else:
                st.metric("🎯 Équilibre théorique", f"0.00 €")

        with col2:
            # Réalité = SRR - SDR
            solde = metrics['realite']
            if solde > 0:
                st.metric("💰 Solde réel final (SRR-SDR)", f"{solde:.2f} €",
                         delta=f"✅ Surplus")
            elif solde < 0:
                st.metric("💰 Solde réel final (SRR-SDR)", f"{solde:.2f} €",
                         delta=f"⚠️ Déficit")
            else:
                st.metric("💰 Solde réel final", f"0.00 €")

    # ===== ONGLET 2: OBJECTIFS =====
    with tab2:
        st.subheader("🎯 Mes objectifs financiers")

        # Charger les objectifs
        df_objectifs = pd.read_sql_query(
            "SELECT * FROM objectifs_financiers ORDER BY date_creation DESC",
            conn
        )

        # Sous-onglets
        obj_tab1, obj_tab2, obj_tab3 = st.tabs(["📋 Mes objectifs", "📊 Progression", "🚀 Stratégies"])

        # ===== SOUS-ONGLET 1: MES OBJECTIFS =====
        with obj_tab1:
            st.markdown("#### ➕ Définir un nouvel objectif")

            col1, col2 = st.columns(2)

            with col1:
                type_objectif = st.selectbox(
                    "Type d'objectif",
                    [
                        "💰 Solde minimum mensuel",
                        "📊 Respect des budgets",
                        "🏦 Épargne cible",
                        "✨ Personnalisé"
                    ],
                    key="type_obj"
                )

                titre_obj = st.text_input(
                    "Titre de l'objectif",
                    key="titre_obj",
                    placeholder="Ex: Économiser pour les vacances"
                )

            with col2:
                # Champs selon le type d'objectif
                if "Solde minimum" in type_objectif:
                    montant_obj = st.number_input(
                        "Solde minimum souhaité (€)",
                        min_value=0.0,
                        step=10.0,
                        value=100.0,
                        key="montant_obj",
                        help="Le solde que vous voulez avoir au minimum à la fin de chaque mois"
                    )
                    periodicite_obj = "mensuel"
                    date_limite_obj = None

                elif "Respect des budgets" in type_objectif:
                    st.info("📊 Objectif: Ne dépasser aucun budget mensuel défini")
                    montant_obj = None
                    periodicite_obj = "mensuel"
                    date_limite_obj = None

                elif "Épargne cible" in type_objectif:
                    montant_obj = st.number_input(
                        "Montant d'épargne cible (€)",
                        min_value=0.0,
                        step=100.0,
                        value=2000.0,
                        key="montant_epargne",
                        help="Le montant total que vous voulez épargner"
                    )
                    date_limite_obj = st.date_input(
                        "Date limite",
                        value=date.today() + timedelta(days=365),
                        key="date_limite_epargne"
                    )
                    periodicite_obj = "unique"

                else:  # Personnalisé
                    montant_obj = st.number_input(
                        "Montant (€) - optionnel",
                        min_value=0.0,
                        step=10.0,
                        value=0.0,
                        key="montant_perso"
                    )
                    periodicite_obj = st.selectbox(
                        "Périodicité",
                        ["mensuel", "trimestriel", "annuel", "unique"],
                        key="period_perso"
                    )
                    if periodicite_obj == "unique":
                        date_limite_obj = st.date_input(
                            "Date limite",
                            value=date.today() + timedelta(days=90),
                            key="date_limite_perso"
                        )
                    else:
                        date_limite_obj = None

            if st.button("💾 Créer l'objectif", type="primary", key="create_obj"):
                if titre_obj and titre_obj.strip():
                    # Déterminer le type simplifié
                    if "Solde minimum" in type_objectif:
                        type_simple = "solde_minimum"
                    elif "Respect" in type_objectif:
                        type_simple = "respect_budgets"
                    elif "Épargne" in type_objectif:
                        type_simple = "epargne_cible"
                    else:
                        type_simple = "personnalise"

                    cursor.execute("""
                        INSERT INTO objectifs_financiers
                        (type_objectif, titre, montant_cible, date_limite, periodicite, statut, date_creation, date_modification)
                        VALUES (?, ?, ?, ?, ?, 'en_cours', ?, ?)
                    """, (
                        type_simple,
                        titre_obj.strip(),
                        montant_obj if montant_obj else None,
                        date_limite_obj.isoformat() if date_limite_obj else None,
                        periodicite_obj,
                        datetime.now().isoformat(),
                        datetime.now().isoformat()
                    ))
                    conn.commit()
                    toast_success(f"Objectif '{titre_obj}' créé !")
                    refresh_and_rerun()
                else:
                    toast_warning("Veuillez saisir un titre")

            # Afficher les objectifs existants
            st.markdown("---")
            st.markdown("#### 📌 Objectifs actifs")

            if not df_objectifs.empty:
                for _, obj in df_objectifs.iterrows():
                    # Icône selon le type
                    type_icons = {
                        "solde_minimum": "💰",
                        "respect_budgets": "📊",
                        "epargne_cible": "🏦",
                        "personnalise": "✨"
                    }
                    icon = type_icons.get(obj["type_objectif"], "🎯")

                    # Statut
                    statut_colors = {
                        "en_cours": "🔵",
                        "atteint": "✅",
                        "echoue": "❌"
                    }
                    statut_icon = statut_colors.get(obj["statut"], "⚪")

                    with st.expander(f"{icon} {obj['titre']} {statut_icon}", expanded=False):
                        col1, col2 = st.columns([3, 1])

                        with col1:
                            st.write(f"**Type:** {obj['type_objectif'].replace('_', ' ').title()}")
                            if obj['montant_cible']:
                                st.write(f"**Montant cible:** {obj['montant_cible']:.2f} €")
                            if obj['date_limite']:
                                st.write(f"**Date limite:** {pd.to_datetime(obj['date_limite']).strftime('%d/%m/%Y')}")
                            st.write(f"**Périodicité:** {obj['periodicite']}")
                            st.caption(f"Créé le : {obj['date_creation'][:10]}")

                        with col2:
                            if st.button("✅ Marquer atteint", key=f"atteint_{obj['id']}"):
                                cursor.execute(
                                    "UPDATE objectifs_financiers SET statut = 'atteint', date_atteint = ? WHERE id = ?",
                                    (datetime.now().isoformat(), obj['id'])
                                )
                                conn.commit()
                                toast_success("Objectif marqué comme atteint ! 🎉")
                                refresh_and_rerun()

                            if st.button("🗑️ Supprimer", key=f"delete_obj_{obj['id']}"):
                                cursor.execute("DELETE FROM objectifs_financiers WHERE id = ?", (obj['id'],))
                                conn.commit()
                                toast_success("Objectif supprimé")
                                refresh_and_rerun()
            else:
                st.info("💡 Aucun objectif défini. Créez-en un ci-dessus !")

        # ===== SOUS-ONGLET 2: PROGRESSION =====
        with obj_tab2:
            st.markdown("#### 📊 Suivi de progression")

            if df_objectifs.empty:
                st.info("💡 Définissez d'abord des objectifs pour voir leur progression")
            else:
                # Calculer le solde actuel
                df_trans = load_transactions()
                if not df_trans.empty:
                    revenus_total = df_trans[df_trans["type"] == "revenu"]["montant"].sum()
                    depenses_total = df_trans[df_trans["type"] == "dépense"]["montant"].sum()
                    solde_actuel = revenus_total - depenses_total
                else:
                    solde_actuel = 0.0

                # Calculer le solde à la fin du mois dernier
                today = datetime.now()
                premier_jour_mois = today.replace(day=1).date()

                if not df_trans.empty:
                    df_mois_precedent = df_trans[
                        pd.to_datetime(df_trans["date"]).dt.date < premier_jour_mois
                    ]
                    if not df_mois_precedent.empty:
                        rev_prec = df_mois_precedent[df_mois_precedent["type"] == "revenu"]["montant"].sum()
                        dep_prec = df_mois_precedent[df_mois_precedent["type"] == "dépense"]["montant"].sum()
                        solde_mois_precedent = rev_prec - dep_prec
                    else:
                        solde_mois_precedent = 0.0
                else:
                    solde_mois_precedent = 0.0

                for _, obj in df_objectifs[df_objectifs["statut"] == "en_cours"].iterrows():
                    st.markdown(f"### 🎯 {obj['titre']}")

                    if obj["type_objectif"] == "solde_minimum":
                        # Objectif: Solde minimum mensuel
                        cible = obj["montant_cible"]
                        progression = (solde_mois_precedent / cible * 100) if cible > 0 else 0

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Solde fin mois dernier", f"{solde_mois_precedent:.2f} €")
                        with col2:
                            st.metric("Objectif", f"{cible:.2f} €")
                        with col3:
                            delta = solde_mois_precedent - cible
                            st.metric("Écart", f"{delta:+.2f} €")

                        # Barre de progression
                        if progression >= 100:
                            st.success(f"✅ Objectif atteint ! ({progression:.0f}%)")
                        elif progression >= 80:
                            st.warning(f"🟡 Presque ! ({progression:.0f}%)")
                        else:
                            st.error(f"❌ Non atteint ({progression:.0f}%)")

                        st.progress(min(progression / 100, 1.0))

                    elif obj["type_objectif"] == "respect_budgets":
                        # Objectif: Respect des budgets
                        if not df_budgets.empty:
                            nb_budgets = len(df_budgets)
                            nb_respectes = 0

                            for _, budget in df_budgets.iterrows():
                                if not df_trans.empty:
                                    depenses_cat = df_trans[
                                        (df_trans["type"] == "dépense") &
                                        (df_trans["categorie"] == budget["categorie"]) &
                                        (pd.to_datetime(df_trans["date"]).dt.date >= premier_jour_mois)
                                    ]["montant"].sum()
                                else:
                                    depenses_cat = 0.0

                                if depenses_cat <= budget["budget_mensuel"]:
                                    nb_respectes += 1

                            progression = (nb_respectes / nb_budgets * 100) if nb_budgets > 0 else 0

                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Budgets respectés", f"{nb_respectes}/{nb_budgets}")
                            with col2:
                                st.metric("Progression", f"{progression:.0f}%")
                            with col3:
                                if progression == 100:
                                    st.success("✅ Parfait !")
                                else:
                                    st.warning(f"⚠️ {nb_budgets - nb_respectes} dépassé(s)")

                            st.progress(progression / 100)
                        else:
                            st.info("💡 Définissez d'abord des budgets")

                    elif obj["type_objectif"] == "epargne_cible":
                        # Objectif: Épargne cible
                        cible = obj["montant_cible"]
                        date_limite = pd.to_datetime(obj["date_limite"]).date() if obj["date_limite"] else None

                        # L'épargne = solde actuel
                        epargne_actuelle = max(solde_actuel, 0)
                        progression = (epargne_actuelle / cible * 100) if cible > 0 else 0

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Épargne actuelle", f"{epargne_actuelle:.2f} €")
                        with col2:
                            st.metric("Objectif", f"{cible:.2f} €")
                        with col3:
                            reste = cible - epargne_actuelle
                            st.metric("Reste à épargner", f"{reste:.2f} €")

                        # Barre de progression
                        if progression >= 100:
                            st.success(f"✅ Objectif atteint ! ({progression:.0f}%)")
                        else:
                            st.info(f"📊 Progression: {progression:.0f}%")

                        st.progress(min(progression / 100, 1.0))

                        # Jours restants
                        if date_limite:
                            jours_restants = (date_limite - today.date()).days
                            if jours_restants > 0:
                                st.caption(f"⏰ {jours_restants} jours restants jusqu'au {date_limite.strftime('%d/%m/%Y')}")
                                # Calcul de l'épargne mensuelle nécessaire
                                if reste > 0:
                                    mois_restants = max(jours_restants / 30, 1)
                                    epargne_mensuelle = reste / mois_restants
                                    st.info(f"💡 Il vous faut épargner environ **{epargne_mensuelle:.2f} €/mois** pour atteindre votre objectif")
                            else:
                                st.error("⏰ Date limite dépassée !")

                    st.markdown("---")

        # ===== SOUS-ONGLET 3: STRATÉGIES =====
        with obj_tab3:
            st.markdown("#### 🚀 Stratégies pour atteindre vos objectifs")

            if df_objectifs.empty:
                st.info("💡 Définissez d'abord des objectifs pour voir les stratégies")
            else:
                # Analyser les objectifs non atteints
                objectifs_en_cours = df_objectifs[df_objectifs["statut"] == "en_cours"]

                if objectifs_en_cours.empty:
                    st.success("🎉 Tous vos objectifs sont atteints ! Félicitations !")
                else:
                    st.info("💡 Voici des recommandations pour atteindre vos objectifs :")

                    for _, obj in objectifs_en_cours.iterrows():
                        st.markdown(f"### 🎯 {obj['titre']}")

                        if obj["type_objectif"] == "solde_minimum":
                            cible = obj["montant_cible"]
                            ecart = cible - solde_mois_precedent

                            if ecart > 0:
                                st.warning(f"⚠️ Il vous manque **{ecart:.2f} €** pour atteindre votre objectif")

                                st.markdown("**💡 Recommandations:**")
                                st.markdown(f"- Réduire vos dépenses de **{ecart:.2f} €** ce mois-ci")
                                st.markdown(f"- Ou augmenter vos revenus de **{ecart:.2f} €**")
                                st.markdown(f"- Ou combiner les deux (réduire de {ecart/2:.2f} € et augmenter de {ecart/2:.2f} €)")

                                # Analyser les catégories où économiser
                                if not df_budgets.empty and not df_trans.empty:
                                    st.markdown("**📊 Où économiser?**")

                                    economies_possibles = []
                                    for _, budget in df_budgets.iterrows():
                                        depenses_cat = df_trans[
                                            (df_trans["type"] == "dépense") &
                                            (df_trans["categorie"] == budget["categorie"]) &
                                            (pd.to_datetime(df_trans["date"]).dt.date >= premier_jour_mois)
                                        ]["montant"].sum()

                                        marge = budget["budget_mensuel"] - depenses_cat
                                        if marge > 0:
                                            economies_possibles.append({
                                                "Catégorie": budget["categorie"],
                                                "Marge disponible": f"{marge:.2f} €"
                                            })

                                    if economies_possibles:
                                        st.dataframe(pd.DataFrame(economies_possibles), hide_index=True, use_container_width=True)
                                    else:
                                        st.caption("💡 Tous vos budgets sont utilisés. Envisagez d'augmenter vos revenus.")

                        elif obj["type_objectif"] == "respect_budgets":
                            st.markdown("**💡 Recommandations:**")
                            st.markdown("- Suivez vos dépenses régulièrement dans l'onglet Budgets")
                            st.markdown("- Recevez des alertes quand vous approchez de votre limite")
                            st.markdown("- Ajustez vos habitudes de consommation dans les catégories dépassées")

                        elif obj["type_objectif"] == "epargne_cible":
                            cible = obj["montant_cible"]
                            reste = cible - max(solde_actuel, 0)

                            if reste > 0:
                                date_limite = pd.to_datetime(obj["date_limite"]).date() if obj["date_limite"] else None

                                if date_limite:
                                    jours_restants = (date_limite - today.date()).days
                                    mois_restants = max(jours_restants / 30, 1)
                                    epargne_mensuelle = reste / mois_restants

                                    st.markdown("**💡 Plan d'épargne:**")
                                    st.markdown(f"- Épargner **{epargne_mensuelle:.2f} €/mois** pendant {int(mois_restants)} mois")
                                    st.markdown(f"- Ou économiser **{reste/jours_restants:.2f} €/jour** pendant {jours_restants} jours")

                                    # Simulation
                                    st.markdown("**📊 Simulation:**")
                                    fig_epargne = go.Figure()

                                    dates_sim = pd.date_range(start=today.date(), end=date_limite, freq='MS')
                                    epargnes = [max(solde_actuel, 0)]

                                    for i in range(len(dates_sim)):
                                        epargnes.append(epargnes[-1] + epargne_mensuelle)

                                    fig_epargne.add_trace(go.Scatter(
                                        x=[today.date()] + dates_sim.tolist(),
                                        y=epargnes,
                                        mode='lines+markers',
                                        name='Épargne projetée',
                                        line=dict(color='green', width=3)
                                    ))

                                    fig_epargne.add_hline(y=cible, line_dash="dash", line_color="blue", annotation_text=f"Objectif: {cible:.0f}€")

                                    fig_epargne.update_layout(
                                        title="Projection d'épargne",
                                        xaxis_title="Date",
                                        yaxis_title="Épargne (€)",
                                        height=400
                                    )

                                    st.plotly_chart(fig_epargne, use_container_width=True)

                        st.markdown("---")

    # ===== ONGLET 3: VUE D'ENSEMBLE =====
    with tab3:
        st.subheader("📊 Vue d'ensemble du mois")

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

    # ===== ONGLET 4: PRÉVISIONS =====
    with tab4:
        st.subheader("📅 Prévisions et Solde prévisionnel")

        # Charger les échéances
        df_echeances = pd.read_sql_query(
            "SELECT * FROM echeances WHERE statut = 'active' ORDER BY date_echeance ASC",
            conn
        )

        # Charger les transactions (pour le solde actuel et les récurrentes)
        df_transactions = load_transactions()

        # Sous-onglets pour organiser l'interface
        sub_tab1, sub_tab2 = st.tabs(["📈 Solde prévisionnel", "➕ Gérer les prévisions"])

        # ===== SUB-TAB 1: SOLDE PRÉVISIONNEL =====
        with sub_tab1:
            st.markdown("#### 📊 Analyse et projection du solde")

            # Calculer le solde actuel
            if not df_transactions.empty:
                revenus = df_transactions[df_transactions["type"] == "revenu"]["montant"].sum()
                depenses = df_transactions[df_transactions["type"] == "dépense"]["montant"].sum()
                solde_actuel = revenus - depenses
            else:
                solde_actuel = 0.0

            # Période de projection et options
            col1, col2, col3 = st.columns([2, 2, 2])

            with col1:
                date_projection = st.date_input(
                    "📅 Projeter jusqu'au",
                    value=date.today() + timedelta(days=90),
                    key="date_proj_main"
                )

            with col2:
                st.metric("💰 Solde actuel", f"{solde_actuel:,.2f} €")

            with col3:
                inclure_previsoires = st.checkbox(
                    "🔮 Inclure échéances prévisoires",
                    value=False,
                    key="inclure_previsoires",
                    help="Activer pour voir l'impact des échéances prévisoires (hypothétiques) sur votre solde"
                )

            # Collecter toutes les prévisions futures
            previsions_futures = []
            proj_ts = pd.Timestamp(date_projection)
            today_ts = pd.Timestamp(datetime.now().date())

            # 1. TRANSACTIONS RÉCURRENTES (de la table transactions)
            if not df_transactions.empty:
                rec_df = df_transactions[
                    (df_transactions["recurrence"].notna()) &
                    (df_transactions["source"].isin(["récurrence_auto", "récurrente_auto", "manuel", "récurrente"]))
                ]

                for _, row in rec_df.iterrows():
                    start_date = pd.Timestamp(row["date"])
                    recurrence = row["recurrence"]
                    current_date = start_date

                    while current_date <= proj_ts:
                        if current_date >= today_ts:
                            previsions_futures.append({
                                "date": current_date,
                                "type": row["type"],
                                "categorie": row["categorie"],
                                "sous_categorie": row.get("sous_categorie", ""),
                                "montant": safe_convert(row["montant"]),
                                "description": row.get("description", ""),
                                "source": "🔁 Récurrente"
                            })

                        if recurrence == "hebdomadaire":
                            current_date += pd.Timedelta(weeks=1)
                        elif recurrence == "mensuelle":
                            current_date += pd.DateOffset(months=1)
                        elif recurrence == "annuelle":
                            current_date += pd.DateOffset(years=1)
                        else:
                            break

            # 2. ÉCHÉANCES (de la table echeances)
            if not df_echeances.empty:
                for _, ech in df_echeances.iterrows():
                    # Filtrer selon le type d'échéance
                    type_ech = ech.get("type_echeance", "prévue")

                    # Si prévisoire et qu'on ne veut pas les inclure, on skip
                    if type_ech == "prévisoire" and not inclure_previsoires:
                        continue

                    date_ech = pd.Timestamp(ech["date_echeance"])
                    recurrence = ech.get("recurrence")

                    # Déterminer l'icône selon le type
                    if type_ech == "prévisoire":
                        source_icon = "🔮 Échéance prévisoire"
                    else:
                        source_icon = "✅ Échéance prévue"

                    # Ajouter l'échéance si elle est dans la période future
                    if date_ech >= today_ts and date_ech <= proj_ts:
                        previsions_futures.append({
                            "date": date_ech,
                            "type": ech["type"],
                            "categorie": ech["categorie"],
                            "sous_categorie": ech.get("sous_categorie", ""),
                            "montant": ech["montant"],
                            "description": ech.get("description", ""),
                            "source": source_icon
                        })

                    # Si récurrente, générer les occurrences futures
                    if recurrence:
                        current_date = date_ech

                        while current_date <= proj_ts:
                            if recurrence == "hebdomadaire":
                                current_date += pd.Timedelta(weeks=1)
                            elif recurrence == "mensuelle":
                                current_date += pd.DateOffset(months=1)
                            elif recurrence == "annuelle":
                                current_date += pd.DateOffset(years=1)
                            else:
                                break

                            if current_date >= today_ts and current_date <= proj_ts:
                                # Utiliser l'icône appropriée selon le type
                                source_rec = f"{source_icon} (récurrent)"
                                previsions_futures.append({
                                    "date": current_date,
                                    "type": ech["type"],
                                    "categorie": ech["categorie"],
                                    "sous_categorie": ech.get("sous_categorie", ""),
                                    "montant": ech["montant"],
                                    "description": f"{ech.get('description', '')} (récurrent)",
                                    "source": source_rec
                                })

            if previsions_futures:
                # Trier par date et supprimer les doublons
                df_prev = pd.DataFrame(previsions_futures).sort_values("date").reset_index(drop=True)

                df_prev = df_prev.drop_duplicates(
                    subset=["date", "type", "categorie", "sous_categorie", "montant"]
                )

                # Calculer le solde prévisionnel cumulé
                solde_cum = [solde_actuel]
                for _, row in df_prev.iterrows():
                    dernier_solde = solde_cum[-1]
                    if row["type"] == "revenu":
                        solde_cum.append(dernier_solde + row["montant"])
                    else:
                        solde_cum.append(dernier_solde - row["montant"])

                df_prev["solde_previsionnel"] = solde_cum[1:]

                # Afficher le tableau
                st.markdown("##### 📋 Prévisions futures (Récurrentes + Échéances)")
                df_prev_display = df_prev.copy()
                df_prev_display["date"] = df_prev_display["date"].dt.strftime("%d/%m/%Y")
                df_prev_display["Type"] = df_prev_display["type"].apply(lambda x: "💹 Revenu" if x == "revenu" else "💸 Dépense")

                st.dataframe(
                    df_prev_display[["date", "Type", "categorie", "montant", "solde_previsionnel", "source", "description"]].rename(columns={
                        "date": "Date",
                        "categorie": "Catégorie",
                        "montant": "Montant (€)",
                        "solde_previsionnel": "Solde prév. (€)",
                        "source": "Origine",
                        "description": "Description"
                    }),
                    use_container_width=True,
                    hide_index=True
                )

                # Métriques
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        f"💹 Solde au {date_projection.strftime('%d/%m/%Y')}",
                        f"{solde_cum[-1]:,.2f} €"
                    )

                with col2:
                    variation = solde_cum[-1] - solde_actuel
                    st.metric(
                        "📊 Variation prévue",
                        f"{variation:+,.2f} €",
                        delta=f"{variation:+,.2f} €"
                    )

                with col3:
                    nb_previsions = len(df_prev)
                    st.metric(
                        "📅 Nombre de prévisions",
                        nb_previsions
                    )

                # Graphique d'évolution
                st.markdown("---")
                st.markdown("##### 📊 Graphique d'évolution du solde")

                # Créer le graphique avec Plotly
                fig = go.Figure()

                # Ligne du solde prévisionnel
                fig.add_trace(go.Scatter(
                    x=df_prev["date"],
                    y=df_prev["solde_previsionnel"],
                    mode='lines+markers',
                    name='Solde prévisionnel',
                    line=dict(color='royalblue', width=3),
                    marker=dict(size=8),
                    hovertemplate='<b>%{x|%d/%m/%Y}</b><br>Solde: %{y:.2f} €<extra></extra>'
                ))

                # Ligne horizontale à 0
                fig.add_hline(y=0, line_dash="dash", line_color="red", annotation_text="⚠️ Seuil 0€")

                # Ligne horizontale du solde actuel
                fig.add_hline(
                    y=solde_actuel,
                    line_dash="dot",
                    line_color="green",
                    annotation_text=f"💰 Solde actuel: {solde_actuel:.0f}€"
                )

                fig.update_layout(
                    title="Évolution du solde prévisionnel (Récurrentes + Échéances)",
                    xaxis_title="Date",
                    yaxis_title="Solde (€)",
                    height=450,
                    hovermode='x unified',
                    showlegend=True
                )

                st.plotly_chart(fig, use_container_width=True)

                # Alertes intelligentes
                st.markdown("---")
                st.markdown("##### 🚨 Alertes et recommandations")

                col1, col2 = st.columns(2)

                with col1:
                    # Calculer le solde minimum
                    min_solde = min(solde_cum[1:])
                    solde_negatif = [s for s in solde_cum[1:] if s < 0]

                    if solde_negatif:
                        st.warning(f"⚠️ **Attention** : Votre solde passera en négatif {len(solde_negatif)} fois pendant cette période !")
                        st.error(f"🔻 **Solde minimum prévu** : **{min_solde:,.2f} €**")
                        st.caption("💡 Le solde minimum est le point le plus bas que votre solde atteindra")
                    else:
                        st.success("✅ Votre solde restera positif sur toute la période")
                        st.info(f"🔻 **Solde minimum prévu** : **{min_solde:,.2f} €**")
                        st.caption("💡 C'est le montant minimum que vous aurez sur votre compte. Gardez au moins ce montant disponible.")

                with col2:
                    # Recommandations
                    if variation < 0:
                        st.info(f"💡 **Recommandation** : Prévoyez d'économiser environ **{abs(variation):,.2f} €** pour compenser")
                    elif variation > 0:
                        st.success(f"🎉 **Bonne nouvelle** : Vous devriez économiser environ **{variation:,.2f} €** !")

                    # Explication supplémentaire
                    st.caption("📊 **Astuce** : Activez/désactivez les échéances prévisoires pour comparer différents scénarios")

            else:
                st.info("💡 Aucune prévision future trouvée. Ajoutez des échéances ou des transactions récurrentes pour voir les projections.")

        # ===== SUB-TAB 2: GÉRER LES PRÉVISIONS =====
        with sub_tab2:
            st.markdown("#### ➕ Ajouter une prévision / échéance")

            st.info("💡 **Astuce** : Ajoutez vos revenus et dépenses futures ici. Vous pouvez créer des prévisions ponctuelles ou récurrentes.")

            # Formulaire unifié
            col1, col2 = st.columns(2)

            with col1:
                type_prev = st.selectbox(
                    "Type",
                    ["dépense", "revenu"],
                    key="type_prev_unified"
                )

                # Catégories existantes
                if not df_transactions.empty:
                    categories = sorted(
                        df_transactions[df_transactions["type"] == type_prev]["categorie"]
                        .dropna()
                        .unique()
                        .tolist()
                    )
                else:
                    categories = []

                mode_cat = st.radio(
                    "Catégorie",
                    ["Existante", "Nouvelle"],
                    horizontal=True,
                    key="mode_cat_prev"
                )

                if mode_cat == "Existante" and categories:
                    categorie_prev = st.selectbox("Sélectionner", categories, key="cat_prev_exist")
                else:
                    categorie_prev = st.text_input("Nom de la catégorie", key="cat_prev_new")

                sous_categorie_prev = st.text_input("Sous-catégorie", key="souscat_prev")

            with col2:
                type_echeance_prev = st.radio(
                    "Nature de l'échéance",
                    ["✅ Prévue (certaine)", "🔮 Prévisoire (hypothétique)"],
                    horizontal=True,
                    key="type_ech_prev",
                    help="Prévue = échéance certaine (ex: loyer). Prévisoire = simulation pour tester l'impact (ex: achat potentiel)"
                )

                montant_prev = st.number_input(
                    "Montant (€)",
                    min_value=0.0,
                    step=10.0,
                    value=100.0,
                    key="montant_prev"
                )

                date_prev = st.date_input(
                    "Date de la prévision",
                    value=date.today() + timedelta(days=30),
                    key="date_prev"
                )

                recurrence_prev = st.selectbox(
                    "Récurrence",
                    ["Aucune", "Hebdomadaire", "Mensuelle", "Annuelle"],
                    key="rec_prev"
                )

            description_prev = st.text_area(
                "Description (optionnel)",
                height=100,
                key="desc_prev",
                placeholder="Ex: Facture EDF, Salaire, Prime, etc."
            )

            st.markdown("---")

            col_btn1, col_btn2 = st.columns(2)

            with col_btn1:
                if st.button("💾 Enregistrer comme échéance", type="primary", key="save_echeance_unified"):
                    if categorie_prev and categorie_prev.strip():
                        rec_value = None if recurrence_prev == "Aucune" else recurrence_prev.lower()
                        # Déterminer le type d'échéance
                        type_ech_value = "prévisoire" if "Prévisoire" in type_echeance_prev else "prévue"

                        cursor.execute("""
                            INSERT INTO echeances
                            (type, categorie, sous_categorie, montant, date_echeance, recurrence, statut, type_echeance, description, date_creation, date_modification)
                            VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?, ?, ?)
                        """, (
                            type_prev,
                            categorie_prev.strip(),
                            sous_categorie_prev.strip() if sous_categorie_prev else "",
                            montant_prev,
                            date_prev.isoformat(),
                            rec_value,
                            type_ech_value,
                            description_prev.strip() if description_prev else "",
                            datetime.now().isoformat(),
                            datetime.now().isoformat()
                        ))
                        conn.commit()

                        label_type = "prévisoire" if type_ech_value == "prévisoire" else "prévue"
                        toast_success(f"Échéance {label_type} {type_prev} ajoutée pour le {date_prev.strftime('%d/%m/%Y')}")
                        refresh_and_rerun()
                    else:
                        toast_warning("Veuillez saisir une catégorie")

            with col_btn2:
                if st.button("🔁 Enregistrer comme transaction récurrente", type="secondary", key="save_recurrence_unified"):
                    if categorie_prev and categorie_prev.strip() and recurrence_prev != "Aucune":
                        rec_value = recurrence_prev.lower()

                        # Ajouter dans la table transactions
                        cursor.execute("""
                            INSERT INTO transactions
                            (type, categorie, sous_categorie, montant, date, recurrence, source, description)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            type_prev,
                            categorie_prev.strip(),
                            sous_categorie_prev.strip() if sous_categorie_prev else "",
                            montant_prev,
                            date_prev.isoformat(),
                            rec_value,
                            "récurrente_auto",
                            description_prev.strip() if description_prev else ""
                        ))

                        # Ajouter aussi dans la table echeances pour la cohérence
                        type_ech_value = "prévisoire" if "Prévisoire" in type_echeance_prev else "prévue"

                        cursor.execute("""
                            INSERT INTO echeances
                            (type, categorie, sous_categorie, montant, date_echeance, recurrence, statut, type_echeance, description, date_creation, date_modification)
                            VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?, ?, ?)
                        """, (
                            type_prev,
                            categorie_prev.strip(),
                            sous_categorie_prev.strip() if sous_categorie_prev else "",
                            montant_prev,
                            date_prev.isoformat(),
                            rec_value,
                            type_ech_value,
                            description_prev.strip() if description_prev else "",
                            datetime.now().isoformat(),
                            datetime.now().isoformat()
                        ))

                        conn.commit()
                        toast_success(f"Transaction récurrente créée ({rec_value}) et ajoutée aux échéances")
                        refresh_and_rerun()
                    elif recurrence_prev == "Aucune":
                        toast_warning("Veuillez sélectionner une récurrence pour créer une transaction récurrente")
                    else:
                        toast_warning("Veuillez saisir une catégorie")

            # Liste des prévisions existantes
            st.markdown("---")
            st.markdown("#### 📋 Prévisions existantes")

            if not df_echeances.empty:
                st.markdown("##### Échéances actives")

                echeances_display = []
                for _, ech in df_echeances.iterrows():
                    icon = "💹" if ech["type"] == "revenu" else "💸"
                    rec_text = ""
                    if ech["recurrence"]:
                        rec_icon = {"hebdomadaire": "🔁 Hebdo", "mensuelle": "🔁 Mensuel", "annuelle": "🔁 Annuel"}.get(ech["recurrence"], "🔁")
                        rec_text = f" {rec_icon}"

                    # Afficher le type d'échéance
                    type_ech = ech.get("type_echeance", "prévue")
                    type_ech_icon = "✅" if type_ech == "prévue" else "🔮"

                    echeances_display.append({
                        "ID": ech["id"],
                        "Nature": f"{type_ech_icon} {type_ech.capitalize()}",
                        "Type": f"{icon} {ech['type'].capitalize()}",
                        "Date": pd.to_datetime(ech["date_echeance"]).strftime("%d/%m/%Y"),
                        "Catégorie": ech["categorie"],
                        "Montant (€)": f"{ech['montant']:.2f}",
                        "Récurrence": rec_text if rec_text else "—",
                        "Description": ech.get("description", "")[:40]
                    })

                df_ech_display = pd.DataFrame(echeances_display)
                st.dataframe(
                    df_ech_display.drop(columns=["ID"]),
                    use_container_width=True,
                    hide_index=True
                )

                # Options de gestion
                col1, col2, col3 = st.columns([3, 1, 1])

                with col1:
                    echeance_to_manage = st.selectbox(
                        "Sélectionner une échéance à gérer",
                        df_echeances["id"].tolist(),
                        format_func=lambda x: f"#{x} - {df_echeances[df_echeances['id']==x].iloc[0]['categorie']} - {df_echeances[df_echeances['id']==x].iloc[0]['montant']:.2f}€",
                        key="echeance_manage_unified"
                    )

                with col2:
                    if st.button("✅ Marquer payée", key="mark_paid_unified"):
                        cursor.execute(
                            "UPDATE echeances SET statut = 'payée', date_modification = ? WHERE id = ?",
                            (datetime.now().isoformat(), echeance_to_manage)
                        )
                        conn.commit()
                        toast_success("Échéance marquée comme payée")
                        refresh_and_rerun()

                with col3:
                    if st.button("🗑️ Supprimer", key="delete_echeance_unified"):
                        cursor.execute(
                            "DELETE FROM echeances WHERE id = ?",
                            (echeance_to_manage,)
                        )
                        conn.commit()
                        toast_success("Échéance supprimée")
                        refresh_and_rerun()
            else:
                st.info("💡 Aucune échéance enregistrée")

    conn.close()


