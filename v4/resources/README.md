# Resources - Ressources Statiques

Ce dossier contient les ressources statiques de l'application (styles CSS, assets).

## Structure

```
resources/
└── styles/
    ├── main.css         # Styles principaux
    ├── components.css   # Styles composants
    └── themes.css       # Thèmes couleurs
```

## 📦 Dépendances

**Aucune dépendance** - CSS pur uniquement.

---

## Utilisation

Les styles sont automatiquement chargés par Streamlit via:

```python
from shared.ui import load_all_styles

# Dans votre app
load_all_styles()
```

---

## Styles Disponibles

### `main.css`
Styles globaux de l'application:
- Reset CSS
- Typographie de base
- Layout principal
- Variables CSS (couleurs, espacements)

### `components.css`
Styles pour composants réutilisables:
- Cartes (cards)
- Boutons personnalisés
- Alertes et notifications
- Tables et listes

### `themes.css`
Thèmes et couleurs:
- Mode sombre (principal)
- Palette de couleurs
- Couleurs sémantiques (succès, erreur, warning)

---

## Customisation

Pour modifier les styles:

1. Éditer le fichier CSS approprié dans `resources/styles/`
2. Les changements sont appliqués au rechargement de l'app
3. Utiliser les variables CSS pour cohérence:

```css
:root {
    --color-primary: #00D4AA;
    --color-expense: #FF6B6B;
    --color-revenue: #00D4AA;
}
```

---

## Mode Sombre

L'application utilise un mode sombre par défaut avec:
- Background: `#1E1E1E`
- Text: `#FFFFFF`
- Accents: Couleurs vives pour contraste
