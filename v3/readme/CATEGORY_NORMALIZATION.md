# 📚 Category Normalization System

**Date:** 2025-11-23
**Version:** 1.0
**Status:** Active

---

## Overview

The Category Normalization System ensures consistent category and subcategory names across the entire application. It handles case variations, extra whitespace, and automatically converts all category names to a standardized format.

### Problem it Solves

**Before Normalization:**
```
User enters:    "UBER"
Database has:   "Uber"
                "uber"
                "UBER"
                "Uber Eats"

Visualization: Multiple entries for same category
               Fragmented data in triangles and bubbles
               Inaccurate financial summaries
```

**After Normalization:**
```
User enters:    "UBER"    →  Normalized to: "Uber"
Database has:   "Uber"    →  All identical
                "uber"    →  No duplicates
                "UBER"    →  Clean, consistent data
```

---

## How It Works

### Normalization Rules

The system applies these rules to all category names:

1. **Case Conversion**: Convert to Title Case (first letter of each word capitalized)
   - "UBER" → "Uber"
   - "alimentation" → "Alimentation"
   - "SALAIRE NET" → "Salaire Net"

2. **Whitespace Cleaning**: Remove extra spaces and trim edges
   - "  UBER  " → "Uber"
   - "SALAIRE   NET" → "Salaire Net"

3. **Null Handling**: Return None for empty values
   - "" → None
   - None → None

### Example Transformations

| Input | Output |
|-------|--------|
| "UBER" | "Uber" |
| "uber" | "Uber" |
| "Uber" | "Uber" |
| "ALIMENTATION" | "Alimentation" |
| "salaire net" | "Salaire Net" |
| "FREELANCE" | "Freelance" |
| "" | None |
| None | None |

---

## Implementation

### Files Modified

#### 1. `modules/services/normalization.py` (NEW)
**Core normalization functions:**

```python
from modules.services.normalization import (
    normalize_category,
    normalize_subcategory,
    normalize_both,
    normalize_dict
)

# Single category
normalized = normalize_category("UBER")  # Returns "Uber"

# Both at once
cat, subcat = normalize_both("UBER", "RIDE")
# Returns: ("Uber", "Ride")

# Dictionary normalization
tx = {"categorie": "UBER", "sous_categorie": "ride"}
normalized_tx = normalize_dict(tx)
# Returns: {"categorie": "Uber", "sous_categorie": "Ride"}
```

#### 2. `modules/database/repositories.py` (MODIFIED)
**Automatically normalizes on save/update:**

```python
# These methods now automatically normalize categories:
TransactionRepository.insert(transaction)           # Auto-normalizes
TransactionRepository.insert_batch(transactions)   # Auto-normalizes
TransactionRepository.update(transaction)          # Auto-normalizes
```

---

## Applying to Existing Data

### Step 1: Backup Your Database

```bash
# Create a backup before running the fix
cp ~/analyse/transactions.db ~/analyse/transactions.db.backup
```

### Step 2: Run the Normalization Script

```bash
cd "C:\Users\djabi\gestion-financière\v3"
python fix_existing_categories.py
```

**Output:**
```
================================================================================
🔧 NORMALIZING EXISTING CATEGORIES IN DATABASE
================================================================================

Found 1,234 transactions to process.

✅ [1/1234] Updated: Uber / Ride
✅ [2/1234] Updated: Alimentation / Restaurant
   Progress: 50/1234 processed...
   Progress: 100/1234 processed...

================================================================================
✅ NORMALIZATION COMPLETE
================================================================================
Total transactions: 1,234
Updated: 856
Skipped (already normalized): 378
================================================================================
```

---

## Integration Points

### 1. When Saving Transactions (AUTOMATIC)

**Entry Points:**
- Manual transaction form submission
- CSV import
- OCR/ticket scanning
- Recurring transactions

**Code Flow:**
```
User enters transaction
    ↓
Transaction object created with raw categories
    ↓
TransactionRepository.insert() called
    ↓
Categories automatically normalized before saving
    ↓
Normalized data stored in database
```

### 2. When Updating Transactions (AUTOMATIC)

**Entry Points:**
- Edit existing transaction
- Change category/subcategory

**Code Flow:**
```
User modifies transaction
    ↓
TransactionRepository.update() called
    ↓
Categories automatically normalized
    ↓
Updated data saved to database
```

### 3. When Reading Transactions (ALREADY NORMALIZED)

**Entry Points:**
- Display in tables
- Build fractal hierarchy
- Create visualizations

**Code Flow:**
```
Read from database
    ↓
Categories are already normalized
    ↓
Consistent display in all views
```

---

## Usage Guide

### For Developers

#### Use the Module in Your Code

```python
from modules.services.normalization import normalize_category, normalize_subcategory

# When processing user input
user_category = request.form.get('category')
normalized = normalize_category(user_category)

# Validate before saving
if normalized:
    transaction.categorie = normalized
    # Save...
```

#### Validate User Input

```python
from modules.services.normalization import validate_categories

is_valid, error_msg = validate_categories(category, subcategory)

if not is_valid:
    st.error(f"Invalid category: {error_msg}")
```

#### Normalize Entire Dictionaries

```python
from modules.services.normalization import normalize_dict

# Useful for batch operations
normalized_transaction = normalize_dict(raw_transaction_dict)
```

### For Users

**No changes needed!** The normalization happens automatically:

1. **Enter a transaction**: Write category any way you want
   - "UBER"
   - "uber"
   - "Uber"

   It will be stored as: "Uber"

2. **View transactions**: Always see consistent names
   - Triangles show "Uber"
   - Bubbles show "Uber"
   - Reports show "Uber"

3. **Edit transactions**: Changed categories are re-normalized
   - Edit "uber" to "taxi" → stored as "Taxi"

---

## Verification

### Check Normalization is Working

#### Run the Test Script

```bash
python -c "
from modules.services.normalization import normalize_category
tests = ['UBER', 'uber', 'Uber', 'ALIMENTATION', 'salaire net']
for test in tests:
    print(f'{test:20} → {normalize_category(test)}')
"
```

**Expected Output:**
```
UBER                 → Uber
uber                 → Uber
Uber                 → Uber
ALIMENTATION         → Alimentation
salaire net          → Salaire Net
```

#### Check Database is Normalized

```bash
# List all unique categories
sqlite3 ~/analyse/transactions.db \
  "SELECT DISTINCT categorie FROM transactions ORDER BY categorie;"
```

**Expected Output:**
```
Alimentation
Dépenses
Education
Factures
Freelance
Investissement
Loisirs
Logement
Revenus
Salaire
Santé
Transport
Uber
Vêtements
```

All in Title Case, no duplicates!

---

## Advanced Features

### Alias Mapping (Optional)

The normalization module includes optional alias mappings for common variations:

```python
from modules.services.normalization import CATEGORY_ALIASES

print(CATEGORY_ALIASES)
# {
#     'UBER': 'Uber',
#     'ALIMENTATION': 'Alimentation',
#     'REVENUS': 'Revenus',
#     ...
# }
```

To use aliases:
```python
from modules.services.normalization import normalize_with_aliases

# Apply alias mapping
normalized = normalize_with_aliases("UBER", use_aliases=True)
# Returns: "Uber"
```

### Custom Aliases

Add to `CATEGORY_ALIASES` in `modules/services/normalization.py`:

```python
CATEGORY_ALIASES = {
    'CUSTOM_CATEGORY': 'Custom Category',
    'MC_DONALD': 'Mcdonald',
    # ... add yours
}
```

---

## Troubleshooting

### Issue: Existing data has inconsistent names

**Solution:** Run `fix_existing_categories.py`:
```bash
python fix_existing_categories.py
```

### Issue: Transactions appear with different capitalization

**Solution:** This shouldn't happen. Check if:
1. `fix_existing_categories.py` was run
2. Latest code is deployed (with normalization in insert/update)

### Issue: Categories still look inconsistent in visualizations

**Solution:**
1. Restart Streamlit to clear cache
2. Hard refresh browser (Ctrl+Shift+R)
3. Verify database with SQL: `SELECT DISTINCT categorie FROM transactions;`

---

## Maintenance

### Regular Checks

Monthly, verify consistency:

```bash
sqlite3 ~/analyse/transactions.db \
  "SELECT categorie, COUNT(*) as count FROM transactions GROUP BY categorie ORDER BY count DESC;"
```

All should have different names (no duplicates by case).

### Updating Normalization Rules

If you want to change normalization behavior:

1. Edit `modules/services/normalization.py`
2. Update `normalize_category()` function
3. Re-run `fix_existing_categories.py` to update existing data

---

## Performance Impact

✅ **Negligible**:
- Normalization happens during insert/update only
- Simple string operations (no regex, no network calls)
- Measurable time: < 1ms per transaction

---

## Summary

```
┌─────────────────────────────────────────────────┐
│   USER INPUT: "UBER", "uber", "Uber"           │
└────────────────────┬────────────────────────────┘
                     │
                     ↓ (normalize_category)
                     │
┌────────────────────┴────────────────────────────┐
│      DATABASE: All stored as "Uber"             │
└────────────────────┬────────────────────────────┘
                     │
                     ↓
┌────────────────────┴────────────────────────────┐
│  VISUALIZATION: Consistent "Uber" in all views │
│  - Triangles
│  - Bubbles
│  - Tables
│  - Reports
└─────────────────────────────────────────────────┘
```

✅ **One format. One truth. No inconsistencies.**

---

**Questions?** Check the code in `modules/services/normalization.py` - it's well documented!
