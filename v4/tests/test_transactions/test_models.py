"""
Unit Tests for Transaction Models

Tests Transaction dataclass without database operations.
"""

import pytest
from datetime import date
from domains.transactions.models import Transaction


@pytest.mark.unit
class TestTransactionModel:
    """Test suite for Transaction model."""
    
    def test_create_transaction(self):
        """Test creating a basic transaction."""
        # Act
        t = Transaction(
            type='dépense',
            categorie='Alimentation',
            montant=45.50,
            date=date(2024, 12, 18),
            description='Test'
        )
        
        # Assert
        assert t.type == 'dépense'
        assert t.categorie == 'Alimentation'
        assert t.montant == 45.50
        assert t.description == 'Test'
    
    
    def test_transaction_with_subcategory(self):
        """Test transaction with subcategory."""
        # Act
        t = Transaction(
            type='revenu',
            categorie='Salaire',
            sous_categorie='Net',
            montant=2500.00,
            date=date.today()
        )
        
        # Assert
        assert t.sous_categorie == 'Net'
        assert t.montant == 2500.00
    
    
    def test_transaction_default_values(self):
        """Test transaction optional fields."""
        # Act
        t = Transaction(
            type='dépense',
            categorie='Test',
            montant=100.0,
            date=date.today()
        )
        
        # Assert
        assert t.id is None  # Not set yet
        assert hasattr(t, 'source')  # Has source attribute
