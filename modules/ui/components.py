"""Reusable UI components for the application.

This module contains toast notifications, badges, and transaction display components.
"""

import os
import logging
from typing import Dict, Any, Optional
import streamlit as st
import streamlit.components.v1 as components
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
# 🔵 BUBBLE FILTER COMPONENT
# ==============================

import pandas as pd
from typing import List, Tuple

def render_bubble_filter(df: pd.DataFrame) -> Tuple[List[str], List[str]]:
    """
    Render interactive bubble filter for transactions with drill-down support.

    Features:
    - Display categories as clickable bubbles
    - Multi-selection with session state
    - Bubble size proportional to total amount
    - Bubble color based on type (expense=red, revenue=green)
    - Drill-down into subcategories
    - Breadcrumb navigation
    - Clear all filters button

    Args:
        df: DataFrame with transaction data

    Returns:
        Tuple of (selected_categories, selected_subcategories) for filtering

    Example:
        >>> df = load_transactions()
        >>> categories, subcategories = render_bubble_filter(df)
        >>> filtered = df[df['categorie'].isin(categories)]
    """

    # Initialize session state
    if 'bubble_drill_level' not in st.session_state:
        st.session_state.bubble_drill_level = 'categories'
    if 'bubble_current_category' not in st.session_state:
        st.session_state.bubble_current_category = None
    if 'bubble_selected_categories' not in st.session_state:
        st.session_state.bubble_selected_categories = []
    if 'bubble_selected_subcategories' not in st.session_state:
        st.session_state.bubble_selected_subcategories = []


    # Section header
    st.subheader("🔍 Filtres par Bulles")

    # Calculate stats by category/type
    df_copy = df.copy()
    df_copy['type'] = df_copy['type'].str.lower().str.strip()

    # ===== CATEGORIES VIEW =====
    if st.session_state.bubble_drill_level == 'categories':
        # Get unique categories with their stats
        categories_stats = df_copy.groupby('categorie').agg({
            'montant': 'sum',
            'type': lambda x: x.mode()[0] if len(x.mode()) > 0 else 'dépense'
        }).reset_index()
        categories_stats.columns = ['categorie', 'total_montant', 'predominant_type']
        categories_stats = categories_stats.sort_values('total_montant', ascending=False)

        # Find min/max for bubble size calculation
        min_amount = categories_stats['total_montant'].min()
        max_amount = categories_stats['total_montant'].max()
        amount_range = max(max_amount - min_amount, 1)  # Avoid division by 0

        # Create breadcrumb
        st.markdown("**📍 Catégories principales**", unsafe_allow_html=True)

        # Clear all button
        col1, col2 = st.columns([6, 1])
        with col2:
            if st.button("🔄 Effacer tous", key="clear_all_bubbles"):
                st.session_state.bubble_selected_categories = []
                st.session_state.bubble_selected_subcategories = []
                st.rerun()

        # Render category bubbles
        col_count = 0
        cols = st.columns(4)

        for idx, row in categories_stats.iterrows():
            cat_name = row['categorie']
            total = row['total_montant']
            cat_type = row['predominant_type']

            # Calculate bubble size factor (scaling between 0.8 and 1.4)
            size_factor = 0.8 + 0.6 * ((total - min_amount) / amount_range)

            # Determine color based on type
            if cat_type == 'revenu':
                bubble_color = '#c8e6c9'
                bubble_border = '#4CAF50'
            else:
                bubble_color = '#ffcdd2'
                bubble_border = '#f44336'

            is_selected = cat_name in st.session_state.bubble_selected_categories

            with cols[col_count % 4]:
                # Create a two-button layout
                col_bubble, col_drill = st.columns([3, 1])

                with col_bubble:
                    # Simple button with label
                    button_label = f"{'✓ ' if is_selected else ''}{cat_name}\n{total:.0f} €"
                    if st.button(button_label, key=f"bubble_cat_{cat_name}", use_container_width=True, help=f"Cliquer pour {'désélectionner' if is_selected else 'sélectionner'} {cat_name}"):
                        # Toggle selection
                        if cat_name in st.session_state.bubble_selected_categories:
                            st.session_state.bubble_selected_categories.remove(cat_name)
                        else:
                            st.session_state.bubble_selected_categories.append(cat_name)
                        st.rerun()

                with col_drill:
                    if st.button("📂", key=f"drill_cat_{cat_name}", help="Voir sous-catégories", use_container_width=True):
                        st.session_state.bubble_drill_level = 'subcategories'
                        st.session_state.bubble_current_category = cat_name
                        st.rerun()

            col_count += 1

    # ===== SUBCATEGORIES VIEW =====
    elif st.session_state.bubble_drill_level == 'subcategories':
        current_cat = st.session_state.bubble_current_category

        # Create breadcrumb with back button
        col1, col2, col3 = st.columns([1, 4, 1])
        with col1:
            if st.button("⬅️ Retour", key="back_to_categories"):
                st.session_state.bubble_drill_level = 'categories'
                st.session_state.bubble_current_category = None
                st.rerun()

        with col2:
            st.markdown(f"**📍 Sous-catégories de _{current_cat}_**", unsafe_allow_html=True)

        # Filter by parent category
        df_filtered = df_copy[df_copy['categorie'] == current_cat]

        # Get subcategories
        subcats_stats = df_filtered.groupby('sous_categorie').agg({
            'montant': 'sum',
            'type': lambda x: x.mode()[0] if len(x.mode()) > 0 else 'dépense'
        }).reset_index()
        subcats_stats.columns = ['sous_categorie', 'total_montant', 'predominant_type']
        subcats_stats = subcats_stats.sort_values('total_montant', ascending=False)

        # Find min/max for bubble size
        min_amount = subcats_stats['total_montant'].min()
        max_amount = subcats_stats['total_montant'].max()
        amount_range = max(max_amount - min_amount, 1)

        # Render subcategory bubbles
        col_count = 0
        cols = st.columns(4)

        for idx, row in subcats_stats.iterrows():
            subcat_name = row['sous_categorie']
            total = row['total_montant']
            subcat_type = row['predominant_type']

            # Size factor
            size_factor = 0.8 + 0.6 * ((total - min_amount) / amount_range)

            # Color based on type
            if subcat_type == 'revenu':
                bubble_color = '#c8e6c9'
                bubble_border = '#4CAF50'
            else:
                bubble_color = '#ffcdd2'
                bubble_border = '#f44336'

            is_selected = subcat_name in st.session_state.bubble_selected_subcategories

            with cols[col_count % 4]:
                # Simple button with label
                button_label = f"{'✓ ' if is_selected else ''}{subcat_name}\n{total:.0f} €"
                if st.button(button_label, key=f"bubble_subcat_{subcat_name}", use_container_width=True, help=f"Cliquer pour {'désélectionner' if is_selected else 'sélectionner'} {subcat_name}"):
                    # Toggle selection
                    if subcat_name in st.session_state.bubble_selected_subcategories:
                        st.session_state.bubble_selected_subcategories.remove(subcat_name)
                    else:
                        st.session_state.bubble_selected_subcategories.append(subcat_name)
                    st.rerun()

            col_count += 1

    return (
        st.session_state.bubble_selected_categories,
        st.session_state.bubble_selected_subcategories
    )
