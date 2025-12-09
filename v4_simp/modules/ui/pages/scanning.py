"""
Scanning Page Module

This module contains the ticket scanning interface using OCR.
"""

import os
import streamlit as st
from datetime import datetime
from typing import Optional
import logging
from config import TO_SCAN_DIR
from modules.database.connection import get_db_connection
from modules.ui.helpers import insert_transaction_batch
from modules.ui.toast_components import toast_success, toast_error, toast_warning
from modules.utils.converters import safe_convert, safe_date_convert
from modules.ocr.scanner import full_ocr
from modules.ocr.parsers import (
    parse_ticket_metadata, extract_text_from_pdf,
    move_ticket_to_sorted, move_ticket_to_problematic
)
from modules.ocr.logging import log_ocr_scan, determine_success_level, log_potential_patterns

logger = logging.getLogger(__name__)


def process_all_tickets_in_folder() -> None:
    """
    Process all tickets in the scanning folder using OCR.

    Features:
    - Auto-detect JPG, PNG, PDF files
    - OCR text extraction
    - Multi-method amount detection (patterns, payment keywords, HT+TVA, fallback)
    - Auto-category detection from filename
    - Manual correction before validation
    - File organization after processing
    - OCR performance logging

    Process:
    1. List all tickets in TO_SCAN_DIR
    2. For each ticket:
       - Extract text via OCR
       - Parse metadata (amount, date, keywords)
       - Deduce category/subcategory from filename
       - Present form for validation
       - On validation: insert transaction, move file, log OCR stats

    Returns:
        None
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
        potential_patterns = data.get("patterns_potentiels", [])
        is_reliable = data.get("fiable", True)

        # Log potential new patterns for future improvements
        if potential_patterns:
            log_potential_patterns(
                filename=ticket_file,
                potential_patterns=potential_patterns,
                montant_final=montant_final,
                methode_detection=methode_detection
            )

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

        # Warn if amount detected by fallback method (unreliable)
        if not is_reliable:
            st.warning(
                f"⚠️ **Montant peu fiable** : Détecté par méthode fallback ({methode_detection}). "
                "Veuillez vérifier et corriger le montant manuellement."
            )

        # Show potential new patterns if found
        if potential_patterns:
            with st.expander(f"🔍 Patterns potentiels détectés ({len(potential_patterns)})"):
                st.caption("Ces patterns pourraient être ajoutés au système de détection :")
                for p in potential_patterns[:5]:  # Show max 5
                    st.code(f"{p.get('pattern')} : {p.get('amount')} → {p.get('line')}")

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

            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                valider = st.form_submit_button("✅ Valider et enregistrer ce ticket", type="primary")
            with col_btn2:
                marquer_problematique = st.form_submit_button(
                    "⚠️ Marquer comme problématique",
                    help="Déplace le ticket dans le dossier des tickets problématiques pour traitement ultérieur"
                )

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

            # Déplacer le ticket avec renommage automatique
            # Extraire une description du nom de fichier original
            original_name = os.path.splitext(ticket_file)[0]
            description_from_file = original_name.split(".")[0] if "." in original_name else original_name
            
            move_ticket_to_sorted(
                ticket_path, 
                categorie, 
                sous_categorie,
                date_ticket=date_ticket.isoformat(),
                montant=montant_corrige,
                description=description_from_file
            )

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

        # Handle "Mark as problematic" button
        if marquer_problematique:
            print(f"\n[DEBUG] Marquage comme problématique pour {ticket_file}")
            print(f"   Méthode détection: {methode_detection}")
            print(f"   Montant détecté: {montant_final}")
            print(f"   Fiable: {is_reliable}\n")

            # Move ticket to problematic directory
            moved_path = move_ticket_to_problematic(
                ticket_path=ticket_path,
                montant_detecte=montant_final,
                methode_detection=methode_detection,
                potential_patterns=potential_patterns
            )

            toast_warning(
                f"📋 Ticket déplacé vers tickets problématiques : {os.path.basename(moved_path)}",
                duration=5000
            )
            st.info(
                "💡 Ce ticket sera disponible dans l'onglet de retraitement pour "
                "être traité ultérieurement avec de meilleurs patterns."
            )
