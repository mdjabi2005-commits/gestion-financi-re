# Module Shared - Résumé

> 📖 **README complet** : [v4/shared/README.md](../../v4/shared/README.md)

---

## 🎯 Rôle du Module

**Infrastructure partagée** par tous les modules : logging, exceptions, database, utils.

**Code réutilisable** : Évite duplication, garantit cohérence

---

## 📁 Architecture

```
shared/
├── logging_config.py      # Logging centralisé
├── exceptions.py          # Exceptions personnalisées
├── database.py            # Connection DB
├── utils.py               # Fonctions helpers
├── ui.py                  # Composants UI réutilisables
└── services/
    └── files.py           # Gestion fichiers
```

---

## ⚙️ Fonctionnalités Clés

### 1. **Logging Centralisé** 🎯

```python
from shared.logging_config import get_logger

logger = get_logger(__name__)
logger.info("Message")
logger.error("Erreur", exc_info=True)
```

**Features** :
- Logs console + fichier (`data/logs/gestio_app.log`)
- Format standardisé
- Rotation automatique (10MB, 5 backup)
- Niveaux configurables

---

### 2. **Exceptions Personnalisées** 🔴

```python
from shared.exceptions import (
    DatabaseError,
    ValidationError,
    OCRError,
    ConfigurationError,
    FileOperationError,
    BusinessLogicError
)
```

**Usage** :
```python
if montant <= 0:
    raise ValidationError("Montant doit être > 0")
```

**Hiérarchie** :
```
GestioException (base)
├── DatabaseError
├── ValidationError
├── OCRError
├── ConfigurationError
├── FileOperationError
└── BusinessLogicError
```

---

### 3. **Database Connection**

```python
from shared.database import get_db_connection

conn = get_db_connection()
cursor = conn.cursor()
# ...
conn.close()
```

**Features** :
- Connection unique (singleton pattern)
- Gestion erreurs
- Path configurable (TEST_MODE support)

---

### 4. **Utils - Fonctions Helpers**

```python
from shared.utils import (
    safe_convert,           # str → float (safe)
    safe_date_convert,      # str → date (safe)
    format_currency,        # float → "12.50€"
    validate_date_range,    # Validation dates
    # ...
)
```

**30+ fonctions** utilitaires

---

### 5. **UI Components**

```python
from shared.ui import (
    toast_success,          # ✅ Notification succès
    toast_error,            # ❌ Notification erreur
    toast_warning,          # ⚠️ Notification warning
    load_transactions,      # Charge transactions (cached)
    # ...
)
```

---

### 6. **File Services**

```python
from shared.services.files import (
    trouver_fichiers_associes,    # Trouve tickets associés
    deplacer_fichier_transaction,  # Déplace ticket
    # ...
)
```

---

## 📊 Statistiques

**logging_config.py** :
- 1 logger configuré
- 2 handlers (console + file)
- Format : `%(asctime)s - %(name)s - %(levelname)s - %(message)s`

**exceptions.py** :
- 1 base exception
- 6 exceptions spécialisées

**utils.py** :
- ~30 fonctions helpers
- Conversion, validation, formatting

---

## 🧪 Tests

- **8 tests unitaires** (Utils)
- **Coverage** : ~90%

**Localisation** : `tests/test_shared/`

---

## 🎯 Principes Design

### DRY (Don't Repeat Yourself)
Tout code utilisé 2+ fois → shared/

### Single Responsibility
Chaque module = 1 responsabilité claire

### Dependency Injection
Modules dépendent de shared/, jamais l'inverse

---

## 📝 Documentation Complète

**Pour détails API, exemples complets, architecture interne** :
👉 [v4/shared/README.md](../../v4/shared/README.md)

**Règles implémentation** :
👉 [../modules/utils-rules.md](../modules/utils-rules.md)

---

**Dernière mise à jour** : 20 décembre 2024
