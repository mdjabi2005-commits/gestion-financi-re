"""Reusable UI components for the application.

This module contains toast notifications, badges, and transaction display components.
"""

import os
import logging
from typing import Dict, Any, Optional, List, Tuple
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

def _init_bubble_state() -> None:
    """Initialize simplified bubble navigation state."""
    if 'bubble_level' not in st.session_state:
        st.session_state.bubble_level = 'main'  # 'main' | 'categories' | 'subcategories'
    if 'selected_category' not in st.session_state:
        st.session_state.selected_category = None
    if 'animation_state' not in st.session_state:
        st.session_state.animation_state = None


def _reset_to_main() -> None:
    """Reset to main bubble view."""
    st.session_state.bubble_level = 'main'
    st.session_state.selected_category = None
    st.session_state.animation_state = None


def render_category_management(df: pd.DataFrame) -> pd.DataFrame:
    """
    Simplified bubble navigation system with 3 levels and explosion animation.

    Navigation:
    - Level 1: Main bubble (total expenses)
    - Level 2: Category bubbles (arranged in spiral/circle)
    - Level 3: Subcategories + Filtered transactions

    Args:
        df: Transaction DataFrame

    Returns:
        Filtered DataFrame based on navigation level
    """
    # Initialize state
    _init_bubble_state()

    # Get current level
    level = st.session_state.bubble_level

    # Render appropriate view
    if level == 'main':
        return _render_main_bubble(df)
    elif level == 'categories':
        return _render_category_bubbles(df)
    elif level == 'subcategories':
        return _render_subcategory_bubbles(df)

    return df


# ==============================
# 🫧 BUBBLE SYSTEM - SIMPLIFIED
# ==============================

# Color mapping for categories
CATEGORY_COLORS = {
    'Alimentation': '#10b981',    # Green
    'Transport': '#3b82f6',       # Blue
    'Loisirs': '#f59e0b',         # Orange
    'Logement': '#8b5cf6',        # Purple
    'Santé': '#ef4444',           # Red
    'Shopping': '#ec4899',        # Pink
    'Autres': '#6b7280'           # Gray
}

def _render_main_bubble(df: pd.DataFrame) -> pd.DataFrame:
    """
    Render the main bubble showing total expenses.
    Click on it to explode into categories.
    """
    df_expenses = df[df['type'] == 'dépense']
    total = df_expenses['montant'].sum()
    n_categories = df_expenses['categorie'].nunique()
    n_transactions = len(df_expenses)

    # CSS for universe background and main bubble
    css = """
    <style>
    .bubble-universe {
        background: radial-gradient(ellipse at center, #1a1a2e 0%, #0f0f1e 100%);
        border-radius: 30px;
        min-height: 500px;
        display: flex;
        justify-content: center;
        align-items: center;
        position: relative;
        overflow: hidden;
        box-shadow: inset 0 0 60px rgba(0, 0, 0, 0.8);
    }

    .main-bubble {
        width: 300px;
        height: 300px;
        border-radius: 50%;
        background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%);
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        cursor: pointer;
        box-shadow: 0 20px 60px rgba(59, 130, 246, 0.4);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        color: white;
        font-weight: 700;
        text-align: center;
        position: relative;
        animation: main-bubble-pulse 2s ease-in-out infinite;
    }

    .main-bubble:hover {
        transform: scale(1.05);
        box-shadow: 0 30px 80px rgba(59, 130, 246, 0.6);
    }

    .main-bubble:active {
        animation: bubble-explode 0.8s cubic-bezier(0.6, 0, 0.8, 1) forwards;
    }

    @keyframes main-bubble-pulse {
        0%, 100% {
            box-shadow: 0 20px 60px rgba(59, 130, 246, 0.4);
        }
        50% {
            box-shadow: 0 25px 70px rgba(59, 130, 246, 0.6);
        }
    }

    @keyframes bubble-explode {
        0% {
            transform: scale(1);
            opacity: 1;
        }
        50% {
            transform: scale(1.4);
            opacity: 0.6;
            filter: blur(2px);
        }
        100% {
            transform: scale(0);
            opacity: 0;
        }
    }

    .bubble-title {
        font-size: 18px;
        margin-bottom: 15px;
        text-transform: uppercase;
        letter-spacing: 1px;
        opacity: 0.9;
    }

    .bubble-amount {
        font-size: 56px;
        font-weight: 900;
        margin: 10px 0;
    }

    .bubble-info {
        font-size: 14px;
        opacity: 0.85;
        margin-top: 15px;
        line-height: 1.6;
    }

    .bubble-hint {
        font-size: 12px;
        margin-top: 20px;
        opacity: 0.7;
        animation: bounce 2s infinite;
    }

    @keyframes bounce {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-10px); }
    }
    </style>
    """

    st.markdown(css, unsafe_allow_html=True)

    # HTML for main bubble
    bubble_html = f'''
    <div class="bubble-universe">
        <div class="main-bubble" id="mainBubble">
            <div class="bubble-title">💰 Total Dépenses</div>
            <div class="bubble-amount">{total:,.0f}€</div>
            <div class="bubble-info">
                {n_categories} catégories<br>
                {n_transactions} transactions
            </div>
            <div class="bubble-hint">👆 Cliquez pour explorer</div>
        </div>
    </div>
    '''

    st.markdown(bubble_html, unsafe_allow_html=True)

    # Hidden button for state change
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("", key="go_to_categories", label_visibility="hidden", use_container_width=False):
            st.session_state.bubble_level = 'categories'
            st.rerun()

    return df_expenses


def _render_category_bubbles(df: pd.DataFrame) -> pd.DataFrame:
    """
    Render categories as bubbles in a spiral arrangement.
    Click on a bubble to drill into subcategories.
    """
    df_expenses = df[df['type'] == 'dépense']
    stats = df_expenses.groupby('categorie').agg({
        'montant': 'sum',
        'sous_categorie': 'count'
    }).reset_index()
    stats.columns = ['categorie', 'montant', 'count']
    stats = stats.sort_values('montant', ascending=False).reset_index(drop=True)

    if stats.empty:
        st.info("Aucune catégorie trouvée")
        return df_expenses

    # CSS for category bubbles (spiral arrangement)
    css = """
    <style>
    .bubble-universe {
        background: radial-gradient(ellipse at center, #1a1a2e 0%, #0f0f1e 100%);
        border-radius: 30px;
        min-height: 600px;
        position: relative;
        overflow: hidden;
        box-shadow: inset 0 0 60px rgba(0, 0, 0, 0.8);
    }

    .bubble-container {
        position: relative;
        width: 100%;
        height: 100%;
        min-height: 600px;
    }

    .category-bubble {
        position: absolute;
        border-radius: 50%;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        cursor: pointer;
        color: white;
        font-weight: 700;
        text-align: center;
        box-shadow: 0 15px 40px rgba(0, 0, 0, 0.4);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        animation: category-appear 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
    }

    .category-bubble:hover {
        transform: scale(1.1);
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6);
        filter: brightness(1.1);
    }

    @keyframes category-appear {
        0% {
            transform: scale(0) rotate(-180deg);
            opacity: 0;
        }
        100% {
            transform: scale(1) rotate(0);
            opacity: 1;
        }
    }

    .bubble-name {
        font-size: 1em;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
    }

    .bubble-amount {
        font-size: 1.6em;
        font-weight: 900;
        margin: 5px 0;
    }

    .bubble-count {
        font-size: 0.8em;
        opacity: 0.8;
        margin-top: 5px;
    }

    .breadcrumb-simple {
        position: absolute;
        top: 20px;
        left: 20px;
        background: rgba(255, 255, 255, 0.1);
        color: white;
        padding: 10px 20px;
        border-radius: 20px;
        font-size: 14px;
        backdrop-filter: blur(10px);
    }

    .back-button {
        position: absolute;
        top: 20px;
        right: 20px;
        background: rgba(239, 68, 68, 0.8);
        color: white;
        padding: 10px 20px;
        border-radius: 20px;
        font-size: 14px;
        cursor: pointer;
        transition: all 0.3s;
        backdrop-filter: blur(10px);
    }

    .back-button:hover {
        background: rgba(239, 68, 68, 1);
        transform: translateY(-2px);
    }
    </style>
    """

    st.markdown(css, unsafe_allow_html=True)

    # Calculate spiral positions (golden ratio)
    golden_angle = 137.5  # Golden angle in degrees
    max_amount = stats['montant'].max()

    # HTML for bubbles
    bubble_html = '<div class="bubble-universe"><div class="bubble-container">'
    bubble_html += '<div class="breadcrumb-simple">🏠 Catégories</div>'

    for i, (_, row) in enumerate(stats.iterrows()):
        cat = row['categorie']
        amount = row['montant']
        count = int(row['count'])

        # Spiral positioning
        angle = i * golden_angle * (math.pi / 180)
        radius = 100 + (i * 30)  # Expanding spiral
        x = 50 + (radius / 150) * 40 * math.cos(angle)
        y = 50 + (radius / 150) * 40 * math.sin(angle)

        # Size proportional to amount
        size = 80 + (amount / max_amount * 100)

        # Color from mapping
        color = CATEGORY_COLORS.get(cat, '#6b7280')

        # Build bubble
        bubble_html += f'''
        <div class="category-bubble"
             id="cat-{cat.replace(' ', '-')}"
             style="left:{x}%; top:{y}%; width:{size}px; height:{size}px;
                     background: linear-gradient(135deg, {color} 0%, {color}dd 100%);
                     animation-delay: {i*0.1}s;"
             onclick="selectCategory('{cat}')">
            <div class="bubble-name">{cat}</div>
            <div class="bubble-amount">{amount:.0f}€</div>
            <div class="bubble-count">{count} items</div>
        </div>
        '''

    bubble_html += '</div></div>'
    st.markdown(bubble_html, unsafe_allow_html=True)

    # Hidden buttons for navigation
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("Retour", key="back_to_main", use_container_width=False):
            _reset_to_main()
            st.rerun()

    with col3:
        # Category selection happens via click simulation
        for _, row in stats.iterrows():
            cat = row['categorie']
            if st.button(f"📂 {cat}", key=f"select_{cat}", use_container_width=False):
                st.session_state.selected_category = cat
                st.session_state.bubble_level = 'subcategories'
                st.rerun()

    return df_expenses


def _render_subcategory_bubbles(df: pd.DataFrame) -> pd.DataFrame:
    """
    Render filtered data for selected category with subcategories visualization.
    Returns filtered DataFrame for display.
    """
    selected_cat = st.session_state.selected_category

    if not selected_cat:
        st.error("Aucune catégorie sélectionnée")
        return df

    df_expenses = df[df['type'] == 'dépense']
    df_filtered = df_expenses[df_expenses['categorie'] == selected_cat]

    if df_filtered.empty:
        st.warning(f"Aucune transaction pour {selected_cat}")
        return df_filtered

    # Breadcrumb
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"### 🏠 {selected_cat}")
    with col2:
        if st.button("↩️ Retour", use_container_width=True):
            st.session_state.bubble_level = 'categories'
            st.session_state.selected_category = None
            st.rerun()

    # Show summary
    st.markdown("---")
    total = df_filtered['montant'].sum()
    n_subs = df_filtered['sous_categorie'].nunique()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total", f"{total:.2f}€")
    with col2:
        st.metric("Sous-catégories", n_subs)
    with col3:
        st.metric("Transactions", len(df_filtered))

    st.markdown("---")

    # Return filtered dataframe for display in parent
    return df_filtered


# ==============================
# 📊 BUBBLE VISUALIZATION
# ==============================

def render_bubble_visualization(stats: pd.DataFrame, selected: List[str]) -> None:
    """
    Render pure visual bubble chart with proportional sizes (non-interactive).
    The bubbles show the visual proportions, interaction happens via buttons below.

    Args:
        stats: Category statistics DataFrame with columns [categorie, montant, pct]
        selected: List of currently selected categories
    """
    if stats.empty:
        return

    # Calculate bubble sizes
    max_amount = stats['montant'].max()
    min_size = 80   # Minimum bubble diameter in pixels
    max_size = 220  # Maximum bubble diameter in pixels

    # Create CSS styles - DESIGN ÉPURÉ ET MODERNE
    css_styles = """
    <style>
    .bubble-viz-container {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        align-items: center;
        gap: 35px;
        padding: 60px 30px;
        background: linear-gradient(to bottom, #f8fafc, #f1f5f9);
        border-radius: 20px;
        margin: 20px 0;
        min-height: 380px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
    }

    .viz-bubble {
        border-radius: 50%;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        border: 3px solid #cbd5e0;
        background: #ffffff;
        color: #1e293b;
        font-weight: 600;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        cursor: default;
    }

    .viz-bubble:hover {
        transform: translateY(-8px);
        box-shadow: 0 12px 24px rgba(0, 0, 0, 0.12);
        border-color: #94a3b8;
    }

    .viz-bubble-selected {
        border: 4px solid #10b981;
        background: linear-gradient(135deg, #ffffff 0%, #ecfdf5 100%);
        box-shadow: 0 8px 20px rgba(16, 185, 129, 0.25);
        animation: gentle-pulse 2.5s ease-in-out infinite;
    }

    .viz-bubble.burst {
        animation: burst-explode 0.6s ease-out forwards;
    }

    @keyframes burst-explode {
        0% {
            transform: scale(1);
            opacity: 1;
            filter: brightness(1);
        }
        50% {
            transform: scale(1.3);
            opacity: 0.8;
            filter: brightness(1.3);
        }
        100% {
            transform: scale(0.3) rotate(360deg);
            opacity: 0;
            filter: brightness(0.5);
        }
    }

    @keyframes gentle-pulse {
        0%, 100% {
            transform: scale(1);
            box-shadow: 0 8px 20px rgba(16, 185, 129, 0.25);
        }
        50% {
            transform: scale(1.02);
            box-shadow: 0 10px 25px rgba(16, 185, 129, 0.3);
        }
    }

    .bubble-checkmark {
        position: absolute;
        top: -12px;
        right: -12px;
        background: #10b981;
        color: white;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
        font-weight: 900;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
        animation: check-pop 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
    }

    @keyframes check-pop {
        0% {
            transform: scale(0) rotate(-45deg);
            opacity: 0;
        }
        100% {
            transform: scale(1) rotate(0deg);
            opacity: 1;
        }
    }

    .bubble-category-name {
        font-size: 0.85em;
        font-weight: 700;
        margin-bottom: 6px;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        color: #475569;
        text-align: center;
        line-height: 1.2;
    }

    .bubble-amount {
        font-size: 1.5em;
        font-weight: 900;
        color: #0f172a;
        margin: 4px 0;
    }

    .bubble-percentage {
        font-size: 0.7em;
        color: #64748b;
        font-weight: 600;
    }

    .viz-bubble-selected .bubble-category-name {
        color: #047857;
    }

    .viz-bubble-selected .bubble-amount {
        color: #059669;
    }

    .viz-bubble-selected .bubble-percentage {
        color: #10b981;
    }
    </style>
    """

    # Display CSS
    st.markdown(css_styles, unsafe_allow_html=True)

    # Generate bubble HTML
    bubble_html = '<div class="bubble-viz-container">'

    for _, row in stats.iterrows():
        cat = row['categorie']
        amount = row['montant']
        pct = row['pct']
        is_selected = cat in selected

        # Calculate proportional size
        size = min_size + (amount / max_amount) * (max_size - min_size)
        font_base = size / 9  # Adaptive font sizing

        # Apply selection styling
        selected_class = 'viz-bubble-selected' if is_selected else ''
        checkmark_html = '<div class="bubble-checkmark">✓</div>' if is_selected else ''

        # Build HTML carefully without f-string issues
        bubble_html += '<div class="viz-bubble ' + selected_class + '" style="width: ' + str(size) + 'px; height: ' + str(size) + 'px;" title="' + cat + ': ' + str(amount) + '€">'
        bubble_html += checkmark_html
        bubble_html += '<div class="bubble-category-name" style="font-size: ' + str(font_base) + 'px;">' + cat + '</div>'
        bubble_html += '<div class="bubble-amount" style="font-size: ' + str(font_base * 1.6) + 'px;">' + str(int(amount)) + '€</div>'
        bubble_html += '<div class="bubble-percentage" style="font-size: ' + str(font_base * 0.9) + 'px;">' + str(pct) + '%</div>'
        bubble_html += '</div>'

    bubble_html += '</div>'

    # Display HTML
    st.markdown(bubble_html, unsafe_allow_html=True)

    # Help text
    st.caption("💡 **Visualisation proportionnelle** : Plus la bulle est grande, plus vous dépensez dans cette catégorie. Utilisez les boutons ci-dessous pour sélectionner.")


# ==============================
# 🫧 HIERARCHICAL BUBBLE SYSTEM
# ==============================

def _render_category_bubbles(stats: pd.DataFrame, df: pd.DataFrame) -> None:
    """
    Render interactive bubbles for category selection with drill-down navigation.
    Uses unified state management.

    Args:
        stats: Category statistics DataFrame
        df: Transaction DataFrame
    """
    # CSS for hierarchical bubbles with animations
    css_hierarchical = """
    <style>
    .hierarchical-bubble-container {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        align-items: center;
        gap: 40px;
        padding: 60px 40px;
        background: linear-gradient(135deg, #f8fafc 0%, #e0e7ff 100%);
        border-radius: 25px;
        margin: 20px 0;
        min-height: 400px;
        position: relative;
    }

    .h-bubble {
        border-radius: 50%;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        border: 4px solid #cbd5e0;
        background: #ffffff;
        color: #1e293b;
        font-weight: 700;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
        transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
        position: relative;
        cursor: pointer;
        animation: bubble-appear 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
    }

    @keyframes bubble-appear {
        0% {
            transform: scale(0) rotate(-180deg);
            opacity: 0;
        }
        100% {
            transform: scale(1) rotate(0deg);
            opacity: 1;
        }
    }

    .h-bubble:hover {
        transform: translateY(-15px) scale(1.1);
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.25);
        border-color: #3b82f6;
    }

    .h-bubble-clickable::after {
        content: '👆';
        position: absolute;
        bottom: -45px;
        left: 50%;
        transform: translateX(-50%);
        font-size: 24px;
        opacity: 0;
        transition: opacity 0.3s;
    }

    .h-bubble-clickable:hover::after {
        opacity: 1;
        animation: bounce 1s infinite;
    }

    @keyframes bounce {
        0%, 100% { transform: translateX(-50%) translateY(0); }
        50% { transform: translateX(-50%) translateY(-10px); }
    }

    .h-bubble.transition-in {
        animation: zoom-in 0.5s ease-out;
    }

    .h-bubble.transition-out {
        animation: zoom-out 0.5s ease-in forwards;
    }

    @keyframes zoom-in {
        0% {
            transform: scale(0) translateY(20px);
            opacity: 0;
        }
        100% {
            transform: scale(1) translateY(0);
            opacity: 1;
        }
    }

    @keyframes zoom-out {
        0% {
            transform: scale(1) translateY(0);
            opacity: 1;
        }
        100% {
            transform: scale(0) translateY(-20px);
            opacity: 0;
        }
    }
    </style>
    """

    st.markdown(css_hierarchical, unsafe_allow_html=True)

    if stats.empty:
        st.info("Aucune catégorie trouvée")
        return

    max_amount = stats['montant'].max()
    min_size = 100
    max_size = 250

    bubble_html = '<div class="hierarchical-bubble-container">'

    for _, row in stats.iterrows():
        cat = row['categorie']
        amount = row['montant']
        size = min_size + (amount / max_amount) * (max_size - min_size)

        bubble_html += '<div class="h-bubble h-bubble-clickable transition-in" style="width: ' + str(size) + 'px; height: ' + str(size) + 'px;" title="' + cat + '">'
        bubble_html += '<div style="font-size: ' + str(size/12) + 'px; font-weight: 700; text-transform: uppercase;">' + cat + '</div>'
        bubble_html += '<div style="font-size: ' + str(size/7) + 'px; font-weight: 900; margin: 8px 0;">' + str(int(amount)) + '€</div>'
        bubble_html += '<div style="font-size: ' + str(size/15) + 'px; color: #64748b;">→ Détails</div>'
        bubble_html += '</div>'

    bubble_html += '</div>'
    st.markdown(bubble_html, unsafe_allow_html=True)

    st.caption("💡 Cliquez sur une bulle pour voir les sous-catégories")

    # Interactive buttons for drill-down
    st.markdown("### 🖱️ Sélectionnez une catégorie pour détails")
    cols = st.columns(4)
    for idx, (_, row) in enumerate(stats.iterrows()):
        cat = row['categorie']
        with cols[idx % 4]:
            if st.button(f"📂 {cat}", key=f"drill_{cat}", use_container_width=True):
                st.session_state.current_parent = cat
                st.session_state.viz_mode = 'subcategories'
                st.rerun()


def _render_subcategory_bubbles(stats: pd.DataFrame, df: pd.DataFrame) -> None:
    """
    Render subcategory bubbles for selected parent category.

    Args:
        stats: Category statistics DataFrame
        df: Transaction DataFrame
    """
    parent = st.session_state.current_parent
    if not parent:
        st.error("Aucune catégorie parente sélectionnée")
        return

    # Filter for subcategories
    df_expenses = df[(df['type'] == 'dépense') & (df['categorie'] == parent)]
    if df_expenses.empty:
        st.info(f"Aucune sous-catégorie pour {parent}")
        return

    sub_stats = df_expenses.groupby('sous_categorie').agg({
        'montant': 'sum'
    }).reset_index().sort_values('montant', ascending=False)

    if sub_stats.empty:
        st.info("Aucune sous-catégorie trouvée")
        return

    # CSS for subcategory bubbles
    css_sub = """
    <style>
    .subcategory-bubble-container {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        align-items: center;
        gap: 30px;
        padding: 50px 30px;
        background: linear-gradient(135deg, #f1f5f9 0%, #e0f2fe 100%);
        border-radius: 20px;
        margin: 20px 0;
        min-height: 350px;
    }

    .sub-bubble {
        border-radius: 50%;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        border: 3px solid #7dd3fc;
        background: linear-gradient(135deg, #ffffff 0%, #f0f9ff 100%);
        color: #0c4a6e;
        font-weight: 600;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
        animation: bubble-appear 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
    }

    .sub-bubble:hover {
        transform: translateY(-10px) scale(1.08);
        box-shadow: 0 15px 35px rgba(3, 102, 214, 0.25);
        border-color: #0369a1;
        background: linear-gradient(135deg, #e0f2fe 0%, #cffafe 100%);
    }
    </style>
    """

    st.markdown(css_sub, unsafe_allow_html=True)

    max_amount = sub_stats['montant'].max()
    min_size = 80
    max_size = 200

    bubble_html = '<div class="subcategory-bubble-container">'

    for _, row in sub_stats.iterrows():
        subcat = row['sous_categorie']
        amount = row['montant']
        size = min_size + (amount / max_amount) * (max_size - min_size)

        bubble_html += '<div class="sub-bubble transition-in" style="width: ' + str(size) + 'px; height: ' + str(size) + 'px;" title="' + subcat + '">'
        bubble_html += '<div style="font-size: ' + str(size/10) + 'px; font-weight: 700; text-align: center;">' + subcat + '</div>'
        bubble_html += '<div style="font-size: ' + str(size/6) + 'px; font-weight: 900; margin: 6px 0; color: #0f172a;">' + str(int(amount)) + '€</div>'
        bubble_html += '</div>'

    bubble_html += '</div>'
    st.markdown(bubble_html, unsafe_allow_html=True)

    st.caption(f"💡 Sous-catégories de **{parent}**")


