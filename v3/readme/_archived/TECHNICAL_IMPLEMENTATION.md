# 🔧 Guide Technique - Implémentation Unifiée de Navigation Fractale

## 📚 Table des Matières

1. [Architecture Globale](#architecture-globale)
2. [Synchronisation JavaScript ↔ Streamlit](#synchronisation-javascript--streamlit)
3. [Flux de Données](#flux-de-données)
4. [Codes de Nœuds](#codes-de-nœuds)
5. [Fonctions Clés](#fonctions-clés)
6. [Dépannage Avancé](#dépannage-avancé)

---

## Architecture Globale

```
┌─────────────────────────────────────────────────────────────────┐
│ NAVIGATEUR - Rendu HTML (Components.html)                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────────────────────┐  ┌─────────────────────┐   │
│  │ fractal.js (Canvas + Events)    │  │ Sync Script         │   │
│  ├─────────────────────────────────┤  ├─────────────────────┤   │
│  │                                 │  │                     │   │
│  │ - hierarchyData (injecté)       │  │ Reads localStorage  │   │
│  │ - currentNode = 'TR'            │  │ Updates URL via     │   │
│  │ - navigationStack = ['TR']      │  │ window.history      │   │
│  │ - selectedNodes = new Set()     │  │ replaceState()      │   │
│  │ - isSelectionMode = false       │  │                     │   │
│  │                                 │  │ Syncs every 200ms   │   │
│  │ Events:                         │  │                     │   │
│  │ - handleCanvasClick()           │  └─────────────────────┘   │
│  │ - toggleSelection()             │                             │
│  │ - handleZoomIn()                │  ┌─────────────────────┐   │
│  │ - handleBack()                  │  │ localStorage        │   │
│  │ - handleReset()                 │  ├─────────────────────┤   │
│  │                                 │  │ fractal_state_v6    │   │
│  │ Render:                         │  │ {                   │   │
│  │ - drawTriangle()                │  │   selectedNodes: [] │   │
│  │ - render(node)                  │  │   action: 'sel'     │   │
│  │                                 │  │   level: 3          │   │
│  │ Sync:                           │  │ }                   │   │
│  │ - sendSelectionToStreamlit()    │  │                     │   │
│  │                                 │  └─────────────────────┘   │
│  └─────────────────────────────────┘                             │
│                                                                   │
│  Browser URL:                                                    │
│  http://localhost:8501/?fractal_selections=CODE1,CODE2          │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                           ↓ HTTP GET
┌─────────────────────────────────────────────────────────────────┐
│ SERVEUR - Streamlit (Python)                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  interface_fractal_unified()                                    │
│  ├─ init_session_state()                                        │
│  ├─ sync_fractal_selections_from_js()  ← Injecte script sync   │
│  ├─ build_fractal_hierarchy()          ← Hierarchy data        │
│  ├─ load_transactions()                ← Toutes les trans      │
│  │                                                               │
│  └─ Colonne gauche (60%):                                       │
│     └─ fractal_navigation(hierarchy)   ← Affiche canvas        │
│                                                                   │
│  └─ Colonne droite (40%):                                       │
│     ├─ st.query_params.get('fractal_selections')               │
│     ├─ Parse selections_from_url                               │
│     ├─ Update st.session_state.fractal_manual_filters           │
│     │                                                            │
│     └─ if selected_nodes_list:                                  │
│        ├─ display_active_filters()                              │
│        ├─ get_transactions_for_codes()     ← Filtrer trans      │
│        ├─ Calculate statistics                                  │
│        └─ display_transactions_table()                          │
│                                                                   │
│        else:                                                     │
│        └─ Display global statistics                             │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Synchronisation JavaScript ↔ Streamlit

### Mécanisme de Synchronisation

```
JavaScript                      Communication               Streamlit
──────────────────────────────────────────────────────────────────────

selectedNodes
= {'CODE1', 'CODE2'}
    ↓
sendSelectionToStreamlit()
    ↓
localStorage.setItem()          [localStorage]
sessionStorage.setItem()        [sessionStorage]
    ↓
syncStateToURL()
    ↓
window.history.replaceState()   [URL Update]    ─→ Browser Address Bar
                                                    ├─ /page
                                                    └─ ?fractal_selections=CODE1,CODE2
                                                            ↓
                                                    Page reload (auto)
                                                            ↓
                                                    Streamlit re-renders
                                                            ↓
                                                    Python code runs
                                                            ↓
                                                    st.query_params
                                                    .get('fractal_selections')
                                                            ↓
                                                    Parse & Extract codes
                                                            ↓
                                                    get_transactions_for_codes()
                                                            ↓
                                                    Render tableau + stats
```

### Points Clés

1. **localStorage** : Persistence côté client (survit aux refresh)
2. **URL Query Params** : Communication avec le serveur Streamlit
3. **synchronisation bidirectionnelle** :
   - User clique triangle → localStorage + URL update
   - Streamlit lit URL → affiche tableau

---

## Flux de Données

### Flux 1 : Sélection Simple

```
User clicks triangle "CODE1"
    ↓
handleCanvasClick()
    ├─ isPointInTriangle() = true
    ├─ isSelectionMode = true (niveau 3)
    └─ toggleSelection('CODE1')
        ├─ selectedNodes.add('CODE1')
        ├─ render()
        └─ sendSelectionToStreamlit()
            ├─ state = {selectedNodes: ['CODE1'], ...}
            ├─ localStorage.setItem() ✅
            └─ syncStateToURL()
                ├─ params = 'fractal_selections=CODE1'
                ├─ window.history.replaceState()
                └─ URL changes to ?fractal_selections=CODE1
                    ↓
                    Streamlit detects URL change
                    ↓
                    st.query_params.get('fractal_selections')
                    = 'CODE1'
                    ↓
                    Parse to ['CODE1']
                    ↓
                    get_transactions_for_codes(['CODE1'])
                    ↓
                    Render tableau with CODE1 transactions
```

### Flux 2 : Multi-Sélection

```
Current state: selectedNodes = {'CODE1'}
URL: ?fractal_selections=CODE1

User clicks triangle "CODE2"
    ↓
toggleSelection('CODE2')
    ├─ selectedNodes.add('CODE2')
    ├─ selectedNodes = {'CODE1', 'CODE2'}  ← Set contains both
    ├─ render() ← Both triangles highlighted blue
    └─ sendSelectionToStreamlit()
        ├─ state.selectedNodes = ['CODE1', 'CODE2']
        ├─ localStorage updated ✅
        └─ syncStateToURL()
            ├─ params = 'fractal_selections=CODE1,CODE2'
            ├─ URL changes
            ↓
            Streamlit re-renders
            ↓
            st.query_params = 'CODE1,CODE2'
            ↓
            Parse to ['CODE1', 'CODE2']
            ↓
            get_transactions_for_codes(['CODE1', 'CODE2'])
            ├─ Filter AND logic: (CODE1) AND (CODE2)
            └─ Returns combined transactions ✅
```

---

## Codes de Nœuds

### Structure des Codes

```
Level 0 (Root)
└── TR                           Univers Financier (racine)

Level 1 (Type)
├── REVENUS                      Catégorie Revenus
└── DEPENSES                     Catégorie Dépenses

Level 2 (Category)
├── CAT_SALAIRE                  Catégorie: Salaire (sous REVENUS)
├── CAT_FREELANCE                Catégorie: Freelance (sous REVENUS)
├── CAT_ALIMENTATION             Catégorie: Alimentation (sous DEPENSES)
├── CAT_TRANSPORT                Catégorie: Transport (sous DEPENSES)
└── ...

Level 3+ (Subcategory) ← MODE SÉLECTION FORCÉ
├── SUBCAT_SALAIRE_NET           Code: SUBCAT_CATEGORIE_SOUSCAT
├── SUBCAT_ALIMENTATION_COURSES  (Format: SUBCAT_UPPER_UPPER)
├── SUBCAT_ALIMENTATION_RESTAURANT
├── SUBCAT_ALIMENTATION_LECLERC
├── SUBCAT_ALIMENTATION_BUREAU_VALLEE
├── SUBCAT_RESTAURANT_KFC
├── SUBCAT_TRANSPORT_ESSENCE
└── ...
```

### Format Codes

```javascript
// JavaScript côté client :
// Code format: SUBCAT_CATEGORIE_SOUSCATEGORIE
// Exemple: "SUBCAT_ALIMENTATION_BUREAU_VALLEE"

// Parser en Python :
// "SUBCAT_ALIMENTATION_BUREAU_VALLEE"
// parts = code[7:].split('_', 1)
// parts[0] = 'ALIMENTATION'
// parts[1] = 'BUREAU_VALLEE'

// Conversion pour la DB :
// Catégorie: 'Alimentation' (title case)
// Sous-catégorie: 'Bureau Vallée' (replace _ avec space, title case)
```

---

## Fonctions Clés

### JavaScript

#### `toggleSelection(nodeCode)`

```javascript
function toggleSelection(nodeCode) {
    // Toggle add/remove from selectedNodes Set
    if (selectedNodes.has(nodeCode)) {
        selectedNodes.delete(nodeCode);
        console.log('[FRACTAL] 🔴 Désélectionné:', nodeCode);
    } else {
        selectedNodes.add(nodeCode);
        console.log('[FRACTAL] 🟢 Sélectionné:', nodeCode);
    }

    // Re-render pour montrer le changement visuel
    render(hierarchyData[currentNode]);

    // Envoyer l'état à Streamlit
    sendSelectionToStreamlit();
}
```

**Quand appelée** : Lors d'un clic triangle en mode sélection

**Effet** :
- Ajoute/retire du Set `selectedNodes`
- Met à jour localStorage
- Met à jour URL
- Rend les triangles en bleu si sélectionnés

---

#### `sendSelectionToStreamlit()`

```javascript
function sendSelectionToStreamlit() {
    const state = {
        action: isSelectionMode ? 'selection' : 'navigation',
        currentNode: currentNode,
        selectedNodes: Array.from(selectedNodes),  // ← Converti en Array
        level: navigationStack.length,
        isSelectionMode: isSelectionMode
    };

    console.log('[FRACTAL] 📤 Envoi à Streamlit:', state);

    // Triple communication :

    // 1. localStorage/sessionStorage
    window.sessionStorage.setItem('fractal_state_v6', JSON.stringify(state));
    window.localStorage.setItem('fractal_state_v6', JSON.stringify(state));

    // 2. postMessage
    window.parent.postMessage({type: 'fractal_state', data: state}, '*');

    // 3. CustomEvent
    document.dispatchEvent(new CustomEvent('fractalStateChanged', {detail: state}));
}
```

**Quand appelée** :
- Après chaque sélection/désélection
- Après navigation
- Après reset

**Effet** :
- Sauvegarde état dans localStorage ✅
- Envoie messages au parent
- Trigger CustomEvent

---

### Python

#### `sync_fractal_selections_from_js()`

```python
def sync_fractal_selections_from_js():
    """Injecte un script JavaScript pour synchroniser l'état via URL."""

    sync_script = """
    <script>
    // Lire l'état depuis localStorage
    function getFractalState() {
        const stateJson = localStorage.getItem('fractal_state_v6') ||
                         sessionStorage.getItem('fractal_state_v6');
        return JSON.parse(stateJson);
    }

    // Mettre à jour l'URL avec les sélections
    function syncStateToURL() {
        const state = getFractalState();
        const selections = state.selectedNodes || [];

        const params = new URLSearchParams();
        if (selections.length > 0) {
            params.set('fractal_selections', selections.join(','));
        }

        const newUrl = window.location.pathname + '?' + params.toString();
        window.history.replaceState({state}, '', newUrl);
    }

    // Sync périodiquement
    setInterval(syncStateToURL, 500);

    // Sync on change event
    document.addEventListener('fractalStateChanged', syncStateToURL);
    </script>
    """

    st.markdown(sync_script, unsafe_allow_html=True)
```

**Quand appelée** : Au début de `interface_fractal_unified()`

**Effet** :
- Injecte le script de synchronisation
- Script met à jour URL toutes les 500ms
- Streamlit détecte changement d'URL automatiquement

---

#### `get_transactions_for_codes(codes, df)`

```python
def get_transactions_for_codes(codes: List[str], df: pd.DataFrame) -> pd.DataFrame:
    """Filtre les transactions avec AND logic sur les codes."""

    if not codes:
        return pd.DataFrame()

    result_df = df.copy()

    for code in codes:
        # SUBCAT codes: SUBCAT_CATEGORIE_SOUSCATEGORIE
        if code.startswith('SUBCAT_'):
            parts = code[7:].split('_', 1)
            if len(parts) == 2:
                category = parts[0].title()           # 'Alimentation'
                subcategory = parts[1].replace('_', ' ').title()  # 'Bureau Vallée'
                result_df = result_df[
                    (result_df['categorie'].str.lower() == category.lower()) &
                    (result_df['sous_categorie'].str.lower() == subcategory.lower())
                ]

        # CAT codes: CAT_CATEGORIE
        elif code.startswith('CAT_'):
            category = code[4:].replace('_', ' ').title()
            result_df = result_df[result_df['categorie'].str.lower() == category.lower()]

        # Type codes: REVENUS, DEPENSES
        elif code == 'REVENUS':
            result_df = result_df[result_df['type'].str.lower() == 'revenu']
        elif code == 'DEPENSES':
            result_df = result_df[result_df['type'].str.lower() == 'dépense']

    return result_df
```

**Logique** : AND logic
- CODE1 AND CODE2 AND CODE3...
- Chaque code filtre le résultat précédent

**Exemple** :
```python
codes = ['SUBCAT_ALIMENTATION_LECLERC', 'SUBCAT_ALIMENTATION_BUREAU_VALLEE']
# Retourne: toutes les transactions qui sont
# (Alimentation ET Leclerc) OU (Alimentation ET Bureau_Vallée)
# = les deux catégories avec AND combinées
```

---

## Dépannage Avancé

### Problème 1 : URL ne se met pas à jour

**Symptômes** :
- Les triangles changent de couleur ✅
- Mais l'URL ne change pas ❌
- Le tableau ne se met pas à jour ❌

**Causes possibles** :
1. JavaScript ne trouve pas localStorage
2. syncStateToURL() n'est pas appelée
3. window.history.replaceState() échoue

**Debug** :
```javascript
// Dans la console (F12):
JSON.parse(localStorage.getItem('fractal_state_v6'))
// Doit afficher: {selectedNodes: [...], ...}

// Vérifier si syncStateToURL existe:
typeof syncStateToURL  // Doit être 'function'

// Appeler manuellement:
syncStateToURL();
// Puis vérifier l'URL
```

**Solution** :
- Vérifier que localStorage n'est pas désactivé
- Vérifier que les scripts s'exécutent sans erreur (F12 → Console)

---

### Problème 2 : Tableau ne se met pas à jour

**Symptômes** :
- URL change correctement ✅
- Mais le tableau affiche rien ❌

**Causes possibles** :
1. `st.query_params` ne lit pas l'URL
2. `get_transactions_for_codes()` retourne DataFrame vide
3. Erreur dans le parsing du code

**Debug** :
```python
# Ajouter temporairement dans fractal_unified.py:
st.write("URL params:", st.query_params)
st.write("Selections from URL:", selections_from_url)
st.write("Parsed list:", selected_nodes_list)
st.write("Session state:", st.session_state.fractal_manual_filters)
st.write("Filtered DF rows:", len(df_filtered) if df_filtered else 0)
```

**Solution** :
- Vérifier les logs dans le terminal Streamlit
- Vérifier que les codes correspondent à la BD

---

### Problème 3 : Glow bleu n'apparaît pas

**Symptômes** :
- Triangles se sélectionnent ✅
- Mais pas de couleur bleu ❌

**Causes possibles** :
1. `isSelected` toujours false
2. `selectedNodes.has(code)` ne fonctionne pas
3. drawTriangle() n'est pas appelée

**Debug** :
```javascript
// Dans drawTriangle():
console.log('Drawing triangle:', nodeData.code);
console.log('isSelected:', isSelected);
console.log('selectedNodes:', Array.from(selectedNodes));

// Vérifier la condition:
if (isSelected) {
    console.log('DRAWING BLUE GLOW for', nodeData.code);
    ctx.strokeStyle = '#3b82f6';
}
```

**Solution** :
- Vérifier que le code exact est dans selectedNodes
- Vérifier que drawTriangle est appelée après chaque clic

---

### Problème 4 : Les filtres disparaissent en naviguant

**Symptômes** :
- Sélections actives au niveau "Supermarché" ✅
- Retour vers "Dépenses" ❌
- Les sélections disparaissent ❌

**Causes possibles** :
1. `handleBack()` réinitialise selectedNodes (BUG!)
2. `handleReset()` appelée accidentellement
3. Page refreshée

**Debug** :
```javascript
// Dans handleBack():
console.log('Before back:', Array.from(selectedNodes));
// Naviguez
console.log('After back:', Array.from(selectedNodes));
// Les deux doivent être identiques
```

**Solution** :
- Vérifier que handleBack() NE contient PAS : `selectedNodes.clear()`
- handleReset() DOIT être la SEULE fonction qui réinitialise

---

## Logs Importants à Vérifier

### Console JavaScript

```
[FRACTAL] Mode sélection: true              ← Doit être true au niveau 3+
[FRACTAL] 🟢 Sélectionné: CODE1             ← Chaque sélection
[FRACTAL] 📤 Envoi à Streamlit: {...}       ← État envoyé
[SYNC-INIT] URL synchronization ready       ← Script sync chargé
[SYNC-URL] Updated URL: /page?fractal...    ← URL mise à jour
```

### Logs Python Streamlit

```
2025-11-23 ... [INFO] Running /modules/ui/pages/fractal_unified.py
2025-11-23 ... [DEBUG] Query params: {'fractal_selections': 'CODE1,CODE2'}
2025-11-23 ... [DEBUG] Filtered dataframe rows: 42
```

---

## Optimisations Futures

1. **Débounce URL updates** : Au lieu de 500ms, utiliser 100ms
2. **Compression état** : Coder les sélections en base64 pour URLShorter
3. **IndexedDB** : Pour persistence plus robuste qu'localStorage
4. **Real-time updates** : WebSockets au lieu de polling
5. **Server-side filtering** : Déplacer `get_transactions_for_codes()` en DB query

---

**Version** : 1.0
**Date** : 2025-11-23
**Auteur** : Claude Code

