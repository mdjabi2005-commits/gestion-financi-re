@echo off
REM ========================================
REM Lanceur Gestion Financiere Little
REM Double-cliquez sur ce fichier pour lancer l'application
REM ========================================

title Gestion Financiere Little - Lanceur

echo.
echo ========================================
echo  Gestion Financiere Little - Lanceur
echo ========================================
echo.

REM Verifier que Python est installe
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python n'est pas installe ou n'est pas dans le PATH
    echo.
    echo Telechargez Python sur: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo [OK] Python est installe
python --version

REM Verifier que Streamlit est installe
echo.
echo Verification de Streamlit...
python -m streamlit --version >nul 2>&1
if errorlevel 1 (
    echo [INFO] Streamlit n'est pas installe
    echo [INFO] Installation de Streamlit en cours...
    python -m pip install streamlit
    if errorlevel 1 (
        echo [ERREUR] Impossible d'installer Streamlit
        pause
        exit /b 1
    )
    echo [OK] Streamlit installe avec succes
) else (
    echo [OK] Streamlit est deja installe
)

REM Chercher le script Python
echo.
echo Recherche du script...

set SCRIPT_FOUND=0
if exist "gestiov4_corrige.py" (
    set SCRIPT=gestiov4_corrige.py
    set SCRIPT_FOUND=1
) else if exist "gestiov4.py" (
    set SCRIPT=gestiov4.py
    set SCRIPT_FOUND=1
) else if exist "gestio.py" (
    set SCRIPT=gestio.py
    set SCRIPT_FOUND=1
)

if %SCRIPT_FOUND%==0 (
    echo [ERREUR] Aucun script trouve
    echo.
    echo Veuillez placer un des fichiers suivants dans ce dossier:
    echo   - gestiov4_corrige.py
    echo   - gestiov4.py
    echo   - gestio.py
    echo.
    pause
    exit /b 1
)

echo [OK] Script trouve: %SCRIPT%

REM Lancer l'application
echo.
echo ========================================
echo  Demarrage de l'application...
echo ========================================
echo.
echo Le navigateur va s'ouvrir automatiquement
echo.
echo Pour arreter l'application, fermez cette fenetre
echo ou appuyez sur Ctrl+C
echo.

python -m streamlit run %SCRIPT%

REM Si Streamlit se ferme, attendre
if errorlevel 1 (
    echo.
    echo [ERREUR] L'application s'est arretee avec une erreur
    pause
)
