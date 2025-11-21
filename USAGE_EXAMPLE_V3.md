# 💡 Exemple d'Utilisation - Système de Bulles V3

## Utilisation Simple

Voici comment intégrer le nouveau système de bulles dans vos pages :

### Exemple 1: Page de Transactions Basique

```python
# Dans une page Streamlit

import streamlit as st
import pandas as pd
from modules.ui.components import render_category_management
from modules.database.repositories import TransactionRepository

def main():
    st.set_page_config(page_title="Transactions", page_icon="📊")

    # Charger les données
    repo = TransactionRepository()
    df = repo.get_all_transactions()

    if df.empty:
        st.warning("Aucune transaction trouvée")
        return

    # Afficher le système de bulles (retourne DataFrame filtré)
    st.title("📊 Mes Transactions")
    st.markdown("---")

    df_filtered = render_category_management(df)

    # Afficher les transactions filtrées
    st.markdown("### 📋 Transactions")
    st.dataframe(df_filtered, use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()
```

---

## Exemple 2: Page avec Statistiques

```python
def main():
    st.title("💰 Gestion Financière")

    # Données
    repo = TransactionRepository()
    df = repo.get_all_transactions()

    # Navigation par bulles
    df_filtered = render_category_management(df)

    # Afficher uniquement si on est au dernier niveau (subcategories)
    if st.session_state.bubble_level == 'subcategories':
        st.markdown("---")

        # Statistiques rapides
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Filtré", f"{df_filtered['montant'].sum():.2f}€")
        with col2:
            st.metric("Transactions", len(df_filtered))
        with col3:
            st.metric("Moyenne", f"{df_filtered['montant'].mean():.2f}€")

        # Tableau
        st.markdown("### 📋 Détails")
        st.dataframe(df_filtered, use_container_width=True)

        # Graphique
        st.markdown("### 📈 Graphique")
        chart_data = df_filtered.groupby('sous_categorie')['montant'].sum()
        st.bar_chart(chart_data)
```

---

## Exemple 3: Layout Complet

```python
def main():
    st.set_page_config(
        page_title="GestioV4",
        page_icon="💰",
        layout="wide"
    )

    # Sidebar
    with st.sidebar:
        st.markdown("# 💰 GestioV4")
        st.markdown("Gestion Financière Intelligente")

        # Option d'export
        export_format = st.selectbox("Format export", ["CSV", "Excel", "PDF"])

    # Main content
    repo = TransactionRepository()
    df = repo.get_all_transactions()

    if df.empty:
        st.error("Aucune donnée disponible")
        return

    # Header
    st.title("📊 Tableau de Bord")
    st.markdown("Naviguez par clic sur les bulles pour explorer vos dépenses")

    st.markdown("---")

    # Bubble navigation system
    df_filtered = render_category_management(df)

    st.markdown("---")

    # Display results based on level
    level = st.session_state.bubble_level

    if level == 'main':
        st.info("👆 Cliquez sur la bulle pour commencer!")

    elif level == 'categories':
        st.info("👆 Cliquez sur une catégorie pour voir les détails")

    elif level == 'subcategories':
        # Show filtered data
        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown("### 📋 Transactions Filtrées")
            st.dataframe(
                df_filtered[['date', 'sous_categorie', 'description', 'montant']],
                use_container_width=True,
                hide_index=True
            )

        with col2:
            st.markdown("### 📊 Résumé")
            st.metric("Total", f"{df_filtered['montant'].sum():.2f}€")
            st.metric("Nombre", len(df_filtered))
            st.metric("Moyenne", f"{df_filtered['montant'].mean():.2f}€")

            # Export button
            if export_format == "CSV":
                csv = df_filtered.to_csv(index=False)
                st.download_button(
                    label="Télécharger CSV",
                    data=csv,
                    file_name=f"{st.session_state.selected_category}.csv",
                    mime="text/csv"
                )

if __name__ == "__main__":
    main()
```

---

## Exemple 4: Intégration avec Autres Composants

```python
def main():
    st.title("💰 Analyse Financière")

    # Load data
    repo = TransactionRepository()
    df = repo.get_all_transactions()

    # Three column layout
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        st.markdown("### Filtres")
        date_range = st.date_input("Période")
        min_amount = st.number_input("Montant min", value=0.0)

    with col2:
        st.markdown("### Navigation Bulles")
        df_filtered = render_category_management(df)

    with col3:
        st.markdown("### Options")
        show_chart = st.checkbox("Afficher graphique", value=True)
        show_table = st.checkbox("Afficher tableau", value=True)

    st.markdown("---")

    # Apply additional filters
    if isinstance(date_range, tuple) and len(date_range) == 2:
        df_filtered = df_filtered[
            (df_filtered['date'] >= date_range[0]) &
            (df_filtered['date'] <= date_range[1])
        ]

    df_filtered = df_filtered[df_filtered['montant'] >= min_amount]

    # Display based on selection
    if st.session_state.bubble_level == 'subcategories':
        if show_chart:
            st.markdown("### 📈 Graphique")
            chart_data = df_filtered.groupby('sous_categorie')['montant'].sum()
            st.bar_chart(chart_data)

        if show_table:
            st.markdown("### 📋 Tableau")
            st.dataframe(df_filtered, use_container_width=True)
```

---

## Accès à l'État

Pour accéder à l'état actuel du système de bulles :

```python
# Dans votre page
current_level = st.session_state.bubble_level
# Valeurs: 'main' | 'categories' | 'subcategories'

selected_cat = st.session_state.selected_category
# Valeur: None ou nom de la catégorie sélectionnée

# Exemple: Afficher du contenu différent selon le niveau
if st.session_state.bubble_level == 'subcategories':
    st.success(f"Vous visualisez: {st.session_state.selected_category}")
```

---

## Debugging

### Afficher l'état en Sidebar

```python
with st.sidebar:
    if st.checkbox("DEBUG"):
        st.json({
            "bubble_level": st.session_state.bubble_level,
            "selected_category": st.session_state.selected_category,
        })
```

### Réinitialiser manuellement

```python
if st.button("🔄 Réinitialiser"):
    from modules.ui.components import _reset_to_main
    _reset_to_main()
    st.rerun()
```

---

## Points Importants

### 1. Retour du DataFrame

`render_category_management()` retourne **TOUJOURS** un DataFrame :
- Level 'main': DataFrame complet (type='dépense')
- Level 'categories': DataFrame complet (type='dépense')
- Level 'subcategories': DataFrame filtré par catégorie

### 2. Pas de Multi-sélection

Contrairement à V2, il n'y a **plus de multi-sélection** :
- On sélectionne UNE catégorie à la fois
- Simple et intuitif
- Perfect pour une navigation hiérarchique

### 3. Animations Automatiques

Les animations se font automatiquement :
- Vous n'avez rien à faire
- Utilisez juste `render_category_management()`
- Le reste est géré par Streamlit + CSS

### 4. État Persistent

L'état est conservé entre les re-runs :
```python
# Clic sur bulle
render_category_management(df)  # Retour
st.rerun()  # Re-render conserve le state

# Vous êtes toujours au même niveau
```

---

## Migration depuis V2

Si vous aviez du code V2 :

```python
# ANCIEN (V2)
selected_list = render_category_management(df)
if selected_list:
    df_filtered = df[df['categorie'].isin(selected_list)]
else:
    df_filtered = df
st.dataframe(df_filtered)

# NOUVEAU (V3) - Plus simple!
df_filtered = render_category_management(df)
st.dataframe(df_filtered)
```

**C'est plus simple maintenant!** ✨

---

## Cas d'Utilisation

### Pour une Page Transactions
```python
df_filtered = render_category_management(df)
st.dataframe(df_filtered)
```

### Pour une Page Analytics
```python
df_filtered = render_category_management(df)
st.bar_chart(df_filtered.groupby('categorie')['montant'].sum())
```

### Pour une Page Budget
```python
df_filtered = render_category_management(df)
total = df_filtered['montant'].sum()
st.metric("Dépensé", f"{total:.2f}€")
```

---

## Troubleshooting

### Problem: La bulle n'explose pas

**Solution:** Utilisez un navigateur moderne (Chrome, Firefox, Safari)

### Problem: L'état ne se met pas à jour

**Solution:** Assurez-vous que `render_category_management(df)` est appelée à chaque re-run.

### Problem: Les couleurs ne s'affichent pas

**Solution:** Vérifiez que la catégorie existe dans `CATEGORY_COLORS`

### Problem: Les animations sont saccadées

**Solution:** C'est normal sur les navigateurs lents. Les animations sont CSS pur (performantes).

---

## FAQ

**Q: Comment afficher le tableau directement au démarrage?**
A: Vous ne pouvez pas. Par design, le user doit d'abord explorer via les bulles.

**Q: Comment ajouter une catégorie de couleur?**
A: Éditez `CATEGORY_COLORS` dans `components.py`:
```python
CATEGORY_COLORS = {
    'MaNouvelleCat': '#HEX_COLOR',
}
```

**Q: Comment changer la taille des bulles?**
A: Modifiez dans `_render_category_bubbles()`:
```python
size = 80 + (amount / max_amount * 100)  # ← Changez ces nombres
```

**Q: Comment désactiver les animations?**
A: Vous ne pouvez pas sans modifier le CSS. Pas recommandé!

---

**Version:** 3.0
**Status:** ✅ Production Ready
**Last Updated:** 21 Nov 2025
