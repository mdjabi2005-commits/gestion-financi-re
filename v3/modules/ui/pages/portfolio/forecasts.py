"""
Forecasts & Predictions Tab

This module implements Tab 4 of the portfolio interface:
- Forecast balance projection (solde prévisionnel)
- Manage upcoming expenses and revenues (échéances)
- Recurring transaction management
- Cash flow forecasting with alerts
"""

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date, timedelta
import plotly.graph_objects as go
from modules.ui.helpers import load_transactions, refresh_and_rerun
from modules.ui.components import toast_success, toast_warning
from config import DB_PATH


def safe_convert(value):
    """Safely convert a value to float."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def render_forecasts_tab(conn: sqlite3.Connection, cursor: sqlite3.Cursor) -> None:
    """
    Render the forecasts and predictions tab.

    Features:
    - Projections of balance based on recurring transactions and upcoming expenses
    - Management of scheduled expenses/revenues (échéances)
    - Alerts on potential negative balance
    - Scenario testing with provisional forecasts

    Args:
        conn: Database connection
        cursor: Database cursor
    """
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

            # Afficher le tableau dans un expander
            with st.expander("📋 Voir le détail des prévisions futures (Récurrentes + Échéances)", expanded=False):
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
