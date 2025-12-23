# Module Portfolio - Gestion du Portefeuille Financier

**Dernière mise à jour** : 23 décembre 2024

---

## 🎯 Vue d'Ensemble

Le module Portfolio permet de gérer et analyser son portefeuille financier complet : échéances, budgets, récurrences (abonnements/salaires) et objectifs financiers. Interface à 3 onglets pour consultation et gestion.

---

## 📦 Dépendances Externes

Ce module nécessite les bibliothèques Python suivantes :

| Bibliothèque | Utilisation | Version Min |
|-------------|-------------|-------------|
| `streamlit` | Interface utilisateur web | ≥1.0 |
| `pandas` | Manipulation de données | ≥1.3 |
| `plotly` | Graphiques interactifs | ≥5.0 |
| `python-dateutil` | Calculs de dates (relativedelta) | ≥2.8 |

**Installation** :
```bash
pip install streamlit pandas plotly python-dateutil
```

---

## 📊 Architecture - 3 Onglets

```
┌─────────────────────────────────────────────┐
│           Module Portfolio                  │
├─────────────┬─────────────┬─────────────────┤
│ Vue         │   Gérer     │    Analyser     │
│ d'ensemble  │   (Hub)     │   (Rapports)    │
├─────────────┼─────────────┼─────────────────┤
│ • Échéances │ • Échéances │ • Tendances     │
│ • Budgets   │ • Budgets   │ • Comparatifs   │
│ • Objectifs │ • Réccurenc.│ • Projections   │
│             │ • Objectifs │                 │
└─────────────┴─────────────┴─────────────────┘
```

---

## 📄 Fichiers du Module

### Structure
```
domains/portfolio/
├── __init__.py
└── pages/
    ├── __init__.py
    ├── portefeuille.py      # Point d'entrée principal
    ├── overview.py          # Onglet Vue d'ensemble
    ├── manage.py            # Onglet Gérer (hub)
    ├── analyze.py           # Onglet Analyser
    └── helpers.py           # Fonctions utilitaires
```

---

## 🔵 Onglet 1 : Vue d'Ensemble (`overview.py`)

### Responsabilité
Dashboard en lecture seule pour consultation rapide.

### Fonctions Principales

#### `render_overview_tab(conn, cursor)`
Affiche 3 sections :

**1. Échéances à venir**
```python
def render_upcoming_deadlines(conn, cursor):
    """Affiche les 5 prochaines échéances"""
```

**2. Budget du mois**
```python
def render_budget_overview_chart(conn, cursor):
    """Graphique Budget vs Dépenses du mois"""
```
Utilise **Plotly** pour graphique en barres groupées.

**3. Objectifs**
```python
def render_objectives_progress(conn, cursor):
    """Liste des objectifs avec barres de progression"""
```

### Dépendances
- `streamlit` : Composants UI
- `pandas` : Manipulation données
- `plotly` : Graphiques barres

---

## 🟢 Onglet 2 : Gérer (`manage.py`)

### Responsabilité
Hub centralisé pour gérer tous les éléments financiers en 4 quadrants.

### Quadrants

```
┌──────────────────┬──────────────────┐
│  1. Échéances    │  2. Budgets      │
│     ponctuelles  │     mensuels     │
├──────────────────┼──────────────────┤
│  3. Récurrences  │  4. Objectifs    │
│     (abonements) │     financiers   │
└──────────────────┴──────────────────┘
```

### Fonctions Principales

#### `render_manage_tab(conn, cursor)`
Point d'entrée affichant les 4 quadrants.

#### `render_echeances_form(conn, cursor)`
Gestion des échéances ponctuelles (prévues/fixes).

#### `render_budgets_form(conn, cursor)`
Définition des budgets mensuels par catégorie.

#### `render_recurrences_form(conn, cursor)`
Gestion des abonnements et salaires récurrents.
**Utilise** : `python-dateutil.relativedelta` pour calculs périodes.

#### `render_objectifs_form(conn, cursor)`
Définition et suivi des objectifs financiers.

### Dépendances
- `streamlit` : Formulaires
- **`python-dateutil`** : Calculs dates récurrentes

---

## 🟠 Onglet 3 : Analyser (`analyze.py`)

### Responsabilité
Analyses et rapports financiers détaillés.

### Fonctions Principales

#### `render_analyze_tab(conn, cursor)`
Affiche analyses et tendances.

### Dépendances
- `streamlit` : Interface
- `pandas` : Analyses données
- `plotly` : Graphiques tendances

---

## 🛠️ Helpers (`helpers.py`)

### Responsabilité
Fonctions utilitaires partagées.

### Fonctions Clés

#### `normalize_recurrence_column(conn)`
```python
def normalize_recurrence_column(conn: sqlite3.Connection) -> None:
    """
    Normalise la colonne recurrence dans echeances.
    Migration de données.
    """
```

**Dépendances** :
- `pandas` : Manipulation données
- **`python-dateutil.relativedelta`** : Calculs dates

---

## 🔧 Intégration

### Utilisation dans l'Application

```python
from domains.portfolio.pages import portefeuille

# Dans votre page Streamlit
# La page gère automatiquement les onglets
```

### Dépendances Internes

```python
from config import DB_PATH
from shared.database import get_db_connection
from shared.services import backfill_recurrences_to_today
from shared.ui import load_transactions, toast_success
```

---

## 💾 Base de Données

### Tables Utilisées

| Table | Description |
|-------|-------------|
| `echeances` | Échéances ponctuelles et fixes |
| `budgets_categories` | Budgets mensuels par catégorie |
| `objectifs_financiers` | Objectifs financiers |
| `transactions` | Transactions financières |

---

## 📈 Graphiques Plotly

**Style** : Mode sombre cohérent
```python
fig.update_layout(
    paper_bgcolor='#1E1E1E',
    plot_bgcolor='#1E1E1E',
    font=dict(color='white')
)
```

---

## 🔗 Références

- [shared/ui](../../shared/ui/README.md) - Composants UI
- [shared/database](../../shared/database/README.md) - Base de données
- [shared/services](../../shared/services/README.md) - Services
- [Plotly Documentation](https://plotly.com/python/)
- [python-dateutil Docs](https://dateutil.readthedocs.io/)
