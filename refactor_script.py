#!/usr/bin/env python3
"""Refactoriser components.py avec bulles compactes"""

original_file = "modules/ui/components.py"

# Read the original file
with open(original_file, "r", encoding="utf-8") as f:
    content = f.read()

# Find section markers
start_marker = "# 🫧 SIMPLIFIED STATE MANAGEMENT"
start_idx = content.find(start_marker)

emoji_marker = "def _get_category_emoji(category: str)"
emoji_idx = content.find(emoji_marker)

# Extract parts
before_render = content[:start_idx]
emoji_func = content[emoji_idx:]

# New render function with compact bubbles
new_render = '''# ==============================
# 🫧 BUBBLE NAVIGATION COMPONENT - Compact & Fluide
# ==============================

def render_category_management(df: pd.DataFrame) -> pd.DataFrame:
    """
    Navigation compacte par bulles rondes avec transitions fluides.

    3 niveaux de navigation avec design optimisé:
    - Niveau 1: Type Selection (2 bulles: Revenus/Dépenses)
    - Niveau 2: Category Selection (Grille compacte de bulles)
    - Niveau 3: Detail View (Transactions filtrées)
    """
    # État de navigation
    if 'nav_level' not in st.session_state:
        st.session_state.nav_level = 'type_selection'
    if 'selected_type' not in st.session_state:
        st.session_state.selected_type = None
    if 'selected_categories' not in st.session_state:
        st.session_state.selected_categories = []

    # CSS pour bulles rondes compactes
    st.markdown("""
    <style>
    /* Container centré */
    .bubble-container {
        max-width: 1000px;
        margin: 0 auto;
        padding: 30px 20px;
    }

    /* Grille de bulles */
    .bubble-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
        gap: 20px;
        padding: 40px 0;
        animation: fadeIn 0.4s ease-out;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* Vraie bulle ronde */
    .bubble {
        aspect-ratio: 1;
        border-radius: 50%;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        color: white;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        text-align: center;
        padding: 20px;
    }

    .bubble:hover {
        transform: scale(1.12) translateY(-8px);
        box-shadow: 0 15px 45px rgba(0, 0, 0, 0.3);
    }

    /* Revenus bulle */
    .bubble-revenus {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    }

    /* Dépenses bulle */
    .bubble-depenses {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
    }

    /* Catégorie bulles avec couleurs variées */
    .bubble-cat-1 { background: linear-gradient(135deg, #f59e0b, #f97316); }
    .bubble-cat-2 { background: linear-gradient(135deg, #8b5cf6, #7c3aed); }
    .bubble-cat-3 { background: linear-gradient(135deg, #ec4899, #db2777); }
    .bubble-cat-4 { background: linear-gradient(135deg, #14b8a6, #0d9488); }
    .bubble-cat-5 { background: linear-gradient(135deg, #ef4444, #dc2626); }
    .bubble-cat-6 { background: linear-gradient(135deg, #3b82f6, #2563eb); }
    .bubble-cat-7 { background: linear-gradient(135deg, #6366f1, #4f46e5); }
    .bubble-cat-8 { background: linear-gradient(135deg, #06b6d4, #0891b2); }

    /* Texte dans la bulle */
    .bubble-emoji {
        font-size: 32px;
        margin-bottom: 8px;
    }

    .bubble-name {
        font-size: 14px;
        font-weight: 600;
        margin-bottom: 4px;
    }

    .bubble-amount {
        font-size: 18px;
        font-weight: 700;
        margin-bottom: 2px;
    }

    .bubble-count {
        font-size: 12px;
        opacity: 0.9;
    }

    /* Titre principal */
    .bubble-title {
        text-align: center;
        color: white;
        font-size: 28px;
        font-weight: 700;
        margin-bottom: 30px;
    }

    /* Breadcrumb */
    .breadcrumb {
        text-align: center;
        color: #94a3b8;
        margin-bottom: 25px;
        font-size: 14px;
    }

    .breadcrumb strong {
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

    # NIVEAU 1: Type Selection
    if st.session_state.nav_level == 'type_selection':
        st.markdown('<div class="bubble-container">', unsafe_allow_html=True)
        st.markdown('<div class="bubble-title">💰 Explorez votre Univers Financier</div>', unsafe_allow_html=True)

        revenus_total = df[df['type'] == 'revenu']['montant'].sum()
        revenus_count = len(df[df['type'] == 'revenu'])
        depenses_total = df[df['type'] == 'dépense']['montant'].sum()
        depenses_count = len(df[df['type'] == 'dépense'])

        col1, col2 = st.columns(2, gap="large")

        with col1:
            st.markdown(f"""
            <div class="bubble bubble-revenus">
                <div class="bubble-emoji">💼</div>
                <div class="bubble-name">REVENUS</div>
                <div class="bubble-amount">{revenus_total:,.0f}€</div>
                <div class="bubble-count">{revenus_count} tx</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Sélectionner", key="btn_rev", use_container_width=True):
                st.session_state.selected_type = 'revenu'
                st.session_state.nav_level = 'category_selection'
                st.rerun()

        with col2:
            st.markdown(f"""
            <div class="bubble bubble-depenses">
                <div class="bubble-emoji">🛒</div>
                <div class="bubble-name">DÉPENSES</div>
                <div class="bubble-amount">{depenses_total:,.0f}€</div>
                <div class="bubble-count">{depenses_count} tx</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Sélectionner", key="btn_dep", use_container_width=True):
                st.session_state.selected_type = 'dépense'
                st.session_state.nav_level = 'category_selection'
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)
        return df

    # NIVEAU 2: Category Selection
    elif st.session_state.nav_level == 'category_selection':
        if st.session_state.selected_type:
            st.markdown('<div class="bubble-container">', unsafe_allow_html=True)

            # Bouton retour
            col1, col2, col3 = st.columns([1, 10, 1])
            with col1:
                if st.button("← Retour", key="back_type"):
                    st.session_state.nav_level = 'type_selection'
                    st.session_state.selected_type = None
                    st.session_state.selected_categories = []
                    st.rerun()

            # Breadcrumb
            type_label = "Revenus" if st.session_state.selected_type == 'revenu' else "Dépenses"
            st.markdown(f'<div class="breadcrumb">Univers → <strong>{type_label}</strong></div>', unsafe_allow_html=True)

            # Titre
            emoji = "💼" if st.session_state.selected_type == 'revenu' else "🛒"
            st.markdown(f'<div class="bubble-title" style="font-size: 24px;">{emoji} Catégories</div>', unsafe_allow_html=True)

            # Statistiques par catégorie
            df_filtered = df[df['type'] == st.session_state.selected_type]
            cat_stats = df_filtered.groupby('categorie').agg({
                'montant': 'sum',
                'sous_categorie': 'count'
            }).reset_index()
            cat_stats.columns = ['categorie', 'montant', 'count']
            cat_stats = cat_stats.sort_values('montant', ascending=False)

            # Grille de bulles
            st.markdown('<div class="bubble-grid">', unsafe_allow_html=True)

            for idx, (_, row) in enumerate(cat_stats.iterrows()):
                col = st.columns(3)[idx % 3]
                with col:
                    cat_name = row['categorie']
                    color_class = f"bubble-cat-{(idx % 8) + 1}"
                    emoji = _get_category_emoji(cat_name)

                    st.markdown(f"""
                    <div class="bubble {color_class}">
                        <div class="bubble-emoji">{emoji}</div>
                        <div class="bubble-name">{cat_name}</div>
                        <div class="bubble-amount">{row['montant']:,.0f}€</div>
                        <div class="bubble-count">{int(row['count'])} items</div>
                    </div>
                    """, unsafe_allow_html=True)

                    if st.button("Voir", key=f"cat_{cat_name}", use_container_width=True):
                        st.session_state.selected_categories = [cat_name]
                        st.session_state.nav_level = 'detail'
                        st.rerun()

            st.markdown('</div></div>', unsafe_allow_html=True)
            return df_filtered

    # NIVEAU 3: Detail View
    elif st.session_state.nav_level == 'detail':
        if st.session_state.selected_categories:
            st.markdown('<div class="bubble-container">', unsafe_allow_html=True)

            # Bouton retour
            if st.button("← Retour aux catégories", key="back_cat"):
                st.session_state.nav_level = 'category_selection'
                st.session_state.selected_categories = []
                st.rerun()

            # Breadcrumb
            type_label = "Revenus" if st.session_state.selected_type == 'revenu' else "Dépenses"
            cat_str = " + ".join(st.session_state.selected_categories)
            st.markdown(f'<div class="breadcrumb">Univers → <strong>{type_label}</strong> → <strong>{cat_str}</strong></div>', unsafe_allow_html=True)

            # Titre
            cat_emoji = _get_category_emoji(st.session_state.selected_categories[0])
            st.markdown(f'<div class="bubble-title" style="font-size: 24px;">{cat_emoji} {st.session_state.selected_categories[0]}</div>', unsafe_allow_html=True)

            # Filtrer les données
            df_filtered = df[
                (df['type'] == st.session_state.selected_type) &
                (df['categorie'].isin(st.session_state.selected_categories))
            ]

            # Métriques
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("💰 Total", f"{df_filtered['montant'].sum():,.0f}€")
            with col2:
                st.metric("📊 Transactions", len(df_filtered))
            with col3:
                st.metric("🏷️ Catégories", len(st.session_state.selected_categories))

            st.divider()

            # Transactions
            st.subheader("📋 Détail des transactions")
            if len(df_filtered) > 0:
                for idx, transaction in df_filtered.iterrows():
                    afficher_carte_transaction(transaction, idx)
            else:
                st.warning("Aucune transaction trouvée")

            st.markdown('</div>', unsafe_allow_html=True)
            return df_filtered

    return df

'''

# Write the refactored file
with open(original_file, "w", encoding="utf-8") as f:
    f.write(before_render)
    f.write(new_render)
    f.write("\n\n")
    f.write(emoji_func)

print("[OK] Refactorisation complète!")
