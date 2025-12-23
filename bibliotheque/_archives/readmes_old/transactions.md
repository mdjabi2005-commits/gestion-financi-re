# Module Transactions - Résumé

> 📖 **README complet** : [v4/domains/transactions/README.md](../../v4/domains/transactions/README.md)

---

## 🎯 Rôle du Module

**Gestion complète des transactions financières** : CRUD, validation, catégorisation.

**Cœur métier** : Enregistrer, modifier, supprimer, afficher transactions

---

## 📁 Architecture

```
domains/transactions/
├── models.py           # Transaction class (dataclass)
├── repository.py       # Data Access Layer (Repository pattern)
├── services.py         # Business Logic Layer
└── pages/
    ├── add.py          # UI ajout transaction
    ├── view.py         # UI voir/éditer transactions
    └── edit_mode.py    # Mode édition inline
```

---

## ⚙️ Fonctionnalités Clés

### 1. **CRUD Transactions**
```python
TransactionRepository.get_all()      # Lire toutes
TransactionRepository.insert()       # Créer
TransactionRepository.update()       # Modifier
TransactionRepository.delete()       # Supprimer
```

### 2. **Validation Données**
- Montant > 0
- Date valide
- Catégorie existe
- Type correct (dépense/revenu)

### 3. **Catégorisation**
- Catégories principales
- Sous-catégories
- Suggestion automatique (OCR)

### 4. **Gestion Fichiers Associés**
- Lien transaction ↔ ticket scanné
- Déplacement automatique
- Suppression synchronisée

### 5. **Récurrences (Futur)**
- Transactions récurrentes
- Génération automatique

---

## 🗂️ Modèle Données

```python
@dataclass
class Transaction:
    type: str                    # "dépense" ou "revenu"
    categorie: str
    sous_categorie: Optional[str]
    montant: float
    date: date
    description: Optional[str]
    source: str                  # "manuel", "OCR", "import_csv"
    id: Optional[int] = None
```

---

## 📊 Base de Données

**Table** : `transactions`

```sql
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY,
    type TEXT NOT NULL,
    categorie TEXT NOT NULL,
    sous_categorie TEXT,
    montant REAL NOT NULL,
    date TEXT NOT NULL,
    description TEXT,
    source TEXT DEFAULT 'manuel'
);
```

---

## 🎨 Interfaces Utilisateur

### Page Ajout (`add.py`)
- Formulaire saisie
- Validation en temps réel
- Suggestion catégorie (si OCR)

### Page Voir (`view.py`)
- Liste transactions (filtres)
- Édition inline (mode édition)
- Visualisation fichiers associés
- Stats rapides

### Mode Édition (`edit_mode.py`)
- `st.data_editor()` pour édition directe
- Modifications multiples
- Validation batch

---

## 🧪 Tests

- **6 tests intégration** (CRUD workflows)
- **Coverage** : ~80%

**Localisation** : `tests/test_integration/test_transaction_workflows.py`

---

## 🔗 Dépendances

**Interne** :
- `shared.database.get_db_connection()`
- `shared.exceptions.ValidationError()`
- `config.DB_PATH`

**Externe** :
- `pandas` (DataFrame manipulation)
- `streamlit` (UI)
- `sqlite3` (Database)

---

## 📝 Documentation Complète

**Pour détails techniques, exemples SQL, patterns Repository** :
👉 [v4/domains/transactions/README.md](../../v4/domains/transactions/README.md)

**Règles implémentation** :
👉 [../modules/database-rules.md](../modules/database-rules.md)

---

**Dernière mise à jour** : 20 décembre 2024
