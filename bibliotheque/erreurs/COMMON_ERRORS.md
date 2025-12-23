# Erreurs Courantes - Gestio V4

## 🎯 Objectif

Documenter les erreurs rencontrées lors du développement pour éviter de les répéter.  
**Basé sur** : Sessions de développement réelles avec IA et développeurs.

---

## 🔴 Erreur #1 : Import Circulaire avec Package

### Symptôme
```
ImportError: cannot import name 'interface_transactions_simplifiee' 
from partially initialized module 'modules.ui.pages.transactions' 
(most likely due to a circular import)
```

### Contexte
Lors de la création d'un package `transactions/` avec `__init__.py` qui importe depuis un fichier parent `transactions.py`.

### Cause profonde
Python confond le **package** `transactions/` avec le **module** `transactions.py` → Conflit de noms.

### Solution
**Option A** : Renommer le fichier parent
```
transactions.py → transactions_view.py
```

**Option B** : Renommer le package
```
transactions/ → transactions_pkg/
```

### Prévention
- ❌ Ne JAMAIS avoir un fichier ET un dossier avec le même nom au même niveau
- ✅ Nommer explicitement (ex: `transactions_view.py` + `transactions_add.py`)

---

## 🔴 Erreur #2 : Oubli de Normalisation

### Symptôme
- Mêmes catégories apparaissent plusieurs fois dans l'arbre Sunburst
- Exemple : "alimentation", "Alimentation", "ALIMENTATION" = 3 entrées différentes

### Contexte
Insertion de transaction sans passer par `normalize_category()`.

### Code problématique
```python
# ❌ MAUVAIS
transaction_data = {
    "categorie": cat.strip(),  # Pas de normalisation !
    "sous_categorie": sous_cat.strip()
}
```

### Solution
```python
# ✅ CORRECT
from modules.services.normalization import normalize_category, normalize_subcategory

transaction_data = {
    "categorie": normalize_category(cat.strip()),
    "sous_categorie": normalize_subcategory(sous_cat.strip())
}
```

### Prévention
- ✅ TOUJOURS normaliser avant insertion
- ✅ Ajouter dans checklist de code review
- ✅ Créer test pytest qui vérifie

---

## 🔴 Erreur #3 : SelectboxColumn vs TextColumn

### Symptôme
Impossible de créer de nouvelles catégories en mode édition dans `st.data_editor`.

### Contexte
Utilisation de `SelectboxColumn` avec liste figée de catégories.

### Code problématique
```python
# ❌ MAUVAIS - Liste fermée
"categorie": st.column_config.SelectboxColumn(
    "Catégorie",
    options=liste_categories  # Utilisateur bloqué !
)
```

### Solution
```python
# ✅ CORRECT - Champ texte libre
"categorie": st.column_config.TextColumn(
    "Catégorie",
    help="Saisir une catégorie existante ou nouvelle"
)
```

### Prévention
- Utiliser `TextColumn` pour champs acceptant nouvelles valeurs
- Utiliser `SelectboxColumn` UNIQUEMENT pour valeurs fixes (ex: Type = revenu/dépense)

---

## 🔴 Erreur #4 : Navigation avec Composants Lourds

### Symptôme
Lors du clic sur "Voir Transactions", l'ancienne page (Home) continue de charger des graphiques Plotly pendant 30 secondes avant de changer.

### Contexte
Streamlit charge toute la page avant de détecter `st.session_state.requested_page`.

### Code problématique
```python
# Dans main.py - APRÈS le rendu
if current_page == "🏠 Accueil":
    interface_accueil()  # Charge TOUT, puis vérifie requested_page
    
if 'requested_page' in st.session_state:
    current_page = st.session_state.requested_page  # Trop tard !
```

### Solution
```python
# Dans main.py - AVANT le rendu
if 'requested_page' in st.session_state:
    current_page = st.session_state.requested_page
    del st.session_state.requested_page
    st.rerun()

# Maintenant, afficher la page
if current_page == "🏠 Accueil":
    interface_accueil()
```

### Prévention
- Toujours vérifier `requested_page` AVANT d'appeler les fonctions d'interface
- Utiliser `st.stop()` si nécessaire pour arrêter l'exécution

---

## 🔴 Erreur #5 : Fichier Trop Gros (Maintainability)

### Symptôme
Fichier `transactions.py` atteignant 881 lignes → difficile à naviguer, à comprendre, à maintenir.

### Contexte
Ajout progressif de fonctionnalités sans refactoring.

### Indicateurs
- ✅ Bon : < 300 lignes
- ⚠️ Attention : 300-500 lignes
- 🔴 Problème : > 500 lignes

### Solution
Refactoring progressif :
```
transactions.py (881 lignes)
    ↓
transactions_view.py (470 lignes)
transactions_add.py (360 lignes)
transactions_helpers.py (140 lignes)
```

### Méthodologie
1. Identifier les blocs fonctionnels
2. Extraire fonction par fonction (pas tout en une fois !)
3. Créer fichier helper
4. Remplacer par import
5. Tester après CHAQUE extraction

---

## 🔴 Erreur #6 : Commande PowerShell Multi-lignes

### Symptôme
```
The command failed with exit code: 1
...
  File "<string>", line 10
```

### Contexte
Tentative d'exécuter un script Python multi-lignes avec des quotes dans PowerShell.

### Code problématique
```powershell
python -c "
print('hello')  # Les quotes posent problème
"
```

### Solution
**Option A** : Fichier temporaire
```python
# Créer script.py
# Exécuter : python script.py
```

**Option B** : Échapper correctement
```powershell
python -c "print(\"hello\")"
```

### Prévention
- Pour scripts > 5 lignes : Créer fichier `.py`
- Utiliser write_to_file + run_command

---

## 🔴 Erreur #7 : Imports Relatifs Non Résolus

### Symptôme
```
ModuleNotFoundError: No module named 'modules'
```

### Contexte
Exécution d'un fichier Python depuis un sous-dossier.

### Code problématique
```bash
# Dans v4/modules/ui/pages/
python transactions.py  # ❌ Erreur !
```

### Solution
```bash
# Toujours depuis la racine v4/
cd c:\Users\djabi\gestion-financière\v4
streamlit run main.py  # ✅ Correct
```

### Prévention
- Lancer TOUJOURS depuis la racine du projet
- Utiliser imports absolus (pas relatifs)

---

## 🟡 Warning #1 : Imports Inutilisés

### Symptôme
Imports en haut de fichier mais jamais utilisés.

### Exemple
```python
from typing import Optional, Dict  # Dict utilisé, Optional non
```

### Impact
- Ralentit le chargement
- Code moins lisible
- Risque d'imports circulaires inutiles

### Solution
```python
# Supprimer ce qui n'est pas utilisé
from typing import Dict  # ✅
```

### Prévention
- Utiliser un linter (pylint, flake8)
- Nettoyer régulièrement

---

## 🟡 Warning #2 : Session State Non Initialisé

### Symptôme
```
KeyError: 'transactions_edit_mode'
```

### Code problématique
```python
# ❌ Direct sans vérification
if st.session_state.transactions_edit_mode:
```

### Solution
```python
# ✅ Toujours initialiser
if 'transactions_edit_mode' not in st.session_state:
    st.session_state.transactions_edit_mode = False

# Maintenant on peut utiliser
if st.session_state.transactions_edit_mode:
```

---

## 📊 Statistiques des Erreurs

| Type d'erreur | Fréquence | Gravité | Temps résolution |
|---------------|-----------|---------|------------------|
| Import circulaire | Haute | Critique | 15-30 min |
| Oubli normalisation | Moyenne | Importante | 5-10 min |
| Fichier trop gros | Basse | Moyenne | 1-2 heures |
| Navigation lente | Basse | Importante | 20-30 min |

---

## 🎓 Leçons Apprises

1. **Tester après CHAQUE modification** - Ne pas accumuler les changements
2. **Nommer explicitement** - Éviter les conflits de noms
3. **Normaliser systématiquement** - Ajouter dans checklist
4. **Refactorer progressivement** - Pas tout d'un coup
5. **Documenter les erreurs** - Pour ne pas répéter

---

## 📝 Template de rapport d'erreur

Quand tu rencontres une nouvelle erreur, ajoute-la ici avec :

```markdown
## 🔴 Erreur #{numéro} : {Titre court}

### Symptôme
{Message d'erreur exact}

### Contexte
{Qu'est-ce qui a causé l'erreur}

### Solution
{Code corrigé}

### Prévention
{Comment éviter à l'avenir}
```

---

**Dernière mise à jour** : 14 décembre 2024  
**Erreurs documentées** : 7 critiques + 2 warnings
