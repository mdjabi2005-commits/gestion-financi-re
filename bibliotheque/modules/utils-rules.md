# Règles - Module Utils

## 🎯 Responsabilité

Fonctions utilitaires globales, helpers cross-module

---

## 📋 Règles strictes

### 1. Utils = Fonctions génériques

**✅ APPARTIENT à utils/** :
- Conversions de types
- Validation de données
- Formatage
- Helpers réutilisables partout

**❌ N'appartient PAS à utils/** :
- Logique métier spécifique → `services/`
- Helpers UI → `ui/helpers.py`
- Helpers database → `database/`

---

### 2. Pas de dépendances lourdes

**❌ ÉVITER dans utils/** :
```python
import streamlit as st  # UI
from modules.database import Repository  # Database
```

**✅ AUTORISÉ** :
```python
import pandas as pd  # Standard
from typing import Optional  # Standard
from datetime import date  # Standard
```

---

### 3. Fonctions pures privilégiées

**Préférer** :
```python
def safe_convert(value, target_type, default):
    """Pure - pas d'effet de bord"""
    try:
        return target_type(value)
    except:
        return default
```

---

### 4. Nommage descriptif

**Format** : `{verbe}_{objet}`

```python
def safe_convert(value, target_type, default)  # ✅
def validate_date(date_str)                    # ✅
def format_currency(amount)                    # ✅

def do_stuff(x)                                # ❌ Pas clair
```

---

## 🏗️ Comment ajouter

### Ajouter une fonction utilitaire

1. **Déterminer le fichier approprié**

```
utils/
├── converters.py       # Conversions de types
├── validators.py       # Validations
├── formatters.py       # Formatage affichage
└── helpers.py          # Autres utilitaires
```

2. **Créer fonction pure**

```python
# utils/converters.py

def safe_convert(value, target_type, default):
    """
    Convertit une valeur en tolérant les erreurs.
    
    Args:
        value: Valeur à convertir
        target_type: Type cible (int, float, str, etc.)
        default: Valeur par défaut si erreur
        
    Returns:
        Valeur convertie ou default
        
    Example:
        >>> safe_convert("42", int, 0)
        42
        >>> safe_convert("abc", int, 0)
        0
    """
    try:
        return target_type(value)
    except (ValueError, TypeError):
        return default
```

3. **Ajouter tests**

```python
# tests/test_converters.py

def test_safe_convert_success():
    assert safe_convert("42", int, 0) == 42

def test_safe_convert_failure():
    assert safe_convert("abc", int, 0) == 0
```

---

## 🎯 Utils existants

### converters.py

**Fonctions** :
```python
def safe_convert(value, target_type, default)
def safe_date_convert(date_str) -> Optional[date]
```

**Usage** :
```python
from modules.utils.converters import safe_convert

montant = safe_convert(user_input, float, 0.0)
```

---

### validators.py

**Fonctions** :
```python
def validate_transaction(transaction: dict) -> Tuple[bool, str]
def validate_date(date_str: str) -> bool
def validate_amount(amount: float) -> bool
```

**Usage** :
```python
from modules.utils.validators import validate_transaction

valid, error = validate_transaction(data)
if not valid:
    show_error(error)
```

---

## 🚨 Erreurs courantes

### Erreur #1 : Logique métier dans utils

**Problème** :
```python
# ❌ Dans utils/helpers.py
def calculate_uber_tax(montant: float) -> float:
    return montant * 0.21  # Logique métier !
```

**Solution** :
```python
# ✅ Dans services/revenue_service.py
def calculate_uber_tax(montant: float) -> float:
    return montant * 0.21
```

### Erreur #2 : Import circulaire

**Problème** :
```python
# utils/helpers.py
from modules.services import normalize_category  # Risque !
```

**Solution** : Si utils dépend de services, c'est que ce n'est pas un util !

### Erreur #3 : Fonction trop spécifique

**Problème** :
```python
# utils/helpers.py
def format_transaction_for_lydia_pdf(trans):
    # Trop spécifique !
```

**Solution** :
```python
# services/pdf_service.py
def format_transaction_for_lydia_pdf(trans):
    # Logique métier spécifique
```

---

## 📝 Checklist

Avant d'ajouter une fonction dans utils :
- [ ] Est-ce vraiment générique ?
- [ ] Pas de dépendance services/database/ui ?
- [ ] Fonction pure (si possible) ?
- [ ] Nom descriptif ?
- [ ] Docstring complète ?
- [ ] Tests créés ?
- [ ] Exemple d'usage ?

---

## 🎓 Principe

> "Si c'est spécifique à un domaine métier, ce n'est pas un util."

**Exemples** :
- ✅ `safe_convert()` - Générique
- ✅ `validate_date()` - Générique
- ❌ `calculate_uber_tax()` - Spécifique
- ❌ `build_fractal_hierarchy()` - Spécifique

---

## 🔗 Références

- [README module](../../v4/modules/utils/README.md)
- [Guide implémentation](../guides/IMPLEMENTATION_GUIDE.md)
- [Services rules](services-rules.md)
