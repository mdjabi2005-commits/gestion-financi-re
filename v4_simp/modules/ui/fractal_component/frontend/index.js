/**
 * Fractal Navigation Component - Streamlit Integration
 *
 * This is the entry point for the Sierpinski triangle navigation component.
 * It wraps the fractal.js functionality with Streamlit component communication.
 */

import Streamlit from "streamlit-component-lib"
import "./fractal.js"

// Initialize component with Streamlit
Streamlit.setComponentReady()
Streamlit.setFrameHeight(document.body.scrollHeight)

// Handle window resize
window.addEventListener('resize', () => {
  Streamlit.setFrameHeight(document.body.scrollHeight)
})

// Export for use as a component
export default {}
