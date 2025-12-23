# 📚 Bibliothèque : Pandas

## 🎯 Qu'est-ce que Pandas ?

**Pandas** est LA bibliothèque Python pour la **manipulation et l'analyse de données**. Elle offre des structures de données puissantes (DataFrame, Series) pour travailler avec des données tabulaires.

**Site officiel** : https://pandas.pydata.org  
**Documentation** : https://pandas.pydata.org/docs

---

## 💡 Pourquoi Pandas dans notre projet ?

1. **DataFrames** : Représentation parfaite pour les transactions
2. **Filtrage facile** : Sélectionner des transactions par critères
3. **Agrégation** : Calculs de totaux, moyennes, groupes
4. **Export** : Vers CSV, Excel facilement
5. **Intégration Streamlit** : Affichage natif des DataFrames

---

## 🔧 Concepts de base

### 1. DataFrame (tableau de données)

Le concept central de Pandas :

```python
import pandas as pd

# Créer un DataFrame
df = pd.DataFrame({
    'type': ['Dépense', 'Revenu', 'Dépense'],
    'montant': [45.50, 2500.00, 15.00],
    'categorie': ['Alimentation', 'Salaire', 'Transport']
})

print(df)
#        type  montant    categorie
# 0  Dépense    45.50  Alimentation
# 1   Revenu  2500.00      Salaire
# 2  Dépense    15.00    Transport
```

**Dans notre app** :
```python
# Charger toutes les transactions
df = TransactionRepository.get_all()
# Retourne un DataFrame avec colonnes: id, type, categorie, montant, date, etc.
```

---

### 2. Sélection de données

**Sélectionner des colonnes** :
```python
# Une colonne → Series
montants = df['montant']

# Plusieurs colonnes → DataFrame
subset = df[['type', 'montant']]
```

**Filtrer des lignes** :
```python
# Dépenses seulement
depenses = df[df['type'] == 'Dépense']

# Montants > 100€
grosses_transactions = df[df['montant'] > 100]

# Plusieurs conditions (& = AND, | = OR)
janvier_depenses = df[
    (df['date'] >= '2025-01-01') &
    (df['date'] <= '2025-01-31') &
    (df['type'] == 'Dépense')
]
```

**Dans notre app** (exemple `home.py`) :
```python
# Filtrer les revenus
df_revenus = df_trans[df_trans['type'] == 'revenu']

# Filtrer par catégorie
df_salaire = df_revenus[df_revenus['categorie'] == 'Salaire']
```

---

### 3. Agrégations et groupes

**Sommes** :
```python
# Total de tous les montants
total = df['montant'].sum()

# Total par type
totaux_par_type = df.groupby('type')['montant'].sum()
# type
# Dépense     60.50
# Revenu    2500.00
```

**Dans notre app** :
```python
# Total dépenses par catégorie
depenses_par_cat = df_depenses.groupby('categorie')['montant'].sum()

# Compter le nombre de transactions par catégorie
nb_trans = df.groupby('categorie').size()
```

**Fonctions d'agrégation** :
```python
df['montant'].sum()    # Somme
df['montant'].mean()   # Moyenne
df['montant'].min()    # Minimum
df['montant'].max()    # Maximum
df['montant'].count()  # Nombre d'éléments (non-NULL)
df['montant'].std()    # Écart-type
```

---

### 4. Manipulation de colonnes

**Ajouter une colonne** :
```python
# Colonne calculée
df['montant_arrondi'] = df['montant'].round(0)

# Colonne conditionnelle
df['niveau'] = df['montant'].apply(
    lambda x: 'Faible' if x < 50 else 'Élevé'
)
```

**Modifier des valeurs** :
```python
# Remplacer
df['type'] = df['type'].replace({'Dépense': 'Expense'})

# Appliquer une fonction
df['montant'] = df['montant'].apply(lambda x: abs(x))
```

**Dans notre app** :
```python
# Convertir la colonne date en datetime
df['date'] = pd.to_datetime(df['date'])

# Extraire le mois
df['mois'] = df['date'].dt.month
```

---

### 5. Trier et ordonner

```python
# Trier par montant (croissant)
df_sorted = df.sort_values('montant')

# Trier par montant (décroissant)
df_sorted = df.sort_values('montant', ascending=False)

# Trier par plusieurs colonnes
df_sorted = df.sort_values(['type', 'montant'], ascending=[True, False])
```

**Dans notre app** (`repositories.py`) :
```python
def get_all(sort_by="date", ascending=False):
    df = pd.read_sql("SELECT * FROM transactions", conn)
    return df.sort_values(sort_by, ascending=ascending)
```

---

### 6. Gestion des dates

```python
# Convertir en datetime
df['date'] = pd.to_datetime(df['date'])

# Extraire des parties
df['annee'] = df['date'].dt.year
df['mois'] = df['date'].dt.month
df['jour_semaine'] = df['date'].dt.day_name()  # 'Monday', 'Tuesday'...

# Filtrer par période
janvier = df[df['date'].dt.month == 1]
```

**Dans notre app** :
```python
# Filtrer par plage de dates
df_filtered = df[
    (df['date'] >= start_date) &
    (df['date'] <= end_date)
]

# Grouper par mois
monthly = df.groupby(df['date'].dt.to_period('M'))['montant'].sum()
```

---

### 7. Valeurs manquantes (NULL)

```python
# Détecter les valeurs manquantes
df.isnull()         # True/False pour chaque cellule
df['col'].isnull()  # True/False pour une colonne

# Compter les valeurs manquantes
df.isnull().sum()

# Supprimer les lignes avec NA
df_clean = df.dropna()

# Remplir les NA
df['sous_categorie'] = df['sous_categorie'].fillna('Aucune')
```

**Dans notre app** :
```python
# Vérifier si sous-catégorie existe
has_subcat = df['sous_categorie'].notna()
```

---

### 8. Export/Import

**Depuis SQLite** :
```python
import sqlite3
import pandas as pd

conn = sqlite3.connect('finances.db')
df = pd.read_sql("SELECT * FROM transactions", conn)
```

**Vers CSV** :
```python
df.to_csv('transactions.csv', index=False, encoding='utf-8')
```

**Depuis CSV** :
```python
df = pd.read_csv('transactions.csv')
```

**Dans notre app** (`csv_export_service.py`) :
```python
def export_transactions_sans_tickets_to_csv():
    df = df[df['source'] == 'import_csv']  # Filtrer
    df.to_csv(CSV_PATH, index=False, encoding='utf-8')  # Exporter
```

---

## 📊 Exemples concrets de notre app

### Calculer le total des dépenses

```python
from modules.database import TransactionRepository

# Charger
df = TransactionRepository.get_all()

# Filtrer les dépenses
df_depenses = df[df['type'] == 'dépense']

# Total
total_depenses = df_depenses['montant'].sum()
print(f"Total dépenses : {total_depenses}€")
```

### Top 5 des catégories les plus dépensières

```python
# Grouper et sommer par catégorie
top_categories = (
    df_depenses
    .groupby('categorie')['montant']
    .sum()
    .sort_values(ascending=False)
    .head(5)
)

print(top_categories)
# categorie
# Alimentation    456.78
# Transport       234.50
# Logement        800.00
# ...
```

### Moyenne de dépenses par jour de la semaine

```python
# Convertir date
df['date'] = pd.to_datetime(df['date'])

# Extraire jour de la semaine
df['jour'] = df['date'].dt.day_name()

# Moyenne par jour
moyenne_par_jour = (
    df_depenses
    .groupby('jour')['montant']
    .mean()
)

print(moyenne_par_jour)
# jour
# Monday       52.30
# Tuesday      48.90
# ...
```

### Évolution mensuelle du solde

```python
# Convertir date
df['date'] = pd.to_datetime(df['date'])

# Extraire mois
df['mois'] = df['date'].dt.to_period('M')

# Grouper par mois et type
monthly = (
    df.groupby(['mois', 'type'])['montant']
    .sum()
    .unstack(fill_value=0)
)

# Calculer le solde
monthly['solde'] = monthly.get('revenu', 0) - monthly.get('dépense', 0)
```

---

## 🔥 Opérations avancées

### Apply (appliquer une fonction)

```python
# Fonction simple
df['montant_double'] = df['montant'].apply(lambda x: x * 2)

# Fonction complexe sur toute la ligne
def categoriser(row):
    if row['montant'] > 100:
        return 'Grosse dépense'
    else:
        return 'Petite dépense'

df['categorie_montant'] = df.apply(categoriser, axis=1)
```

### Merge (jointure)

```python
# Joindre deux DataFrames
df_final = pd.merge(
    df_transactions,
    df_categories,
    on='categorie',
    how='left'  # ou 'inner', 'right', 'outer'
)
```

### Pivot Table

```python
# Tableau croisé dynamique
pivot = df.pivot_table(
    values='montant',
    index='categorie',
    columns='type',
    aggfunc='sum',
    fill_value=0
)
```

---

## ⚠️ Pièges courants

### 1. SettingWithCopyWarning

```python
# ❌ Mauvais (peut générer un warning)
subset = df[df['type'] == 'Dépense']
subset['montant'] = subset['montant'] * 2

# ✅ Bon
subset = df[df['type'] == 'Dépense'].copy()
subset['montant'] = subset['montant'] * 2
```

### 2. Filtrage avec &, | (pas and, or)

```python
# ❌ Erreur
df[(df['montant'] > 50) and (df['type'] == 'Dépense')]

# ✅ Correct
df[(df['montant'] > 50) & (df['type'] == 'Dépense')]
```

### 3. Index reset

```python
# Après filtrage, les index peuvent être non-contigus
df_filtered = df[df['montant'] > 100]
# Index: [0, 2, 5, 7, ...]

# Réinitialiser l'index
df_filtered = df_filtered.reset_index(drop=True)
# Index: [0, 1, 2, 3, ...]
```

---

## 📖 Ressources

- **Documentation** : https://pandas.pydata.org/docs
- **Cheat Sheet** : https://pandas.pydata.org/Pandas_Cheat_Sheet.pdf
- **10 minutes to pandas** : https://pandas.pydata.org/docs/user_guide/10min.html

---

## 💡 Pandas dans notre projet

| Fichier | Utilisation |
|---------|------------|
| `repositories.py` | get_all() retourne un DataFrame |
| `home.py` | Calculs de statistiques, filtrage |
| `transactions.py` | Affichage et édition de transactions |
| `fractal_service.py` | Agrégations par catégorie |
| `csv_export_service.py` | Export vers CSV |
