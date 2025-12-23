# Règles - Module UI

## 🎯 Responsabilité

Interface utilisateur Streamlit, Pages, Composants

---

## 📋 Règles strictes

### 1. Séparation UI / Logique métier

**❌ INTERDIT** - Logique dans UI :
```python
# Dans une page Streamlit
def interface_transactions():
    # SQL direct
    conn = get_db_connection()  # MAUVAIS !
    
    # Logique complexe
    if categorie.lower() == "alimentation":  # Devrait être dans services
```

**✅ CORRECT** - UI appelle services :
```python
def interface_transactions():
    # Appel Repository
    transactions = TransactionRepository.get_all()
    
    # Appel service
    hierarchy = build_fractal_hierarchy()
    
    # UI uniquement
    st.dataframe(transactions)
```

---

### 2. Nommage des fonctions

**Format obligatoire** :

- **Pages complètes** : `interface_{nom}()`
- **Composants** : `render_{nom}()`
- **Helpers**: `{verbe}_{nom}()`

```python
def interface_voir_transactions():  # Page
def render_calendar(df):             # Composant
def load_transactions():             # Helper
```

---

### 3. Session State - Nommage

**Format** : `{page}_{variable}_{type}`

```python
# ✅ BON
st.session_state.transactions_edit_mode = False
st.session_state.cal_transactions_start_date = date.today()

# ❌ MAUVAIS
st.session_state.edit = False  # Trop général
st.session_state.d = date.today()  # Pas clair
```

---

### 4. Navigation entre pages

**TOUJOURS via `requested_page`** :

```python
# Dans une page
if st.button("Voir Transactions"):
    st.session_state.requested_page = "📊 Voir Transactions"
    st.rerun()
```

**Géré dans main.py AVANT rendu** :
```python
# main.py - AU DÉBUT
if 'requested_page' in st.session_state:
    current_page = st.session_state.requested_page
    del st.session_state.requested_page
    st.rerun()

# Maintenant afficher la page
if current_page == "🏠 Accueil":
    interface_accueil()
```

---

### 5. Structure fichiers pages

**Limite** : 500 lignes max par fichier

**Si dépassé** : Créer package
```
pages/
├── transactions/
│   ├── __init__.py       # Exports
│   ├── view.py           # Vue
│   └── add.py            # Ajout
```

---

## 🏗️ Comment ajouter

### Ajouter une nouvelle page

1. **Créer fichier** dans `modules/ui/pages/`
```python
# ma_page.py
import streamlit as st

def interface_ma_page():
    """Documentation claire"""
    st.title("Ma Page")
    # ...
```

2. **Exporter dans `__init__.py`**
```python
from .ma_page import interface_ma_page

__all__ = [..., 'interface_ma_page']
```

3. **Ajouter dans `main.py`**
```python
from modules.ui.pages import interface_ma_page

pages = {
    "📄 Ma Page": interface_ma_page
}
```

---

### Créer un composant réutilisable

**Emplacement** : `modules/ui/components/`

```python
# mon_composant.py
import streamlit as st

def render_mon_composant(data, key=None):
    """
    Composant réutilisable.
    
    Args:
        data: Données à afficher
        key: Clé Streamlit unique
        
    Returns:
        Résultat interaction utilisateur
    """
    with st.container():
        # Rendu composant
        result = st.selectbox("Choose", options, key=key)
        return result
```

---

## 🎨 Standards UI

### Couleurs projet

```python
COLORS = {
    "revenu": "#00D4AA",      # Vert
    "depense": "#FF6B6B",     # Rouge
    "primary": "#4A90E2",     # Bleu
    "warning": "#FFD93D",     # Jaune
    "dark_bg": "#1E1E1E"      # Fond sombre
}
```

### Icônes standards

```python
ICONS = {
    "transaction": "💳",
    "revenu": "💹",
    "depense": "💸",
    "calendar": "📅",
    "chart": "📊"
}
```

---

## 🚨 Erreurs courantes

### Erreur #1 : Session state non initialisé

**Problème** :
```python
if st.session_state.edit_mode:  # KeyError !
```

**Solution** :
```python
if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = False

if st.session_state.edit_mode:  # ✅
```

### Erreur #2 : Navigation lente

**Problème** : Composants lourds se chargent avant changement de page

**Solution** : Vérifier `requested_page` AVANT rendu

### Erreur #3 : Keys dupliquées

**Problème** :
```python
st.button("OK")  # Clé auto
st.button("OK")  # Même clé → Erreur !
```

**Solution** :
```python
st.button("OK", key="btn_save")
st.button("OK", key="btn_cancel")
```

---

## 📝 Checklist

Avant de commit :
- [ ] Pas de SQL direct
- [ ] Nommage fonction correct (`interface_`/`render_`)
- [ ] Session state initialisé
- [ ] Keys uniques sur widgets
- [ ] Navigation via `requested_page`
- [ ] Fichier < 500 lignes
- [ ] Imports absolus

---

## 🔗 Références

- [README module](../../v4/modules/ui/README.md)
- [Guide Streamlit](../../v4/help/streamlit.md)
- [Guide implémentation](../guides/IMPLEMENTATION_GUIDE.md)
