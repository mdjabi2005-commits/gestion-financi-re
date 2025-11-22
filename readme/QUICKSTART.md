# 🚀 Guide de Démarrage Rapide - Gestio V4

## ✅ Problème résolu : Regex lookbehind

**Erreur rencontrée :** `look-behind requires fixed-width pattern`

**Solution appliquée :**
- Corrigé les expressions régulières dans `modules/ocr/parsers.py`
- Remplacé les lookbehind à largeur variable par des groupes de capture

---

## 📦 Installation

### 1. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 2. Installer Tesseract OCR (pour le scan de tickets)

**Ubuntu/Debian :**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-fra
```

**macOS :**
```bash
brew install tesseract tesseract-lang
```

**Windows :**
Télécharger depuis : https://github.com/UB-Mannheim/tesseract/wiki

---

## 🎯 Lancement

```bash
streamlit run main.py
```

L'application sera accessible à : **http://localhost:8501**

---

## 📁 Structure des dossiers (créés automatiquement)

L'application créera ces dossiers dans `~/gestion_financiere_data/` :

```
~/gestion_financiere_data/
├── transactions.db          # Base de données SQLite
├── tickets_a_scanner/       # Déposez vos tickets ici pour OCR
├── tickets_tries/           # Tickets traités et classés
├── revenus_a_traiter/       # PDFs de revenus à scanner
├── revenus_traites/         # Revenus traités
└── ocr_logs/               # Logs de performance OCR
    ├── pattern_log.json
    ├── performance_stats.json
    ├── pattern_stats.json
    └── scan_history.jsonl
```

---

## 🔍 Fichiers de log

### Application principale
- **Fichier :** `gestio_app.log` (dans le dossier du projet)
- **Contenu :** Tous les logs de l'application
- **Commande :** `tail -f gestio_app.log` pour suivre en temps réel

### Logs OCR
- **Dossier :** `~/gestion_financiere_data/ocr_logs/`
- **Fichiers :**
  - `scan_history.jsonl` - Historique de tous les scans
  - `performance_stats.json` - Statistiques de performance
  - `pattern_stats.json` - Statistiques par pattern détecté

---

## 🐛 Résolution de problèmes

### Erreur : "No module named 'streamlit'"
```bash
pip install streamlit pandas pytesseract opencv-python Pillow plotly
```

### Erreur : "tesseract is not installed"
Installez Tesseract OCR (voir section Installation ci-dessus)

### Erreur de base de données
```bash
# Supprimer la base de données corrompue
rm ~/gestion_financiere_data/transactions.db

# Relancer l'application (créera une nouvelle DB)
streamlit run main.py
```

### Voir les logs détaillés
```bash
# Logs de l'application
cat gestio_app.log

# Dernières 50 lignes
tail -50 gestio_app.log

# Suivre en temps réel
tail -f gestio_app.log
```

---

## 🎨 Fonctionnalités principales

### 🏠 Accueil
- Tableau de bord avec balance, dépenses, revenus
- Graphiques d'évolution mensuelle
- Répartition par catégorie

### 💳 Transactions
- Ajout manuel
- Import CSV en masse
- Édition et suppression
- Filtrage avancé

### 📸 Scanner Tickets
- OCR automatique des tickets de caisse
- 4 méthodes de détection du montant
- Catégorisation automatique depuis le nom du fichier

### 💵 Revenus
- Ajout manuel
- Scan automatique de PDFs (fiches de paie, Uber)
- **Calcul automatique de la fiscalité Uber (21%)**

### 🔄 Récurrences
- Transactions récurrentes (quotidien, hebdomadaire, mensuel, annuel)
- Génération automatique des occurrences passées
- Gestion avancée avec historique de versions

### 💼 Portefeuille
- Budgets par catégorie
- Objectifs financiers
- Prévisions et échéances

### 🔍 Analyse OCR
- Statistiques de performance
- Patterns fiables vs problématiques
- Diagnostic complet avec recommandations

---

## 📝 Nommage des fichiers pour OCR automatique

Pour une catégorisation automatique :

```
nom.categorie.sous_categorie.extension

Exemples :
- carrefour.alimentation.courses.jpg
- essence.transport.carburant.png
- resto.loisirs.sorties.pdf
```

---

## 🔧 Configuration personnalisée

### Modifier les chemins
Éditez `config/paths.py` :

```python
DATA_DIR = os.path.expanduser("~/mon_dossier_perso")
```

### Modifier le taux de taxe Uber
Éditez `config/ocr_config.py` :

```python
UBER_TAX_RATE = 0.21  # 21% par défaut
```

### Modifier les couleurs de l'interface
Éditez `config/ui_config.py` :

```python
PRIMARY_COLOR = "#10b981"  # Vert
SECONDARY_COLOR = "#3b82f6"  # Bleu
```

---

## 📊 Import CSV

Format attendu :

```csv
type,date,categorie,sous_categorie,montant,description
dépense,2025-01-15,alimentation,courses,45.50,Carrefour
revenu,2025-01-20,salaire,salaire net,2500.00,Janvier 2025
```

---

## 🆘 Support

En cas de problème :

1. **Consultez les logs :** `cat gestio_app.log`
2. **Vérifiez la configuration :** `config/paths.py`
3. **Testez les imports :**
   ```bash
   python3 -c "from modules.database import init_db; print('OK')"
   ```

---

## ✅ Checklist de premier lancement

- [ ] Python 3.8+ installé
- [ ] Dépendances installées (`pip install -r requirements.txt`)
- [ ] Tesseract OCR installé
- [ ] Lancé `streamlit run main.py`
- [ ] Application accessible sur http://localhost:8501
- [ ] Dossiers créés automatiquement dans `~/gestion_financiere_data/`

---

**Version :** 4.0 (Refactored)
**Date :** 2025-11-17
**Auteur :** djabi
