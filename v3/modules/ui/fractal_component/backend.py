"""
Streamlit Component Backend for Fractal Navigation.

Wraps the custom JavaScript/HTML component and provides Python interface.

@author: djabi
@version: 1.0
@date: 2025-11-22
"""

import streamlit.components.v1 as components
from pathlib import Path
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Get the absolute path to the frontend directory
_parent_dir = Path(__file__).parent
_build_dir = _parent_dir / "frontend"

# Declare the component
_fractal_navigation = components.declare_component(
    "fractal_navigation",
    path=str(_build_dir)
)


def fractal_navigation(
    data: Dict[str, Any],
    key: Optional[str] = None,
    height: int = 800
) -> Optional[Dict[str, Any]]:
    """
    Fractal Navigation Component - Interactive Sierpinski triangle-based navigation.

    Renders an interactive fractal visualization for hierarchical data exploration.
    Users can click on triangles to zoom in, with animations and transitions.

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

    Returns:
        Dictionary with interaction result:
        {
            'action': 'zoom' | 'back' | 'reset' | None,
            'code': 'CAT_INVESTISSEMENT',  # Code of clicked node
            'level': 2,  # Current depth level (0-3)
            'timestamp': 1234567890,  # When action occurred
            'current_node': 'REVENUS'  # Currently displayed node
        }
        Returns None if no action has occurred yet.

    Example:
        >>> from modules.services.fractal_service import build_fractal_hierarchy
        >>> from modules.ui.fractal_component import fractal_navigation
        >>>
        >>> hierarchy = build_fractal_hierarchy()
        >>> result = fractal_navigation(hierarchy, key='main_fractal')
        >>>
        >>> if result and result['action'] == 'zoom':
        >>>     st.info(f"Navigated to: {result['code']}")
        >>> elif result and result['action'] == 'back':
        >>>     st.info("Returned to previous level")
    """
    try:
        # Validate input data
        if not data:
            logger.warning("No data provided to fractal_navigation component")
            return None

        if 'TR' not in data:
            logger.warning("Invalid hierarchy structure: missing 'TR' root node")
            return None

        # Call the component with data
        component_value = _fractal_navigation(
            data=data,
            height=height,
            key=key
        )

        # Log the interaction
        if component_value:
            logger.info(f"Fractal navigation event: {component_value}")

        return component_value

    except Exception as e:
        logger.error(f"Error in fractal_navigation component: {e}", exc_info=True)
        return None
