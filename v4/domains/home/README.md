# Module Home - Page d'Accueil

**Dernière mise à jour** : 23 décembre 2024

---

## 🎯 Vue d'Ensemble

Le module Home implémente la page d'accueil de l'application avec un dashboard financier complet. Il affiche une vue d'ensemble de la situation financière en temps réel avec 5 sections principales.

---

## 📦 Dépendances Externes

Ce module nécessite les bibliothèques Python suivantes :

| Bibliothèque | Utilisation | Version Min |
|-------------|-------------|-------------|
| `streamlit` | Interface utilisateur web | ≥1.0 |
| `pandas` | Manipulation de données | ≥1.3 |
| `plotly` | Graphiques interactifs | ≥5.0 |

**Installation** :
```bash
pip install streamlit pandas plotly
```

---

## 📊 Architecture

### Structure en 5 Sections

```
┌─────────────────────────────────────────────┐
│          Page d'Accueil (Dashboard)         │
├──────────────────┬──────────────────────────┤
│ 1. Statut Global │  2. Échéances           │
│    (gauche haut) │     (droite haut)       │
├──────────────────┼──────────────────────────┤
│ 3. Catégories    │  4. Dernières           │
│    (gauche bas)  │     Transactions        │
│                  │     (droite bas)        │
├──────────────────┴──────────────────────────┤
│ 5. Pilotage Financier (pleine largeur)     │
└─────────────────────────────────────────────┘
```

---

## 📄 Fichiers du Module

### Structure
```
domains/home/
├── __init__.py
└── pages/
    └── home.py          # Page principale du dashboard
```

### `home.py` - Dashboard Principal

**Responsabilité** : Afficher vue d'ensemble financière complète

**Fonction principale** :
```python
def interface_accueil() -> None:
    """
    Page d'accueil avec dashboard financier en 5 sections.
    
    Affiche une vue d'ensemble complète de la situation financière.
    """
```

**Sections affichées** :
1. **Statut Global** : Solde actuel, revenus, dépenses
2. **Échéances** : Prochaines échéances à venir
3. **Catégories** : Répartition des dépenses par catégorie
4. **Dernières Transactions** : Liste des transactions récentes
5. **Pilotage Financier** : Indicateurs de performance

---

## 🔧 Intégration

### Utilisation dans l'Application

```python
from domains.home.pages.home import interface_accueil

# Dans votre page Streamlit
interface_accueil()
```

### Dépendances Internes

Le module Home utilise les modules partagés suivants :

```python
from shared.ui import load_transactions         # Chargement des données
from shared.database import get_db_connection   # Accès base de données
```

---

## 📈 Graphiques et Visualisations

Le module utilise **Plotly** pour créer des graphiques interactifs :

- **Graphiques en secteurs** : Répartition des catégories
- **Graphiques en barres** : Évolution temporelle
- **Indicateurs KPI** : Métriques financières

**Style** : Mode sombre avec palette de couleurs personnalisée

---

## 🔗 Références

- [shared/ui](../../shared/ui/README.md) - Composants UI partagés
- [shared/database](../../shared/database/README.md) - Gestion base de données
- [Plotly Documentation](https://plotly.com/python/) - Graphiques interactifs
