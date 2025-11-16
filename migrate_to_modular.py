#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de migration automatique pour restructurer gestiov4.py en architecture modulaire.

Ce script :
1. Crée la structure de dossiers modulaire
2. Extrait les fonctions du fichier monolithique
3. Les organise dans les bons modules
4. Gère les imports automatiquement
5. Crée un nouveau point d'entrée minimaliste
"""

import os
import re
import shutil
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime


class MigrationScript:
    """Gère la migration de gestiov4.py vers une architecture modulaire."""

    def __init__(self, source_file="gestiov4.py", backup=True):
        self.source_file = source_file
        self.backup = backup
        self.base_dir = Path(".")

        # Structure des modules avec leurs fonctions associées
        self.module_mapping = {
            # Core - Database
            "core/database.py": [
                "get_db_connection",
                "init_db",
                "migrate_database_schema",
            ],

            # Core - Transactions
            "core/transactions.py": [
                "load_transactions",
                "load_recurrent_transactions",
                "insert_transaction_batch",
                "validate_transaction_data",
            ],

            # Core - Budget
            "core/budget.py": [
                "analyze_exceptional_expenses",
                "analyze_budget_history",
                "analyze_monthly_budget_coverage",
                "get_period_start_date",
                "calculate_months_in_period",
            ],

            # Core - Recurrences
            "core/recurrences.py": [
                "backfill_recurrences_to_today",
                "normalize_recurrence_column",
                "_inc",
            ],

            # OCR - Logging
            "ocr/logging.py": [
                "log_pattern_occurrence",
                "log_ocr_scan",
                "update_performance_stats",
                "update_pattern_stats",
                "determine_success_level",
                "get_ocr_performance_report",
                "get_best_patterns",
                "get_worst_patterns",
                "get_scan_history",
            ],

            # OCR - Engine
            "ocr/engine.py": [
                "full_ocr",
                "extract_text_from_pdf",
                "nettoyer_montant",
            ],

            # OCR - Parsers
            "ocr/parsers.py": [
                "parse_ticket_metadata",
                "parse_uber_pdf",
                "parse_fiche_paie",
                "parse_pdf_dispatcher",
                "get_montant_from_line",
            ],

            # OCR - Patterns
            "ocr/patterns.py": [
                "analyze_external_log",
                "extract_patterns_from_text",
                "calculate_pattern_reliability",
                "diagnose_ocr_patterns",
            ],

            # Services - File Manager
            "services/file_manager.py": [
                "trouver_fichiers_associes",
                "supprimer_fichiers_associes",
                "deplacer_fichiers_associes",
                "move_ticket_to_sorted",
            ],

            # Services - Uber Tax
            "services/uber_tax.py": [
                "apply_uber_tax",
                "process_uber_revenue",
            ],

            # Utils - Converters
            "utils/converters.py": [
                "safe_convert",
                "safe_date_convert",
                "normaliser_date",
                "numero_to_mois",
            ],

            # Utils - Validators
            "utils/validators.py": [
                "validate_transaction_data",
                "correct_category_name",
            ],

            # UI - Components
            "ui/components.py": [
                "show_toast",
                "toast_success",
                "toast_warning",
                "toast_error",
                "get_badge_html",
                "get_badge_icon",
                "afficher_carte_transaction",
                "afficher_documents_associes",
                "refresh_and_rerun",
            ],

            # UI - Pages
            "ui/pages/accueil.py": [
                "interface_accueil",
            ],

            "ui/pages/transactions.py": [
                "interface_transactions_unifiee",
                "interface_voir_transactions_v3",
                "interface_transactions_simplifiee",
            ],

            "ui/pages/portefeuille.py": [
                "interface_portefeuille",
            ],

            "ui/pages/scan_tickets.py": [
                "interface_ajouter_depenses_fusionnee",
                "process_all_tickets_in_folder",
            ],

            "ui/pages/scan_revenus.py": [
                "interface_ajouter_revenu",
                "interface_process_all_revenues_in_folder",
            ],

            "ui/pages/recurrences.py": [
                "interface_gerer_recurrences",
                "interface_transaction_recurrente",
            ],

            "ui/pages/analytics.py": [
                "interface_ocr_analysis_complete",
                "interface_own_scans",
                "interface_external_logs",
                "interface_comparison",
                "interface_diagnostic",
            ],

            "ui/pages/investissements.py": [
                "interface_voir_investissements_alpha",
            ],
        }

        # Imports nécessaires par module
        self.module_imports = {
            "core/database.py": [
                "import sqlite3",
                "import os",
                "from config import DB_PATH",
            ],
            "core/transactions.py": [
                "import pandas as pd",
                "import sqlite3",
                "from datetime import datetime, date",
                "from config import DB_PATH",
                "from core.database import get_db_connection",
            ],
            "core/budget.py": [
                "import pandas as pd",
                "import sqlite3",
                "from datetime import date",
                "from dateutil.relativedelta import relativedelta",
                "from config import DB_PATH",
                "from core.transactions import load_transactions",
            ],
            "core/recurrences.py": [
                "import sqlite3",
                "import pandas as pd",
                "from datetime import datetime, date",
                "from dateutil.relativedelta import relativedelta",
                "from config import DB_PATH",
                "from core.database import get_db_connection",
            ],
            "ocr/logging.py": [
                "import os",
                "import json",
                "from datetime import datetime",
            ],
            "ocr/engine.py": [
                "import pytesseract",
                "from PIL import Image",
                "import cv2",
                "import numpy as np",
                "import re",
                "import PyPDF2",
            ],
            "ocr/parsers.py": [
                "import re",
                "from datetime import datetime",
                "from ocr.engine import extract_text_from_pdf",
            ],
            "ocr/patterns.py": [
                "import re",
                "import pandas as pd",
                "from datetime import datetime",
            ],
            "services/file_manager.py": [
                "import os",
                "import shutil",
                "from pathlib import Path",
                "from config import SORTED_DIR, REVENUS_TRAITES",
            ],
            "services/uber_tax.py": [
                "from datetime import datetime",
            ],
            "utils/converters.py": [
                "import re",
                "from datetime import datetime, date",
                "from dateutil import parser",
            ],
            "utils/validators.py": [
                "from datetime import datetime",
            ],
            "ui/components.py": [
                "import streamlit as st",
                "import streamlit.components.v1 as components",
                "from datetime import datetime",
                "from services.file_manager import trouver_fichiers_associes",
            ],
            "ui/pages/accueil.py": [
                "import streamlit as st",
                "import pandas as pd",
                "import plotly.express as px",
                "from datetime import datetime, date, timedelta",
                "from dateutil.relativedelta import relativedelta",
                "from core.transactions import load_transactions",
                "from ui.components import toast_success, toast_warning",
            ],
            "ui/pages/transactions.py": [
                "import streamlit as st",
                "import pandas as pd",
                "from datetime import datetime, date",
                "from core.transactions import load_transactions",
                "from core.database import get_db_connection",
                "from ui.components import afficher_carte_transaction, toast_success, toast_error, refresh_and_rerun",
            ],
            "ui/pages/portefeuille.py": [
                "import streamlit as st",
                "import pandas as pd",
                "import sqlite3",
                "from datetime import datetime, date",
                "from core.budget import analyze_exceptional_expenses, get_period_start_date, calculate_months_in_period",
                "from core.transactions import load_transactions",
                "from core.database import get_db_connection",
                "from ui.components import toast_success, toast_warning, toast_error, refresh_and_rerun",
            ],
            "ui/pages/scan_tickets.py": [
                "import streamlit as st",
                "import os",
                "from PIL import Image",
                "from datetime import datetime, date",
                "from ocr.engine import full_ocr",
                "from ocr.parsers import parse_ticket_metadata",
                "from ocr.logging import log_ocr_scan",
                "from services.file_manager import move_ticket_to_sorted",
                "from core.database import get_db_connection",
                "from ui.components import toast_success, toast_error, refresh_and_rerun",
            ],
            "ui/pages/scan_revenus.py": [
                "import streamlit as st",
                "import os",
                "from datetime import datetime, date",
                "from ocr.parsers import parse_uber_pdf, parse_fiche_paie, parse_pdf_dispatcher",
                "from services.uber_tax import process_uber_revenue",
                "from core.database import get_db_connection",
                "from ui.components import toast_success, toast_error, refresh_and_rerun",
            ],
            "ui/pages/recurrences.py": [
                "import streamlit as st",
                "import pandas as pd",
                "from datetime import datetime, date",
                "from core.transactions import load_recurrent_transactions",
                "from core.recurrences import backfill_recurrences_to_today",
                "from core.database import get_db_connection",
                "from ui.components import toast_success, toast_warning, toast_error, refresh_and_rerun",
            ],
            "ui/pages/analytics.py": [
                "import streamlit as st",
                "import pandas as pd",
                "import plotly.express as px",
                "from ocr.logging import get_ocr_performance_report, get_scan_history",
                "from ocr.patterns import diagnose_ocr_patterns, analyze_external_log",
                "from ui.components import toast_success",
            ],
            "ui/pages/investissements.py": [
                "import streamlit as st",
                "import pandas as pd",
                "from alpha_vantage.timeseries import TimeSeries",
                "import matplotlib.pyplot as plt",
                "from ui.components import toast_success, toast_error",
            ],
        }

    def create_backup(self):
        """Crée une sauvegarde du fichier source."""
        if self.backup and os.path.exists(self.source_file):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"{self.source_file}.backup_{timestamp}"
            shutil.copy2(self.source_file, backup_file)
            print(f"✅ Sauvegarde créée : {backup_file}")
            return backup_file
        return None

    def create_directory_structure(self):
        """Crée la structure de dossiers pour les modules."""
        directories = [
            "core",
            "ocr",
            "services",
            "utils",
            "ui",
            "ui/pages",
        ]

        for directory in directories:
            dir_path = self.base_dir / directory
            dir_path.mkdir(parents=True, exist_ok=True)

            # Créer __init__.py
            init_file = dir_path / "__init__.py"
            if not init_file.exists():
                init_file.write_text("# -*- coding: utf-8 -*-\n")

            print(f"✅ Dossier créé : {directory}/")

        print("\n✅ Structure de dossiers créée avec succès !")

    def extract_function_code(self, content: str, function_name: str) -> str:
        """Extrait le code complet d'une fonction depuis le contenu source."""
        lines = content.split('\n')
        function_lines = []
        in_function = False
        function_indent = 0

        for i, line in enumerate(lines):
            # Détection du début de la fonction
            if re.match(rf'^def {re.escape(function_name)}\(', line):
                in_function = True
                function_indent = len(line) - len(line.lstrip())
                function_lines.append(line)

            elif in_function:
                # Ligne vide - toujours inclure
                if not line.strip():
                    function_lines.append(line)
                    continue

                # Commentaire au même niveau ou plus indenté - inclure
                if line.strip().startswith('#'):
                    current_indent = len(line) - len(line.lstrip())
                    if current_indent > function_indent:
                        function_lines.append(line)
                    else:
                        # Commentaire au niveau 0 = séparateur de section
                        if re.match(r'^#\s*=', line):
                            break
                        function_lines.append(line)
                    continue

                # Ligne de code
                current_indent = len(line) - len(line.lstrip())

                # Si l'indentation est <= à l'indentation de la fonction
                # et que ce n'est pas une suite de la def, c'est la fin
                if current_indent <= function_indent:
                    # Vérifier si c'est une nouvelle fonction/classe
                    if line.lstrip().startswith('def ') or line.lstrip().startswith('class ') or line.lstrip().startswith('@'):
                        break
                    # Séparateur de section
                    if re.match(r'^#\s*=', line):
                        break
                    # Sinon, probablement la fin du fichier ou un commentaire
                    break

                # Ligne indentée - partie de la fonction
                function_lines.append(line)

        if function_lines:
            # Nettoyer les lignes vides à la fin
            while function_lines and not function_lines[-1].strip():
                function_lines.pop()

            return '\n'.join(function_lines) + "\n\n\n"

        return None

    def read_source_file(self) -> str:
        """Lit le contenu du fichier source."""
        with open(self.source_file, 'r', encoding='utf-8') as f:
            return f.read()

    def extract_config_section(self, content: str) -> str:
        """Extrait la section de configuration (imports de config, constantes OCR, etc.)."""
        lines = content.split('\n')
        config_lines = []

        # Chercher la section de configuration
        in_config = False
        for line in lines:
            # Section des imports de config
            if 'from config import' in line:
                in_config = True
                config_lines.append(line)
            elif in_config:
                # Constantes OCR
                if any(x in line for x in ['OCR_LOGS_DIR', 'LOG_PATH', 'OCR_PERFORMANCE_LOG', 'PATTERN_STATS_LOG', 'OCR_SCAN_LOG']):
                    config_lines.append(line)
                elif line.strip() and not line.startswith('#') and 'def ' in line:
                    break
                elif line.strip():
                    config_lines.append(line)

        return '\n'.join(config_lines) + '\n\n' if config_lines else ''

    def create_module_file(self, module_path: str, functions: List[str], content: str):
        """Crée un fichier module avec les fonctions extraites."""
        file_path = self.base_dir / module_path

        # Header du module
        module_name = module_path.split('/')[-1].replace('.py', '')
        header = f'''# -*- coding: utf-8 -*-
"""
Module {module_name} - Partie de l'application gestiov4
Généré automatiquement par migrate_to_modular.py
"""

'''

        # Imports
        imports = self.module_imports.get(module_path, [])
        imports_section = '\n'.join(imports) + '\n\n\n' if imports else ''

        # Config (si nécessaire pour certains modules)
        config_section = ''
        if 'ocr/' in module_path:
            config_section = self.extract_config_section(content)

        # Fonctions
        functions_code = []
        for func_name in functions:
            func_code = self.extract_function_code(content, func_name)
            if func_code:
                functions_code.append(func_code)
                print(f"  ✅ {func_name}()")
            else:
                print(f"  ⚠️  {func_name}() - Non trouvée")

        # Écrire le fichier
        full_content = header + imports_section + config_section + ''.join(functions_code)

        file_path.write_text(full_content, encoding='utf-8')
        print(f"📄 Module créé : {module_path}\n")

    def create_main_file(self):
        """Crée le nouveau fichier principal gestiov4.py."""
        main_content = '''# -*- coding: utf-8 -*-
"""
Application de Gestion Financière v4
Point d'entrée principal

Architecture modulaire :
- core/       : Logique métier (database, transactions, budget, recurrences)
- ocr/        : OCR et parsing de documents
- services/   : Services métier (file_manager, uber_tax)
- ui/         : Interface utilisateur (components, pages)
- utils/      : Utilitaires (converters, validators)
"""

import streamlit as st
from core.database import init_db, migrate_database_schema
from ui.pages import (
    accueil,
    transactions,
    portefeuille,
    scan_tickets,
    scan_revenus,
    recurrences,
    analytics,
    investissements,
)


# Configuration Streamlit
st.set_page_config(layout="wide", page_title="Gestion Financière v4")

st.markdown("""
    <style>
    div[data-testid="stDataFrame"] div[role="gridcell"] {
        font-size: 16px !important;
        padding: 8px !important;
    }
    </style>
""", unsafe_allow_html=True)


def main():
    """Point d'entrée principal de l'application."""

    # Initialiser la base de données
    init_db()
    migrate_database_schema()

    # Menu de navigation
    st.sidebar.title("🏦 Gestion Financière")

    menu = st.sidebar.radio(
        "Navigation",
        [
            "🏠 Accueil",
            "💸 Ajouter Dépense (Scan)",
            "💵 Ajouter Revenu",
            "📊 Voir Transactions",
            "🔄 Transactions Récurrentes",
            "💼 Portefeuille",
            "📈 Investissements",
            "🔍 Analyses OCR",
        ]
    )

    # Routage vers les pages
    if menu == "🏠 Accueil":
        accueil.interface_accueil()

    elif menu == "💸 Ajouter Dépense (Scan)":
        scan_tickets.interface_ajouter_depenses_fusionnee()

    elif menu == "💵 Ajouter Revenu":
        scan_revenus.interface_ajouter_revenu()

    elif menu == "📊 Voir Transactions":
        transactions.interface_transactions_unifiee()

    elif menu == "🔄 Transactions Récurrentes":
        recurrences.interface_gerer_recurrences()

    elif menu == "💼 Portefeuille":
        portefeuille.interface_portefeuille()

    elif menu == "📈 Investissements":
        investissements.interface_voir_investissements_alpha()

    elif menu == "🔍 Analyses OCR":
        analytics.interface_ocr_analysis_complete()


if __name__ == "__main__":
    main()
'''

        # Sauvegarder l'ancien gestiov4.py si nécessaire
        if os.path.exists("gestiov4_new.py"):
            os.remove("gestiov4_new.py")

        with open("gestiov4_new.py", 'w', encoding='utf-8') as f:
            f.write(main_content)

        print("✅ Nouveau fichier principal créé : gestiov4_new.py")

    def migrate(self):
        """Lance la migration complète."""
        print("=" * 70)
        print("🚀 MIGRATION VERS ARCHITECTURE MODULAIRE")
        print("=" * 70)
        print()

        # 1. Créer sauvegarde
        print("📦 Étape 1 : Sauvegarde du fichier source")
        backup_file = self.create_backup()
        print()

        # 2. Lire le fichier source
        print("📖 Étape 2 : Lecture du fichier source")
        content = self.read_source_file()
        print(f"✅ {len(content)} caractères lus\n")

        # 3. Créer structure de dossiers
        print("📁 Étape 3 : Création de la structure de dossiers")
        self.create_directory_structure()
        print()

        # 4. Créer les modules
        print("🔧 Étape 4 : Extraction et création des modules")
        for module_path, functions in self.module_mapping.items():
            print(f"\n📄 Création de {module_path}")
            self.create_module_file(module_path, functions, content)

        # 5. Créer le fichier principal
        print("\n🎯 Étape 5 : Création du nouveau fichier principal")
        self.create_main_file()
        print()

        # 6. Résumé
        print("=" * 70)
        print("✅ MIGRATION TERMINÉE AVEC SUCCÈS !")
        print("=" * 70)
        print()
        print("📋 Prochaines étapes :")
        print("  1. Vérifier les modules créés dans core/, ocr/, services/, ui/, utils/")
        print("  2. Tester la nouvelle architecture : streamlit run gestiov4_new.py")
        print("  3. Si tout fonctionne, remplacer gestiov4.py par gestiov4_new.py")
        print(f"  4. La sauvegarde est disponible : {backup_file}")
        print()


if __name__ == "__main__":
    migrator = MigrationScript(source_file="gestiov4.py", backup=True)
    migrator.migrate()
