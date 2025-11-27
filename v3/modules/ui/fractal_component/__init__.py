"""
Fractal Navigation Component

Composant Streamlit pour la navigation fractale interactive.
Utilise des triangles Sierpinski adaptatifs pour explorer les hiérarchies de données.

@author: djabi
@version: 2.0
@date: 2025-11-25
"""

from .backend import fractal_navigation, render_hidden_buttons

__all__ = ['fractal_navigation', 'render_hidden_buttons']
