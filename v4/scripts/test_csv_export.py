"""
Script de test pour l'export CSV des transactions sans tickets.

Ce script permet de tester la fonctionnalité d'export CSV des transactions
avec source='import_csv' qui n'ont pas de documents associés.
"""

import sys
import os

# Ajouter le dossier parent au path pour pouvoir importer les modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.services.csv_export_service import (
    get_transactions_sans_tickets,
    export_transactions_sans_tickets_to_csv,
    get_export_path
)


def main():
    """Test l'export CSV des transactions sans tickets."""
    
    print("=" * 60)
    print("TEST: Export CSV des transactions sans tickets")
    print("=" * 60)
    print()
    
    # 1. Récupérer les transactions sans tickets
    print("📋 Récupération des transactions sans tickets...")
    transactions = get_transactions_sans_tickets()
    
    if not transactions:
        print("ℹ️  Aucune transaction trouvée avec source='import_csv' sans tickets")
        print()
        print("💡 Pour tester cette fonctionnalité:")
        print("   1. Importez des transactions via CSV dans l'interface")
        print("   2. Assurez-vous que ces transactions n'ont pas de documents associés")
        print("   3. Relancez ce script")
        return
    
    print(f"✅ {len(transactions)} transaction(s) trouvée(s)")
    print()
    
    # Afficher un aperçu des transactions
    print("📊 Aperçu des 5 premières transactions:")
    print("-" * 60)
    for i, trans in enumerate(transactions[:5], 1):
        print(f"{i}. ID: {trans.get('id')} | Date: {trans.get('date')} | "
              f"Catégorie: {trans.get('categorie')} | Montant: {trans.get('montant'):.2f}€")
    print()
    
    # 2. Exporter vers CSV
    print("💾 Export vers CSV...")
    try:
        nb_exported = export_transactions_sans_tickets_to_csv()
        export_path = get_export_path()
        
        print(f"✅ Export réussi!")
        print(f"📂 Fichier créé: {export_path}")
        print(f"📊 Nombre de transactions exportées: {nb_exported}")
        print()
        
        # Vérifier que le fichier existe
        if os.path.exists(export_path):
            file_size = os.path.getsize(export_path)
            print(f"✅ Fichier validé (taille: {file_size} bytes)")
        else:
            print("❌ Erreur: Le fichier n'a pas été créé")
            
    except Exception as e:
        print(f"❌ Erreur lors de l'export: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 60)
    print("TEST TERMINÉ")
    print("=" * 60)


if __name__ == "__main__":
    main()
