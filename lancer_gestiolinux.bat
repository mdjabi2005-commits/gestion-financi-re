#!/bin/bash
# ========================================
# Lanceur Gestion Financière Little
# Double-cliquez sur ce fichier pour lancer l'application
# ========================================

echo ""
echo "========================================"
echo " Gestion Financière Little - Lanceur"
echo "========================================"
echo ""

# Vérifier que Python est installé
if ! command -v python3 &> /dev/null; then
    echo "[ERREUR] Python3 n'est pas installé"
    echo ""
    echo "Installation:"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "  macOS: brew install python3"
    echo ""
    exit 1
fi

echo "[OK] Python est installé"
python3 --version

# Vérifier que Streamlit est installé
echo ""
echo "Vérification de Streamlit..."
if ! python3 -m streamlit --version &> /dev/null; then
    echo "[INFO] Streamlit n'est pas installé"
    echo "[INFO] Installation de Streamlit en cours..."
    python3 -m pip install streamlit
    if [ $? -ne 0 ]; then
        echo "[ERREUR] Impossible d'installer Streamlit"
        exit 1
    fi
    echo "[OK] Streamlit installé avec succès"
else
    echo "[OK] Streamlit est déjà installé"
fi

# Chercher le script Python
echo ""
echo "Recherche du script..."

SCRIPT=""
if [ -f "gestiov4_corrige.py" ]; then
    SCRIPT="gestiov4_corrige.py"
elif [ -f "gestiov4.py" ]; then
    SCRIPT="gestiov4.py"
elif [ -f "gestio.py" ]; then
    SCRIPT="gestio.py"
fi

if [ -z "$SCRIPT" ]; then
    echo "[ERREUR] Aucun script trouvé"
    echo ""
    echo "Veuillez placer un des fichiers suivants dans ce dossier:"
    echo "  - gestiov4_corrige.py"
    echo "  - gestiov4.py"
    echo "  - gestio.py"
    echo ""
    exit 1
fi

echo "[OK] Script trouvé: $SCRIPT"

# Lancer l'application
echo ""
echo "========================================"
echo " Démarrage de l'application..."
echo "========================================"
echo ""
echo "Le navigateur va s'ouvrir automatiquement"
echo ""
echo "Pour arrêter l'application, appuyez sur Ctrl+C"
echo ""

python3 -m streamlit run "$SCRIPT"

# Si Streamlit se ferme avec une erreur
if [ $? -ne 0 ]; then
    echo ""
    echo "[ERREUR] L'application s'est arrêtée avec une erreur"
    read -p "Appuyez sur Entrée pour fermer..."
fi
