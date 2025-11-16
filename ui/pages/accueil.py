# -*- coding: utf-8 -*-
"""
Module accueil - Partie de l'application gestiov4
Généré automatiquement par migrate_to_modular.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from core.transactions import load_transactions
from ui.components import toast_success, toast_warning


def interface_accueil():
    """Page d'accueil simplifiée avec système de bulles (expanders)"""
    st.title("🏠 Tableau de Bord Financier")

    # Charger les données avec gestion d'erreurs
    try:
        df = load_transactions()
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        toast_error("Erreur lors du chargement des données")
        return

    if df.empty:
        st.info("💰 Aucune transaction enregistrée. Commencez par ajouter vos premières transactions !")
        return

    # === PÉRIODE (COMPACTE) ===
    premiere_date = df["date"].min().date()
    derniere_date = df["date"].max().date()

    col1, col2, col3 = st.columns([3, 2, 1])

    with col1:
        periode_options = {
            "Depuis le début": "debut",
            "3 derniers mois": 3,
            "6 derniers mois": 6,
            "12 derniers mois": 12,
            "Personnalisée": "custom"
        }
        periode_choice = st.selectbox("📅 Période d'analyse", list(periode_options.keys()), key="periode_accueil")

    with col2:
        if periode_choice == "Personnalisée":
            date_debut = st.date_input("Début", value=premiere_date, key="debut_accueil")
            date_fin = st.date_input("Fin", value=derniere_date, key="fin_accueil")
        elif periode_choice == "Depuis le début":
            date_debut = premiere_date
            date_fin = derniere_date
        else:
            mois_retour = periode_options[periode_choice]
            date_debut = max(premiere_date, date.today() - relativedelta(months=mois_retour))
            date_fin = derniere_date

        st.caption(f"📆 {date_debut.strftime('%d/%m/%y')} → {date_fin.strftime('%d/%m/%y')}")

    with col3:
        if st.button("🔄", key="refresh_accueil", help="Actualiser les données"):
            refresh_and_rerun()

    # Filtrer les données
    df_periode = df[(df["date"] >= pd.Timestamp(date_debut)) & (df["date"] <= pd.Timestamp(date_fin))]

    if df_periode.empty:
        toast_warning("Aucune transaction dans la période sélectionnée.")
        return

    # === MÉTRIQUES PRINCIPALES (SIMPLIFIÉES) ===
    st.markdown("---")

    total_revenus = df_periode[df_periode["type"] == "revenu"]["montant"].sum()
    total_depenses = df_periode[df_periode["type"] == "dépense"]["montant"].sum()
    solde_periode = total_revenus - total_depenses
    nb_transactions = len(df_periode)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "💰 Solde",
            f"{solde_periode:+.0f} €",
            delta="Positif" if solde_periode >= 0 else "Négatif",
            delta_color="normal" if solde_periode >= 0 else "inverse",
            help="Revenus - Dépenses sur la période sélectionnée"
        )

    with col2:
        st.metric(
            "💸 Dépenses",
            f"{total_depenses:.0f} €",
            delta=f"{len(df_periode[df_periode['type'] == 'dépense'])} transactions",
            help="Total des dépenses sur la période"
        )

    with col3:
        st.metric(
            "💹 Revenus",
            f"{total_revenus:.0f} €",
            delta=f"{len(df_periode[df_periode['type'] == 'revenu'])} transactions",
            help="Total des revenus sur la période"
        )

    with col4:
        mois_couverts = max(1, ((date_fin - date_debut).days // 30))
        tx_par_mois = nb_transactions / mois_couverts
        st.metric(
            "📊 Activité",
            f"{tx_par_mois:.1f}/mois",
            delta=f"{nb_transactions} total",
            help="Nombre moyen de transactions par mois"
        )

    # === MÉTRIQUES DÉTAILLÉES (EN ACCORDÉON) ===
    with st.expander("📈 Voir métriques détaillées"):
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if total_revenus > 0:
                taux_epargne = (solde_periode / total_revenus) * 100
                if taux_epargne >= 20:
                    emoji, message = "🎉", "Excellent"
                elif taux_epargne >= 10:
                    emoji, message = "👍", "Très bien"
                elif taux_epargne >= 0:
                    emoji, message = "✅", "Correct"
                else:
                    emoji, message = "🚨", "Découvert"

                st.metric(f"{emoji} Taux d'épargne", f"{taux_epargne:.1f}%", delta=message)
            else:
                st.metric("Taux d'épargne", "N/A")

        with col2:
            if total_revenus > 0:
                ratio_depenses = (total_depenses / total_revenus) * 100
                st.metric("📊 Ratio dépenses/revenus", f"{ratio_depenses:.0f}%")
            else:
                st.metric("Ratio dépenses/revenus", "N/A")

        with col3:
            df_depenses = df_periode[df_periode["type"] == "dépense"]
            if not df_depenses.empty:
                depense_max = df_depenses["montant"].max()
                st.metric("🔥 Plus grosse dépense", f"{depense_max:.0f} €")
            else:
                st.metric("Plus grosse dépense", "0 €")

        with col4:
            if not df_depenses.empty:
                depense_moyenne = df_depenses["montant"].median()
                st.metric("📊 Dépense médiane", f"{depense_moyenne:.0f} €")
            else:
                st.metric("Dépense médiane", "0 €")

        # Explication des métriques
        st.info("""
        **💡 Explication des métriques :**
        - **Taux d'épargne** : Pourcentage de vos revenus que vous épargnez (Solde / Revenus × 100)
        - **Ratio dépenses/revenus** : Part de vos revenus dépensée (Dépenses / Revenus × 100)
        - **Plus grosse dépense** : La transaction la plus importante de la période
        - **Dépense médiane** : Montant médian de vos dépenses (50% en-dessous, 50% au-dessus)
        """)

    # === ÉVOLUTION MENSUELLE (TABLEAU + GRAPHIQUE COMBINÉS) ===
    with st.expander("📊 Évolution mensuelle", expanded=True):
        df_mensuel = df_periode.copy()
        df_mensuel["mois"] = df_mensuel["date"].dt.to_period("M")
        df_mensuel["mois_str"] = df_mensuel["date"].dt.strftime("%b %Y")

        # Préparation données
        df_evolution = df_mensuel.groupby(["mois_str", "type"])["montant"].sum().unstack(fill_value=0)
        df_evolution = df_evolution.reindex(sorted(df_evolution.index, key=lambda x: pd.to_datetime(x, format='%b %Y')))

        if not df_evolution.empty:
            # Tableau compact
            st.markdown("**📋 Résumé mensuel**")
            df_display = df_evolution.copy()
            df_display["Solde"] = df_display.get("revenu", 0) - df_display.get("dépense", 0)
            df_display = df_display.reset_index()
            df_display.columns = ["Mois", "Dépenses", "Revenus", "Solde"]

            st.dataframe(
                df_display,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Mois": st.column_config.TextColumn("📅 Mois"),
                    "Dépenses": st.column_config.NumberColumn("💸 Dépenses", format="%.0f €"),
                    "Revenus": st.column_config.NumberColumn("💹 Revenus", format="%.0f €"),
                    "Solde": st.column_config.NumberColumn("💰 Solde", format="%+.0f €")
                }
            )

            # Graphique intégré
            st.markdown("**📈 Graphique d'évolution**")

            # Détection thème
            try:
                theme = st.get_option("theme.base")
                is_dark = theme == "dark"
            except:
                is_dark = False

            bg_color = "#0E1117" if is_dark else "white"
            text_color = "white" if is_dark else "black"

            fig, ax = plt.subplots(figsize=(12, 5))
            fig.patch.set_facecolor(bg_color)
            ax.set_facecolor(bg_color)
            ax.tick_params(colors=text_color)

            x_pos = np.arange(len(df_evolution.index))
            bar_width = 0.6

            # Barres revenus et dépenses
            if "revenu" in df_evolution.columns:
                ax.bar(x_pos, df_evolution["revenu"], bar_width, label="Revenus", color="#00D4AA", alpha=0.9)
            if "dépense" in df_evolution.columns:
                ax.bar(x_pos, -df_evolution["dépense"], bar_width, label="Dépenses", color="#FF6B6B", alpha=0.9)

            # Ligne de solde
            if "revenu" in df_evolution.columns and "dépense" in df_evolution.columns:
                solde = df_evolution["revenu"] - df_evolution["dépense"]
                ax.plot(x_pos, solde, label="Solde", color="#4A90E2", marker='o', linewidth=2.5, markersize=5)

            ax.axhline(0, color=text_color, linewidth=1, alpha=0.5)
            ax.set_ylabel("Montant (€)", color=text_color, fontweight='bold')
            ax.set_xlabel("Mois", color=text_color, fontweight='bold')
            ax.set_xticks(x_pos)
            ax.set_xticklabels(df_evolution.index, rotation=45, ha='right', color=text_color)
            ax.legend(facecolor=bg_color, edgecolor=text_color, labelcolor=text_color)
            ax.grid(True, alpha=0.2)

            for spine in ax.spines.values():
                spine.set_color(text_color)
                spine.set_alpha(0.3)

            plt.tight_layout()
            st.pyplot(fig)
        else:
            st.info("Pas assez de données pour l'analyse mensuelle")

    # === RÉPARTITION PAR CATÉGORIES ===
    with st.expander("🥧 Répartition par catégories"):
        col1, col2 = st.columns(2)

        # Détection thème pour les pie charts
        try:
            theme = st.get_option("theme.base")
            is_dark = theme == "dark"
        except:
            is_dark = False

        bg_color = "#0E1117" if is_dark else "white"
        text_color = "white" if is_dark else "black"

        with col1:
            st.markdown("**💸 Dépenses par catégorie**")
            depenses_df = df_periode[df_periode["type"] == "dépense"]
            if not depenses_df.empty:
                categories_depenses = depenses_df.groupby("categorie")["montant"].sum().sort_values(ascending=False)

                # Top 6 + Autres
                top_categories = categories_depenses.head(6)
                autres = categories_depenses[6:].sum() if len(categories_depenses) > 6 else 0
                if autres > 0:
                    top_categories = top_categories.copy()
                    top_categories["Autres"] = autres

                fig, ax = plt.subplots(figsize=(7, 5))
                fig.patch.set_facecolor(bg_color)
                ax.set_facecolor(bg_color)

                colors = plt.cm.Set3(np.linspace(0, 1, len(top_categories)))
                wedges, texts, autotexts = ax.pie(
                    top_categories.values,
                    labels=top_categories.index,
                    autopct='%1.1f%%',
                    startangle=90,
                    colors=colors,
                    wedgeprops={'edgecolor': bg_color, 'linewidth': 2}
                )

                for text in texts:
                    text.set_color(text_color)
                for autotext in autotexts:
                    autotext.set_color('white' if is_dark else 'black')
                    autotext.set_fontweight('bold')

                ax.axis('equal')
                st.pyplot(fig)
            else:
                st.info("Aucune dépense")

        with col2:
            st.markdown("**💹 Revenus par catégorie**")
            revenus_df = df_periode[df_periode["type"] == "revenu"]
            if not revenus_df.empty:
                categories_revenus = revenus_df.groupby("categorie")["montant"].sum().sort_values(ascending=False)

                fig, ax = plt.subplots(figsize=(7, 5))
                fig.patch.set_facecolor(bg_color)
                ax.set_facecolor(bg_color)

                colors = plt.cm.Pastel1(np.linspace(0, 1, len(categories_revenus)))
                wedges, texts, autotexts = ax.pie(
                    categories_revenus.values,
                    labels=categories_revenus.index,
                    autopct='%1.1f%%',
                    startangle=90,
                    colors=colors,
                    wedgeprops={'edgecolor': bg_color, 'linewidth': 2}
                )

                for text in texts:
                    text.set_color(text_color)
                for autotext in autotexts:
                    autotext.set_color('white' if is_dark else 'black')
                    autotext.set_fontweight('bold')

                ax.axis('equal')
                st.pyplot(fig)
            else:
                st.info("Aucun revenu")

    # === TOPS TRANSACTIONS (MENU DÉROULANT + GRAPHIQUE) ===
    with st.expander("🎯 Tops transactions"):
        col1, col2 = st.columns([1, 3])

        with col1:
            type_top = st.radio("Type", ["💸 Dépenses", "💹 Revenus"], key="type_top")
            nombre_top = st.selectbox("Nombre", [5, 10, 15, 20], key="nb_top")

        with col2:
            if type_top == "💸 Dépenses":
                top_trans = df_periode[df_periode["type"] == "dépense"].nlargest(nombre_top, "montant")
                couleur = "#FF6B6B"
                signe = "-"
            else:
                top_trans = df_periode[df_periode["type"] == "revenu"].nlargest(nombre_top, "montant")
                couleur = "#00D4AA"
                signe = "+"

            if not top_trans.empty:
                # Graphique horizontal
                fig, ax = plt.subplots(figsize=(10, max(5, nombre_top * 0.4)))

                try:
                    theme = st.get_option("theme.base")
                    is_dark = theme == "dark"
                except:
                    is_dark = False

                bg_color = "#0E1117" if is_dark else "white"
                text_color = "white" if is_dark else "black"

                fig.patch.set_facecolor(bg_color)
                ax.set_facecolor(bg_color)
                ax.tick_params(colors=text_color)

                # Labels avec catégorie + date
                labels = [f"{row['categorie']}\n{row['date'].strftime('%d/%m/%y')}" for _, row in top_trans.iterrows()]
                y_pos = np.arange(len(labels))

                ax.barh(y_pos, top_trans["montant"], color=couleur, alpha=0.8)
                ax.set_yticks(y_pos)
                ax.set_yticklabels(labels, color=text_color)
                ax.set_xlabel("Montant (€)", color=text_color, fontweight='bold')
                ax.set_title(f"Top {nombre_top} {type_top}", color=text_color, fontweight='bold')
                ax.grid(True, alpha=0.2, axis='x')
                ax.invert_yaxis()

                # Valeurs sur barres
                for i, v in enumerate(top_trans["montant"]):
                    ax.text(v, i, f" {v:.0f}€", va='center', color=text_color, fontweight='bold')

                for spine in ax.spines.values():
                    spine.set_color(text_color)
                    spine.set_alpha(0.3)

                plt.tight_layout()
                st.pyplot(fig)

                # Liste détaillée dessous
                st.markdown("**📋 Détails des transactions**")
                for idx, trans in top_trans.iterrows():
                    col_a, col_b = st.columns([4, 1])
                    with col_a:
                        st.write(f"**{trans['categorie']}** → {trans['sous_categorie']}")
                        st.caption(f"📅 {trans['date'].strftime('%d/%m/%Y')}")
                    with col_b:
                        st.markdown(f"<p style='color: {couleur}; font-size: 18px; text-align: right; font-weight: bold;'>{signe}{trans['montant']:.2f} €</p>", unsafe_allow_html=True)
                    st.markdown("---")
            else:
                st.info("Aucune transaction")

    # === DERNIÈRES TRANSACTIONS ===
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


