"""
Pytest Configuration and Fixtures

Provides shared fixtures for all tests.
"""

import pytest
import sqlite3
import tempfile
import os
from pathlib import Path
from datetime import date, datetime


@pytest.fixture
def temp_db():
    """
    Create a temporary SQLite database for testing.
    
    Yields:
        Path to temporary database file
        
    Cleanup:
        Automatically removes the database after test
    """
    # Create temporary database file
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    # Create connection and initialize schema
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create transactions table
    cursor.execute("""
        CREATE TABLE transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            categorie TEXT NOT NULL,
            sous_categorie TEXT,
            description TEXT,
            montant REAL NOT NULL,
            date TEXT NOT NULL,
            source TEXT DEFAULT 'manuel',
            recurrence TEXT,
            date_fin TEXT
        )
    """)
    
    # Create recurrences table
    cursor.execute("""
        CREATE TABLE recurrences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            categorie TEXT NOT NULL,
            sous_categorie TEXT,
            montant REAL NOT NULL,
            date_debut TEXT NOT NULL,
            date_fin TEXT,
            frequence TEXT NOT NULL,
            description TEXT,
            statut TEXT DEFAULT 'active'
        )
    """)
    
    conn.commit()
    conn.close()
    
    yield db_path
    
    # Cleanup
    try:
        os.unlink(db_path)
    except:
        pass


@pytest.fixture
def sample_transaction():
    """Sample transaction data for testing."""
    return {
        'type': 'dépense',
        'categorie': 'Alimentation',
        'sous_categorie': 'Supermarché',
        'description': 'Courses Leclerc',
        'montant': 45.50,
        'date': '2024-12-18',
        'source': 'manuel'
    }


@pytest.fixture
def sample_transactions():
    """Multiple sample transactions for batch testing."""
    return [
        {
            'type': 'dépense',
            'categorie': 'Alimentation',
            'sous_categorie': 'Restaurant',
            'description': 'Déjeuner',
            'montant': 25.00,
            'date': '2024-12-15',
            'source': 'manuel'
        },
        {
            'type': 'revenu',
            'categorie': 'Salaire',
            'sous_categorie': 'Net',
            'description': 'Salaire décembre',
            'montant': 2500.00,
            'date': '2024-12-01',
            'source': 'manuel'
        },
        {
            'type': 'dépense',
            'categorie': 'Transport',
            'sous_categorie': 'Essence',
            'description': 'Total',
            'montant': 60.00,
            'date': '2024-12-10',
            'source': 'OCR'
        }
    ]


@pytest.fixture
def sample_ocr_text():
    """Sample OCR text from a ticket for testing."""
    return """
    CARREFOUR MARKET
    123 RUE DE LA PAIX
    75001 PARIS
    
    Date: 18/12/2024
    
    Produits:
    Pain           1.50€
    Lait           2.30€
    Fromage        5.20€
    
    TOTAL:        15.50€
    
    CB: ****1234
    MERCI DE VOTRE VISITE
    """


@pytest.fixture
def sample_ocr_text_uber():
    """Sample OCR text from Uber receipt."""
    return """
    UBER
    Votre reçu
    
    Date: 17/12/2024
    Trajet: Gare -> Bureau
    
    MONTANT TOTAL: 25.80€
    Paiement par CB
    
    Merci d'avoir utilisé Uber
    """


@pytest.fixture
def temp_image_file(tmp_path):
    """Create a temporary image file for OCR testing."""
    image_path = tmp_path / "test_ticket.jpg"
    # Create a dummy file (real tests would need actual image)
    image_path.write_text("dummy image data")
    return str(image_path)


@pytest.fixture
def mock_csv_data():
    """Sample CSV data for export testing."""
    import pandas as pd
    
    return pd.DataFrame([
        {
            'id': 1,
            'date': '2024-12-01',
            'type': 'dépense',
            'categorie': 'Alimentation',
            'sous_categorie': 'Supermarché',
            'description': 'Courses',
            'montant': 45.50,
            'source': 'manuel'
        },
        {
            'id': 2,
            'date': '2024-12-05',
            'type': 'revenu',
            'categorie': 'Salaire',
            'sous_categorie': 'Net',
            'description': 'Paye',
            'montant': 2500.00,
            'source': 'manuel'
        }
    ])
