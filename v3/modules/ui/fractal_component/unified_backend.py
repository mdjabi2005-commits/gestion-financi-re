"""
Unified Fractal Component Backend - Custom Streamlit Component

Composant qui gère la navigation hiérarchique ET la sélection multi-catégories.
Retourne l'état complet de la navigation et des sélections à Streamlit.

@author: djabi
@version: 2.0 (Unified with Selection)
@date: 2025-11-23
"""

import streamlit as st
import streamlit.components.v1 as components
import logging
from typing import Dict, Any, Optional, List
import os
import json

logger = logging.getLogger(__name__)
_COMPONENT_DIR = os.path.dirname(os.path.abspath(__file__))


def unified_fractal_navigation(
    data: Dict[str, Any],
    key: Optional[str] = None,
    height: int = 500
) -> Optional[Dict[str, Any]]:
    """
    Unified Fractal Navigation Component with Selection Support.

    Returns:
        {
            'action': 'navigation' | 'selection',
            'currentNode': 'CAT_ALIMENTATION',
            'selectedNodes': ['SUBCAT_ALIMENTATION_COURSES', 'SUBCAT_ALIMENTATION_RESTAURANT'],
            'level': 3,
            'isSelectionMode': True/False,
            'timestamp': unix_timestamp
        }
    """

    try:
        if not data:
            logger.warning("No data provided to unified_fractal_navigation")
            st.warning("Aucune donnée disponible")
            return None

        if 'TR' not in data:
            logger.warning("Invalid hierarchy structure")
            st.error("Structure de hiérarchie invalide")
            return None

        # Read CSS
        css_file = os.path.join(_COMPONENT_DIR, "frontend", "fractal.css")
        with open(css_file, "r", encoding="utf-8") as f:
            css_content = f.read()

        # Read JS
        js_file = os.path.join(_COMPONENT_DIR, "frontend", "fractal.js")
        with open(js_file, "r", encoding="utf-8") as f:
            js_content = f.read()

        # Prepare data
        data_json = json.dumps(data, ensure_ascii=False)

        # HTML content with Streamlit component communication
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
                    <div class="info-title">🔺 Navigation Fractale</div>
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
                            <span class="info-label">Mode</span>
                            <span class="info-value" id="modeDisplay">Navigation</span>
                        </div>
                    </div>
                </div>
                <div class="breadcrumb-container">
                    <div class="breadcrumb">
                        <span id="breadcrumbText">TR</span>
                    </div>
                </div>
                <div class="controls">
                    <button id="backBtn" class="control-btn back-btn" title="Retour">
                        ← Retour
                    </button>
                    <button id="resetBtn" class="control-btn reset-btn" title="Réinitialiser">
                        🏠 Réinitialiser
                    </button>
                </div>
                <div id="tooltip" class="tooltip" style="display: none;"></div>
            </div>

            <script>
                // Streamlit API
                if (typeof window.parent !== 'undefined') {{
                    window.streamlitReady = true;
                }}

                // Inject data
                window.hierarchyDataInjected = {data_json};
                window.enableUnifiedMode = true;

                console.log('[UNIFIED] Data injected, unified mode enabled');

                {js_content}

                // Communicate with Streamlit
                function sendSelectionToStreamlit() {{
                    const state = {{
                        action: isSelectionMode ? 'selection' : 'navigation',
                        currentNode: currentNode,
                        selectedNodes: Array.from(selectedNodes),
                        level: navigationStack.length,
                        isSelectionMode: isSelectionMode,
                        timestamp: Date.now()
                    }};

                    console.log('[UNIFIED] Sending state to Streamlit:', state);

                    // Try Streamlit API first
                    if (typeof window.parent !== 'undefined' && window.parent !== window) {{
                        try {{
                            window.parent.postMessage({{
                                type: 'streamlit:componentReady',
                                data: state
                            }}, '*');
                        }} catch (e) {{
                            console.log('[UNIFIED] Streamlit API unavailable');
                        }}
                    }}
                }}

                // Call original sendSelectionToStreamlit if it exists
                if (typeof window.sendSelectionToStreamlit !== 'undefined') {{
                    window._originalSend = window.sendSelectionToStreamlit;
                    window.sendSelectionToStreamlit = function() {{
                        window._originalSend();
                        sendSelectionToStreamlit();
                    }};
                }} else {{
                    window.sendSelectionToStreamlit = sendSelectionToStreamlit;
                }}
            </script>
        </body>
        </html>
        """

        # Display using Streamlit's iframe component
        components.html(html_content, height=height, scrolling=False)

        return None

    except Exception as e:
        logger.error(f"Error in unified_fractal_navigation: {{e}}", exc_info=True)
        st.error(f"Erreur: {{str(e)}}")
        return None
