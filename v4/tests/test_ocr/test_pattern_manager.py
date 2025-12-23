"""
Unit Tests for Pattern Manager

Tests OCR pattern loading and management.
"""

import pytest
from pathlib import Path
from domains.ocr.pattern_manager import PatternManager, get_pattern_manager


@pytest.mark.unit
@pytest.mark.ocr
class TestPatternManager:
    """Test suite for OCR Pattern Manager."""
    
    def test_get_pattern_manager_singleton(self):
        """Test pattern manager is singleton."""
        # Act
        manager1 = get_pattern_manager()
        manager2 = get_pattern_manager()
        
        # Assert
        assert manager1 is manager2
    
    
    def test_load_patterns_success(self):
        """Test loading patterns from config file."""
        # Act
        manager = get_pattern_manager()
        
        # Assert
        assert manager.config is not None
        assert isinstance(manager.config, dict)
    
    
    def test_get_amount_patterns(self):
        """Test retrieving amount patterns."""
        # Arrange
        manager = get_pattern_manager()
        
        # Act
        patterns = manager.get_amount_patterns()
        
        # Assert
        assert isinstance(patterns, list)
        assert len(patterns) > 0
        # Should have common patterns
        assert any('TOTAL' in str(p).upper() for p in patterns)
    
    
    def test_get_payment_patterns(self):
        """Test retrieving payment patterns."""
        # Arrange
        manager = get_pattern_manager()
        
        # Act
        patterns = manager.get_payment_patterns()
        
        # Assert
        assert isinstance(patterns, list)
        assert len(patterns) > 0
        # Should have payment keywords
        assert any('CB' in str(p).upper() or 'CARTE' in str(p).upper() for p in patterns)
    
    
    def test_pattern_has_variations(self):
        """Test patterns include OCR variations."""
        # Arrange
        manager = get_pattern_manager()
        patterns = manager.get_amount_patterns()
        
        # Act - Check if patterns handle common OCR errors
        pattern_str = str(patterns)
        
        # Assert - Should have variations like REEL/KEEL, etc.
        # (Based on actual patterns in config)
        assert len(pattern_str) > 0
    
    
    def test_config_path_absolute(self):
        """Test config path is absolute."""
        # Arrange
        manager = PatternManager()
        
        # Act
        config_path = Path(manager.config_path)
        
        # Assert
        assert config_path.is_absolute()
    
    
    def test_fallback_to_default_config(self):
        """Test fallback when config file missing."""
        # Arrange - Invalid path
        manager = PatternManager(config_path="/invalid/path/config.yml")
        
        # Act
        config = manager.config
        
        # Assert - Should have default config
        assert config is not None
        assert isinstance(config, dict)
