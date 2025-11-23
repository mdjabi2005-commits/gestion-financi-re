#!/usr/bin/env python3
"""
Script to normalize existing categories in the database.

This script will:
1. Read all transactions from the database
2. Normalize their categories and subcategories
3. Update them in place

Run this ONCE after deploying the normalization changes.
"""

import sys
from pathlib import Path

# Setup path
sys.path.insert(0, str(Path(__file__).parent))

from modules.database.repositories import TransactionRepository
from modules.database.models import Transaction
from modules.services.normalization import normalize_category, normalize_subcategory


def fix_existing_categories():
    """Normalize all existing categories in the database."""

    print("=" * 80)
    print("🔧 NORMALIZING EXISTING CATEGORIES IN DATABASE")
    print("=" * 80)

    # Fetch all transactions (returns DataFrame)
    df = TransactionRepository.get_all()

    if df.empty:
        print("✅ No transactions found in database.")
        return

    print(f"\nFound {len(df)} transactions to process.\n")

    updated_count = 0
    skipped_count = 0

    for idx, (_, row) in enumerate(df.iterrows(), 1):
        # Get current values
        current_cat = row['categorie']
        current_subcat = row['sous_categorie']

        # Normalize
        normalized_cat = normalize_category(current_cat)
        normalized_subcat = normalize_subcategory(current_subcat)

        # Check if normalization is needed
        needs_update = (
            normalized_cat != current_cat or
            normalized_subcat != current_subcat
        )

        if needs_update:
            # Create transaction object for update
            tx = Transaction(
                id=row['id'],
                type=row['type'],
                categorie=normalized_cat,
                sous_categorie=normalized_subcat,
                description=row['description'],
                montant=row['montant'],
                date=row['date'],
                source=row['source'],
                recurrence=row.get('recurrence'),
                date_fin=row.get('date_fin')
            )

            if TransactionRepository.update(tx):
                updated_count += 1
                print(f"✅ [{idx}/{len(df)}] Updated: {normalized_cat} / {normalized_subcat}")
            else:
                print(f"❌ [{idx}/{len(df)}] Failed to update transaction ID {row['id']}")
        else:
            skipped_count += 1

        # Progress
        if idx % 50 == 0:
            print(f"   Progress: {idx}/{len(df)} processed...")

    print("\n" + "=" * 80)
    print("✅ NORMALIZATION COMPLETE")
    print("=" * 80)
    print(f"Total transactions: {len(df)}")
    print(f"Updated: {updated_count}")
    print(f"Skipped (already normalized): {skipped_count}")
    print("=" * 80)


if __name__ == "__main__":
    try:
        fix_existing_categories()
    except Exception as e:
        print(f"\n❌ Error during normalization: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
