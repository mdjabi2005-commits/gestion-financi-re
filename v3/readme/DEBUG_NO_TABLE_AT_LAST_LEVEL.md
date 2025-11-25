# 🔍 DEBUG - Table Invisible au Dernier Niveau

## 🐛 Problème Rapporté

Je clique sur "Septembre" (dernier niveau) et **je ne vois pas de tableau**, seulement la navigation fractale.

---

## 🧐 Diagnostic Étape par Étape

### Étape 1️⃣ : Vérifier que tu es au DERNIER niveau

Quand tu navigues jusqu'à "Septembre", tu devrais voir dans la **console JavaScript (F12)** :

```
[FRACTAL] ═══════════════════════════════════
[FRACTAL] isLastLevel() Check:
[FRACTAL]   navigationStack: ['TR', 'REVENUS', 'UBER', 'SEPTEMBRE']
[FRACTAL]   currentLevel: 3
[FRACTAL]   currentNode: SUBCAT_REVENUS_UBER_SEPTEMBRE (ou similaire)
[FRACTAL]   node.children: 0
[FRACTAL] ✅ Niveau 3 → MODE SÉLECTION
[FRACTAL] ═══════════════════════════════════
```

**Si tu ne vois PAS cela** :
- ❌ Tu n'es peut-être pas au dernier niveau
- ❌ La console n'affiche pas les logs (vérifier F12 → Console tab)

---

### Étape 2️⃣ : Vérifier que le MODE SÉLECTION est activé

Dans la console JavaScript, tu devrais voir des logs comme :

```
[FRACTAL] Mode sélection: true
[FRACTAL] 🟢 Sélectionné: SUBCAT_REVENUS_UBER_SEPTEMBRE
[FRACTAL] Sélections actuelles: (1) ['SUBCAT_REVENUS_UBER_SEPTEMBRE']
```

**Si tu ne vois PAS "Mode sélection: true"** :
- ❌ Le système pense que tu es en mode NAVIGATION pas SÉLECTION
- ❌ Les triangles ne seront pas sélectionnables

---

### Étape 3️⃣ : Vérifier que l'URL est mise à jour

Après avoir cliqué sur un triangle :

1. Ouvre la **barre d'adresse** du navigateur
2. Cherche le paramètre `?fractal_selections=...`
3. Exemple : `http://localhost:8501/?fractal_selections=SUBCAT_REVENUS_UBER_SEPTEMBRE`

**Si l'URL ne change PAS** :
- ❌ JavaScript n'appelle pas `syncStateToURL()`
- ❌ La synchronisation URL ↔ Python ne fonct ionne pas

---

### Étape 4️⃣ : Vérifier le DEBUG sur la page

Dans la **colonne droite** de Streamlit, tu devrais voir :

```
🔍 DEBUG - État Actuel
└─ URL Query Params: {'fractal_selections': 'SUBCAT_REVENUS_UBER_SEPTEMBRE'}

🔍 DEBUG: selections_from_url = `SUBCAT_REVENUS_UBER_SEPTEMBRE`

🔍 DEBUG: Parsed 1 codes from URL: ['SUBCAT_REVENUS_UBER_SEPTEMBRE']
```

**Si les DEBUG affichent vide** :
- ❌ L'URL n'est pas mise à jour par JavaScript
- ❌ Streamlit ne lit pas les query params

---

## 🎯 Solutions Par Cas

### CAS A : J'ai "currentLevel: 3" et "MODE SÉLECTION" mais URL ne change pas

**Problème** : `syncStateToURL()` n'est pas appelée ou échoue

**Solution** :
1. Ouvre la console JavaScript (F12 → Console)
2. Copie-colle ceci :
```javascript
// Forcer la synchronisation
syncStateToURL();
console.log('URL after sync:', window.location.href);
```
3. Si l'URL ne change pas après, le problème est dans `syncStateToURL()`

**Fix** : Vérifie que `window.history.replaceState()` est supporté

---

### CAS B : J'ai l'URL correcte mais le DEBUG affiche vide

**Problème** : Streamlit ne lit pas l'URL (query params non parsés)

**Solution** :
1. Essaie de **refresh la page** (F5)
2. Après refresh, l'URL devrait persister et être lue
3. Si ça marche après refresh, c'est un problème de synchronisation temps réel

**Fix** : Ajouter un bouton "Synchroniser" que l'utilisateur clique après sélection

---

### CAS C : Tout semble bon mais pas de tableau

**Problème** : Le tableau est filtré mais retourne 0 résultats

**Solution** :
1. Ajoute ceci après le DEBUG :
```python
st.write("**DEBUG - Selected nodes list:**", selected_nodes_list)
st.write("**DEBUG - Number of transactions:**", len(df_all))

if selected_nodes_list:
    df_filtered = get_transactions_for_codes(selected_nodes_list, df_all)
    st.write("**DEBUG - Filtered DF rows:**", len(df_filtered))
    st.write("**DEBUG - Filtered DF sample:**")
    st.dataframe(df_filtered.head(10))
```

2. Vérifier que :
   - `selected_nodes_list` contient le bon code
   - `df_filtered` a des lignes
   - Les catégories/sous-catégories correspondent à la BD

---

### CAS D : Je ne vois pas le tableau même avec les étapes A-C correctes

**Problème** : C'est un problème d'interface Streamlit

**Solution** :
1. Vérifier que le `if selected_nodes_list:` est vrai
2. Ajouter du debug juste après :
```python
if selected_nodes_list:
    st.write("✅ TABLEAU DEVRAIT APPARAÎTRE ICI")
    st.markdown("---")
    # ... rest of code
```

3. Si "✅ TABLEAU DEVRAIT APPARAÎTRE ICI" n'est pas affiché, c'est que `selected_nodes_list` est vide

---

## 🔧 Checklist de Débogage Rapide

Copie-colle cette checklist et vérifie chaque point :

```
JAVASCRIPT SIDE (F12 → Console):
[ ] Voir logs avec "[FRACTAL]"
[ ] currentLevel = 3
[ ] Mode sélection: true
[ ] URL change après clic (regarder barre d'adresse)
[ ] Voir log [SYNC-URL] Updated URL
[ ] Voir logs des sélections (🟢 Sélectionné)

PYTHON SIDE (Streamlit page):
[ ] Voir DEBUG affichant l'URL query params
[ ] Voir selections_from_url non-vide
[ ] Voir "Parsed X codes from URL"
[ ] Voir selected_nodes_list contenant le code

TABLE SHOULD APPEAR:
[ ] Voir "Filtres actifs:"
[ ] Voir les badges des filtres
[ ] Voir le tableau avec transactions
[ ] Voir statistiques (montants, count)
```

---

## 🛠️ Tests Manuels

### TEST 1️⃣ : Vérifier que le DERNIER niveau est détecté

```
1. Naviguer : TR → Revenus → Uber → Septembre
2. F12 → Console
3. Chercher: [FRACTAL] ✅ Niveau 3 → MODE SÉLECTION
```

**Résultat attendu** : ✅ Message visible

---

### TEST 2️⃣ : Vérifier que la sélection fonctionne

```
1. Même navigation
2. Cliquer sur le triangle "Septembre"
3. F12 → Console
4. Chercher: [FRACTAL] 🟢 Sélectionné
```

**Résultat attendu** : ✅ Message visible après clic

---

### TEST 3️⃣ : Vérifier que l'URL change

```
1. Même navigation et clic
2. Regarder la barre d'adresse
3. Elle devrait contenir: ?fractal_selections=SUBCAT_...
```

**Résultat attendu** : ✅ URL change après 500ms

---

### TEST 4️⃣ : Vérifier que Streamlit lit l'URL

```
1. Même étapes
2. Regarder la colonne DROITE
3. Chercher: 🔍 DEBUG: selections_from_url = `SUBCAT_...`
```

**Résultat attendu** : ✅ DEBUG affiche la sélection

---

### TEST 5️⃣ : Vérifier que le tableau apparaît

```
1. Même étapes
2. Regarder en dessous du DEBUG
3. Tableau devrait apparaître avec transactions
```

**Résultat attendu** : ✅ Tableau affiche les données

---

## 📋 Logs Importants à Noter

Quand tu investigues, **copie ces informations** :

1. **Console JavaScript (F12 → Console)** :
   - Tous les logs `[FRACTAL]`
   - Tous les logs `[SYNC]`
   - Les erreurs rouges (si any)

2. **DEBUG Streamlit** (colonne droite) :
   - Les valeurs affichées
   - Les codes parsés
   - Les filtres actifs

3. **Terminal Streamlit** :
   - Erreurs Python
   - Logs d'exécution
   - Messages de débogage

---

## 🎯 Points de Vérification Finaux

**Si AUCUNE de tes vérifications ne montre le problème** :

1. **Force un refresh** : F5 dans le navigateur
2. **Vérifie la BD** : Est-ce qu'il y a réellement des transactions pour "Septembre" ?
3. **Teste avec une autre catégorie** : Ex: un autre mois ou catégorie
4. **Vérifie la console du terminal Streamlit** pour les erreurs Python

---

## 📞 Rapport de Bug

Si le problème persiste, fournis :

1. **Screenshot du DEBUG affichant** :
   - URL Query Params
   - Session State
   - selections_from_url

2. **Screenshot de la console F12** montrant :
   - Les logs [FRACTAL]
   - L'URL actuelle

3. **Screenshot du terminal Streamlit** (s'il y a des erreurs)

---

Avec cette checklist, tu devrais identifier **exactement** où le système échoue ! 🎯

