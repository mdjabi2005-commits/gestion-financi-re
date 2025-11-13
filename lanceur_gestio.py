#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 Lanceur Graphique - Gestion Financière Little
Lanceur professionnel pour démarrer l'application sans passer par CMD/PowerShell
"""

import sys
import os
import subprocess
import webbrowser
import time
from pathlib import Path
import socket

try:
    from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                                 QHBoxLayout, QPushButton, QLabel, QTextEdit, 
                                 QFrame, QSystemTrayIcon, QMenu, QAction)
    from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer
    from PyQt5.QtGui import QIcon, QFont, QTextCursor, QPixmap
except ImportError:
    print("❌ PyQt5 n'est pas installé.")
    print("📦 Installation en cours...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "PyQt5"])
    from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                                 QHBoxLayout, QPushButton, QLabel, QTextEdit, 
                                 QFrame, QSystemTrayIcon, QMenu, QAction)
    from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer
    from PyQt5.QtGui import QIcon, QFont, QTextCursor, QPixmap


class StreamlitThread(QThread):
    """Thread pour exécuter Streamlit en arrière-plan"""
    output_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)
    url_ready_signal = pyqtSignal(str)
    
    def __init__(self, script_path, port=8501):
        super().__init__()
        self.script_path = script_path
        self.port = port
        self.process = None
        self.running = False
    
    def find_free_port(self):
        """Trouve un port libre si le port par défaut est occupé"""
        for port in range(self.port, self.port + 10):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(('localhost', port))
                    return port
                except OSError:
                    continue
        return self.port
    
    def run(self):
        """Démarre Streamlit"""
        self.running = True
        
        # Trouver un port libre
        free_port = self.find_free_port()
        if free_port != self.port:
            self.output_signal.emit(f"⚠️ Port {self.port} occupé, utilisation du port {free_port}")
            self.port = free_port
        
        # Commande pour lancer Streamlit
        cmd = [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(self.script_path),
            f"--server.port={self.port}",
            "--server.headless=true",
            "--browser.gatherUsageStats=false"
        ]
        
        try:
            self.output_signal.emit(f"🚀 Démarrage de l'application...")
            self.output_signal.emit(f"📂 Script: {self.script_path}")
            self.output_signal.emit(f"🌐 Port: {self.port}")
            self.status_signal.emit("running")
            
            # Démarrer le processus
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Lire la sortie ligne par ligne
            url_sent = False
            for line in self.process.stdout:
                if not self.running:
                    break
                    
                line = line.strip()
                if line:
                    self.output_signal.emit(line)
                    
                    # Détecter quand Streamlit est prêt
                    if "You can now view your Streamlit app" in line or "Local URL:" in line:
                        if not url_sent:
                            url = f"http://localhost:{self.port}"
                            self.url_ready_signal.emit(url)
                            url_sent = True
            
        except Exception as e:
            self.output_signal.emit(f"❌ Erreur: {str(e)}")
            self.status_signal.emit("error")
        finally:
            if self.process:
                self.process.wait()
            self.status_signal.emit("stopped")
            self.running = False
    
    def stop(self):
        """Arrête Streamlit"""
        self.running = False
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()


class GestioLauncher(QMainWindow):
    """Interface graphique du lanceur"""
    
    def __init__(self):
        super().__init__()
        self.streamlit_thread = None
        self.app_url = None
        self.script_path = self.find_script()
        
        self.init_ui()
        self.setup_tray()
    
    def find_script(self):
        """Trouve le script gestiov4_corrige.py ou gestiov4.py"""
        possible_names = ["gestiov4_corrige.py", "gestiov4.py", "gestio.py"]
        
        # Chercher dans le répertoire courant
        current_dir = Path.cwd()
        for name in possible_names:
            path = current_dir / name
            if path.exists():
                return path
        
        # Chercher dans le répertoire du lanceur
        launcher_dir = Path(__file__).parent
        for name in possible_names:
            path = launcher_dir / name
            if path.exists():
                return path
        
        # Par défaut, utiliser gestiov4_corrige.py
        return current_dir / "gestiov4_corrige.py"
    
    def init_ui(self):
        """Initialise l'interface utilisateur"""
        self.setWindowTitle("🚀 Gestion Financière Little - Lanceur")
        self.setMinimumSize(800, 600)
        self.setStyleSheet(self.get_stylesheet())
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # === EN-TÊTE ===
        header = self.create_header()
        main_layout.addWidget(header)
        
        # === INFORMATIONS ===
        info_frame = QFrame()
        info_frame.setObjectName("infoFrame")
        info_layout = QVBoxLayout(info_frame)
        
        self.status_label = QLabel("⚪ Application arrêtée")
        self.status_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.status_label.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(self.status_label)
        
        self.script_label = QLabel(f"📂 Script: {self.script_path.name}")
        self.script_label.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(self.script_label)
        
        self.url_label = QLabel("🌐 URL: Non disponible")
        self.url_label.setAlignment(Qt.AlignCenter)
        self.url_label.setStyleSheet("color: #6b7280;")
        info_layout.addWidget(self.url_label)
        
        main_layout.addWidget(info_frame)
        
        # === BOUTONS DE CONTRÔLE ===
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)
        
        self.start_btn = QPushButton("▶️ Démarrer")
        self.start_btn.setObjectName("startButton")
        self.start_btn.clicked.connect(self.start_app)
        
        self.stop_btn = QPushButton("⏹️ Arrêter")
        self.stop_btn.setObjectName("stopButton")
        self.stop_btn.clicked.connect(self.stop_app)
        self.stop_btn.setEnabled(False)
        
        self.open_btn = QPushButton("🌐 Ouvrir dans le navigateur")
        self.open_btn.setObjectName("openButton")
        self.open_btn.clicked.connect(self.open_browser)
        self.open_btn.setEnabled(False)
        
        buttons_layout.addWidget(self.start_btn)
        buttons_layout.addWidget(self.stop_btn)
        buttons_layout.addWidget(self.open_btn)
        
        main_layout.addLayout(buttons_layout)
        
        # === CONSOLE DE LOGS ===
        console_label = QLabel("📋 Console")
        console_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        main_layout.addWidget(console_label)
        
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setFont(QFont("Consolas", 9))
        self.console.setStyleSheet("""
            QTextEdit {
                background-color: #1f2937;
                color: #10b981;
                border: 2px solid #374151;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        main_layout.addWidget(self.console)
        
        # === BOUTON QUITTER ===
        quit_btn = QPushButton("❌ Quitter")
        quit_btn.setObjectName("quitButton")
        quit_btn.clicked.connect(self.quit_app)
        main_layout.addWidget(quit_btn)
        
        # Message de bienvenue
        self.log("✨ Bienvenue dans le lanceur de Gestion Financière Little")
        self.log(f"📂 Script trouvé: {self.script_path}")
        
        if not self.script_path.exists():
            self.log("⚠️ ATTENTION: Le script n'existe pas encore!")
            self.log(f"   Veuillez placer votre script dans: {self.script_path}")
    
    def create_header(self):
        """Crée l'en-tête de l'application"""
        header = QFrame()
        header.setObjectName("header")
        header_layout = QVBoxLayout(header)
        
        title = QLabel("💰 Gestion Financière Little")
        title.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #10b981;")
        
        subtitle = QLabel("Lanceur d'application professionnel")
        subtitle.setFont(QFont("Segoe UI", 12))
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #6b7280;")
        
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        
        return header
    
    def setup_tray(self):
        """Configure l'icône dans la barre des tâches"""
        self.tray_icon = QSystemTrayIcon(self)
        
        # Menu du tray
        tray_menu = QMenu()
        
        show_action = QAction("Afficher", self)
        show_action.triggered.connect(self.show)
        
        quit_action = QAction("Quitter", self)
        quit_action.triggered.connect(self.quit_app)
        
        tray_menu.addAction(show_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_activated)
        self.tray_icon.show()
    
    def tray_activated(self, reason):
        """Gère les clics sur l'icône du tray"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()
    
    def start_app(self):
        """Démarre l'application Streamlit"""
        if not self.script_path.exists():
            self.log("❌ Erreur: Le script n'existe pas!")
            self.log(f"   Chemin attendu: {self.script_path}")
            return
        
        if self.streamlit_thread and self.streamlit_thread.running:
            self.log("⚠️ L'application est déjà en cours d'exécution")
            return
        
        self.log("🚀 Démarrage de l'application...")
        
        # Créer et démarrer le thread
        self.streamlit_thread = StreamlitThread(self.script_path)
        self.streamlit_thread.output_signal.connect(self.log)
        self.streamlit_thread.status_signal.connect(self.update_status)
        self.streamlit_thread.url_ready_signal.connect(self.on_url_ready)
        self.streamlit_thread.start()
        
        # Mettre à jour l'UI
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
    
    def stop_app(self):
        """Arrête l'application Streamlit"""
        if self.streamlit_thread:
            self.log("⏹️ Arrêt de l'application...")
            self.streamlit_thread.stop()
            self.streamlit_thread.wait()
            self.streamlit_thread = None
        
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.open_btn.setEnabled(False)
        self.app_url = None
    
    def open_browser(self):
        """Ouvre l'application dans le navigateur"""
        if self.app_url:
            webbrowser.open(self.app_url)
            self.log(f"🌐 Ouverture de {self.app_url} dans le navigateur")
        else:
            self.log("⚠️ L'URL n'est pas encore disponible")
    
    def on_url_ready(self, url):
        """Appelé quand l'URL de l'application est prête"""
        self.app_url = url
        self.url_label.setText(f"🌐 URL: {url}")
        self.url_label.setStyleSheet("color: #10b981; font-weight: bold;")
        self.open_btn.setEnabled(True)
        
        self.log(f"✅ Application prête: {url}")
        
        # Ouvrir automatiquement le navigateur après 2 secondes
        QTimer.singleShot(2000, self.open_browser)
    
    def update_status(self, status):
        """Met à jour le statut de l'application"""
        if status == "running":
            self.status_label.setText("🟢 Application en cours d'exécution")
            self.status_label.setStyleSheet("color: #10b981;")
        elif status == "stopped":
            self.status_label.setText("⚪ Application arrêtée")
            self.status_label.setStyleSheet("color: #6b7280;")
            self.url_label.setText("🌐 URL: Non disponible")
            self.url_label.setStyleSheet("color: #6b7280;")
        elif status == "error":
            self.status_label.setText("🔴 Erreur")
            self.status_label.setStyleSheet("color: #ef4444;")
    
    def log(self, message):
        """Ajoute un message à la console"""
        timestamp = time.strftime("%H:%M:%S")
        self.console.append(f"[{timestamp}] {message}")
        self.console.moveCursor(QTextCursor.End)
    
    def quit_app(self):
        """Quitte complètement l'application"""
        if self.streamlit_thread and self.streamlit_thread.running:
            reply = self.confirm_quit()
            if not reply:
                return
            self.stop_app()
        
        self.tray_icon.hide()
        QApplication.quit()
    
    def confirm_quit(self):
        """Demande confirmation avant de quitter"""
        from PyQt5.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(
            self,
            "Confirmation",
            "L'application est en cours d'exécution.\nVoulez-vous vraiment quitter?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        return reply == QMessageBox.Yes
    
    def closeEvent(self, event):
        """Gère la fermeture de la fenêtre"""
        if self.streamlit_thread and self.streamlit_thread.running:
            event.ignore()
            self.hide()
            self.tray_icon.showMessage(
                "Gestion Financière Little",
                "L'application continue de fonctionner en arrière-plan",
                QSystemTrayIcon.Information,
                2000
            )
        else:
            event.accept()
    
    def get_stylesheet(self):
        """Retourne le CSS de l'application"""
        return """
            QMainWindow {
                background-color: #f9fafb;
            }
            
            QFrame#header {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #10b981,
                    stop:1 #059669
                );
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 10px;
            }
            
            QFrame#infoFrame {
                background-color: white;
                border: 2px solid #e5e7eb;
                border-radius: 12px;
                padding: 20px;
            }
            
            QPushButton {
                padding: 12px 24px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                border: none;
            }
            
            QPushButton#startButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #10b981,
                    stop:1 #059669
                );
                color: white;
            }
            
            QPushButton#startButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #059669,
                    stop:1 #047857
                );
            }
            
            QPushButton#startButton:disabled {
                background-color: #d1d5db;
                color: #9ca3af;
            }
            
            QPushButton#stopButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ef4444,
                    stop:1 #dc2626
                );
                color: white;
            }
            
            QPushButton#stopButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #dc2626,
                    stop:1 #b91c1c
                );
            }
            
            QPushButton#stopButton:disabled {
                background-color: #d1d5db;
                color: #9ca3af;
            }
            
            QPushButton#openButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3b82f6,
                    stop:1 #2563eb
                );
                color: white;
            }
            
            QPushButton#openButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2563eb,
                    stop:1 #1d4ed8
                );
            }
            
            QPushButton#openButton:disabled {
                background-color: #d1d5db;
                color: #9ca3af;
            }
            
            QPushButton#quitButton {
                background-color: #6b7280;
                color: white;
            }
            
            QPushButton#quitButton:hover {
                background-color: #4b5563;
            }
            
            QLabel {
                color: #1f2937;
            }
        """


def main():
    """Fonction principale"""
    app = QApplication(sys.argv)
    app.setApplicationName("Gestion Financière Little")
    app.setStyle("Fusion")
    
    launcher = GestioLauncher()
    launcher.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
