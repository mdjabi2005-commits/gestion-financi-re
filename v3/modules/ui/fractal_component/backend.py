"""
Streamlit Component Backend for Fractal Navigation.

Provides interactive Sierpinski triangle-based fractal visualization.
Uses HTML/Canvas with Streamlit's components.html()

@author: djabi
@version: 2.0
@date: 2025-11-23
"""

import streamlit as st
import streamlit.components.v1 as components
import logging
from typing import Dict, Any, Optional
import os
import json

logger = logging.getLogger(__name__)

# Get the directory where this component is located
_COMPONENT_DIR = os.path.dirname(os.path.abspath(__file__))


def fractal_navigation(
    data: Dict[str, Any],
    key: Optional[str] = None,
    height: int = 800,
    enable_selection_callback: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Fractal Navigation Component - Interactive hierarchical data visualization.

    Renders Sierpinski triangle-based interactive interface for hierarchical exploration.
    Users can click on triangles to navigate the hierarchy with smooth animations.

    Args:
        data: Complete fractal hierarchy from build_fractal_hierarchy()
              Expected structure:
              {
                  'TR': {...},
                  'REVENUS': {...},
                  'CAT_SALAIRE': {...},
                  'SUBCAT_SALAIRE_NET': {...}
              }

        key: Unique key for this component instance (required by Streamlit)

        height: Height of the component in pixels (default: 800)

        enable_selection_callback: If True, sends selection messages to parent window
                                   (for integration with other components)

    Returns:
        Dictionary with interaction result:
        {
            'code': 'CAT_INVESTISSEMENT',
            'label': 'Category Name',
            'level': 2,
            'action': 'zoom' | 'back' | 'reset'
        }
        Returns None if no data provided or error occurs.

    Example:
        >>> from modules.services.fractal_service import build_fractal_hierarchy
        >>> from modules.ui.fractal_component import fractal_navigation
        >>>
        >>> hierarchy = build_fractal_hierarchy()
        >>> result = fractal_navigation(hierarchy, key='main_fractal')
        >>> if result:
        >>>     st.info(f"Navigated to: {result['label']}")
    """

    try:
        # Validate input data
        if not data:
            logger.warning("No data provided to fractal_navigation component")
            st.warning("Aucune donnée disponible pour la visualisation fractale")
            return None

        if 'TR' not in data:
            logger.warning("Invalid hierarchy structure: missing 'TR' root node")
            st.error("Structure de hiérarchie invalide")
            return None

        # Read the CSS file
        css_file = os.path.join(_COMPONENT_DIR, "frontend", "fractal.css")
        with open(css_file, "r", encoding="utf-8") as f:
            css_content = f.read()

        # Read the JavaScript file
        js_file = os.path.join(_COMPONENT_DIR, "frontend", "fractal.js")
        with open(js_file, "r", encoding="utf-8") as f:
            js_content = f.read()

        # Prepare data as JSON (properly escaped for embedding in JS)
        data_json = json.dumps(data, ensure_ascii=False)

        # Create the HTML with embedded CSS and JS
        html_content = f"""
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Fractal Navigation</title>
            <style>
                {css_content}
            </style>
        </head>
        <body>
            <div id="app" class="fractal-container">
                <canvas id="fractalCanvas"></canvas>
                <div class="info-panel">
                    <div class="info-title">🔺 Univers Fractal</div>
                    <div class="info-content">
                        <div class="info-item">
                            <span class="info-label">Niveau</span>
                            <span class="info-value" id="levelDisplay">1</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Montant Total</span>
                            <span class="info-value" id="totalDisplay">0€</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Catégories</span>
                            <span class="info-value" id="categoriesDisplay">0</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Zoom</span>
                            <span class="info-value" id="zoomDisplay">1.0x</span>
                        </div>
                    </div>
                </div>
                <div class="breadcrumb-container">
                    <div class="breadcrumb">
                        <span id="breadcrumbText">TR</span>
                    </div>
                </div>
                <div class="zoom-indicator">
                    <div class="zoom-bar">
                        <div class="zoom-progress" id="zoomProgress"></div>
                    </div>
                    <div class="zoom-label">Profondeur</div>
                </div>
                <div class="controls">
                    <button id="backBtn" class="control-btn back-btn" title="Retour au niveau précédent">
                        ← Retour
                    </button>
                    <button id="resetBtn" class="control-btn reset-btn" title="Retour à la vue d'ensemble">
                        🏠 Vue d'ensemble
                    </button>
                </div>
                <div id="tooltip" class="tooltip" style="display: none;"></div>
            </div>

            <script>
                // Inject data into global scope for fractal.js to use
                window.hierarchyDataInjected = {data_json};
                window.enableSelectionCallback = {str(enable_selection_callback).lower()};

                console.log('[BACKEND] Data injected to window:', Object.keys(window.hierarchyDataInjected).length, 'nodes');
                console.log('[BACKEND] Selection callback enabled:', window.enableSelectionCallback);

                {js_content}

                // ========== COMMUNICATION AVEC STREAMLIT VIA postMessage ==========
                console.log('[POSTMESSAGE-SYNC] Initialisation du système postMessage');

                // Quand les sélections changent, envoyer un postMessage au parent (Streamlit)
                document.addEventListener('fractalStateChanged', function(e) {{
                    console.log('[POSTMESSAGE-SYNC] fractalStateChanged détecté');
                    try {{
                        const state = JSON.parse(localStorage.getItem('fractal_state_v6') || '{{}}');
                        const selections = state.selectedNodes || [];
                        console.log('[POSTMESSAGE-SYNC] Envoi postMessage avec sélections:', selections);
                        window.parent.postMessage({{
                            type: 'fractal_selections_changed',
                            selections: selections,
                            timestamp: Date.now()
                        }}, '*');
                        console.log('[POSTMESSAGE-SYNC] ✅ postMessage envoyé');
                    }} catch (e) {{
                        console.log('[POSTMESSAGE-SYNC] ❌ Erreur:', e);
                    }}
                }});

                // Polling aussi
                let lastSelections = '';
                setInterval(function() {{
                    try {{
                        const state = JSON.parse(localStorage.getItem('fractal_state_v6') || '{{}}');
                        const selectionsStr = (state.selectedNodes || []).join(',');
                        if (selectionsStr !== lastSelections) {{
                            lastSelections = selectionsStr;
                            console.log('[POSTMESSAGE-SYNC] Changement via polling, envoi postMessage');
                            window.parent.postMessage({{
                                type: 'fractal_selections_changed',
                                selections: state.selectedNodes || [],
                                timestamp: Date.now()
                            }}, '*');
                        }}
                    }} catch (e) {{}}
                }}, 300);

                console.log('[POSTMESSAGE-SYNC] ✅ Prêt');
            </script>
        </body>
        </html>
        """

        # Display the HTML component
        components.html(html_content, height=height, scrolling=True)

        # Since components.html() returns None, we rely on session_state
        # JavaScript code in the HTML will update window variables that
        # can be monitored through Streamlit's session state if needed
        # For now, navigation is handled by passing data through the hierarchy structure

        return None

    except Exception as e:
        logger.error(f"Error in fractal_navigation component: {e}", exc_info=True)
        st.error(f"Erreur dans la visualisation fractale: {str(e)}")
        return None


def _get_emoji_for_node(node: Dict[str, Any]) -> str:
    """Get appropriate emoji for a node based on its label."""

    label = node.get('label', '').lower()
    code = node.get('code', '').lower()

    emoji_map = {
        'revenus': '💼',
        'dépenses': '🛒',
        'salaire': '💵',
        'freelance': '🖥️',
        'investissement': '📈',
        'alimentation': '🍔',
        'transport': '🚗',
        'logement': '🏠',
        'santé': '⚕️',
        'loisirs': '🎮',
        'factures': '📄',
        'vêtements': '👕',
        'education': '📚',
    }

    for key, emoji in emoji_map.items():
        if key in label or key in code:
            return emoji

    return '📁'
