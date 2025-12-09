# 🔺 Guide Rapide - Interface Unifiée de Navigation Fractale

## 🎯 Objectif

L'interface combine **Navigation par Triangles Fractals** (gauche 60%) avec un **Tableau de Transactions Dynamique** (droite 40%) dans une **SEULE INTERFACE COHÉRENTE**.

---

## 🎮 Comment Utiliser

### 1️⃣ **Naviguer dans la Hiérarchie**

```
Univers Financier (TR)
    ↓
Clic sur triangle → Zoom dans Dépenses
    ↓
Clic sur triangle → Zoom dans Supermarché
    ↓
✅ Vous êtes au dernier niveau = Mode Sélection Activé
```

**Boutons disponibles** :
- `← Retour` : Remonte d'un niveau (filtres restent actifs ✅)
- `🏠 Vue d'ensemble` : Retour à la racine + reset des filtres

---

### 2️⃣ **Sélectionner des Catégories**

Au dernier niveau (ex: Supermarché), vous voyez les sous-catégories en **triangles**.

**Cliquer sur un triangle** = Sélectionner/Désélectionner

**Indications visuelles** :
- 🔵 **Bleu brillant** = Sélectionné
- ✓ **Checkmark** = Confirmé
- ⚪ **Gris** = Non sélectionné

---

### 3️⃣ **Le Tableau se Met à Jour Automatiquement**

Dès que vous sélectionnez un triangle :

**Colonne Droite** affiche :
- 🎯 **Filtres Actifs** : Badges avec codes sélectionnés
- 📊 **Statistiques** : Montants, nombre de transactions
- 📋 **Tableau** : Les transactions filtrées
- 💾 **Export CSV** : Bouton pour télécharger

---

### 4️⃣ **Multi-Filtrage** ⭐

**Vous pouvez sélectionner PLUSIEURS sous-catégories** :

```
1. Cliquer "Bureau_Vallée" → Tableau affiche ses transactions
2. Cliquer "Leclerc" → Tableau affiche Bureau_Vallée + Leclerc (combinés)
3. Cliquer "Carrefour" → Tableau affiche Bureau_Vallée + Leclerc + Carrefour
```

Les transactions s'additionnent avec une **logique AND**.

---

### 5️⃣ **Navigation Intelligente avec Filtres Persistants**

Les filtres **RESTENT ACTIFS** même si vous naviguez :

```
Sélection actuelle : Bureau_Vallée, Leclerc (au Supermarché)
        ↓
Cliquer "← Retour" → Allez à "Dépenses"
        ↓
Naviguer vers "Restaurant"
        ↓
Cliquer "KFC"
        ↓
Tableau = Bureau_Vallée + Leclerc + KFC (3 sélections) ✅
```

**C'est utile pour comparer plusieurs catégories** !

---

### 6️⃣ **Supprimer un Filtre**

Dans la section "Filtres Actifs" à droite, chaque badge a un bouton `❌` :

```
Filtres Actifs:
🔹 Bureau_Vallée    [❌]  ← Cliquer pour retirer
🔹 Leclerc          [❌]
🔹 KFC              [❌]
```

Cliquer `❌` = Retirer le filtre instantanément

---

### 7️⃣ **Reset Complet**

Cliquer le bouton `🏠 Vue d'ensemble` (en bas du fractal) :

```
✅ Retour à la racine "TR"
✅ Tous les filtres supprimés
✅ Tableau affiche statistiques globales
```

---

## 📊 Vue d'Ensemble de l'Interface

```
┌─────────────────────────────────────────────────────────────┐
│  🔺 Navigation Fractale Unifiée                             │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│ ┌──────────────────────────┐  ┌──────────────────────────┐  │
│ │                          │  │                          │  │
│ │  60% - TRIANGLES         │  │  40% - TABLEAU           │  │
│ │  ─────────────────       │  │  ────────────────        │  │
│ │                          │  │                          │  │
│ │  Breadcrumb              │  │  🎯 Filtres Actifs       │  │
│ │  TR → Dépenses → Super   │  │  Bureau_Vallée [❌]      │  │
│ │                          │  │  Leclerc [❌]           │  │
│ │  [Triangles Fractals]    │  │  ──────────────          │  │
│ │                          │  │                          │  │
│ │  🔵 Bureau_Vallée        │  │  📊 Statistiques         │  │
│ │  🔵 Leclerc              │  │  Trans: 25               │  │
│ │  ⚪ Carrefour            │  │  Revenus: 0€             │  │
│ │  ⚪ Auchan               │  │  Dépenses: 523€          │  │
│ │  ⚪ Photomaton           │  │  Solde: -523€            │  │
│ │                          │  │                          │  │
│ │  [Zooms]                 │  │  📋 Tableau              │  │
│ │  ← Retour                │  │  [Transactions ...]      │  │
│ │  🏠 Vue d'ensemble       │  │                          │  │
│ │                          │  │  💾 Exporter CSV         │  │
│ └──────────────────────────┘  └──────────────────────────┘  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 💡 Cas d'Usage Courants

### Cas 1️⃣ : "Je veux voir mes dépenses chez Bureau_Vallée"

```
1. Naviguer : TR → Dépenses → Supermarché
2. Cliquer "Bureau_Vallée"
3. Tableau affiche automatiquement ses transactions
✅ Fait !
```

### Cas 2️⃣ : "Je veux comparer Bureau_Vallée, Leclerc et Carrefour"

```
1. Naviguer : TR → Dépenses → Supermarché
2. Cliquer "Bureau_Vallée"
3. Cliquer "Leclerc"
4. Cliquer "Carrefour"
5. Tableau affiche les 3 combinés, avec total additionnés
✅ Comparaison terminée !
```

### Cas 3️⃣ : "Je veux ajouter mes dépenses restaurant à ma sélection supermarché"

```
1. Sélections actuelles : Bureau_Vallée + Leclerc (Supermarché)
2. ← Retour vers "Dépenses"
3. Naviguer vers "Restaurant"
4. Cliquer "KFC"
5. Tableau = Bureau_Vallée + Leclerc + KFC ✅
6. Vous pouvez continuer à ajouter : "Subway", "McDo", etc.
✅ Multi-catégorie contrôlée !
```

### Cas 4️⃣ : "Je veux commencer frais"

```
1. N'importe où dans l'interface
2. Cliquer "🏠 Vue d'ensemble"
3. Reset total, retour à zéro
✅ Nouveau départ !
```

---

## 🔍 Conseils & Astuces

### Astuce 1️⃣ : Comprendre les Montants

- **Bleu dans les triangles** = Total pour cette catégorie
- **Tableau à droite** = Transactions individuelles
- **Statistiques** = Sommes des transactions filtrées

### Astuce 2️⃣ : Combiner les Filtres Intelligemment

Les filtres utilisent une **logique AND** :
- Bureau_Vallée **ET** Leclerc = Transactions dans les deux
- Bureau_Vallée **ET** Leclerc **ET** KFC = Transactions dans les trois

### Astuce 3️⃣ : Exporter les Données

Une fois vos filtres appliqués, le bouton **💾 Exporter CSV** télécharge exactement ce que vous voyez dans le tableau.

### Astuce 4️⃣ : Persistent Filters = Puissant

Ne pas oublier que les filtres restent actifs en naviguant. C'est puissant pour analyser plusieurs catégories à la fois !

---

## ❌ Dépannage

### ❌ Les triangles ne changent pas de couleur quand je clique

**Solution** :
1. Ouvrir la console (F12)
2. Chercher si le console.log affiche `Mode sélection: true`
3. Si c'est `false`, vous n'êtes pas au dernier niveau
4. Vérifier le breadcrumb = doit avoir 3 niveaux

### ❌ Le tableau ne se met pas à jour

**Solution** :
1. Vérifier l'URL = elle doit contenir `?fractal_selections=...`
2. Vérifier le localStorage (F12 → Application → Local Storage)
3. Si l'URL ne change pas, refresh la page

### ❌ Les filtres disparaissent en naviguant

**Cela ne devrait pas arriver**, mais si c'est le cas :
1. C'est probablement un bug
2. Cliquer "🏠 Vue d'ensemble"
3. Recommencer la sélection

---

## 📞 Support

Si quelque chose ne fonctionne pas :

1. Ouvrir la console (F12 → Onglet Console)
2. Chercher les erreurs rouges
3. Noer les codes `[FRACTAL]` et `[SYNC]`
4. Les signaler avec screenshot de la console

---

## 🎯 Résumé des Raccourcis

| Action | Résultat |
|--------|----------|
| Clic sur triangle (dernier niveau) | Toggle sélection |
| Clic sur triangle (autres niveaux) | Navigate deeper |
| Clic `← Retour` | Remonter + filtres restent |
| Clic `🏠 Vue d'ensemble` | Reset complet |
| Clic `❌` dans Filtres Actifs | Retirer ce filtre |
| Clic `💾 Exporter CSV` | Télécharger les données |

---

**Bienvenue dans l'interface unifiée !** 🎉

L'interface est maintenant **fluide, cohérente et intuitive**. Profitez de l'expérience !

