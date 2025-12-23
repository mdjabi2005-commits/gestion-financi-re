# Règles - Module Database

## 🎯 Responsabilité

Accès aux données, Repositories, Modèles

---

## 📋 Règles strictes

### 1. Pattern Repository OBLIGATOIRE

**❌ INTERDIT** - SQL direct dans services ou UI :
```python
# Dans services/ ou ui/
conn = get_db_connection()
cursor.execute("SELECT * FROM transactions")  # MAUVAIS !
```

**✅ CORRECT** - Via Repository :
```python
from modules.database.repositories import TransactionRepository

transactions = TransactionRepository.get_all()
```

---

### 2. Dataclasses pour les modèles

**Format obligatoire** :
```python
from dataclasses import dataclass
from datetime import date
from typing import Optional

@dataclass
class Transaction:
    id: Optional[int] = None
    type: str = ""
    date: date = None
    montant: float = 0.0
    categorie: str = ""
    sous_categorie: Optional[str] = None
    description: str = ""
    source: Optional[str] = "manuel"
```

---

### 3. Nommage des Repositories

**Format** : `{Entity}Repository`

```python
class TransactionRepository:
    @staticmethod
    def get_all() -> List[Transaction]:
        ...
    
    @staticmethod
    def get_by_id(transaction_id: int) -> Optional[Transaction]:
        ...
    
    @staticmethod
    def insert(transaction: Transaction) -> Optional[int]:
        ...
```

---

### 4. Gestion des connexions

**TOUJOURS** via context manager :

```python
from modules.database.connection import get_db_connection

def get_all() -> List[Transaction]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # ...
        return results
    # Fermeture automatique
```

---

### 5. Transactions SQL

**Pour opérations multiples** :

```python
with get_db_connection() as conn:
    try:
        conn.execute("BEGIN")
        # Opération 1
        # Opération 2
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise
```

---

## 🏗️ Comment ajouter

### Ajouter une nouvelle table

1. **Créer le modèle** dans `models.py`
```python
@dataclass
class NouvelleEntite:
    id: Optional[int] = None
    # champs...
```

2. **Créer le Repository** dans `repositories.py`
```python
class NouvelleEntiteRepository:
    @staticmethod
    def get_all() -> List[NouvelleEntite]:
        ...
```

3. **Migration SQL** dans `scripts/`
```sql
CREATE TABLE IF NOT EXISTS nouvelle_entite (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    -- colonnes...
);
```

4. **Tester**
```python
# tests/test_repositories.py
def test_nouvelle_entite_insert():
    ...
```

---

### Ajouter une méthode Repository

```python
class TransactionRepository:
    
    @staticmethod
    def get_by_category(categorie: str) -> List[Transaction]:
        """
        Récupère transactions par catégorie.
        
        Args:
            categorie: Nom catégorie (normalisé)
            
        Returns:
            Liste transactions
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM transactions 
                WHERE categorie = ?
            """, (categorie,))
            
            rows = cursor.fetchall()
            return [Transaction(*row) for row in rows]
```

---

## 🚨 Erreurs courantes

### Erreur #1 : Oubli normalisation

**Problème** :
```python
# ❌ Catégorie non normalisée
TransactionRepository.get_by_category("alimentation")  # Pas trouvé !
```

**Solution** :
```python
# ✅ Toujours normaliser avant requête
from modules.services.normalization import normalize_category

categorie = normalize_category("alimentation")  # "Alimentation"
TransactionRepository.get_by_category(categorie)
```

### Erreur #2 : SQL injection

**❌ DANGEREUX** :
```python
cursor.execute(f"SELECT * FROM transactions WHERE id = {user_input}")
```

**✅ SÛR** :
```python
cursor.execute("SELECT * FROM transactions WHERE id = ?", (user_input,))
```

### Erreur #3 : Connexion non fermée

**❌ MAUVAIS** :
```python
conn = get_db_connection()
cursor = conn.cursor()
# Oubli de fermer !
```

**✅ BON** :
```python
with get_db_connection() as conn:
    cursor = conn.cursor()
    # Fermeture automatique
```

---

## 📝 Checklist

Avant de commit :
- [ ] Utilise Repository (pas SQL direct)
- [ ] Dataclass créée pour nouveau modèle
- [ ] Context manager pour connexions
- [ ] Paramètres sécurisés (pas de f-string)
- [ ] Normalisation appliquée
- [ ] Tests écrits

---

## 🔗 Références

- [README module](../../v4/modules/database/README.md)
- [Guide implémentation](../guides/IMPLEMENTATION_GUIDE.md)
- [Erreurs courantes](../guides/COMMON_ERRORS.md)
