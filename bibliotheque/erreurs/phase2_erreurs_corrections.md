# Phase 2 - Erreurs et Corrections

**Période** : 19 décembre 2024 (Session Phase 2)  
**Context** : Finalisation OCR + Tests d'intégration

---

## Erreur #1 : Streamlit Widget State Modification

### 📍 Contexte
**Date** : 19 décembre 2024, 21h26  
**Fichier** : `main.py` ligne 141  
**Session** : Phase 2 finalisation + tests intégration

### ❌ Problème
```python
# APRÈS création du widget
page = st.sidebar.radio("Navigation", pages, key="nav_radio")

# ... plus tard ...
if st.session_state.get("requested_page"):
    st.session_state.nav_radio = st.session_state.requested_page  # ❌ ERREUR
```

**Message d'erreur** :
```
StreamlitAPIException: `st.session_state.nav_radio` cannot be modified 
after the widget with key `nav_radio` is instantiated.
```

### 🔍 Cause
Streamlit interdit la modification de `session_state` pour une clé de widget **après** que le widget soit créé. On essayait de changer `nav_radio` après avoir créé le `st.radio()` avec cette clé.

### ✅ Solution
Déplacer la modification AVANT la création du widget :

```python
# AVANT création du widget
if "nav_radio" not in st.session_state:
    st.session_state.nav_radio = "🏠 Accueil"

# Handle page change BEFORE widget creation
if st.session_state.get("requested_page"):
    st.session_state.nav_radio = st.session_state.requested_page
    st.session_state.requested_page = None

# Maintenant on crée le widget
page = st.sidebar.radio("Navigation", pages, key="nav_radio")
```

### 📝 Leçon
✅ **Règle Streamlit : Modifier session_state AVANT widget**  
✅ Ordre critique : Init → Modify → Create Widget  
✅ Ne jamais modifier state d'un widget après sa création

**Fix appliqué** : `main.py` lines 113-116

---

**Erreurs cataloguées Phase 2** : 1  
**Temps résolution** : 2 min  
**Impact** : Aucun - résolu immédiatement
