"""
Transactions Page Module

This module contains all transaction-related interface functions including:
- Simplified transaction interface (main menu)
- View/Edit transactions interface
- Add expenses interface (manual + CSV import)
"""

import streamlit as st
import pandas as pd
import io
from datetime import datetime, date, timedelta
from typing import Optional, Dict
from config import DB_PATH, TO_SCAN_DIR , REVENUS_A_TRAITER
from modules.database.connection import get_db_connection
from modules.ui.helpers import (
    load_transactions,
    insert_transaction_batch,
    refresh_and_rerun
)

from modules.ui.toast_components import (
    toast_success, toast_error, toast_warning,
    afficher_documents_associes, get_badge_icon
)
from modules.utils.converters import safe_convert, safe_date_convert
from modules.services.revenue_service import is_uber_transaction, process_uber_revenue
from modules.services.recurrence_service import backfill_recurrences_to_today
from modules.services.normalization import normalize_category, normalize_subcategory
from modules.services.file_service import (
    deplacer_fichiers_associes,
    supprimer_fichiers_associes
)
from modules.services.fractal_service import build_fractal_hierarchy
from modules.ui.fractal_component import fractal_navigation, render_hidden_buttons
from modules.ui.components.charts import render_evolution_chart
from modules.ui.components.calendar_component import render_calendar, get_calendar_date_range


def get_transactions_for_fractal_code(code: str, hierarchy: Dict, df: pd.DataFrame) -> pd.DataFrame:
    """
    Get transactions for a specific fractal code (category or subcategory).

    For subcategories (level 3), also filter by parent category to avoid getting
    transactions from other categories that might have the same subcategory name.
    """
    if not code or code not in hierarchy:
        return pd.DataFrame()

    node = hierarchy[code]
    level = node.get('level', 0)

    # Niveau 3 (sous-catégories) - IMPORTANT: filtrer aussi par catégorie parente ET par type
    if level == 3:
        subcategory_name = node.get('label', '')
        parent_code = node.get('parent', '')

        # Récupérer la catégorie parente
        if parent_code and parent_code in hierarchy:
            parent_node = hierarchy[parent_code]
            category_name = parent_node.get('label', '')
            parent_parent_code = parent_node.get('parent', '')

            # Déterminer le type (revenu/dépense) à partir du grand-parent
            transaction_type = 'revenu' if parent_parent_code == 'REVENUS' else 'dépense'

            # Filtrer par type ET catégorie ET sous-catégorie pour éviter tout conflit
            df_filtered = df[
                (df['type'].str.lower() == transaction_type.lower()) &
                (df['categorie'].str.lower() == category_name.lower()) &
                (df['sous_categorie'].str.lower() == subcategory_name.lower())
            ]
            return df_filtered
        else:
            # Fallback si pas de parent (ne devrait pas arriver)
            return df[df['sous_categorie'].str.lower() == subcategory_name.lower()]

    # Niveau 2 (catégories) - afficher toutes les sous-catégories de cette catégorie
    elif level == 2:
        category_name = node.get('label', '')
        parent_code = node.get('parent', '')  # This is REVENUS or DEPENSES (level 1)

        # Déterminer le type (revenu/dépense) directement depuis le parent
        transaction_type = 'revenu' if parent_code == 'REVENUS' else 'dépense'

        # Filtrer par catégorie ET type pour éviter les doublons si une catégorie existe dans les deux
        return df[
            (df['categorie'].str.lower() == category_name.lower()) &
            (df['type'].str.lower() == transaction_type.lower())
        ]

    # Niveau 1 (type: Revenus/Dépenses) - afficher toutes les transactions du type
    elif level == 1:
        transaction_type = 'revenu' if code == 'REVENUS' else 'dépense'
        return df[df['type'].str.lower() == transaction_type.lower()]

    # Niveau 0 (root) - afficher tout
    elif level == 0:
        return df

    return pd.DataFrame()


def interface_transactions_simplifiee() -> None:
    """
    Simplified transaction interface - main menu for adding transactions.

    Features:
    - Scanner un ticket (OCR)
    - Ajouter des dépenses (manuel + CSV)
    - Créer une transaction récurrente
    - Ajouter un revenu

    Returns:
        None
    """
    st.title("💸 Ajouter une Transaction")

    # Menu de sélection principal
    col1, col2 = st.columns([3, 1])

    with col1:
        type_action = st.selectbox(
            "Que voulez-vous faire ?",
            [
                "📸 Scanner un ticket (OCR)",
                "💰 Scanner un revenu (PDF)",
                "💸 Ajouter une Dépense ou un Revenu"
            ],
            key="type_action_transaction"
        )

    with col2:
        st.caption("")
        st.caption("")
        if st.button("🔄 Actualiser", key="refresh_transactions"):
            refresh_and_rerun()

    st.markdown("---")

    # === SCANNER UN TICKET ===
    if type_action == "📸 Scanner un ticket (OCR)":
        st.subheader("📸 Scanner les tickets automatiquement")
        st.info(f"**📂 Dossier de scan :** `{TO_SCAN_DIR}`")

        with st.expander("ℹ️ Comment ça marche ?", expanded=False):
            st.markdown(f"""
            ### Mode d'emploi :
            1. **Nommer votre ticket** avec le format : `nom.categorie.sous_categorie.extension`
               - Exemple : `carrefour.alimentation.courses.jpg`
               - Exemple : `shell.transport.essence.jpg`
            2. **Déposer le fichier** dans le dossier : `{TO_SCAN_DIR}`
            3. **Cliquer sur "Scanner"** ci-dessous
            4. **Vérifier et valider** les informations détectées

            **Formats acceptés :** JPG, PNG, PDF
            """)

        # Import scanning function here to avoid circular imports
        from .scanning import process_all_tickets_in_folder
        process_all_tickets_in_folder()

    # === AJOUTER DES DÉPENSES (MANUEL + CSV) ===
    elif type_action == "💰 Scanner un revenu (PDF)":
        from .revenues import interface_process_all_revenues_in_folder
        st.subheader("💰 Scanner un revenu (PDF)")
        st.info(f"**📂 Dossier de scan :** `{REVENUS_A_TRAITER}`")
        interface_process_all_revenues_in_folder()

    # === REVENU (NON-RÉCURRENT) ===
    elif type_action == "💸 Ajouter une Dépense ou un Revenu":
        
        # Import revenue function to avoid circular imports
        interface_ajouter_depenses_fusionnee() 


def interface_ajouter_depenses_fusionnee() -> None:
    """
    Unified interface for adding expenses (manual + CSV import).

    Features:
    - Manual entry form
    - CSV bulk import with template download
    - Duplicate detection
    - Uber revenue processing support

    Returns:
        None
    """
    st.subheader("💸 Ajouter une Dépense ou un Revenu")

    # Tabs pour séparer clairement les deux méthodes
    tab1, tab2 = st.tabs(["✍️ Ajout manuel", "📄 Import CSV"])

    # ===== TAB 1: AJOUT MANUEL =====
    with tab1:
        st.markdown("### ✍️ Ajouter une dépense manuellement")
        st.info("💡 Remplissez le formulaire ci-dessous pour ajouter une seule dépense")

        with st.form("add_manual_depense"):
            col1, col2, col3 = st.columns(3)

            with col1:
                date_tr = st.date_input("📅 Date", value=date.today())
                type_tr = st.selectbox("📊 Type", ["dépense", "revenu"])

            with col2:
                cat = st.text_input("🏷️ Catégorie principale", placeholder="Ex: Alimentation")
                sous_cat = st.text_input("📌 Sous-catégorie", placeholder="Ex: Courses")

            with col3:
                montant = st.number_input("💰 Montant (€)", min_value=0.0, step=0.01, format="%.2f")
                desc = st.text_input("📝 Description", placeholder="Ex: Carrefour")

            # Uber tax checkbox (shown inside form so user can see it before submitting)
            apply_uber_tax = st.checkbox(
                "🚗 Appliquer la taxe Uber (21%) pour ce revenu ?",
                value=False,
                key="apply_uber_tax_manual",
                help="Cochez cette case uniquement si c'est un revenu Uber. Le prélèvement de 21% sera appliqué automatiquement. ⚠️ Ne pas ajouter les dépenses URSSAF séparément dans ce cas."
            )

            valider = st.form_submit_button("✅ Ajouter la transaction", type="primary")

        if valider:
            if not cat or montant <= 0:
                toast_error("Veuillez entrer au moins une catégorie et un montant valide.")
            else:
                transaction_data = {
                    "type": type_tr,
                    "categorie": normalize_category(cat.strip()),
                    "sous_categorie": normalize_subcategory(sous_cat.strip()),
                    "description": desc.strip(),
                    "montant": float(montant),
                    "date": date_tr.isoformat(),
                    "source": "manuel"
                }

                # Process Uber revenue ONLY if user checked the box AND it's actually an Uber transaction
                if type_tr == "revenu" and apply_uber_tax:
                    if is_uber_transaction(cat, desc):
                        transaction_data, uber_msg = process_uber_revenue(transaction_data, apply_tax=True)
                        if uber_msg:
                            st.info(uber_msg)
                    else:
                        st.warning("⚠️ La taxe Uber n'a pas été appliquée car la transaction ne contient pas le mot 'Uber'.")

                insert_transaction_batch([transaction_data])
                toast_success(f"✅ Transaction ajoutée : {cat} — {transaction_data['montant']:.2f} €")
                st.balloons()
                st.info("💡 N'oubliez pas d'actualiser la page pour voir vos changements")

    # ===== TAB 2: IMPORT CSV =====
    with tab2:
        st.markdown("### 📄 Importer plusieurs dépenses depuis un fichier CSV")

        # Guide étape par étape
        st.markdown("#### 📋 Guide d'importation")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("##### 1️⃣ Télécharger le modèle")
            st.caption("Téléchargez le fichier modèle CSV avec les colonnes requises")

            # Créer un modèle CSV
            modele_csv = """type,date,categorie,sous_categorie,montant,description
dépense,2024-01-15,alimentation,courses,45.50,Carrefour
dépense,2024-01-16,transport,essence,60.00,Shell Station
revenu,2024-01-01,salaire,mensuel,2500.00,Salaire janvier
dépense,2024-01-20,loisirs,restaurant,35.80,Pizza
revenu,2024-01-15,freelance,mission,450.00,Projet X"""

            st.download_button(
                label="⬇️ Télécharger le modèle",
                data=modele_csv,
                file_name="modele_transactions.csv",
                mime="text/csv",
                help="Modèle avec exemples de transactions"
            )

        with col2:
            st.markdown("##### 2️⃣ Compléter le fichier")
            st.caption("Ouvrez le fichier dans Excel/LibreOffice et ajoutez vos transactions")
            st.markdown("""
            **Colonnes requises :**
            - `type` : dépense ou revenu
            - `date` : AAAA-MM-JJ
            - `categorie` : Catégorie principale
            - `sous_categorie` : Sous-catégorie
            - `montant` : Montant (avec . ou ,)
            - `description` : Description
            """)

        with col3:
            st.markdown("##### 3️⃣ Importer le fichier")
            st.caption("Uploadez votre fichier CSV complété ci-dessous")

        st.markdown("---")

        # Zone d'upload
        uploaded_file = st.file_uploader(
            "📤 Sélectionner votre fichier CSV",
            type=['csv'],
            help="Sélectionnez le fichier CSV avec vos transactions",
            key="csv_uploader_depenses"
        )

        if uploaded_file is not None:
            st.success(f"✅ Fichier '{uploaded_file.name}' chargé !")

            try:
                # Lire le CSV
                df_import = pd.read_csv(io.StringIO(uploaded_file.getvalue().decode('utf-8')))

                st.markdown("#### 📊 Aperçu des données")
                st.dataframe(df_import.head(10), use_container_width=True)

                st.info(f"📈 **{len(df_import)}** transactions détectées dans le fichier")

                # Options d'import
                col1, col2 = st.columns(2)

                with col1:
                    ignorer_doublons = st.checkbox(
                        "🔒 Ignorer les doublons",
                        value=True,
                        help="Évite d'importer plusieurs fois la même transaction"
                    )

                with col2:
                    st.caption("")

                # Bouton d'import
                if st.button("✅ Importer les transactions", type="primary", key="import_csv_depenses_btn"):
                    with st.spinner("Import en cours..."):
                        # Préparer les transactions
                        transactions_a_importer = []

                        for idx, row in df_import.iterrows():
                            # Conversion sécurisée
                            transaction = {
                                "type": str(row.get('type', 'dépense')).strip().lower(),
                                "date": str(row.get('date', datetime.now().date())),
                                "categorie": str(row.get('categorie', 'Divers')).strip(),
                                "sous_categorie": str(row.get('sous_categorie', 'Autre')).strip(),
                                "montant": safe_convert(row.get('montant', 0)),
                                "description": str(row.get('description', '')).strip() if pd.notna(row.get('description')) else "",
                                "source": "CSV Import"
                            }

                            # Validation basique
                            if transaction["montant"] > 0:
                                transactions_a_importer.append(transaction)

                        if transactions_a_importer:
                            # Insertion
                            if ignorer_doublons:
                                # Charger transactions existantes pour vérifier doublons
                                df_existant = load_transactions()
                                nouvelles = []
                                doublons = 0

                                for trans in transactions_a_importer:
                                    # Vérification doublon simple (même date, montant, catégorie)
                                    est_doublon = False
                                    if not df_existant.empty:
                                        est_doublon = (
                                            (df_existant['date'] == pd.Timestamp(trans['date'])) &
                                            (df_existant['montant'] == trans['montant']) &
                                            (df_existant['categorie'] == trans['categorie'])
                                        ).any()

                                    if not est_doublon:
                                        nouvelles.append(trans)
                                    else:
                                        doublons += 1

                                if nouvelles:
                                    insert_transaction_batch(nouvelles)
                                    toast_success(f"✅ {len(nouvelles)} transaction(s) importée(s) avec succès !")
                                    if doublons > 0:
                                        st.warning(f"⚠️ {doublons} doublon(s) ignoré(s)")
                                else:
                                    st.warning("⚠️ Toutes les transactions sont des doublons")
                            else:
                                insert_transaction_batch(transactions_a_importer)
                                toast_success(f"✅ {len(transactions_a_importer)} transaction(s) importée(s) !")

                            st.balloons()
                            st.info("💡 N'oubliez pas d'actualiser la page pour voir vos changements")
                        else:
                            toast_error("Aucune transaction valide trouvée dans le fichier")

            except Exception as e:
                st.error(f"❌ Erreur lors de la lecture du fichier : {e}")
                st.caption("Vérifiez que le fichier respecte bien le format du modèle")


def interface_voir_transactions() -> None:
    """
    View transactions interface with interactive calendar and chart.
    
    Layout:
    1. Top: Navigation Fractale (gauche) + Calendrier (droite)
    2. Middle: Métriques (pleine largeur)
    3. Bottom: Graphique (gauche) + Tableau (droite)
    
    Mode Consultation uniquement.
    """
    # CSS pour compacter la page
    st.markdown("""
    <style>
        .stMetric { margin-bottom: 0rem !important; gap: 0 !important; }
        hr { margin: 0.2rem 0 !important; padding: 0 !important; }
        [data-testid="stHeading"] { margin-bottom: 0.2rem !important; padding-bottom: 0rem !important; margin-top: 0.2rem !important; }
    </style>
    """, unsafe_allow_html=True)

    st.title("📊 Mes Transactions")

    backfill_recurrences_to_today(DB_PATH)
    df = load_transactions()

    if df.empty:
        st.info("💰 Aucune transaction enregistrée. Commencez par en ajouter !")
        return

    # =====================================================
    # SECTION 1: NAVIGATION FRACTALE + CALENDRIER (haut)
    # =====================================================
    col_fractal, col_calendar = st.columns([2, 1])
    
    with col_fractal:
        st.subheader("🔺 Navigation Fractale")
        hierarchy = build_fractal_hierarchy()
        fractal_navigation(hierarchy, key='fractal_transactions')
    
    with col_calendar:
        st.subheader("📅 Calendrier")
        selected_date = render_calendar(df, key='cal_transactions')

    st.markdown("---")

    # =====================================================
    # APPLIQUER LES FILTRES (Calendrier + Fractale)
    # =====================================================
    df_filtered = df.copy()
    df_filtered["date"] = pd.to_datetime(df_filtered["date"])

    # Filtre calendrier (date ou plage)
    date_debut, date_fin = get_calendar_date_range(key='cal_transactions')
    
    if date_debut and date_fin:
        # Plage complète
        df_filtered = df_filtered[
            (df_filtered["date"].dt.date >= date_debut) &
            (df_filtered["date"].dt.date <= date_fin)
        ]
    elif date_debut:
        # Seulement date de début (depuis cette date)
        df_filtered = df_filtered[df_filtered["date"].dt.date >= date_debut]
    elif date_fin:
        # Seulement date de fin (jusqu'à cette date)
        df_filtered = df_filtered[df_filtered["date"].dt.date <= date_fin]
    # Sinon (None, None) : pas de filtre de date, afficher tout

    # Filtre fractal (catégories)
    if 'fractal_selections' in st.session_state and st.session_state.fractal_selections:
        selected_codes = list(st.session_state.fractal_selections)
        df_fractal_filtered = pd.DataFrame()

        for code in selected_codes:
            df_code = get_transactions_for_fractal_code(code, hierarchy, df_filtered)
            df_fractal_filtered = pd.concat([df_fractal_filtered, df_code], ignore_index=True)

        if not df_fractal_filtered.empty:
            df_filtered = df_fractal_filtered.drop_duplicates(subset=['id'], keep='first')

    # Tri par date (plus récentes en premier)
    df_filtered = df_filtered.sort_values("date", ascending=False).reset_index(drop=True)

    if df_filtered.empty:
        st.warning("🔍 Aucune transaction trouvée avec ces filtres")
        return

    # =====================================================
    # SECTION 2: MÉTRIQUES (milieu)
    # =====================================================
    total_revenus = df_filtered[df_filtered["type"] == "revenu"]["montant"].sum()
    total_depenses = df_filtered[df_filtered["type"] == "dépense"]["montant"].sum()
    solde = total_revenus - total_depenses

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📊 Transactions", len(df_filtered))
    with col2:
        st.metric("💹 Revenus", f"{total_revenus:.0f} €")
    with col3:
        st.metric("💸 Dépenses", f"{total_depenses:.0f} €")
    with col4:
        delta_color = "normal" if solde >= 0 else "inverse"
        st.metric("💰 Solde", f"{solde:+.0f} €", delta_color=delta_color)

    st.markdown("---")

    # =====================================================
    # SECTION 3: GRAPHIQUE + TABLEAU (bas)
    # =====================================================
    col_graph, col_table = st.columns([1, 1.5])

    with col_graph:
        st.subheader("📈 Graphique")
        render_evolution_chart(df_filtered, height=450)

    with col_table:
        st.subheader("📋 Transactions")
        
        # Préparer l'affichage
        df_display = df_filtered.copy()
        df_display["montant"] = df_display["montant"].apply(lambda x: safe_convert(x, float, 0.0))
        df_display["Type"] = df_display["type"].apply(lambda x: "🟢" if x == "revenu" else "🔴")
        df_display["Date"] = pd.to_datetime(df_display["date"]).dt.strftime("%d/%m/%Y")
        df_display["Montant"] = df_display["montant"].apply(lambda x: f"{x:.2f}")

        st.dataframe(
            df_display[["Type", "Date", "categorie", "sous_categorie", "Montant", "description"]].rename(columns={
                "categorie": "Catégorie",
                "sous_categorie": "Sous-catégorie",
                "description": "Description"
            }),
            use_container_width=True,
            height=450,
            hide_index=True
        )

        st.caption(f"{len(df_display)} transactions")

    # =====================================================
    # BOUTONS D'ACTION
    # =====================================================
    st.markdown("---")
    
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("➕ Ajouter une Transaction", use_container_width=True):
            st.session_state.requested_page = "💳 Transactions"
            st.rerun()
    
    with col2:
        if st.button("🔄 Réinitialiser filtres", use_container_width=True):
            st.session_state.fractal_selections = set()
            if "cal_transactions_selected_date" in st.session_state:
                st.session_state.cal_transactions_selected_date = None
            st.rerun()

    # =====================================================
    # FICHIERS ASSOCIÉS (sensible aux filtres)
    # =====================================================
    with st.expander(f"📎 Fichiers associés ({len(df_filtered)} transactions)", expanded=False):
        st.caption("Affichage des fichiers pour les transactions actuellement filtrées")
        
        if not df_filtered.empty:
            # Parcourir les transactions filtrées et afficher les fichiers
            for idx, row in df_filtered.iterrows():
                # Utiliser la fonction existante pour afficher les documents
                with st.container():
                    st.markdown(f"**{row['description']}** - {row['date'].strftime('%d/%m/%Y')} - {row['montant']:.2f} €")
                    # Passer la row complète (Series) convertie en dict
                    afficher_documents_associes(row.to_dict())
                    if idx < len(df_filtered) - 1:  # Pas de séparateur après la dernière
                        st.markdown("---")
        else:
            st.info("Aucune transaction à afficher")
    
    # Boutons cachés pour JavaScript automation (dans un expander)
    with st.expander("🔧 Contrôles fractale (debug)", expanded=False):
        render_hidden_buttons(hierarchy, key='fractal_transactions')



def render_graphique_section_v2(df: pd.DataFrame) -> None:
    """Section Graphique (droite milieu)."""
    import plotly.graph_objects as go
    
    st.markdown("### Graphique")
    
    # Bar chart mensuel
    if not df.empty:
        df_monthly = df.copy()
        df_monthly["mois"] = df_monthly["date"].dt.to_period("M").astype(str)
        monthly_sum = df_monthly.groupby("mois")["montant"].sum()
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=monthly_sum.index,
            y=monthly_sum.values,
            marker_color=['#4A90E2', '#00D4AA', '#FFD93D', '#FF6B6B'] * len(monthly_sum),
            text=[f"{v:.0f}" for v in monthly_sum.values],
            textposition='outside'
        ))
        
        fig.update_layout(
            height=500,  # Augmenté de 300 à 500px
            margin=dict(t=10, b=30, l=30, r=10),
            paper_bgcolor='#1E1E1E',
            plot_bgcolor='#1E1E1E',
            xaxis=dict(showgrid=False, color='white'),
            yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', color='white'),
            font=dict(color='white')
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aucune donnée disponible")


def render_tableau_transactions_v2(df: pd.DataFrame) -> None:
    """Section Tableau des Transactions (bas)."""
    
    # Afficher toutes les transactions
    df_display = df.copy()
    
    # Préparer affichage
    df_display["Type"] = df_display["type"].apply(
        lambda x: "🔴" if x == "dépense" else "🟢"
    )
    df_display["Date"] = df_display["date"].dt.strftime("%d/%m/%Y")
    df_display["Montant"] = df_display["montant"].apply(lambda x: f"{x:.2f}")
    
    # Dataframe
    st.dataframe(
        df_display[["Type", "Date", "categorie", "sous_categorie", "Montant", "description"]].rename(columns={
            "categorie": "Catégorie",
            "sous_categorie": "Sous-catégorie",
            "description": "Description"
        }),
        use_container_width=True,
        hide_index=True,
        height=500
    )
    
    st.caption(f"{len(df_display)} transactions")
