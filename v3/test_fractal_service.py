#!/usr/bin/env python3
"""
Unit tests for fractal_service.py

Tests the data hierarchy building and color assignment logic.

@author: djabi
@version: 1.0
@date: 2025-11-22
"""

import sys
import logging
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_imports():
    """Test that all imports work correctly."""
    try:
        from modules.services.fractal_service import (
            build_fractal_hierarchy,
            get_category_color,
            get_type_color,
            get_transactions_for_node,
            get_node_info
        )
        logger.info("[PASS] All imports successful")
        return True
    except ImportError as e:
        logger.error(f"[FAIL] Import error: {e}")
        return False


def test_color_functions():
    """Test color assignment functions."""
    from modules.services.fractal_service import get_category_color, get_type_color

    # Test type colors
    color_revenu = get_type_color('revenu')
    color_depense = get_type_color('depense')

    assert color_revenu == '#10b981', f"Expected #10b981, got {color_revenu}"
    assert color_depense == '#f59e0b', f"Expected #f59e0b, got {color_depense}"

    logger.info("[PASS] Type color functions work correctly")

    # Test category colors
    color_salaire = get_category_color('Salaire', 'revenu')
    color_alimentat = get_category_color('Alimentation', 'depense')

    assert color_salaire == '#059669', f"Expected #059669, got {color_salaire}"
    assert color_alimentat == '#ef4444', f"Expected #ef4444, got {color_alimentat}"

    logger.info("[PASS] Category color functions work correctly")

    return True


def test_hierarchy_structure():
    """Test that hierarchy building returns correct structure."""
    from modules.services.fractal_service import build_fractal_hierarchy

    hierarchy = build_fractal_hierarchy()

    # Check root node exists
    assert 'TR' in hierarchy, "Root node 'TR' not found"
    assert hierarchy['TR']['code'] == 'TR', "Root node code mismatch"

    logger.info("[PASS] Hierarchy root node structure is correct")

    # Check nodes have required fields
    for code, node in hierarchy.items():
        required_fields = ['code', 'label', 'color', 'parent', 'children']
        for field in required_fields:
            assert field in node, f"Node {code} missing field '{field}'"

    logger.info("[PASS] All nodes have required fields")

    return True


def test_backend_imports():
    """Test that backend component wrapper imports correctly."""
    try:
        from modules.ui.fractal_component.backend import fractal_navigation
        logger.info("[PASS] Backend component imports successfully")
        return True
    except ImportError as e:
        logger.error(f"[FAIL] Backend import failed: {e}")
        return False


def test_frontend_files():
    """Test that frontend files exist and are readable."""
    from pathlib import Path

    frontend_dir = Path("modules/ui/fractal_component/frontend")

    files_to_check = [
        frontend_dir / "index.html",
        frontend_dir / "fractal.js",
        frontend_dir / "fractal.css"
    ]

    for filepath in files_to_check:
        if not filepath.exists():
            logger.error(f"[FAIL] Frontend file not found: {filepath}")
            return False

        # Check file is not empty
        if filepath.stat().st_size == 0:
            logger.error(f"[FAIL] Frontend file is empty: {filepath}")
            return False

    logger.info(f"[PASS] All {len(files_to_check)} frontend files exist and have content")
    return True


def test_demo_page_syntax():
    """Test that the demo page has valid Python syntax."""
    try:
        import py_compile
        py_compile.compile('pages/fractal_view.py', doraise=True)
        logger.info("[PASS] Demo page has valid Python syntax")
        return True
    except py_compile.PyCompileError as e:
        logger.error(f"[FAIL] Demo page syntax error: {e}")
        return False


def test_documentation():
    """Test that README_FRACTAL.md exists and has content."""
    from pathlib import Path

    readme = Path("README_FRACTAL.md")

    if not readme.exists():
        logger.error("[FAIL] README_FRACTAL.md not found")
        return False

    if readme.stat().st_size < 1000:
        logger.error("[FAIL] README_FRACTAL.md is too short")
        return False

    # Check for key sections
    content = readme.read_text()
    required_sections = [
        "Vue d'ensemble",
        "Architecture",
        "Installation",
        "Utilisation",
        "API",
        "Géométries"
    ]

    for section in required_sections:
        if section not in content:
            logger.error(f"[FAIL] Missing documentation section: {section}")
            return False

    logger.info("[PASS] README documentation is complete")
    return True


def run_all_tests():
    """Run all tests and report results."""
    tests = [
        ("Imports", test_imports),
        ("Color Functions", test_color_functions),
        ("Hierarchy Structure", test_hierarchy_structure),
        ("Backend Imports", test_backend_imports),
        ("Frontend Files", test_frontend_files),
        ("Demo Page Syntax", test_demo_page_syntax),
        ("Documentation", test_documentation),
    ]

    logger.info("=" * 60)
    logger.info("FRACTAL NAVIGATION - TEST SUITE")
    logger.info("=" * 60)

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"[FAIL] {test_name}: {str(e)}")
            results.append((test_name, False))

    # Summary
    logger.info("=" * 60)
    logger.info("TEST RESULTS SUMMARY")
    logger.info("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        logger.info(f"{test_name:.<45} [{status}]")

    logger.info("=" * 60)
    logger.info(f"TOTAL: {passed}/{total} tests passed")
    logger.info("=" * 60)

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
