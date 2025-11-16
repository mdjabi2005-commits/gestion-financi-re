# -*- coding: utf-8 -*-
"""
Module parsers - Partie de l'application gestiov4
Généré automatiquement par migrate_to_modular.py
"""

import os
import re
import logging
from datetime import datetime
from ocr.engine import extract_text_from_pdf
from utils.converters import safe_convert
from config import BASE_DIR, DATA_DIR, DB_PATH, TO_SCAN_DIR, SORTED_DIR, REVENUS_A_TRAITER, REVENUS_TRAITES

logger = logging.getLogger(__name__)

# Créer les dossiers de logs OCR (configuration commune)
OCR_LOGS_DIR = os.path.join(DATA_DIR, "ocr_logs")
os.makedirs(OCR_LOGS_DIR, exist_ok=True)
LOG_PATH = os.path.join(OCR_LOGS_DIR, "pattern_log.json")
OCR_PERFORMANCE_LOG = os.path.join(OCR_LOGS_DIR, "performance_stats.json")
PATTERN_STATS_LOG = os.path.join(OCR_LOGS_DIR, "pattern_stats.json")
OCR_SCAN_LOG = os.path.join(OCR_LOGS_DIR, "scan_history.jsonl")

def parse_ticket_metadata(ocr_text: str):
    """
    Analyse un texte OCR de ticket pour extraire les montants (total, paiements, TVA),
    et choisit le montant final par validation croisée.
    Version V2 avec conversions sécurisées.
    """
    lines = [l.strip() for l in ocr_text.split("\n") if l.strip()]

    def normalize_line(l):
        return l.replace("O", "0").replace("o", "0").replace("I", "1").replace("l", "1").strip()

    lines = [normalize_line(l) for l in lines]

    montant_regex = r"(\d{1,5}[.,]\d{1,2})"

    # === MÉTHODE A : Totaux directs (comme avant)
    total_patterns = [
        r"TOTAL\s*TTC",
        r"TOTAL\s*(A\s*PAYER)?",
        r"MONTANT\s*(R[EÉ][EÉ][LI]|R[EÉ][LI][LI]|TTC)?",  # REEL, RÉEL, RELL, RFEI, etc.
        r"NET\s*A\s*PAYER",
        r"À\s*PAYER",
        r"TOTAL$",
        r"TTC",
        r"MONTANT\s*EUR",  # Variante Leclerc
    ]
    montants_A = []
    patterns_A_matches = []
    for pattern in total_patterns:
        montant, matched = get_montant_from_line(pattern, lines)
        if matched and montant > 0:  # Ne compter que si le pattern a VRAIMENT matché
            montants_A.append(round(montant, 2))
            patterns_A_matches.append(pattern)

    # === MÉTHODE B : Somme des paiements (CB, espèces, web, etc.)
    paiement_patterns = [r"CB", r"CARTE", r"ESPECES", r"WEB", r"PAYPAL", r"CHEQUE"]
    montants_B = []
    for l in lines:
        if any(re.search(p, l, re.IGNORECASE) for p in paiement_patterns):
            found = re.findall(montant_regex, l)
            for val in found:
                montants_B.append(safe_convert(val))
    somme_B = round(sum(montants_B), 2) if montants_B else 0.0

    # === MÉTHODE C : Net + TVA
    net_lines = [l for l in lines if re.search(r"HT|NET", l, re.IGNORECASE)]
    tva_lines = [l for l in lines if re.search(r"TVA|T\.V\.A", l, re.IGNORECASE)]
    total_HT = 0.0
    total_TVA = 0.0
    for l in net_lines:
        vals = re.findall(montant_regex, l)
        for v in vals:
            total_HT += safe_convert(v)
    for l in tva_lines:
        vals = re.findall(montant_regex, l)
        for v in vals:
            total_TVA += safe_convert(v)
    somme_C = round(total_HT + total_TVA, 2) if total_HT > 0 else 0.0

    # === MÉTHODE D : fallback global (si rien trouvé)
    all_amounts = [safe_convert(m) for m in re.findall(montant_regex, ocr_text)]
    montant_fallback = max(all_amounts) if all_amounts else 0.0

    # === VALIDATION CROISÉE
    candidats = [x for x in montants_A + [somme_B, somme_C, montant_fallback] if x > 0]
    freq = {}
    for m in candidats:
        m_rond = round(m, 2)
        freq[m_rond] = freq.get(m_rond, 0) + 1
    if not freq:
        montant_final = 0.0
        methode_detection = "AUCUNE"
    else:
        montant_final = max(freq, key=freq.get)  # prend le montant le plus récurrent

        # Déterminer quelle méthode a trouvé ce montant
        methode_detection = []
        if montant_final in montants_A:
            methode_detection.append("A-PATTERNS")
        if somme_B == montant_final:
            methode_detection.append("B-PAIEMENT")
        if somme_C == montant_final:
            methode_detection.append("C-HT+TVA")
        if montant_fallback == montant_final and not methode_detection:
            methode_detection.append("D-FALLBACK")
        methode_detection = "+".join(methode_detection) if methode_detection else "UNKNOWN"

    # === Détection de la date (inchangée)
    date_patterns = [
        r"\b\d{1,2}[./\-]\d{1,2}[./\-]\d{2,4}\b",
        r"\b\d{1,2}\s*(janv|févr|mars|avr|mai|juin|juil|août|sept|oct|nov|déc)\.?\s*\d{2,4}\b"
    ]
    detected_date = None
    for p in date_patterns:
        match = re.search(p, ocr_text, re.IGNORECASE)
        if match:
            try:
                detected_date = parser.parse(match.group(0), dayfirst=True, fuzzy=True).date().isoformat()
                break
            except:
                continue
    if not detected_date:
        detected_date = datetime.now().date().isoformat()

    # === Lignes clés (pour affichage dans interface)
    key_lines = [
        l for l in lines if any(re.search(p, l, re.IGNORECASE) for p in total_patterns + paiement_patterns)
    ]

    # === Résultat final
    montants_possibles = sorted(set(candidats), reverse=True)
    return {
        "montants_possibles": montants_possibles if montants_possibles else [montant_final],
        "montant": montant_final,
        "date": detected_date,
        "infos": "\n".join(key_lines),
        "methode_detection": methode_detection,
        "debug_info": {
            "methode_A": montants_A,
            "methode_B": somme_B,
            "methode_C": somme_C,
            "methode_D": montant_fallback,
            "patterns_A": patterns_A_matches
        }
    }


def parse_uber_pdf(pdf_path: str) -> dict:
    """
    Parseur spécifique pour les PDF Uber.
    Objectif : extraire le montant net (net earnings) et la date de fin de période de facturation.
    Renvoie dict avec clés : montant (float), date (datetime.date), categorie, sous_categorie, source.
    Version V2 avec application automatique du 79%.
    """
    text = extract_text_from_pdf(pdf_path)
    if not text:
        return {
            "montant": 0.0,
            "date": datetime.now().date(),
            "categorie": "Revenu",
            "sous_categorie": "Uber",
            "source": "PDF Uber"
        }

    # Cherche une période de facturation sous forme "Période de facturation : 01/07/2025 - 31/07/2025"
    date_fin = None
    periode_match = re.search(
        r"P[eé]riode de facturation\s*[:\-]?\s*([0-3]?\d[\/\-\.][01]?\d[\/\-\.]\d{2,4})\s*[\-–]\s*([0-3]?\d[\/\-\.][01]?\d[\/\-\.]\d{2,4})",
        text,
        re.IGNORECASE
    )
    if periode_match:
        debut_str, fin_str = periode_match.groups()
        for fmt in ("%d/%m/%Y", "%d/%m/%y", "%d-%m-%Y", "%d-%m-%y"):
            try:
                date_fin = datetime.strptime(fin_str, fmt).date()
                break
            except Exception:
                continue

    # Si non trouvé par pattern, on tente de trouver une date "Période terminée le : 31/07/2025" ou "Period ending 31/07/2025"
    if not date_fin:
        m2 = re.search(
            r"(period ending|p[eé]riode termin[eé]e le|Date de fin)\s*[:\-]?\s*([0-3]?\d[\/\-\.][01]?\d[\/\-\.]\d{2,4})",
            text,
            re.IGNORECASE
        )
        if m2:
            date_str = m2.group(2)
            for fmt in ("%d/%m/%Y", "%d/%m/%y", "%d-%m-%Y", "%d-%m-%y"):
                try:
                    date_fin = datetime.strptime(date_str, fmt).date()
                    break
                except Exception:
                    continue

    if not date_fin:
        date_fin = datetime.now().date()

    # Montant net : varie selon le PDF Uber (Net earnings, Total to be paid, etc.)
    montant = 0.0
    montant_patterns = [
        r"(?:Net earnings|Net to driver|Total net|Montant net|Net earnings \(driver\))\s*[:\-\–]?\s*([0-9]+[.,][0-9]{2})\s*€?",
        r"([\d]{1,3}(?:[ .,]\d{3})*[.,]\d{2})\s*€\s*(?:net|netto|net earnings|to driver)?"
    ]
    for p in montant_patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            s = m.group(1).replace(" ", "").replace(".", "").replace(",", ".") if "," in m.group(1) and "." in m.group(1) else m.group(1).replace(",", ".").replace(" ", "")
            try:
                montant = safe_convert(s)
                break
            except Exception:
                continue

    # fallback: chercher le dernier montant présent dans le texte
    if montant == 0.0:
        all_amounts = re.findall(r"(\d+[.,]\d{2})\s*€?", text)
        if all_amounts:
            for a in reversed(all_amounts):
                try:
                    candidate = safe_convert(a)
                    if candidate > 0:
                        montant = candidate
                        break
                except:
                    continue

    # 🔥 V2: APPLICATION AUTOMATIQUE 79% POUR UBER
    montant_net = round(montant * 0.79, 2) if montant > 0 else 0.0
    tax_amount = round(montant - montant_net, 2) if montant > 0 else 0.0
    
    if montant > 0:
        logger.info(f"Uber PDF processed: {montant}€ → {montant_net}€ net (after 21% tax)")

    return {
        "montant": montant_net,  # 🔥 Retourne le montant NET après impôts
        "date": date_fin,
        "categorie": "Uber Eats",  # 🔥 Catégorie standardisée
        "sous_categorie": "Uber",
        "source": "PDF Uber",
        "montant_brut": montant,  # 🔥 Information supplémentaire
        "tax_amount": tax_amount
    }


def parse_fiche_paie(pdf_path: str) -> dict:
    """
    Parseur spécifique pour fiche de paie.
    Objectif : trouver la période (ou la date concernée) et le net à payer.
    Renvoie dict similaire à parse_uber_pdf.
    """
    text = extract_text_from_pdf(pdf_path)
    if not text:
        return {"montant": 0.0, "date": datetime.now().date(), "categorie": "Revenu", "sous_categorie": "Salaire", "source": "PDF Fiche de paie"}

    # 1) Trouver le net à payer (patterns : NET A PAYER, Net à payer, Net pay, Net salary)
    montant = 0.0
    net_patterns = [
        r"NET\s*A\s*PAYER\s*[:\-\–]?\s*([0-9]+[.,][0-9]{2})",
        r"Net à payer\s*[:\-\–]?\s*([0-9]+[.,][0-9]{2})",
        r"Net à payer \(à vous\)\s*[:\-\–]?\s*([0-9]+[.,][0-9]{2})",
        r"Net\s*[:\-\–]?\s*([0-9]+[.,][0-9]{2})"  # fallback
    ]
    for p in net_patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            try:
                montant = safe_convert(m.group(1))
                break
            except:
                continue

    # fallback : prendre le dernier montant trouvé, mais prudence
    if montant == 0.0:
        amounts = re.findall(r"(\d+[.,]\d{2})\s*€?", text)
        if amounts:
            candidates = [safe_convert(a) for a in amounts]
            bigs = [c for c in candidates if c > 100]
            montant = bigs[-1] if bigs else candidates[-1]

    # 2) Trouver la période ou la date : recherche de "période" ou intervalle "01/07/2025 - 31/07/2025"
    date_found = None
    periode_match = re.search(r"(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})\s*[\-–]\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})", text)
    if periode_match:
        fin_str = periode_match.groups()[1]
        for fmt in ("%d/%m/%Y", "%d/%m/%y", "%d-%m-%Y", "%d-%m-%y"):
            try:
                date_found = datetime.strptime(fin_str, fmt).date()
                break
            except:
                pass

    if not date_found:
        m2 = re.search(r"Pour le mois de\s+([A-Za-zéûà]+)\s+(\d{4})", text, re.IGNORECASE)
        if m2:
            mois_str, annee_str = m2.groups()
            mois_map = {
                "janvier":1,"février":2,"fevrier":2,"mars":3,"avril":4,"mai":5,"juin":6,
                "juillet":7,"août":8,"aout":8,"septembre":9,"octobre":10,"novembre":11,"décembre":12,"decembre":12
            }
            mois_key = mois_str.lower()
            mois_num = mois_map.get(mois_key)
            if mois_num:
                from calendar import monthrange
                last_day = monthrange(int(annee_str), mois_num)[1]
                date_found = date(int(annee_str), mois_num, last_day)

    if not date_found:
        date_found = datetime.now().date()

    return {
        "montant": round(float(montant), 2),
        "date": date_found,
        "categorie": "Revenu",
        "sous_categorie": "Salaire",
        "source": "PDF Fiche de paie"
    }


def parse_pdf_dispatcher(pdf_path: str, source_type: str) -> dict:
    """
    Dispatcher simple pour choisir le parseur adapté.
    source_type attendu : 'uber', 'fiche_paie', 'ticket' (ou 'auto' pour tentative heuristique).
    """
    stype = source_type.lower().strip()
    if stype in ("uber", "uber_pdf", "uber eats"):
        return parse_uber_pdf(pdf_path)
    elif stype in ("fiche_paie", "fiche de paie", "paye", "salaire"):
        return parse_fiche_paie(pdf_path)
    elif stype in ("ticket", "receipt", "ticket_ocr"):
        text = extract_text_from_pdf(pdf_path)
        return parse_ticket_metadata(text)
    elif stype == "auto":
        text = extract_text_from_pdf(pdf_path).lower()
        if "uber" in text or "net to driver" in text or "period" in text:
            return parse_uber_pdf(pdf_path)
        if "net a payer" in text or "fiche de paie" in text or "bulletin" in text:
            return parse_fiche_paie(pdf_path)
        return {"montant": 0.0, "date": datetime.now().date(), "categorie": "Revenu", "sous_categorie": "Inconnu", "source": "PDF Auto"}
    else:
        raise ValueError(f"Source_type inconnu pour parse_pdf_dispatcher: {source_type}")


def get_montant_from_line(label_pattern, all_lines, allow_next_line=True):
    """
    Recherche un montant à partir d'un label (ex: 'TOTAL', 'MONTANT RÉEL', etc.)
    Retourne (montant, pattern_matched) où pattern_matched indique si le pattern a vraiment été trouvé.
    """
    montant_regex = r"(\d{1,5}[.,]?\d{0,2})\s*(?:€|eur|euros?)?"

    def clean_ocr_text(txt):
        """Corrige les erreurs courantes de lecture OCR (O/0, I/1, etc.)."""
        # Ne remplacer O par 0 QUE dans un contexte numérique (entouré de chiffres)
        # Exemple: "1O5" → "105", mais "MONTANT" reste "MONTANT"
        txt = re.sub(r'(\d)[Oo](\d)', r'\g<1>0\g<2>', txt)  # 1O5 → 105
        txt = re.sub(r'(\d)[Oo](?=\s|$|,|\.)', r'\g<1>0', txt)  # 1O → 10
        txt = re.sub(r'(?<=\s|^|,|\.)[Oo](\d)', r'0\g<1>', txt)  # O5 → 05

        # Ne remplacer I/l par 1 QUE dans un contexte numérique
        txt = re.sub(r'(\d)[Il](\d)', r'\g<1>1\g<2>', txt)  # 2I5 → 215
        txt = re.sub(r'(\d)[Il](?=\s|$|,|\.)', r'\g<1>1', txt)  # 2I → 21
        txt = re.sub(r'(?<=\s|^|,|\.)[Il](\d)', r'1\g<1>', txt)  # I5 → 15

        # Nettoyer les espaces
        txt = re.sub(r"[\u200b\s]+", " ", txt)
        return txt.strip()

    for i, l in enumerate(all_lines):
        l_clean = clean_ocr_text(l)

        # Recherche du label (ex: 'TOTAL', 'MONTANT', etc.)
        if re.search(label_pattern, l_clean, re.IGNORECASE):
            found_same = re.findall(montant_regex, l_clean, re.IGNORECASE)
            if found_same:
                # Prend le montant le plus grand sur la ligne (souvent le total TTC)
                return (safe_convert(max(found_same, key=lambda x: safe_convert(x))), True)

            # Ligne suivante possible
            if allow_next_line and i + 1 < len(all_lines):
                next_line = clean_ocr_text(all_lines[i + 1])
                found_next = re.findall(montant_regex, next_line, re.IGNORECASE)
                if found_next:
                    return (safe_convert(max(found_next, key=lambda x: safe_convert(x))), True)

    # Pattern pas trouvé
    return (0.0, False)


