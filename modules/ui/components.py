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
# ==============================
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
