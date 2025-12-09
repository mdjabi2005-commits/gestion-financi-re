"""
Dynamic Tree Page - Interactive Financial Tree Visualization

Full-page D3.js hierarchical tree without distractions.
"""

import streamlit as st
import pandas as pd
from modules.services.fractal_service import build_fractal_hierarchy
from modules.ui.helpers import load_transactions
from modules.ui.fractal_component import fractal_navigation


def interface_arbre_financier_dynamique() -> None:
    """
    Arbre Financier Dynamique - Full-page tree visualization.
    """
    st.title("🌳 Arbre Financier Dynamique")
    
    # Load transactions
    df = load_transactions()
    
    if df.empty:
        st.info("💰 Aucune transaction enregistrée. Commencez par en ajouter !")
        return
    
    # Build hierarchy
    hierarchy = build_fractal_hierarchy()
    
    if not hierarchy:
        st.warning("⚠️ Impossible de construire la hiérarchie des transactions")
        return
    
    # JUST THE TREE - NOTHING ELSE
    fractal_navigation(
        hierarchy=hierarchy,
        key='fractal_tree_page',
        show_canvas=True
    )
    
    # ==========================================
    # GESTION DES CATÉGORIES
    # ==========================================
    st.markdown("---")
    st.subheader("⚙️ Gestion des Catégories")
    
    tab_create, tab_subcategory, tab_delete = st.tabs(["➕ Créer catégorie", "🌿 Créer sous-catégorie", "🗑️ Supprimer"])
    
    # ===== TAB 1 : CRÉER CATÉGORIE PRINCIPALE =====
    with tab_create:
        with st.form("create_category_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_category_name = st.text_input(
                    "Nom de la catégorie",
                    placeholder="Ex: Loisirs, Salaire...",
                    help="Nom de la nouvelle catégorie principale"
                )
            
            with col2:
                category_type = st.selectbox(
                    "Type",
                    options=["Dépense", "Revenu"],
                    help="Type de catégorie"
                )
            
            submitted = st.form_submit_button("✅ Créer la catégorie", use_container_width=True, type="primary")
            
            if submitted and new_category_name:
                from modules.database.repositories import TransactionRepository
                from modules.database.models import Transaction
                from datetime import date
                
                try:
                    placeholder = Transaction(
                        type=category_type.lower(),
                        categorie=new_category_name,
                        sous_categorie=None,
                        description=f"Catégorie {new_category_name}",
                        montant=0.01,
                        date=date(2000, 1, 1),
                        source="categorie_placeholder"
                    )
                    
                    transaction_id = TransactionRepository.insert(placeholder)
                    
                    if transaction_id:
                        st.success(f"✅ Catégorie **{new_category_name}** créée !")
                        st.rerun()
                    else:
                        st.error("❌ Erreur lors de la création")
                except Exception as e:
                    st.error(f"❌ Erreur : {str(e)}")
    
    # ===== TAB 2 : CRÉER SOUS-CATÉGORIE =====
    with tab_subcategory:
        with st.form("create_subcategory_form"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Get existing categories
                existing_cats = {}
                for code, node in hierarchy.items():
                    if node.get('level') == 1:  # Only main categories
                        existing_cats[code] = {
                            'label': node.get('label', code),
                            'type': node.get('transaction_type', 'dépense')
                        }
                
                if existing_cats:
                    parent_cat = st.selectbox(
                        "Catégorie parente",
                        options=list(existing_cats.keys()),
                        format_func=lambda x: existing_cats[x]['label'],
                        help="Catégorie dans laquelle créer la sous-catégorie"
                    )
                else:
                    st.warning("Aucune catégorie disponible")
                    parent_cat = None
            
            with col2:
                subcategory_name = st.text_input(
                    "Nom de la sous-catégorie",
                    placeholder="Ex: Netflix, Prime...",
                    help="Nom de la sous-catégorie"
                )
            
            with col3:
                st.write("")  # Spacing
                st.write("")
                submitted_sub = st.form_submit_button("✅ Créer", use_container_width=True, type="primary")
            
            if submitted_sub and subcategory_name and parent_cat:
                from modules.database.repositories import TransactionRepository
                from modules.database.models import Transaction
                from datetime import date
                
                try:
                    parent_info = existing_cats[parent_cat]
                    
                    placeholder = Transaction(
                        type=parent_info['type'],
                        categorie=parent_info['label'],
                        sous_categorie=subcategory_name,
                        description=f"Sous-catégorie {subcategory_name}",
                        montant=0.01,
                        date=date(2000, 1, 1),
                        source="categorie_placeholder"
                    )
                    
                    transaction_id = TransactionRepository.insert(placeholder)
                    
                    if transaction_id:
                        st.success(f"✅ Sous-catégorie **{subcategory_name}** créée sous **{parent_info['label']}** !")
                        st.rerun()
                    else:
                        st.error("❌ Erreur lors de la création")
                except Exception as e:
                    st.error(f"❌ Erreur : {str(e)}")
    
    # ===== TAB 3 : SUPPRIMER CATÉGORIE =====
    with tab_delete:
        st.warning("⚠️ **Attention** : La suppression est permanente")
        
        with st.form("delete_category_form"):
            # Get all categories with transaction count
            df = load_transactions()
            category_stats = df.groupby(['type', 'categorie', 'sous_categorie']).size().reset_index(name='count')
            
            # Build options
            delete_options = []
            for _, row in category_stats.iterrows():
                if pd.notna(row['sous_categorie']):
                    label = f"{row['categorie']} → {row['sous_categorie']} ({row['count']} transactions)"
                    value = f"{row['categorie']}||{row['sous_categorie']}"
                else:
                    label = f"{row['categorie']} ({row['count']} transactions)"
                    value = f"{row['categorie']}||"
                delete_options.append((value, label))
            
            if delete_options:
                selected = st.selectbox(
                    "Catégorie à supprimer",
                    options=[opt[0] for opt in delete_options],
                    format_func=lambda x: next((opt[1] for opt in delete_options if opt[0] == x), x),
                    help="Sélectionnez la catégorie ou sous-catégorie à supprimer"
                )
                
                delete_action = st.radio(
                    "Action sur les transactions",
                    options=["Supprimer les transactions", "Garder sans catégorie"],
                    help="Que faire des transactions de cette catégorie ?"
                )
                
                confirm = st.checkbox("Je confirme la suppression")
                
                submitted_del = st.form_submit_button("🗑️ Supprimer", use_container_width=True, type="secondary")
                
                if submitted_del and confirm and selected:
                    from modules.database.repositories import TransactionRepository
                    from modules.database.connection import get_db_connection, close_connection
                    
                    try:
                        parts = selected.split('||')
                        cat_name = parts[0]
                        subcat_name = parts[1] if parts[1] else None
                        
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        
                        if delete_action == "Supprimer les transactions":
                            # Delete all transactions in this category
                            if subcat_name:
                                cursor.execute(
                                    "DELETE FROM transactions WHERE categorie = ? AND sous_categorie = ?",
                                    (cat_name, subcat_name)
                                )
                            else:
                                cursor.execute(
                                    "DELETE FROM transactions WHERE categorie = ?",
                                    (cat_name,)
                                )
                        else:
                            # Set category to "Non classé"
                            if subcat_name:
                                cursor.execute(
                                    "UPDATE transactions SET categorie = 'Non classé', sous_categorie = NULL WHERE categorie = ? AND sous_categorie = ?",
                                    (cat_name, subcat_name)
                                )
                            else:
                                cursor.execute(
                                    "UPDATE transactions SET categorie = 'Non classé', sous_categorie = NULL WHERE categorie = ?",
                                    (cat_name,)
                                )
                        
                        conn.commit()
                        close_connection(conn)
                        
                        label_text = f"{cat_name} → {subcat_name}" if subcat_name else cat_name
                        st.success(f"✅ **{label_text}** supprimée !")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Erreur : {str(e)}")
            else:
                st.info("Aucune catégorie à supprimer")
