# 🔺 Démarrage Rapide - Navigation Fractale

Bienvenue ! Voici comment commencer en **2 minutes**.

---

## ⚡ Démarrage Ultra-Rapide

### 1️⃣ Ouvrez un terminal

```bash
cd "C:\Users\djabi\gestion-financière\v3"
```

### 2️⃣ Lancez l'application

```bash
streamlit run pages/fractal_view.py
```

### 3️⃣ Explorez !

Une fenêtre de navigateur s'ouvrira automatiquement à `http://localhost:8501`

---

## 🎯 Qu'est-ce que je vais voir ?

### 1. Dashboard avec statistiques
- Nombre de catégories
- Nombre de sous-catégories
- Montant total
- Nombre de transactions

### 2. Composant fractal interactif
- **Triangles colorés** représentant votre hiérarchie financière
- **Cliquez** sur un triangle pour zoomer
- **Survolez** pour voir les détails (montant, %)

### 3. Détails de la sélection
- Informations complètes du nœud sélectionné
- Liste des transactions (pour les sous-catégories)
- Option d'export CSV

---

## 🎮 Comment naviguer

### Navigation à la souris
```
👆 Cliquez sur un triangle
     ↓
🔍 Zoom vers la catégorie
     ↓
ℹ️ Voir les détails
     ↓
← Clic "Retour" pour revenir
🏠 Clic "Vue d'ensemble" pour reset
```

### Panels disponibles

| Panel | Position | Info |
|-------|----------|------|
| Info Panel | Top-right | Niveau, montant, catégories, zoom |
| Breadcrumb | Top-left | Chemin de navigation |
| Zoom Indicator | Bottom-left | Barre de profondeur |
| Buttons | Bottom-right | Retour et réinitialisation |

---

## 🎨 Compréhension des couleurs

### Revenus (Verts 💚)
- 💼 Revenu total
- 💵 Salaire
- 🖥️ Freelance
- 📈 Investissement

### Dépenses (Oranges/Rouges ❤️)
- 🛒 Dépenses totales
- 🍔 Alimentation
- 🚗 Transport
- 🏠 Logement
- ⚕️ Santé
- 🎮 Loisirs

---

## 🔧 Filtrer par dates

### En haut à gauche de la page
```
📅 Date début: Sélectionnez la date de départ
📅 Date fin: Sélectionnez la date de fin
🔄 Cliquez "Actualiser"
```

Les données affichées se mettront à jour automatiquement.

---

## 📊 Hiérarchie des niveaux

```
Niveau 0: 🔺 Univers Financier
   │
   ├── Niveau 1: 💼 Revenus    🛒 Dépenses
   │   │
   │   ├── Niveau 2: Catégories (Salaire, Alimentation, etc.)
   │   │   │
   │   │   └── Niveau 3: Sous-catégories (Salaire Net, Courses, etc.)
```

### Patterns géométriques

```
2 éléments:    3 éléments:    4 éléments:    6 éléments:
▲  ▲          ▲            ▲              ▲   ▲
              / \           |             / \ /
                           ▲ ▲           ▲   ▲
```

---

## 💡 Conseils

### ✅ Bonnes pratiques

1. **Commencez au niveau Type** (Revenus/Dépenses)
   - C'est plus lisible et rapide

2. **Utilisez les filtres de date**
   - Pour voir des patterns mensuels/trimestriels

3. **Explorez les sous-catégories**
   - C'est là que vous voyez les transactions détaillées

4. **Utilisez le bouton Retour**
   - Plus pratique que de naviguer manuellement

### ⚠️ À savoir

- Les animations durent **700ms** (normal, c'est intentionnel)
- Le hover affiche un **tooltip avec le montant**
- L'export CSV contient **toutes les transactions du nœud**

---

## 🐛 Si quelque chose ne marche pas

### Le composant est vide
```
→ Vérifiez qu'il y a des données dans la base
→ Vérifiez la plage de dates
→ Cliquez le bouton "Actualiser"
```

### Les triangles sont mal positionnés
```
→ C'est un bug mineur, rechargez la page (F5)
```

### Les animations sont lentes
```
→ C'est normal pour 1000+ transactions
→ Réduisez la plage de dates
```

---

## 📚 Pour aller plus loin

### Documentation complète
Consultez **`README_FRACTAL.md`** pour :
- API détaillée
- Guide d'intégration
- Troubleshooting avancé
- Benchmarks

### Code source
- Service : `modules/services/fractal_service.py`
- Composant : `modules/ui/fractal_component/`
- Demo : `pages/fractal_view.py`

### Tests
```bash
python test_fractal_service.py
```

---

## 🚀 Intégration dans votre page

```python
import streamlit as st
from modules.services.fractal_service import build_fractal_hierarchy
from modules.ui.fractal_component import fractal_navigation

# Construire la hiérarchie
hierarchy = build_fractal_hierarchy()

# Afficher le composant
result = fractal_navigation(hierarchy, key='my_fractal')

# Gérer la navigation
if result:
    st.write(f"Action: {result['action']}")
    st.write(f"Code: {result['code']}")
```

---

## 📞 Besoin d'aide ?

### Questions fréquentes

**Q: Pourquoi les triangles ?**
A: C'est une fractale de Sierpiński, qui permet une visualisation hiérarchique intuitive.

**Q: Je peux changer les couleurs ?**
A: Oui ! Éditez `modules/services/fractal_service.py` - section `REVENUS_COLORS` et `DEPENSES_COLORS`.

**Q: Comment ajouter mes propres catégories ?**
A: Elles s'ajoutent automatiquement depuis la base de données.

**Q: Je peux exporter les données ?**
A: Oui ! Cliquez le bouton "Télécharger CSV" au niveau sous-catégorie.

---

## ✨ Prochaines étapes

1. **Lancez l'app** : `streamlit run pages/fractal_view.py`
2. **Explorez les données** : Cliquez sur les triangles
3. **Filtrez par dates** : Testez différentes périodes
4. **Exportez** : Téléchargez les données CSV
5. **Intégrez** : Utilisez dans votre propre page Streamlit

---

## 🎉 Vous êtes prêt !

La Navigation Fractale est **production-ready** et **entièrement testée**.

Amusez-vous à explorer vos données financières ! 🚀

---

**Version:** 1.0
**Dernière mise à jour:** 2025-11-23
**Status:** ✅ Production-Ready

