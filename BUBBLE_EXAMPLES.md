# 🫧 Exemples Pratiques - Système de Bulles

## Template Standard pour Pages Streamlit

### Template Basique
```python
import streamlit as st
import pandas as pd
from modules.ui.components import render_category_management

def render_page(df: pd.DataFrame):
    """Render page with bubble filtering system."""

    # Page header
    st.title("💰 Mes Transactions")

    # Get selected categories (returns list)
    selected_categories = render_category_management(df)

    # Apply filter
    if selected_categories:
        df_display = df[df['categorie'].isin(selected_categories)]
        st.info(f"Affichage {len(df_display)} transactions filtrées")
    else:
        df_display = df
        st.info(f"Affichage toutes les {len(df)} transactions")

    # Display results
    st.dataframe(df_display, use_container_width=True)
```

---

## Exemples Complets par Type de Page

### 1. Page Transactions (Listing Simple)

```python
# modules/ui/pages/transactions.py

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

from modules.ui.components import render_category_management
from modules.database.repositories import TransactionRepository

def render_transactions_page():
    """Display and filter transactions with bubble system."""

    st.set_page_config(page_title="Transactions", page_icon="📊", layout="wide")

    # Initialize database
    repo = TransactionRepository()

    # Load data
    df = repo.get_all_transactions()

    if df.empty:
        st.warning("Aucune transaction trouvée")
        return

    # ========== FILTERING ==========
    st.markdown("## 📊 Filtrer les Transactions")
    selected_categories = render_category_management(df)

    # ========== DATA PROCESSING ==========
    if selected_categories:
        df_filtered = df[df['categorie'].isin(selected_categories)]
    else:
        df_filtered = df

    # ========== SIDEBAR STATS ==========
    with st.sidebar:
        st.markdown("### 📈 Statistiques")
        st.metric("Total Dépenses", f"{df_filtered['montant'].sum():.2f}€")
        st.metric("Transactions", len(df_filtered))
        st.metric("Moyennes", f"{df_filtered['montant'].mean():.2f}€")

    # ========== RESULTS DISPLAY ==========
    st.markdown("### 📋 Résultats")

    # Sort options
    col1, col2 = st.columns(2)
    with col1:
        sort_by = st.selectbox("Trier par", ["Date", "Montant", "Catégorie"])
    with col2:
        sort_order = st.radio("Ordre", ["Décroissant", "Croissant"], horizontal=True)

    # Apply sorting
    if sort_by == "Date":
        df_filtered = df_filtered.sort_values('date', ascending=(sort_order == "Croissant"))
    elif sort_by == "Montant":
        df_filtered = df_filtered.sort_values('montant', ascending=(sort_order == "Croissant"))
    else:
        df_filtered = df_filtered.sort_values('categorie', ascending=(sort_order == "Croissant"))

    # Display table
    st.dataframe(
        df_filtered[['date', 'categorie', 'sous_categorie', 'description', 'montant']],
        use_container_width=True,
        hide_index=True
    )

if __name__ == "__main__":
    render_transactions_page()
```

---

### 2. Page Analyse (Avec Graphiques)

```python
# modules/ui/pages/analytics.py

import streamlit as st
import pandas as pd
import plotly.express as px

from modules.ui.components import render_category_management
from modules.database.repositories import TransactionRepository

def render_analytics_page():
    """Display analytics with bubble filtering."""

    st.set_page_config(page_title="Analyse", page_icon="📊", layout="wide")

    # Load data
    repo = TransactionRepository()
    df = repo.get_all_transactions()

    if df.empty:
        st.warning("Aucune donnée disponible")
        return

    # ========== FILTERING ==========
    st.markdown("## 📊 Analyse par Catégories")
    selected_categories = render_category_management(df)

    # Apply filter
    df_filtered = df[df['categorie'].isin(selected_categories)] if selected_categories else df

    # ========== METRICS ==========
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total = df_filtered['montant'].sum()
        st.metric(
            "Total Dépenses",
            f"{total:.2f}€",
            delta=f"{(total/df['montant'].sum()*100):.1f}% du total" if selected_categories else None
        )

    with col2:
        st.metric("Transactions", len(df_filtered))

    with col3:
        avg = df_filtered['montant'].mean()
        st.metric("Dépense Moyenne", f"{avg:.2f}€")

    with col4:
        max_spend = df_filtered['montant'].max()
        st.metric("Dépense Max", f"{max_spend:.2f}€")

    # ========== VISUALIZATIONS ==========
    st.markdown("### 📈 Visualisations")

    tab1, tab2, tab3 = st.tabs(["Pie Chart", "Bar Chart", "Time Series"])

    with tab1:
        # Pie chart by category
        cat_summary = df_filtered.groupby('categorie')['montant'].sum().reset_index()
        fig = px.pie(
            cat_summary,
            values='montant',
            names='categorie',
            title="Répartition par Catégorie"
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        # Bar chart
        cat_summary = df_filtered.groupby('categorie')['montant'].sum().sort_values(ascending=False)
        st.bar_chart(cat_summary)

    with tab3:
        # Time series
        df_time = df_filtered.groupby(pd.to_datetime(df_filtered['date']).dt.date)['montant'].sum()
        st.line_chart(df_time)

if __name__ == "__main__":
    render_analytics_page()
```

---

### 3. Page Budget (Avec Indicateurs)

```python
# modules/ui/pages/budget.py

import streamlit as st
import pandas as pd

from modules.ui.components import render_category_management
from modules.database.repositories import TransactionRepository

def render_budget_page():
    """Display budget with bubble filtering."""

    st.set_page_config(page_title="Budget", page_icon="💰", layout="wide")

    # Load data
    repo = TransactionRepository()
    df = repo.get_all_transactions()

    if df.empty:
        st.warning("Aucune donnée disponible")
        return

    # Budget limits (configurable)
    BUDGET_LIMITS = {
        'Alimentation': 500,
        'Transport': 200,
        'Loisirs': 300,
        'Autres': 150
    }

    # ========== FILTERING ==========
    selected_categories = render_category_management(df)
    df_filtered = df[df['categorie'].isin(selected_categories)] if selected_categories else df

    # ========== BUDGET PROGRESS ==========
    st.markdown("## 💰 Suivi du Budget")

    for category, limit in BUDGET_LIMITS.items():
        # Get category data
        cat_data = df_filtered[df_filtered['categorie'] == category]
        spent = cat_data['montant'].sum()
        remaining = limit - spent
        pct = min(100, (spent / limit * 100))

        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            # Color indicator
            if pct >= 100:
                color = "#ef4444"  # Red
                status = "🔴 Dépassé"
            elif pct >= 80:
                color = "#f59e0b"  # Orange
                status = "🟠 Attention"
            else:
                color = "#10b981"  # Green
                status = "🟢 OK"

            st.markdown(f"### {category} {status}")

            # Progress bar
            st.progress(
                value=min(pct/100, 1),
                text=f"{spent:.0f}€ / {limit:.0f}€ ({pct:.0f}%)"
            )

        with col2:
            st.metric("Restant", f"{max(0, remaining):.0f}€")

        with col3:
            if pct >= 100:
                st.metric("Dépassement", f"{abs(remaining):.0f}€", delta_color="inverse")
            else:
                st.metric("Budget", f"{limit:.0f}€")

if __name__ == "__main__":
    render_budget_page()
```

---

### 4. Page Comparaison (Avant/Après Filtrage)

```python
# modules/ui/pages/comparison.py

import streamlit as st
import pandas as pd

from modules.ui.components import render_category_management
from modules.database.repositories import TransactionRepository

def render_comparison_page():
    """Compare total vs filtered data."""

    st.set_page_config(page_title="Comparaison", page_icon="⚖️", layout="wide")

    # Load data
    repo = TransactionRepository()
    df = repo.get_all_transactions()

    if df.empty:
        st.warning("Aucune donnée disponible")
        return

    # ========== FILTERING ==========
    selected_categories = render_category_management(df)
    df_filtered = df[df['categorie'].isin(selected_categories)] if selected_categories else df

    # ========== COMPARISON TABLE ==========
    st.markdown("## ⚖️ Avant / Après Filtrage")

    comparison = pd.DataFrame({
        'Métrique': [
            'Nombre de transactions',
            'Total dépenses',
            'Dépense moyenne',
            'Dépense minimum',
            'Dépense maximum',
            'Écart-type'
        ],
        'Avant (Tout)': [
            len(df),
            f"{df['montant'].sum():.2f}€",
            f"{df['montant'].mean():.2f}€",
            f"{df['montant'].min():.2f}€",
            f"{df['montant'].max():.2f}€",
            f"{df['montant'].std():.2f}€"
        ],
        'Après (Filtré)': [
            len(df_filtered),
            f"{df_filtered['montant'].sum():.2f}€",
            f"{df_filtered['montant'].mean():.2f}€",
            f"{df_filtered['montant'].min():.2f}€",
            f"{df_filtered['montant'].max():.2f}€",
            f"{df_filtered['montant'].std():.2f}€"
        ]
    })

    st.dataframe(comparison, use_container_width=True, hide_index=True)

    # ========== INSIGHTS ==========
    st.markdown("### 💡 Insights")

    total_all = df['montant'].sum()
    total_filtered = df_filtered['montant'].sum()
    pct_selected = (total_filtered / total_all * 100) if total_all > 0 else 0

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "% du Budget Sélectionné",
            f"{pct_selected:.1f}%",
            delta=f"{total_filtered:.2f}€ sur {total_all:.2f}€"
        )

    with col2:
        if len(df_filtered) > 0:
            st.metric(
                "% des Transactions",
                f"{(len(df_filtered)/len(df)*100):.1f}%",
                delta=f"{len(df_filtered)} sur {len(df)}"
            )

    with col3:
        avg_all = df['montant'].mean()
        avg_filtered = df_filtered['montant'].mean()
        diff = ((avg_filtered - avg_all) / avg_all * 100)
        st.metric(
            "Dépense Moyenne vs Globale",
            f"{avg_filtered:.2f}€",
            delta=f"{diff:+.1f}%" if diff else "Égal"
        )

if __name__ == "__main__":
    render_comparison_page()
```

---

### 5. Integration dans Main App

```python
# gestiov4.py - Main app file

import streamlit as st
import pandas as pd

from modules.ui.pages.transactions import render_transactions_page
from modules.ui.pages.analytics import render_analytics_page
from modules.ui.pages.budget import render_budget_page
from modules.ui.pages.comparison import render_comparison_page

def main():
    """Main application entry point."""

    st.set_page_config(
        page_title="GestioV4",
        page_icon="💰",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Sidebar navigation
    with st.sidebar:
        st.markdown("# 💰 GestioV4")
        st.markdown("Gestion Financière Intelligente")
        st.markdown("---")

        page = st.radio(
            "Navigation",
            ["Transactions", "Analyse", "Budget", "Comparaison"],
            icons=["📊", "📈", "💰", "⚖️"]
        )

        st.markdown("---")
        st.caption("v4.0 - Système de Bulles V2")

    # Load data once
    from modules.database.repositories import TransactionRepository
    repo = TransactionRepository()
    df = repo.get_all_transactions()

    # Route to page
    if page == "Transactions":
        render_transactions_page()
    elif page == "Analyse":
        render_analytics_page()
    elif page == "Budget":
        render_budget_page()
    elif page == "Comparaison":
        render_comparison_page()

if __name__ == "__main__":
    main()
```

---

## Patterns Courants

### Pattern 1: Simple Filter & Display
```python
selected = render_category_management(df)
df_filtered = df[df['categorie'].isin(selected)] if selected else df
st.dataframe(df_filtered)
```

### Pattern 2: Filter + Sidebar Metrics
```python
selected = render_category_management(df)
df_filtered = df[df['categorie'].isin(selected)] if selected else df

with st.sidebar:
    st.metric("Total", f"{df_filtered['montant'].sum():.2f}€")
    st.metric("Count", len(df_filtered))
```

### Pattern 3: Filter + Multiple Sections
```python
selected = render_category_management(df)
df_filtered = df[df['categorie'].isin(selected)] if selected else df

col1, col2 = st.columns(2)

with col1:
    st.subheader("Table")
    st.dataframe(df_filtered)

with col2:
    st.subheader("Stats")
    st.write(df_filtered.describe())
```

### Pattern 4: Filter + Export
```python
selected = render_category_management(df)
df_filtered = df[df['categorie'].isin(selected)] if selected else df

# Export button
csv = df_filtered.to_csv(index=False)
st.download_button(
    label="Télécharger CSV",
    data=csv,
    file_name="transactions.csv",
    mime="text/csv"
)
```

---

## Cas d'Usage Avancés

### Utilisation avec Dates
```python
import pandas as pd
from datetime import datetime, timedelta

selected = render_category_management(df)
df_filtered = df[df['categorie'].isin(selected)] if selected else df

# Add date filter
date_range = st.date_input(
    "Période",
    value=(df['date'].min(), df['date'].max()),
    key='date_range'
)

if len(date_range) == 2:
    df_filtered = df_filtered[
        (df_filtered['date'] >= date_range[0]) &
        (df_filtered['date'] <= date_range[1])
    ]

st.dataframe(df_filtered)
```

### Utilisation avec Montant Min/Max
```python
selected = render_category_management(df)
df_filtered = df[df['categorie'].isin(selected)] if selected else df

col1, col2 = st.columns(2)
with col1:
    min_amount = st.number_input("Montant min", value=0.0)
with col2:
    max_amount = st.number_input("Montant max", value=df_filtered['montant'].max())

df_filtered = df_filtered[
    (df_filtered['montant'] >= min_amount) &
    (df_filtered['montant'] <= max_amount)
]

st.dataframe(df_filtered)
```

### Utilisation avec Type (Revenu/Dépense)
```python
selected = render_category_management(df)

transaction_type = st.selectbox(
    "Type",
    ["Tous", "Dépenses", "Revenus"]
)

if transaction_type != "Tous":
    type_map = {"Dépenses": "dépense", "Revenus": "revenu"}
    df = df[df['type'] == type_map[transaction_type]]

df_filtered = df[df['categorie'].isin(selected)] if selected else df
st.dataframe(df_filtered)
```

---

## Testing

### Test Function Example
```python
def test_render_with_selection():
    """Test rendering with specific selection."""
    import pandas as pd
    import streamlit as st

    # Create test data
    df = pd.DataFrame({
        'categorie': ['A', 'A', 'B', 'C'],
        'sous_categorie': ['A1', 'A2', 'B1', 'C1'],
        'montant': [100, 150, 200, 75],
        'type': ['dépense'] * 4,
        'date': pd.date_range('2025-01-01', periods=4)
    })

    # Manually set state for testing
    st.session_state['selected_categories'] = ['A', 'B']

    # Filter
    selected = st.session_state['selected_categories']
    df_filtered = df[df['categorie'].isin(selected)]

    # Assert
    assert len(df_filtered) == 3
    assert df_filtered['montant'].sum() == 450

    print("Test passed!")
```

---

**Last Updated:** 21 November 2025
**Status:** Ready for Production
