# -*- coding: utf-8 -*-
"""
Module scan_tickets - Partie de l'application gestiov4
Généré automatiquement par migrate_to_modular.py
"""

import streamlit as st
import os
import pandas as pd
import logging
from PIL import Image
from datetime import datetime, date
from ocr.engine import full_ocr, extract_text_from_pdf
from ocr.parsers import parse_ticket_metadata
from ocr.logging import log_ocr_scan
from services.file_manager import move_ticket_to_sorted
from core.database import get_db_connection
from core.transactions import insert_transaction_batch, load_transactions
from utils.converters import safe_convert, safe_date_convert
from ui.components import toast_success, toast_error, toast_warning, refresh_and_rerun
from config import TO_SCAN_DIR

logger = logging.getLogger(__name__)


def interface_ajouter_depenses_fusionnee():
    """Interface fusionnée pour ajouter des dépenses : manuel ou import CSV"""
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

                # 🔥 V2: Traitement Uber pour les revenus
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
                import io
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


def process_all_tickets_in_folder():
    """
    Traite tous les tickets du dossier TO_SCAN_DIR :
    - OCR
    - extraction montants / date / infos clés
    - confirmation utilisateur
    - insertion en base + déplacement
    Version V2 avec conversions sécurisées.
    """
    print("\n" + "="*60)
    print("[DEBUG] FONCTION process_all_tickets_in_folder APPELEE")
    print("="*60 + "\n")

    st.subheader("🧾 Traitement des tickets à scanner V2")

    tickets = [f for f in os.listdir(TO_SCAN_DIR) if f.lower().endswith((".jpg", ".png", ".jpeg", ".pdf"))]

    print(f"[DEBUG] TO_SCAN_DIR : {TO_SCAN_DIR}")
    print(f"[DEBUG] Tickets trouves : {len(tickets)}")
    for t in tickets:
        print(f"  - {t}")
    print()

    if not tickets:
        st.info("📂 Aucun ticket à scanner pour le moment.")
        return

    st.write(f"🧮 {len(tickets)} ticket(s) détecté(s) dans le dossier à scanner.")

    for ticket_file in tickets:
        ticket_path = os.path.join(TO_SCAN_DIR, ticket_file)
        st.markdown("---")
        st.markdown(f"### 🧾 {ticket_file}")

        # --- OCR selon format ---
        try:
            if ticket_file.lower().endswith(".pdf"):
                text = extract_text_from_pdf(ticket_path)
                with st.expander(f"📄 Texte OCR extrait du PDF : {ticket_file}", expanded=False):
                    st.text_area("Contenu OCR :", text, height=200)
            else:
                text = full_ocr(ticket_path, show_ticket=True)
        except Exception as e:
            logger.error(f"OCR failed for {ticket_file}: {e}")
            toast_error(f"Erreur OCR sur {ticket_file} : {e}", 5000)
            continue

        # --- Analyse du texte OCR ---
        data = parse_ticket_metadata(text)

        montant_final = data.get("montant", 0.0)
        montants_possibles = data.get("montants_possibles", [montant_final])
        detected_date = data.get("date", datetime.now().date().isoformat())
        key_info = data.get("infos", "")
        methode_detection = data.get("methode_detection", "UNKNOWN")
        debug_info = data.get("debug_info", {})

        # Afficher la méthode de détection
        print(f"\n[OCR-DETECTION] Ticket: {ticket_file}")
        print(f"[OCR-DETECTION] Methode utilisee: {methode_detection}")
        print(f"[OCR-DETECTION] Montant final: {montant_final}€")
        print(f"[OCR-DETECTION] Candidats methode A (patterns): {debug_info.get('methode_A', [])}")
        print(f"[OCR-DETECTION] Patterns A trouves: {debug_info.get('patterns_A', [])}")
        print(f"[OCR-DETECTION] Candidat methode B (paiements): {debug_info.get('methode_B', 0)}€")
        print(f"[OCR-DETECTION] Candidat methode C (HT+TVA): {debug_info.get('methode_C', 0)}€")
        print(f"[OCR-DETECTION] Candidat methode D (fallback): {debug_info.get('methode_D', 0)}€\n")

        # --- Déduction de la catégorie et sous-catégorie à partir du nom de fichier ---
        name = os.path.splitext(ticket_file)[0]
        parts = name.split(".")[1:]

        if len(parts) >= 2:
            categorie_auto = parts[1].capitalize()
            sous_categorie_auto = parts[0].capitalize()
        elif len(parts) == 1:
            categorie_auto = parts[0].capitalize()
            sous_categorie_auto = "Autre"
        else:
            categorie_auto = "Divers"
            sous_categorie_auto = "Autre"

        st.markdown(f"🧠 **Catégorie auto-détectée :** {categorie_auto} → {sous_categorie_auto}")

        with st.expander("📜 Aperçu OCR (lignes clés)"):
            st.text(key_info)

        with st.form(f"form_{ticket_file}"):
            col1, col2 = st.columns(2)
            with col1:
                categorie = st.text_input("Catégorie principale", categorie_auto)
                sous_categorie = st.text_input("Sous-catégorie (ex: supermarché, restaurant...)", sous_categorie_auto)
            with col2:
                montant_select = st.selectbox(
                    "Montant détecté",
                    options=[round(m, 2) for m in montants_possibles],
                    index=0 if montants_possibles else 0
                )
                montant_corrige = st.number_input(
                    "💶 Corriger le montant si besoin (€)",
                    value=float(montant_select) if montant_select else 0.0,
                    min_value=0.0,
                    step=0.01
                )
                date_ticket = st.date_input("📅 Date du ticket", safe_date_convert(detected_date))

            valider = st.form_submit_button("✅ Valider et enregistrer ce ticket")

        if valider:
            print(f"\n[DEBUG] FORMULAIRE VALIDE pour {ticket_file}")
            print(f"   Categorie: {categorie}")
            print(f"   Montant: {montant_corrige}")
            print(f"   Montants possibles: {montants_possibles}\n")

            if not categorie or montant_corrige <= 0:
                print(f"[DEBUG] VALIDATION ECHOUEE : categorie='{categorie}', montant={montant_corrige}")
                toast_error("Catégorie ou montant invalide")
                continue

            print("[DEBUG] Validation OK, insertion transaction...")
            # Insérer la transaction
            insert_transaction_batch([{
                "type": "dépense",
                "categorie": categorie.strip(),
                "sous_categorie": sous_categorie.strip(),
                "montant": safe_convert(montant_corrige),
                "date": date_ticket.isoformat(),
                "source": "OCR"
            }])

            # Déplacer le ticket
            move_ticket_to_sorted(ticket_path, categorie, sous_categorie)

            # === ENREGISTRER LES STATISTIQUES OCR ===
            # Déterminer le niveau de succès
            success_level = determine_success_level(montants_possibles, montant_corrige)

            # Extraire les patterns détectés du texte OCR
            patterns_detectes = []
            text_lower = text.lower()
            ticket_patterns = ['total', 'montant', 'ttc', 'cb', 'carte', 'espèces', 'esp']
            for pattern in ticket_patterns:
                if pattern in text_lower:
                    patterns_detectes.append(pattern)

            # Enregistrer le scan avec toutes les infos
            log_ocr_scan(
                document_type="ticket",
                filename=ticket_file,
                montants_detectes=montants_possibles,
                montant_choisi=montant_corrige,
                categorie=categorie.strip(),
                sous_categorie=sous_categorie.strip(),
                patterns_detectes=patterns_detectes,
                success_level=success_level,
                methode_detection=methode_detection
            )

            # Afficher un message selon le niveau de succès avec la méthode de détection
            methode_msg = {
                "A-PATTERNS": "via patterns (TOTAL/TTC/MONTANT)",
                "B-PAIEMENT": "via CB/CARTE/ESPECES",
                "C-HT+TVA": "via calcul HT+TVA",
                "D-FALLBACK": "via fallback (plus grand montant)",
                "A-PATTERNS+D-FALLBACK": "via patterns + fallback"
            }.get(methode_detection, f"méthode {methode_detection}")

            if success_level == "exact":
                toast_success(f"Ticket enregistré : {montant_corrige:.2f} € (détecté {methode_msg})")
            elif success_level == "partial":
                toast_warning(f"Ticket enregistré : {montant_corrige:.2f} € (montant dans la liste, {methode_msg})")
            else:
                toast_warning(f"Ticket enregistré : {montant_corrige:.2f} € (corrigé manuellement, détection {methode_msg})", 4000)


