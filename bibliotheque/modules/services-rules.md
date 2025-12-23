# Règles - Module Services

## 🎯 Responsabilité

Logique métier, orchestration, business logic

---

## 📋 Règles strictes

### 1. Services = Logique métier pure

**❌ INTERDIT** :
- Accès direct à la base de données (utiliser Repository)
- Code UI (Streamlit)
- Configuration hard-codée

**✅ AUTORISÉ** :
- Orchestration entre modules
- Transformations de données
- Logique métier complexe
- Validation business

---

### 2. Nommage des services

**Format** : `{domain}_service.py`

```
services/
├── fractal_service.py        # Hiérarchie Sunburst
├── revenue_service.py         # Logique revenus Uber
├── file_service.py            # Gestion fichiers
├── normalization.py           # Normalisation données
└── recurrence_service.py      # Récurrences
```

---

### 3. Fonctions pures quand possible

**Préférer** :
```python
def normalize_category(category: str) -> str:
    """Fonction pure - pas d'effet de bord"""
    return category.strip().title()
```

**Éviter** :
```python
def normalize_category(category: str) -> None:
    """Modifie état global - NON !"""
    global_category = category.strip().title()
```

---

### 4. Normalisation OBLIGATOIRE

**TOUJOURS normaliser** avant insertion :

```python
from modules.services.normalization import normalize_category, normalize_subcategory

# ✅ BON
categorie = normalize_category(user_input.strip())
sous_categorie = normalize_subcategory(user_input.strip())

# ❌ MAUVAIS
categorie = user_input  # Risque de doublons !
```

---

## 🏗️ Comment ajouter

### Créer un nouveau service

1. **Créer fichier** `modules/services/mon_service.py`
```python
"""
Mon Service - Description

Responsabilité : [Ce que fait le service]
"""

from modules.database.repositories import TransactionRepository
from modules.services.normalization import normalize_category

def ma_fonction_metier(data):
    """
    Description claire.
    
    Args:
        data: Description
        
    Returns:
        Résultat transformé
        
    Raises:
        ValueError: Si données invalides
    """
    # Validation
    if not data:
        raise ValueError("Data required")
    
    # Transformation
    normalized = normalize_category(data)
    
    # Orchestration
    result = TransactionRepository.get_by_category(normalized)
    
    return result
```

2. **Exporter dans `__init__.py`**
```python
from .mon_service import ma_fonction_metier
```

3. **Utiliser dans UI ou autres services**
```python
from modules.services.mon_service import ma_fonction_metier

result = ma_fonction_metier(user_data)
```

---

### Ajouter logique à un service existant

**Exemple** : Nouvelle règle de normalisation

```python
# modules/services/normalization.py

def normalize_amount(amount: float) -> float:
    """
    Normalise un montant.
    
    Args:
        amount: Montant brut
        
    Returns:
        Montant arrondi à 2 décimales
        
    Example:
        >>> normalize_amount(10.12345)
        10.12
    """
    return round(amount, 2)
```

---

## 🎯 Services existants

### fractal_service.py
**Responsabilité** : Construction hiérarchie Sunburst

**Fonction principale** :
```python
def build_fractal_hierarchy() -> Dict:
    """Construit hiérarchie financière complète"""
```

**Usage** :
```python
hierarchy = build_fractal_hierarchy()
# Retourne dict avec codes, labels, values, colors
```

---

### revenue_service.py
**Responsabilité** : Logique revenus Uber (taxe 21%)

**Fonctions** :
```python
def is_uber_transaction(categorie: str, description: str) -> bool
def process_uber_revenue(transaction: dict, apply_tax: bool) -> Tuple[dict, str]
```

---

### file_service.py
**Responsabilité** : Gestion fichiers associés

**Fonctions** :
```python
def trouver_fichiers_associes(transaction: dict) -> List[str]
def deplacer_fichiers_associes(old_trans: dict, new_trans: dict)
def supprimer_fichiers_associes(transaction: dict)
```

---

### normalization.py
**Responsabilité** : Normalisation chaînes

**Fonctions** :
```python
def normalize_category(category: str) -> str
def normalize_subcategory(subcategory: str) -> str
```

**Règle** : Title Case avec exceptions (PDF, OCR, CSV)

---

## 🚨 Erreurs courantes

### Erreur #1 : Oubli normalisation

**Impact** : Doublons dans base ("alimentation" vs "Alimentation")

**Solution** : TOUJOURS normaliser avant insertion

### Erreur #2 : SQL dans services

**Problème** :
```python
# ❌ Dans file_service.py
conn = get_db_connection()  # INTERDIT !
```

**Solution** :
```python
# ✅ Utiliser Repository
from modules.database.repositories import TransactionRepository
transactions = TransactionRepository.get_all()
```

### Erreur #3 : Logique UI dans services

**Problème** :
```python
# ❌ Dans normalization.py
import streamlit as st  # INTERDIT !
st.success("Normalisé")
```

**Solution** :
```python
# ✅ Retourner résultat, UI affiche
return normalized_value
```

---

## 📝 Checklist

Avant de commit un service :
- [ ] Pas de SQL direct (utilise Repository)
- [ ] Pas de code UI (Streamlit)
- [ ] Fonctions pures quand possible
- [ ] Docstrings complètes
- [ ] Validation des entrées
- [ ] Gestion des erreurs
- [ ] Tests unitaires créés

---

## 🔗 Références

- [README module](../../v4/modules/services/README.md)
- [Guide implémentation](../guides/IMPLEMENTATION_GUIDE.md)
- [Database rules](database-rules.md)
