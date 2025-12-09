"""
Streamlit Component Backend for Fractal Navigation.

Provides interactive Sierpinski triangle-based fractal visualization.
Uses HTML/Canvas with Streamlit's components.html()

@author: djabi
@version: 3.1 (Simplified - triangles + buttons)
@date: 2025-11-25
"""

import streamlit as st
import streamlit.components.v1 as components
import json
from typing import Dict, Any, Optional


def fractal_navigation(
    hierarchy: Dict[str, Any],
    key: Optional[str] = None,
    default: Optional[Dict[str, Any]] = None,
    show_canvas: bool = True
) -> None:
    """
    Render interactive Sierpinski triangle navigation.

    Displays triangles as a beautiful visual interface.
    Actual filtering/selection is handled via visible buttons below.

    Args:
        hierarchy: Complete fractal hierarchy from build_fractal_hierarchy()
        key: Unique key for this component instance
        default: Unused (kept for compatibility)
        show_canvas: Whether to display the canvas (default: True). Set to False to only show hidden buttons.
    """
    if not isinstance(hierarchy, dict):
        raise ValueError("hierarchy doit être un dictionnaire")

    if 'TR' not in hierarchy:
        raise ValueError("hierarchy doit contenir un nœud racine 'TR'")

    # Initialize session state
    if f'{key}_current_node' not in st.session_state:
        st.session_state[f'{key}_current_node'] = 'TR'
    if f'{key}_nav_stack' not in st.session_state:
        st.session_state[f'{key}_nav_stack'] = ['TR']

    current_node = st.session_state[f'{key}_current_node']
    nav_stack = st.session_state[f'{key}_nav_stack']

    # Get current node info
    node = hierarchy.get(current_node, {})
    children_codes = node.get('children', [])

    # Get selected codes from session state
    if 'fractal_selections' not in st.session_state:
        st.session_state.fractal_selections = set()
    selected_codes = st.session_state.fractal_selections

    # Render the triangle visualization (pure visual) - only if show_canvas is True
    if show_canvas:
        # Afficher le breadcrumb/chemin en haut avec navigation cliquable
        breadcrumb_cols = st.columns(len(nav_stack) * 2 - 1, gap="small")

        for idx, code in enumerate(nav_stack):
            breadcrumb_node = hierarchy.get(code, {})
            label = breadcrumb_node.get('label', code)

            # Afficher le label
            col_idx = idx * 2
            if col_idx < len(breadcrumb_cols):
                with breadcrumb_cols[col_idx]:
                    if st.button(label, key=f"{key}_breadcrumb_{idx}_{code}", use_container_width=True):
                        # Naviguer au niveau cliqué
                        new_nav_stack = nav_stack[:idx+1]
                        st.session_state[f'{key}_current_node'] = code
                        st.session_state[f'{key}_nav_stack'] = new_nav_stack
                        st.rerun()

            # Afficher le séparateur (sauf pour le dernier)
            if idx < len(nav_stack) - 1:
                sep_idx = idx * 2 + 1
                if sep_idx < len(breadcrumb_cols):
                    with breadcrumb_cols[sep_idx]:
                        st.write("→")

        # Create unique component key to avoid caching issues
        unique_component_key = f"{key}_{current_node}"
        # Convert to tuples for caching (hashable types)
        children_codes_tuple = tuple(children_codes)
        selected_codes_tuple = tuple(selected_codes) if selected_codes else None
        html_content = _build_fractal_html(hierarchy, current_node, children_codes_tuple, unique_component_key, selected_codes_tuple)
        component_response = components.html(html_content, height=900)

        st.markdown("---")

        # Gérer les réponses du component (clics normaux)
    else:
        component_response = None

    # Handle component responses (triangle clicks)
    if component_response:
        if isinstance(component_response, dict):
            if component_response.get('type') == 'triangle_click':
                clicked_code = component_response.get('code')
                clicked_label = component_response.get('label')

                if clicked_code:

                    # Trouver le nœud correspondant
                    clicked_node = hierarchy.get(clicked_code, {})
                    has_children = len(clicked_node.get('children', [])) > 0

                    if has_children:
                        # Navigation : zoomer dans cette catégorie
                        nav_stack.append(clicked_code)
                        st.session_state[f'{key}_current_node'] = clicked_code
                        st.session_state[f'{key}_nav_stack'] = nav_stack
                        st.rerun()
                    else:
                        # Sélection au dernier niveau : ajouter aux filtres
                        if 'fractal_selections' not in st.session_state:
                            st.session_state.fractal_selections = set()

                        if clicked_code in st.session_state.fractal_selections:
                            st.session_state.fractal_selections.discard(clicked_code)
                        else:
                            st.session_state.fractal_selections.add(clicked_code)

                        st.rerun()



@st.fragment
def render_hidden_buttons(hierarchy: Dict[str, Any], key: Optional[str] = None) -> None:
    """
    Render hidden buttons for JavaScript automation at the bottom of the page.
    
    Uses @st.fragment to isolate button rendering from main page updates,
    improving animation performance.

    These buttons must be in the DOM for JavaScript to discover and click them.
    They are rendered invisibly (hidden columns) to avoid taking up visual space.

    Args:
        hierarchy: Complete fractal hierarchy
        key: Unique key for this component instance (must match fractal_navigation key)
    """
    if not key:
        return

    # Get current state
    if f'{key}_current_node' not in st.session_state:
        current_node = 'TR'
    else:
        current_node = st.session_state[f'{key}_current_node']

    if f'{key}_nav_stack' not in st.session_state:
        nav_stack = ['TR']
    else:
        nav_stack = st.session_state[f'{key}_nav_stack']

    node = hierarchy.get(current_node, {})
    children_codes = node.get('children', [])

    # Add compact CSS for hidden buttons (invisible but still in DOM for JS)
    st.markdown("""
    <style>
        /* Cacher les boutons pour le fractal mais les garder dans le DOM */
        .fractal-hidden-buttons {
            position: absolute;
            left: -9999px;
            opacity: 0;
            pointer-events: none;
            height: 0;
            overflow: hidden;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Wrapper pour les boutons cachés (seront rendus hors écran mais cliquables par JS)
    st.markdown('<div class="fractal-hidden-buttons">', unsafe_allow_html=True)

    # Filter buttons (invisible to user, only for JavaScript automation)
    if current_node == 'TR':
        col1, col2 = st.columns(2)

        with col1:
            if st.button("➕ Ajouter le filtre Revenus", key=f"{key}_add_filter_revenus", use_container_width=True):
                if 'fractal_selections' not in st.session_state:
                    st.session_state.fractal_selections = set()
                if 'REVENUS' not in st.session_state.fractal_selections:
                    st.session_state.fractal_selections.add('REVENUS')
                st.rerun()
        with col2:
            if st.button("➕ Ajouter le filtre Dépenses", key=f"{key}_add_filter_depenses", use_container_width=True):
                if 'fractal_selections' not in st.session_state:
                    st.session_state.fractal_selections = set()
                if 'DEPENSES' not in st.session_state.fractal_selections:
                    st.session_state.fractal_selections.add('DEPENSES')
                st.rerun()

    # Navigation buttons for triangles
    if children_codes:
        for idx, child_code in enumerate(children_codes):
            child_node = hierarchy.get(child_code, {})
            child_label = child_node.get('label', child_code)
            child_total = child_node.get('amount') or child_node.get('total') or 0

            child_level = child_node.get('level', 0)
            sub_children = child_node.get('children', [])
            has_children = len(sub_children) > 0

            # Create button text
            if has_children:
                btn_text = f"📂 {child_label} ({child_total:,.0f}€)"
            else:
                btn_text = f"📋 {child_label} ({child_total:,.0f}€)"

            # Create unique key - use stable key independent of nav_stack for performance
            unique_key = f"{key}_nav_{child_code}_{idx}"

            # Invisible button for JavaScript to find and click
            if st.button(btn_text, key=unique_key, use_container_width=True):
                if has_children:
                    # Navigate deeper
                    nav_stack.append(child_code)
                    st.session_state[f'{key}_current_node'] = child_code
                    st.session_state[f'{key}_nav_stack'] = nav_stack
                    st.rerun()
                else:
                    # Leaf node: select for filtering
                    if 'fractal_selections' not in st.session_state:
                        st.session_state.fractal_selections = set()

                    if child_code in st.session_state.fractal_selections:
                        st.session_state.fractal_selections.discard(child_code)
                        st.rerun()
                    else:
                        if child_level == 3:
                            parent_code = child_node.get('parent', '')
                            if parent_code in st.session_state.fractal_selections:
                                st.warning(f"{child_label} est déjà incluse dans {hierarchy.get(parent_code, {}).get('label', parent_code)}")
                            else:
                                st.session_state.fractal_selections.add(child_code)
                                st.rerun()
                        else:
                            st.session_state.fractal_selections.add(child_code)
                            st.rerun()

            # Add filter toggle button for level 2 categories
            if child_level == 2 and has_children:
                if 'fractal_selections' not in st.session_state:
                    st.session_state.fractal_selections = set()

                is_selected = child_code in st.session_state.fractal_selections
                button_text = f"✕ Retirer le filtre '{child_label}'" if is_selected else f"➕ Ajouter le filtre '{child_label}'"
                add_filter_key = f"add_filter_{child_code}_{idx}"

                if st.button(button_text, key=add_filter_key, use_container_width=True):
                    if is_selected:
                        st.session_state.fractal_selections.discard(child_code)
                    else:
                        st.session_state.fractal_selections.add(child_code)
                    st.rerun()
    
    # Fermer le div des boutons cachés
    st.markdown('</div>', unsafe_allow_html=True)


def _get_category_emoji(label: str) -> str:
    """Get emoji for category label."""
    emoji_map = {
        # Types principaux
        'Revenus': '💼',
        'Dépenses': '🛒',

        # Catégories de revenus
        'Salaire': '💵',
        'Freelance': '🖥️',
        'Investissement': '📈',
        'Autres revenus': '💰',

        # Catégories de dépenses
        'Alimentation': '🍔',
        'Supermarché': '🛒',
        'Restaurant': '🍽️',
        'Boulangerie': '🥖',

        'Transport': '🚗',
        'Autoroute': '🛣️',
        'Essence': '⛽',
        'Stationnement': '🅿️',

        'Logement': '🏠',
        'Loyer': '🏠',

        'Santé': '⚕️',
        'Loisirs': '🎮',

        'Factures': '📄',
        'Abonnement': '📱',

        'Vêtements': '👕',
        'Education': '📚',
        'Uca': '🎓',

        'Banque': '🏦',
        'Assurance': '🛡️',

        'Divers': '📦'
    }

    return emoji_map.get(label, '📁')


def _get_category_color(label: str) -> str:
    """Get color for category label - restore original colors."""
    color_map = {
        # Jaune/Orange
        'Stationnement': '#fbbf24',
        'Autoroute': '#fbbf24',
        'Boulangerie': '#fbbf24',
        'Banque': '#fbbf24',
        'Essence': '#fbbf24',
        'Restaurant': '#fbbf24',
        'Uca': '#fbbf24',
        'Alimentation': '#fbbf24',
        'Supermarché': '#fbbf24',
        'Loyer': '#fbbf24',
        'Logement': '#fbbf24',

        # Violet/Magenta pour Transport
        'Transport': '#a855f7',
        'Autoroute': '#a855f7',

        # Vert/Teal/Cyan pour Assurance et Divers
        'Assurance': '#06b6d4',
        'Divers': '#06b6d4',

        # Roses pour certaines catégories
        'Santé': '#ec4899',
        'Loisirs': '#f43f5e',
        'Vêtements': '#f43f5e',
        'Education': '#ec4899',

        # Bleu pour Revenus/Factures
        'Revenus': '#3b82f6',
        'Dépenses': '#f59e0b',
        'Factures': '#06b6d4',
        'Abonnement': '#06b6d4',
        'Freelance': '#3b82f6',
        'Salaire': '#f59e0b',
        'Investissement': '#10b981'
    }

    # Retourner la couleur, sinon jaune par défaut
    return color_map.get(label, '#fbbf24')


@st.cache_data(show_spinner=False)
def _build_fractal_html(
    hierarchy: Dict[str, Any],
    current_node: str,
    children_codes: tuple,  # Changed from list to tuple for hashability
    component_key: str,
    selected_codes: tuple = None  # Changed from set to tuple for hashability
) -> str:
    """Build HTML/CSS/JS for fractal visualization (visual only).
    
    Cached to avoid regenerating HTML on every render, improving performance.
    """

    if not children_codes:
        return "<p style='color: #94a3b8; text-align: center; padding: 20px;'>Aucune sous-catégorie</p>"

    # Convert tuple back to set for processing
    if selected_codes is None:
        selected_codes = set()
    else:
        selected_codes = set(selected_codes)

    # Prepare children data
    children_data = {}
    for child_code in children_codes:
        child_node = hierarchy.get(child_code, {})
        label = child_node.get('label', child_code)
        children_data[child_code] = {
            'label': label,
            'emoji': _get_category_emoji(label),
            'color': _get_category_color(label),
            'amount': child_node.get('amount') or child_node.get('total') or 0,
            'has_children': len(child_node.get('children', [])) > 0,
            'level': child_node.get('level', 0),  # Ajouter le niveau pour adapter le long-click
        }

    # Generate positions
    num_children = len(children_codes)
    positions = _get_triangle_positions(num_children, 550, 550)

    # Generate button keys for reference
    button_key_map = {}
    nav_stack_str = '_'.join(['TR'] + [current_node]) if current_node != 'TR' else 'TR'
    for idx, child_code in enumerate(children_codes):
        button_key_map[child_code] = f"{component_key}_nav_{nav_stack_str}_{idx}_{child_code}"

    # Convert selected_codes set to list for JSON serialization
    selected_codes_list = list(selected_codes) if selected_codes else []

    return f"""
    <style>
        body, html {{ width: 100%; height: 100%; margin: 0; padding: 0; }}
        #fractal-canvas-{component_key} {{ display: block; width: 100%; height: 100%; }}
    </style>

    <canvas id="fractal-canvas-{component_key}"></canvas>

    <script>
    (function() {{
        const KEY = '{component_key}';
        const CHILDREN_DATA = {json.dumps(children_data)};
        const CHILDREN_CODES = {json.dumps(children_codes)};
        const POSITIONS = {json.dumps(positions)};
        const SELECTED_CODES_FROM_PYTHON = {json.dumps(selected_codes_list)};
        const BUTTON_KEY_MAP = {json.dumps(button_key_map)};

        // Importer Streamlit pour communication - essayer plusieurs chemins
        let Streamlit = null;
        try {{
            // Essai 1: window.parent.Streamlit (ancienne méthode)
            if (window.parent && window.parent.Streamlit) {{
                Streamlit = window.parent.Streamlit;
            }}
            // Essai 2: window.top.Streamlit
            else if (window.top && window.top.Streamlit) {{
                Streamlit = window.top.Streamlit;
            }}
            // Essai 3: Chercher dans les frames
            else if (window.frames && window.frames.length > 0) {{
                for (let i = 0; i < window.frames.length; i++) {{
                    if (window.frames[i].Streamlit) {{
                        Streamlit = window.frames[i].Streamlit;
                        break;
                    }}
                }}
            }}
            // Essai 4: Chercher dans parent.parent
            else if (window.parent && window.parent.parent && window.parent.parent.Streamlit) {{
                Streamlit = window.parent.parent.Streamlit;
            }}
        }} catch (e) {{
            console.warn('Erreur accès Streamlit:', e.message);
        }}

        console.log('Streamlit disponible?', !!Streamlit);

        const canvas = document.getElementById('fractal-canvas-' + KEY);
        if (!canvas) return;

        const ctx = canvas.getContext('2d', {{ antialias: 'true' }});
        canvas.width = canvas.parentElement.clientWidth;
        canvas.height = canvas.parentElement.clientHeight;

        const centerX = canvas.width / 2;
        const centerY = canvas.height / 2;
        let hoveredIdx = null;
        let heldTriangleIdx = null;
        let longClickTimer = null;
        let mouseDownTime = null;
        const longClickDuration = 1500; // 1.5 secondes
        const triangles = [];

        // Utiliser directement les codes sélectionnés passés par Python
        let selectedCodes = new Set(SELECTED_CODES_FROM_PYTHON);
        console.log('Codes sélectionnés depuis Python:', Array.from(selectedCodes));

        function drawTriangle(x, y, size, data, isHovered, isHeld, isSelected) {{
            // Gradient principal avec direction verticale - utiliser la couleur de la catégorie
            const grad = ctx.createLinearGradient(x, y - size - 5, x, y + size + 5);

            if (isHeld) {{
                // Long-click held: version brillante et saturée (vert)
                grad.addColorStop(0, '#10b981');
                grad.addColorStop(0.5, '#059669');
                grad.addColorStop(1, '#047857');
            }} else if (isSelected) {{
                // Item sélectionné: reste vert
                grad.addColorStop(0, '#10b981');
                grad.addColorStop(0.5, '#059669');
                grad.addColorStop(1, '#047857');
            }} else if (isHovered) {{
                // Hover: version plus claire et saturée de la couleur
                const baseColor = data.color || '#fbbf24';
                grad.addColorStop(0, baseColor);
                grad.addColorStop(0.5, '#f472b6');
                grad.addColorStop(1, '#ec4899');
            }} else {{
                // Normal: gradient basé sur la couleur de la catégorie
                const baseColor = data.color || '#fbbf24';
                // Créer un gradient avec nuances de la couleur
                grad.addColorStop(0, baseColor);
                grad.addColorStop(0.5, baseColor);
                grad.addColorStop(1, 'rgba(0, 0, 0, 0.2)');
            }}

            // Draw triangle fill
            ctx.fillStyle = grad;
            ctx.beginPath();
            ctx.moveTo(x, y - size);
            ctx.lineTo(x - size, y + size);
            ctx.lineTo(x + size, y + size);
            ctx.closePath();
            ctx.fill();

            // Draw border avec effet plus prononcé
            if (isHeld) {{
                // Border glow effect on long-click held (vert)
                ctx.strokeStyle = 'rgba(16, 185, 129, 0.9)';
                ctx.lineWidth = 5;
                ctx.beginPath();
                ctx.moveTo(x, y - size);
                ctx.lineTo(x - size, y + size);
                ctx.lineTo(x + size, y + size);
                ctx.closePath();
                ctx.stroke();

                // Inner border - vert bright
                ctx.strokeStyle = '#34d399';
                ctx.lineWidth = 2;
            }} else if (isSelected) {{
                // Border pour item sélectionné (vert mais moins épais)
                ctx.strokeStyle = 'rgba(16, 185, 129, 0.7)';
                ctx.lineWidth = 3;
                ctx.beginPath();
                ctx.moveTo(x, y - size);
                ctx.lineTo(x - size, y + size);
                ctx.lineTo(x + size, y + size);
                ctx.closePath();
                ctx.stroke();

                // Inner border - vert
                ctx.strokeStyle = '#34d399';
                ctx.lineWidth = 1.5;
            }} else if (isHovered) {{
                // Border glow effect on hover
                ctx.strokeStyle = 'rgba(244, 63, 94, 0.8)';
                ctx.lineWidth = 4;
                ctx.beginPath();
                ctx.moveTo(x, y - size);
                ctx.lineTo(x - size, y + size);
                ctx.lineTo(x + size, y + size);
                ctx.closePath();
                ctx.stroke();

                // Inner border
                ctx.strokeStyle = '#f43f5e';
                ctx.lineWidth = 2;
            }} else {{
                ctx.strokeStyle = 'rgba(255, 255, 255, 0.4)';
                ctx.lineWidth = 2;
            }}

            ctx.beginPath();
            ctx.moveTo(x, y - size);
            ctx.lineTo(x - size, y + size);
            ctx.lineTo(x + size, y + size);
            ctx.closePath();
            ctx.stroke();

            // Text setup
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';

            // Positionnement adaptatif basé sur la taille du triangle
            const emojiOffset = size * 0.35;
            const labelOffset = size * 0.0;
            const amountOffset = size * 0.45;

            // 1. Emoji (en haut) - taille augmentée
            const emojiFontSize = size > 50 ? 32 : 28;
            ctx.font = emojiFontSize + 'px sans-serif';
            ctx.fillStyle = 'rgba(255, 255, 255, 0.95)';
            ctx.fillText(data.emoji, x, y - emojiOffset);

            // 2. Label (au milieu) - taille plus grande et lisible
            const labelFontSize = size > 50 ? 14 : 12;
            ctx.font = 'bold ' + labelFontSize + 'px Inter';

            // Shadow plus prononcé pour meilleur contraste
            ctx.fillStyle = 'rgba(0, 0, 0, 0.6)';
            ctx.fillText(data.label.substring(0, 14), x + 1, y + labelOffset + 3.5);
            ctx.fillText(data.label.substring(0, 14), x - 1, y + labelOffset + 3.5);
            ctx.fillText(data.label.substring(0, 14), x, y + labelOffset + 4.5);

            // Text principal blanc
            ctx.fillStyle = '#ffffff';
            ctx.fillText(data.label.substring(0, 14), x, y + labelOffset + 3);

            // 3. Montant (en bas) avec cyan vibrant - taille augmentée
            const amountFontSize = size > 50 ? 13 : 11;
            ctx.font = 'bold ' + amountFontSize + 'px Inter';
            const amt = new Intl.NumberFormat('fr-FR', {{
                style: 'currency',
                currency: 'EUR',
                minimumFractionDigits: 0
            }}).format(Math.abs(data.amount));

            // Shadow sombre pour le montant
            ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
            ctx.fillText(amt, x + 1, y + amountOffset + 3.5);
            ctx.fillText(amt, x - 1, y + amountOffset + 3.5);
            ctx.fillText(amt, x, y + amountOffset + 4.5);

            // Montant cyan vibrant
            ctx.fillStyle = '#22d3ee';
            ctx.fillText(amt, x, y + amountOffset + 3);
        }}

        function render() {{
            // Background gradient
            const grad = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
            grad.addColorStop(0, '#0a0e27');
            grad.addColorStop(1, '#1a1f3a');
            ctx.fillStyle = grad;
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            // Draw triangles
            CHILDREN_CODES.forEach((code, idx) => {{
                const pos = POSITIONS[idx];
                const x = centerX + pos.x;
                const y = centerY + pos.y;
                const size = pos.size;
                const data = CHILDREN_DATA[code];
                const isHovered = hoveredIdx === idx;
                const isHeld = heldTriangleIdx === idx;
                const isSelected = selectedCodes.has(code);

                drawTriangle(x, y, size, data, isHovered, isHeld, isSelected);
            }});
        }}

        function isInTriangle(px, py, x, y, size) {{
            const p1 = {{ x: x, y: y - size }};
            const p2 = {{ x: x - size, y: y + size }};
            const p3 = {{ x: x + size, y: y + size }};

            const denom = (p2.y - p3.y) * (p1.x - p3.x) + (p3.x - p2.x) * (p1.y - p3.y);
            if (denom === 0) return false;

            const a = ((p2.y - p3.y) * (px - p3.x) + (p3.x - p2.x) * (py - p3.y)) / denom;
            const b = ((p3.y - p1.y) * (px - p3.x) + (p1.x - p3.x) * (py - p3.y)) / denom;
            const c = 1 - a - b;

            return a >= 0 && b >= 0 && c >= 0;
        }}

        canvas.addEventListener('mousemove', (e) => {{
            const rect = canvas.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            let found = -1;
            CHILDREN_CODES.forEach((code, idx) => {{
                const pos = POSITIONS[idx];
                const tx = centerX + pos.x;
                const ty = centerY + pos.y;
                if (isInTriangle(x, y, tx, ty, pos.size)) {{
                    found = idx;
                }}
            }});

            if (found !== hoveredIdx) {{
                hoveredIdx = found;
                canvas.style.cursor = found >= 0 ? 'pointer' : 'default';
                render();
            }}
        }});

        canvas.addEventListener('mouseleave', () => {{
            hoveredIdx = null;
            if (heldTriangleIdx !== null) {{
                // Annuler le long-click si la souris quitte le canvas
                clearTimeout(longClickTimer);
                heldTriangleIdx = null;
            }}
            canvas.style.cursor = 'default';
            render();
        }});

        // Long-click detection: mousedown starts the timer
        canvas.addEventListener('mousedown', (e) => {{
            const rect = canvas.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            let pressedIdx = -1;
            CHILDREN_CODES.forEach((code, idx) => {{
                const pos = POSITIONS[idx];
                const tx = centerX + pos.x;
                const ty = centerY + pos.y;
                if (isInTriangle(x, y, tx, ty, pos.size)) {{
                    pressedIdx = idx;
                }}
            }});

            // Si on appuie sur un triangle, démarrer le timer
            if (pressedIdx >= 0) {{
                mouseDownTime = Date.now();
                heldTriangleIdx = pressedIdx;

                // Déterminer la durée selon le niveau
                const heldCode = CHILDREN_CODES[pressedIdx];
                const heldLevel = CHILDREN_DATA[heldCode].level;
                const clickDuration = 1000; // 1s pour tous les niveaux

                longClickTimer = setTimeout(() => {{
                    // Timer écoulé: long-click activé
                    const heldCode = CHILDREN_CODES[heldTriangleIdx];
                    const heldLabel = CHILDREN_DATA[heldCode].label;
                    const heldLevel = CHILDREN_DATA[heldCode].level;

                    const durMsg = '1s';
                    console.log('⏱️ Long-click détecté (' + durMsg + '):', heldLabel);
                    console.log('📋 Clic long-click sur bouton:', heldLabel);

                    // Chercher le bouton approprié selon le niveau
                    try {{
                        let button = null;
                        let parentDoc = window.parent.document;
                        const allButtons = parentDoc.querySelectorAll('button');

                        // Niveau 1: Chercher bouton "Ajouter le filtre" pour le type
                        if (heldLevel === 1) {{
                            for (let btn of allButtons) {{
                                const btnText = (btn.innerText || btn.textContent || '').trim();
                                // Format: "➕ Ajouter le filtre Revenus" ou "➕ Ajouter le filtre Dépenses"
                                if ((heldLabel === 'Revenus' && btnText.includes('Ajouter le filtre Revenus')) ||
                                    (heldLabel === 'Dépenses' && btnText.includes('Ajouter le filtre Dépenses'))) {{
                                    button = btn;
                                    break;
                                }}
                            }}
                        }} else {{
                            // Niveau 2+: Chercher bouton "Ajouter le filtre" OU "Retirer le filtre" avec ce label
                            for (let btn of allButtons) {{
                                const btnText = (btn.innerText || btn.textContent || '').trim();
                                if ((btnText.includes('Ajouter le filtre') || btnText.includes('Retirer le filtre')) && btnText.includes(heldLabel)) {{
                                    button = btn;
                                    break;
                                }}
                            }}
                        }}

                        if (button) {{
                            console.log('✅ Bouton trouvé pour:', heldLabel);
                            button.click();
                            // Rafraîchir pour afficher la couleur verte
                            setTimeout(() => {{
                                render();
                            }}, 100);
                        }} else {{
                            console.warn('⚠️ Bouton NON trouvé pour:', heldLabel, '(niveau', heldLevel + ')');
                        }}
                    }} catch (e) {{
                        console.error('❌ Erreur lors du long-click:', e.message);
                    }}
                }}, clickDuration);

                render();
            }}
        }});

        // Mouseup: cancel long-click if released before timer completes (normal click)
        canvas.addEventListener('mouseup', (e) => {{
            if (longClickTimer) {{
                clearTimeout(longClickTimer);
                longClickTimer = null;

                // Si le long-click n'a pas complété, faire un clic normal
                const elapsedTime = Date.now() - mouseDownTime;
                if (heldTriangleIdx >= 0) {{
                    // Clic normal: cliquer le bouton Streamlit
                    const clickedIdx = heldTriangleIdx;
                    const clickedCode = CHILDREN_CODES[clickedIdx];
                    const clickedLabel = CHILDREN_DATA[clickedCode].label;

                    console.log('✅ Triangle cliqué (clic normal):', clickedLabel, '(Code:', clickedCode, ')');

                    try {{
                        let button = null;
                        let parentDoc = window.parent.document;
                        const allButtons = parentDoc.querySelectorAll('button');

                        // Chercher le bouton avec une correspondance plus précise
                        // Utiliser le code comme clé plutôt que le texte
                        const expectedKey = BUTTON_KEY_MAP[clickedCode];
                        if (expectedKey) {{
                            for (let btn of allButtons) {{
                                if (btn.getAttribute('data-testid') === 'hidden-nav-button' ||
                                    btn.getAttribute('data-testid') === 'hidden-filter-button') {{
                                    // Vérifier si c'est le bon bouton en utilisant la clé
                                    if (btn.id === expectedKey || btn.getAttribute('data-key') === expectedKey) {{
                                        button = btn;
                                        break;
                                    }}
                                }}
                            }}
                        }}

                        // Fallback: si on n'a pas trouvé par clé, chercher par texte avec correspondance exacte
                        if (!button) {{
                            for (let btn of allButtons) {{
                                const btnText = (btn.innerText || btn.textContent || '').trim();
                                // Correspondance plus stricte: commencer avec l'emoji et le label exact
                                // Format: "📂 Novembre (montant€)" ou "📋 Novembre (montant€)"
                                if (btnText.startsWith('📂 ' + clickedLabel + ' (') ||
                                    btnText.startsWith('📋 ' + clickedLabel + ' (')) {{
                                    button = btn;
                                    break;
                                }}
                            }}
                        }}

                        if (button) {{
                            console.log('🖱️ Clic sur le bouton:', clickedLabel);
                            button.click();
                        }} else {{
                            console.warn('⚠️ Bouton non trouvé pour:', clickedLabel);
                        }}
                    }} catch (e) {{
                        console.error('❌ Erreur lors du clic:', e.message);
                    }}
                }}
            }}

            heldTriangleIdx = null;
            render();
        }});

        render();
    }})();
    </script>
    """


def _get_triangle_positions(num_children: int, canvas_width: int, canvas_height: int) -> list:
    """Generate triangle positions based on number of children."""
    import math

    positions = []

    if num_children == 1:
        base_size = 75
        positions.append({'x': 0, 'y': 0, 'size': base_size})
    elif num_children == 2:
        base_size = 75
        spacing = 130
        positions.append({'x': -spacing, 'y': 0, 'size': base_size})
        positions.append({'x': spacing, 'y': 0, 'size': base_size})
    elif num_children == 3:
        base_size = 75
        positions.append({'x': 0, 'y': -100, 'size': base_size})
        positions.append({'x': -100, 'y': 80, 'size': base_size})
        positions.append({'x': 100, 'y': 80, 'size': base_size})
    elif num_children == 4:
        base_size = 75
        spacing = 130
        positions.append({'x': 0, 'y': -spacing, 'size': base_size})
        positions.append({'x': spacing, 'y': 0, 'size': base_size})
        positions.append({'x': 0, 'y': spacing, 'size': base_size})
        positions.append({'x': -spacing, 'y': 0, 'size': base_size})
    else:
        # Pour 5+ catégories, adapter taille et rayon
        # Taille réduite adaptée au nombre de catégories
        base_size = max(45, 75 - (num_children * 1.5))

        # Rayon adaptatif : AUGMENTÉ pour utiliser plus d'espace
        # Formule: radius = 160 + (num_children * 10)
        # Pour 11 catégories : radius = 160 + 110 = 270px (plus d'espace)
        # Pour 7 catégories : radius = 160 + 70 = 230px
        # Pour 5 catégories : radius = 160 + 50 = 210px
        radius = 160 + (num_children * 10)

        angle_step = 2 * math.pi / num_children
        for i in range(num_children):
            angle = (i * angle_step) - (math.pi / 2)
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            positions.append({'x': x, 'y': y, 'size': base_size})

    return positions
