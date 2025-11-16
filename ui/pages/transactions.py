# -*- coding: utf-8 -*-
"""
Module transactions - Partie de l'application gestiov4
Généré automatiquement par migrate_to_modular.py
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
from core.transactions import load_transactions
from core.database import get_db_connection
from ui.components import afficher_carte_transaction, toast_success, toast_error, refresh_and_rerun


def interface_transactions_unifiee():
    st.subheader("📊 Gestion des transactions (manuel + CSV) V2")

    os.makedirs("data", exist_ok=True)
    if not os.path.exists(TRANSACTIONS_CSV):
        pd.DataFrame(columns=COLUMNS).to_csv(TRANSACTIONS_CSV, index=False, encoding="utf-8")
        st.info("🆕 Fichier `transactions.csv` créé automatiquement.")

    try:
        df_base = pd.read_csv(TRANSACTIONS_CSV, encoding="utf-8")
    except UnicodeDecodeError:
        df_base = pd.read_csv(TRANSACTIONS_CSV, encoding="ISO-8859-1")

    conn = get_db_connection()
    df_sqlite = pd.read_sql_query("""
        SELECT date, categorie, sous_categorie, description, montant, type, source, recurrence
        FROM transactions
    """, conn)
    conn.close()

    st.markdown("#### 📥 Importer un ou plusieurs fichiers CSV de transactions")
    st.info("Les colonnes doivent être écrites sous ce format : `date`, `categorie`, `sous_categorie`, `description`, `montant`, `type`")
    st.info("💡 La colonne `description` peut être vide.")

    uploaded_files = st.file_uploader(
        "Glissez un ou plusieurs fichiers CSV ici",
        type=["csv"],
        accept_multiple_files=True
    )

    all_new_rows = []

    if uploaded_files:
        for uploaded in uploaded_files:
            raw_data = uploaded.read()
            encoding = detect(raw_data)["encoding"] or "utf-8"
            uploaded.seek(0)

            try:
                df_new = pd.read_csv(uploaded, encoding=encoding)
                if "date" in df_new.columns:
                    df_new["date"] = df_new["date"].apply(normaliser_date)
                if "montant" in df_new.columns:
                    df_new["montant"] = df_new["montant"].apply(nettoyer_montant)
            except Exception as e:
                logger.error(f"CSV import failed for {uploaded.name}: {e}")
                toast_error("Erreur lors de la lecture de {uploaded.name} : {e}")
                continue

            required_cols = ["date", "categorie", "sous_categorie", "description", "montant"]
            missing = [c for c in required_cols if c not in df_new.columns]
            if missing:
                toast_error("{uploaded.name} : colonnes manquantes ({', '.join(missing)})")
                st.error("Vérifiez bien l'orthographe des colonnes.")
                toast_error("Les transaction n'ont pas pu être ajoutée. Vérifiez bien le format du csv",10000)
                continue

            all_new_rows.append(df_new)
            toast_success("{uploaded.name} importé avec succès ({len(df_new)} lignes).")

        if all_new_rows:
            df_new_total = pd.concat(all_new_rows, ignore_index=True)

            for df in [df_base, df_new_total, df_sqlite]:
                for col in ["categorie", "sous_categorie", "description"]:
                    if col in df.columns:
                        df[col] = df[col].fillna("").astype(str).str.strip().str.lower()

            for df in [df_new_total, df_sqlite]:
                if "montant" in df.columns:
                    df["montant"] = df["montant"].apply(lambda x: safe_convert(x, float, 0.0))

            df_new_total = df_new_total.drop_duplicates(
                subset=["date", "montant", "categorie", "sous_categorie", "description"],
                keep="first"
            )

            df_combined = pd.concat([df_base, df_new_total], ignore_index=True)

            duplicates_internal = df_combined.duplicated(
                subset=["date", "montant", "categorie", "sous_categorie", "description"],
                keep=False
            )
            df_dupes_internal = df_combined[duplicates_internal]

            df_merged = df_new_total.merge(
                df_sqlite,
                on=["date", "montant", "categorie", "sous_categorie", "description"],
                how="left",
                indicator=True
            )
            df_dupes_sqlite = df_merged[df_merged["_merge"] != "left_only"]

            df_new_clean = df_merged[df_merged["_merge"] == "left_only"].drop(columns=["_merge"])

            if not df_dupes_internal.empty or not df_dupes_sqlite.empty:
                toast_warning("Doublons détectés :")
                if not df_dupes_internal.empty:
                    st.caption("🔁 Dans les fichiers importés / CSV local :")
                    st.dataframe(df_dupes_internal)
                if not df_dupes_sqlite.empty:
                    st.caption("🗄️ Déjà présents dans la base SQLite :")
                    st.dataframe(df_dupes_sqlite)

                keep_dupes = st.radio(
                    "Souhaitez-vous quand même conserver les doublons internes ?",
                    ["Non", "Oui"],
                    horizontal=True,
                    key="keep_dupes_choice"
                )
            else:
                keep_dupes = "Non"

            if keep_dupes == "Non":
                df_final = df_combined.drop_duplicates(
                    subset=["date", "montant", "categorie", "sous_categorie", "description"],
                    keep="first"
                )
            else:
                df_final = df_combined

            df_final.to_csv(TRANSACTIONS_CSV, index=False, encoding="utf-8")

            if not df_new_clean.empty:
                if "type" not in df_new_clean.columns:
                    toast_warning("Colonne 'type' absente — les lignes seront marquées comme 'dépense'.")
                    df_new_clean["type"] = "dépense"

                transactions_to_insert = []
                for _, row in df_new_clean.iterrows():
                    transaction = {
                        "type": str(row.get("type", "dépense")).strip().lower(),
                        "categorie": str(row["categorie"]).strip().lower(),
                        "sous_categorie": str(row.get("sous_categorie", "")).strip().lower(),
                        "description": str(row.get("description", "")).strip(),
                        "montant": safe_convert(row["montant"]),
                        "date": row["date"],
                        "source": "import_csv"
                    }
                    
                    # 🔥 V2: Traitement Uber pour les revenus
                    if transaction["type"] == "revenu":
                        transaction, uber_msg = process_uber_revenue(transaction)
                        if uber_msg:
                            toast_success("{uber_msg}")
                    
                    transactions_to_insert.append(transaction)

                insert_transaction_batch(transactions_to_insert)
                toast_success(f"{len(df_new_clean)} transaction(s) importée(s)")
                toast_success("Pensez à bien actualiser la page", 5000)
            else:
                st.info("ℹ️ Aucune nouvelle transaction à insérer (toutes déjà présentes).")

    st.markdown("---")
    st.markdown("#### ✍️ Ajouter manuellement une transaction")

    with st.form("add_manual"):
        col1, col2, col3 = st.columns(3)
        with col1:
            date_tr = st.date_input("Date", value=date.today())
            type_tr = st.selectbox("Type", ["dépense", "revenu"])
        with col2:
            cat = st.text_input("Catégorie principale")
            sous_cat = st.text_input("Sous-catégorie")
        with col3:
            montant = st.number_input("Montant (€)", min_value=0.0, step=0.01, format="%.2f")
            desc = st.text_input("Description")

        valider = st.form_submit_button("💾 Ajouter la transaction")

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
            
            # 🔥 V2: Traitement Uber pour les revenus
            if type_tr == "revenu":
                transaction_data, uber_msg = process_uber_revenue(transaction_data)
                if uber_msg:
                    st.success(uber_msg)

            new_line = pd.DataFrame([transaction_data])

            df_updated = pd.concat([df_base, new_line], ignore_index=True).drop_duplicates(
                subset=["date", "montant", "categorie", "sous_categorie", "description"],
                keep="first"
            ).reset_index(drop=True)

            df_updated.to_csv(TRANSACTIONS_CSV, index=False, encoding="utf-8")

            insert_transaction_batch([transaction_data])

            toast_success(f"Transaction ajoutée : {cat} — {transaction_data['montant']:.2f} €")
            toast_success("Pense à bien rafraichir la page")

    df_latest = pd.read_csv(TRANSACTIONS_CSV, encoding="utf-8")
    csv_buf = BytesIO()
    csv_buf.write(df_latest.to_csv(index=False).encode("utf-8"))

    st.download_button(
        label="⬇️ Télécharger le fichier CSV complet",
        data=csv_buf.getvalue(),
        file_name="transactions.csv",
        mime="text/csv"
    )


def interface_voir_transactions_v3():
    """Interface unifiée : Voir ET gérer les transactions (simplifiée)"""
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

                # 📎 Afficher les documents associés si OCR ou PDF
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

                    # DEBUG : Afficher quelques exemples de comparaison
                    with st.expander("🔍 DEBUG : Pourquoi aucun changement ?"):
                        st.write("**Comparaison de la première ligne :**")
                        if len(df_edited) > 0:
                            idx = df_edited.index[0]
                            orig = df_edit.loc[idx]
                            edit = df_edited.loc[idx]

                            st.write("**Original (df_edit) :**")
                            st.json({
                                "date": str(orig["date"]),
                                "type": str(orig.get("type")),
                                "categorie": str(orig.get("categorie")),
                                "sous_categorie": str(orig.get("sous_categorie")),
                                "montant": str(orig.get("montant")),
                                "description": str(orig.get("description"))
                            })

                            st.write("**Édité (df_edited) :**")
                            st.json({
                                "date": str(edit["date"]),
                                "type": str(edit.get("type")),
                                "categorie": str(edit.get("categorie")),
                                "sous_categorie": str(edit.get("sous_categorie")),
                                "montant": str(edit.get("montant")),
                                "description": str(edit.get("description"))
                            })

                            st.write("**Les DataFrames sont-ils identiques ?**")
                            st.write(f"Date égale: {str(orig['date']) == str(edit['date'])}")
                            st.write(f"Type égal: {str(orig.get('type')) == str(edit.get('type'))}")
                            st.write(f"Catégorie égale: {str(orig.get('categorie')) == str(edit.get('categorie'))}")
                            st.write(f"Montant égal: {str(orig.get('montant')) == str(edit.get('montant'))}")

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
        interface_gerer_recurrences()


def interface_transactions_simplifiee():
    """Interface simplifiée pour ajouter des transactions (sans sous-onglets)"""
    st.title("💸 Ajouter une Transaction")

    # Menu de sélection principal
    col1, col2 = st.columns([3, 1])

    with col1:
        type_action = st.selectbox(
            "Que voulez-vous faire ?",
            [
                "📸 Scanner un ticket (OCR)",
                "💸 Ajouter des dépenses",
                "🔁 Créer une transaction récurrente",
                "💰 Ajouter un revenu"
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
            st.markdown("""
            ### Mode d'emploi :
            1. **Nommer votre ticket** avec le format : `nom.categorie.sous_categorie.extension`
               - Exemple : `carrefour.alimentation.courses.jpg`
               - Exemple : `shell.transport.essence.jpg`
            2. **Déposer le fichier** dans le dossier : `{}`
            3. **Cliquer sur "Scanner"** ci-dessous
            4. **Vérifier et valider** les informations détectées

            **Formats acceptés :** JPG, PNG, PDF
            """.format(TO_SCAN_DIR))

        process_all_tickets_in_folder()

    # === AJOUTER DES DÉPENSES (MANUEL + CSV) ===
    elif type_action == "💸 Ajouter des dépenses":
        interface_ajouter_depenses_fusionnee()

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

        interface_transaction_recurrente(type_transaction=type_val)

    # === REVENU (NON-RÉCURRENT) ===
    elif type_action == "💰 Ajouter un revenu":
        st.subheader("💰 Ajouter un revenu")

        interface_ajouter_revenu()


