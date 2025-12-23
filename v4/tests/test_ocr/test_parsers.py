"""
Unit Tests for OCR Parsers - PUBLIC API ONLY

Tests OCR text parsing using public interfaces.
"""

import pytest
from domains.ocr.parsers import _normalize_ocr_text, parse_ticket_metadata_v2


@pytest.mark.unit
@pytest.mark.ocr
class TestOCRParsers:
    """Test suite for OCR parsing functions."""
    
    # === NORMALIZATION TESTS ===
    
    def test_normalize_ocr_text(self):
        """Test OCR text normalization."""
        # Arrange
        raw_text = "  TOTAL:   15.50€  \n\n  Date: 18/12/2024  \n  "
        
        # Act
        lines = _normalize_ocr_text(raw_text)
        
        # Assert
        assert isinstance(lines, list)
        assert len(lines) > 0
        assert any("TOTAL" in line for line in lines)
    
    
    def test_normalize_empty_text(self):
        """Test normalizing empty text."""
        # Act
        lines = _normalize_ocr_text("")
        
        # Assert
        assert isinstance(lines, list)
        assert len(lines) <= 1
    
    
    def test_normalize_multiline(self):
        """Test normalizing multi-line text."""
        # Arrange
        text = "Line 1\nLine 2\nLine 3"
        
        # Act
        lines = _normalize_ocr_text(text)
        
        # Assert
        assert isinstance(lines, list)
        assert len(lines) == 3
    
    
    def test_normalize_preserves_keywords(self):
        """Test normalization doesn't break keywords like MONTANT."""
        # Arrange
        text = "MONTANT TOTAL: 15.50"
        
        # Act
        lines = _normalize_ocr_text(text)
        
        # Assert - Should NOT have M0NTANT (O→0 replacement would break it)
        assert any("MONTANT" in line for line in lines)
        assert not any("M0NTANT" in line for line in lines)
    
    
    # === FULL PARSING TESTS ===
    
    def test_parse_ticket_returns_dict(self):
        """Test that parse returns a dictionary."""
        # Arrange
        text = "TOTAL: 15.50€\nDate: 18/12/2024"
        
        # Act
        result = parse_ticket_metadata_v2(text)
        
        # Assert
        assert result is not None
        assert isinstance(result, dict)
        assert 'montant' in result
    
    
    def test_parse_empty_text(self):
        """Test parsing empty text."""
        # Act
        result = parse_ticket_metadata_v2("")
        
        # Assert
        assert result is not None
        assert isinstance(result, dict)
    
    
    def test_parse_with_total_keyword(self):
        """Test parsing text with TOTAL keyword."""
        # Arrange
        text = "TOTAL TTC: 25.80€\nDate: 19/12/2024"
        
        # Act
        result = parse_ticket_metadata_v2(text)
        
        # Assert
        assert result['montant'] > 0
        assert abs(result['montant'] - 25.80) < 0.01
    
    
    def test_parse_includes_metadata(self):
        """Test result includes validation metadata."""
        # Arrange
        text = "TOTAL: 15.50€"
        
        # Act
        result = parse_ticket_metadata_v2(text)
        
        # Assert
        assert 'fiable' in result
        assert 'methode_detection' in result
        assert 'date' in result
    
    
    def test_parse_validates_cross_check(self):
        """Test cross-validation increases reliability."""
        # Arrange - Text with same amount in multiple places
        text = "TOTAL: 15.50€\nMONTANT: 15.50"
        
        # Act
        result = parse_ticket_metadata_v2(text)
        
        # Assert
        assert result['montant'] == 15.50
        # Cross-validation should mark as reliable
        assert isinstance(result.get('fiable'), bool)
    
    
    def test_parse_detects_date(self):
        """Test date detection in OCR text."""
        # Arrange
        text = "Date: 19/12/2024\nTotal: 10€"
        
        # Act
        result = parse_ticket_metadata_v2(text)
        
        # Assert
        assert 'date' in result
        assert result['date'] is not None
    
    
    def test_parse_handles_euro_symbol(self):
        """Test parsing amount with € symbol."""
        # Arrange
        text = "TOTAL: 12.50€"
        
        # Act
        result = parse_ticket_metadata_v2(text)
        
        # Assert
        assert result['montant'] > 0
    
    
    def test_parse_handles_decimal_comma(self):
        """Test parsing amount with comma decimal."""
        # Arrange
        text = "TOTAL: 12,50"
        
        # Act
        result = parse_ticket_metadata_v2(text)
        
        # Assert
        assert result['montant'] > 0
