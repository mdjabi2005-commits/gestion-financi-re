# Running Tests for Gestion Financière V4

## Installation

Install pytest and coverage tools:
```bash
pip install pytest pytest-cov
```

## Running Tests

### Run all tests
```bash
cd v4
pytest
```

### Run with verbose output
```bash
pytest -v
```

### Run specific test file
```bash
pytest tests/test_transactions/test_repository.py
```

### Run specific test
```bash
pytest tests/test_transactions/test_repository.py::TestTransactionRepository::test_insert_transaction_success
```

### Run tests by marker
```bash
# Only unit tests
pytest -m unit

# Only OCR tests
pytest -m ocr

# Only database tests
pytest -m database
```

## Coverage

### Generate coverage report
```bash
pytest --cov=domains --cov=shared --cov-report=html
```

### View coverage in browser
```bash
# After running coverage
start htmlcov/index.html  # Windows
open htmlcov/index.html   # macOS
```

### Coverage for specific module
```bash
pytest --cov=domains.transactions --cov-report=term-missing
```

## Test Structure

```
v4/
├── pytest.ini          # Pytest configuration
├── tests/
│   ├── conftest.py     # Shared fixtures
│   ├── test_transactions/
│   │   └── test_repository.py
│   ├── test_ocr/
│   │   ├── test_parsers.py
│   │   └── test_pattern_manager.py
│   └── test_services/
│       └── test_csv_export.py
```

## Fixtures Available

- `temp_db` - Temporary SQLite database
- `sample_transaction` - Single transaction data
- `sample_transactions` - Multiple transactions
- `sample_ocr_text` - Sample OCR text from ticket
- `sample_ocr_text_uber` - Uber receipt OCR text
- `temp_image_file` - Temporary image file
- `mock_csv_data` - Sample DataFrame for CSV tests

## Writing New Tests

Example test:
```python
import pytest
from shared.exceptions import DatabaseError

@pytest.mark.unit
def test_my_function(temp_db, sample_transaction):
    # Arrange
    data = sample_transaction
    
    # Act
    result = my_function(data)
    
    # Assert
    assert result is not None
    assert result['montant'] == 45.50
```

## Continuous Integration

Tests should run automatically before commits:
```bash
# Pre-commit check
pytest --maxfail=1 --disable-warnings -q
```

## Target Coverage

- **Current**: 0%
- **Phase 1 Goal**: 20-30%
- **Production Goal**: 60-70%

## Common Issues

### Import errors
Make sure you're in the v4/ directory:
```bash
cd v4
pytest
```

### Database locked
Close all Streamlit instances before running tests.

### Missing dependencies
```bash
pip install -r requirements.txt
pip install pytest pytest-cov
```
