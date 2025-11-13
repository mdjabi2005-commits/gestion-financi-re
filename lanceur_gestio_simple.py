#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 Lanceur Simple - Gestion Financière Little
Lanceur avec Tkinter (pas besoin d'installer PyQt5)
"""

import sys
import os
import subprocess
import webbrowser
import threading
import time
import socket
from pathlib import Path
import tkinter as tk
from tkinter import scrolledtext, messagebox
from tkinter import ttk


class GestioLauncherSimple:
    """Lanceur simple avec Tkinter"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("🚀 Gestion Financière Little - Lanceur")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        self.process = None
        self.running = False
        self.app_url = None
        self.script_path = self.find_script()
        
        self.setup_ui()
        self.log("✨ Bienvenue dans le lanceur de Gestion Financière Little")
        self.log(f"📂 Script: {self.script_path}")
        
        if not self.script_path.exists():
            self.log("⚠️ ATTENTION: Le script n'existe pas encore!")
            self.log(f"   Veuillez placer votre script dans: {self.script_path}")
    
    def find_script(self):
        """Trouve le script gestiov4"""
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
        
        return current_dir / "gestiov4_corrige.py"
    
    def setup_ui(self):
        """Configure l'interface utilisateur"""
        # Style
        style = ttk.Style()
        style.theme_use('clam')
        
        # === EN-TÊTE ===
        header_frame = tk.Frame(self.root, bg="#10b981", height=120)
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text="💰 Gestion Financière Little",
            font=("Segoe UI", 24, "bold"),
            bg="#10b981",
            fg="white"
        )
        title_label.pack(pady=15)
        
        subtitle_label = tk.Label(
            header_frame,
            text="Lanceur d'application professionnel",
            font=("Segoe UI", 12),
            bg="#10b981",
            fg="#f0fdf4"
        )
        subtitle_label.pack()
        
        # === INFORMATIONS ===
        info_frame = tk.Frame(self.root, bg="white", relief=tk.RIDGE, bd=2)
        info_frame.pack(fill=tk.X, padx=20, pady=20)
        
        self.status_label = tk.Label(
            info_frame,
            text="⚪ Application arrêtée",
            font=("Segoe UI", 14, "bold"),
            bg="white",
            fg="#6b7280"
        )
        self.status_label.pack(pady=10)
        
        self.script_label = tk.Label(
            info_frame,
            text=f"📂 Script: {self.script_path.name}",
            font=("Segoe UI", 10),
            bg="white",
            fg="#374151"
        )
        self.script_label.pack(pady=5)
        
        self.url_label = tk.Label(
            info_frame,
            text="🌐 URL: Non disponible",
            font=("Segoe UI", 10),
            bg="white",
            fg="#6b7280"
        )
        self.url_label.pack(pady=5)
        
        # === BOUTONS DE CONTRÔLE ===
        buttons_frame = tk.Frame(self.root, bg="#f9fafb")
        buttons_frame.pack(fill=tk.X, padx=20, pady=10)
        
        button_style = {
            "font": ("Segoe UI", 11, "bold"),
            "width": 20,
            "height": 2,
            "relief": tk.FLAT,
            "cursor": "hand2"
        }
        
        self.start_btn = tk.Button(
            buttons_frame,
            text="▶️ Démarrer",
            command=self.start_app,
            bg="#10b981",
            fg="white",
            activebackground="#059669",
            **button_style
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = tk.Button(
            buttons_frame,
            text="⏹️ Arrêter",
            command=self.stop_app,
            bg="#ef4444",
            fg="white",
            activebackground="#dc2626",
            state=tk.DISABLED,
            **button_style
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.open_btn = tk.Button(
            buttons_frame,
            text="🌐 Ouvrir navigateur",
            command=self.open_browser,
            bg="#3b82f6",
            fg="white",
            activebackground="#2563eb",
            state=tk.DISABLED,
            **button_style
        )
        self.open_btn.pack(side=tk.LEFT, padx=5)
        
        # === CONSOLE ===
        console_frame = tk.Frame(self.root, bg="#f9fafb")
        console_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        console_label = tk.Label(
            console_frame,
            text="📋 Console",
            font=("Segoe UI", 11, "bold"),
            bg="#f9fafb",
            fg="#1f2937"
        )
        console_label.pack(anchor=tk.W, pady=(0, 5))
        
        self.console = scrolledtext.ScrolledText(
            console_frame,
            font=("Consolas", 9),
            bg="#1f2937",
            fg="#10b981",
            insertbackground="white",
            wrap=tk.WORD,
            relief=tk.RIDGE,
            bd=2
        )
        self.console.pack(fill=tk.BOTH, expand=True)
        
        # === BOUTON QUITTER ===
        quit_btn = tk.Button(
            self.root,
            text="❌ Quitter",
            command=self.quit_app,
            bg="#6b7280",
            fg="white",
            activebackground="#4b5563",
            font=("Segoe UI", 11, "bold"),
            width=20,
            height=2,
            relief=tk.FLAT,
            cursor="hand2"
        )
        quit_btn.pack(pady=10)
    
    def find_free_port(self, start_port=8501):
        """Trouve un port libre"""
        for port in range(start_port, start_port + 10):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(('localhost', port))
                    return port
                except OSError:
                    continue
        return start_port
    
    def start_app(self):
        """Démarre l'application"""
        if not self.script_path.exists():
            self.log("❌ Erreur: Le script n'existe pas!")
            messagebox.showerror("Erreur", f"Le script n'existe pas:\n{self.script_path}")
            return
        
        if self.running:
            self.log("⚠️ L'application est déjà en cours")
            return
        
        self.log("🚀 Démarrage de l'application...")
        
        # Trouver un port libre
        port = self.find_free_port()
        self.log(f"🌐 Port utilisé: {port}")
        
        # Démarrer dans un thread séparé
        thread = threading.Thread(target=self._run_streamlit, args=(port,), daemon=True)
        thread.start()
        
        # Mettre à jour l'UI
        self.start_btn.config(state=tk.DISABLED, bg="#d1d5db")
        self.stop_btn.config(state=tk.NORMAL, bg="#ef4444")
        self.update_status("🟢 Application en cours d'exécution", "#10b981")
    
    def _run_streamlit(self, port):
        """Exécute Streamlit (dans un thread)"""
        cmd = [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(self.script_path),
            f"--server.port={port}",
            "--server.headless=true",
            "--browser.gatherUsageStats=false"
        ]
        
        try:
            self.running = True
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            url_opened = False
            for line in self.process.stdout:
                if not self.running:
                    break
                
                line = line.strip()
                if line:
                    self.log(line)
                    
                    # Détecter quand Streamlit est prêt
                    if ("You can now view" in line or "Local URL:" in line) and not url_opened:
                        self.app_url = f"http://localhost:{port}"
                        self.root.after(0, self.on_app_ready)
                        url_opened = True
            
            self.process.wait()
            
        except Exception as e:
            self.log(f"❌ Erreur: {e}")
        finally:
            self.running = False
            self.root.after(0, self.on_app_stopped)
    
    def on_app_ready(self):
        """Appelé quand l'app est prête"""
        self.url_label.config(text=f"🌐 URL: {self.app_url}", fg="#10b981")
        self.open_btn.config(state=tk.NORMAL, bg="#3b82f6")
        self.log(f"✅ Application prête: {self.app_url}")
        
        # Ouvrir automatiquement après 2 secondes
        self.root.after(2000, self.open_browser)
    
    def on_app_stopped(self):
        """Appelé quand l'app s'arrête"""
        self.update_status("⚪ Application arrêtée", "#6b7280")
        self.url_label.config(text="🌐 URL: Non disponible", fg="#6b7280")
        self.start_btn.config(state=tk.NORMAL, bg="#10b981")
        self.stop_btn.config(state=tk.DISABLED, bg="#d1d5db")
        self.open_btn.config(state=tk.DISABLED, bg="#d1d5db")
        self.app_url = None
    
    def stop_app(self):
        """Arrête l'application"""
        if not self.running:
            return
        
        self.log("⏹️ Arrêt de l'application...")
        self.running = False
        
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None
    
    def open_browser(self):
        """Ouvre le navigateur"""
        if self.app_url:
            webbrowser.open(self.app_url)
            self.log(f"🌐 Ouverture de {self.app_url}")
        else:
            self.log("⚠️ URL non disponible")
    
    def quit_app(self):
        """Quitte l'application"""
        if self.running:
            if messagebox.askyesno("Confirmation", 
                                   "L'application est en cours.\nVoulez-vous vraiment quitter?"):
                self.stop_app()
                self.root.quit()
        else:
            self.root.quit()
    
    def update_status(self, text, color):
        """Met à jour le statut"""
        self.status_label.config(text=text, fg=color)
    
    def log(self, message):
        """Ajoute un message à la console"""
        timestamp = time.strftime("%H:%M:%S")
        self.console.insert(tk.END, f"[{timestamp}] {message}\n")
        self.console.see(tk.END)
        self.console.update()


def main():
    """Fonction principale"""
    root = tk.Tk()
    app = GestioLauncherSimple(root)
    root.mainloop()


if __name__ == "__main__":
    main()
