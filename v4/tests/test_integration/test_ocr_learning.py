"""
Integration Tests for OCR Learning System

Tests complete learning workflow when user corrects OCR errors.
"""

import pytest
from domains.ocr.learning_service import (
    analyze_user_correction,
    find_amount_in_text,
    generate_amount_variants,
    suggest_pattern_from_context
)


@pytest.mark.integration
@pytest.mark.ocr
class TestOCRLearningIntegration:
    """Integration tests for OCR learning workflows."""
    
    def test_correction_workflow_amount_found(self):
        """Test complete workflow when amount is found in OCR."""
        # Arrange - User scans ticket with unknown pattern
        ocr_text = "PRICE FINAL: 25.80€\nDate: 19/12/2024"
        detected_amount = 0.0  # OCR didn't detect it
        corrected_amount = 25.80  # User corrects
        
        # Act - System analyzes correction
        analysis = analyze_user_correction(
            ocr_text=ocr_text,
            detected_amount=detected_amount,
            corrected_amount=corrected_amount,
            detection_methods=[]
        )
        
        # Assert - Should find amount and suggest pattern
        assert analysis.found_in_text is True
        assert analysis.scan_error is False
        assert analysis.suggested_pattern is not None
        assert "PRICE" in analysis.suggested_pattern or "FINAL" in analysis.suggested_pattern
    
    
    def test_correction_workflow_scan_error(self):
        """Test workflow when amount not in OCR (scan error)."""
        # Arrange - Amount not in OCR text
        ocr_text = "RESTAURANT XYZ\nMerci"
        detected_amount = 0.0
        corrected_amount = 25.80  # User manually enters
        
        # Act
        analysis = analyze_user_correction(
            ocr_text=ocr_text,
            detected_amount=detected_amount,
            corrected_amount=corrected_amount,
            detection_methods=[]
        )
        
        # Assert - Should detect scan error
        assert analysis.scan_error is True
        assert analysis.found_in_text is False
    
    
    def test_correction_workflow_already_correct(self):
        """Test workflow when OCR was already correct."""
        # Arrange
        ocr_text = "TOTAL: 15.50€"
        detected_amount = 15.50
        corrected_amount = 15.50  # Same
        
        # Act
        analysis = analyze_user_correction(
            ocr_text=ocr_text,
            detected_amount=detected_amount,
            corrected_amount=corrected_amount,
            detection_methods=['A']
        )
        
        # Assert
        assert analysis.already_detected is True
    
    
    def test_find_amount_with_variants(self):
        """Test finding amount with different formats."""
        # Arrange
        ocr_text = "Total: 25,80€"  # Comma decimal
        amount = 25.80  # Dot decimal
        
        # Act
        found, variant, line_idx = find_amount_in_text(ocr_text, amount)
        
        # Assert
        assert found is True
        assert variant in ["25.80", "25,80", "25.80€", "25,80€"]
    
    
    def test_pattern_suggestion_from_context(self):
        """Test pattern generation from context."""
        # Arrange
        context_lines = ["PRICE TOTAL: 25.80€"]
        amount_variant = "25.80"
        
        # Act
        pattern = suggest_pattern_from_context(context_lines, amount_variant)
        
        # Assert
        assert pattern is not None
        assert len(pattern) > 0
        # Should contain PRICE or TOTAL
        assert "PRICE" in pattern.upper() or "TOTAL" in pattern.upper()
    
    
    def test_amount_variants_generation(self):
        """Test generating amount format variants."""
        # Arrange
        amount = 25.80
        
        # Act
        variants = generate_amount_variants(amount)
        
        # Assert
        assert "25.80" in variants  # Dot
        assert "25,80" in variants  # Comma
        assert "2580" in variants   # No decimal
        assert "25.80€" in variants  # With euro
        assert len(variants) >= 5
    
    
    def test_learning_workflow_realistic_ticket(self):
        """Test complete learning workflow with realistic ticket."""
        # Arrange - Realistic Carrefour ticket
        ocr_text = """
        CARREFOUR
        MONTANT REEL: 45.30€
        CB: 45.30
        Date: 19/12/2024
        Merci
        """
        detected_amount = 0.0  # Pattern "MONTANT REEL" unknown
        corrected_amount = 45.30
        
        # Act
        analysis = analyze_user_correction(
            ocr_text=ocr_text,
            detected_amount=detected_amount,
            corrected_amount=corrected_amount,
            detection_methods=[]
        )
        
        # Assert - Should learn this pattern
        assert analysis.found_in_text is True
        assert analysis.suggested_pattern is not None
        assert len(analysis.context_lines) > 0
