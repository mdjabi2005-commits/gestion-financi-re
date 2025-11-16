# -*- coding: utf-8 -*-
"""
Module logging - Partie de l'application gestiov4
Généré automatiquement par migrate_to_modular.py
"""

import os
import json
from datetime import datetime


from config import BASE_DIR, DATA_DIR, DB_PATH, TO_SCAN_DIR, SORTED_DIR, REVENUS_A_TRAITER, REVENUS_TRAITES
# Créer les dossiers de logs OCR
OCR_LOGS_DIR = os.path.join(DATA_DIR, "ocr_logs")
os.makedirs(OCR_LOGS_DIR, exist_ok=True)
LOG_PATH = os.path.join(OCR_LOGS_DIR, "pattern_log.json")
OCR_PERFORMANCE_LOG = os.path.join(OCR_LOGS_DIR, "performance_stats.json")
PATTERN_STATS_LOG = os.path.join(OCR_LOGS_DIR, "pattern_stats.json")
OCR_SCAN_LOG = os.path.join(OCR_LOGS_DIR, "scan_history.jsonl")
# === JOURNAL OCR ===

def log_pattern_occurrence(pattern_name: str):
    """Enregistre chaque mot-clé détecté par l'OCR dans un journal JSON."""
    try:
        data = {}
        if os.path.exists(LOG_PATH):
            with open(LOG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        data[pattern_name] = data.get(pattern_name, 0) + 1
        with open(LOG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[OCR-LOG] Erreur journalisation : {e}")


def log_ocr_scan(document_type: str, filename: str, montants_detectes: list, montant_choisi: float,
                 categorie: str, sous_categorie: str, patterns_detectes: list = None, success_level: str = "exact",
                 methode_detection: str = "UNKNOWN"):
    """
    Enregistre un scan OCR complet avec son résultat.

    Args:
        document_type: "ticket" ou "revenu"
        filename: nom du fichier scanné
        montants_detectes: liste des montants trouvés par l'OCR
        montant_choisi: montant finalement choisi par l'utilisateur
        categorie: catégorie de la transaction
        sous_categorie: sous-catégorie de la transaction
        patterns_detectes: liste des patterns détectés (optionnel)
        success_level: "exact" (montant exact détecté), "partial" (dans la liste), "failed" (corrigé manuellement)
        methode_detection: "A-PATTERNS", "B-PAIEMENT", "C-HT+TVA", "D-FALLBACK" ou combinaison
    """
    try:
        print(f"[OCR-LOG] Début enregistrement : {filename}, type={document_type}, success={success_level}")

        # 1. Enregistrer dans l'historique (JSONL)
        scan_entry = {
            "timestamp": datetime.now().isoformat(),
            "document_type": document_type,
            "filename": filename,
            "montants_detectes": [float(m) for m in montants_detectes] if montants_detectes else [],
            "montant_choisi": float(montant_choisi),
            "categorie": categorie,
            "sous_categorie": sous_categorie,
            "patterns_detectes": patterns_detectes or [],
            "success_level": success_level,
            "methode_detection": methode_detection,
            "result": {
                "success": success_level in ["exact", "partial"]
            },
            "extraction": {
                "montant_final": float(montant_choisi),
                "categorie_final": categorie
            }
        }

        print(f"[OCR-LOG] Écriture dans {OCR_SCAN_LOG}")
        with open(OCR_SCAN_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(scan_entry, ensure_ascii=False) + "\n")
        print("[OCR-LOG] Historique enregistre")

        # 2. Mettre à jour les statistiques de performance
        print("[OCR-LOG] Mise à jour performance stats...")
        update_performance_stats(document_type, success_level)

        # 3. Mettre à jour les statistiques par pattern
        if patterns_detectes:
            print(f"[OCR-LOG] Mise à jour pattern stats ({len(patterns_detectes)} patterns)...")
            update_pattern_stats(patterns_detectes, success_level)

        print("[OCR-LOG] Log OCR termine avec succes")

    except Exception as e:
        logger.error(f"[OCR-LOG] Erreur lors de l'enregistrement du scan : {e}")
        print(f"[OCR-LOG] ERREUR : {e}")
        import traceback
        traceback.print_exc()


def update_performance_stats(document_type: str, success_level: str):
    """Met à jour les statistiques de performance globales."""
    try:
        # Charger les stats existantes
        stats = {}
        if os.path.exists(OCR_PERFORMANCE_LOG):
            with open(OCR_PERFORMANCE_LOG, "r", encoding="utf-8") as f:
                stats = json.load(f)

        # Initialiser si nécessaire
        if document_type not in stats:
            stats[document_type] = {
                "total": 0,
                "success": 0,
                "partial": 0,
                "failed": 0,
                "success_rate": 0.0,
                "correction_rate": 0.0
            }

        # Mettre à jour
        stats[document_type]["total"] += 1
        if success_level == "exact":
            stats[document_type]["success"] += 1
        elif success_level == "partial":
            stats[document_type]["partial"] += 1
        else:
            stats[document_type]["failed"] += 1

        # Calculer les taux
        total = stats[document_type]["total"]
        stats[document_type]["success_rate"] = (stats[document_type]["success"] / total * 100) if total > 0 else 0
        stats[document_type]["correction_rate"] = (stats[document_type]["failed"] / total * 100) if total > 0 else 0

        # Ajouter timestamp de mise à jour
        stats["last_updated"] = datetime.now().isoformat()

        # Sauvegarder
        with open(OCR_PERFORMANCE_LOG, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)

    except Exception as e:
        logger.error(f"[OCR-LOG] Erreur mise à jour performance : {e}")


def update_pattern_stats(patterns_detectes: list, success_level: str):
    """Met à jour les statistiques par pattern."""
    try:
        # Charger les stats existantes
        stats = {}
        if os.path.exists(PATTERN_STATS_LOG):
            with open(PATTERN_STATS_LOG, "r", encoding="utf-8") as f:
                stats = json.load(f)

        # Mettre à jour chaque pattern
        for pattern in patterns_detectes:
            if pattern not in stats:
                stats[pattern] = {
                    "total_detections": 0,
                    "success_count": 0,
                    "partial_count": 0,
                    "failure_count": 0,
                    "success_rate": 0.0,
                    "reliability_score": 0.0
                }

            stats[pattern]["total_detections"] += 1

            if success_level == "exact":
                stats[pattern]["success_count"] += 1
            elif success_level == "partial":
                stats[pattern]["partial_count"] += 1
            else:
                stats[pattern]["failure_count"] += 1

            # Calculer taux de succès
            total = stats[pattern]["total_detections"]
            success = stats[pattern]["success_count"] + stats[pattern]["partial_count"]
            stats[pattern]["success_rate"] = (success / total * 100) if total > 0 else 0

            # Score de fiabilité (pondéré par nombre de détections)
            weight = min(total / 10, 1.0)
            stats[pattern]["reliability_score"] = stats[pattern]["success_rate"] * weight

        # Sauvegarder
        with open(PATTERN_STATS_LOG, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)

    except Exception as e:
        logger.error(f"[OCR-LOG] Erreur mise à jour patterns : {e}")


def determine_success_level(montants_detectes: list, montant_choisi: float) -> str:
    """
    Détermine le niveau de succès de la détection OCR.

    Returns:
        "exact" : Le montant choisi est le premier de la liste (succès total)
        "partial" : Le montant choisi est dans la liste mais pas le premier (succès partiel)
        "failed" : Le montant choisi n'est pas dans la liste (échec)
    """
    if not montants_detectes:
        return "failed"

    # Arrondir pour comparaison
    montants_arrondis = [round(float(m), 2) for m in montants_detectes]
    montant_choisi_arrondi = round(float(montant_choisi), 2)

    if montants_arrondis and montants_arrondis[0] == montant_choisi_arrondi:
        return "exact"
    elif montant_choisi_arrondi in montants_arrondis:
        return "partial"
    else:
        return "failed"


def get_ocr_performance_report():
    """Récupère le rapport de performance depuis les fichiers locaux."""
    try:
        print(f"[DEBUG] get_ocr_performance_report() - Chemin: {OCR_PERFORMANCE_LOG}")
        if os.path.exists(OCR_PERFORMANCE_LOG):
            print("[DEBUG] Fichier existe, lecture...")
            with open(OCR_PERFORMANCE_LOG, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"[DEBUG] Données chargées: {data}")
                return data
        else:
            print("[DEBUG] Fichier n'existe pas")
    except Exception as e:
        print(f"[DEBUG] ERREUR lors de la lecture: {e}")
        import traceback
        traceback.print_exc()
    return {}


def get_best_patterns(min_detections, min_success_rate):
    """Récupère les meilleurs patterns."""
    # À adapter selon votre structure
    try:
        if os.path.exists(PATTERN_STATS_LOG):
            with open(PATTERN_STATS_LOG, 'r', encoding='utf-8') as f:
                stats = json.load(f)
                # Filtrer et retourner
                return [
                    {
                        'pattern': k,
                        'success_rate': v.get('success_rate', 0),
                        'reliability_score': v.get('reliability_score', 0),
                        'detections': v.get('total_detections', 0),
                        'corrections': v.get('correction_count', 0)
                    }
                    for k, v in stats.items()
                    if v.get('total_detections', 0) >= min_detections
                    and v.get('success_rate', 0) >= min_success_rate
                ]
    except:
        pass
    return []


def get_worst_patterns(min_detections, max_success_rate):
    """Récupère les patterns problématiques."""
    # À adapter selon votre structure
    try:
        if os.path.exists(PATTERN_STATS_LOG):
            with open(PATTERN_STATS_LOG, 'r', encoding='utf-8') as f:
                stats = json.load(f)
                return [
                    {
                        'pattern': k,
                        'success_rate': v.get('success_rate', 0),
                        'detections': v.get('total_detections', 0),
                        'corrections': v.get('correction_count', 0)
                    }
                    for k, v in stats.items()
                    if v.get('total_detections', 0) >= min_detections
                    and v.get('success_rate', 0) <= max_success_rate
                ]
    except:
        pass
    return []


def get_scan_history(document_type=None, limit=100):
    """Récupère l'historique des scans."""
    # À adapter selon votre structure
    try:
        if os.path.exists(OCR_SCAN_LOG):
            scans = []
            with open(OCR_SCAN_LOG, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        scan = json.loads(line)
                        if document_type is None or scan.get('document_type') == document_type:
                            scans.append(scan)
                    except:
                        continue
            return scans[:limit]
    except:
        pass
    return []


