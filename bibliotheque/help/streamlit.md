# 📚 Bibliothèque : Streamlit

## 🎯 Qu'est-ce que Streamlit ?

**Streamlit** est un framework Python open-source pour créer rapidement des **applications web interactives** sans écrire de HTML/CSS/JavaScript. Parfait pour les data scientists et développeurs Python qui veulent partager leurs analyses et outils.

**Site officiel** : https://streamlit.io  
**Documentation** : https://docs.streamlit.io

---

## 💡 Pourquoi Streamlit dans notre projet ?

1. **Rapidité de développement** : Créer une interface en quelques lignes
2. **Pas de frontend séparé** : Tout en Python
3. **Réactivité automatique** : L'app se met à jour quand les données changent
4. **Composants riches** : Graphiques, tableaux, formulaires, etc.
5. **Gratuit et open-source**

---

## 🔧 Concepts de base

### 1. Script = Application

Ton application Streamlit est juste un script Python qui s'exécute de haut en bas.

```python
# main.py
import streamlit as st

st.title("Mon Application")
st.write("Hello World!")
```

**Lancer** :
```bash
streamlit run main.py
```

---

### 2. Réactivité automatique (Reruns)

À chaque interaction utilisateur, **tout le script est ré-exécuté**. C'est le concept central de Streamlit.

```python
import streamlit as st

# Compteur d'exécutions
if 'count' not in st.session_state:
    st.session_state.count = 0

st.session_state.count += 1
st.write(f"Script exécuté {st.session_state.count} fois")

# Chaque clic = rerun complet
if st.button("Cliquer"):
    st.write("Bouton cliqué !")
```

---

### 3. Session State (État persistant)

Pour **conserver des données entre les reruns** :

```python
import streamlit as st

# Initialisation
if 'nom' not in st.session_state:
    st.session_state.nom = ""

# Modification
st.session_state.nom = st.text_input("Nom", st.session_state.nom)

# Lecture
st.write(f"Bonjour {st.session_state.nom}")
```

**Dans notre app (exemple concret)** :
```python
# Stocker la page demandée pour navigation programmée
st.session_state.requested_page = "💳 Transactions"

# Lire dans main.py
if st.session_state.get("requested_page"):
    navigate_to(st.session_state.requested_page)
```

---

## 📦 Composants utilisés dans notre app

### Entrées utilisateur

**Boutons** :
```python
if st.button("➕ Ajouter"):
    # Action
    pass

# Avec clé unique (important !)
if st.button("Supprimer", key="btn_delete_42"):
    delete_transaction(42)
```

**Champs texte** :
```python
nom = st.text_input("Nom")
description = st.text_area("Description")
```

**Sélection** :
```python
categorie = st.selectbox("Catégorie", ["Alimentation", "Transport"])
```

**Nombres** :
```python
montant = st.number_input("Montant", min_value=0.0, step=0.01)
```

**Dates** :
```python
date = st.date_input("Date")
```

---

### Affichage

**Texte** :
```python
st.title("Titre principal")
st.header("En-tête")
st.subheader("Sous-titre")
st.write("Texte normal ou n'importe quoi")
```

**Markdown** :
```python
st.markdown("## Titre 2")
st.markdown("**Gras** et *italique*")

# HTML inline
st.markdown("<p style='color:red'>Rouge</p>", unsafe_allow_html=True)
```

**Métriques** :
```python
st.metric(
    label="Solde", 
    value="1 234 €",
    delta="+150 €"  # Affiche une flèche verte
)
```

**Tableaux** :
```python
import pandas as pd

df = pd.DataFrame({
    'Nom': ['Alice', 'Bob'],
    'Montant': [100, 200]
})

st.dataframe(df)  # Tableau interactif
st.table(df)      # Tableau statique
```

**Graphiques** :
```python
import plotly.graph_objects as go

fig = go.Figure(data=[go.Bar(x=['A', 'B'], y=[10, 20])])
st.plotly_chart(fig, use_container_width=True)
```

---

### Layout

**Colonnes** :
```python
col1, col2, col3 = st.columns([1, 2, 1])  # Proportions

with col1:
    st.write("Colonne 1")

with col2:
    st.write("Colonne 2")

with col3:
    st.write("Colonne 3")
```

**Sidebar** :
```python
with st.sidebar:
    st.title("Menu")
    page = st.radio("Page", ["Accueil", "Transactions"])
```

**Tabs** :
```python
tab1, tab2 = st.tabs(["Onglet 1", "Onglet 2"])

with tab1:
    st.write("Contenu 1")

with tab2:
    st.write("Contenu 2")
```

**Expander (accordéon)** :
```python
with st.expander("Voir plus"):
    st.write("Contenu caché par défaut")
```

---

### Feedback utilisateur

**Messages** :
```python
st.success("✅ Succès")
st.info("ℹ️ Information")
st.warning("⚠️ Attention")
st.error("❌ Erreur")
```

**Spinner (chargement)** :
```python
with st.spinner("Chargement en cours..."):
    time.sleep(2)  # Opération longue
    st.success("Terminé !")
```

**Toast (notification)** :
```python
st.toast("Notification !", icon="🎉")
```

---

## 🔄 Gestion des reruns

### Problème : Reruns en boucle

```python
# ❌ MAUVAIS - Boucle infinie !
if st.button("Click"):
    st.session_state.value = 42
    st.rerun()  # Ne JAMAIS faire ça dans un if button !
```

### Solution : st.stop()

```python
# ✅ BON - Arrête l'exécution
if st.session_state.get("requested_page"):
    st.stop()  # Stoppe complètement le script
```

### Exemple dans notre app (main.py)

```python
# Si changement de page demandé, rerun AVANT de rendre quoi que ce soit
if st.session_state.get("requested_page"):
    st.session_state.nav_radio = st.session_state.requested_page
    st.session_state.requested_page = None
    st.rerun()  # Rerun immédiat, rien ne s'affiche après

# Sinon, afficher la page normalement
if page == "Accueil":
    interface_accueil()
```

---

## 💾 Cache (Performance)

Pour **éviter de recalculer** les données à chaque rerun :

**Cache de données** :
```python
@st.cache_data
def load_transactions():
    # Opération coûteuse (lecture DB, calculs...)
    df = pd.read_sql("SELECT * FROM transactions", conn)
    return df

# Appelé plusieurs fois, mais calculé 1 seule fois !
df = load_transactions()
```

**Invalidation du cache** :
```python
# Manuellement
st.cache_data.clear()

# Avec TTL (Time To Live)
@st.cache_data(ttl=300)  # 5 minutes
def get_data():
    return expensive_computation()
```

**Dans notre app** (`fractal_service.py`) :
```python
@st.cache_data
def _build_fractal_hierarchy_cached(date_debut, date_fin):
    # Construction de la hiérarchie (coûteux)
    return build_hierarchy()

# Invalidation intelligente si nb transactions change
if current_count != st.session_state.last_transaction_count:
    st.cache_data.clear()
```

---

## 🎨 Configuration de l'app

**`st.set_page_config()`** - À appeler EN PREMIER :

```python
st.set_page_config(
    page_title="Gestio V4",
    page_icon="💰",
    layout="wide",           # ou "centered"
    initial_sidebar_state="expanded"  # ou "collapsed"
)
```

**CSS personnalisé** :
```python
st.markdown("""
<style>
    .stMetric { margin-bottom: 0rem !important; }
    [data-testid="stHeading"] { color: red; }
</style>
""", unsafe_allow_html=True)
```

---

## ⚠️ Pièges courants

### 1. Keys manquantes (widgets)

```python
# ❌ ERREUR si 2 boutons identiques
st.button("Supprimer")
st.button("Supprimer")  # DuplicateWidgetID !

# ✅ Solution : keys uniques
st.button("Supprimer", key="delete_1")
st.button("Supprimer", key="delete_2")
```

### 2. Variables perdues entre reruns

```python
# ❌ Variable perdue à chaque rerun
count = 0
if st.button("Incrémenter"):
    count += 1  # Toujours 1 !
st.write(count)

# ✅ Utiliser session_state
if 'count' not in st.session_state:
    st.session_state.count = 0

if st.button("Incrémenter"):
    st.session_state.count += 1
st.write(st.session_state.count)
```

### 3. Reruns infinis

```python
# ❌ Boucle infinie
if some_condition:
    st.rerun()  # Déclenché à chaque rerun !

# ✅ Condition qui devient fausse
if st.session_state.get("need_rerun"):
    st.session_state.need_rerun = False  # Désactiver
    st.rerun()
```

---

## 📖 Ressources

- **Documentation officielle** : https://docs.streamlit.io
- **Cheat sheet** : https://docs.streamlit.io/library/cheatsheet
- **Forum** : https://discuss.streamlit.io
- **Exemples** : https://streamlit.io/gallery

---

## 💡 Dans notre projet

Voici comment Streamlit est utilisé dans Gestio V4 :

| Fichier | Utilisation Streamlit |
|---------|----------------------|
| `main.py` | Configuration app, navigation, routing |
| `modules/ui/pages/*.py` | Toutes les pages de l'interface |
| `modules/ui/components/*.py` | Composants réutilisables |
| `modules/ui/helpers.py` | Fonctions utilitaires UI |
| `modules/ui/toast_components.py` | Notifications toast personnalisées |

**Composants personnalisés** (JavaScript + Python) :
- `modules/ui/sunburst_navigation` - Navigation circulaire
- `modules/ui/financial_tree_component` - Arbre financier D3.js
- `modules/ui/components/calendar_component` - Calendrier interactif
