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
            // Gradient principal avec direction verticale pour meilleur relief
            const grad = ctx.createLinearGradient(x, y - size - 5, x, y + size + 5);

            if (isHovered) {{
                // Hover: magenta vibrant avec plus de couleur
                grad.addColorStop(0, '#f472b6');
                grad.addColorStop(0.5, '#ec4899');
                grad.addColorStop(1, '#be185d');
            }} else {{
                // Normal: orange/gold avec profondeur
                grad.addColorStop(0, '#fbbf24');
                grad.addColorStop(0.5, '#f59e0b');
                grad.addColorStop(1, '#d97706');
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
                ctx.strokeStyle = 'rgba(59, 130, 246, 0.6)';
                ctx.lineWidth = 4;
                ctx.beginPath();
                ctx.moveTo(x, y - size);
                ctx.lineTo(x - size, y + size);
                ctx.lineTo(x + size, y + size);
                ctx.closePath();
                ctx.stroke();

                // Inner border
                ctx.strokeStyle = '#3b82f6';
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

            // 1. Emoji (en haut)
            ctx.font = '24px sans-serif';
            ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
            ctx.fillText(data.emoji, x, y - 12);

            // 2. Label (au milieu)
            ctx.font = 'bold 12px Inter';
            ctx.fillStyle = 'rgba(0, 0, 0, 0.3)';
            ctx.fillText(data.label.substring(0, 14), x + 0.5, y + 2.5);
            ctx.fillStyle = '#ffffff';
            ctx.fillText(data.label.substring(0, 14), x, y + 2);

            // 3. Montant (en bas) avec cyan vibrant
            ctx.fillStyle = 'rgba(0, 0, 0, 0.3)';
            ctx.font = 'bold 11px Inter';
            const amt = new Intl.NumberFormat('fr-FR', {{
                style: 'currency',
                currency: 'EUR',
                minimumFractionDigits: 0
            }}).format(Math.abs(data.amount));
            ctx.fillText(amt, x + 0.5, y + 13.5);
            ctx.fillStyle = '#22d3ee';
            ctx.fillText(amt, x, y + 13);
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

        render();
    }})();
    </script>
    """


def _get_triangle_positions(num_children: int, canvas_width: int, canvas_height: int) -> list:
    """Generate triangle positions based on number of children."""
    import math

    positions = []
    base_size = 55

    if num_children == 1:
        positions.append({'x': 0, 'y': 0, 'size': base_size})
    elif num_children == 2:
        spacing = 100
        positions.append({'x': -spacing, 'y': 0, 'size': base_size})
        positions.append({'x': spacing, 'y': 0, 'size': base_size})
    elif num_children == 3:
        positions.append({'x': 0, 'y': -80, 'size': base_size})
        positions.append({'x': -80, 'y': 60, 'size': base_size})
        positions.append({'x': 80, 'y': 60, 'size': base_size})
    elif num_children == 4:
        spacing = 100
        positions.append({'x': 0, 'y': -spacing, 'size': base_size})
        positions.append({'x': spacing, 'y': 0, 'size': base_size})
        positions.append({'x': 0, 'y': spacing, 'size': base_size})
        positions.append({'x': -spacing, 'y': 0, 'size': base_size})
    else:
        radius = 130 if num_children <= 6 else 140
        angle_step = 2 * math.pi / num_children
        for i in range(num_children):
            angle = (i * angle_step) - (math.pi / 2)
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            positions.append({'x': x, 'y': y, 'size': base_size})

    return positions
