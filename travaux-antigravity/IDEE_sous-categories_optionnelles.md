# 💡 Idée : Sous-catégories Optionnelles + Intelligence LAMOMS-COACH

**Date** : 2 janvier 2026  
**Statut** : Idée à implémenter  
**Priorité** : Moyenne (après agents)

---

## 🎯 Problème Identifié

**Hiérarchie actuelle** : Type → Catégorie → Sous-catégorie (obligatoire) → Description

**Problèmes** :
- ❌ Sous-catégorie difficile à remplir pour certaines transactions
- ❌ Pas toujours pertinente (ex: "Salaire" n'a pas besoin de sous-catégorie)
- ❌ Crée de la friction lors de l'ajout rapide
- ❌ Graphiques parfois trop détaillés

---

## ✅ Solution Recommandée

### Rendre Sous-catégorie OPTIONNELLE

**Changements** :
1. Champ sous-catégorie devient facultatif dans formulaire
2. Graphiques adaptatifs (2 ou 3 niveaux selon données)
3. Catégories "simples" pré-définies (Salaire, Loyer, etc.)
4. Suggestions intelligentes pour catégories complexes

**Avantages** :
- ✅ Flexibilité maximale pour l'utilisateur
- ✅ Rapide pour transactions simples
- ✅ Détail disponible si besoin
- ✅ Pas de changement DB (déjà NULL-able)

---

## 🤖 Intelligence LAMOMS-COACH

### Cas d'Usage Principal

**Scénario** : Utilisateur a 50 transactions "Alimentation" sans sous-catégorie

**LAMOMS-COACH** :
1. **Détecte** : Trop de transactions dans une catégorie
2. **Analyse** : Patterns (montants, descriptions, fréquence)
3. **Suggère** : Sous-catégories pertinentes
   - Restaurant (20 trans, 25€ moy)
   - Courses (25 trans, 45€ moy)
   - Snacks (5 trans, 8€ moy)
4. **Applique** : Avec validation utilisateur
5. **Apprend** : Pour futures transactions

---

## 🔧 Outils pour LAMOMS-COACH

### 1. Analyser Distribution
```python
@tool
def analyze_category_distribution(category: str) -> dict:
    """Analyser si une catégorie a besoin de sous-catégories."""
    # Retourne suggestions basées sur patterns
```

### 2. Suggérer Sous-catégories
```python
@tool
def suggest_subcategories(category: str) -> list:
    """Suggérer sous-catégories via analyse ML."""
    # Analyse montants, descriptions, fréquence
```

### 3. Appliquer Sous-catégories
```python
@tool
def apply_subcategories(category: str, rules: dict) -> dict:
    """Appliquer automatiquement des sous-catégories."""
    # UPDATE transactions avec règles intelligentes
```

### 4. Nettoyer Sous-catégories
```python
@tool
def cleanup_subcategories(category: str) -> dict:
    """Supprimer sous-catégories peu utilisées."""
    # Fusionner ou supprimer si < 3 transactions
```

---

## 📊 Workflow Complet

### Étape 1 : Détection
```
COACH: "📊 Vous avez 50 transactions 'Alimentation' ce mois.
        ⚠️ Recommandation : Créer sous-catégories pour mieux analyser."
```

### Étape 2 : Suggestion
```
COACH: "💡 Suggestions basées sur vos habitudes :
        1. Restaurant (20 trans, 25€ moy)
        2. Courses (25 trans, 45€ moy)
        3. Snacks (5 trans, 8€ moy)
        
        Appliquer ces sous-catégories ?"
```

### Étape 3 : Application
```
USER: "Oui"
COACH: "✅ 45 transactions mises à jour
        📊 Graphiques actualisés"
```

### Étape 4 : Apprentissage
```
COACH: "Nouvelle dépense 22€ chez 'Le Bistrot'
        💡 Sous-catégorie 'Restaurant' ?
        [Oui] [Non] [Toujours pour ce lieu]"
```

---

## 🚀 Plan d'Implémentation

### Phase 1 : Base (1-2h)
- [ ] Rendre sous-catégorie optionnelle dans formulaire
- [ ] Adapter graphiques (2 ou 3 niveaux)
- [ ] Tester avec données existantes

### Phase 2 : Intelligence COACH (4-6h)
- [ ] Créer outil `analyze_category_distribution`
- [ ] Créer outil `suggest_subcategories`
- [ ] Créer outil `apply_subcategories`
- [ ] Intégrer dans workflow LAMOMS-COACH

### Phase 3 : Apprentissage (Optionnel)
- [ ] ML pour patterns automatiques
- [ ] Suggestions proactives
- [ ] Nettoyage automatique

---

## 💡 Avantages pour l'Écosystème

### Pour l'Utilisateur
- ✅ Flexibilité : Pas obligé de remplir
- ✅ Intelligence : L'agent organise pour lui
- ✅ Évolution : Structure s'adapte aux habitudes

### Pour LAMOMS-COACH
- ✅ Analyse plus fine des dépenses
- ✅ Suggestions budgétaires personnalisées
- ✅ Détection de patterns de consommation
- ✅ Budgets par sous-catégorie

### Pour BIBLIOTHÉCAIRE
- ✅ Documenter règles de catégorisation
- ✅ Apprendre des corrections utilisateur

### Pour MAINTENANCE
- ✅ Nettoyer catégories inutilisées
- ✅ Fusionner doublons

---

## 📝 Exemples Concrets

### Cas 1 : Transaction Simple
```
Type: Revenu
Catégorie: Salaire
Sous-catégorie: (vide) ✅
Description: Janvier 2026
```

### Cas 2 : Transaction Détaillée
```
Type: Dépense
Catégorie: Alimentation
Sous-catégorie: Restaurant ✅
Description: Déjeuner client
```

### Cas 3 : COACH Suggère
```
50 transactions "Alimentation" → COACH crée automatiquement :
- Restaurant (20)
- Courses (25)
- Snacks (5)
```

---

## 🎯 Prochaines Étapes

1. **Maintenant** : Idée documentée ✅
2. **Après agents** : Implémenter Phase 1
3. **Avec LAMOMS-COACH** : Implémenter Phase 2
4. **Optionnel** : Phase 3 (ML)

---

**Note** : Cette amélioration rend le système plus flexible pour l'utilisateur ET plus intelligent pour les agents. Win-win ! 🎉

**Lien** : Discussion du 2 janvier 2026, 22h20
