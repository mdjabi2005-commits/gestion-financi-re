# 📐 Architecture Modulaire - Gestion Financière v4

## 🎯 Vue d'ensemble

L'application a été restructurée en architecture modulaire pour faciliter la maintenance, le débogage et l'évolution du code.

**Avant :** 1 fichier monolithique de 6846 lignes
**Après :** Architecture modulaire avec 27 fichiers organisés

---

## 📁 Structure des Dossiers

```
gestion-financi-re/
├── gestiov4.py                 # ⚠️ ANCIEN fichier (sauvegarde)
├── gestiov4_new.py             # ✅ NOUVEAU point d'entrée (180 lignes)
├── config.py                   # Configuration (chemins, constantes)
├── migrate_to_modular.py       # Script de migration automatique
│
├── core/                       # 🏗️ Logique métier principale (744 lignes)
│   ├── __init__.py
│   ├── database.py             # Connexion DB, init, migrations (131 lignes)
│   ├── transactions.py         # CRUD transactions (188 lignes)
│   ├── budget.py               # Analyses budgétaires (301 lignes)
│   └── recurrences.py          # Gestion récurrences (123 lignes)
│
├── ocr/                        # 🔍 OCR et parsing de documents (981 lignes)
│   ├── __init__.py
│   ├── engine.py               # Moteur OCR, extraction texte (91 lignes)
│   ├── parsers.py              # Parsing tickets, PDFs (390 lignes)
│   ├── logging.py              # Logs et statistiques OCR (302 lignes)
│   └── patterns.py             # Analyse patterns OCR (198 lignes)
│
├── services/                   # ⚙️ Services métier (241 lignes)
│   ├── __init__.py
│   ├── file_manager.py         # Gestion fichiers (186 lignes)
│   └── uber_tax.py             # Calculs Uber (55 lignes)
│
├── ui/                         # 🎨 Interface utilisateur (4565 lignes)
│   ├── __init__.py
│   ├── components.py           # Composants réutilisables (227 lignes)
│   └── pages/                  # Pages de l'application
│       ├── __init__.py
│       ├── accueil.py          # Page d'accueil (428 lignes)
│       ├── transactions.py     # Gestion transactions (673 lignes)
│       ├── portefeuille.py     # Budgets et objectifs (1408 lignes)
│       ├── scan_tickets.py     # Scan dépenses (263 lignes)
│       ├── scan_revenus.py     # Scan revenus (280 lignes)
│       ├── recurrences.py      # Transactions récurrentes (397 lignes)
│       ├── analytics.py        # Analyses OCR (790 lignes)
│       └── investissements.py  # Suivi investissements (98 lignes)
│
└── utils/                      # 🛠️ Utilitaires (154 lignes)
    ├── __init__.py
    ├── converters.py           # Conversions de données (112 lignes)
    └── validators.py           # Validation (42 lignes)
```

---

## 🔧 Description des Modules

### 📦 core/ - Logique Métier

**database.py**
- `get_db_connection()` - Connexion à SQLite
- `init_db()` - Initialisation des tables
- `migrate_database_schema()` - Migrations automatiques

**transactions.py**
- `load_transactions()` - Chargement transactions
- `load_recurrent_transactions()` - Transactions récurrentes
- `insert_transaction_batch()` - Insertion par lot
- `validate_transaction_data()` - Validation données

**budget.py**
- `analyze_exceptional_expenses()` - Analyse dépenses exceptionnelles
- `analyze_budget_history()` - Historique budgets
- `calculate_months_in_period()` - Calcul période
- `get_period_start_date()` - Date début période

**recurrences.py**
- `backfill_recurrences_to_today()` - Génération récurrences
- `normalize_recurrence_column()` - Normalisation

### 🔍 ocr/ - OCR et Parsing

**engine.py**
- `full_ocr()` - OCR complet sur image
- `extract_text_from_pdf()` - Extraction texte PDF
- `nettoyer_montant()` - Nettoyage montants

**parsers.py**
- `parse_ticket_metadata()` - Parsing tickets
- `parse_uber_pdf()` - Parsing relevés Uber
- `parse_fiche_paie()` - Parsing fiches de paie
- `parse_pdf_dispatcher()` - Routage parsing PDFs

**logging.py**
- `log_ocr_scan()` - Journalisation scans
- `get_ocr_performance_report()` - Rapport performance
- `get_scan_history()` - Historique scans

**patterns.py**
- `extract_patterns_from_text()` - Extraction patterns
- `diagnose_ocr_patterns()` - Diagnostic patterns
- `calculate_pattern_reliability()` - Fiabilité patterns

### ⚙️ services/ - Services

**file_manager.py**
- `trouver_fichiers_associes()` - Recherche fichiers
- `supprimer_fichiers_associes()` - Suppression fichiers
- `deplacer_fichiers_associes()` - Déplacement fichiers
- `move_ticket_to_sorted()` - Archivage tickets

**uber_tax.py**
- `apply_uber_tax()` - Application charges Uber
- `process_uber_revenue()` - Traitement revenus Uber

### 🎨 ui/ - Interface

**components.py**
- `toast_success()`, `toast_warning()`, `toast_error()` - Notifications
- `afficher_carte_transaction()` - Carte transaction
- `afficher_documents_associes()` - Documents liés
- `get_badge_html()`, `get_badge_icon()` - Badges

**pages/** - Pages Streamlit
- Chaque page est une interface complète Streamlit
- Import dans gestiov4_new.py pour navigation

### 🛠️ utils/ - Utilitaires

**converters.py**
- `safe_convert()` - Conversion sécurisée
- `safe_date_convert()` - Conversion dates
- `normaliser_date()` - Normalisation dates

**validators.py**
- `validate_transaction_data()` - Validation transactions
- `correct_category_name()` - Correction noms catégories

---

## 🚀 Utilisation

### Lancer l'application avec la nouvelle architecture

```bash
streamlit run gestiov4_new.py
```

### Retour à l'ancienne version (si nécessaire)

```bash
streamlit run gestiov4.py
```

### Sauvegarde

La sauvegarde de l'ancien fichier est disponible dans :
- `gestiov4.py.backup_YYYYMMDD_HHMMSS`

---

## ✅ Avantages de cette Architecture

1. **🔍 Lisibilité** : Code organisé par domaine fonctionnel
2. **🐛 Débogage** : Isolation des bugs par module
3. **♻️ Réutilisabilité** : Fonctions accessibles facilement
4. **✅ Tests** : Tests unitaires par module
5. **👥 Collaboration** : Travail simultané sur différents modules
6. **⚡ Performance** : Imports sélectifs
7. **📚 Documentation** : Structure auto-documentée

---

## 🔄 Migration

Le script `migrate_to_modular.py` a automatiquement :
1. Créé la structure de dossiers
2. Extrait les fonctions du fichier monolithique
3. Organisé les fonctions dans les modules appropriés
4. Généré les imports nécessaires
5. Créé un nouveau point d'entrée minimaliste

---

## 📝 Prochaines Étapes

### Si la nouvelle architecture fonctionne :

1. Tester toutes les fonctionnalités
2. Remplacer `gestiov4.py` par `gestiov4_new.py`
3. Supprimer les sauvegardes après validation

```bash
mv gestiov4.py gestiov4_old.py
mv gestiov4_new.py gestiov4.py
```

### Développement futur :

- Ajouter des tests unitaires dans `tests/`
- Documenter chaque module avec Sphinx
- Créer des fixtures pour les tests
- Ajouter du logging applicatif

---

## 📞 Support

En cas de problème :
1. Vérifier les logs d'erreur
2. Consulter ce document
3. Restaurer depuis la sauvegarde si nécessaire

---

*Document généré automatiquement lors de la migration modulaire*
*Date : 2025-11-16*
