# Script pour ajouter frontmatter YAML aux fichiers restants
# Phase 2.1 - Standardisation bibliothèque

frontmatter_configs = {
    "streamlit.md": """---
type: guide_librairie
library: streamlit
difficulty: beginner
tags: [ui, web, interface, dashboard]
phase: 1
last_updated: 2024-12-14
estimated_reading: 15min
status: active
related:
  - help/plotly.md
  - help/pandas.md
---""",
    
    "sqlite3.md": """---
type: guide_librairie
library: sqlite3
difficulty: intermediate
tags: [database, sql, persistence]
phase: 1
last_updated: 2024-12-14
estimated_reading: 15min
status: active
related:
  - modules/database-rules.md
  - help/pandas.md
---""",
    
    "08_phase3_build_installation.md": """---
type: walkthrough
phase: 3
date: 2024-12-22
tags: [build, installation, multi-os, pyinstaller]
difficulty: advanced
estimated_reading: 30min
status: active
related:
  - guides/BUILD.md
  - ajouts/04_amelioration_ocr.md
---""",
    
    "COMMON_ERRORS.md": """---
type: erreur
difficulty: intermediate
tags: [debugging, troubleshooting, solutions]
last_updated: 2024-12-18
estimated_reading: 25min
status: active
total_errors: 7
related:
  - erreurs/phase1_erreurs_corrections.md
  - erreurs/phase2_erreurs_corrections.md
---""",
    
    "ARCHITECTURE.md": """---
type: guide_general
difficulty: intermediate
tags: [architecture, structure, patterns, design]
last_updated: 2024-12-16
estimated_reading: 30min
status: active
related:
  - guides/IMPLEMENTATION_GUIDE.md
  - modules/INVENTAIRE_LIBRAIRIES.md
---"""
}

print("Frontmatter configs ready for manual application")
print(f"Total files: {len(frontmatter_configs)}")
