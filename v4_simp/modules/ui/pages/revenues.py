"""
Revenues Page Module

This module contains all revenue-related interface functions including:
- Add revenue interface (manual, scan folder, recurring)
- Process all revenues from folder
"""

import os
import shutil
import streamlit as st
import re
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from typing import Optional, Dict, Any
import logging
from config import REVENUS_A_TRAITER, REVENUS_TRAITES
from modules.database.connection import get_db_connection
from modules.ui.helpers import insert_transaction_batch
from modules.ui.toast_components import toast_success, toast_error, toast_warning
from modules.utils.converters import safe_convert, safe_date_convert
from modules.services.revenue_service import is_uber_transaction, process_uber_revenue
from modules.services.normalization import normalize_category, normalize_subcategory
from modules.ocr.parsers import parse_uber_pdf, parse_fiche_paie
from modules.utils.formatters import numero_to_mois
from modules.ocr.logging import log_ocr_scan, determine_success_level

logger = logging.getLogger(__name__)


def interface_process_all_revenues_in_folder() -> None:
    """
    Scan and register all revenues from the revenue folder.

    Features:
    - Auto-detection from PDF files
    - Uber PDF special parsing
    - Paystub OCR parsing
    - Manual correction before validation
    - File organization after processing
    - OCR performance logging

    Process:
    1. Scan all PDFs in REVENUS_A_TRAITER folder
    2. Parse each PDF (Uber or standard paystub)
    3. Allow user to review and edit detected data
    4. Insert into database on confirmation
    5. Move files to REVENUS_TRAITES folder

    Returns:
        None
    """
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
                    # Uber tax already applied in parse_uber_pdf
                    toast_success(f"Uber PDF traité: {parsed.get('montant_brut', 0):.2f}€ → {parsed['montant']:.2f}€ net")
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
                "source":"PDF",
                "preview_text": parsed.get("preview_text", "")  # NEW: Store preview text
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
            
            # NEW: Show preview text if available
            if data.get("preview_text"):
                with st.expander("📄 Aperçu du texte extrait (PDF)"):
                    st.text_area("Texte du PDF:", value=data["preview_text"], height=150, key=f"rev_preview_{idx}", disabled=True)

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

        # Check if any Uber revenues detected
        has_uber = any(is_uber_transaction(data["categorie"], "") for data in st.session_state["revenus_data"])

        if has_uber:
            st.warning("🚗 **Revenus Uber détectés !**")
            apply_uber_tax = st.checkbox(
                "✅ Appliquer la taxe Uber (21%) sur tous les revenus Uber ?",
                value=True,
                key="apply_uber_tax_batch",
                help="Si coché, applique automatiquement le prélèvement de 21% sur les revenus Uber. ⚠️ Ne pas ajouter les dépenses URSSAF séparément."
            )
        else:
            apply_uber_tax = False

        toast_warning("Vérifie bien les informations avant de confirmer l'enregistrement.")

        if st.button("✅ Confirmer et enregistrer tous les revenus"):
            conn = get_db_connection()
            cursor = conn.cursor()

            for data in st.session_state["revenus_data"]:
                # Application Uber tax si nécessaire
                transaction_data = {
                    "type": "revenu",
                    "categorie": data["categorie"],
                    "sous_categorie": data["sous_categorie"],
                    "montant": data["montant"],
                    "date": data["date"].isoformat(),
                    "source": data["source"]
                }

                # Traitement Uber avec confirmation
                transaction_data, uber_msg = process_uber_revenue(transaction_data, apply_tax=apply_uber_tax)
                if uber_msg:
                    toast_success(f"{uber_msg}")

                cursor.execute("""
                    INSERT INTO transactions (type, categorie, sous_categorie, montant, date, source)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    "revenu",
                    normalize_category(transaction_data["categorie"]),
                    normalize_subcategory(transaction_data["sous_categorie"]),
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
