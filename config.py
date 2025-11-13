# -*- coding: utf-8 -*-
"""
Created on Thu Oct 16 19:59:08 2025

@author: djabi
"""

import os

# ==============================
# 📂 CONFIGURATION GLOBALE DU PROJET
# ==============================

# 📍 Dossier racine du projet
BASE_DIR = r"C:\Users\djabi\gestion-financière"

# ==============================
# 📁 Dossiers principaux
# ==============================
TO_SCAN_DIR = os.path.join(BASE_DIR, "tickets_a_scanner")   # Dossier source (tickets à scanner)
SORTED_DIR = os.path.join(BASE_DIR, "tickets_scanner")      # Dossier final (classé)

# Dossier data interne
DATA_DIR = os.path.join(BASE_DIR, "data")

# Dossiers pour les revenus
REVENUS_A_TRAITER = os.path.join(BASE_DIR, "revenus_a_traiter")
REVENUS_TRAITES = os.path.join(BASE_DIR, "revenus_traités")

# ==============================
# 💾 Base de données SQLite
# ==============================
DB_PATH = os.path.join(DATA_DIR, "finances.db")

# ==============================
# 🛠️ Création automatique des dossiers
# ==============================
for d in [TO_SCAN_DIR, SORTED_DIR, DATA_DIR, REVENUS_A_TRAITER, REVENUS_TRAITES]:
    os.makedirs(d, exist_ok=True)

# 🔹 Emplacement de la base de données
DB_PATH = os.path.join(DATA_DIR, "finances.db")
