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
# 💰 CATEGORY VISUALIZATION & FILTERING SYSTEM
# ==============================
# Dual-view system with proportional bubbles + chips for category management

import pandas as pd
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


def render_view_mode_selector() -> str:
    """
    Render radio buttons to select between different visualization modes.

    Returns:
        Selected mode: 'bubbles' | 'chips' | 'hybrid'
    """
    # Initialize session state
    if 'category_view_mode' not in st.session_state:
        st.session_state.category_view_mode = 'hybrid'

    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.button("📊 Graphique", use_container_width=True,
                     key="btn_bubbles", help="Vue avec bulles proportionnelles"):
            st.session_state.category_view_mode = 'bubbles'

    with col2:
        if st.button("🏷️ Chips", use_container_width=True,
                     key="btn_chips", help="Vue avec tags de filtrage"):
            st.session_state.category_view_mode = 'chips'

    with col3:
        if st.button("🔄 Hybride", use_container_width=True,
                     key="btn_hybrid", help="Vue combinée"):
            st.session_state.category_view_mode = 'hybrid'

    return st.session_state.category_view_mode


def render_category_management(df: pd.DataFrame) -> List[str]:
    """
    Main function combining both visualization systems.
    Returns list of selected categories for filtering.

    Args:
        df: Transaction DataFrame

    Returns:
        List of selected category names
    """
    # Initialize session state
    for key in ['selected_categories', 'drill_level', 'parent_category', 'breadcrumb']:
        if key not in st.session_state:
            init_vals = {
                'selected_categories': [],
                'drill_level': 'categories',
                'parent_category': None,
                'breadcrumb': ['Toutes']
            }
            st.session_state[key] = init_vals[key]

    # Add CSS styles
    st.markdown("""
    <style>
    .bubble-container {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        align-items: center;
        gap: 20px;
        padding: 30px;
        min-height: 250px;
        background: #f8f9fa;
        border-radius: 12px;
    }

    .bubble {
        border-radius: 20px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        cursor: pointer;
        transition: all 0.3s ease;
        border: 2px solid;
        opacity: 0.75;
        text-align: center;
        padding: 10px;
        font-weight: 500;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .bubble:hover {
        transform: scale(1.05);
        box-shadow: 0 8px 16px rgba(0,0,0,0.15);
        opacity: 1;
    }

    .bubble-selected {
        border-width: 3px;
        opacity: 1;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }

    .bubble-expense {
        background: rgba(239, 68, 68, 0.15);
        border-color: #ef4444;
        color: #991b1b;
    }

    .bubble-revenue {
        background: rgba(16, 185, 129, 0.15);
        border-color: #10b981;
        color: #065f46;
    }

    .chips-container {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        padding: 20px;
        background: #f8f9fa;
        border-radius: 12px;
    }

    .chip {
        display: inline-block;
        padding: 8px 16px;
        margin: 0;
        border-radius: 20px;
        border: 2px solid #e0e0e0;
        background: white;
        cursor: pointer;
        transition: all 0.2s ease;
        font-size: 13px;
        font-weight: 500;
        white-space: nowrap;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }

    .chip:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        border-color: #999;
    }

    .chip-selected {
        background: #e8f5e9;
        border-color: #4CAF50;
        border-width: 2px;
        color: #2e7d32;
        font-weight: 600;
    }

    .breadcrumb {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 10px 0;
        font-size: 13px;
        margin-bottom: 15px;
    }

    .breadcrumb-item {
        padding: 4px 8px;
        background: #e8e9eb;
        border-radius: 4px;
        cursor: pointer;
    }

    .breadcrumb-item:hover {
        background: #d4d5d7;
    }

    .breadcrumb-item.active {
        background: #4CAF50;
        color: white;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

    # Display header
    st.markdown("## 💰 Gestion des Catégories")

    # Mode selector
    mode = render_view_mode_selector()
    st.markdown("---")

    # Get category stats
    stats = calculate_category_stats(df)

    if stats.empty:
        st.info("Aucune catégorie trouvée")
        return []

    # Render based on mode
    if mode == 'bubbles':
        return _render_bubble_view(stats, df)
    elif mode == 'chips':
        return _render_chips_view(stats, df)
    else:  # hybrid
        return _render_hybrid_view(stats, df)


def _render_bubble_view(stats: pd.DataFrame, df: pd.DataFrame) -> List[str]:
    """Render proportional bubble visualization."""
    st.subheader("📊 Répartition Visuelle")

    selected = st.session_state.get('selected_categories', [])

    # Create bubble HTML
    bubble_html = '<div class="bubble-container">'

    for _, row in stats.iterrows():
        cat = row['categorie']
        amount = row['montant']
        pct = row['pct']
        cat_type = row['type_predominant']

        # Calculate bubble size (60px to 360px)
        ratio = amount / stats['montant'].sum() if stats['montant'].sum() > 0 else 0
        size = int(60 + ratio * 300)

        bubble_type = 'revenue' if 'revenu' in cat_type else 'expense'
        is_selected = cat in selected

        bubble_html += f"""
        <div class="bubble bubble-{bubble_type} {'bubble-selected' if is_selected else ''}"
             style="width: {size}px; height: {size}px; font-size: {10 + ratio * 8}px;">
            <strong>{cat}</strong>
            <div style="font-size: 0.85em; margin-top: 4px;">{amount:.0f}€</div>
            <div style="font-size: 0.75em; opacity: 0.8;">{pct}%</div>
        </div>
        """

    bubble_html += '</div>'
    st.markdown(bubble_html, unsafe_allow_html=True)

    # Selection via buttons below
    st.markdown("### Cliquer sur une catégorie :")
    cols = st.columns(4)

    for idx, (_, row) in enumerate(stats.iterrows()):
        cat = row['categorie']
        is_selected = cat in selected

        with cols[idx % 4]:
            button_text = f"{'✓ ' if is_selected else ''}{cat}\n{row['montant']:.0f}€"
            if st.button(button_text, key=f"bubble_select_{cat}", use_container_width=True):
                if cat in selected:
                    selected.remove(cat)
                else:
                    selected.append(cat)

    st.session_state.selected_categories = selected
    return selected


def _render_chips_view(stats: pd.DataFrame, df: pd.DataFrame) -> List[str]:
    """Render chips/tags visualization with multi-selection."""
    st.subheader("🏷️ Filtres Rapides")

    selected = st.session_state.get('selected_categories', [])

    # Render chips
    st.markdown('<div class="chips-container">', unsafe_allow_html=True)

    cols = st.columns(4)
    for idx, (_, row) in enumerate(stats.iterrows()):
        cat = row['categorie']
        amount = row['montant']
        is_selected = cat in selected

        chip_html = f"{'✓ ' if is_selected else ''}{cat} | {amount:.0f}€"

        with cols[idx % 4]:
            if st.button(chip_html, key=f"chip_select_{cat}", use_container_width=True,
                        help=f"{'Désélectionner' if is_selected else 'Sélectionner'} {cat}"):
                if cat in selected:
                    selected.remove(cat)
                else:
                    selected.append(cat)

    st.markdown('</div>', unsafe_allow_html=True)

    # Show selection counter
    if selected:
        trans_count = len(df[df['categorie'].isin(selected)])
        st.info(f"📊 {len(selected)} catégorie(s) sélectionnée(s) → {trans_count} transactions")

    # Action buttons
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🔄 Effacer tout", use_container_width=True):
            selected.clear()

    with col2:
        if len(selected) == 1 and st.button("↓ Voir sous-catégories", use_container_width=True):
            st.session_state.drill_level = 'subcategories'
            st.session_state.parent_category = selected[0]
            st.rerun()

    st.session_state.selected_categories = selected
    return selected


def _render_hybrid_view(stats: pd.DataFrame, df: pd.DataFrame) -> List[str]:
    """Render combined view with bubbles and chips synchronized."""
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### 📊 Répartition")
        selected = _render_bubble_view_minimal(stats, df)

    with col2:
        st.markdown("### 🏷️ Sélection")
        selected = _render_chips_view_minimal(stats, df, selected)

    return selected


def _render_bubble_view_minimal(stats: pd.DataFrame, df: pd.DataFrame) -> List[str]:
    """Minimal bubble view for hybrid mode."""
    selected = st.session_state.get('selected_categories', [])

    # Create simplified bubble HTML
    bubble_html = '<div class="bubble-container" style="min-height: 300px;">'

    for _, row in stats.iterrows():
        cat = row['categorie']
        amount = row['montant']
        pct = row['pct']
        cat_type = row['type_predominant']

        ratio = amount / stats['montant'].sum() if stats['montant'].sum() > 0 else 0
        size = int(50 + ratio * 250)

        bubble_type = 'revenue' if 'revenu' in cat_type else 'expense'
        is_selected = cat in selected

        bubble_html += f"""
        <div class="bubble bubble-{bubble_type} {'bubble-selected' if is_selected else ''}"
             style="width: {size}px; height: {size}px; font-size: {9 + ratio * 6}px;"
             onclick="alert('{cat}')">
            <strong>{cat}</strong>
            <div style="font-size: 0.8em; margin-top: 3px;">{pct}%</div>
        </div>
        """

    bubble_html += '</div>'
    st.markdown(bubble_html, unsafe_allow_html=True)

    return selected


def _render_chips_view_minimal(stats: pd.DataFrame, df: pd.DataFrame, selected: List[str]) -> List[str]:
    """Minimal chips view for hybrid mode."""
    for _, row in stats.iterrows():
        cat = row['categorie']
        is_selected = cat in selected

        button_text = f"{'✓ ' if is_selected else ''}{cat} | {row['montant']:.0f}€"
        if st.button(button_text, key=f"hybrid_chip_{cat}", use_container_width=True):
            if cat in selected:
                selected.remove(cat)
            else:
                selected.append(cat)

    st.session_state.selected_categories = selected
    return selected
