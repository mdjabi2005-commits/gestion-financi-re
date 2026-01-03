---
type: guide_librairie
library: plotly
difficulty: intermediate
tags: [graphiques, visualisation, interactif, dashboard]
phase: 2
last_updated: 2024-12-25
estimated_reading: 20min
status: active
related:
  - help/pandas.md
  - help/streamlit.md
---

# 📚 Bibliothèque : Plotly

## 🎯 Qu'est-ce que Plotly ?

**Plotly** est une bibliothèque Python pour créer des **graphiques interactifs** de qualité professionnelle. Les graphiques sont rendus en JavaScript (D3.js) et permettent zoom, survol, sélection, etc.

**Site officiel** : https://plotly.com/python  
**Documentation** : https://plotly.com/python/reference

---

## 💡 Pourquoi Plotly dans notre projet ?

1. **Interactivité** : Zoom, pan, hover automatiques
2. **Beauté** : Graphiques modernes et professionnels
3. **Intégration Streamlit** : `st.plotly_chart()` natif
4. **Variété** : Barres, lignes, pie, sunburst, etc.
5. **Personnalisation** : Contrôle total sur couleurs, layout

---

## 🔧 Concepts de base

### 1. Graph Objects (go)

API bas niveau pour contrôle total :

```python
import plotly.graph_objects as go

fig = go.Figure(
    data=[go.Bar(x=['A', 'B', 'C'], y=[10, 20, 15])],
    layout=go.Layout(title="Mon graphique")
)

fig.show()  # Dans Jupyter ou navigateur

# Avec Streamlit
import streamlit as st
st.plotly_chart(fig, use_container_width=True)
```

---

## 📊 Types de graphiques utilisés dans notre app

### 1. Bar Chart (Graphique en barres)

**Utilisation** : Revenus vs Dépenses, évolution mensuelle

```python
import plotly.graph_objects as go

fig = go.Figure()

# Barres vertes (revenus)
fig.add_trace(go.Bar(
    x=['Jan', 'Fév', 'Mar'],
    y=[2500, 2500, 2600],
    name='Revenus',
    marker_color='#00D4AA'  # Vert
))

# Barres rouges (dépenses)
fig.add_trace(go.Bar(
    x=['Jan', 'Fév', 'Mar'],
    y=[1800, 1950, 2100],
    name='Dépenses',
    marker_color='#FF6B6B'  # Rouge
))

fig.update_layout(
    title="Revenus vs Dépenses",
    barmode='group',  # ou 'stack' pour empilées
    plot_bgcolor='#1e293b',  # Fond sombre
    paper_bgcolor='#1e293b',
    font_color='white'
)
```

**Dans notre app** (`home.py`) :
```python
# Graphique Revenus/Dépenses/Solde mensuel
fig = go.Figure()
fig.add_trace(go.Bar(x=mois, y=revenus, name='Revenus', marker_color='#10b981'))
fig.add_trace(go.Bar(x=mois, y=depenses, name='Dépenses', marker_color='#ef4444'))
fig.add_trace(go.Scatter(x=mois, y=solde, name='Solde', line=dict(color='#64748b', width=3)))
```

---

### 2. Pie Chart (Camembert)

**Utilisation** : Répartition des dépenses par catégorie

```python
import plotly.graph_objects as go

categories = ['Alimentation', 'Transport', 'Logement']
montants = [456.78, 234.50, 800.00]

fig = go.Figure(data=[go.Pie(
    labels=categories,
    values=montants,
    hole=0.3,  # Donut chart
    marker=dict(
        colors=['#ef4444', '#f59e0b', '#10b981'],  # Couleurs personnalisées
        line=dict(color='white', width=2)
    ),
    textinfo='label+percent',  # Afficher label + %
    textposition='inside'
)])

fig.update_layout(
    title="Répartition des dépenses",
    showlegend=True
)
```

**Dans notre app** (`home.py`) :
```python
# Pie charts dépenses et revenus
fig_depenses = go.Figure(data=[go.Pie(
    labels=df_depenses.groupby('categorie').groups.keys(),
    values=df_depenses.groupby('categorie')['montant'].sum(),
    hole=0.4
)])
```

---

### 3. Sunburst (Graphique hiérarchique circulaire)

**Utilisation** : Visualisation de la hiérarchie financière (Type → Catégorie → Sous-catégorie)

```python
import plotly.graph_objects as go

fig = go.Figure(go.Sunburst(
    labels=['Tout', 'Revenus', 'Dépenses', 'Salaire', 'Freelance', 'Alimentation'],
    parents=['', 'Tout', 'Tout', 'Revenus', 'Revenus', 'Dépenses'],
    values=[5000, 3000, 2000, 2500, 500, 800],
    branchvalues="total",  # ou "remainder"
    marker=dict(
        colors=['#64748b', '#00D4AA', '#FF6B6B', '#10b981', '#34d399', '#ef4444']
    )
))

fig.update_layout(
    margin=dict(t=0, l=0, r=0, b=0)  # Plein écran
)
```

**Dans notre app** :  
→ Composant personnalisé `sunburst_navigation` (JavaScript + Python)

---

### 4. Scatter (Nuage de points / Ligne)

**Utilisation** : Évolution du solde dans le temps

```python
import plotly.graph_objects as go

dates = ['2025-01-01', '2025-01-02', '2025-01-03']
solde = [1000, 1050, 980]

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=dates,
    y=solde,
    mode='lines+markers',  # ou juste 'lines' ou 'markers'
    name='Solde',
    line=dict(color='#10b981', width=3),
    marker=dict(size=8, color='#34d399')
))

fig.update_layout(
    title="Évolution du solde",
    xaxis_title="Date",
    yaxis_title="Solde (€)"
)
```

**Dans notre app** (`home.py`) :
```python
# Ligne de solde mensuel
fig.add_trace(go.Scatter(
    x=mois,
    y=solde,
    mode='lines+markers',
    name='Solde',
    line=dict(color='#64748b', width=3)
))
```

---

## 🎨 Personnalisation avancée

### 1. Layout (Mise en page)

```python
fig.update_layout(
    title="Mon Graphique",
    title_font_size=24,
    title_font_color='white',
    
    # Fond
    plot_bgcolor='#1e293b',   # Couleur du graphique
    paper_bgcolor='#0f172a',  # Couleur de la page
    
    # Axes
    xaxis=dict(
        title="Mois",
        gridcolor='#475569',
        showgrid=True
    ),
    yaxis=dict(
        title="Montant (€)",
        gridcolor='#475569',
        showgrid=True
    ),
    
    # Police
    font=dict(
        family='Inter, sans-serif',
        size=14,
        color='white'
    ),
    
    # Légende
    showlegend=True,
    legend=dict(
        x=1,
        y=1,
        bgcolor='rgba(0,0,0,0.5)'
    ),
    
    # Marges
    margin=dict(l=50, r=50, t=80, b=50),
    
    # Hauteur
    height=400,
    
    # Hover
    hovermode='x unified'  # ou 'closest', False
)
```

**Dans notre app** :
```python
# Style dark pour tous les graphiques
fig.update_layout(
    plot_bgcolor='#1e293b',
    paper_bgcolor='#1e293b',
    font_color='white'
)
```

---

### 2. Couleurs

**Palette personnalisée** :
```python
colors = {
    'revenue': '#00D4AA',
    'expense': '#FF6B6B',
    'balance_positive': '#10b981',
    'balance_negative': '#ef4444'
}

fig.update_traces(marker_color=colors['revenue'])
```

**Gradient** :
```python
fig.update_traces(
    marker=dict(
        color=values,
        colorscale='Viridis',  # ou 'Blues', 'Reds', etc.
        showscale=True
    )
)
```

---

### 3. Annotations

```python
fig.add_annotation(
    x='Janvier',
    y=2500,
    text="Pic de revenus",
    showarrow=True,
    arrowhead=2,
    arrowsize=1,
    arrowwidth=2,
    arrowcolor="#636363",
    ax=20,
    ay=-30
)
```

---

### 4. Shapes (Formes)

```python
# Ligne horizontale (seuil)
fig.add_hline(
    y=1000,
    line_dash="dash",
    line_color="red",
    annotation_text="Seuil critique"
)

# Rectangle
fig.add_shape(
    type="rect",
    x0='Jan', x1='Mar',
    y0=0, y1=500,
    fillcolor="green",
    opacity=0.2,
    line_width=0
)
```

---

## 🔥 Exemples concrets de notre app

### Graphique Revenus vs Dépenses par mois

```python
from modules.database import TransactionRepository
import pandas as pd
import plotly.graph_objects as go

# Charger transactions
df = TransactionRepository.get_all()
df['date'] = pd.to_datetime(df['date'])
df['mois'] = df['date'].dt.to_period('M').astype(str)

# Grouper par mois et type
monthly = (
    df.groupby(['mois', 'type'])['montant']
    .sum()
    .unstack(fill_value=0)
)

# Créer le graphique
fig = go.Figure()

fig.add_trace(go.Bar(
    x=monthly.index,
    y=monthly.get('revenu', 0),
    name='Revenus',
    marker_color='#00D4AA'
))

fig.add_trace(go.Bar(
    x=monthly.index,
    y=monthly.get('dépense', 0),
    name='Dépenses',
    marker_color='#FF6B6B'
))

# Ajouter solde en ligne
solde = monthly.get('revenu', 0) - monthly.get('dépense', 0)
fig.add_trace(go.Scatter(
    x=monthly.index,
    y=solde,
    name='Solde',
    mode='lines+markers',
    line=dict(color='#64748b', width=3)
))

fig.update_layout(
    title="Évolution Revenus, Dépenses et Solde",
    xaxis_title="Mois",
    yaxis_title="Montant (€)",
    barmode='group',
    plot_bgcolor='#1e293b',
    paper_bgcolor='#1e293b',
    font_color='white'
)

# Afficher dans Streamlit
st.plotly_chart(fig, use_container_width=True)
```

---

## ⚠️ Bonnes pratiques

### 1. use_container_width=True

```python
# ✅ Toujours utiliser dans Streamlit
st.plotly_chart(fig, use_container_width=True)

# ❌ Largeur fixe (ne s'adapte pas)
st.plotly_chart(fig)
```

### 2. Réutiliser les couleurs

```python
# ✅ Définir des constantes
from config.ui_config import COLORS

fig.add_trace(go.Bar(marker_color=COLORS['revenue']))
```

### 3. Dark mode cohérent

```python
# ✅ Style cohérent partout
def apply_dark_theme(fig):
    fig.update_layout(
        plot_bgcolor='#1e293b',
        paper_bgcolor='#1e293b',
        font_color='white',
        xaxis=dict(gridcolor='#475569'),
        yaxis=dict(gridcolor='#475569')
    )
    return fig

fig = go.Figure(...)
fig = apply_dark_theme(fig)
```

---

## 📖 Ressources

- **Documentation** : https://plotly.com/python
- **Exemples** : https://plotly.com/python/plotly-express
- **Référence complète** : https://plotly.com/python/reference

---

## 💡 Plotly dans notre projet

| Fichier | Graphiques utilisés |
|---------|---------------------|
| `home.py` | Bar (revenus/dépenses), Pie (répartition), Scatter (solde) |
| `sunburst_navigation` | Sunburst (hiérarchie financière) |
| `transactions.py` | Potentiellement des graphiques d'analyse |
