# Shared Database

Gestion de la base de données SQLite partagée entre tous les modules.

## Structure

```
shared/database/
├── __init__.py
├── connection.py    # Gestion des connexions DB
└── schema.py        # Schéma et migrations
```

## 📦 Dépendances Externes

| Bibliothèque | Utilisation | Version Min |
|-------------|-------------|-------------|
| `sqlite3` | Base de données | Inclus dans Python |

**Aucune installation requise** - sqlite3 est inclus dans la bibliothèque standard Python.

---

## Responsabilités

**Connection** (`connection.py`):
- Gestion du pool de connexions
- Configuration timeout et pragma
- Fermeture propre des connexions

**Schema** (`schema.py`):
- Initialisation base de données
- Migrations de schéma
- Création des tables

---

## Usage

### Obtenir une Connexion

```python
from shared.database import get_db_connection

# Connexion automatique avec configuration optimale
conn = get_db_connection()
cursor = conn.cursor()

# Utiliser la connexion
cursor.execute("SELECT * FROM transactions")

# Commit et fermeture
conn.commit()
conn.close()
```

### Initialiser la Base

```python
from shared.database import init_db

# Crée toutes les tables nécessaires
init_db()
```

### Migration de Schéma

```python
from shared.database import migrate_database_schema

# Applique migrations si nécessaire
migrate_database_schema()
```

---

## Configuration

Le chemin de la base de données est défini dans `config/database_config.py`:

```python
DATABASE_PATH = "data/transactions.db"
DATABASE_TIMEOUT = 30.0  # secondes
```

---

## Tables Principales

| Table | Description |
|-------|-------------|
| `transactions` | Toutes les transactions financières |
| `echeances` | Échéances ponctuelles et fixes  |
| `budgets_categories` | Budgets mensuels par catégorie |
| `objectifs_financiers` | Objectifs financiers |
| `recurrences` | Abonnements et salaires récurrents |
| `ocr_logs` | Logs des scans OCR |

---

## Principes

**Singleton Connection**: 
- Une connexion réutilisable par thread
- Évite les multiples ouvertures

**Sécurité**:
- Toujours utiliser des paramètres préparés
- Éviter les injections SQL

**Performance**:
- WAL mode activé automatiquement
- Pragma optimize au démarrage
