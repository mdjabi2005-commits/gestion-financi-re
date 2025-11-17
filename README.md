# Gestio V4 - Application de Gestion Financière

## 📋 Description

Gestio V4 est une application de gestion financière moderne développée avec Streamlit. Elle permet de suivre vos dépenses et revenus, avec des fonctionnalités avancées d'OCR pour scanner automatiquement vos tickets de caisse et reçus.

## 🏗️ Architecture

Cette version (V4) a été entièrement refactorisée pour une meilleure maintenabilité et séparation des responsabilités.

```
gestion-financi-re/
├── config/                     # Configuration centralisée
│   ├── __init__.py
│   ├── paths.py               # Chemins des fichiers et dossiers
│   ├── database_config.py     # Configuration base de données
│   ├── ocr_config.py          # Configuration OCR et taxes
│   └── ui_config.py           # Configuration interface utilisateur
│
├── modules/
│   ├── database/              # Couche d'accès aux données
│   │   ├── connection.py      # Gestion des connexions SQLite
│   │   ├── schema.py          # Initialisation et migrations
│   │   ├── models.py          # Modèles de données
│   │   └── repositories.py    # Pattern Repository
│   │
│   ├── services/              # Logique métier
│   │   ├── revenue_service.py     # Traitement des revenus (Uber, taxes)
│   │   ├── recurrence_service.py  # Gestion des récurrences
│   │   └── file_service.py        # Opérations sur fichiers
│   │
│   ├── ocr/                   # Traitement OCR
│   │   ├── scanner.py         # Scan d'images
│   │   ├── parsers.py         # Analyse de tickets/PDFs
│   │   ├── logging.py         # Journalisation OCR
│   │   └── diagnostics.py     # Analyse de performance
│   │
│   ├── ui/                    # Interface utilisateur
│   │   ├── components.py      # Composants réutilisables
│   │   ├── helpers.py         # Fonctions d'assistance
│   │   ├── styles.py          # Gestion des styles CSS
│   │   └── pages/             # Pages de l'application
│   │       ├── home.py
│   │       ├── transactions.py
│   │       ├── revenues.py
│   │       ├── recurrences.py
│   │       ├── portfolio.py
│   │       ├── scanning.py
│   │       └── ocr_page.py
│   │
│   └── utils/                 # Utilitaires
│       ├── converters.py      # Conversion de types
│       ├── validators.py      # Validation de données
│       ├── formatters.py      # Formatage
│       └── constants.py       # Constantes
│
├── resources/
│   └── styles/                # Feuilles de style CSS
│       ├── main.css
│       ├── responsive.css
│       └── dark_mode.css
│
├── tests/                     # Tests unitaires et d'intégration
│   ├── unit/
│   └── integration/
│
├── main.py                    # Point d'entrée de l'application
└── requirements.txt           # Dépendances Python
```

## 🚀 Installation

### Prérequis

- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)
- Tesseract OCR installé sur votre système

### Installation de Tesseract

**Ubuntu/Debian :**
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-fra
```

**macOS :**
```bash
brew install tesseract tesseract-lang
```

**Windows :**
Téléchargez l'installeur depuis : https://github.com/UB-Mannheim/tesseract/wiki

### Installation des dépendances Python

```bash
pip install -r requirements.txt
```

## 📦 Dépendances principales

- `streamlit` - Framework d'interface utilisateur
- `pandas` - Manipulation de données
- `pytesseract` - OCR (Optical Character Recognition)
- `opencv-python` (cv2) - Traitement d'images
- `Pillow` (PIL) - Manipulation d'images
- `plotly` - Visualisations interactives
- `python-dateutil` - Manipulation de dates

## 🎯 Utilisation

### Lancer l'application

```bash
streamlit run main.py
```

L'application sera accessible à l'adresse : `http://localhost:8501`

### Fonctionnalités principales

#### 🏠 Accueil
- Tableau de bord avec métriques financières
- Visualisation de l'évolution mensuelle
- Graphiques de répartition par catégorie

#### 💳 Transactions
- Ajout manuel de dépenses/revenus
- Import CSV en masse
- Visualisation et édition des transactions
- Filtrage avancé par date, type, catégorie

#### 📸 Scanner Tickets
- OCR automatique des tickets de caisse
- Détection intelligente du montant (4 méthodes)
- Organisation automatique des fichiers
- Suivi de performance OCR

#### 💵 Revenus
- Ajout manuel de revenus
- Scan automatique de PDFs (fiches de paie, Uber)
- Calcul automatique de la fiscalité Uber (21%)
- Traitement par lots

#### 🔄 Récurrences
- Création de transactions récurrentes
- Génération automatique des occurrences passées
- Gestion avancée avec historique de versions
- Prévision budgétaire automatique

#### 💼 Portefeuille
- Gestion de budgets par catégorie
- Objectifs financiers
- Prévisions et échéances
- Vue d'ensemble consolidée

#### 🔍 Analyse OCR
- Statistiques de performance
- Analyse des patterns fiables/problématiques
- Historique des scans
- Diagnostic complet

## 🔧 Configuration

### Chemins personnalisés

Modifiez le fichier `config/paths.py` pour personnaliser les chemins :

```python
DATA_DIR = os.path.expanduser("~/gestion_financiere_data")
DB_PATH = os.path.join(DATA_DIR, "transactions.db")
TO_SCAN_DIR = os.path.join(DATA_DIR, "tickets_a_scanner")
```

### Taxes Uber

Modifiez `config/ocr_config.py` :

```python
UBER_TAX_RATE = 0.21  # 21% de prélèvement fiscal
```

### Interface utilisateur

Personnalisez les couleurs dans `config/ui_config.py` :

```python
PRIMARY_COLOR = "#10b981"
SECONDARY_COLOR = "#3b82f6"
```

## 📊 Format de fichiers

### Import CSV

Format attendu :
```csv
type,date,categorie,sous_categorie,montant,description
dépense,2025-01-15,alimentation,courses,45.50,Carrefour
revenu,2025-01-20,salaire,salaire net,2500.00,Janvier 2025
```

### Nommage des tickets

Pour une catégorisation automatique :
```
nom.categorie.sous_categorie.extension

Exemples :
- carrefour.alimentation.courses.jpg
- essence.transport.carburant.png
- restaurant.loisirs.sorties.pdf
```

## 🧪 Tests

```bash
# Tests unitaires
pytest tests/unit/

# Tests d'intégration
pytest tests/integration/

# Tous les tests avec couverture
pytest --cov=modules tests/
```

## 📝 Logs

Les logs sont enregistrés dans `gestio_app.log`

Niveaux de log :
- INFO : Opérations normales
- WARNING : Avertissements
- ERROR : Erreurs récupérables
- CRITICAL : Erreurs critiques

## 🐛 Dépannage

### Problème d'OCR

```bash
# Vérifier l'installation de Tesseract
tesseract --version

# Tester l'OCR
tesseract image.jpg output -l fra
```

### Problème de base de données

```bash
# Réinitialiser la base de données
rm ~/gestion_financiere_data/transactions.db

# Relancer l'application pour recréer la DB
streamlit run main.py
```

### Problème d'import

```bash
# Vérifier l'installation des modules
pip list | grep streamlit

# Réinstaller les dépendances
pip install -r requirements.txt --force-reinstall
```

## 🤝 Contribution

### Structure du code

- **Type hints** obligatoires pour toutes les fonctions
- **Docstrings** Google-style pour toutes les fonctions publiques
- **Tests** unitaires pour toute nouvelle fonctionnalité
- **Logging** approprié (INFO, WARNING, ERROR)

### Workflow

1. Créer une branche : `git checkout -b feature/ma-fonctionnalite`
2. Développer avec tests
3. Commit : `git commit -m "feat: ajout de ma fonctionnalité"`
4. Push : `git push origin feature/ma-fonctionnalite`
5. Créer une Pull Request

## 📄 Licence

Ce projet est sous licence MIT.

## 👤 Auteur

- **djabi**
- Version : 4.0 (Refactored)
- Date : 2025-11-17

## 📚 Ressources

- [Documentation Streamlit](https://docs.streamlit.io/)
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
- [Pandas Documentation](https://pandas.pydata.org/docs/)
- [Plotly Documentation](https://plotly.com/python/)

## 🆚 Historique des versions

- **V4.0** (2025-11-17) : Refactorisation complète en architecture modulaire
- **V3.0** : Ajout du portefeuille et des prévisions
- **V2.0** : Ajout de l'OCR et des récurrences
- **V1.0** : Version initiale avec gestion basique des transactions
