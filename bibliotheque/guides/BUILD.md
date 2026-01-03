---
type: guide_general
difficulty: advanced
tags: [build, deployment, pyinstaller, github-actions]
last_updated: 2024-12-22
estimated_reading: 25min
status: active
phase: 3
related:
  - ajouts/08_phase3_build_installation.md
  - guides/IMPLEMENTATION_GUIDE.md
---

# Guide de Build - Gestio V4

**Dernière mise à jour** : 23 décembre 2024

---

## 🎯 Vue d'Ensemble

Ce guide explique comment construire et packager Gestio V4 pour les différentes plateformes (Windows, Linux, macOS).

**Workflow GitHub Actions** : `.github/workflows/build.yml`

---

## 📦 Packages Générés

Le workflow génère 3 packages :

| Plateforme | Fichier | Contenu |
|------------|---------|---------|
| **Windows** | `GestionFinanciere-Windows.zip` | `.exe` + install script PowerShell + Tesseract |
| **Linux** | `GestionFinanciere-Linux.zip` | Scripts Python + `run.sh` + Tesseract |
| **macOS** | `GestionFinanciere-macOS.zip` | Scripts Python + `run.sh` + Tesseract |

---

## 🔧 Workflow Build Complet

### 1. Déclenchement

```yaml
on:
  push:
    branches: [ main ]
  workflow_dispatch:  # Manuel depuis GitHub Actions
```

Le build se lance automatiquement à chaque push sur `main` ou manuellement.

### 2. Matrice Multi-Plateforme

```yaml
strategy:
  matrix:
    os: [windows-latest, ubuntu-latest, macos-latest]
```

Le workflow s'exécute en parallèle sur les 3 OS.

---

## 🪟 Build Windows

### Étapes

1. **Installation Python 3.13**
2. **Installation dépendances** :
   ```bash
   pip install streamlit pandas plotly python-dateutil pytesseract opencv-python-headless Pillow pdfminer.six regex requests
   ```

3. **Compilation PyInstaller** :
   ```bash
   pyinstaller app/launch.py \
     --onefile \
     --windowed \
     --name "GestionFinanciere" \
     --add-data "app/main.py;." \
     --add-data "app/config;./config" \
     --add-data "app/domains;./domains" \
     --add-data "app/shared;./shared" \
     --add-data "app/resources;./resources"
   ```

4. **Package final** :
   - `GestionFinanciere.exe` (portable)
   - `install_and_run_windows.ps1` (script setup)
   - `tesseract/` (OCR binaire inclus)

### Tesseract Embarqué

**Critique** : Tesseract doit être dans le ZIP final
```bash
# Copier depuis le dépôt
cp -r tesseract dist/
```

---

## 🐧 Build Linux

### Bug Critique Corrigé (✅ Résolu)

**Problème** : Le workflow ne copiait que `app/*.py`, **pas les sous-dossiers** !

```bash
# ❌ AVANT (INCOMPLET)
cp app/*.py dist/linux/

# ✅ APRÈS (COMPLET)
cp -r app/* dist/linux/
```

**Conséquence** : Sans les dossiers `config/`, `domains/`, `shared/`, `resources/`, l'app ne démarre pas.

### Étapes

1. **Installer Python 3.13**
2. **Copier TOUT le dossier app** :
   ```bash
   mkdir -p dist/linux
   cp -r app/* dist/linux/
   ```

3. **Créer script run.sh** :
   - Détecte la distribution Linux (Debian, Fedora, Arch, MX Linux)
   - Installe Python si manquant
   - Installe Tesseract OCR
   - Crée environnement virtuel
   - Installe dépendances Python
   - Lance Streamlit

4. **Package final** :
   - Tous les fichiers Python (structure complète)
   - `run.sh` (exécutable)
   - `tesseract/` (binaire optionnel)

### Script run.sh Features

Intelligent et robuste :
```bash
# Détection distribution
detect_linux_distro()

# Installation auto Python
if ! command -v python3; then
  # Install selon distro (apt, dnf, pacman)
fi

# Environnement virtuel
python3 -m venv .little_finance_env
source .little_finance_env/bin/activate

# Dépendances
pip install streamlit pandas pytesseract Pillow python-dateutil opencv-python-headless plotly regex pdfminer.six requests

# Lancement
streamlit run gui_launcher.py --server.headless true
```

---

## 🍎 Build macOS

Identique à Linux :

```bash
mkdir -p dist/macos
cp -r app/* dist/macos/  # TOUT le dossier !
```

**Script run.sh** adapté pour macOS (Homebrew).

---

## 📊 Dépendances Build

### Dépendances Corrigées (✅ Résolu)

**Problème** : `matplotlib` était installé mais **non utilisé** dans le projet.

```bash
# ❌ AVANT
pip install ... matplotlib ...

# ✅ APRÈS  
pip install ... plotly regex ...
```

### Liste Complète Actuelle

```bash
pip install \
  streamlit \
  pandas \
  plotly \           # ✅ Ajouté (graphiques interactifs)
  python-dateutil \
  pytesseract \
  opencv-python-headless \
  Pillow \
  pdfminer.six \
  regex \            # ✅ Ajouté (patterns avancés OCR)
  requests
```

**Voir** : [ARCHITECTURE.md - Table dépendances](../bibliotheque/ARCHITECTURE.md#-dépendances-python-par-module)

---

## 🚀 Release GitHub

### Versioning

Version lue depuis `version.txt` :
```bash
V=$(cat version.txt | tr -d ' \r\n')
echo "VERSION=$V" >> $GITHUB_ENV
```

### Notes de Release Automatiques

Générées via **conventional commits** :

```bash
# Types détectés
feat:     → ✨ Nouvelles fonctionnalités
fix:      → 🐛 Corrections
perf:     → ⚡ Performances
refactor: → 🧹 Refactor
docs:     → 📝 Documentation
```

### Draft Release

```yaml
uses: softprops/action-gh-release@v2
with:
  tag_name: v${{ env.VERSION }}
  draft: true  # À publier manuellement
  files: |
    dist/GestionFinanciere*.zip
```

Les releases sont créées en **brouillon** pour validation manuelle.

---

## ⚙️ Commandes Locales

### Build Windows (local)

```powershell
# Installer PyInstaller
pip install pyinstaller

# Compiler
pyinstaller app/launch.py --onefile --windowed --name "GestionFinanciere"

# Vérifier
.\dist\GestionFinanciere.exe
```

### Test Linux/macOS (local)

```bash
# Simulation du package
mkdir -p dist/linux
cp -r app/* dist/linux/
cd dist/linux

# Créer venv et installer
python3 -m venv .venv
source .venv/bin/activate
pip install -r ../../app/requirements.txt

# Lancer
streamlit run gui_launcher.py
```

---

## 🔍 Vérifications Post-Build

### Checklist Windows

- [ ] `GestionFinanciere.exe` présent dans ZIP
- [ ] Dossier `tesseract/` inclus
- [ ] Script `install_and_run_windows.ps1` présent
- [ ] Taille exe \> 50 MB (si trop petit = erreur)

### Checklist Linux/macOS

- [ ] Dossier `app/` complet copié (pas juste `*.py`)
- [ ] Sous-dossiers présents :
  - [ ] `config/`
  - [ ] `domains/`
  - [ ] `shared/`
  - [ ] `resources/`
- [ ] Script `run.sh` exécutable (`chmod +x`)
- [ ] Tesseract inclus (optionnel, installé par script)

---

## 🐛 Problèmes Connus et Solutions

### 1. ❌ Package Linux vide ou incomplet

**Symptôme** : App ne démarre pas sur Linux, erreurs `ModuleNotFoundError`

**Cause** : Copie `app/*.py` au lieu de `app/*`

**Solution** : ✅ Corrigé dans workflow
```bash
cp -r app/* dist/linux/  # Copie TOUT
```

### 2. ❌ Matplotlib non utilisé

**Symptôme** : Dépendance inutile ralentit installation

**Cause** : Erreur historique, projet utilise Plotly

**Solution** : ✅ Retiré du workflow
```bash
# Remplacé par plotly
```

### 3. ❌ Regex manquant

**Symptôme** : OCR parsing échoue, patterns ne fonctionnent pas

**Cause** : Dépendance `regex` non installée

**Solution** : ✅ Ajouté au workflow
```bash
pip install regex
```

### 4. ❌ Tesseract absent du package

**Symptôme** : OCR ne fonctionne pas sur Windows

**Cause** : Dossier `tesseract/` non copié

**Solution** : Vérifier étape de copie
```bash
if [ -d "tesseract" ]; then
  cp -r tesseract dist/
fi
```

---

## 📚 Ressources

- **Workflow** : [.github/workflows/build.yml](../.github/workflows/build.yml)
- **Dépendances** : [ARCHITECTURE.md](../bibliotheque/ARCHITECTURE.md)
- **PyInstaller** : https://pyinstaller.org/en/stable/

---

## 💡 En Cas de Problème

1. Vérifier logs GitHub Actions
2. Tester build local avec commandes ci-dessus
3. Valider présence de tous les dossiers dans package
4. Vérifier `requirements.txt` à jour

**Logs** : GitHub Actions → Onglet "Actions" → Sélectionner run → Voir logs détaillés
