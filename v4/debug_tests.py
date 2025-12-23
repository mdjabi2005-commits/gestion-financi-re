"""
Manual Test Runner - Debug pytest issues

Run individual test functions manually to identify problems.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("MANUAL TEST RUNNER - DEBUG MODE")
print("=" * 60)

# Test 1: Import conftest
print("\n[1] Testing conftest imports...")
try:
    from tests.conftest import temp_db, sample_transaction, sample_ocr_text
    print("✅ conftest imports OK")
except Exception as e:
    print(f"❌ conftest import failed: {e}")
    sys.exit(1)

# Test 2: Import transaction repository
print("\n[2] Testing transaction repository imports...")
try:
    from domains.transactions.repository import TransactionRepository
    from domains.transactions.models import Transaction
    print("✅ Transaction imports OK")
except Exception as e:
    print(f"❌ Transaction import failed: {e}")
    sys.exit(1)

# Test 3: Import OCR parsers
print("\n[3] Testing OCR parser imports...")
try:
    from domains.ocr.parsers import _normalize_ocr_text, parse_ticket_metadata_v2
    print("✅ OCR parser imports OK")
except Exception as e:
    print(f"❌ OCR parser import failed: {e}")
    sys.exit(1)

# Test 4: Test fixture creation
print("\n[4] Testing fixture creation...")
try:
    import tempfile
    import sqlite3
    
    # Create temp DB
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE transactions (
            id INTEGER PRIMARY KEY,
            type TEXT,
            categorie TEXT,
            sous_categorie TEXT,
            description TEXT,
            montant REAL,
            date TEXT,
            source TEXT
        )
    """)
    conn.commit()
    conn.close()
    
    print(f"✅ Temp DB created: {db_path}")
    os.unlink(db_path)
    print("✅ Temp DB cleaned")
    
except Exception as e:
    print(f"❌ Fixture creation failed: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Run OCR normalize test manually
print("\n[5] Running OCR normalize test manually...")
try:
    from domains.ocr.parsers import _normalize_ocr_text
    
    raw_text = "  TOTAL:   15.50€  \n\n  Date: 18/12/2024  \n  "
    lines = _normalize_ocr_text(raw_text)
    
    assert isinstance(lines, list), "Should return a list"
    assert len(lines) > 0, "Should have lines"
    print(f"✅ OCR normalize OK - {len(lines)} lines")
    print(f"   Sample: {lines[:2]}")
    
except Exception as e:
    print(f"❌ OCR normalize failed: {e}")
    import traceback
    traceback.print_exc()

# Test 6: Test Transaction model
print("\n[6] Testing Transaction model...")
try:
    from domains.transactions.models import Transaction
    from datetime import date
    
    t = Transaction(
        type='dépense',
        categorie='Test',
        montant=100.0,
        date=date.today(),
        description='Test transaction'
    )
    
    print(f"✅ Transaction model OK")
    print(f"   Type: {t.type}, Montant: {t.montant}€")
    
except Exception as e:
    print(f"❌ Transaction model failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print("If all tests above passed, pytest issues are likely:")
print("1. Path configuration")
print("2. Fixture injection")
print("3. Test discovery")
print("\nNext step: Run pytest with --collect-only to see discovery")
print("=" * 60)
