"""
Unit Tests for Transaction Service

Tests category normalization and business logic.
"""

import pytest
from domains.transactions.service import normalize_category, normalize_subcategory


@pytest.mark.unit
class TestTransactionService:
    """Test suite for transaction service functions."""
    
    def test_normalize_category_lowercase(self):
        """Test category normalization from lowercase."""
        # Act
        result = normalize_category("alimentation")
        
        # Assert
        assert result == "Alimentation"
    
    
    def test_normalize_category_uppercase(self):
        """Test category normalization from uppercase."""
        # Act
        result = normalize_category("TRANSPORT")
        
        # Assert
        assert result == "Transport"
    
    
    def test_normalize_category_mixed_case(self):
        """Test category normalization from mixed case."""
        # Act
        result = normalize_category("AlImEnTaTiOn")
        
        # Assert
        assert result == "Alimentation"
    
    
    def test_normalize_category_with_spaces(self):
        """Test category normalization with extra spaces."""
        # Act
        result = normalize_category("  Alimentation  ")
        
        # Assert
        assert result == "Alimentation"
    
    
    def test_normalize_subcategory(self):
        """Test subcategory normalization."""
        # Act
        result = normalize_subcategory("supermarché")
        
        # Assert
        assert result == "Supermarché"
    
    
    def test_normalize_empty_string(self):
        """Test normalizing empty/None values."""
        # Act
        result1 = normalize_category("")
        result2 = normalize_category(None)
        
        # Assert
        assert result1 in ["", None]  # Depends on implementation
        assert result2 in ["", None]
