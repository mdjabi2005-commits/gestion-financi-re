# -*- coding: utf-8 -*-
"""
Module engine - Partie de l'application gestiov4
Généré automatiquement par migrate_to_modular.py
"""

import pytesseract
from PIL import Image
import cv2
import numpy as np
import re
import PyPDF2


from config import BASE_DIR, DATA_DIR, DB_PATH, TO_SCAN_DIR, SORTED_DIR, REVENUS_A_TRAITER, REVENUS_TRAITES
# Créer les dossiers de logs OCR
OCR_LOGS_DIR = os.path.join(DATA_DIR, "ocr_logs")
os.makedirs(OCR_LOGS_DIR, exist_ok=True)
LOG_PATH = os.path.join(OCR_LOGS_DIR, "pattern_log.json")
OCR_PERFORMANCE_LOG = os.path.join(OCR_LOGS_DIR, "performance_stats.json")
PATTERN_STATS_LOG = os.path.join(OCR_LOGS_DIR, "pattern_stats.json")
OCR_SCAN_LOG = os.path.join(OCR_LOGS_DIR, "scan_history.jsonl")
# === JOURNAL OCR ===

def full_ocr(image_path: str, show_ticket: bool = False) -> str:
    """
    Effectue un OCR complet sur une image de ticket.
    Version robuste + option d'affichage du ticket dans Streamlit.
    """
    try:
        # --- Lecture robuste du fichier image ---
        image_data = np.fromfile(image_path, dtype=np.uint8)
        image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)

        if image is None:
            raise FileNotFoundError(f"Impossible de lire ou décoder l'image : {image_path}")

        # --- Prétraitement pour OCR ---
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (3, 3), 0)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        pil_img = Image.fromarray(thresh)

        # --- OCR MULTI-LANGUES (français + anglais) ---
        # Utilise fra+eng pour mieux reconnaître TOTAL, PAYMENT, AMOUNT, etc.
        text = pytesseract.image_to_string(pil_img, lang="fra+eng")
        text = text.replace("\x0c", "").strip()
        
        # Log les langues détectées pour statistiques
        if text:
            log_pattern_occurrence("ocr_success_fra+eng")

        # --- Option : affichage dans Streamlit ---
        if show_ticket:
            with st.expander(f"🧾 Aperçu du ticket : {os.path.basename(image_path)}", expanded=False):
                st.image(cv2.cvtColor(image, cv2.COLOR_BGR2RGB), caption=os.path.basename(image_path))
                if text:
                    st.text_area("Texte OCR détecté :", text, height=200)
                else:
                    toast_warning("Aucun texte détecté par l'OCR.")

        return text

    except Exception as e:
        logger.error(f"OCR error on {image_path}: {e}")
        toast_error("Erreur OCR sur {os.path.basename(image_path)} : {e}")
        show_toast(f"Erreur OCR: {os.path.basename(image_path)}", toast_type="error")
        return ""


def extract_text_from_pdf(pdf_path):
    """Lit un PDF et renvoie le texte brut."""
    from pdfminer.high_level import extract_text
    try:
        return extract_text(pdf_path)
    except Exception as e:
        logger.warning(f"Impossible de lire le PDF {pdf_path} ({e})")
        toast_warning("Impossible de lire le PDF {pdf_path} ({e})")
        return ""


def nettoyer_montant(montant_str):
    """
    Nettoie et convertit un montant en float
    Gère les virgules, espaces, symboles monétaires
    """
    return safe_convert(montant_str, float, 0.0)

# 🔥 FONCTIONS UTILITAIRES AMÉLIORÉES


