"""
Recurrences Page Module

This module contains all recurrence-related interface functions including:
- Create recurring transaction interface
- Manage recurring transactions interface (edit, delete, version history)
"""

import streamlit as st
import pandas as pd
import re
import matplotlib.pyplot as plt
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from typing import Optional
import logger
from config import DB_PATH
from modules.database.connection import get_db_connection
from modules.ui.helpers import (
    load_recurrent_transactions,
    insert_transaction_batch,
    refresh_and_rerun
)
from modules.ui.components import toast_success, toast_error
from modules.utils.converters import safe_convert, safe_date_convert
from modules.services.file_service import supprimer_fichiers_associes


def interface_transaction_recurrente(type_transaction: str = "dépense") -> None:
    """
    Interface for creating recurring transactions.

    Features:
    - Create recurring expense or revenue
    - Auto-backfill past occurrences
    - Auto-create budget for recurring expenses
    - Support for weekly, monthly, and annual recurrence

    Args:
        type_transaction: Type of transaction ("dépense" or "revenu")

    Returns:
        None
    """
    with st.form("ajouter_transaction_recurrente", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            categorie = st.text_input("Catégorie principale (ex: logement, assurance, salaire)")
            sous_categorie = st.text_input("Sous-catégorie (ex: EDF, Netflix, Loyer)")
            montant = st.number_input("Montant (€)", min_value=0.0, format="%.2f", step=0.01)
        with col2:
            recurrence = st.selectbox("Fréquence", ["hebdomadaire", "mensuelle", "annuelle"])
            date_debut = st.date_input("Date de début", date.today())
            date_fin = st.date_input("Date de fin (facultatif)", None)
        submit_btn = st.form_submit_button("💾 Enregistrer la récurrence")

    if submit_btn:
        if not categorie or montant <= 0:
            toast_error("Veuillez entrer une catégorie et un montant valide.")
            return

        safe_categorie = re.sub(r'[<>:"/\\|?*]', "_", categorie.strip())
        safe_sous_categorie = re.sub(r'[<>:"/\\|?*]', "_", sous_categorie.strip()) if sous_categorie else ""

        today = date.today()
        occurrences = []
        current_date = date_debut
        while current_date <= today:
            occurrences.append(current_date)
            if recurrence == "hebdomadaire":
                current_date += timedelta(weeks=1)
            elif recurrence == "mensuelle":
                current_date += relativedelta(months=1)
            elif recurrence == "annuelle":
                current_date += relativedelta(years=1)
            if date_fin and current_date > date_fin:
                break

        transactions = [
            {
                "type": type_transaction,
                "categorie": safe_categorie,
                "sous_categorie": safe_sous_categorie,
                "montant": montant,
                "date": date_debut.isoformat(),
                "source": "récurrente",
                "recurrence": recurrence,
                "date_fin": date_fin.isoformat() if date_fin else ""
            }
        ] + [
            {
                "type": type_transaction,
                "categorie": safe_categorie,
                "sous_categorie": safe_sous_categorie,
                "montant": montant,
                "date": d.isoformat(),
                "source": "récurrente_auto",
                "recurrence": recurrence
            } for d in occurrences
        ]

        insert_transaction_batch(transactions)

        # AUTO-CREATE BUDGET only for recurring expenses
        if type_transaction == "dépense":
            # Calculate monthly budget amount based on recurrence frequency
            if recurrence == "hebdomadaire":
                monthly_amount = montant * 4.33  # approximately 4.33 weeks per month
            elif recurrence == "mensuelle":
                monthly_amount = montant
            elif recurrence == "annuelle":
                monthly_amount = montant / 12

            # Insert or update the budget for this category
            conn = get_db_connection()
            cursor = conn.cursor()
            now = datetime.now().isoformat()

            cursor.execute("""
                INSERT OR IGNORE INTO budgets_categories
                (categorie, budget_mensuel, date_creation, date_modification)
                VALUES (?, ?, ?, ?)
            """, (safe_categorie, monthly_amount, now, now))

            conn.commit()
            conn.close()

            toast_success(f"Transaction récurrente ajoutée ({recurrence})")
            st.success(f"✅ Budget auto-créé pour la catégorie '{safe_categorie}' : {monthly_amount:.2f}€/mois")
        else:
            toast_success(f"Transaction récurrente ajoutée ({recurrence})")
            st.success(f"✅ Revenu récurrent créé pour la catégorie '{safe_categorie}'")

        st.info(f"{len(occurrences)} occurrence(s) passée(s) ajoutée(s).")


def interface_gerer_recurrences() -> None:
    """
    Interface for managing recurring transactions.

    Features:
    - View all active recurrences
    - Create new version with different amount (preserves history)
    - Update all occurrences (modifies history)
    - Delete entire recurrence
    - View version history with evolution chart
    - Impact calculation for changes (monthly, annual)

    Tab 1: Manage recurrences
    - Grouped by category/subcategory
    - Show current amount and frequency
    - Impact preview for changes
    - Three action buttons:
      1. Create new version (recommended - preserves history)
      2. Update all occurrences (modifies history)
      3. Delete

    Tab 2: Version history
    - Timeline of all versions per recurrence
    - Evolution chart showing amount changes over time

    Returns:
        None
    """
    st.subheader("🔁 Gérer les transactions récurrentes V3 - Avec historique")

    # Tab pour séparer gestion et historique
    tab1, tab2 = st.tabs(["📝 Gérer les récurrences", "📊 Historique des versions"])

    with tab1:
        df = load_recurrent_transactions()

        if df.empty:
            st.info("Aucune transaction récurrente trouvée.")
            return

        # Grouper par catégorie/sous-catégorie pour avoir une vue unique par récurrence
        df_grouped = df.groupby(['categorie', 'sous_categorie']).agg({
            'id': 'first',
            'type': 'first',
            'montant': 'first',
            'recurrence': 'first',
            'date': 'first',
            'date_fin': 'first'
        }).reset_index()

        st.markdown("### 📋 Liste des récurrences actives")

        # Afficher les récurrences sous forme de cartes
        for idx, row in df_grouped.iterrows():
            with st.expander(f"{'🟢' if row['type'] == 'revenu' else '🔴'} {row['categorie']} → {row['sous_categorie']}", expanded=False):
                col1, col2, col3 = st.columns([2, 2, 1])

                with col1:
                    st.metric("💰 Montant actuel", f"{safe_convert(row['montant'], float, 0.0):.2f} €")
                    st.caption(f"🔁 Récurrence : {row['recurrence']}")

                with col2:
                    date_debut = safe_date_convert(row['date'])
                    date_fin = safe_date_convert(row['date_fin']) if row['date_fin'] else None
                    st.caption(f"📅 Début : {date_debut.strftime('%d/%m/%Y')}")
                    if date_fin:
                        st.caption(f"📅 Fin : {date_fin.strftime('%d/%m/%Y')}")
                    else:
                        st.caption("📅 Fin : Indéterminée")

                with col3:
                    st.caption(f"Type : {row['type']}")

                st.markdown("---")
                st.markdown("#### ✏️ Modifier cette récurrence")

                # Formulaire de modification
                col_form1, col_form2 = st.columns(2)

                with col_form1:
                    new_montant = st.number_input(
                        "Nouveau montant (€)",
                        value=float(safe_convert(row['montant'], float, 0.0)),
                        step=0.01,
                        key=f"montant_{idx}"
                    )

                    new_recurrence = st.selectbox(
                        "Récurrence",
                        ["hebdomadaire", "mensuelle", "annuelle"],
                        index=["hebdomadaire", "mensuelle", "annuelle"].index(row["recurrence"]),
                        key=f"rec_{idx}"
                    )

                with col_form2:
                    date_application = st.date_input(
                        "📅 Appliquer à partir du",
                        value=datetime.now().date(),
                        help="Les occurrences avant cette date garderont l'ancien montant",
                        key=f"date_app_{idx}"
                    )

                    nouvelle_date_fin = st.date_input(
                        "📅 Date de fin",
                        value=date_fin if date_fin else datetime.now().date() + timedelta(days=365),
                        key=f"date_fin_{idx}"
                    )

                # Calcul de l'impact
                montant_actuel = safe_convert(row['montant'], float, 0.0)
                difference = new_montant - montant_actuel

                if difference != 0:
                    st.markdown("#### 💹 Impact prévisionnel")

                    # Calculer l'impact sur 12 mois
                    if new_recurrence == "hebdomadaire":
                        occurrences_par_an = 52
                    elif new_recurrence == "mensuelle":
                        occurrences_par_an = 12
                    else:  # annuelle
                        occurrences_par_an = 1

                    impact_annuel = difference * occurrences_par_an
                    impact_color = "green" if impact_annuel > 0 else "red"
                    impact_icon = "📈" if impact_annuel > 0 else "📉"

                    col_imp1, col_imp2, col_imp3 = st.columns(3)

                    with col_imp1:
                        st.metric("Différence par occurrence", f"{difference:+.2f} €")

                    with col_imp2:
                        st.metric("Impact mensuel", f"{(difference * occurrences_par_an / 12):+.2f} €")

                    with col_imp3:
                        st.metric("Impact annuel", f"{impact_annuel:+.2f} €")

                    st.markdown(f"""
                    <div style='background: linear-gradient(135deg, {"#d1fae5" if impact_annuel > 0 else "#fee2e2"} 0%, {"#a7f3d0" if impact_annuel > 0 else "#fecaca"} 100%);
                         padding: 15px; border-radius: 10px; margin: 10px 0;
                         border-left: 5px solid {impact_color};'>
                        <strong>{impact_icon} Impact sur 12 mois : {impact_annuel:+.2f} €</strong>
                        <br><small>Cette modification {"augmentera" if impact_annuel > 0 else "réduira"} votre solde de {abs(impact_annuel):.2f}€ par an</small>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("---")

                # Boutons d'action
                col_btn1, col_btn2, col_btn3 = st.columns(3)

                with col_btn1:
                    if st.button("💾 Créer nouvelle version", key=f"save_{idx}", type="primary"):
                        # Créer une nouvelle version
                        conn = get_db_connection()
                        cursor = conn.cursor()

                        # 1. Mettre à jour l'ancienne version avec une date de fin
                        cursor.execute("""
                            UPDATE transactions
                            SET date_fin = ?
                            WHERE source='récurrente_auto'
                            AND categorie = ?
                            AND sous_categorie = ?
                            AND (date_fin IS NULL OR date_fin > ?)
                        """, (
                            date_application.isoformat(),
                            row['categorie'],
                            row['sous_categorie'],
                            date_application.isoformat()
                        ))

                        # 2. Créer la nouvelle version
                        cursor.execute("""
                            INSERT INTO transactions
                            (type, categorie, sous_categorie, montant, date, source, recurrence, date_fin, description)
                            VALUES (?, ?, ?, ?, ?, 'récurrente_auto', ?, ?, ?)
                        """, (
                            row['type'],
                            row['categorie'],
                            row['sous_categorie'],
                            new_montant,
                            date_application.isoformat(),
                            new_recurrence,
                            nouvelle_date_fin.isoformat(),
                            f"Version créée le {datetime.now().strftime('%d/%m/%Y')} - Ancien montant: {montant_actuel:.2f}€"
                        ))

                        conn.commit()
                        conn.close()

                        st.success(f"""
                        ✅ **Nouvelle version créée !**
                        - Ancien montant : {montant_actuel:.2f}€ (jusqu'au {(date_application - timedelta(days=1)).strftime('%d/%m/%Y')})
                        - Nouveau montant : {new_montant:.2f}€ (à partir du {date_application.strftime('%d/%m/%Y')})

                        Les transactions futures seront créées avec le nouveau montant.
                        """)
                        toast_success("c'est dur la france de Macron")
                        refresh_and_rerun()

                with col_btn2:
                    if st.button("🔄 Modifier toutes les occurrences", key=f"update_all_{idx}"):
                        conn = get_db_connection()
                        cursor = conn.cursor()

                        # Modifier toutes les occurrences (passées et futures)
                        cursor.execute("""
                            UPDATE transactions
                            SET montant = ?, recurrence = ?, date_fin = ?
                            WHERE (source LIKE 'récurrente%' OR source = 'récurrence_auto')
                            AND categorie = ?
                            AND sous_categorie = ?
                        """, (
                            new_montant,
                            new_recurrence,
                            nouvelle_date_fin.isoformat(),
                            row['categorie'],
                            row['sous_categorie']
                        ))

                        conn.commit()
                        conn.close()

                        st.success(f"""
                        ✅ **Toutes les occurrences modifiées !**
                        - Nouveau montant : {new_montant:.2f}€
                        - Récurrence : {new_recurrence}

                        ⚠️ L'historique a été modifié.
                        """)
                        refresh_and_rerun()

                with col_btn3:
                    if st.button("🗑️ Supprimer", key=f"delete_{idx}"):
                        conn = get_db_connection()
                        cursor = conn.cursor()

                        # First, get all transactions to delete for file cleanup
                        df_to_delete = pd.read_sql_query("""
                            SELECT * FROM transactions
                            WHERE (source LIKE 'récurrente%' OR source = 'récurrence_auto')
                            AND categorie = ?
                            AND sous_categorie = ?
                        """, conn, params=(row['categorie'], row['sous_categorie']))

                        # Delete associated files for OCR/PDF sourced transactions
                        fichiers_supprimes = 0
                        for _, transaction in df_to_delete.iterrows():
                            if transaction.get("source") in ["OCR", "PDF"]:
                                nb_supprimes = supprimer_fichiers_associes(transaction.to_dict())
                                fichiers_supprimes += nb_supprimes

                        # Delete from database
                        cursor.execute("""
                            DELETE FROM transactions
                            WHERE (source LIKE 'récurrente%' OR source = 'récurrence_auto')
                            AND categorie = ?
                            AND sous_categorie = ?
                        """, (row['categorie'], row['sous_categorie']))

                        conn.commit()
                        conn.close()

                        message = "🗑️ Récurrence supprimée entièrement."
                        if fichiers_supprimes > 0:
                            message += f" ({fichiers_supprimes} fichier(s) supprimé(s))"
                        st.success(message)
                        refresh_and_rerun()

    with tab2:
        st.markdown("### 📊 Historique des versions de récurrences")

        conn = get_db_connection()
        df_all = pd.read_sql_query("""
            SELECT * FROM transactions
            WHERE source='récurrente_auto'
            ORDER BY categorie, sous_categorie, date ASC
        """, conn)
        conn.close()

        if df_all.empty:
            st.info("Aucun historique disponible.")
            return

        # Grouper par catégorie/sous-catégorie
        for (cat, souscat), group in df_all.groupby(['categorie', 'sous_categorie']):
            st.markdown(f"#### {cat} → {souscat}")

            # Afficher l'historique des versions
            versions = []
            for idx, row in group.iterrows():
                date_debut = safe_date_convert(row['date'])
                date_fin = safe_date_convert(row['date_fin']) if row['date_fin'] else None
                montant = safe_convert(row['montant'], float, 0.0)

                versions.append({
                    'Version': f"V{len(versions) + 1}",
                    'Période': f"{date_debut.strftime('%d/%m/%Y')} → {date_fin.strftime('%d/%m/%Y') if date_fin else 'En cours'}",
                    'Montant': f"{montant:.2f} €",
                    'Récurrence': row['recurrence'],
                    'Type': row['type']
                })

            df_versions = pd.DataFrame(versions)
            st.dataframe(df_versions, use_container_width=True, hide_index=True)

            # Graphique d'évolution du montant
            if len(versions) > 1:
                st.markdown("##### 📈 Évolution du montant")

                fig, ax = plt.subplots(figsize=(10, 3))
                montants = [safe_convert(row['montant'], float, 0.0) for _, row in group.iterrows()]
                dates = [safe_date_convert(row['date']) for _, row in group.iterrows()]

                ax.plot(dates, montants, marker='o', linewidth=2, markersize=8, color='#667eea')
                ax.set_xlabel("Date", fontweight='bold')
                ax.set_ylabel("Montant (€)", fontweight='bold')
                ax.set_title(f"Évolution du montant - {cat}", fontweight='bold')
                ax.grid(True, alpha=0.3)
                plt.xticks(rotation=45)
                plt.tight_layout()

                st.pyplot(fig)

            st.markdown("---")
