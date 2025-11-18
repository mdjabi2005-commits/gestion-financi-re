"""
Transactions Page Module

This module contains all transaction-related interface functions including:
- Simplified transaction interface (main menu)
- View/Edit transactions interface
- Add expenses interface (manual + CSV import)
"""

import streamlit as st
import pandas as pd
import io
import sqlite3
from datetime import datetime, date, timedelta
from typing import Optional
import logger
from config import DB_PATH, TO_SCAN_DIR , REVENUS_A_TRAITER
from modules.database.connection import get_db_connection
from modules.ui.helpers import (
    load_transactions,
    load_recurrent_transactions,
    insert_transaction_batch,
    refresh_and_rerun
)

from modules.ui.components import toast_success, toast_error, toast_warning, afficher_documents_associes, get_badge_icon
from modules.utils.converters import safe_convert, safe_date_convert
from modules.services.revenue_service import process_uber_revenue
from modules.services.recurrence_service import backfill_recurrences_to_today
from modules.services.file_service import (
    deplacer_fichiers_associes,
    supprimer_fichiers_associes
)


def interface_transactions_simplifiee() -> None:
    """
    Simplified transaction interface - main menu for adding transactions.

    Features:
    - Scanner un ticket (OCR)
    - Ajouter des dépenses (manuel + CSV)
    - Créer une transaction récurrente
    - Ajouter un revenu

    Returns:
        None
    """
    st.title("💸 Ajouter une Transaction")

    # Menu de sélection principal
    col1, col2 = st.columns([3, 1])

    with col1:
        type_action = st.selectbox(
            "Que voulez-vous faire ?",
            [
                "📸 Scanner un ticket (OCR)",
                "💰 Scanner un revenu (PDF),
                "🔁 Créer une transaction récurrente",
                "💸 Ajouter une Transaction"
            ],
            key="type_action_transaction"
        )

    with col2:
        st.caption("")
        st.caption("")
        if st.button("🔄 Actualiser", key="refresh_transactions"):
            refresh_and_rerun()

    st.markdown("---")

    # === SCANNER UN TICKET ===
    if type_action == "📸 Scanner un ticket (OCR)":
        st.subheader("📸 Scanner les tickets automatiquement")
        st.info(f"**📂 Dossier de scan :** `{TO_SCAN_DIR}`")

        with st.expander("ℹ️ Comment ça marche ?", expanded=False):
            st.markdown(f"""
            ### Mode d'emploi :
            1. **Nommer votre ticket** avec le format : `nom.categorie.sous_categorie.extension`
               - Exemple : `carrefour.alimentation.courses.jpg`
               - Exemple : `shell.transport.essence.jpg`
            2. **Déposer le fichier** dans le dossier : `{TO_SCAN_DIR}`
            3. **Cliquer sur "Scanner"** ci-dessous
            4. **Vérifier et valider** les informations détectées

            **Formats acceptés :** JPG, PNG, PDF
            """)

        # Import scanning function here to avoid circular imports
        from .scanning import process_all_tickets_in_folder
        process_all_tickets_in_folder()

    # === AJOUTER DES DÉPENSES (MANUEL + CSV) ===
    elif type_action == "💰 Scanner un revenu (PDF)":
        from .revenues import process_all_revenues_in_folder
        st.subheader("💰 Scanner un revenu (PDF)")
        st.info(f"**📂 Dossier de scan :** `{REVENUS_A_TRAITER}`")
        process_all_revenues_in_folder()
        
    # === TRANSACTION RÉCURRENTE (DÉPENSE OU REVENU) ===
    elif type_action == "🔁 Créer une transaction récurrente":
        st.subheader("🔁 Créer une transaction récurrente")

        # Sélecteur de type
        col1, col2 = st.columns([1, 3])
        with col1:
            type_transaction = st.radio(
                "Type",
                ["💸 Dépense", "💰 Revenu"],
                horizontal=True,
                key="type_transaction_selector"
            )

        type_val = "dépense" if "Dépense" in type_transaction else "revenu"

        if type_val == "dépense":
            st.info("💡 Les dépenses récurrentes sont automatiquement ajoutées chaque mois/semaine")
            st.info("📊 Un budget sera créé automatiquement pour cette catégorie")
        else:
            st.info("💡 Les revenus récurrents sont automatiquement ajoutés chaque mois/semaine")

        # Import recurrence function to avoid circular imports
        from .recurrences import interface_transaction_recurrente
        interface_transaction_recurrente(type_transaction=type_val)

    # === REVENU (NON-RÉCURRENT) ===
    elif type_action == "💸 Ajouter une Transaction":
        st.subheader("💸 Ajouter une Transaction")

        # Import revenue function to avoid circular imports
        from .transactions import  interface_transactions_simplifiee
        interface_transactions_simplifiee()


def interface_ajouter_depenses_fusionnee() -> None:
    """
    Unified interface for adding expenses (manual + CSV import).

    Features:
    - Manual entry form
    - CSV bulk import with template download
    - Duplicate detection
    - Uber revenue processing support

    Returns:
        None
    """
    st.subheader("💸 Ajouter des dépenses")

    # Tabs pour séparer clairement les deux méthodes
    tab1, tab2 = st.tabs(["✍️ Ajout manuel", "📄 Import CSV"])

    # ===== TAB 1: AJOUT MANUEL =====
    with tab1:
        st.markdown("### ✍️ Ajouter une dépense manuellement")
        st.info("💡 Remplissez le formulaire ci-dessous pour ajouter une seule dépense")

        with st.form("add_manual_depense"):
            col1, col2, col3 = st.columns(3)

            with col1:
                date_tr = st.date_input("📅 Date", value=date.today())
                type_tr = st.selectbox("📊 Type", ["dépense", "revenu"])

            with col2:
                cat = st.text_input("🏷️ Catégorie principale", placeholder="Ex: Alimentation")
                sous_cat = st.text_input("📌 Sous-catégorie", placeholder="Ex: Courses")

            with col3:
                montant = st.number_input("💰 Montant (€)", min_value=0.0, step=0.01, format="%.2f")
                desc = st.text_input("📝 Description", placeholder="Ex: Carrefour")

            valider = st.form_submit_button("✅ Ajouter la transaction", type="primary")

        if valider:
            if not cat or montant <= 0:
                toast_error("Veuillez entrer au moins une catégorie et un montant valide.")
            else:
                transaction_data = {
                    "type": type_tr,
                    "categorie": cat.strip().lower(),
                    "sous_categorie": sous_cat.strip().lower(),
                    "description": desc.strip(),
                    "montant": float(montant),
                    "date": date_tr.isoformat(),
                    "source": "manuel"
                }

                # Process Uber revenue if applicable
                if type_tr == "revenu":
                    transaction_data, uber_msg = process_uber_revenue(transaction_data)
                    if uber_msg:
                        st.success(uber_msg)

                insert_transaction_batch([transaction_data])
                toast_success(f"✅ Transaction ajoutée : {cat} — {transaction_data['montant']:.2f} €")
                st.balloons()
                st.info("💡 N'oubliez pas d'actualiser la page pour voir vos changements")

    # ===== TAB 2: IMPORT CSV =====
    with tab2:
        st.markdown("### 📄 Importer plusieurs dépenses depuis un fichier CSV")

        # Guide étape par étape
        st.markdown("#### 📋 Guide d'importation")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("##### 1️⃣ Télécharger le modèle")
            st.caption("Téléchargez le fichier modèle CSV avec les colonnes requises")

            # Créer un modèle CSV
            modele_csv = """type,date,categorie,sous_categorie,montant,description
dépense,2024-01-15,alimentation,courses,45.50,Carrefour
dépense,2024-01-16,transport,essence,60.00,Shell Station
revenu,2024-01-01,salaire,mensuel,2500.00,Salaire janvier
dépense,2024-01-20,loisirs,restaurant,35.80,Pizza
revenu,2024-01-15,freelance,mission,450.00,Projet X"""

            st.download_button(
                label="⬇️ Télécharger le modèle",
                data=modele_csv,
                file_name="modele_transactions.csv",
                mime="text/csv",
                help="Modèle avec exemples de transactions"
            )

        with col2:
            st.markdown("##### 2️⃣ Compléter le fichier")
            st.caption("Ouvrez le fichier dans Excel/LibreOffice et ajoutez vos transactions")
            st.markdown("""
            **Colonnes requises :**
            - `type` : dépense ou revenu
            - `date` : AAAA-MM-JJ
            - `categorie` : Catégorie principale
            - `sous_categorie` : Sous-catégorie
            - `montant` : Montant (avec . ou ,)
            - `description` : Description
            """)

        with col3:
            st.markdown("##### 3️⃣ Importer le fichier")
            st.caption("Uploadez votre fichier CSV complété ci-dessous")

        st.markdown("---")

        # Zone d'upload
        uploaded_file = st.file_uploader(
            "📤 Sélectionner votre fichier CSV",
            type=['csv'],
            help="Sélectionnez le fichier CSV avec vos transactions",
            key="csv_uploader_depenses"
        )

        if uploaded_file is not None:
            st.success(f"✅ Fichier '{uploaded_file.name}' chargé !")

            try:
                # Lire le CSV
                df_import = pd.read_csv(io.StringIO(uploaded_file.getvalue().decode('utf-8')))

                st.markdown("#### 📊 Aperçu des données")
                st.dataframe(df_import.head(10), use_container_width=True)

                st.info(f"📈 **{len(df_import)}** transactions détectées dans le fichier")

                # Options d'import
                col1, col2 = st.columns(2)

                with col1:
                    ignorer_doublons = st.checkbox(
                        "🔒 Ignorer les doublons",
                        value=True,
                        help="Évite d'importer plusieurs fois la même transaction"
                    )

                with col2:
                    st.caption("")

                # Bouton d'import
                if st.button("✅ Importer les transactions", type="primary", key="import_csv_depenses_btn"):
                    with st.spinner("Import en cours..."):
                        # Préparer les transactions
                        transactions_a_importer = []

                        for idx, row in df_import.iterrows():
                            # Conversion sécurisée
                            transaction = {
                                "type": str(row.get('type', 'dépense')).strip().lower(),
                                "date": str(row.get('date', datetime.now().date())),
                                "categorie": str(row.get('categorie', 'Divers')).strip(),
                                "sous_categorie": str(row.get('sous_categorie', 'Autre')).strip(),
                                "montant": safe_convert(row.get('montant', 0)),
                                "description": str(row.get('description', '')).strip() if pd.notna(row.get('description')) else "",
                                "source": "CSV Import"
                            }

                            # Validation basique
                            if transaction["montant"] > 0:
                                transactions_a_importer.append(transaction)

                        if transactions_a_importer:
                            # Insertion
                            if ignorer_doublons:
                                # Charger transactions existantes pour vérifier doublons
                                df_existant = load_transactions()
                                nouvelles = []
                                doublons = 0

                                for trans in transactions_a_importer:
                                    # Vérification doublon simple (même date, montant, catégorie)
                                    est_doublon = False
                                    if not df_existant.empty:
                                        est_doublon = (
                                            (df_existant['date'] == pd.Timestamp(trans['date'])) &
                                            (df_existant['montant'] == trans['montant']) &
                                            (df_existant['categorie'] == trans['categorie'])
                                        ).any()

                                    if not est_doublon:
                                        nouvelles.append(trans)
                                    else:
                                        doublons += 1

                                if nouvelles:
                                    insert_transaction_batch(nouvelles)
                                    toast_success(f"✅ {len(nouvelles)} transaction(s) importée(s) avec succès !")
                                    if doublons > 0:
                                        st.warning(f"⚠️ {doublons} doublon(s) ignoré(s)")
                                else:
                                    st.warning("⚠️ Toutes les transactions sont des doublons")
                            else:
                                insert_transaction_batch(transactions_a_importer)
                                toast_success(f"✅ {len(transactions_a_importer)} transaction(s) importée(s) !")

                            st.balloons()
                            st.info("💡 N'oubliez pas d'actualiser la page pour voir vos changements")
                        else:
                            toast_error("Aucune transaction valide trouvée dans le fichier")

            except Exception as e:
                st.error(f"❌ Erreur lors de la lecture du fichier : {e}")
                st.caption("Vérifiez que le fichier respecte bien le format du modèle")


def interface_voir_transactions_v3() -> None:
    """
    View and edit transactions interface with filters and data editor.

    Features:
    - Advanced filtering (period, type, category)
    - Consultation mode (read-only)
    - Edition mode (edit/delete transactions)
    - Quick stats display
    - Associated documents viewing
    - Recurrence management in expander

    Returns:
        None
    """
    st.title("📊 Mes Transactions")

    backfill_recurrences_to_today(DB_PATH)
    df = load_transactions()

    if df.empty:
        st.info("💰 Aucune transaction enregistrée. Commencez par en ajouter !")
        return

    # === FILTRES SIMPLIFIÉS ===
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])

    with col1:
        # Filtre de période simplifié
        periode = st.selectbox(
            "📅 Période",
            ["Tout voir", "Ce mois", "Mois dernier", "30 derniers jours", "Cette année", "Personnalisée"],
            key="periode_voir_v3"
        )

    # Calculer dates selon période
    today = datetime.now().date()

    if periode == "Tout voir":
        date_debut, date_fin = None, None
    elif periode == "Ce mois":
        date_debut = today.replace(day=1)
        date_fin = today
    elif periode == "Mois dernier":
        premier_mois = today.replace(day=1)
        date_fin = premier_mois - timedelta(days=1)
        date_debut = date_fin.replace(day=1)
    elif periode == "30 derniers jours":
        date_debut = today - timedelta(days=30)
        date_fin = today
    elif periode == "Cette année":
        date_debut = today.replace(month=1, day=1)
        date_fin = today
    else:  # Personnalisée
        with col2:
            date_debut = st.date_input("Début", value=today - timedelta(days=30), key="debut_v3")
        with col3:
            date_fin = st.date_input("Fin", value=today, key="fin_v3")

    # Afficher la période sélectionnée
    if periode != "Personnalisée":
        with col2:
            if date_debut:
                st.caption(f"📅 Du {date_debut.strftime('%d/%m/%y')}")
            else:
                st.caption("📅 Depuis le début")
        with col3:
            if date_fin:
                st.caption(f"📅 Au {date_fin.strftime('%d/%m/%y')}")
            else:
                st.caption("📅 Jusqu'à aujourd'hui")

    with col4:
        if st.button("🔄", help="Actualiser"):
            refresh_and_rerun()

    # Filtres supplémentaires (simplifiés)
    col1, col2, col3 = st.columns(3)

    with col1:
        type_filter = st.selectbox("Type", ["Toutes", "Dépense", "Revenu"], key="type_v3")

    with col2:
        categories = ["Toutes"] + sorted(df["categorie"].dropna().unique().tolist())
        cat_filter = st.selectbox("Catégorie", categories, key="cat_v3")

    with col3:
        # Mode affichage
        mode_affichage = st.selectbox("Mode", ["👁️ Consultation", "✏️ Édition"], key="mode_v3")

    st.markdown("---")

    # === APPLIQUER LES FILTRES ===
    df_filtered = df.copy()
    df_filtered["date"] = pd.to_datetime(df_filtered["date"])

    # Filtre période
    if date_debut and date_fin:
        df_filtered = df_filtered[
            (df_filtered["date"].dt.date >= date_debut) &
            (df_filtered["date"].dt.date <= date_fin)
        ]

    # Filtre type
    if type_filter == "Dépense":
        df_filtered = df_filtered[df_filtered["type"] == "dépense"]
    elif type_filter == "Revenu":
        df_filtered = df_filtered[df_filtered["type"] == "revenu"]

    # Filtre catégorie
    if cat_filter != "Toutes":
        df_filtered = df_filtered[df_filtered["categorie"] == cat_filter]

    # TRI PAR DATE (plus récentes en premier) - PAR DÉFAUT
    df_filtered = df_filtered.sort_values("date", ascending=False).reset_index(drop=True)

    if df_filtered.empty:
        st.warning("🔍 Aucune transaction trouvée avec ces filtres")
        return

    # Statistiques rapides (compactes)
    total_revenus = df_filtered[df_filtered["type"] == "revenu"]["montant"].sum()
    total_depenses = df_filtered[df_filtered["type"] == "dépense"]["montant"].sum()
    solde = total_revenus - total_depenses

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Transactions", len(df_filtered))
    with col2:
        st.metric("💹 Revenus", f"{total_revenus:.0f} €")
    with col3:
        st.metric("💸 Dépenses", f"{total_depenses:.0f} €")
    with col4:
        delta_color = "normal" if solde >= 0 else "inverse"
        st.metric("💰 Solde", f"{solde:+.0f} €", delta_color=delta_color)

    st.markdown("---")

    # === MODE CONSULTATION ===
    if mode_affichage == "👁️ Consultation":
        st.subheader("📋 Liste des transactions")

        # Tableau simplifié (non éditable)
        df_display = df_filtered.copy()
        df_display["montant"] = df_display["montant"].apply(lambda x: safe_convert(x, float, 0.0))

        # Ajouter icônes
        df_display["Type"] = df_display["type"].apply(lambda x: "🟢" if x == "revenu" else "🔴")
        df_display["Date"] = pd.to_datetime(df_display["date"]).dt.strftime("%d/%m/%Y")

        # Montant signé pour l'affichage
        df_display["Montant"] = df_display.apply(
            lambda row: row["montant"] if row["type"] == "revenu" else -row["montant"],
            axis=1
        )

        st.dataframe(
            df_display[["Type", "Date", "categorie", "sous_categorie", "Montant", "description"]].rename(columns={
                "categorie": "Catégorie",
                "sous_categorie": "Sous-catégorie",
                "description": "Description"
            }),
            use_container_width=True,
            height=500,
            hide_index=True,
            column_config={
                "Montant": st.column_config.NumberColumn("Montant (€)", format="%.2f €")
            }
        )

        # Expander pour détails
        with st.expander("🔍 Voir détails par transaction"):
            for idx, trans in df_display.head(20).iterrows():
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    type_icon = "💹" if trans["type"] == "revenu" else "💸"
                    st.write(f"{type_icon} **{trans['categorie']}** → {trans['sous_categorie']}")
                with col2:
                    st.caption(f"📅 {trans['Date']}")
                    if trans.get('description'):
                        st.caption(f"📝 {trans['description']}")
                with col3:
                    couleur = "#00D4AA" if trans["type"] == "revenu" else "#FF6B6B"
                    signe = "+" if trans["type"] == "revenu" else "-"
                    st.markdown(f"<p style='color: {couleur}; text-align: right; font-weight: bold;'>{signe}{abs(trans['Montant']):.2f} €</p>", unsafe_allow_html=True)

                # Afficher les documents associés si OCR ou PDF
                if trans.get('source') in ['OCR', 'PDF']:
                    with st.expander(f"📎 Voir les documents ({get_badge_icon(trans.to_dict())})", expanded=False):
                        afficher_documents_associes(trans.to_dict())

                st.markdown("---")

    # === MODE ÉDITION ===
    else:
        st.subheader("✏️ Modifier ou supprimer des transactions")

        st.info("💡 Modifiez les valeurs directement dans le tableau, puis cliquez sur 'Enregistrer'")

        # Préparer le tableau éditable
        df_edit = df_filtered.copy()
        df_edit["montant"] = df_edit["montant"].apply(lambda x: safe_convert(x, float, 0.0))

        # Ajouter colonne de suppression
        df_edit.insert(0, "🗑️", False)

        # Afficher l'éditeur (en incluant l'ID pour la synchronisation fiable)
        df_edited = st.data_editor(
            df_edit[["id", "🗑️", "date", "type", "categorie", "sous_categorie", "montant", "description"]],
            use_container_width=True,
            num_rows="fixed",
            hide_index=True,
            key="editor_v3",
            column_config={
                "id": st.column_config.NumberColumn("ID", disabled=True),
                "🗑️": st.column_config.CheckboxColumn("🗑️ Suppr.", help="Cocher pour supprimer"),
                "date": st.column_config.DateColumn("Date", format="DD/MM/YYYY"),
                "type": st.column_config.SelectboxColumn("Type", options=["dépense", "revenu"]),
                "categorie": st.column_config.TextColumn("Catégorie"),
                "sous_categorie": st.column_config.TextColumn("Sous-catégorie"),
                "montant": st.column_config.NumberColumn("Montant (€)", format="%.2f", min_value=0),
                "description": st.column_config.TextColumn("Description")
            }
        )

        # Boutons d'action
        col1, col2, col3 = st.columns([2, 2, 4])

        with col1:
            if st.button("💾 Enregistrer les modifications", type="primary", key="save_v3"):
                conn = get_db_connection()
                cursor = conn.cursor()
                modified = 0
                fichiers_deplaces = 0

                # Itérer sur les lignes éditées
                for idx, row in df_edited.iterrows():
                    # Récupérer l'original par ID pour synchronisation fiable
                    original_rows = df_edit[df_edit["id"] == row["id"]]
                    if original_rows.empty:
                        st.warning(f"⚠️ Transaction ID {row['id']} non trouvée dans l'original")
                        continue

                    original = original_rows.iloc[0]

                    # Détection des changements (simple et fiable)
                    has_changes = False
                    for col in ["type", "categorie", "sous_categorie", "description", "montant", "date"]:
                        if str(row[col]) != str(original[col]):
                            has_changes = True
                            break

                    if has_changes:
                        # Déplacer les fichiers si nécessaire (catégorie/sous-catégorie changées)
                        transaction_old = original.to_dict()
                        transaction_new = {
                            "categorie": row["categorie"],
                            "sous_categorie": row["sous_categorie"],
                            "source": original.get("source", ""),
                            "type": row["type"]
                        }

                        nb_deplaces = deplacer_fichiers_associes(transaction_old, transaction_new)
                        fichiers_deplaces += nb_deplaces

                        # Mise à jour de la base de données
                        cursor.execute("""
                            UPDATE transactions
                            SET type = ?, categorie = ?, sous_categorie = ?, montant = ?,
                                date = ?, description = ?
                            WHERE id = ?
                        """, (
                            str(row["type"]).strip().lower(),
                            str(row["categorie"]).strip().lower(),
                            str(row["sous_categorie"]).strip().lower(),
                            safe_convert(row["montant"], float, 0.0),
                            safe_date_convert(row["date"]).isoformat(),
                            str(row.get("description", "")).strip(),
                            row["id"]
                        ))
                        modified += 1

                try:
                    conn.commit()
                    conn.close()
                except Exception as e:
                    st.error(f"❌ Erreur lors de la sauvegarde en base de données: {str(e)}")
                    return

                if modified > 0:
                    message = f"✅ {modified} transaction(s) modifiée(s) !"
                    if fichiers_deplaces > 0:
                        message += f" ({fichiers_deplaces} fichier(s) déplacé(s))"
                    toast_success(message)
                    st.success(message)
                    refresh_and_rerun()
                else:
                    st.warning("⚠️ Aucune modification détectée")

        with col2:
            to_delete = df_edited[df_edited["🗑️"] == True]
            if len(to_delete) > 0:
                if st.button(f"🗑️ Supprimer ({len(to_delete)})", type="secondary", key="delete_v3"):
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    fichiers_supprimes = 0

                    for idx, row in to_delete.iterrows():
                        trans_id = row["id"]

                        # Récupérer la transaction complète avec la source
                        original_rows = df_edit[df_edit["id"] == trans_id]
                        if original_rows.empty:
                            continue
                        transaction = original_rows.iloc[0].to_dict()

                        # Supprimer les fichiers associés si source = OCR ou PDF
                        if transaction.get("source") in ["OCR", "PDF"]:
                            nb_supprimes = supprimer_fichiers_associes(transaction)
                            fichiers_supprimes += nb_supprimes

                        # Supprimer de la base de données
                        cursor.execute("DELETE FROM transactions WHERE id = ?", (trans_id,))

                    conn.commit()
                    conn.close()

                    message = f"{len(to_delete)} transaction(s) supprimée(s) !"
                    if fichiers_supprimes > 0:
                        message += f" ({fichiers_supprimes} fichier(s) supprimé(s))"
                    toast_success(message)
                    refresh_and_rerun()

    # === GÉRER LES RÉCURRENCES (EN EXPANDER) ===
    st.markdown("---")
    with st.expander("🔁 Gérer les récurrences"):
        from .recurrences import interface_gerer_recurrences
        interface_gerer_recurrences()
