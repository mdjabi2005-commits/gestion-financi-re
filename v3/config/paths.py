"""File paths configuration."""

import os
from pathlib import Path

# Base directory
_home = Path.home()
DATA_DIR = str(_home / "analyse")

# Database
DB_PATH = os.path.join(DATA_DIR, "finances2.db")

# Scan directories
TO_SCAN_DIR = os.path.join(DATA_DIR, "tickets_a_scanner")
SORTED_DIR = os.path.join(DATA_DIR, "tickets_tries")
PROBLEMATIC_DIR = os.path.join(DATA_DIR, "tickets_problematiques")

# Revenue directories
REVENUS_A_TRAITER = os.path.join(DATA_DIR, "revenus_a_traiter")
REVENUS_TRAITES = os.path.join(DATA_DIR, "revenus_traites")

# OCR Logs
OCR_LOGS_DIR = os.path.join(DATA_DIR, "ocr_logs")
LOG_PATH = os.path.join(OCR_LOGS_DIR, "pattern_log.json")
OCR_PERFORMANCE_LOG = os.path.join(OCR_LOGS_DIR, "performance_stats.json")
PATTERN_STATS_LOG = os.path.join(OCR_LOGS_DIR, "pattern_stats.json")
OCR_SCAN_LOG = os.path.join(OCR_LOGS_DIR, "scan_history.jsonl")
POTENTIAL_PATTERNS_LOG = os.path.join(OCR_LOGS_DIR, "potential_patterns.jsonl")

# Create directories
for directory in [DATA_DIR, TO_SCAN_DIR, SORTED_DIR, PROBLEMATIC_DIR,
                  REVENUS_A_TRAITER, REVENUS_TRAITES, OCR_LOGS_DIR]:
    os.makedirs(directory, exist_ok=True)
