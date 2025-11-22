#!/usr/bin/env python3
"""
Launch script for Fractal Navigation Demo.

This script properly sets up the Python path and launches the fractal_view page.

Usage:
    python run_fractal.py

or with Streamlit directly:
    streamlit run pages/fractal_view.py -- --logger.level=warning
"""

import subprocess
import sys
from pathlib import Path

def main():
    """Launch the Fractal Navigation Demo."""

    # Get the directory of this script
    script_dir = Path(__file__).parent.resolve()

    # Run streamlit with proper Python path
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(script_dir / "pages" / "fractal_view.py"),
        "--logger.level=warning"
    ]

    print(f"Launching Fractal Navigation Demo...")
    print(f"Working directory: {script_dir}")
    print(f"Command: {' '.join(cmd)}\n")

    try:
        subprocess.run(cmd, cwd=str(script_dir))
    except KeyboardInterrupt:
        print("\nApplication closed.")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
