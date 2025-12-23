"""
🎮 Console de Contrôle - Centre de Commandes

Console pour gérer l'application, lancer des commandes, et accéder aux outils.
Version Base - Sera enrichie en Phase 3.
"""

import streamlit as st
from pathlib import Path
from datetime import datetime
import subprocess
import sys


def render_console():
    """Render the control console."""
    
    st.title("🎮 Console de Contrôle")
    st.caption("Centre de commandes pour gérer votre application")
    
    # === STATUS APP ===
    st.header("📊 Status Application")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("🟢 Status", "En ligne", delta="Running")
    
    with col2:
        db_path = Path("data/database.db")
        if db_path.exists():
            db_size = db_path.stat().st_size / 1024  # KB
            st.metric("💾 Base de données", f"{db_size:.1f} KB")
        else:
            st.metric("💾 Base de données", "Non trouvée", delta_color="off")
    
    with col3:
        log_path = Path("data/logs/gestio_app.log")
        if log_path.exists():
            log_size = log_path.stat().st_size / 1024  # KB
            st.metric("📝 Logs", f"{log_size:.1f} KB")
        else:
            st.metric("📝 Logs", "Non trouvés", delta_color="off")
    
    st.markdown("---")
    
    # === QUICK ACTIONS ===
    st.header("⚡ Actions Rapides")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📝 Logs")
        
        if st.button("📋 Voir les logs (20 dernières lignes)", use_container_width=True):
            show_recent_logs()
        
        if st.button("🔍 Ouvrir le fichier de logs", use_container_width=True):
            open_log_file()
        
        if st.button("🗑️ Nettoyer les vieux logs", use_container_width=True):
            clean_old_logs()
    
    with col2:
        st.subheader("🧪 Tests")
        
        if st.button("▶️ Lancer les tests", use_container_width=True):
            run_tests()
        
        if st.button("📊 Rapport de coverage", use_container_width=True):
            show_coverage_info()
        
        if st.button("🔄 Réinstaller pytest", use_container_width=True):
            reinstall_pytest()
    
    st.markdown("---")
    
    # === SYSTEM INFO ===
    st.header("💻 Informations Système")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Python Version** : {sys.version.split()[0]}")
        st.write(f"**Streamlit Version** : {st.__version__}")
        st.write(f"**Répertoire** : `{Path.cwd()}`")
    
    with col2:
        st.write(f"**Date/Heure** : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Count files
        py_files = len(list(Path.cwd().rglob("*.py")))
        st.write(f"**Fichiers Python** : {py_files}")
        
        # Test infrastructure
        if Path("pytest.ini").exists():
            st.write(f"**Tests** : ✅ Infrastructure OK")
        else:
            st.write(f"**Tests** : ⚠️ Non configurés")
    
    st.markdown("---")
    
    # === SHORTCUTS ===
    st.header("🔗 Raccourcis")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**📁 Dossiers**")
        st.markdown("- [data/](data/)")
        st.markdown("- [data/logs/](data/logs/)")
        st.markdown("- [tests/](tests/)")
    
    with col2:
        st.markdown("**📄 Fichiers Clés**")
        st.markdown("- [pytest.ini](pytest.ini)")
        st.markdown("- [main.py](main.py)")
        st.markdown("- [README.md](README.md)")
    
    with col3:
        st.markdown("**🧪 Tests**")
        st.markdown("- [tests/README.md](tests/README.md)")
        st.markdown("- [QUICKSTART_TESTS.md](QUICKSTART_TESTS.md)")
    
    st.markdown("---")
    
    # === PHASE 3 PREVIEW ===
    with st.expander("🚀 Fonctionnalités Futures (Phase 3)"):
        st.info("""
        **Prochaines améliorations** :
        - 🔄 Vérifier les mises à jour
        - 📦 Installer les dépendances
        - 🏗️ Builder l'application (PyInstaller)
        - 🐛 Débugger en temps réel
        - 📊 Dashboard de performance
        - 🔧 Configuration avancée
        - 📤 Export/Backup automatique
        - 🌐 Déploiement multi-OS
        """)
    
    st.markdown("---")
    st.caption("v4 Production Console | Phase 1 ✅ | Session 18 Déc 2024")


# === HELPER FUNCTIONS ===

def show_recent_logs():
    """Display recent log entries."""
    log_file = Path("data/logs/gestio_app.log")
    
    if not log_file.exists():
        st.warning("⚠️ Fichier de logs introuvable")
        return
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        recent = lines[-20:] if len(lines) > 20 else lines
        
        st.code("".join(recent), language="log")
        st.success(f"✅ Affichage des {len(recent)} dernières lignes")
    
    except Exception as e:
        st.error(f"❌ Erreur : {e}")


def open_log_file():
    """Open log file in system editor."""
    log_file = Path("data/logs/gestio_app.log")
    
    if not log_file.exists():
        st.warning("⚠️ Fichier de logs introuvable")
        return
    
    try:
        import os
        os.startfile(log_file)  # Windows
        st.success("✅ Fichier ouvert dans l'éditeur")
    except Exception as e:
        st.error(f"❌ Erreur : {e}")
        st.info(f"📁 Chemin : `{log_file.absolute()}`")


def clean_old_logs():
    """Clean old log backup files."""
    log_dir = Path("data/logs")
    
    if not log_dir.exists():
        st.warning("⚠️ Dossier logs introuvable")
        return
    
    backups = list(log_dir.glob("gestio_app.log.*"))
    
    if not backups:
        st.info("ℹ️ Aucun backup à nettoyer")
        return
    
    for backup in backups:
        backup.unlink()
    
    st.success(f"✅ {len(backups)} backup(s) supprimé(s)")


def run_tests():
    """Run pytest tests."""
    with st.spinner("🧪 Lancement des tests..."):
        try:
            result = subprocess.run(
                ["pytest", "-v"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            st.code(result.stdout + result.stderr, language="text")
            
            if result.returncode == 0:
                st.success("✅ Tests réussis !")
            else:
                st.error(f"❌ Tests échoués (exit code: {result.returncode})")
        
        except subprocess.TimeoutExpired:
            st.error("⏱️ Timeout - Tests trop longs")
        except FileNotFoundError:
            st.error("❌ pytest non installé - Exécutez : `pip install pytest`")
        except Exception as e:
            st.error(f"❌ Erreur : {e}")


def show_coverage_info():
    """Display coverage report info."""
    coverage_dir = Path("htmlcov")
    
    if coverage_dir.exists():
        st.success("✅ Rapport de coverage disponible")
        st.info(f"📁 Ouvrez : `{coverage_dir / 'index.html'}`")
        
        if st.button("🌐 Ouvrir dans le navigateur"):
            import webbrowser
            webbrowser.open((coverage_dir / "index.html").absolute().as_uri())
    else:
        st.warning("⚠️ Rapport non généré")
        st.info("💡 Lancez : `pytest --cov=domains --cov=shared --cov-report=html`")


def reinstall_pytest():
    """Reinstall pytest and pytest-cov."""
    with st.spinner("📦 Installation de pytest..."):
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", "pytest", "pytest-cov"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            st.code(result.stdout, language="text")
            
            if result.returncode == 0:
                st.success("✅ pytest installé avec succès !")
            else:
                st.error(f"❌ Erreur d'installation (exit code: {result.returncode})")
        
        except Exception as e:
            st.error(f"❌ Erreur : {e}")


if __name__ == "__main__":
    render_console()
