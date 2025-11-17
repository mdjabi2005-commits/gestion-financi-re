"""Document parsing functions for extracting structured data from OCR text."""

import os
import re
import shutil
import logging
from datetime import datetime, date
from calendar import monthrange
from typing import Dict, Tuple, List, Optional, Any
from dateutil import parser
from pdfminer.high_level import extract_text

from config import SORTED_DIR
from modules.utils import safe_convert

logger = logging.getLogger(__name__)


def get_montant_from_line(
    label_pattern: str,
    all_lines: List[str],
    allow_next_line: bool = True
) -> Tuple[float, bool]:
    """
    Extract amount from a line matching a pattern.

    Searches for a label pattern (e.g., 'TOTAL', 'MONTANT') and extracts
    the associated amount from the same line or the next line.

    Args:
        label_pattern: Regex pattern to find the label
        all_lines: List of all text lines
        allow_next_line: Whether to check the next line if no amount found on current line

    Returns:
        Tuple of (amount, found) where found indicates if pattern matched
    """
    montant_regex = r"(\d{1,5}[.,]?\d{0,2})\s*(?:€|eur|euros?)?"

    def clean_ocr_text(txt: str) -> str:
        """Correct common OCR reading errors (O/0, I/1, etc.)."""
        # Replace O with 0 ONLY in numeric context
        txt = re.sub(r'(\d)[Oo](\d)', r'\g<1>0\g<2>', txt)  # 1O5 → 105
        txt = re.sub(r'(\d)[Oo](?=\s|$|,|\.)', r'\g<1>0', txt)  # 1O → 10
        txt = re.sub(r'(^|[\s,\.])[Oo](\d)', r'\g<1>0\g<2>', txt)  # O5 at start/after delimiter → 05

        # Replace I/l with 1 ONLY in numeric context
        txt = re.sub(r'(\d)[Il](\d)', r'\g<1>1\g<2>', txt)  # 2I5 → 215
        txt = re.sub(r'(\d)[Il](?=\s|$|,|\.)', r'\g<1>1', txt)  # 2I → 21
        txt = re.sub(r'(^|[\s,\.])[Il](\d)', r'\g<1>1\g<2>', txt)  # I5 at start/after delimiter → 15

        # Clean spaces
        txt = re.sub(r"[\u200b\s]+", " ", txt)
        return txt.strip()

    for i, l in enumerate(all_lines):
        l_clean = clean_ocr_text(l)

        # Search for label (e.g., 'TOTAL', 'MONTANT', etc.)
        if re.search(label_pattern, l_clean, re.IGNORECASE):
            found_same = re.findall(montant_regex, l_clean, re.IGNORECASE)
            if found_same:
                # Take the largest amount on the line (often the TTC total)
                return (safe_convert(max(found_same, key=lambda x: safe_convert(x))), True)

            # Check next line if allowed
            if allow_next_line and i + 1 < len(all_lines):
                next_line = clean_ocr_text(all_lines[i + 1])
                found_next = re.findall(montant_regex, next_line, re.IGNORECASE)
                if found_next:
                    return (safe_convert(max(found_next, key=lambda x: safe_convert(x))), True)

    # Pattern not found
    return (0.0, False)


def parse_ticket_metadata(ocr_text: str) -> Dict[str, Any]:
    """
    Extract metadata from receipt OCR text using multiple detection methods.

    Uses four detection methods:
    A. Direct total patterns (TOTAL TTC, MONTANT, NET A PAYER, etc.)
    B. Payment sum (CB, CARTE, ESPECES, etc.)
    C. Net + VAT sum (HT + TVA)
    D. Global fallback (largest amount)

    Cross-validates results and returns the most frequent amount.

    Args:
        ocr_text: Raw OCR text from receipt

    Returns:
        Dictionary containing:
        - montants_possibles: List of all possible amounts
        - montant: Final selected amount
        - date: Detected or current date
        - infos: Key lines from the receipt
        - methode_detection: Detection method used
        - debug_info: Detailed detection information
    """
    lines = [l.strip() for l in ocr_text.split("\n") if l.strip()]

    def normalize_line(l: str) -> str:
        return l.replace("O", "0").replace("o", "0").replace("I", "1").replace("l", "1").strip()

    lines = [normalize_line(l) for l in lines]

    montant_regex = r"(\d{1,5}[.,]\d{1,2})"

    # === METHOD A: Direct totals ===
    total_patterns = [
        r"TOTAL\s*TTC",
        r"TOTAL\s*(A\s*PAYER)?",
        r"MONTANT\s*(R[EÉ][EÉ][LI]|R[EÉ][LI][LI]|TTC)?",  # REEL, RÉEL, RELL, RFEI, etc.
        r"NET\s*A\s*PAYER",
        r"À\s*PAYER",
        r"TOTAL$",
        r"TTC",
        r"MONTANT\s*EUR",  # Leclerc variant
    ]
    montants_A = []
    patterns_A_matches = []
    for pattern in total_patterns:
        montant, matched = get_montant_from_line(pattern, lines)
        if matched and montant > 0:  # Only count if pattern REALLY matched
            montants_A.append(round(montant, 2))
            patterns_A_matches.append(pattern)

    # === METHOD B: Sum of payments ===
    paiement_patterns = [r"CB", r"CARTE", r"ESPECES", r"WEB", r"PAYPAL", r"CHEQUE"]
    montants_B = []
    for l in lines:
        if any(re.search(p, l, re.IGNORECASE) for p in paiement_patterns):
            found = re.findall(montant_regex, l)
            for val in found:
                montants_B.append(safe_convert(val))
    somme_B = round(sum(montants_B), 2) if montants_B else 0.0

    # === METHOD C: Net + VAT ===
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

    # === METHOD D: Global fallback ===
    all_amounts = [safe_convert(m) for m in re.findall(montant_regex, ocr_text)]
    montant_fallback = max(all_amounts) if all_amounts else 0.0

    # === CROSS-VALIDATION ===
    candidats = [x for x in montants_A + [somme_B, somme_C, montant_fallback] if x > 0]
    freq = {}
    for m in candidats:
        m_rond = round(m, 2)
        freq[m_rond] = freq.get(m_rond, 0) + 1

    if not freq:
        montant_final = 0.0
        methode_detection = "AUCUNE"
    else:
        montant_final = max(freq, key=freq.get)  # Take most frequent amount

        # Determine which method found this amount
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

    # === Date detection ===
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

    # === Key lines (for display in interface) ===
    key_lines = [
        l for l in lines if any(re.search(p, l, re.IGNORECASE) for p in total_patterns + paiement_patterns)
    ]

    # === Final result ===
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


def move_ticket_to_sorted(ticket_path: str, categorie: str, sous_categorie: str) -> None:
    """
    Move a ticket to the sorted directory with category/subcategory structure.

    Creates a unique filename if a file with the same name already exists.

    Args:
        ticket_path: Path to the ticket file
        categorie: Category name
        sous_categorie: Subcategory name
    """
    cat_dir = os.path.join(SORTED_DIR, categorie.strip())
    souscat_dir = os.path.join(cat_dir, sous_categorie.strip())
    os.makedirs(souscat_dir, exist_ok=True)

    base_name = os.path.basename(ticket_path)
    dest_path = os.path.join(souscat_dir, base_name)

    # If a file with the same name exists, create a unique name
    if os.path.exists(dest_path):
        name, ext = os.path.splitext(base_name)
        counter = 1
        while os.path.exists(dest_path):
            new_name = f"{name}_{counter}{ext}"
            dest_path = os.path.join(souscat_dir, new_name)
            counter += 1

    shutil.move(ticket_path, dest_path)
    logger.info(f"Ticket moved to: {dest_path}")


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Read a PDF and return raw text.

    Args:
        pdf_path: Path to PDF file

    Returns:
        Extracted text or empty string on error
    """
    try:
        return extract_text(pdf_path)
    except Exception as e:
        logger.warning(f"Unable to read PDF {pdf_path} ({e})")
        return ""


def parse_uber_pdf(pdf_path: str) -> Dict[str, Any]:
    """
    Parse an Uber Eats PDF invoice to extract revenue information.

    Extracts:
    - Billing period end date
    - Net earnings amount
    - Applies automatic 79% net calculation (21% tax)

    Args:
        pdf_path: Path to Uber PDF file

    Returns:
        Dictionary with montant (net), date, categorie, sous_categorie, source,
        montant_brut, and tax_amount
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

    # Look for billing period: "Période de facturation : 01/07/2025 - 31/07/2025"
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

    # If not found, try "Période terminée le : 31/07/2025" or "Period ending 31/07/2025"
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

    # Net amount: varies by Uber PDF (Net earnings, Total to be paid, etc.)
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

    # Fallback: find last amount in text
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

    # Apply automatic 79% for Uber
    montant_net = round(montant * 0.79, 2) if montant > 0 else 0.0
    tax_amount = round(montant - montant_net, 2) if montant > 0 else 0.0

    if montant > 0:
        logger.info(f"Uber PDF processed: {montant}€ → {montant_net}€ net (after 21% tax)")

    return {
        "montant": montant_net,  # Return NET amount after taxes
        "date": date_fin,
        "categorie": "Uber Eats",  # Standardized category
        "sous_categorie": "Uber",
        "source": "PDF Uber",
        "montant_brut": montant,  # Additional information
        "tax_amount": tax_amount
    }


def parse_fiche_paie(pdf_path: str) -> Dict[str, Any]:
    """
    Parse a salary slip (fiche de paie) PDF.

    Extracts:
    - Net pay amount
    - Pay period or month

    Args:
        pdf_path: Path to salary slip PDF

    Returns:
        Dictionary with montant, date, categorie, sous_categorie, and source
    """
    text = extract_text_from_pdf(pdf_path)
    if not text:
        return {
            "montant": 0.0,
            "date": datetime.now().date(),
            "categorie": "Revenu",
            "sous_categorie": "Salaire",
            "source": "PDF Fiche de paie"
        }

    # 1) Find net pay (patterns: NET A PAYER, Net à payer, Net pay, Net salary)
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

    # Fallback: take last amount found, but be careful
    if montant == 0.0:
        amounts = re.findall(r"(\d+[.,]\d{2})\s*€?", text)
        if amounts:
            candidates = [safe_convert(a) for a in amounts]
            bigs = [c for c in candidates if c > 100]
            montant = bigs[-1] if bigs else candidates[-1]

    # 2) Find period or date: search for "période" or interval "01/07/2025 - 31/07/2025"
    date_found = None
    periode_match = re.search(
        r"(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})\s*[\-–]\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})",
        text
    )
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
                "janvier": 1, "février": 2, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6,
                "juillet": 7, "août": 8, "aout": 8, "septembre": 9, "octobre": 10, "novembre": 11,
                "décembre": 12, "decembre": 12
            }
            mois_key = mois_str.lower()
            mois_num = mois_map.get(mois_key)
            if mois_num:
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


def parse_pdf_dispatcher(pdf_path: str, source_type: str) -> Dict[str, Any]:
    """
    Dispatch PDF parsing to the appropriate parser based on source type.

    Args:
        pdf_path: Path to PDF file
        source_type: Type of PDF ("uber", "fiche_paie", "ticket", etc.)

    Returns:
        Parsed document metadata
    """
    stype = source_type.lower().strip()

    if stype in ("uber", "uber_pdf", "uber eats"):
        return parse_uber_pdf(pdf_path)
    elif stype in ("fiche_paie", "fiche de paie", "paye", "salaire"):
        return parse_fiche_paie(pdf_path)
    elif stype in ("ticket", "receipt", "ticket_ocr"):
        text = extract_text_from_pdf(pdf_path)
        return parse_ticket_metadata(text)
    else:
        # Default: try ticket parsing
        text = extract_text_from_pdf(pdf_path)
        return parse_ticket_metadata(text)
