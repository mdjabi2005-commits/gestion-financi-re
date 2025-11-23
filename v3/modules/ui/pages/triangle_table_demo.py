"""
Triangle & Table - Demonstration & Comparison

This module provides a demo page that explains both approaches
and allows users to choose which one to use.

@author: djabi
@version: 1.0
@date: 2025-11-23
"""

import streamlit as st


def show_demo():
    """Show comparison of both approaches."""

    st.set_page_config(page_title="📊 Triangle & Table - Démo", layout="wide")
    st.title("📊 Triangle & Table - Comparaison des Approches")

    st.markdown("""
    # Deux façons de lier les triangles et la table

    Nous avons implémenté deux approches différentes pour l'interaction entre les triangles fractals
    et la table de transactions. Chacune a ses avantages et inconvénients.

    **Testez les deux et choisissez celle qui vous plaît le plus !**
    """)

    st.markdown("---")

    # === APPROACH 1 ===
    st.heading("✨ Approach 1: Interactive Selection (Sélection Interactive)")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("""
        ### Layout
        ```
        ┌─────────────────────────────────────┐
        │   Fractal Triangle (Haut)           │
        │   - Visualisation hiérarchique      │
        └─────────────────────────────────────┘
                         ↓ (click triangle)
        ┌─────────────────────────────────────┐
        │   Boutons de Sélection              │
        │   - Type (Revenus/Dépenses)         │
        │   - Catégories (dynamiques)         │
        └─────────────────────────────────────┘
                         ↓
        ┌─────────────────────────────────────┐
        │   Statistiques & Infos               │
        └─────────────────────────────────────┘
                         ↓
        ┌─────────────────────────────────────┐
        │   Table de Transactions (Bas)       │
        │   - Auto-filtrée par sélection      │
        └─────────────────────────────────────┘
        ```

        ### Comment ça marche
        1. **Visualisez** la structure avec les triangles
        2. **Cliquez sur les boutons** pour sélectionner une catégorie
        3. **La table se filtre automatiquement**
        4. **Les statistiques se mettent à jour** en temps réel

        ### Avantages ✅
        - Interface intuitive et fluide
        - Feedback visuel immédiat
        - Vue hiérarchique complète
        - Navigation progressive (du général au particulier)
        - Facile à comprendre pour les nouveaux utilisateurs

        ### Inconvénients ❌
        - Faut scrolliner verticallement pour voir table
        - Une seule sélection à la fois
        - Moins d'espace pour chaque composant
        """)

    with col2:
        if st.button(
            "🚀 Tester Approach 1",
            key="test_v1",
            use_container_width=True,
            type="primary"
        ):
            st.switch_page("pages/triangle_table_v1.py")

        st.markdown("")
        st.markdown("")

        st.info("""
        ### 📊 Cas d'usage ideal:
        - Exploration progressive
        - Apprenants nouveaux
        - Petits écrans/mobiles
        - Focus sur la hiérarchie
        """)

    st.markdown("---")

    # === APPROACH 2 ===
    st.heading("📐 Approach 2: Side-by-Side Layout (Disposition Côte à Côte)")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("""
        ### Layout
        ```
        ┌────────────────────────────────────────────────────────┐
        │  LEFT (40%)            │   RIGHT (60%)                │
        │  ┌──────────────────┐  │  ┌──────────────────────────┐│
        │  │ Fractal Triangle │  │  │ Boutons de Sélection     ││
        │  │                  │  │  │                          ││
        │  │                  │  │  │ Statistiques             ││
        │  │                  │  │  │ ┌─────────────┐           │
        │  │                  │  │  │ │ Trans    Tab││
        │  │                  │  │  │ │             ││
        │  │                  │  │  │ │             ││
        │  │                  │  │  │ └─────────────┘││
        │  │                  │  │  │                          ││
        │  └──────────────────┘  │  └──────────────────────────┘│
        └────────────────────────────────────────────────────────┘
        ```

        ### Comment ça marche
        1. **Triangles à gauche** - Vue complète de la hiérarchie
        2. **Table à droite** - Transactions filtrées en direct
        3. **Boutons compacts** - Sélection rapide
        4. **Tout visible** - Moins de scrolling

        ### Avantages ✅
        - Voir triangles ET table simultanément
        - Moins de scrolling vertical
        - Vue de tableau de bord
        - Comparaison plus facile
        - Plus de contexte visible à la fois
        - Efficace pour les utilisateurs expérimentés

        ### Inconvénients ❌
        - Moins d'espace pour chaque composant
        - Peut être dense sur petits écrans
        - Nécessite un écran large (desktop)
        - Moins d'espace pour la table
        """)

    with col2:
        if st.button(
            "🚀 Tester Approach 2",
            key="test_v2",
            use_container_width=True,
            type="primary"
        ):
            st.switch_page("pages/triangle_table_v2.py")

        st.markdown("")
        st.markdown("")

        st.info("""
        ### 📊 Cas d'usage ideal:
        - Vue d'ensemble rapidement
        - Utilisateurs expérimentés
        - Écrans larges/desktop
        - Analyse comparative
        """)

    st.markdown("---")

    # === COMPARISON TABLE ===
    st.heading("📊 Comparaison Détaillée")

    comparison_data = {
        "Critère": [
            "Navigation verticale",
            "Visibility simultanée",
            "Espace triangles",
            "Espace table",
            "Scrolling",
            "Mobile-friendly",
            "Screen size min",
            "Courbe d'apprentissage",
            "Efficacité (expert)",
            "Contexte visible"
        ],
        "Approach 1": [
            "Bonne",
            "❌ Partielle",
            "✅ Grand",
            "✅ Grand",
            "Beaucoup",
            "✅ Oui",
            "Petit",
            "✅ Facile",
            "Modérée",
            "Limité"
        ],
        "Approach 2": [
            "Minimale",
            "✅ Complète",
            "Petit",
            "Moyen",
            "Minimal",
            "❌ Non",
            "Large (1200px)",
            "Modérée",
            "✅ Excellente",
            "✅ Maximal"
        ]
    }

    import pandas as pd
    df_comparison = pd.DataFrame(comparison_data)

    st.dataframe(
        df_comparison,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Critère": st.column_config.TextColumn("Critère", width=200),
            "Approach 1": st.column_config.TextColumn("Approach 1", width=150),
            "Approach 2": st.column_config.TextColumn("Approach 2", width=150)
        }
    )

    st.markdown("---")

    # === RECOMMENDATION ===
    st.heading("💡 Recommandations")

    col1, col2 = st.columns(2)

    with col1:
        st.success("""
        ### Choisir Approach 1 si:
        - 📱 Vous utilisez une tablette ou mobile
        - 🎯 Vous préférez l'exploration progressive
        - 👥 Nouveaux utilisateurs dans votre équipe
        - 📚 Vous voulez apprendre la structure
        - 🔍 Vous explorez les données graduellement
        """)

    with col2:
        st.info("""
        ### Choisir Approach 2 si:
        - 🖥️ Vous avez un grand écran (desktop)
        - ⚡ Vous préférez voir tout d'un coup
        - 👨‍💻 Vous êtes utilisateur expérimenté
        - 📊 Vous analysez rapidement
        - 🔄 Vous comparez des catégories
        """)

    st.markdown("---")

    # === NAVIGATION ===
    st.heading("🚀 Essayez les deux !")

    col1, col2 = st.columns(2)

    with col1:
        st.button(
            "👈 Approach 1: Interactive Selection",
            key="nav_v1",
            use_container_width=True,
            type="primary",
            on_click=lambda: st.switch_page("pages/triangle_table_v1.py")
        )

    with col2:
        st.button(
            "Approach 2: Side-by-Side Layout 👉",
            key="nav_v2",
            use_container_width=True,
            type="primary",
            on_click=lambda: st.switch_page("pages/triangle_table_v2.py")
        )


if __name__ == "__main__":
    show_demo()
