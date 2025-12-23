"""
Integration Tests for Transaction Operations - SIMPLIFIED

Tests complete workflows with actual repository implementation.
"""

import pytest
import sqlite3
from pathlib import Path
from datetime import date
from domains.transactions.repository import TransactionRepository
from domains.transactions.models import Transaction


@pytest.mark.integration
@pytest.mark.database
class TestTransactionIntegration:
    """Integration tests for transaction workflows."""
    
    def test_add_transaction_complete_workflow(self, temp_db):
        """Test adding a transaction - complete workflow."""
        # Arrange
        repo = TransactionRepository()
        transaction = Transaction(
            type='dépense',
            categorie='Alimentation',
            sous_categorie='Courses',
            montant=45.50,
            date=date(2024, 12, 19),
            description='Test Leclerc'
        )
        
        # Act
        transaction_id = repo.insert(transaction)
        
        # Assert
        assert transaction_id is not None
        assert transaction_id > 0
    
    
    def test_update_transaction_correction(self, temp_db):
        """Test correcting a transaction - user correction workflow."""
        # Arrange
        repo = TransactionRepository()
        initial = Transaction(
            type='dépense',
            categorie='Transport',
            montant=15.50,
            date=date.today(),
            description='Carburant'
        )
        transaction_id = repo.insert(initial)
        
        # Act - User corrects the amount
        repo.update(
            transaction_id,
            {'montant': 25.80}
        )
        
        # Assert - Verify via DB query
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT montant FROM transactions WHERE id = ?", (transaction_id,))
        result = cursor.fetchone()
        conn.close()
        
        assert result is not None
        assert result[0] == 25.80
    
    
    def test_delete_transaction_workflow(self, temp_db):
        """Test deleting a transaction."""
        # Arrange
        repo = TransactionRepository()
        transaction = Transaction(
            type='dépense',
            categorie='Divers',
            montant=10.0,
            date=date.today()
        )
        transaction_id = repo.insert(transaction)
        
        # Act
        repo.delete(transaction_id)
        
        # Assert - Verify deleted
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM transactions WHERE id = ?", (transaction_id,))
        result = cursor.fetchone()
        conn.close()
        
        assert result is None
    
    
    def test_batch_insert_transactions(self, temp_db):
        """Test adding multiple transactions at once."""
        # Arrange
        repo = TransactionRepository()
        transactions = [
            Transaction(
                type='dépense',
                categorie='Alimentation',
                montant=15.0,
                date=date.today()
            ),
            Transaction(
                type='dépense',
                categorie='Transport',
                montant=25.0,
                date=date.today()
            ),
        ]
        
        # Act
        inserted_ids = repo.insert_batch(transactions)
        
        # Assert
        assert len(inserted_ids) == 2
        assert all(id > 0 for id in inserted_ids)
    
    
    def test_transaction_persistence_after_correction(self, temp_db):
        """Test that corrections persist correctly."""
        # Arrange
        repo = TransactionRepository()
        transaction = Transaction(
            type='dépense',
            categorie='Restaurant',
            montant=30.0,
            date=date.today(),
            description='Pizza'
        )
        transaction_id = repo.insert(transaction)
        
        # Act - Make corrections
        repo.update(transaction_id, {'montant': 35.0})
        repo.update(transaction_id, {'description': 'Pizza + Boisson'})
        
        # Assert - Verify final state
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT montant, description FROM transactions WHERE id = ?",
            (transaction_id,)
        )
        result = cursor.fetchone()
        conn.close()
        
        assert result[0] == 35.0
        assert result[1] == 'Pizza + Boisson'
