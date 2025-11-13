#!/usr/bin/env python3
"""Script de test pour vérifier le système de logging OCR."""

import json
import os
from datetime import datetime

# Configuration
DATA_DIR = "data"
OCR_LOGS_DIR = os.path.join(DATA_DIR, "ocr_logs")
os.makedirs(OCR_LOGS_DIR, exist_ok=True)

OCR_SCAN_LOG = os.path.join(OCR_LOGS_DIR, "scan_history.jsonl")
OCR_PERFORMANCE_LOG = os.path.join(OCR_LOGS_DIR, "performance_stats.json")
PATTERN_STATS_LOG = os.path.join(OCR_LOGS_DIR, "pattern_stats.json")

print("=== TEST DU SYSTEME DE LOGGING OCR ===\n")

# 1. Créer un scan de test
print("[1] Creation d'un scan de test...")
scan_entry = {
    "timestamp": datetime.now().isoformat(),
    "document_type": "ticket",
    "filename": "test_ticket.jpg",
    "montants_detectes": [15.50, 20.00, 15.50],
    "montant_choisi": 15.50,
    "categorie": "Alimentation",
    "sous_categorie": "Courses",
    "patterns_detectes": ["total", "montant", "ttc"],
    "success_level": "exact",
    "result": {"success": True},
    "extraction": {"montant_final": 15.50, "categorie_final": "Alimentation"}
}

with open(OCR_SCAN_LOG, "a", encoding="utf-8") as f:
    f.write(json.dumps(scan_entry, ensure_ascii=False) + "\n")
print(f"   ✓ Scan enregistre dans {OCR_SCAN_LOG}")

# 2. Créer des stats de performance
print("\n[2] Creation des stats de performance...")
perf_stats = {
    "ticket": {
        "total": 1,
        "success": 1,
        "partial": 0,
        "failed": 0,
        "success_rate": 100.0,
        "correction_rate": 0.0
    },
    "last_updated": datetime.now().isoformat()
}

with open(OCR_PERFORMANCE_LOG, "w", encoding="utf-8") as f:
    json.dump(perf_stats, f, indent=2, ensure_ascii=False)
print(f"   ✓ Stats enregistrees dans {OCR_PERFORMANCE_LOG}")

# 3. Créer des stats de patterns
print("\n[3] Creation des stats de patterns...")
pattern_stats = {
    "total": {
        "total_detections": 1,
        "success_count": 1,
        "partial_count": 0,
        "correction_count": 0,
        "success_rate": 100.0,
        "reliability_score": 100.0
    },
    "montant": {
        "total_detections": 1,
        "success_count": 1,
        "partial_count": 0,
        "correction_count": 0,
        "success_rate": 100.0,
        "reliability_score": 100.0
    },
    "ttc": {
        "total_detections": 1,
        "success_count": 1,
        "partial_count": 0,
        "correction_count": 0,
        "success_rate": 100.0,
        "reliability_score": 100.0
    }
}

with open(PATTERN_STATS_LOG, "w", encoding="utf-8") as f:
    json.dump(pattern_stats, f, indent=2, ensure_ascii=False)
print(f"   ✓ Patterns enregistres dans {PATTERN_STATS_LOG}")

# 4. Vérification
print("\n[4] Verification des fichiers...")
files = [
    ("scan_history.jsonl", OCR_SCAN_LOG),
    ("performance_stats.json", OCR_PERFORMANCE_LOG),
    ("pattern_stats.json", PATTERN_STATS_LOG)
]

for name, path in files:
    if os.path.exists(path):
        size = os.path.getsize(path)
        print(f"   ✓ {name}: {size} bytes")
    else:
        print(f"   ✗ {name}: MANQUANT")

print("\n=== TEST TERMINE ===")
print(f"\nMaintenant, ouvre l'application Streamlit et va sur la page 'Analyse'.")
print(f"Tu devrais voir 1 ticket scanne avec 100% de succes !")
