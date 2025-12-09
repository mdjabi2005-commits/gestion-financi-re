"""Script to delete recurring transactions from the database."""

import sqlite3
import sys
from pathlib import Path

# Chemin vers la base de données
# Utiliser finance2.db si fourni en argument, sinon finances.db
if len(sys.argv) > 1:
    DB_PATH = Path(sys.argv[1])
else:
    DB_PATH = Path(__file__).parent.parent / "analyse" / "finance2.db"

def delete_recurring_transactions():
    """Delete all recurring transactions from the database."""
    
    if not DB_PATH.exists():
        print(f"❌ La base de données n'existe pas : {DB_PATH}")
        return
    
    try:
        # Connexion à la base
        connexion = sqlite3.connect(str(DB_PATH))
        curseur = connexion.cursor()
        
        # Compter les transactions récurrentes avant suppression
        curseur.execute("SELECT COUNT(*) FROM transactions WHERE recurrence IS NOT NULL AND recurrence != 'Aucune'")
        nombre_avant = curseur.fetchone()[0]
        
        print(f"📊 Nombre de transactions récurrentes trouvées : {nombre_avant}")
        
        if nombre_avant > 0:
            # Afficher les transactions à supprimer
            curseur.execute("""
                SELECT id, description, categorie, montant, recurrence, date 
                FROM transactions 
                WHERE recurrence IS NOT NULL AND recurrence != 'Aucune'
                ORDER BY date DESC
            """)
            
            transactions = curseur.fetchall()
            print("\n📋 Transactions à supprimer :")
            for trans in transactions:
                print(f"  ID: {trans[0]} | {trans[1]} | {trans[2]} | {trans[3]}€ | Récurrence: {trans[4]} | Date: {trans[5]}")
            
            # Demander confirmation
            confirmation = input("\n⚠️  Êtes-vous sûr ? (oui/non) : ").strip().lower()
            
            if confirmation == "oui":
                # Supprimer les transactions récurrentes
                curseur.execute("DELETE FROM transactions WHERE recurrence IS NOT NULL AND recurrence != 'Aucune'")
                connexion.commit()
                
                # Vérifier le résultat
                curseur.execute("SELECT COUNT(*) FROM transactions WHERE recurrence IS NOT NULL AND recurrence != 'Aucune'")
                nombre_apres = curseur.fetchone()[0]
                
                print(f"\n✅ {nombre_avant} transactions récurrentes supprimées avec succès!")
                print(f"📊 Transactions récurrentes restantes : {nombre_apres}")
            else:
                print("❌ Suppression annulée.")
        else:
            print("ℹ️  Aucune transaction récurrente trouvée.")
        
        connexion.close()
        
    except sqlite3.Error as e:
        print(f"❌ Erreur de base de données : {e}")

if __name__ == "__main__":
    delete_recurring_transactions()
