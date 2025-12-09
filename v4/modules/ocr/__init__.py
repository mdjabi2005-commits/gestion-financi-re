"""OCR module for document scanning, parsing, and performance tracking."""

# Logging functions
from .logging import (
    log_pattern_occurrence,
    log_ocr_scan,
    update_performance_stats,
    update_pattern_stats,
    determine_success_level
)

# Scanner functions
from .scanner import full_ocr

# Parser functions
from .parsers import (
    get_montant_from_line,
    parse_ticket_metadata,
    move_ticket_to_sorted,
    move_ticket_to_problematic,
    detect_potential_patterns,
    test_patterns_on_ticket,
    extract_text_from_pdf,
    parse_uber_pdf,
    parse_fiche_paie,
    parse_pdf_dispatcher
)

# Diagnostics functions
from .diagnostics import (
    get_ocr_performance_report,
    get_best_patterns,
    get_worst_patterns,
    get_scan_history,
    analyze_external_log,
    extract_patterns_from_text,
    calculate_pattern_reliability,
    diagnose_ocr_patterns
)

# Export functions
from .export_logs import (
    get_logs_summary,
    prepare_logs_for_support,
    export_logs_to_desktop
)

__all__ = [
    # Logging
    'log_pattern_occurrence',
    'log_ocr_scan',
    'update_performance_stats',
    'update_pattern_stats',
    'determine_success_level',

    # Scanner
    'full_ocr',

    # Parsers
    'get_montant_from_line',
    'parse_ticket_metadata',
    'move_ticket_to_sorted',
    'move_ticket_to_problematic',
    'detect_potential_patterns',
    'test_patterns_on_ticket',
    'extract_text_from_pdf',
    'parse_uber_pdf',
    'parse_fiche_paie',
    'parse_pdf_dispatcher',

    # Diagnostics
    'get_ocr_performance_report',
    'get_best_patterns',
    'get_worst_patterns',
    'get_scan_history',
    'analyze_external_log',
    'extract_patterns_from_text',
    'calculate_pattern_reliability',
    'diagnose_ocr_patterns',

    # Export
    'get_logs_summary',
    'prepare_logs_for_support',
    'export_logs_to_desktop'
]
