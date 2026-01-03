---
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
---

# 📚 Bibliothèque : SQLite3

## 🎯 Qu'est-ce que SQLite ?

**SQLite** est une base de données **SQL légère et embarquée** - un seul fichier `.db` contient toute la base. Pas de serveur à lancer, idéal pour applications desktop et petits projets.

**Site officiel** : https://www.sqlite.org  
**Documentation Python** : https://docs.python.org/3/library/sqlite3.html

---

## 💡 Pourquoi SQLite dans notre projet ?

1. **Simplicité** : Un seul fichier `finances.db`
2. **Pas de serveur** : Fonctionne directement
3. **Performance** : Rapide pour notre usage
4. **Portable** : Copier le fichier = backup complet
5. **Intégré Python** : Module `sqlite3` natif

---

## 🔧 Concepts de base

### 1. Connexion

```python
import sqlite3

# Ouvrir/créer une base de données
conn = sqlite3.connect('finances.db')

# Créer un curseur
cursor = conn.cursor()

# Exécuter des requêtes...

# Fermer
conn.close()
```

**Dans notre app** (`connection.py`) :
```python
def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH, timeout=30.0)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")  # Mode WAL pour concurrence
    conn.row_factory = sqlite3.Row  # Retourner dicts
    return conn
```

---

### 2. Créer une table

```python
cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    categorie TEXT NOT NULL,
    montant REAL NOT NULL,
    date TEXT NOT NULL
)
""")

conn.commit()  # Sauvegarder les changements
```

**Dans notre app** (`schema.py`) :
```python
TRANSACTIONS_SCHEMA = """
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    categorie TEXT NOT NULL,
    sous_categorie TEXT,
    description TEXT,
    montant REAL NOT NULL,
    date TEXT NOT NULL,
    source TEXT DEFAULT 'Manuel',
    recurrence TEXT,
    date_fin TEXT
)
"""
```

---

### 3. Insérer des données

**INSERT simple** :
```python
cursor.execute("""
    INSERT INTO transactions (type, categorie, montant, date)
    VALUES (?, ?, ?, ?)
""", ("Dépense", "Alimentation", 45.50, "2025-01-15"))

conn.commit()

# Récupérer l'ID auto-généré
transaction_id = cursor.lastrowid
print(f"Transaction créée avec ID: {transaction_id}")
```

**INSERT multiple** :
```python
data = [
    ("Dépense", "Transport", 15.00, "2025-01-15"),
    ("Revenu", "Salaire", 2500.00, "2025-01-01")
]

cursor.executemany("""
    INSERT INTO transactions (type, categorie, montant, date)
    VALUES (?, ?, ?, ?)
""", data)

conn.commit()
```

**Dans notre app** (`repositories.py`) :
```python
def insert(transaction: Transaction):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO transactions 
        (type, categorie, sous_categorie, description, montant, date, source)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        transaction.type,
        normalize_category(transaction.categorie),
        normalize_subcategory(transaction.sous_categorie),
        transaction.description,
        transaction.montant,
        transaction.date.isoformat(),
        transaction.source
    ))
    
    conn.commit()
    transaction_id = cursor.lastrowid
    conn.close()
    
    return transaction_id
```

---

### 4. Lire des données

**SELECT simple** :
```python
cursor.execute("SELECT * FROM transactions")
rows = cursor.fetchall()  # Toutes les lignes

for row in rows:
    print(row)
```

**SELECT avec filtre** :
```python
cursor.execute("""
    SELECT * FROM transactions
    WHERE type = ? AND montant > ?
""", ("Dépense", 100))

rows = cursor.fetchall()
```

**SELECT une seule ligne** :
```python
cursor.execute("""
    SELECT * FROM transactions WHERE id = ?
""", (42,))

row = cursor.fetchone()  # Une seule ligne ou None

if row:
    print(f"Transaction: {row['description']}")
```

**Dans notre app** :
```python
def get_by_id(transaction_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM transactions WHERE id = ?
    """, (transaction_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return Transaction.from_row(row)
    return None
```

---

### 5. Mettre à jour

```python
cursor.execute("""
    UPDATE transactions
    SET montant = ?, description = ?
    WHERE id = ?
""", (52.50, "Montant corrigé", 42))

conn.commit()
```

**Dans notre app** :
```python
def update(transaction: Transaction):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE transactions
        SET type = ?, categorie = ?, montant = ?, date = ?, description = ?
        WHERE id = ?
    """, (
        transaction.type,
        normalize_category(transaction.categorie),
        transaction.montant,
        transaction.date.isoformat(),
        transaction.description,
        transaction.id
    ))
    
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    
    return success
```

---

### 6. Supprimer

```python
cursor.execute("""
    DELETE FROM transactions WHERE id = ?
""", (42,))

conn.commit()
```

**Dans notre app** :
```python
def delete(transaction_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        DELETE FROM transactions WHERE id = ?
    """, (transaction_id,))
    
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    
    return success
```

---

## 🔥 Fonctions avancées

### 1. Agrégations

```python
# Somme
cursor.execute("""
    SELECT SUM(montant) as total FROM transactions
    WHERE type = 'Dépense'
""")
total = cursor.fetchone()['total']

# Comptage
cursor.execute("""
    SELECT COUNT(*) as nb FROM transactions
""")
nb = cursor.fetchone()['nb']

# Groupé
cursor.execute("""
    SELECT categorie, SUM(montant) as total
    FROM transactions
    WHERE type = 'Dépense'
    GROUP BY categorie
    ORDER BY total DESC
""")
rows = cursor.fetchall()
```

---

### 2. Jointures

```python
cursor.execute("""
    SELECT t.*, c.couleur
    FROM transactions t
    LEFT JOIN categories c ON t.categorie = c.nom
    WHERE t.type = 'Dépense'
""")
```

---

### 3. row_factory (Dicts au lieu de tuples)

```python
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute("SELECT * FROM transactions WHERE id = ?", (42,))
row = cursor.fetchone()

# Accès par nom de colonne
print(row['montant'])
print(row['description'])

# Convertir en dict
row_dict = dict(row)
```

**Dans notre app** : Activé partout via `get_db_connection()`

---

### 4. Transactions (atomicité)

```python
conn = sqlite3.connect('finances.db')

try:
    cursor = conn.cursor()
    
    # Plusieurs opérations
    cursor.execute("INSERT INTO transactions (...) VALUES (...)")
    cursor.execute("UPDATE autre_table SET ...")
    
    # Si tout OK, commit
    conn.commit()
    
except sqlite3.Error as e:
    # Si erreur, annuler tout
    conn.rollback()
    print(f"Erreur : {e}")
    
finally:
    conn.close()
```

---

## ⚠️ Points clés

### 1. Placeholders (?)

```python
# ✅ BON - Protection contre SQL injection
montant = 100
cursor.execute("SELECT * FROM transactions WHERE montant > ?", (montant,))

# ❌ DANGEREUX - Injection SQL possible !
cursor.execute(f"SELECT * FROM transactions WHERE montant > {montant}")
```

### 2. Commit obligatoire

```python
# INSERT/UPDATE/DELETE ne sont pas sauvegardés sans commit()
cursor.execute("INSERT INTO ...")
conn.commit()  # ← NÉCESSAIRE !
```

### 3. Fermer les connexions

```python
conn = sqlite3.connect('finances.db')
try:
    # Opérations...
    pass
finally:
    conn.close()  # Toujours fermer
```

---

## 🚀 PRAGMA (Configuration SQLite)

### Mode WAL (Write-Ahead Logging)

Permet lectures et écritures simultanées :

```python
conn.execute("PRAGMA journal_mode = WAL")
```

**Avantages** :
- Meilleure concurrence
- Pas de corruption si crash
- Plus rapide pour notre usage

**Dans notre app** : Activé dans `get_db_connection()`

### Foreign Keys

Active les contraintes de clés étrangères :

```python
conn.execute("PRAGMA foreign_keys = ON")
```

### Busy Timeout

Évite les erreurs "database is locked" :

```python
conn.execute("PRAGMA busy_timeout = 30000")  # 30 secondes
```

---

## 📊 Intégration avec Pandas

**Lire toute une table** :
```python
import pandas as pd

df = pd.read_sql("SELECT * FROM transactions", conn)
```

**Écrire un DataFrame** :
```python
df.to_sql('transactions', conn, if_exists='append', index=False)
```

**Dans notre app** (`repositories.py`) :
```python
def get_all():
    conn = get_db_connection()
    df = pd.read_sql("SELECT * FROM transactions ORDER BY date DESC", conn)
    conn.close()
    return df
```

---

## ⚙️ Cas d'usage de notre app

### Récupérer toutes les transactions filtrées

```python
conn = get_db_connection()
cursor = conn.cursor()

cursor.execute("""
    SELECT * FROM transactions
    WHERE date >= ? AND date <= ?
    AND type = ?
    ORDER BY date DESC
""", (start_date, end_date, 'Dépense'))

rows = cursor.fetchall()
transactions = [Transaction.from_row(row) for row in rows]
conn.close()
```

### Statistiques par catégorie

```python
cursor.execute("""
    SELECT 
        categorie,
        SUM(montant) as total,
        COUNT(*) as nb_transactions,
        AVG(montant) as moyenne
    FROM transactions
    WHERE type = 'Dépense'
    GROUP BY categorie
    ORDER BY total DESC
""")

stats = cursor.fetchall()
```

---

## 📖 Ressources

- **Documentation Python** : https://docs.python.org/3/library/sqlite3.html
- **SQL Tutorial** : https://www.sqlitetutorial.net
- **PRAGMA** : https://www.sqlite.org/pragma.html

---

## 💡 SQLite dans notre projet

| Fichier | Utilisation |
|---------|------------|
| `connection.py` | Gestion des connexions SQLite |
| `schema.py` | Création et migration des tables |
| `repositories.py` | Toutes les requêtes SQL (CRUD) |
| `main.py` | Initialisation de la base au démarrage |

**Fichier de base de données** : `~/analyse/finances.db` (défini dans `paths.py`)
