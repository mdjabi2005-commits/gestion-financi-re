"""Reusable UI components for the application.

This module contains toast notifications, badges, and transaction display components.
"""

import os
import logging
from typing import Dict, Any, Optional, List, Tuple
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from PIL import Image

from modules.services.file_service import trouver_fichiers_associes

logger = logging.getLogger(__name__)


# ==============================
# 🔔 TOAST NOTIFICATIONS
# ==============================

def show_toast(message: str, toast_type: str = "success", duration: int = 3000) -> None:
    """
    Display a professional toast notification.

    Args:
        message: Message to display
        toast_type: Type of toast - 'success', 'warning', 'error'
        duration: Duration in milliseconds (default: 3000ms)

    Example:
        >>> show_toast("Transaction saved!", "success", 3000)
        >>> show_toast("Warning: duplicate detected", "warning", 5000)
    """
    # Define color and icon based on type
    toast_config = {
        "success": {"color": "#10b981", "icon": "✅", "bg_light": "#d1fae5"},
        "warning": {"color": "#f59e0b", "icon": "⚠️", "bg_light": "#fef3c7"},
        "error": {"color": "#ef4444", "icon": "❌", "bg_light": "#fee2e2"}
    }

    config = toast_config.get(toast_type, toast_config["success"])

    components.html(f"""
        <div style="
            position:fixed;
            bottom:30px;right:30px;
            background:linear-gradient(135deg, {config['color']} 0%, {config['bg_light']} 100%);
            color:#1f2937;
            padding:12px 24px;
            border-radius:12px;
            font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
            font-weight:600;
            box-shadow:0 4px 20px rgba(0,0,0,0.15);
            border-left:4px solid {config['color']};
            z-index:9999;
            animation:slideIn 0.3s ease-out, fadeOut {duration/1000}s {(duration-1000)/1000}s forwards;">
            <span style="font-size:18px;margin-right:8px;">{config['icon']}</span>
            {message}
        </div>
        <style>
        @keyframes slideIn {{
          from {{
            transform: translateX(400px);
            opacity: 0;
          }}
          to {{
            transform: translateX(0);
            opacity: 1;
          }}
        }}
        @keyframes fadeOut {{
          0% {{opacity:1;}}
          100% {{opacity:0;visibility:hidden;}}
        }}
        </style>
    """, height=80)


def toast_success(message: str, duration: int = 3000) -> None:
    """
    Display a success toast notification.

    Args:
        message: Success message to display
        duration: Duration in milliseconds (default: 3000ms)

    Example:
        >>> toast_success("Transaction successfully saved!")
    """
    show_toast(message, "success", duration)


def toast_warning(message: str, duration: int = 3000) -> None:
    """
    Display a warning toast notification.

    Args:
        message: Warning message to display
        duration: Duration in milliseconds (default: 3000ms)

    Example:
        >>> toast_warning("Duplicate transaction detected")
    """
    show_toast(message, "warning", duration)


def toast_error(message: str, duration: int = 3000) -> None:
    """
    Display an error toast notification.

    Args:
        message: Error message to display
        duration: Duration in milliseconds (default: 3000ms)

    Example:
        >>> toast_error("Failed to save transaction")
    """
    show_toast(message, "error", duration)


# ==============================
# 🏷️ BADGE COMPONENTS
# ==============================

def get_badge_html(transaction: Dict[str, Any]) -> str:
    """
    Generate HTML badge for a transaction based on its source.

    Args:
        transaction: Transaction dictionary with 'source' and 'type' keys

    Returns:
        HTML string for the badge with appropriate styling

    Example:
        >>> tx = {'source': 'OCR', 'type': 'dépense'}
        >>> badge = get_badge_html(tx)
        >>> '🧾 Ticket' in badge
        True
    """
    source = transaction.get("source", "")
    type_transaction = transaction.get("type", "")

    if source == "OCR":
        badge = "🧾 Ticket"
        couleur = "#1f77b4"
        emoji = "🧾"
    elif source == "PDF":
        if type_transaction == "revenu":
            badge = "💼 Bulletin"
            couleur = "#2ca02c"
            emoji = "💼"
        else:
            badge = "📄 Facture"
            couleur = "#ff7f0e"
            emoji = "📄"
    elif source in ["manuel", "récurrente", "récurrente_auto"]:
        badge = "📝 Manuel"
        couleur = "#7f7f7f"
        emoji = "📝"
    else:
        badge = "📎 Autre"
        couleur = "#9467bd"
        emoji = "📎"

    return f"<span style='background-color: {couleur}; color: white; padding: 4px 12px; border-radius: 16px; font-size: 0.8em; font-weight: bold;'>{emoji} {badge}</span>"


def get_badge_icon(transaction: Dict[str, Any]) -> str:
    """
    Get the icon emoji for a transaction based on its source.

    Args:
        transaction: Transaction dictionary with 'source' and 'type' keys

    Returns:
        Emoji string representing the transaction source

    Example:
        >>> tx = {'source': 'OCR', 'type': 'dépense'}
        >>> icon = get_badge_icon(tx)
        >>> icon
        '🧾'
    """
    source = transaction.get("source", "")
    type_transaction = transaction.get("type", "")

    if source == "OCR":
        return "🧾"
    elif source == "PDF":
        return "💼" if type_transaction == "revenu" else "📄"
    elif source in ["manuel", "récurrente", "récurrente_auto"]:
        return "📝"
    else:
        return "📎"


# ==============================
# 📋 TRANSACTION DISPLAY COMPONENTS
# ==============================

def afficher_carte_transaction(transaction: Dict[str, Any], idx: Optional[int] = None) -> None:
    """
    Display a transaction card with details and associated documents.

    Creates a two-column layout showing transaction details on the left
    and amount/documents on the right.

    Args:
        transaction: Transaction dictionary with keys:
            - categorie: Category name
            - sous_categorie: Subcategory name
            - date: Transaction date
            - description: Optional description
            - recurrence: Optional recurrence pattern
            - type: 'revenu' or 'dépense'
            - montant: Amount
            - source: Transaction source (OCR, PDF, etc.)
        idx: Optional index for the transaction (not used but kept for compatibility)

    Example:
        >>> tx = {
        ...     'categorie': 'Alimentation',
        ...     'sous_categorie': 'Restaurant',
        ...     'date': '2025-01-15',
        ...     'type': 'dépense',
        ...     'montant': 45.50,
        ...     'source': 'OCR'
        ... }
        >>> afficher_carte_transaction(tx)
    """
    col1, col2 = st.columns([3, 1])

    with col1:
        st.write(f"**Catégorie :** {transaction['categorie']}")
        st.write(f"**Sous-catégorie :** {transaction['sous_categorie']}")
        st.write(f"**Date :** {transaction['date']}")

        if transaction.get('description'):
            st.write(f"**Description :** {transaction['description']}")

        if transaction.get('recurrence'):
            st.write(f"**Récurrence :** {transaction['recurrence']}")

    with col2:
        montant_color = "green" if transaction['type'] == 'revenu' else "red"
        montant_prefix = "+" if transaction['type'] == 'revenu' else "-"
        st.markdown(
            f"<h2 style='color: {montant_color}; text-align: center;'>"
            f"{montant_prefix}{transaction['montant']:.2f} €</h2>",
            unsafe_allow_html=True
        )

        # Display documents automatically if available
        if transaction['source'] in ['OCR', 'PDF']:
            st.markdown("---")
            st.markdown("**📎 Documents :**")
            # Handle both dict and Series
            if hasattr(transaction, 'to_dict'):
                afficher_documents_associes(transaction.to_dict())
            else:
                afficher_documents_associes(transaction)


def afficher_documents_associes(transaction: Dict[str, Any]) -> None:
    """
    Display documents associated with a transaction in an enhanced format.

    Shows images and PDFs in tabs, with OCR text extraction capabilities
    for images and text preview for PDFs.

    Args:
        transaction: Transaction dictionary with keys:
            - categorie: Category name
            - sous_categorie: Subcategory name
            - date: Transaction date
            - source: Transaction source
            - type: Transaction type

    Side effects:
        - Displays images using st.image()
        - Shows PDF download buttons
        - May display expanders with OCR text or PDF content

    Example:
        >>> tx = {
        ...     'categorie': 'Alimentation',
        ...     'sous_categorie': 'Restaurant',
        ...     'date': '2025-01-15',
        ...     'source': 'OCR',
        ...     'type': 'dépense'
        ... }
        >>> afficher_documents_associes(tx)
    """
    fichiers = trouver_fichiers_associes(transaction)

    if not fichiers:
        source = transaction.get("source", "")
        type_transaction = transaction.get("type", "")

        if source == "OCR":
            st.warning("🧾 Aucun ticket de caisse trouvé dans les dossiers")
        elif source == "PDF":
            if type_transaction == "revenu":
                st.warning("💼 Aucun bulletin de paie trouvé")
            else:
                st.warning("📄 Aucune facture trouvée")
        else:
            st.info("📝 Aucun document associé")
        return

    # Display each file in tabs
    tabs = st.tabs([f"Document {i+1}" for i in range(len(fichiers))])

    for i, (tab, fichier) in enumerate(zip(tabs, fichiers)):
        with tab:
            nom_fichier = os.path.basename(fichier)

            if fichier.lower().endswith(('.jpg', '.jpeg', '.png')):
                # Display the image
                try:
                    image = Image.open(fichier)
                    st.image(image, caption=f"🧾 {nom_fichier}", use_column_width=True)

                    # Optional: Re-OCR
                    with st.expander("🔍 Analyser le texte"):
                        # Import here to avoid circular dependency
                        try:
                            from modules.ocr.scanner import full_ocr
                            texte_ocr = full_ocr(fichier, show_ticket=False)
                            st.text_area("Texte du ticket:", texte_ocr, height=150)
                        except ImportError:
                            st.warning("OCR module not available")

                except Exception as e:
                    toast_error(f"Impossible d'afficher l'image: {e}")

            elif fichier.lower().endswith('.pdf'):
                # Display PDF info
                st.success(f"📄 **{nom_fichier}**")

                # Extract text automatically
                try:
                    # Import here to avoid circular dependency
                    try:
                        from modules.ocr.parsers import extract_text_from_pdf
                        texte_pdf = extract_text_from_pdf(fichier)
                        if texte_pdf.strip():
                            with st.expander("📖 Contenu du document"):
                                apercu = texte_pdf[:2000] + "..." if len(texte_pdf) > 2000 else texte_pdf
                                st.text_area("Extrait:", apercu, height=200)
                    except ImportError:
                        st.info("📄 Document PDF (extraction de texte non disponible)")
                except Exception:
                    st.info("📄 Document PDF (contenu non extrait)")

                # Download button
                with open(fichier, "rb") as f:
                    st.download_button(
                        label="⬇️ Télécharger le document",
                        data=f.read(),
                        file_name=nom_fichier,
                        mime="application/pdf",
                        use_container_width=True
                    )


# ==============================
# 💰 CATEGORY VISUALIZATION & FILTERING SYSTEM
# ==============================
# Unified system with proportional bubbles + chips for category management

import pandas as pd
import math
import time
from typing import List, Dict, Any

@st.cache_data(ttl=300)
def calculate_category_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate statistics for each category (amount, percentage, count).

    Args:
        df: Transaction DataFrame

    Returns:
        DataFrame with columns: [categorie, montant, pct, count, type_predominant]
    """
    if df.empty:
        return pd.DataFrame(columns=['categorie', 'montant', 'pct', 'count', 'type_predominant'])

    df_copy = df.copy()
    df_copy['type'] = df_copy['type'].str.lower().str.strip()

    stats = df_copy.groupby('categorie', as_index=False).agg({
        'montant': ['sum', 'count'],
        'type': lambda x: x.mode()[0] if len(x.mode()) > 0 else 'dépense'
    }).reset_index(drop=True)

    stats.columns = ['categorie', 'montant', 'count', 'type_predominant']
    stats['montant'] = stats['montant'].round(2)

    total = stats['montant'].sum()
    stats['pct'] = (stats['montant'] / total * 100).round(1)

    return stats.sort_values('montant', ascending=False).reset_index(drop=True)


# ==============================
# 🫧 SIMPLIFIED STATE MANAGEMENT
# ==============================
# 🫧 BUBBLE NAVIGATION COMPONENT
# ==============================

def render_category_management(df: pd.DataFrame) -> pd.DataFrame:
    """
    Navigation élégante par bulles avec design moderne.

    Implémente une navigation en 3 niveaux avec esthétique premium:
    - Niveau 1: Choix Revenus/Dépenses (bulles colorées)
    - Niveau 2: Sélection de catégories (grille moderne)
    - Niveau 3: Affichage des transactions (détail enrichi)

    Args:
        df: DataFrame contenant les transactions

    Returns:
        DataFrame filtré selon la sélection de l'utilisateur
    """
    # Initialiser l'état de navigation
    if 'nav_level' not in st.session_state:
        st.session_state.nav_level = 'type_selection'
    if 'selected_type' not in st.session_state:
        st.session_state.selected_type = None
    if 'selected_category' not in st.session_state:
        st.session_state.selected_category = None

    # CSS moderne et élégant
    st.markdown("""
    <style>
    /* Conteneur principal */
    .nav-container {
        margin: 30px 0;
    }

    /* Titre avec accent */
    .nav-title {
        font-size: 28px;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 30px;
        text-align: center;
    }

    /* Bouton type (Revenus/Dépenses) */
    .type-bubble {
        padding: 40px 20px;
        border-radius: 20px;
        text-align: center;
        font-weight: 600;
        transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
        border: 2px solid transparent;
        cursor: pointer;
        position: relative;
        overflow: hidden;
    }

    .type-bubble::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: rgba(255, 255, 255, 0.1);
        transition: left 0.3s ease;
        z-index: 0;
    }

    .type-bubble:hover::before {
        left: 100%;
    }

    .type-bubble > * {
        position: relative;
        z-index: 1;
    }

    /* Revenus */
    .revenus-bubble {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        box-shadow: 0 10px 40px rgba(16, 185, 129, 0.3);
    }

    .revenus-bubble:hover {
        transform: translateY(-5px);
        box-shadow: 0 20px 60px rgba(16, 185, 129, 0.4);
        border-color: rgba(255, 255, 255, 0.3);
    }

    /* Dépenses */
    .depenses-bubble {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: white;
        box-shadow: 0 10px 40px rgba(245, 158, 11, 0.3);
    }

    .depenses-bubble:hover {
        transform: translateY(-5px);
        box-shadow: 0 20px 60px rgba(245, 158, 11, 0.4);
        border-color: rgba(255, 255, 255, 0.3);
    }

    /* Montant dans la bulle */
    .bubble-amount {
        font-size: 32px;
        font-weight: 700;
        margin: 10px 0;
        text-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
    }

    .bubble-subtitle {
        font-size: 14px;
        opacity: 0.95;
        margin: 5px 0;
    }

    /* Grille de catégories */
    .categories-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 15px;
        margin: 30px 0;
    }

    /* Bouton catégorie */
    .category-card {
        padding: 25px;
        border-radius: 16px;
        text-align: center;
        cursor: pointer;
        border: 2px solid transparent;
        transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        position: relative;
        overflow: hidden;
    }

    .category-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
        transition: left 0.5s;
    }

    .category-card:hover::before {
        left: 100%;
    }

    .category-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 15px 50px rgba(0, 0, 0, 0.15);
        border-color: #667eea;
    }

    .category-card > * {
        position: relative;
        z-index: 1;
    }

    .category-icon {
        font-size: 32px;
        margin-bottom: 8px;
    }

    .category-name {
        font-weight: 600;
        font-size: 16px;
        color: #1f2937;
        margin: 8px 0;
    }

    .category-amount {
        font-size: 20px;
        font-weight: 700;
        color: #667eea;
        margin: 5px 0;
    }

    .category-count {
        font-size: 12px;
        color: #6b7280;
        opacity: 0.8;
    }

    /* Bouton retour */
    .back-button {
        padding: 10px 20px;
        border-radius: 10px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        display: inline-block;
        margin-bottom: 20px;
    }

    .back-button:hover {
        transform: scale(1.05);
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
    }

    /* Breadcrumb navigation */
    .breadcrumb-nav {
        font-size: 14px;
        color: #6b7280;
        margin-bottom: 20px;
        font-weight: 500;
    }

    .breadcrumb-nav span {
        color: #667eea;
        font-weight: 600;
    }

    /* Section titre avec icône */
    .section-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 25px;
        padding-bottom: 15px;
        border-bottom: 3px solid #f0f0f0;
    }

    .section-header h2 {
        margin: 0;
        font-size: 24px;
        font-weight: 700;
        color: #1f2937;
    }

    /* Métrique élégante */
    .metric-enhanced {
        background: linear-gradient(135deg, #f5f7fa 0%, #e9ecef 100%);
        padding: 20px;
        border-radius: 12px;
        border-left: 4px solid #667eea;
        transition: all 0.3s ease;
    }

    .metric-enhanced:hover {
        box-shadow: 0 5px 20px rgba(0, 0, 0, 0.1);
        transform: translateY(-2px);
    }

    .metric-label {
        font-size: 12px;
        color: #6b7280;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
    }

    .metric-value {
        font-size: 28px;
        font-weight: 700;
        color: #667eea;
        margin: 0;
    }

    /* Divider élégant */
    .elegant-divider {
        height: 2px;
        background: linear-gradient(90deg, transparent, #e5e7eb, transparent);
        margin: 30px 0;
        border: none;
    }
    </style>
    """, unsafe_allow_html=True)

    # NIVEAU 1: Sélection Revenus/Dépenses
    if st.session_state.nav_level == 'type_selection':
        st.markdown('<div class="nav-title">💰 Explorez votre Univers Financier</div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2, gap="large")

        revenus_total = df[df['type'] == 'revenu']['montant'].sum()
        revenus_count = len(df[df['type'] == 'revenu'])
        depenses_total = df[df['type'] == 'dépense']['montant'].sum()
        depenses_count = len(df[df['type'] == 'dépense'])

        with col1:
            # Bulle revenus
            st.markdown(f"""
            <div class="type-bubble revenus-bubble">
                <div style="font-size: 48px; margin-bottom: 10px;">💼</div>
                <div style="font-size: 18px; font-weight: 700; margin-bottom: 5px;">REVENUS</div>
                <div class="bubble-amount">{revenus_total:,.0f}€</div>
                <div class="bubble-subtitle">{revenus_count} transactions</div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("Voir les revenus", key="btn_revenus", use_container_width=True):
                st.session_state.selected_type = 'revenu'
                st.session_state.nav_level = 'category_selection'
                st.rerun()

        with col2:
            # Bulle dépenses
            st.markdown(f"""
            <div class="type-bubble depenses-bubble">
                <div style="font-size: 48px; margin-bottom: 10px;">🛒</div>
                <div style="font-size: 18px; font-weight: 700; margin-bottom: 5px;">DÉPENSES</div>
                <div class="bubble-amount">{depenses_total:,.0f}€</div>
                <div class="bubble-subtitle">{depenses_count} transactions</div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("Voir les dépenses", key="btn_depenses", use_container_width=True):
                st.session_state.selected_type = 'dépense'
                st.session_state.nav_level = 'category_selection'
                st.rerun()

        return df

    # NIVEAU 2: Sélection de catégories
    elif st.session_state.nav_level == 'category_selection':
        if st.session_state.selected_type:
            # Bouton retour
            if st.button("← Retour", key="btn_back_to_type", help="Retour à la sélection du type"):
                st.session_state.nav_level = 'type_selection'
                st.session_state.selected_type = None
                st.session_state.selected_category = None
                st.rerun()

            # Filtrer par type
            df_filtered = df[df['type'] == st.session_state.selected_type]

            # Breadcrumb
            type_label = "Revenus" if st.session_state.selected_type == 'revenu' else "Dépenses"
            st.markdown(f'<div class="breadcrumb-nav">Sélection → <span>{type_label}</span></div>', unsafe_allow_html=True)

            # Titre section
            emoji = "💼" if st.session_state.selected_type == 'revenu' else "🛒"
            st.markdown(f'<div class="section-header"><h2>{emoji} Catégories</h2></div>', unsafe_allow_html=True)

            # Statistiques par catégorie
            cat_stats = df_filtered.groupby('categorie').agg({
                'montant': 'sum',
                'sous_categorie': 'count'
            }).reset_index()
            cat_stats.columns = ['categorie', 'montant', 'count']
            cat_stats = cat_stats.sort_values('montant', ascending=False)

            # Afficher les catégories en grille
            st.markdown('<div class="categories-grid">', unsafe_allow_html=True)

            for idx, row in cat_stats.iterrows():
                col = st.columns(3)[idx % 3]
                with col:
                    # Catégorie card
                    category_name = row['categorie']
                    category_emoji = _get_category_emoji(category_name)

                    st.markdown(f"""
                    <div class="category-card">
                        <div class="category-icon">{category_emoji}</div>
                        <div class="category-name">{category_name}</div>
                        <div class="category-amount">{row['montant']:,.0f}€</div>
                        <div class="category-count">{int(row['count'])} items</div>
                    </div>
                    """, unsafe_allow_html=True)

                    if st.button(f"Voir", key=f"btn_cat_{category_name}", use_container_width=True):
                        st.session_state.selected_category = category_name
                        st.session_state.nav_level = 'detail'
                        st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)
            return df_filtered

    # NIVEAU 3: Détail des transactions
    elif st.session_state.nav_level == 'detail':
        if st.session_state.selected_category:
            # Bouton retour
            if st.button("← Retour", key="btn_back_to_cat", help="Retour aux catégories"):
                st.session_state.nav_level = 'category_selection'
                st.session_state.selected_category = None
                st.rerun()

            # Filtrer par type et catégorie
            df_filtered = df[
                (df['type'] == st.session_state.selected_type) &
                (df['categorie'] == st.session_state.selected_category)
            ]

            # Breadcrumb
            type_label = "Revenus" if st.session_state.selected_type == 'revenu' else "Dépenses"
            st.markdown(f'<div class="breadcrumb-nav">Sélection → <span>{type_label}</span> → <span>{st.session_state.selected_category}</span></div>', unsafe_allow_html=True)

            # Titre section
            category_emoji = _get_category_emoji(st.session_state.selected_category)
            st.markdown(f'<div class="section-header"><h2>{category_emoji} {st.session_state.selected_category}</h2></div>', unsafe_allow_html=True)

            # Statistiques avec style amélioré
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown(f"""
                <div class="metric-enhanced">
                    <div class="metric-label">💰 Total</div>
                    <div class="metric-value">{df_filtered['montant'].sum():,.0f}€</div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                <div class="metric-enhanced">
                    <div class="metric-label">📊 Transactions</div>
                    <div class="metric-value">{len(df_filtered)}</div>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                st.markdown(f"""
                <div class="metric-enhanced">
                    <div class="metric-label">🏷️ Sous-catégories</div>
                    <div class="metric-value">{df_filtered['sous_categorie'].nunique()}</div>
                </div>
                """, unsafe_allow_html=True)

            # Divider
            st.markdown('<div class="elegant-divider"></div>', unsafe_allow_html=True)

            # Afficher les transactions
            st.subheader("📋 Détail des transactions")
            for idx, transaction in df_filtered.iterrows():
                afficher_carte_transaction(transaction, idx)

            return df_filtered

    # Par défaut retourner tout
    return df


def _get_category_emoji(category: str) -> str:
    """Retourne l'emoji approprié pour une catégorie."""
    category_emojis = {
        'Alimentation': '🍽️',
        'Transport': '🚗',
        'Loisirs': '🎮',
        'Logement': '🏠',
        'Santé': '⚕️',
        'Shopping': '🛍️',
        'Éducation': '📚',
        'Assurances': '🛡️',
        'Abonnements': '📱',
        'Divertissement': '🎬',
        'Utilities': '⚡',
        'Autre': '📎',
    }
    return category_emojis.get(category, '📌')
