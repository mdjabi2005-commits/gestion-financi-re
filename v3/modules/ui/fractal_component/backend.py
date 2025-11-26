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
    default: Optional[Dict[str, Any]] = None
) -> None:
    """
    Render interactive Sierpinski triangle navigation.

    Displays triangles as a beautiful visual interface.
    Actual filtering/selection is handled via visible buttons below.

    Args:
        hierarchy: Complete fractal hierarchy from build_fractal_hierarchy()
        key: Unique key for this component instance
        default: Unused (kept for compatibility)
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

    # Render the triangle visualization (pure visual)
    html_content = _build_fractal_html(hierarchy, current_node, children_codes, key)
    components.html(html_content, height=650)

    st.markdown("---")

    # Navigation buttons
    col1, col2 = st.columns([1, 1])
    with col1:
        if len(nav_stack) > 1:
            nav_depth = '_'.join(nav_stack)
            if st.button("← Retour", key=f"{key}_back_{nav_depth}", use_container_width=True):
                nav_stack.pop()
                st.session_state[f'{key}_current_node'] = nav_stack[-1]
                st.session_state[f'{key}_nav_stack'] = nav_stack
                st.rerun()

    with col2:
        if current_node != 'TR':
            nav_depth = '_'.join(nav_stack)
            if st.button("🏠 Vue d'ensemble", key=f"{key}_reset_{nav_depth}", use_container_width=True):
                st.session_state[f'{key}_current_node'] = 'TR'
                st.session_state[f'{key}_nav_stack'] = ['TR']
                st.rerun()

    st.markdown("---")

    # Selection buttons (visible, functional)
    if children_codes:
        st.markdown("**Sous-niveaux:**")

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

            # Create unique key
            unique_key = f"{key}_nav_{'_'.join(nav_stack)}_{idx}_{child_code}"

            # Button to navigate or select
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

            # Add filter button for categories
            child_level = child_node.get('level', 0)
            if child_level == 2 and has_children:
                nav_depth = '_'.join(nav_stack)
                add_filter_key = f"add_filter_{nav_depth}_{idx}_{child_code}"
                if st.button(f"➕ Ajouter le filtre '{child_label}'", key=add_filter_key, use_container_width=True):
                    if 'fractal_selections' not in st.session_state:
                        st.session_state.fractal_selections = set()

                    if child_code in st.session_state.fractal_selections:
                        st.warning(f"{child_label} est déjà sélectionnée")
                    else:
                        st.session_state.fractal_selections.add(child_code)
                        st.rerun()


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


def _build_fractal_html(
    hierarchy: Dict[str, Any],
    current_node: str,
    children_codes: list,
    component_key: str
) -> str:
    """Build HTML/CSS/JS for fractal visualization (visual only)."""

    if not children_codes:
        return "<p style='color: #94a3b8; text-align: center; padding: 20px;'>Aucune sous-catégorie</p>"

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
        }

    # Generate positions
    num_children = len(children_codes)
    positions = _get_triangle_positions(num_children, 400, 400)

    # Generate button keys for reference
    button_key_map = {}
    nav_stack_str = '_'.join(['TR'] + [current_node]) if current_node != 'TR' else 'TR'
    for idx, child_code in enumerate(children_codes):
        button_key_map[child_code] = f"{component_key}_nav_{nav_stack_str}_{idx}_{child_code}"

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
        const BUTTON_KEY_MAP = {json.dumps(button_key_map)};

        // Importer Streamlit pour communication
        let Streamlit;
        try {{
            Streamlit = window.parent.Streamlit;
        }} catch (e) {{
            console.warn('Streamlit not available in this context');
        }}

        const canvas = document.getElementById('fractal-canvas-' + KEY);
        if (!canvas) return;

        const ctx = canvas.getContext('2d', {{ antialias: 'true' }});
        canvas.width = canvas.parentElement.clientWidth;
        canvas.height = canvas.parentElement.clientHeight;

        const centerX = canvas.width / 2;
        const centerY = canvas.height / 2;
        let hoveredIdx = null;
        const triangles = [];

        function drawTriangle(x, y, size, data, isHovered) {{
            // Gradient principal avec direction verticale - utiliser la couleur de la catégorie
            const grad = ctx.createLinearGradient(x, y - size - 5, x, y + size + 5);

            if (isHovered) {{
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
            if (isHovered) {{
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

                drawTriangle(x, y, size, data, isHovered);
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
            canvas.style.cursor = 'default';
            render();
        }});

        canvas.addEventListener('click', (e) => {{
            const rect = canvas.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            let clickedIdx = -1;
            CHILDREN_CODES.forEach((code, idx) => {{
                const pos = POSITIONS[idx];
                const tx = centerX + pos.x;
                const ty = centerY + pos.y;
                if (isInTriangle(x, y, tx, ty, pos.size)) {{
                    clickedIdx = idx;
                }}
            }});

            // Si un triangle a été cliqué, chercher et cliquer le bouton correspondant
            if (clickedIdx >= 0) {{
                const clickedCode = CHILDREN_CODES[clickedIdx];
                const clickedLabel = CHILDREN_DATA[clickedCode].label;
                const clickedData = CHILDREN_DATA[clickedCode];

                console.log('Triangle cliqué:', clickedLabel, '| Index:', clickedIdx);

                // Attendre un peu pour laisser le DOM se stabiliser
                setTimeout(() => {{
                    // Chercher le bouton par son texte visible (approche 1)
                    let button = null;
                    const allButtons = document.querySelectorAll('button');

                    for (let btn of allButtons) {{
                        const btnText = (btn.innerText || btn.textContent || '').trim();
                        // Chercher une correspondance partielle du label
                        if (btnText.includes(clickedLabel)) {{
                            button = btn;
                            console.log('Bouton trouvé par texte:', btnText);
                            break;
                        }}
                    }}

                    // Approche 2: Si pas trouvé, chercher par position (le clickedIdx-ème bouton)
                    if (!button && allButtons.length > clickedIdx) {{
                        button = allButtons[clickedIdx + 6]; // +6 car les premiers boutons sont Back/Reset
                        console.log('Bouton trouvé par index alternatif');
                    }}

                    // Approche 3: chercher le premier bouton après la canvas (logique Streamlit)
                    if (!button) {{
                        const canvasContainer = canvas.closest('[data-testid="stVerticalBlock"]') || canvas.parentElement;
                        if (canvasContainer) {{
                            const buttons = canvasContainer.parentElement.querySelectorAll('button');
                            if (buttons.length > clickedIdx) {{
                                button = buttons[clickedIdx];
                                console.log('Bouton trouvé dans conteneur parent');
                            }}
                        }}
                    }}

                    // Cliquer le bouton si trouvé
                    if (button) {{
                        console.log('✅ Clic sur le bouton pour:', clickedLabel);
                        button.click();
                        // Force un petit délai pour Streamlit
                        setTimeout(() => {{}}, 100);
                    }} else {{
                        console.error('❌ Bouton NON trouvé pour:', clickedLabel);
                        console.log('Total boutons dans la page:', allButtons.length);
                    }}
                }}, 50);
            }}
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
        base_size = 55
        positions.append({'x': 0, 'y': 0, 'size': base_size})
    elif num_children == 2:
        base_size = 55
        spacing = 100
        positions.append({'x': -spacing, 'y': 0, 'size': base_size})
        positions.append({'x': spacing, 'y': 0, 'size': base_size})
    elif num_children == 3:
        base_size = 55
        positions.append({'x': 0, 'y': -80, 'size': base_size})
        positions.append({'x': -80, 'y': 60, 'size': base_size})
        positions.append({'x': 80, 'y': 60, 'size': base_size})
    elif num_children == 4:
        base_size = 55
        spacing = 100
        positions.append({'x': 0, 'y': -spacing, 'size': base_size})
        positions.append({'x': spacing, 'y': 0, 'size': base_size})
        positions.append({'x': 0, 'y': spacing, 'size': base_size})
        positions.append({'x': -spacing, 'y': 0, 'size': base_size})
    else:
        # Pour 5+ catégories, adapter taille et rayon
        # Taille réduite adaptée au nombre de catégories
        base_size = max(35, 60 - (num_children * 1.5))

        # Rayon adaptatif : AUGMENTÉ pour utiliser plus d'espace
        # Formule: radius = 140 + (num_children * 8)
        # Pour 11 catégories : radius = 140 + 88 = 228px (remplissage meilleur)
        # Pour 7 catégories : radius = 140 + 56 = 196px
        # Pour 5 catégories : radius = 140 + 40 = 180px
        radius = 140 + (num_children * 8)

        angle_step = 2 * math.pi / num_children
        for i in range(num_children):
            angle = (i * angle_step) - (math.pi / 2)
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            positions.append({'x': x, 'y': y, 'size': base_size})

    return positions
