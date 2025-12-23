# Guide d'Implémentation - Gestio V4

## 🎯 Objectif de ce document

Ce document définit les **règles strictes** à respecter lors de l'ajout ou modification de code dans le projet Gestio V4.  
**Public cible** : IA assistantes, nouveaux développeurs, contributeurs externes.

---

## 📋 Règles générales

### 1. Architecture en couches - STRICTEMENT RESPECTÉE

```
UI Layer (modules/ui/)
    ↓ Peut importer
Services Layer (modules/services/)
    ↓ Peut importer
Database Layer (modules/database/)
    ↓ Peut importer
Config Layer (config/)
```

**❌ INTERDIT** :
- `database/` ne peut PAS importer depuis `services/` ou `ui/`
- `services/` ne peut PAS importer depuis `ui/`
- `config/` ne peut PAS importer depuis aucun module

**✅ AUTORISÉ** :
- `ui/` peut importer depuis `services/`, `database/`, `config/`, `utils/`
- `services/` peut importer depuis `database/`, `config/`, `utils/`
- `database/` peut importer depuis `config/`, `utils/`

---

## 📦 Règles d'imports

### Import absolu obligatoire

**❌ INTERDIT** :
```python
from ..database import TransactionRepository  # Relatif
import database  # Ambigu
```

**✅ CORRECT** :
```python
from modules.database.repositories import TransactionRepository
from modules.services.normalization import normalize_category
from config import DB_PATH
```

### Ordre des imports

**TOUJOURS dans cet ordre** :
```python
# 1. Imports standard Python
import os
import pandas as pd
from datetime import date
from typing import Optional, Dict

# 2. Imports bibliothèques externes
import streamlit as st
import plotly.graph_objects as go

# 3. Imports du projet (config en premier)
from config import DB_PATH, CATEGORIES_DEPENSES
from modules.database.repositories import TransactionRepository
from modules.services.normalization import normalize_category
from modules.ui.helpers import load_transactions
```

### Imports conditionnels

**Quand utiliser** : Pour éviter les imports circulaires

**✅ CORRECT** :
```python
def interface_transactions_simplifiee():
    # Import local pour éviter import circulaire
    from modules.ui.pages.scanning import process_all_tickets_in_folder
    process_all_tickets_in_folder()
```

---

## 🏗️ Structure des modules

### Règle 1 : Un fichier = Une responsabilité

**❌ INTERDIT** :
- Fichier de 1000+ lignes avec plusieurs responsabilités
- Mélanger UI + logique métier + accès base de données

**✅ CORRECT** :
```
modules/ui/pages/
├── transactions_view.py          # Visualisation uniquement
├── transactions_add.py           # Ajout uniquement  
└── transactions_helpers.py       # Helpers partagés
```

### Règle 2 : Nommage cohérent

**Fichiers** :
- Modules : `snake_case.py` (ex: `transaction_service.py`)
- Classes : `PascalCase` (ex: `TransactionRepository`)
- Fonctions : `snake_case` (ex: `load_transactions()`)

**Fonctions UI Streamlit** :
- Préfixe `interface_` pour les pages complètes
- Préfixe `render_` pour les composants
```python
def interface_voir_transactions():  # Page complète
def render_calendar(df):            # Composant
```

---

## 🗄️ Règles Base de Données

### Utiliser TOUJOURS le Repository Pattern

**❌ INTERDIT - SQL direct dans l'UI** :
```python
# Dans transactions.py
conn = get_db_connection()
cursor = conn.cursor()
cursor.execute("SELECT * FROM transactions")  # MAUVAIS !
```

**✅ CORRECT - Via Repository** :
```python
from modules.database.repositories import TransactionRepository

transactions = TransactionRepository.get_all()
```

### Normalisation obligatoire

**TOUJOURS normaliser** catégories et sous-catégories avant insertion :

```python
from modules.services.normalization import normalize_category, normalize_subcategory

transaction_data = {
    "categorie": normalize_category(cat.strip()),      # OBLIGATOIRE
    "sous_categorie": normalize_subcategory(subcat.strip())  # OBLIGATOIRE
}
```

---

## 🎨 Règles UI (Streamlit)

### Session State - Nommage conventionnel

**Format** : `{page}_{variable}_{type}`

```python
# ✅ BON
st.session_state.transactions_edit_mode = False
st.session_state.cal_transactions_start_date = date.today()

# ❌ MAUVAIS
st.session_state.edit = False  # Trop générique
st.session_state.d = date.today()  # Pas clair
```

### Navigation entre pages

**TOUJOURS utiliser** `requested_page` :

```python
# ✅ CORRECT
if st.button("Voir Transactions"):
    st.session_state.requested_page = "📊 Voir Transactions"
    st.rerun()
```

**Géré dans `main.py`** AVANT le rendu :
```python
# Dans main.py - AVANT d'afficher la page
if 'requested_page' in st.session_state:
    current_page = st.session_state.requested_page
    del st.session_state.requested_page
    st.rerun()
```

---

## 🧪 Tests avec pytest

### Structure obligatoire

```
tests/
├── __init__.py
├── test_repositories.py      # Tests base de données
├── test_services.py           # Tests logique métier
└── test_normalization.py      # Tests normalisation
```

### Format des tests

```python
def test_{fonction}_{scenario}():
    """Description claire du test"""
    # Arrange
    input_data = "alimentation"
    
    # Act
    result = normalize_category(input_data)
    
    # Assert
    assert result == "Alimentation"
```

### Lancer les tests

```bash
# Tous les tests
pytest tests/

# Un fichier spécifique
pytest tests/test_normalization.py

# Avec verbose
pytest tests/ -v
```

---

## 📁 Gestion des fichiers

### Chemins - TOUJOURS depuis config

**❌ INTERDIT** :
```python
path = "c:/Users/djabi/data/tickets"  # Dur-codé !
```

**✅ CORRECT** :
```python
from config import TO_SCAN_DIR
path = TO_SCAN_DIR
```

### Manipulation fichiers

**TOUJOURS via `file_service`** :

```python
from modules.services.file_service import (
    deplacer_fichiers_associes,
    trouver_fichiers_associes
)

# ✅ BON
fichiers = trouver_fichiers_associes(transaction_dict)

# ❌ MAUVAIS - Manipulation directe
import os
os.listdir(some_path)  # Ne pas faire !
```

---

## 🔧 Règles de refactoring

### Avant d'extraire une fonction

**Checklist** :
1. ✅ La fonction fait plus de 50 lignes ?
2. ✅ Elle est réutilisée ailleurs ?
3. ✅ Elle a une responsabilité unique ?
4. ✅ Tu peux la nommer clairement ?

Si 3/4 réponses = OUI → Extraire

### Extraire progressivement

**❌ INTERDIT** : Tout casser et reconstruire

**✅ CORRECT** : Approche incrémentale
1. Créer nouveau fichier
2. Copier fonction
3. Remplacer par import
4. Tester
5. Répéter
6. Supprimer ancien fichier

---

## 🚨 Erreurs courantes à éviter

### 1. Imports circulaires

**Symptôme** :
```
ImportError: cannot import name 'X' from partially initialized module
```

**Solution** : Import conditionnel ou restructurer

### 2. Duplication de code

**Règle** : Si tu copies-colles 3 fois → Créer une fonction

### 3. Fichiers trop gros

**Limite** : 500 lignes max par fichier  
**Action** : Découper si dépassé

### 4. Oublier la normalisation

**Toujours normaliser** avant insertion :
```python
categorie = normalize_category(cat.strip())  # OBLIGATOIRE
```

---

## 📝 Documentation obligatoire

### Docstrings pour fonctions publiques

```python
def interface_voir_transactions() -> None:
    """
    Interface de visualisation des transactions.
    
    Fonctionnalités :
    - Arbre dynamique Sunburst pour navigation
    - Calendrier pour filtrage par date
    - Mode édition avec st.data_editor
    
    Returns:
        None
    """
```

### Commentaires pour logique complexe

```python
# Filtrer par type ET catégorie ET sous-catégorie pour éviter tout conflit
df_filtered = df[
    (df['type'].str.lower() == transaction_type.lower()) &
    (df['categorie'].str.lower() == category_name.lower()) &
    (df['sous_categorie'].str.lower() == subcategory_name.lower())
]
```

---

## ✅ Checklist avant commit

- [ ] Tous les imports sont absolus
- [ ] L'architecture en couches est respectée
- [ ] Les catégories sont normalisées
- [ ] Pas de SQL direct (utilise Repository)
- [ ] Fichier < 500 lignes
- [ ] Docstrings ajoutées
- [ ] Tests pytest créés (si logique métier)
- [ ] Application testée manuellement
- [ ] Aucun chemin dur-codé

---

## 🎓 Principes de conception

1. **DRY** - Don't Repeat Yourself
2. **SOLID** - Single Responsibility Principle surtout
3. **KISS** - Keep It Simple, Stupid
4. **Separation of Concerns** - UI ≠ Business Logic ≠ Data Access

---

## 📞 Contact

En cas de doute sur une règle, consulter :
- README.md du module concerné ou help pour regarder les librairies utilisées en détail
- Regarder le dossier erreurs pour erreurs courantes
- Les fichiers existants comme exemple
