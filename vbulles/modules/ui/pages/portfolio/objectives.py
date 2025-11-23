"""
Financial Objectives Tab

This module implements Tab 2 of the portfolio interface:
- Financial goal creation and management
- Goal progress tracking
- Goal achievement strategies and recommendations
- Multiple goal types: solde minimum, budget respect, savings target, custom
"""

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date, timedelta
import plotly.graph_objects as go
from modules.ui.helpers import load_transactions, refresh_and_rerun
from modules.ui.components import toast_success, toast_warning
from config import DB_PATH


def render_objectives_tab(conn: sqlite3.Connection, cursor: sqlite3.Cursor) -> None:
    """
    Render the financial objectives tab.

    Features:
    - Create new financial objectives
    - Track objective progress
    - View achievement strategies
    - Mark objectives as completed

    Args:
        conn: Database connection
        cursor: Database cursor
    """
    st.subheader("🎯 Mes objectifs financiers")

    # Charger les objectifs
    df_objectifs = pd.read_sql_query(
        "SELECT * FROM objectifs_financiers ORDER BY date_creation DESC",
        conn
    )

    # Charger les budgets pour les métriques
    df_budgets = pd.read_sql_query(
        "SELECT * FROM budgets_categories",
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

                                for i in range(len(dates_sim) - 1):
                                    epargnes.append(epargnes[-1] + epargne_mensuelle)

                                fig_epargne.add_trace(go.Scatter(
                                    x=dates_sim,
                                    y=epargnes[:len(dates_sim)],
                                    mode='lines+markers',
                                    name='Projection',
                                    line=dict(color='green', width=3)
                                ))

                                fig_epargne.add_hline(y=cible, line_dash="dash", line_color="red",
                                                     annotation_text="Objectif", annotation_position="right")

                                fig_epargne.update_layout(
                                    title="Projection d'épargne",
                                    xaxis_title="Date",
                                    yaxis_title="Épargne (€)",
                                    hovermode='x unified',
                                    height=400
                                )

                                st.plotly_chart(fig_epargne, use_container_width=True)

                    st.markdown("---")
