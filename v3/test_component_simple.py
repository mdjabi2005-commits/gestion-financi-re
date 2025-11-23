#!/usr/bin/env python3
"""
Simple test for the fixed fractal navigation component.

Run with: streamlit run test_component_simple.py
"""

import streamlit as st
import sys
from pathlib import Path

# Setup path
sys.path.insert(0, str(Path(__file__).parent))

from modules.services.fractal_service import build_fractal_hierarchy
from modules.ui.fractal_component import fractal_navigation

# ==============================
# Page Configuration
# ==============================

st.set_page_config(
    page_title="Test Fractal Component",
    page_icon="🔺",
    layout="wide"
)

# ==============================
# Main Content
# ==============================

st.title("🔺 Test - Fractal Navigation Component")

st.markdown("""
This page tests the fixed fractal navigation component.

**What you should see:**
1. A sidebar on the left with navigation buttons
2. The main content area on the right with details
3. Interactive navigation when you click buttons
4. Breadcrumb navigation showing your position
5. Metrics for the current node
""")

st.divider()

# Build the hierarchy
try:
    with st.spinner("Building hierarchy..."):
        hierarchy = build_fractal_hierarchy()

    if not hierarchy or len(hierarchy) <= 1:
        st.error("No data in hierarchy. Check your database.")
    else:
        st.success(f"✅ Hierarchy loaded: {len(hierarchy)} nodes")

        # Display the component
        st.markdown("---")
        st.subheader("Interactive Navigation")

        result = fractal_navigation(hierarchy, key='test_component')

        st.markdown("---")

        # Show result
        if result:
            st.markdown("### Last Navigation Result")
            st.json(result)

except Exception as e:
    st.error(f"Error: {str(e)}")
    import traceback
    st.code(traceback.format_exc())

# ==============================
# Debug Info
# ==============================

with st.expander("ℹ️ Debug Information"):
    st.markdown("### Session State Keys")
    for key in st.session_state.keys():
        st.code(f"{key}: {st.session_state[key]}")

    st.markdown("### Hierarchy Structure (first 5 nodes)")
    try:
        hierarchy = build_fractal_hierarchy()
        for i, (code, node) in enumerate(list(hierarchy.items())[:5]):
            st.write(f"- **{code}**: {node.get('label', 'N/A')} ({len(node.get('children', []))} children)")
    except:
        st.error("Could not load hierarchy")
