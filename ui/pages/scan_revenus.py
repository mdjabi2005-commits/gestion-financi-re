# -*- coding: utf-8 -*-
"""
Module scan_revenus - Partie de l'application gestiov4
Généré automatiquement par migrate_to_modular.py
"""

import streamlit as st
import os
from datetime import datetime, date
from ocr.parsers import parse_uber_pdf, parse_fiche_paie, parse_pdf_dispatcher
from services.uber_tax import process_uber_revenue
from core.database import get_db_connection
from ui.components import toast_success, toast_error, refresh_and_rerun


def interface_ajouter_revenu():
    st.subheader("💼 Ajouter un revenu V2")

    mode = st.selectbox(
        "Choisir le mode d'ajout du revenu :",
        ["Sélectionner...", "Scanner depuis le dossier", "Ajouter manuellement", "Revenu récurrent"]
    )

    if mode == "Scanner depuis le dossier":
        interface_process_all_revenues_in_folder()

    elif mode == "Ajouter manuellement":
        with st.form("ajouter_revenu_manuel", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                categorie = st.text_input("Catégorie principale (ex: Uber, Animation, Salaire)")
                sous_categorie = st.text_input("Sous-catégorie (ex: septembre, octobre, etc.)")
            with col2:
                montant = st.number_input("Montant (€)", min_value=0.0, format="%.2f", step=0.01)
                date_revenu = st.date_input("Date du revenu", date.today())

            submit_btn = st.form_submit_button("💾 Enregistrer le revenu")

        if submit_btn:
            if not categorie or montant <= 0:
                toast_error("Veuillez entrer une catégorie et un montant valide.")
                return

            transaction_data = {
                "type": "revenu",
                "categorie": categorie.strip(),
                "sous_categorie": sous_categorie.strip(),
                "montant": montant,
                "date": date_revenu.isoformat(),
                "source": "manuel"
            }
            
            # 🔥 V2: Traitement Uber automatique
            transaction_data, uber_msg = process_uber_revenue(transaction_data)
            if uber_msg:
                st.success(uber_msg)

            insert_transaction_batch([transaction_data])
            toast_success("Revenu manuel ajouté avec succès !")

    elif mode == "Revenu récurrent":
        with st.form("ajouter_revenu_recurrent", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                categorie = st.text_input("Catégorie principale (ex: Salaire, Bourse, CAF)")
                sous_categorie = st.text_input("Sous-catégorie (ex: septembre, octobre, etc.)")
                montant = st.number_input("Montant du revenu (€)", min_value=0.0, format="%.2f", step=0.01)
            with col2:
                recurrence = st.selectbox("Fréquence", ["mensuelle", "hebdomadaire", "annuelle"])
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
                {"type": "revenu", "categorie": safe_categorie, "sous_categorie": safe_sous_categorie,
                 "montant": montant, "date": date_debut.isoformat(), "source": "récurrente", "recurrence": recurrence,
                 "date_fin": date_fin.isoformat() if date_fin else ""}
            ] + [
                {"type": "revenu", "categorie": safe_categorie, "sous_categorie": safe_sous_categorie,
                 "montant": montant, "date": d.isoformat(), "source": "récurrente_auto", "recurrence": recurrence}
                for d in occurrences
            ]
            
            # 🔥 V2: Traitement Uber pour tous les revenus récurrents
            processed_transactions = []
            for transaction in transactions:
                if transaction["type"] == "revenu":
                    processed_transaction, uber_msg = process_uber_revenue(transaction)
                    if uber_msg and transaction is transactions[0]:  # Afficher seulement pour le modèle
                        st.success(uber_msg)
                    processed_transactions.append(processed_transaction)
                else:
                    processed_transactions.append(transaction)
            
            insert_transaction_batch(processed_transactions)
            toast_success(f"Revenu récurrent ({recurrence}) ajouté avec succès.")
            st.info(f"{len(occurrences)} versement(s) passé(s) ajouté(s).")


def interface_process_all_revenues_in_folder():
    st.subheader("📥 Scanner et enregistrer tous les revenus depuis le dossier V2")

    src_folder = REVENUS_A_TRAITER 

    if "revenus_data" not in st.session_state:
        st.session_state["revenus_data"] = []

    if st.button("🚀 Scanner tous les revenus") and not st.session_state["revenus_data"]:
        pdfs = [os.path.join(root, f)
                for root, _, files in os.walk(src_folder)
                for f in files if f.lower().endswith(".pdf")]

        if not pdfs:
            toast_warning("Aucun PDF de revenu trouvé dans le dossier.")
            return

        data_list = []
        for pdf_path in pdfs:
            parent_folder = os.path.basename(os.path.dirname(pdf_path))

            if parent_folder.lower() in ["revenus_a_traiter", "revenus_traité", "revenus_traités"]:
                sous_dossier = "Revenus"
            else:
                sous_dossier = parent_folder

            try:
                if sous_dossier.lower() == "uber":
                    parsed = parse_uber_pdf(pdf_path)
                    # 🔥 V2: Uber tax already applied in parse_uber_pdf
                    toast_success("Uber PDF traité: {parsed.get('montant_brut', 0):.2f}€ → {parsed['montant']:.2f}€ net")
                else:
                    parsed = parse_fiche_paie(pdf_path)
            except Exception as e:
                logger.error(f"PDF parsing failed for {pdf_path}: {e}")
                parsed = {"montant": 0.0, "date": datetime.today().date(), "source": "PDF Auto"}

            date_val = parsed.get("date", datetime.today().date())
            if isinstance(date_val, str):
                date_val = safe_date_convert(date_val)
            mois_nom = numero_to_mois(f"{date_val.month:02d}")

            data_list.append({
                "file": os.path.basename(pdf_path),
                "path": pdf_path,
                "categorie": sous_dossier,
                "sous_categorie": mois_nom,
                "montant": parsed.get("montant", 0.0),
                "montant_initial": parsed.get("montant", 0.0),  # Sauvegarder le montant détecté par OCR
                "date": date_val,
                "source":"PDF"
            })

        st.session_state["revenus_data"] = data_list
        toast_success("Revenus scannés avec succès. Tu peux maintenant les modifier avant validation.")

    if st.session_state.get("revenus_data"):
        updated_list = []
        for idx, data in enumerate(st.session_state["revenus_data"]):
            st.markdown("---")
            st.write(f"📄 {data['file']}")
            col1, col2 = st.columns(2)
            with col1:
                cat = st.text_input(f"Catégorie ({data['file']})", value=data["categorie"], key=f"rev_cat_{idx}")
                souscat = st.text_input(f"Sous-catégorie ({data['file']})", value=data["sous_categorie"], key=f"rev_souscat_{idx}")
            with col2:
                montant_str = f"{data['montant']:.2f}" if data["montant"] else ""
                montant_edit = st.text_input(f"Montant (€) ({data['file']})", value=montant_str, key=f"rev_montant_{idx}")
                date_edit = st.date_input(f"Date ({data['file']})", value=data["date"], key=f"rev_date_{idx}")

            montant_val = safe_convert(montant_edit)

            updated_list.append({
                "file": data["file"],
                "path": data["path"],
                "categorie": cat.strip(),
                "sous_categorie": souscat.strip(),
                "montant": montant_val,
                "montant_initial": data.get("montant_initial", montant_val),  # Conserver le montant OCR initial
                "date": date_edit,
                "source": data["source"]
            })

        st.session_state["revenus_data"] = updated_list

        st.markdown("---")
        toast_warning("Vérifie bien les informations avant de confirmer l'enregistrement.")

        if st.button("✅ Confirmer et enregistrer tous les revenus"):
            conn = get_db_connection()
            cursor = conn.cursor()

            for data in st.session_state["revenus_data"]:
                # 🔥 V2: Application Uber tax si nécessaire
                transaction_data = {
                    "type": "revenu",
                    "categorie": data["categorie"],
                    "sous_categorie": data["sous_categorie"],
                    "montant": data["montant"],
                    "date": data["date"].isoformat(),
                    "source": data["source"]
                }

                # Traitement Uber
                transaction_data, uber_msg = process_uber_revenue(transaction_data)
                if uber_msg:
                    toast_success("{uber_msg}")

                cursor.execute("""
                    INSERT INTO transactions (type, categorie, sous_categorie, montant, date, source)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    "revenu",
                    transaction_data["categorie"],
                    transaction_data["sous_categorie"],
                    transaction_data["montant"],
                    transaction_data["date"],
                    transaction_data["source"]
                ))

                target_dir = os.path.join(REVENUS_TRAITES, data["categorie"], data["sous_categorie"])
                os.makedirs(target_dir, exist_ok=True)

                shutil.move(data["path"], os.path.join(target_dir, data["file"]))

                # === ENREGISTRER LES STATISTIQUES OCR ===
                # Comparer le montant initial (OCR) avec le montant final (choisi par l'utilisateur)
                montant_initial = data.get("montant_initial", data["montant"])
                montant_final = data["montant"]

                # Déterminer le niveau de succès
                success_level = determine_success_level([montant_initial], montant_final)

                # Patterns pour les revenus (basiques, on peut enrichir plus tard)
                patterns_detectes = []
                if data["categorie"].lower() == "uber":
                    patterns_detectes = ["uber", "revenu", "pdf"]
                else:
                    patterns_detectes = ["salaire", "revenu", "pdf"]

                # Enregistrer le scan
                log_ocr_scan(
                    document_type="revenu",
                    filename=data["file"],
                    montants_detectes=[montant_initial],
                    montant_choisi=montant_final,
                    categorie=data["categorie"],
                    sous_categorie=data["sous_categorie"],
                    patterns_detectes=patterns_detectes,
                    success_level=success_level
                )

            conn.commit()
            conn.close()
            toast_success("Tous les revenus ont été enregistrés et rangés avec succès !")
            st.session_state.pop("revenus_data")


