# -*- coding: utf-8 -*-
"""
Created on Tue Nov 11 17:16:10 2025

@author: djabi
"""

from difflib import get_close_matches
import os
import shutil
import sqlite3
import pandas as pd
import pytesseract 
from PIL import Image
import re
import streamlit as st
from datetime import datetime, date, timedelta
from dateutil import parser
from dateutil.relativedelta import relativedelta
from alpha_vantage.timeseries import TimeSeries
import matplotlib.pyplot as plt
import cv2
import numpy as np
from io import BytesIO
from pathlib import Path
from chardet import detect
import logging
import json
import streamlit.components.v1 as components
import plotly.express as px
import plotly.graph_objects as go


# ==============================
# 📄 Configuration Streamlit
# ==============================
st.set_page_config(layout="wide")
st.markdown("""
    <style>
    div[data-testid="stDataFrame"] div[role="gridcell"] {
        font-size: 16px !important;
        padding: 8px !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==============================
# 📂 CONFIGURATION DES DOSSIERS
# ==============================
from config import BASE_DIR, DATA_DIR, DB_PATH, TO_SCAN_DIR, SORTED_DIR, REVENUS_A_TRAITER, REVENUS_TRAITES

# Créer les dossiers de logs OCR
OCR_LOGS_DIR = os.path.join(DATA_DIR, "ocr_logs")
os.makedirs(OCR_LOGS_DIR, exist_ok=True)

LOG_PATH = os.path.join(OCR_LOGS_DIR, "pattern_log.json")
OCR_PERFORMANCE_LOG = os.path.join(OCR_LOGS_DIR, "performance_stats.json")
PATTERN_STATS_LOG = os.path.join(OCR_LOGS_DIR, "pattern_stats.json")
OCR_SCAN_LOG = os.path.join(OCR_LOGS_DIR, "scan_history.jsonl")

# === JOURNAL OCR ===
def log_pattern_occurrence(pattern_name: str):
    """Enregistre chaque mot-clé détecté par l'OCR dans un journal JSON."""
    try:
        data = {}
        if os.path.exists(LOG_PATH):
            with open(LOG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        data[pattern_name] = data.get(pattern_name, 0) + 1
        with open(LOG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[OCR-LOG] Erreur journalisation : {e}")

def log_ocr_scan(document_type: str, filename: str, montants_detectes: list, montant_choisi: float,
                 categorie: str, sous_categorie: str, patterns_detectes: list = None, success_level: str = "exact"):
    """
    Enregistre un scan OCR complet avec son résultat.

    Args:
        document_type: "ticket" ou "revenu"
        filename: nom du fichier scanné
        montants_detectes: liste des montants trouvés par l'OCR
        montant_choisi: montant finalement choisi par l'utilisateur
        categorie: catégorie de la transaction
        sous_categorie: sous-catégorie de la transaction
        patterns_detectes: liste des patterns détectés (optionnel)
        success_level: "exact" (montant exact détecté), "partial" (dans la liste), "failed" (corrigé manuellement)
    """
    try:
        print(f"[OCR-LOG] Début enregistrement : {filename}, type={document_type}, success={success_level}")

        # 1. Enregistrer dans l'historique (JSONL)
        scan_entry = {
            "timestamp": datetime.now().isoformat(),
            "document_type": document_type,
            "filename": filename,
            "montants_detectes": [float(m) for m in montants_detectes] if montants_detectes else [],
            "montant_choisi": float(montant_choisi),
            "categorie": categorie,
            "sous_categorie": sous_categorie,
            "patterns_detectes": patterns_detectes or [],
            "success_level": success_level,
            "result": {
                "success": success_level in ["exact", "partial"]
            },
            "extraction": {
                "montant_final": float(montant_choisi),
                "categorie_final": categorie
            }
        }

        print(f"[OCR-LOG] Écriture dans {OCR_SCAN_LOG}")
        with open(OCR_SCAN_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(scan_entry, ensure_ascii=False) + "\n")
        print(f"[OCR-LOG] Historique enregistre")

        # 2. Mettre à jour les statistiques de performance
        print(f"[OCR-LOG] Mise à jour performance stats...")
        update_performance_stats(document_type, success_level)

        # 3. Mettre à jour les statistiques par pattern
        if patterns_detectes:
            print(f"[OCR-LOG] Mise à jour pattern stats ({len(patterns_detectes)} patterns)...")
            update_pattern_stats(patterns_detectes, success_level)

        print(f"[OCR-LOG] Log OCR termine avec succes")

    except Exception as e:
        logger.error(f"[OCR-LOG] Erreur lors de l'enregistrement du scan : {e}")
        print(f"[OCR-LOG] ERREUR : {e}")
        import traceback
        traceback.print_exc()

def update_performance_stats(document_type: str, success_level: str):
    """Met à jour les statistiques de performance globales."""
    try:
        # Charger les stats existantes
        stats = {}
        if os.path.exists(OCR_PERFORMANCE_LOG):
            with open(OCR_PERFORMANCE_LOG, "r", encoding="utf-8") as f:
                stats = json.load(f)

        # Initialiser si nécessaire
        if document_type not in stats:
            stats[document_type] = {
                "total": 0,
                "success": 0,
                "partial": 0,
                "failed": 0,
                "success_rate": 0.0,
                "correction_rate": 0.0
            }

        # Mettre à jour
        stats[document_type]["total"] += 1
        if success_level == "exact":
            stats[document_type]["success"] += 1
        elif success_level == "partial":
            stats[document_type]["partial"] += 1
        else:
            stats[document_type]["failed"] += 1

        # Calculer les taux
        total = stats[document_type]["total"]
        stats[document_type]["success_rate"] = (stats[document_type]["success"] / total * 100) if total > 0 else 0
        stats[document_type]["correction_rate"] = (stats[document_type]["failed"] / total * 100) if total > 0 else 0

        # Ajouter timestamp de mise à jour
        stats["last_updated"] = datetime.now().isoformat()

        # Sauvegarder
        with open(OCR_PERFORMANCE_LOG, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)

    except Exception as e:
        logger.error(f"[OCR-LOG] Erreur mise à jour performance : {e}")

def update_pattern_stats(patterns_detectes: list, success_level: str):
    """Met à jour les statistiques par pattern."""
    try:
        # Charger les stats existantes
        stats = {}
        if os.path.exists(PATTERN_STATS_LOG):
            with open(PATTERN_STATS_LOG, "r", encoding="utf-8") as f:
                stats = json.load(f)

        # Mettre à jour chaque pattern
        for pattern in patterns_detectes:
            if pattern not in stats:
                stats[pattern] = {
                    "total_detections": 0,
                    "success_count": 0,
                    "partial_count": 0,
                    "failure_count": 0,
                    "success_rate": 0.0,
                    "reliability_score": 0.0
                }

            stats[pattern]["total_detections"] += 1

            if success_level == "exact":
                stats[pattern]["success_count"] += 1
            elif success_level == "partial":
                stats[pattern]["partial_count"] += 1
            else:
                stats[pattern]["failure_count"] += 1

            # Calculer taux de succès
            total = stats[pattern]["total_detections"]
            success = stats[pattern]["success_count"] + stats[pattern]["partial_count"]
            stats[pattern]["success_rate"] = (success / total * 100) if total > 0 else 0

            # Score de fiabilité (pondéré par nombre de détections)
            weight = min(total / 10, 1.0)
            stats[pattern]["reliability_score"] = stats[pattern]["success_rate"] * weight

        # Sauvegarder
        with open(PATTERN_STATS_LOG, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)

    except Exception as e:
        logger.error(f"[OCR-LOG] Erreur mise à jour patterns : {e}")

def determine_success_level(montants_detectes: list, montant_choisi: float) -> str:
    """
    Détermine le niveau de succès de la détection OCR.

    Returns:
        "exact" : Le montant choisi est le premier de la liste (succès total)
        "partial" : Le montant choisi est dans la liste mais pas le premier (succès partiel)
        "failed" : Le montant choisi n'est pas dans la liste (échec)
    """
    if not montants_detectes:
        return "failed"

    # Arrondir pour comparaison
    montants_arrondis = [round(float(m), 2) for m in montants_detectes]
    montant_choisi_arrondi = round(float(montant_choisi), 2)

    if montants_arrondis and montants_arrondis[0] == montant_choisi_arrondi:
        return "exact"
    elif montant_choisi_arrondi in montants_arrondis:
        return "partial"
    else:
        return "failed"

def show_toast(message: str, toast_type="success", duration=3000):
    """
    Affiche une notification toast professionnelle.
    
    Args:
        message (str): Message à afficher
        toast_type (str): Type de toast - 'success', 'warning', 'error'
        duration (int): Durée en millisecondes (défaut: 3000ms)
    """
    # Définir couleur et icône selon le type
    toast_config = {
        "success": {"color": "#10b981", "icon": "✅", "bg_light": "#d1fae5"},
        "warning": {"color": "#f59e0b", "icon": "⚠️", "bg_light": "#fef3c7"},
        "error": {"color": "#ef4444", "icon": "❌", "bg_light": "#fee2e2"}
    }
    
    config = toast_config.get(toast_type, toast_config["success"])
    
    components.html(f"""
        <div style="
            position:fixed;
            bottom:30px;right:30px;
            background:linear-gradient(135deg, {config['color']} 0%, {config['bg_light']} 100%);
            color:#1f2937;
            padding:12px 24px;
            border-radius:12px;
            font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
            font-weight:600;
            box-shadow:0 4px 20px rgba(0,0,0,0.15);
            border-left:4px solid {config['color']};
            z-index:9999;
            animation:slideIn 0.3s ease-out, fadeOut {duration/1000}s {(duration-1000)/1000}s forwards;">
            <span style="font-size:18px;margin-right:8px;">{config['icon']}</span>
            {message}
        </div>
        <style>
        @keyframes slideIn {{
          from {{
            transform: translateX(400px);
            opacity: 0;
          }}
          to {{
            transform: translateX(0);
            opacity: 1;
          }}
        }}
        @keyframes fadeOut {{
          0% {{opacity:1;}}
          100% {{opacity:0;visibility:hidden;}}
        }}
        </style>
    """, height=80)

def toast_success(message: str, duration=3000):
    """Toast de succès rapide"""
    show_toast(message, "success", duration)

def toast_warning(message: str, duration=3000):
    """Toast d'avertissement rapide"""
    show_toast(message, "warning", duration)

def toast_error(message: str, duration=3000):
    """Toast d'erreur rapide"""
    show_toast(message, "error", duration)

@st.cache_data(ttl=300)
def load_transactions(sort_by="date", ascending=False):
    """
    Charge toutes les transactions depuis la base SQLite avec tri et conversions sécurisées.
    
    Args:
        sort_by (str): Colonne de tri ('date' ou 'montant')
        ascending (bool): Ordre croissant (True) ou décroissant (False)
    
    Returns:
        pd.DataFrame: DataFrame trié avec conversions sécurisées appliquées
    """
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM transactions", conn)
    conn.close()
    
    if df.empty:
        return df
    
    # 🔥 CONVERSIONS SÉCURISÉES
    df["montant"] = df["montant"].apply(lambda x: safe_convert(x, float, 0.0))
    df["date"] = df["date"].apply(lambda x: safe_date_convert(x))
    
    # Conversion pour pandas
    df["date"] = pd.to_datetime(df["date"])
    
    # 🔥 TRI PAR DÉFAUT : Plus récent en premier
    df = df.sort_values(by=sort_by, ascending=ascending)
    
    return df

@st.cache_data(ttl=300)
def load_recurrent_transactions():
    """
    Charge uniquement les transactions récurrentes automatiques avec conversions sécurisées.
    
    Returns:
        pd.DataFrame: DataFrame des récurrences trié par date (plus récent en premier)
    """
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM transactions WHERE source='récurrente_auto'", conn)
    conn.close()
    
    if df.empty:
        return df
    
    # 🔥 CONVERSIONS SÉCURISÉES
    df["montant"] = df["montant"].apply(lambda x: safe_convert(x, float, 0.0))
    df["date"] = df["date"].apply(lambda x: safe_date_convert(x))
    
    # Conversion pour pandas
    df["date"] = pd.to_datetime(df["date"])
    
    # Tri par date décroissante
    df = df.sort_values(by="date", ascending=False)
    
    return df

def refresh_and_rerun():
    """
    Vide le cache des données et recharge la page.
    À utiliser après toute modification de données (ajout, suppression, modification).
    """
    st.cache_data.clear()
    st.rerun()


# ==============================
# 🛡️ CONFIGURATION LOGGING V2
# ==============================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("gestio_app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==============================
# 🔧 FONCTIONS UTILITAIRES (à adapter selon votre implémentation)
# ==============================

def get_ocr_performance_report():
    """Récupère le rapport de performance depuis les fichiers locaux."""
    # À adapter selon votre structure
    try:
        if os.path.exists(OCR_PERFORMANCE_LOG):
            with open(OCR_PERFORMANCE_LOG, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {}

def get_best_patterns(min_detections, min_success_rate):
    """Récupère les meilleurs patterns."""
    # À adapter selon votre structure
    try:
        if os.path.exists(PATTERN_STATS_LOG):
            with open(PATTERN_STATS_LOG, 'r', encoding='utf-8') as f:
                stats = json.load(f)
                # Filtrer et retourner
                return [
                    {
                        'pattern': k,
                        'success_rate': v.get('success_rate', 0),
                        'reliability_score': v.get('reliability_score', 0),
                        'detections': v.get('total_detections', 0),
                        'corrections': v.get('correction_count', 0)
                    }
                    for k, v in stats.items()
                    if v.get('total_detections', 0) >= min_detections
                    and v.get('success_rate', 0) >= min_success_rate
                ]
    except:
        pass
    return []

def get_worst_patterns(min_detections, max_success_rate):
    """Récupère les patterns problématiques."""
    # À adapter selon votre structure
    try:
        if os.path.exists(PATTERN_STATS_LOG):
            with open(PATTERN_STATS_LOG, 'r', encoding='utf-8') as f:
                stats = json.load(f)
                return [
                    {
                        'pattern': k,
                        'success_rate': v.get('success_rate', 0),
                        'detections': v.get('total_detections', 0),
                        'corrections': v.get('correction_count', 0)
                    }
                    for k, v in stats.items()
                    if v.get('total_detections', 0) >= min_detections
                    and v.get('success_rate', 0) <= max_success_rate
                ]
    except:
        pass
    return []

def get_scan_history(document_type=None, limit=100):
    """Récupère l'historique des scans."""
    # À adapter selon votre structure
    try:
        if os.path.exists(OCR_SCAN_LOG):
            scans = []
            with open(OCR_SCAN_LOG, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        scan = json.loads(line)
                        if document_type is None or scan.get('document_type') == document_type:
                            scans.append(scan)
                    except:
                        continue
            return scans[:limit]
    except:
        pass
    return []

# ==============================
# 🔍 FONCTIONS D'ANALYSE AVANCÉES
# ==============================

def analyze_external_log(uploaded_file):
    """
    Analyse un fichier de log externe uploadé par un utilisateur.
    Supporte JSON, JSONL et TXT.
    """
    try:
        content = uploaded_file.read()
        
        if uploaded_file.name.endswith('.jsonl'):
            # Format JSONL (une ligne JSON par scan)
            lines = content.decode('utf-8').split('\n')
            scans = []
            for line in lines:
                if line.strip():
                    try:
                        scans.append(json.loads(line))
                    except:
                        continue
            return scans
        
        elif uploaded_file.name.endswith('.json'):
            # Format JSON standard
            data = json.loads(content)
            
            # Si c'est un pattern_log.json (simple compteur)
            if isinstance(data, dict) and all(isinstance(v, (int, float)) for v in data.values()):
                return {"type": "pattern_counts", "data": data}
            
            # Si c'est un scan_history ou performance log
            return data if isinstance(data, list) else [data]
        
        else:
            # Format texte, essayer de parser
            text = content.decode('utf-8')
            # Tentative d'extraction de patterns depuis du texte brut
            patterns = extract_patterns_from_text(text)
            return {"type": "raw_text", "patterns": patterns, "content": text}
    
    except Exception as e:
        st.error(f"Erreur lors de l'analyse du fichier : {e}")
        return None

def extract_patterns_from_text(text):
    """Extrait les patterns reconnus depuis un texte brut."""
    patterns = []
    
    # Patterns de tickets
    ticket_patterns = [
        'total', 'montant', 'ttc', 'cb', 'carte', 'espèces', 'esp',
        'carrefour', 'auchan', 'leclerc', 'lidl', 'intermarché', 
        'restaurant', 'boulangerie', 'pharmacie'
    ]
    
    # Patterns de revenus
    revenu_patterns = [
        'salaire', 'net', 'brut', 'paie', 'bulletin', 'mensuel',
        'cotisations', 'sécurité sociale', 'retraite', 'prélèvement'
    ]
    
    text_lower = text.lower()
    
    for pattern in ticket_patterns + revenu_patterns:
        if pattern in text_lower:
            count = text_lower.count(pattern)
            patterns.append({
                'pattern': pattern,
                'count': count,
                'type': 'ticket' if pattern in ticket_patterns else 'revenu'
            })
    
    return patterns

def calculate_pattern_reliability(pattern_data):
    """Calcule la fiabilité d'un pattern basé sur ses stats."""
    if isinstance(pattern_data, dict):
        total = pattern_data.get('total_detections', 0)
        success = pattern_data.get('success_count', 0)
        
        if total == 0:
            return 0
        
        success_rate = success / total
        # Pondération par nombre de détections (max à 10)
        weight = min(total / 10, 1.0)
        
        return success_rate * weight * 100
    return 0

def diagnose_ocr_patterns(scans_data):
    """
    Diagnostic complet des patterns OCR.
    Retourne des recommandations d'amélioration.
    """
    diagnostics = {
        'total_scans': 0,
        'success_rate': 0,
        'problematic_patterns': [],
        'reliable_patterns': [],
        'recommendations': []
    }
    
    if not scans_data:
        return diagnostics
    
    # Analyse selon le type de données
    if isinstance(scans_data, dict) and scans_data.get('type') == 'pattern_counts':
        # Analyse simple des compteurs
        patterns = scans_data['data']
        diagnostics['total_patterns'] = len(patterns)
        diagnostics['most_common'] = sorted(patterns.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Recommandations basiques
        if len(patterns) < 10:
            diagnostics['recommendations'].append("⚠️ Peu de patterns détectés. Enrichir la base de patterns.")
        
    elif isinstance(scans_data, list):
        # Analyse complète des scans
        diagnostics['total_scans'] = len(scans_data)
        
        pattern_stats = {}
        for scan in scans_data:
            if 'patterns_detected' in scan:
                for pattern in scan['patterns_detected']:
                    if pattern not in pattern_stats:
                        pattern_stats[pattern] = {
                            'detections': 0,
                            'successes': 0,
                            'failures': 0
                        }
                    
                    pattern_stats[pattern]['detections'] += 1
                    
                    if scan.get('result', {}).get('success'):
                        pattern_stats[pattern]['successes'] += 1
                    else:
                        pattern_stats[pattern]['failures'] += 1
        
        # Identifier patterns problématiques et fiables
        for pattern, stats in pattern_stats.items():
            success_rate = stats['successes'] / stats['detections'] if stats['detections'] > 0 else 0
            
            if success_rate < 0.5 and stats['detections'] >= 3:
                diagnostics['problematic_patterns'].append({
                    'pattern': pattern,
                    'success_rate': success_rate * 100,
                    'detections': stats['detections']
                })
            
            if success_rate > 0.7 and stats['detections'] >= 5:
                diagnostics['reliable_patterns'].append({
                    'pattern': pattern,
                    'success_rate': success_rate * 100,
                    'detections': stats['detections']
                })
        
        # Calcul taux de succès global
        total_success = sum(1 for scan in scans_data if scan.get('result', {}).get('success'))
        diagnostics['success_rate'] = (total_success / len(scans_data) * 100) if scans_data else 0
        
        # Recommandations spécifiques
        if diagnostics['success_rate'] < 50:
            diagnostics['recommendations'].append("❌ Taux de succès faible. Revoir la logique d'extraction.")
        
        if diagnostics['problematic_patterns']:
            diagnostics['recommendations'].append(
                f"⚠️ {len(diagnostics['problematic_patterns'])} patterns problématiques à corriger"
            )
        
        if not diagnostics['reliable_patterns']:
            diagnostics['recommendations'].append("💡 Aucun pattern fiable identifié. Améliorer la détection.")
    
    return diagnostics


# ==============================
# 🛡️ FONCTIONS DE SÉCURITÉ V2
# ==============================

def safe_convert(value, convert_type=float, default=0.0):
    """
    Conversion sécurisée des valeurs avec gestion d'erreurs robuste
    """
    try:
        if pd.isna(value) or value is None or str(value).strip() == "":
            return default
            
        value_str = str(value).strip()
        
        if convert_type == float:
            # Nettoyage complet pour les montants
            value_str = value_str.replace(' ', '').replace('€', '').replace('"', '').replace("'", "")
            # Gestion virgule/point
            if ',' in value_str and '.' in value_str:
                value_str = value_str.replace(',', '')
            else:
                value_str = value_str.replace(',', '.')
            
            value_str = re.sub(r'[^\d.-]', '', value_str)
            
            result = float(value_str)
            return round(result, 2)
            
        elif convert_type == int:
            return int(float(value_str))
        elif convert_type == str:
            return value_str
        else:
            return convert_type(value)
            
    except (ValueError, TypeError, AttributeError) as e:
        logger.warning(f"Conversion failed for value '{value}': {e}")
        return default

def safe_date_convert(date_str, default=None):
    """
    Conversion sécurisée des dates avec multiples formats
    """
    if default is None:
        default = datetime.now().date()
    
    if pd.isna(date_str) or date_str is None or str(date_str).strip() == "":
        return default
        
    date_str = str(date_str).strip()
    
    formats = [
        "%Y-%m-%d", "%d/%m/%Y", "%d/%m/%y", 
        "%Y/%m/%d", "%d-%m-%Y", "%d-%m-%y",
        "%d.%m.%Y", "%d.%m.%y"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    
    try:
        return parser.parse(date_str, dayfirst=True, fuzzy=True).date()
    except:
        logger.warning(f"Date conversion failed for '{date_str}', using default")
        return default

def validate_transaction_data(transaction):
    """
    Validation complète des données transaction
    """
    errors = []
    
    if transaction.get('type') not in ['revenu', 'dépense']:
        errors.append("Type must be 'revenu' or 'dépense'")
    
    if not transaction.get('categorie') or not str(transaction['categorie']).strip():
        errors.append("Catégorie is required")
    
    montant = safe_convert(transaction.get('montant', 0))
    if montant <= 0:
        errors.append("Montant must be positive")
    
    date_val = safe_date_convert(transaction.get('date'))
    if date_val > datetime.now().date():
        errors.append("Date cannot be in the future")
    
    return errors
#faire une fonction générique quip permet d'appliquer une taxe
def apply_uber_tax(categorie, montant_brut, description=""):
    """
    Applique automatiquement la réduction de 21% pour les revenus Uber
    """
    categorie_lower = str(categorie).lower().strip()
    description_lower = str(description).lower().strip()
    
    uber_keywords = ['uber', 'uber eats', 'livraison', 'driver', 'delivery']
    is_uber_revenu = any(keyword in categorie_lower for keyword in uber_keywords) or \
                    any(keyword in description_lower for keyword in uber_keywords)
    
    if is_uber_revenu and montant_brut > 0:
        montant_net = round(montant_brut * 0.79, 2)
        tax_amount = round(montant_brut - montant_net, 2)
        
        message = f"""
        🚗 **Revenu Uber détecté** - Application automatique de la fiscalité :
        - Montant brut : {montant_brut:.2f}€
        - Prélèvement fiscal (21%) : -{tax_amount:.2f}€  
        - **Montant net : {montant_net:.2f}€**
        """
        
        logger.info(f"Uber tax applied: {montant_brut}€ → {montant_net}€")
        return montant_net, message
    
    return montant_brut, ""

def process_uber_revenue(transaction):
    """
    Traitement spécialisé pour les revenus Uber
    """
    montant_initial = safe_convert(transaction.get('montant', 0))
    categorie = transaction.get('categorie', '')
    
    montant_final, tax_message = apply_uber_tax(categorie, montant_initial, 
                                              transaction.get('description', ''))
    
    transaction['montant'] = montant_final
    
    if 'uber' not in categorie.lower():
        transaction['categorie'] = 'Uber Eats'
    
    return transaction, tax_message

def get_db_connection():
    """Retourne une connexion SQLite cohérente avec DB_PATH."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON")  #Bloquer les clès étrangères
        return conn
    except sqlite3.Error as e:
        logger.error(f"Database connection failed: {e}")
        toast_error("Erreur de connexion à la base de données")
        raise

def init_db():
    """Initialise ou met à jour la base de données SQLite avec la table 'transactions'."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Créer la table avec le bon schéma
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            categorie TEXT,
            sous_categorie TEXT,
            description TEXT,
            montant REAL,
            date TEXT,
            source TEXT,
            recurrence TEXT,
            date_fin TEXT
        )
    """)
    
    # 🔄 Mettre à jour la table si elle existe avec l'ancien schéma
    try:
        cursor.execute("ALTER TABLE transactions ADD COLUMN source TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass  # La colonne existe déjà
    
    try:
        cursor.execute("ALTER TABLE transactions ADD COLUMN recurrence TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute("ALTER TABLE transactions ADD COLUMN date_fin TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass
    
    conn.commit()
    conn.close()

def migrate_database_schema():
    """Migre le schéma de la base de données vers les nouveaux noms de colonnes"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Vérifier si la table existe avec l'ancien schéma
        cursor.execute("PRAGMA table_info(transactions)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Si les anciennes colonnes existent, on migre
        if "Catégorie" in columns or "Sous-catégorie" in columns:
            logger.info("Migration du schema de la base de donnees...")
            
            # Créer une nouvelle table avec le bon schéma
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT,
                    categorie TEXT,
                    sous_categorie TEXT,
                    description TEXT,
                    montant REAL,
                    date TEXT,
                    source TEXT,
                    recurrence TEXT,
                    date_fin TEXT
                )
            """)
            
            # Copier les données en mappant les anciens noms vers les nouveaux
            cursor.execute("""
                INSERT INTO transactions_new 
                (id, type, categorie, sous_categorie, description, montant, date, source, recurrence, date_fin)
                SELECT 
                id, 
                type, 
                "Catégorie" AS categorie, 
                "Sous-catégorie" AS sous_categorie, 
                description, 
                montant, 
                "Date" AS date, 
                "Source" AS source, 
                "Récurrence" AS recurrence, 
                date_fin
                FROM transactions
            """)
            
            # Supprimer l'ancienne table
            cursor.execute("DROP TABLE transactions")
            
            # Renommer la nouvelle table
            cursor.execute("ALTER TABLE transactions_new RENAME TO transactions")

            logger.info("Migration terminee avec succes!")
        else:
            logger.info("Le schema est deja a jour")
            
    except Exception as e:
        logger.error(f"Erreur lors de la migration: {e}")
    finally:
        conn.commit()
        conn.close()

# Appeler la migration au démarrage
init_db()
migrate_database_schema()
###tous analyse le 11/11/2025
# ==============================
# 📁 Dictionnaire des mois
# ==============================
mois_dict = {
    "janvier": "01", "février": "02", "mars": "03", "avril": "04",
    "mai": "05", "juin": "06", "juillet": "07", "août": "08",
    "septembre": "09", "octobre": "10", "novembre": "11", "décembre": "12"
}
def numero_to_mois(num: str) -> str:
    for mois, numero in mois_dict.items():
        if numero == num:
            return mois
    return "inconnu"


# ==============================
# 🧠 OCR ET TRAITEMENT DE TICKET ET REVENU
# ==============================
def full_ocr(image_path: str, show_ticket: bool = False) -> str:
    """
    Effectue un OCR complet sur une image de ticket.
    Version robuste + option d'affichage du ticket dans Streamlit.
    """
    try:
        # --- Lecture robuste du fichier image ---
        image_data = np.fromfile(image_path, dtype=np.uint8)
        image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)

        if image is None:
            raise FileNotFoundError(f"Impossible de lire ou décoder l'image : {image_path}")

        # --- Prétraitement pour OCR ---
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (3, 3), 0)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        pil_img = Image.fromarray(thresh)

        # --- OCR MULTI-LANGUES (français + anglais) ---
        # Utilise fra+eng pour mieux reconnaître TOTAL, PAYMENT, AMOUNT, etc.
        text = pytesseract.image_to_string(pil_img, lang="fra+eng")
        text = text.replace("\x0c", "").strip()
        
        # Log les langues détectées pour statistiques
        if text:
            log_pattern_occurrence("ocr_success_fra+eng")

        # --- Option : affichage dans Streamlit ---
        if show_ticket:
            with st.expander(f"🧾 Aperçu du ticket : {os.path.basename(image_path)}", expanded=False):
                st.image(cv2.cvtColor(image, cv2.COLOR_BGR2RGB), caption=os.path.basename(image_path))
                if text:
                    st.text_area("Texte OCR détecté :", text, height=200)
                else:
                    toast_warning("Aucun texte détecté par l'OCR.")

        return text

    except Exception as e:
        logger.error(f"OCR error on {image_path}: {e}")
        toast_error("Erreur OCR sur {os.path.basename(image_path)} : {e}")
        show_toast(f"Erreur OCR: {os.path.basename(image_path)}", toast_type="error")
        return ""

def nettoyer_montant(montant_str):
    """
    Nettoie et convertit un montant en float
    Gère les virgules, espaces, symboles monétaires
    """
    return safe_convert(montant_str, float, 0.0)

# 🔥 FONCTIONS UTILITAIRES AMÉLIORÉES

def trouver_fichiers_associes(transaction, base_dirs=[SORTED_DIR, REVENUS_TRAITES]):
    """
    Trouve les fichiers (images/PDF) associés à une transaction basée sur:
    - Catégorie et sous-catégorie
    - Date (approximative)
    - Montant (approximatif)
    """
    fichiers_trouves = []
    
    categorie = transaction.get("categorie", "").strip()
    sous_categorie = transaction.get("sous_categorie", "").strip()
    date_transaction = transaction.get("date", "")
    montant = transaction.get("montant", 0.0)
    source = transaction.get("source", "")
    
    # Déterminer le dossier de recherche selon la source
    if source in ["OCR", "import_csv"] and "dépense" in transaction.get("type", ""):
        dossiers_recherche = [SORTED_DIR]
    elif source in ["PDF", "import_csv"] and "revenu" in transaction.get("type", ""):
        dossiers_recherche = [REVENUS_TRAITES]
    else:
        dossiers_recherche = base_dirs
    
    for base_dir in dossiers_recherche:
        if not os.path.exists(base_dir):
            continue
            
        # Construire le chemin attendu : base/categorie/sous_categorie/
        chemin_attendu = os.path.join(base_dir, categorie, sous_categorie)
        
        if os.path.exists(chemin_attendu):
            # Rechercher tous les fichiers dans le dossier
            for fichier in os.listdir(chemin_attendu):
                if fichier.lower().endswith(('.jpg', '.jpeg', '.png', '.pdf')):
                    chemin_complet = os.path.join(chemin_attendu, fichier)
                    
                    # Vérification supplémentaire par date (optionnelle)
                    if date_transaction:
                        try:
                            # Extraire la date du nom de fichier si possible
                            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', fichier)
                            if date_match:
                                date_fichier = date_match.group(1)
                                if date_fichier in date_transaction:
                                    fichiers_trouves.append(chemin_complet)
                                    continue
                        except:
                            pass
                    
                    # Si pas de correspondance par date, on l'ajoute quand même
                    fichiers_trouves.append(chemin_complet)
    
    return fichiers_trouves[:5]  # Limiter à 5 fichiers maximum

def get_badge_html(transaction):
    """Retourne le badge HTML pour une transaction"""
    source = transaction.get("source", "")
    type_transaction = transaction.get("type", "")
    
    if source == "OCR":
        badge = "🧾 Ticket"
        couleur = "#1f77b4"
        emoji = "🧾"
    elif source == "PDF":
        if type_transaction == "revenu":
            badge = "💼 Bulletin"
            couleur = "#2ca02c"
            emoji = "💼"
        else:
            badge = "📄 Facture"
            couleur = "#ff7f0e"
            emoji = "📄"
    elif source in ["manuel", "récurrente", "récurrente_auto"]:
        badge = "📝 Manuel"
        couleur = "#7f7f7f"
        emoji = "📝"
    else:
        badge = "📎 Autre"
        couleur = "#9467bd"
        emoji = "📎"
    
    return f"<span style='background-color: {couleur}; color: white; padding: 4px 12px; border-radius: 16px; font-size: 0.8em; font-weight: bold;'>{emoji} {badge}</span>"

def get_badge_icon(transaction):
    """Retourne juste l'emoji du badge"""
    source = transaction.get("source", "")
    type_transaction = transaction.get("type", "")
    
    if source == "OCR":
        return "🧾"
    elif source == "PDF":
        return "💼" if type_transaction == "revenu" else "📄"
    elif source in ["manuel", "récurrente", "récurrente_auto"]:
        return "📝"
    else:
        return "📎"

def afficher_carte_transaction(transaction, idx):
    """Affiche une carte détaillée pour la vue rapide"""
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.write(f"**Catégorie :** {transaction['categorie']}")
        st.write(f"**Sous-catégorie :** {transaction['sous_categorie']}")
        st.write(f"**Date :** {transaction['date']}")
        
        if transaction.get('description'):
            st.write(f"**Description :** {transaction['description']}")
            
        if transaction.get('recurrence'):
            st.write(f"**Récurrence :** {transaction['recurrence']}")
    
    with col2:
        montant_color = "green" if transaction['type'] == 'revenu' else "red"
        montant_prefix = "+" if transaction['type'] == 'revenu' else "-"
        st.markdown(f"<h2 style='color: {montant_color}; text-align: center;'>{montant_prefix}{transaction['montant']:.2f} €</h2>", unsafe_allow_html=True)
        
        # Afficher automatiquement les documents si disponibles
        if transaction['source'] in ['OCR', 'PDF']:
            st.markdown("---")
            st.markdown("**📎 Documents :**")
            afficher_documents_associes(transaction.to_dict())

def afficher_documents_associes(transaction):
    """Affiche les documents associés à une transaction de façon améliorée"""
    fichiers = trouver_fichiers_associes(transaction)
    
    if not fichiers:
        source = transaction.get("source", "")
        type_transaction = transaction.get("type", "")
        
        if source == "OCR":
            st.warning("🧾 Aucun ticket de caisse trouvé dans les dossiers")
        elif source == "PDF":
            if type_transaction == "revenu":
                st.warning("💼 Aucun bulletin de paie trouvé")
            else:
                st.warning("📄 Aucune facture trouvée")
        else:
            st.info("📝 Aucun document associé")
        return

    # Afficher chaque fichier dans des onglets
    tabs = st.tabs([f"Document {i+1}" for i in range(len(fichiers))])
    
    for i, (tab, fichier) in enumerate(zip(tabs, fichiers)):
        with tab:
            nom_fichier = os.path.basename(fichier)
            
            if fichier.lower().endswith(('.jpg', '.jpeg', '.png')):
                # Afficher l'image
                try:
                    image = Image.open(fichier)
                    st.image(image, caption=f"🧾 {nom_fichier}", use_column_width=True)
                    
                    # Option: ré-OCR
                    with st.expander("🔍 Analyser le texte"):
                        texte_ocr = full_ocr(fichier, show_ticket=False)
                        st.text_area("Texte du ticket:", texte_ocr, height=150)
                        
                except Exception as e:
                    toast_error("Impossible d'afficher l'image: {e}")
                    
            elif fichier.lower().endswith('.pdf'):
                # Afficher les infos du PDF
                st.success(f"📄 **{nom_fichier}**")
                
                # Extraire le texte automatiquement
                try:
                    texte_pdf = extract_text_from_pdf(fichier)
                    if texte_pdf.strip():
                        with st.expander("📖 Contenu du document"):
                            apercu = texte_pdf[:2000] + "..." if len(texte_pdf) > 2000 else texte_pdf
                            st.text_area("Extrait:", apercu, height=200)
                except:
                    st.info("📄 Document PDF (contenu non extrait)")
                
                # Téléchargement
                with open(fichier, "rb") as f:
                    st.download_button(
                        label="⬇️ Télécharger le document",
                        data=f.read(),
                        file_name=nom_fichier,
                        mime="application/pdf",
                        use_container_width=True
                    )

def normaliser_date(date_str):
    """
    Convertit une date (JJ/MM/AAAA, JJ/MM/AA, AAAA-MM-JJ, etc.)
    en format ISO (AAAA-MM-JJ) pour la base SQLite.
    """
    return safe_date_convert(date_str).isoformat()

def insert_transaction_batch(transactions):
    """
    Insère plusieurs transactions dans la base SQLite.
    Évite les doublons basés sur (type, categorie, sous_categorie, montant, date).
    Version V2 avec validation et traitement Uber.
    """
    if not transactions:
        return
    conn = get_db_connection()
    cur = conn.cursor()

    inserted, skipped, uber_processed = 0, 0, 0
    uber_messages = []

    for t in transactions:
        try:
            # Validation des données
            errors = validate_transaction_data(t)
            if errors:
                logger.warning(f"Transaction validation failed: {errors}")
                skipped += 1
                continue

            # Nettoyage des données
            clean_t = {
                "type": str(t["type"]).strip().lower(),
                "categorie": str(t.get("categorie", "")).strip(),
                "sous_categorie": str(t.get("sous_categorie", "")).strip(),
                "description": str(t.get("description", "")).strip(),
                "montant": safe_convert(t["montant"]),
                "date": safe_date_convert(t["date"]).isoformat(),
                "source": str(t.get("source", "manuel")).strip(),
                "recurrence": str(t.get("recurrence", "")).strip(),
                "date_fin": safe_date_convert(t.get("date_fin")).isoformat() if t.get("date_fin") else ""
            }

            # Traitement Uber pour les revenus
            if clean_t["type"] == "revenu":
                clean_t, uber_msg = process_uber_revenue(clean_t)
                if uber_msg:
                    uber_processed += 1
                    uber_messages.append(uber_msg)

            cur.execute("""
                SELECT COUNT(*) FROM transactions
                WHERE type = ? AND categorie = ? AND sous_categorie = ?
                      AND montant = ? AND date = ?
            """, (
                clean_t["type"],
                clean_t.get("categorie", ""),
                clean_t.get("sous_categorie", ""),
                float(clean_t["montant"]),
                clean_t["date"]
            ))

            if cur.fetchone()[0] > 0:
                skipped += 1
                continue

            cur.execute("""
                INSERT INTO transactions
                (type, categorie, sous_categorie, description, montant, date, source, recurrence, date_fin)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                clean_t["type"],
                clean_t.get("categorie", ""),
                clean_t.get("sous_categorie", ""),
                clean_t.get("description", ""),
                float(clean_t["montant"]),
                clean_t["date"],
                clean_t.get("source", "manuel"),
                clean_t.get("recurrence", ""),
                clean_t.get("date_fin", "")
            ))
            inserted += 1

        except Exception as e:
            logger.error(f"Erreur lors de l'insertion de {t}: {e}")

    conn.commit()
    conn.close()
    
    # Affichage des résultats
    if inserted > 0:
        toast_success("{inserted} transaction(s) insérée(s).")
        if uber_processed > 0:
            st.info(f"🚗 {uber_processed} revenu(s) Uber traité(s) avec application de la fiscalité (79%)")
            for msg in uber_messages:
                st.success(msg)
    if skipped > 0:
        st.info(f"ℹ️ {skipped} doublon(s) détecté(s) et ignoré(s).")

def get_montant_from_line(label_pattern, all_lines, allow_next_line=True):
    """
    Recherche un montant à partir d'un label (ex: 'TOTAL', 'MONTANT RÉEL', etc.)
    Corrigée pour être plus robuste face aux erreurs d'OCR et aux formats de tickets variés.
    """
    montant_regex = r"(\d{1,5}[.,]?\d{0,2})\s*(?:€|eur|euros?)?"

    def clean_ocr_text(txt):
        """Corrige les erreurs courantes de lecture OCR (O/0, I/1, etc.)."""
        txt = txt.replace("O", "0").replace("o", "0")
        txt = txt.replace("I", "1").replace("l", "1")
        txt = re.sub(r"[\u200b\s]+", " ", txt)
        return txt.strip()

    for i, l in enumerate(all_lines):
        l_clean = clean_ocr_text(l)

        # Recherche du label (ex: 'TOTAL', 'MONTANT', etc.)
        if re.search(label_pattern, l_clean, re.IGNORECASE):
            found_same = re.findall(montant_regex, l_clean, re.IGNORECASE)
            if found_same:
                # Prend le montant le plus grand sur la ligne (souvent le total TTC)
                return safe_convert(max(found_same, key=lambda x: safe_convert(x)))

            # Ligne suivante possible
            if allow_next_line and i + 1 < len(all_lines):
                next_line = clean_ocr_text(all_lines[i + 1])
                found_next = re.findall(montant_regex, next_line, re.IGNORECASE)
                if found_next:
                    return safe_convert(max(found_next, key=lambda x: safe_convert(x)))

    # Si rien trouvé, essaie de repérer un montant seul sur une ligne typique de paiement
    for l in all_lines:
        l_clean = clean_ocr_text(l)
        match = re.search(r"(\d+[.,]\d{2})", l_clean)
        if match:
            return safe_convert(match.group(1))

    return 0.0

def parse_ticket_metadata(ocr_text: str):
    """
    Analyse un texte OCR de ticket pour extraire les montants (total, paiements, TVA),
    et choisit le montant final par validation croisée.
    Version V2 avec conversions sécurisées.
    """
    lines = [l.strip() for l in ocr_text.split("\n") if l.strip()]

    def normalize_line(l):
        return l.replace("O", "0").replace("o", "0").replace("I", "1").replace("l", "1").strip()

    lines = [normalize_line(l) for l in lines]

    montant_regex = r"(\d{1,5}[.,]\d{1,2})"

    # === MÉTHODE A : Totaux directs (comme avant)
    total_patterns = [
        r"TOTAL\s*TTC", r"TOTAL\s*(A\s*PAYER)?", r"MONTANT\s*(R[EÉ]EL|TTC)?",
        r"NET\s*A\s*PAYER", r"À\s*PAYER", r"TOTAL$", r"TTC"
    ]
    montants_A = []
    for pattern in total_patterns:
        m = get_montant_from_line(pattern, lines)
        if m > 0:
            montants_A.append(round(m, 2))

    # === MÉTHODE B : Somme des paiements (CB, espèces, web, etc.)
    paiement_patterns = [r"CB", r"CARTE", r"ESPECES", r"WEB", r"PAYPAL", r"CHEQUE"]
    montants_B = []
    for l in lines:
        if any(re.search(p, l, re.IGNORECASE) for p in paiement_patterns):
            found = re.findall(montant_regex, l)
            for val in found:
                montants_B.append(safe_convert(val))
    somme_B = round(sum(montants_B), 2) if montants_B else 0.0

    # === MÉTHODE C : Net + TVA
    net_lines = [l for l in lines if re.search(r"HT|NET", l, re.IGNORECASE)]
    tva_lines = [l for l in lines if re.search(r"TVA|T\.V\.A", l, re.IGNORECASE)]
    total_HT = 0.0
    total_TVA = 0.0
    for l in net_lines:
        vals = re.findall(montant_regex, l)
        for v in vals:
            total_HT += safe_convert(v)
    for l in tva_lines:
        vals = re.findall(montant_regex, l)
        for v in vals:
            total_TVA += safe_convert(v)
    somme_C = round(total_HT + total_TVA, 2) if total_HT > 0 else 0.0

    # === MÉTHODE D : fallback global (si rien trouvé)
    all_amounts = [safe_convert(m) for m in re.findall(montant_regex, ocr_text)]
    montant_fallback = max(all_amounts) if all_amounts else 0.0

    # === VALIDATION CROISÉE
    candidats = [x for x in montants_A + [somme_B, somme_C, montant_fallback] if x > 0]
    freq = {}
    for m in candidats:
        m_rond = round(m, 2)
        freq[m_rond] = freq.get(m_rond, 0) + 1
    if not freq:
        montant_final = 0.0
    else:
        montant_final = max(freq, key=freq.get)  # prend le montant le plus récurrent

    # === Détection de la date (inchangée)
    date_patterns = [
        r"\b\d{1,2}[./\-]\d{1,2}[./\-]\d{2,4}\b",
        r"\b\d{1,2}\s*(janv|févr|mars|avr|mai|juin|juil|août|sept|oct|nov|déc)\.?\s*\d{2,4}\b"
    ]
    detected_date = None
    for p in date_patterns:
        match = re.search(p, ocr_text, re.IGNORECASE)
        if match:
            try:
                detected_date = parser.parse(match.group(0), dayfirst=True, fuzzy=True).date().isoformat()
                break
            except:
                continue
    if not detected_date:
        detected_date = datetime.now().date().isoformat()

    # === Lignes clés (pour affichage dans interface)
    key_lines = [
        l for l in lines if any(re.search(p, l, re.IGNORECASE) for p in total_patterns + paiement_patterns)
    ]

    # === Résultat final
    montants_possibles = sorted(set(candidats), reverse=True)
    return {
        "montants_possibles": montants_possibles if montants_possibles else [montant_final],
        "montant": montant_final,
        "date": detected_date,
        "infos": "\n".join(key_lines)
    }

def move_ticket_to_sorted(ticket_path, categorie, sous_categorie):
    """Déplace un ticket traité vers le dossier 'tickets_scannes' classé par catégorie/sous-catégorie.
       Gère automatiquement les doublons en renommant les fichiers si nécessaire."""
    cat_dir = os.path.join(SORTED_DIR, categorie.strip())
    souscat_dir = os.path.join(cat_dir, sous_categorie.strip())
    os.makedirs(souscat_dir, exist_ok=True)

    base_name = os.path.basename(ticket_path)
    dest_path = os.path.join(souscat_dir, base_name)

    # 🔁 Si un fichier du même nom existe déjà, on crée un nom unique
    if os.path.exists(dest_path):
        name, ext = os.path.splitext(base_name)
        counter = 1
        while os.path.exists(dest_path):
            new_name = f"{name}_{counter}{ext}"
            dest_path = os.path.join(souscat_dir, new_name)
            counter += 1

    shutil.move(ticket_path, dest_path)
    toast_success("Ticket déplacé vers : {dest_path}")

def extract_text_from_pdf(pdf_path):
    """Lit un PDF et renvoie le texte brut."""
    from pdfminer.high_level import extract_text
    try:
        return extract_text(pdf_path)
    except Exception as e:
        logger.warning(f"Impossible de lire le PDF {pdf_path} ({e})")
        toast_warning("Impossible de lire le PDF {pdf_path} ({e})")
        return ""

def parse_uber_pdf(pdf_path: str) -> dict:
    """
    Parseur spécifique pour les PDF Uber.
    Objectif : extraire le montant net (net earnings) et la date de fin de période de facturation.
    Renvoie dict avec clés : montant (float), date (datetime.date), categorie, sous_categorie, source.
    Version V2 avec application automatique du 79%.
    """
    text = extract_text_from_pdf(pdf_path)
    if not text:
        return {
            "montant": 0.0,
            "date": datetime.now().date(),
            "categorie": "Revenu",
            "sous_categorie": "Uber",
            "source": "PDF Uber"
        }

    # Cherche une période de facturation sous forme "Période de facturation : 01/07/2025 - 31/07/2025"
    date_fin = None
    periode_match = re.search(
        r"P[eé]riode de facturation\s*[:\-]?\s*([0-3]?\d[\/\-\.][01]?\d[\/\-\.]\d{2,4})\s*[\-–]\s*([0-3]?\d[\/\-\.][01]?\d[\/\-\.]\d{2,4})",
        text,
        re.IGNORECASE
    )
    if periode_match:
        debut_str, fin_str = periode_match.groups()
        for fmt in ("%d/%m/%Y", "%d/%m/%y", "%d-%m-%Y", "%d-%m-%y"):
            try:
                date_fin = datetime.strptime(fin_str, fmt).date()
                break
            except Exception:
                continue

    # Si non trouvé par pattern, on tente de trouver une date "Période terminée le : 31/07/2025" ou "Period ending 31/07/2025"
    if not date_fin:
        m2 = re.search(
            r"(period ending|p[eé]riode termin[eé]e le|Date de fin)\s*[:\-]?\s*([0-3]?\d[\/\-\.][01]?\d[\/\-\.]\d{2,4})",
            text,
            re.IGNORECASE
        )
        if m2:
            date_str = m2.group(2)
            for fmt in ("%d/%m/%Y", "%d/%m/%y", "%d-%m-%Y", "%d-%m-%y"):
                try:
                    date_fin = datetime.strptime(date_str, fmt).date()
                    break
                except Exception:
                    continue

    if not date_fin:
        date_fin = datetime.now().date()

    # Montant net : varie selon le PDF Uber (Net earnings, Total to be paid, etc.)
    montant = 0.0
    montant_patterns = [
        r"(?:Net earnings|Net to driver|Total net|Montant net|Net earnings \(driver\))\s*[:\-\–]?\s*([0-9]+[.,][0-9]{2})\s*€?",
        r"([\d]{1,3}(?:[ .,]\d{3})*[.,]\d{2})\s*€\s*(?:net|netto|net earnings|to driver)?"
    ]
    for p in montant_patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            s = m.group(1).replace(" ", "").replace(".", "").replace(",", ".") if "," in m.group(1) and "." in m.group(1) else m.group(1).replace(",", ".").replace(" ", "")
            try:
                montant = safe_convert(s)
                break
            except Exception:
                continue

    # fallback: chercher le dernier montant présent dans le texte
    if montant == 0.0:
        all_amounts = re.findall(r"(\d+[.,]\d{2})\s*€?", text)
        if all_amounts:
            for a in reversed(all_amounts):
                try:
                    candidate = safe_convert(a)
                    if candidate > 0:
                        montant = candidate
                        break
                except:
                    continue

    # 🔥 V2: APPLICATION AUTOMATIQUE 79% POUR UBER
    montant_net = round(montant * 0.79, 2) if montant > 0 else 0.0
    tax_amount = round(montant - montant_net, 2) if montant > 0 else 0.0
    
    if montant > 0:
        logger.info(f"Uber PDF processed: {montant}€ → {montant_net}€ net (after 21% tax)")

    return {
        "montant": montant_net,  # 🔥 Retourne le montant NET après impôts
        "date": date_fin,
        "categorie": "Uber Eats",  # 🔥 Catégorie standardisée
        "sous_categorie": "Uber",
        "source": "PDF Uber",
        "montant_brut": montant,  # 🔥 Information supplémentaire
        "tax_amount": tax_amount
    }

def parse_fiche_paie(pdf_path: str) -> dict:
    """
    Parseur spécifique pour fiche de paie.
    Objectif : trouver la période (ou la date concernée) et le net à payer.
    Renvoie dict similaire à parse_uber_pdf.
    """
    text = extract_text_from_pdf(pdf_path)
    if not text:
        return {"montant": 0.0, "date": datetime.now().date(), "categorie": "Revenu", "sous_categorie": "Salaire", "source": "PDF Fiche de paie"}

    # 1) Trouver le net à payer (patterns : NET A PAYER, Net à payer, Net pay, Net salary)
    montant = 0.0
    net_patterns = [
        r"NET\s*A\s*PAYER\s*[:\-\–]?\s*([0-9]+[.,][0-9]{2})",
        r"Net à payer\s*[:\-\–]?\s*([0-9]+[.,][0-9]{2})",
        r"Net à payer \(à vous\)\s*[:\-\–]?\s*([0-9]+[.,][0-9]{2})",
        r"Net\s*[:\-\–]?\s*([0-9]+[.,][0-9]{2})"  # fallback
    ]
    for p in net_patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            try:
                montant = safe_convert(m.group(1))
                break
            except:
                continue

    # fallback : prendre le dernier montant trouvé, mais prudence
    if montant == 0.0:
        amounts = re.findall(r"(\d+[.,]\d{2})\s*€?", text)
        if amounts:
            candidates = [safe_convert(a) for a in amounts]
            bigs = [c for c in candidates if c > 100]
            montant = bigs[-1] if bigs else candidates[-1]

    # 2) Trouver la période ou la date : recherche de "période" ou intervalle "01/07/2025 - 31/07/2025"
    date_found = None
    periode_match = re.search(r"(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})\s*[\-–]\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})", text)
    if periode_match:
        fin_str = periode_match.groups()[1]
        for fmt in ("%d/%m/%Y", "%d/%m/%y", "%d-%m-%Y", "%d-%m-%y"):
            try:
                date_found = datetime.strptime(fin_str, fmt).date()
                break
            except:
                pass

    if not date_found:
        m2 = re.search(r"Pour le mois de\s+([A-Za-zéûà]+)\s+(\d{4})", text, re.IGNORECASE)
        if m2:
            mois_str, annee_str = m2.groups()
            mois_map = {
                "janvier":1,"février":2,"fevrier":2,"mars":3,"avril":4,"mai":5,"juin":6,
                "juillet":7,"août":8,"aout":8,"septembre":9,"octobre":10,"novembre":11,"décembre":12,"decembre":12
            }
            mois_key = mois_str.lower()
            mois_num = mois_map.get(mois_key)
            if mois_num:
                from calendar import monthrange
                last_day = monthrange(int(annee_str), mois_num)[1]
                date_found = date(int(annee_str), mois_num, last_day)

    if not date_found:
        date_found = datetime.now().date()

    return {
        "montant": round(float(montant), 2),
        "date": date_found,
        "categorie": "Revenu",
        "sous_categorie": "Salaire",
        "source": "PDF Fiche de paie"
    }

def parse_pdf_dispatcher(pdf_path: str, source_type: str) -> dict:
    """
    Dispatcher simple pour choisir le parseur adapté.
    source_type attendu : 'uber', 'fiche_paie', 'ticket' (ou 'auto' pour tentative heuristique).
    """
    stype = source_type.lower().strip()
    if stype in ("uber", "uber_pdf", "uber eats"):
        return parse_uber_pdf(pdf_path)
    elif stype in ("fiche_paie", "fiche de paie", "paye", "salaire"):
        return parse_fiche_paie(pdf_path)
    elif stype in ("ticket", "receipt", "ticket_ocr"):
        text = extract_text_from_pdf(pdf_path)
        return parse_ticket_metadata(text)
    elif stype == "auto":
        text = extract_text_from_pdf(pdf_path).lower()
        if "uber" in text or "net to driver" in text or "period" in text:
            return parse_uber_pdf(pdf_path)
        if "net a payer" in text or "fiche de paie" in text or "bulletin" in text:
            return parse_fiche_paie(pdf_path)
        return {"montant": 0.0, "date": datetime.now().date(), "categorie": "Revenu", "sous_categorie": "Inconnu", "source": "PDF Auto"}
    else:
        raise ValueError(f"Source_type inconnu pour parse_pdf_dispatcher: {source_type}")

def _inc(d, recurrence):
    if recurrence == "hebdomadaire":
        return d + relativedelta(weeks=1)
    if recurrence == "mensuelle":
        return d + relativedelta(months=1)
    if recurrence == "annuelle":
        return d + relativedelta(years=1)
    return d

def backfill_recurrences_to_today(db_path):
    """
    Pour chaque modèle 'récurrente', génère toutes les occurrences manquantes
    (source='récurrente_auto') jusqu'à aujourd'hui (ou date_fin si elle existe).
    """
    today = date.today()

    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
       SELECT id, type, categorie, sous_categorie, montant, date, source, recurrence, date_fin
       FROM transactions
       WHERE source='récurrente'
    """)
    models = cur.fetchall()

    for m in models:
        cat = (m["categorie"] or "").strip()
        sous = (m["sous_categorie"] or "").strip()
        rec = (m["recurrence"] or "").strip()
        if not rec:
            continue

        try:
            start = date.fromisoformat(m["date"])
        except Exception:
            continue
        end_limit = None
        if m["date_fin"]:
            try:
                end_limit = date.fromisoformat(m["date_fin"])
            except Exception:
                end_limit = None
        limit = min(today, end_limit) if end_limit else today

        if start > limit:
            continue

        cur.execute("""
            SELECT MAX(date) as last_date
            FROM transactions
            WHERE source='récurrente_auto'
              AND categorie=? AND sous_categorie=?
              AND recurrence=?
              AND type=?
        """, (cat, sous, rec, m["type"]))
        row = cur.fetchone()
        last = date.fromisoformat(row["last_date"]) if row and row["last_date"] else None

        if last:
            next_d = _inc(last, rec)
        else:
            next_d = start

        to_insert = []
        while next_d <= limit:
            to_insert.append((
                m["type"], cat, sous, float(m["montant"]), next_d.isoformat(),
                "récurrente_auto", rec, m["date_fin"]
            ))
            next_d = _inc(next_d, rec)

        if to_insert:
            cur.executemany("""
                INSERT INTO transactions (type, categorie, sous_categorie, montant, date, source, recurrence, date_fin)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, to_insert)

    conn.commit()
    conn.close()
    
# ==============================
#  🏠 ACCUEIL V2
# ============================== 
def interface_accueil():
    st.title("🏠 Tableau de Bord Financier V2")
    
    # Charger les données avec gestion d'erreurs
    try:
        df = load_transactions()
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        toast_error("Erreur lors du chargement des données")
        return
    
    if df.empty:
        st.info("💰 Aucune transaction enregistrée. Commencez par ajouter vos premières transactions !")
        return
    
    # 🔥 DÉTERMINER LA PREMIÈRE TRANSACTION
    premiere_date = df["date"].min().date()
    derniere_date = df["date"].max().date()
    
    st.markdown("---")
    st.subheader("🎯 Période d'analyse")
    
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
    
    with col1:
        periode_options = {
            "Depuis le début": "debut",
            "6 derniers mois": 6,
            "3 derniers mois": 3, 
            "12 derniers mois": 12,
            "Personnalisée": "custom"
        }
        periode_choice = st.selectbox("Choisir la période", list(periode_options.keys()))
    
    with col2:
        if periode_choice == "Personnalisée":
            date_debut = st.date_input("Date de début", value=premiere_date)
            date_fin = st.date_input("Date de fin", value=derniere_date)
        elif periode_choice == "Depuis le début":
            date_debut = premiere_date
            date_fin = derniere_date
            st.info(f"📅 Depuis le début\n{date_debut.strftime('%d/%m/%Y')}")
        else:
            mois_retour = periode_options[periode_choice]
            date_debut = max(premiere_date, date.today() - relativedelta(months=mois_retour))
            date_fin = derniere_date
            st.info(f"📅 {date_debut.strftime('%d/%m/%Y')} → {date_fin.strftime('%d/%m/%Y')}")
    
    with col3:
        duree_mois = max(1, ((date_fin - date_debut).days // 30))
        st.metric(
            "📅 Couverture", 
            f"{duree_mois} mois",
            delta=f"Depuis {premiere_date.strftime('%d/%m/%y')}"
        )
    
    with col4:
        if st.button("🔄 Actualiser"):
            refresh_and_rerun()
    
    # Filtrer les données selon la période
    df_periode = df[(df["date"] >= pd.Timestamp(date_debut)) & (df["date"] <= pd.Timestamp(date_fin))]
    
    if df_periode.empty:
        toast_warning("Aucune transaction dans la période sélectionnée.")
        return
    
    # 🔥 STATISTIQUES PAR MOIS
    df_mensuel = df_periode.copy()
    df_mensuel["mois"] = df_mensuel["date"].dt.to_period("M")
    df_mensuel["mois_str"] = df_mensuel["date"].dt.strftime("%b %Y")
    
    transactions_par_mois = df_mensuel.groupby("mois_str").agg({
        "montant": "count",
        "type": lambda x: (x == "revenu").sum()
    }).rename(columns={"montant": "total_transactions", "type": "nb_revenus"})
    
    transactions_par_mois["nb_depenses"] = transactions_par_mois["total_transactions"] - transactions_par_mois["nb_revenus"]
    
    # 🔥 MÉTRIQUES PRINCIPALES AMÉLIORÉES
    st.markdown("---")
    st.subheader("📈 Vue d'Ensemble")
    
    total_revenus = df_periode[df_periode["type"] == "revenu"]["montant"].sum()
    total_depenses = df_periode[df_periode["type"] == "dépense"]["montant"].sum()
    solde_periode = total_revenus - total_depenses
    nb_transactions = len(df_periode)
    
    df_depenses = df_periode[df_periode["type"] == "dépense"]
    df_revenus = df_periode[df_periode["type"] == "revenu"]
    
    nb_depenses = len(df_depenses)
    nb_revenus = len(df_revenus)
    mois_couverts = max(1, ((date_fin - date_debut).days // 30))
    
    depenses_mensuelles = total_depenses / mois_couverts
    revenus_mensuels = total_revenus / mois_couverts
    moyenne_depense = df_depenses["montant"].median() if not df_depenses.empty else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        solde_color = "green" if solde_periode >= 0 else "red"
        solde_icon = "📈" if solde_periode >= 0 else "📉"
        st.metric(
            f"{solde_icon} Solde période", 
            f"{solde_periode:+.2f} €",
            delta=f"{solde_periode/mois_couverts:+.0f} €/mois"
        )
    
    with col2:
        st.metric(
            "💸 Dépenses totales", 
            f"{total_depenses:.2f} €",
            delta=f"~{depenses_mensuelles:.0f} €/mois • {nb_depenses} transactions"
        )
    
    with col3:
        st.metric(
            "💹 Revenus totaux", 
            f"{total_revenus:.2f} €",
            delta=f"~{revenus_mensuels:.0f} €/mois • {nb_revenus} transactions"
        )
    
    with col4:
        transactions_mensuelles = nb_transactions / mois_couverts
        st.metric(
            "📊 Activité moyenne", 
            f"{transactions_mensuelles:.1f}/mois",
            delta=f"{nb_transactions} transactions total"
        )
    
    # 🔥 TABLEAU DES TRANSACTIONS PAR MOIS
    st.markdown("---")
    st.subheader("📅 Activité Mensuelle")
    
    if not transactions_par_mois.empty:
        transactions_par_mois = transactions_par_mois.sort_index(
            key=lambda x: pd.to_datetime(x, format='%b %Y')
        )
        
        df_display = transactions_par_mois.reset_index()
        df_display = df_display.rename(columns={
            "mois_str": "Mois",
            "total_transactions": "Total",
            "nb_revenus": "Revenus",
            "nb_depenses": "Dépenses"
        })
        
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Mois": st.column_config.TextColumn("📅 Mois"),
                "Total": st.column_config.NumberColumn("📊 Total", format="%d"),
                "Revenus": st.column_config.NumberColumn("💹 Revenus", format="%d"),
                "Dépenses": st.column_config.NumberColumn("💸 Dépenses", format="%d")
            }
        )
        
        # 🔥 GRAPHIQUE DE L'ACTIVITÉ MENSUELLE
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📈 Évolution du nombre de transactions**")
            
            fig, ax = plt.subplots(figsize=(10, 4))
            
            try:
                theme = st.get_option("theme.base")
                is_dark_theme = theme == "dark"
            except:
                is_dark_theme = False
                
            bg_color = "#0E1117" if is_dark_theme else "white"
            text_color = "white" if is_dark_theme else "black"
            
            fig.patch.set_facecolor(bg_color)
            ax.set_facecolor(bg_color)
            ax.tick_params(colors=text_color)
            ax.xaxis.label.set_color(text_color)
            ax.yaxis.label.set_color(text_color)
            ax.title.set_color(text_color)
            
            x_pos = np.arange(len(transactions_par_mois.index))
            bar_width = 0.6
            
            bars_total = ax.bar(x_pos, transactions_par_mois["total_transactions"], 
                               bar_width, label="Total", alpha=0.7, color="#4A90E2")
            
            ax.set_ylabel("Nombre de transactions", color=text_color, fontweight='bold')
            ax.set_xlabel("Mois", color=text_color, fontweight='bold')
            ax.set_title("Évolution de l'activité mensuelle", color=text_color, fontweight='bold')
            
            ax.set_xticks(x_pos)
            ax.set_xticklabels(transactions_par_mois.index, rotation=45, ha='right', color=text_color)
            ax.legend(facecolor=bg_color, edgecolor=text_color, labelcolor=text_color)
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            st.pyplot(fig)
        
        with col2:
            st.markdown("**🥧 Répartition Revenus/Dépenses**")
            
            total_revenus_count = transactions_par_mois["nb_revenus"].sum()
            total_depenses_count = transactions_par_mois["nb_depenses"].sum()
            
            if total_revenus_count + total_depenses_count > 0:
                fig, ax = plt.subplots(figsize=(8, 4))
                
                fig.patch.set_facecolor(bg_color)
                ax.set_facecolor(bg_color)
                
                data = [total_revenus_count, total_depenses_count]
                labels = [f"Revenus\n{total_revenus_count}", f"Dépenses\n{total_depenses_count}"]
                colors = ["#00D4AA", "#FF6B6B"]
                
                wedges, texts, autotexts = ax.pie(
                    data, 
                    labels=labels, 
                    autopct='%1.1f%%', 
                    startangle=90,
                    colors=colors,
                    wedgeprops={'edgecolor': bg_color, 'linewidth': 2}
                )
                
                for text in texts:
                    text.set_color(text_color)
                    text.set_fontweight('bold')
                for autotext in autotexts:
                    autotext.set_color('white')
                    autotext.set_fontweight('bold')
                
                ax.axis('equal')
                ax.set_title("Répartition des transactions", color=text_color, fontweight='bold')
                st.pyplot(fig)
            else:
                st.info("📊 Pas assez de données pour le graphique")
    
    else:
        st.info("📅 Pas assez de données pour l'analyse mensuelle")
    
    # 🔥 INDICATEURS DE SANTÉ FINANCIÈRE
    st.markdown("---")
    st.subheader("💰 Santé Financière")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if total_revenus > 0:
            taux_epargne = (solde_periode / total_revenus) * 100
            
            if taux_epargne >= 20:
                message = "🎉 Excellent"
                couleur = "normal"
            elif taux_epargne >= 10:
                message = "👍 Très bien" 
                couleur = "normal"
            elif taux_epargne >= 0:
                message = "✅ Correct"
                couleur = "off"
            else:
                message = "🚨 Découvert"
                couleur = "inverse"
                
            st.metric(
                "🎯 Taux d'épargne", 
                f"{taux_epargne:.1f}%",
                delta=message,
                delta_color=couleur
            )
        else:
            st.metric("🎯 Taux d'épargne", "N/A", delta="Aucun revenu")
    
    with col2:
        if total_revenus > 0:
            ratio_depenses = (total_depenses / total_revenus) * 100
            
            if ratio_depenses <= 80:
                message = "✅ Maîtrisé"
                couleur = "normal"
            elif ratio_depenses <= 100:
                message = "⚠️ Limite"
                couleur = "off" 
            else:
                message = "🚨 Dangereux"
                couleur = "inverse"
                
            st.metric(
                "📊 Ratio dépenses", 
                f"{ratio_depenses:.1f}%",
                delta=message,
                delta_color=couleur
            )
        else:
            st.metric("📊 Ratio dépenses", "N/A", delta="Aucun revenu")
    
    with col3:
        if not df_depenses.empty:
            depense_max = df_depenses["montant"].max()
            
            if total_revenus > 0:
                ratio_max = (depense_max / (total_revenus/mois_couverts)) * 100
                if ratio_max > 50:
                    message = "🚨 Important"
                    couleur = "inverse"
                elif ratio_max > 25:
                    message = "⚠️ Notable"
                    couleur = "off"
                else:
                    message = "✅ Normal"
                    couleur = "normal"
            else:
                message = "💰 Dépense"
                couleur = "normal"
                
            st.metric(
                "🔥 Plus grosse dépense", 
                f"{depense_max:.0f} €",
                delta=message,
                delta_color=couleur
            )
        else:
            st.metric("🔥 Plus grosse dépense", "0 €")
    
    with col4:
        tx_par_mois = nb_transactions / mois_couverts
        if tx_par_mois > 20:
            message = "📈 Actif"
            couleur = "normal"
        elif tx_par_mois > 10:
            message = "📊 Moyen"
            couleur = "normal"
        else:
            message = "📉 Faible"
            couleur = "off"
            
        st.metric(
            "🔄 Activité moyenne", 
            f"{tx_par_mois:.1f}/mois",
            delta=message,
            delta_color=couleur
        )
    
    # 🔥 DÉTECTION DU THÈME STREAMLIT
    try:
        theme = st.get_option("theme.base")
        is_dark_theme = theme == "dark"
    except:
        is_dark_theme = False
    
    # 🔥 COULEURS ADAPTATIVES AU THÈME
    if is_dark_theme:
        bg_color = "#0E1117"
        text_color = "white"
        grid_color = "#2E2E2E"
        face_color = "#0E1117"
    else:
        bg_color = "white"
        text_color = "black"
        grid_color = "#E0E0E0"
        face_color = "white"
    
    couleur_revenus = "#00D4AA"
    couleur_depenses = "#FF6B6B"
    couleur_solde = "#4A90E2"
    
    # 🔥 GRAPHIQUE PRINCIPAL ADAPTÉ AU THÈME
    st.markdown("---")
    st.subheader("📊 Évolution Financière")
    
    df_mensuel = df_periode.copy()
    df_mensuel["mois"] = df_mensuel["date"].dt.to_period("M")
    df_mensuel["mois_str"] = df_mensuel["date"].dt.strftime("%b %Y")
    
    df_evolution = df_mensuel.groupby(["mois_str", "type"])["montant"].sum().unstack(fill_value=0)
    df_evolution = df_evolution.reindex(sorted(df_evolution.index, key=lambda x: pd.to_datetime(x, format='%b %Y')))
    
    if not df_evolution.empty:
        plt.style.use('default')
        fig, ax = plt.subplots(figsize=(12, 6))
        
        fig.patch.set_facecolor(bg_color)
        ax.set_facecolor(bg_color)
        ax.tick_params(colors=text_color)
        ax.xaxis.label.set_color(text_color)
        ax.yaxis.label.set_color(text_color)
        ax.title.set_color(text_color)
        
        bar_width = 0.6
        x_pos = np.arange(len(df_evolution.index))
        
        if "revenu" in df_evolution.columns:
            bars_revenus = ax.bar(x_pos, df_evolution["revenu"], bar_width, 
                                  label="Revenus", color=couleur_revenus, alpha=0.9,
                                  edgecolor=text_color, linewidth=0.5)
        
        if "dépense" in df_evolution.columns:
            bars_depenses = ax.bar(x_pos, -df_evolution["dépense"], bar_width, 
                                   label="Dépenses", color=couleur_depenses, alpha=0.9,
                                   edgecolor=text_color, linewidth=0.5)
        
        if "revenu" in df_evolution.columns and "dépense" in df_evolution.columns:
            solde_mensuel = df_evolution.get("revenu", 0) - df_evolution.get("dépense", 0)
            line_solde = ax.plot(x_pos, solde_mensuel, label="Solde", color=couleur_solde, 
                                 marker='o', linewidth=3, markersize=6, markerfacecolor=bg_color,
                                 markeredgecolor=couleur_solde, markeredgewidth=2)
        
        ax.axhline(0, color=text_color, linewidth=1, alpha=0.5)
        ax.set_ylabel("Montant (€)", fontsize=12, fontweight='bold', color=text_color)
        ax.set_xlabel("Mois", fontsize=12, fontweight='bold', color=text_color)
        ax.set_title("Évolution des Revenus et Dépenses", fontsize=14, fontweight='bold', pad=20, color=text_color)
        
        legend = ax.legend(loc='upper left', frameon=True, fancybox=True, 
                          facecolor=bg_color, edgecolor=text_color, labelcolor=text_color)
        
        ax.grid(True, alpha=0.2, color=grid_color)
        ax.set_xticks(x_pos)
        ax.set_xticklabels(df_evolution.index, rotation=45, ha='right', color=text_color)
        
        def add_value_labels(ax, bars):
            for bar in bars:
                height = bar.get_height()
                if abs(height) > 0:
                    label_color = text_color if abs(height) > max(ax.get_ylim())*0.1 else text_color
                    va = 'bottom' if height > 0 else 'top'
                    y_offset = 10 if height > 0 else -20
                    
                    ax.text(bar.get_x() + bar.get_width()/2., height + y_offset,
                           f'{abs(height):.0f}€', ha='center', va=va,
                           fontweight='bold', fontsize=9, color=label_color)
        
        if "revenu" in df_evolution.columns:
            add_value_labels(ax, bars_revenus)
        if "dépense" in df_evolution.columns:
            add_value_labels(ax, bars_depenses)
        
        for spine in ax.spines.values():
            spine.set_color(text_color)
            spine.set_alpha(0.3)
        
        plt.tight_layout()
        st.pyplot(fig)
        
    else:
        st.info("📈 Pas assez de données pour afficher l'évolution mensuelle")
    
    
    # 🔥 RÉPARTITION DES CATÉGORIES ADAPTÉE
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🥧 Dépenses par Catégorie")
        
        depenses_df = df_periode[df_periode["type"] == "dépense"]
        if not depenses_df.empty:
            categories_depenses = depenses_df.groupby("categorie")["montant"].sum().sort_values(ascending=False)
            total_depenses_calc = categories_depenses.sum()
            
            seuil_minimum = 0.03
            categories_principales = categories_depenses[categories_depenses / total_depenses_calc >= seuil_minimum]
            categories_autres = categories_depenses[categories_depenses / total_depenses_calc < seuil_minimum]
            
            if not categories_autres.empty:
                categories_principales = categories_principales.copy()
                categories_principales["Autres"] = categories_autres.sum()
            
            if not categories_principales.empty:
                fig, ax = plt.subplots(figsize=(8, 6))
                
                fig.patch.set_facecolor(bg_color)
                ax.set_facecolor(bg_color)
                
                colors = plt.cm.Set3(np.linspace(0, 1, len(categories_principales)))
                wedges, texts, autotexts = ax.pie(
                    categories_principales.values, 
                    labels=categories_principales.index, 
                    autopct='%1.1f%%', 
                    startangle=90,
                    colors=colors,
                    wedgeprops={'edgecolor': bg_color, 'linewidth': 2}
                )
                
                for text in texts:
                    text.set_color(text_color)
                for autotext in autotexts:
                    autotext.set_color('white' if is_dark_theme else 'black')
                    autotext.set_fontweight('bold')
                
                ax.axis('equal')
                ax.set_title(f"Dépenses ({len(categories_principales)} catégories)", 
                           color=text_color, fontweight='bold')
                st.pyplot(fig)
                
    with col2:
        st.subheader("📊 Revenus par Catégorie")
        
        revenus_df = df_periode[df_periode["type"] == "revenu"]
        if not revenus_df.empty:
            categories_revenus = revenus_df.groupby("categorie")["montant"].sum().sort_values(ascending=False)
            total_revenus_calc = categories_revenus.sum()
            
            seuil_minimum = 0.03
            categories_principales = categories_revenus[categories_revenus / total_revenus_calc >= seuil_minimum]
            categories_autres = categories_revenus[categories_revenus / total_revenus_calc < seuil_minimum]
            
            if not categories_autres.empty:
                categories_principales = categories_principales.copy()
                categories_principales["Autres"] = categories_autres.sum()
            
            if not categories_principales.empty:
                fig, ax = plt.subplots(figsize=(8, 6))
                
                fig.patch.set_facecolor(bg_color)
                ax.set_facecolor(bg_color)
                
                colors = plt.cm.Pastel1(np.linspace(0, 1, len(categories_principales)))
                wedges, texts, autotexts = ax.pie(
                    categories_principales.values, 
                    labels=categories_principales.index, 
                    autopct='%1.1f%%', 
                    startangle=90,
                    colors=colors,
                    wedgeprops={'edgecolor': bg_color, 'linewidth': 2}
                )
                
                for text in texts:
                    text.set_color(text_color)
                for autotext in autotexts:
                    autotext.set_color('black')
                    autotext.set_fontweight('bold')
                
                ax.axis('equal')
                ax.set_title(f"Revenus ({len(categories_principales)} catégories)", 
                           color=text_color, fontweight='bold')
                st.pyplot(fig)
    
    # 🔥 PLUS GROSSES TRANSACTIONS (REVENUS ET DÉPENSES)
    st.markdown("---")
    st.subheader("🎯 Transactions Importantes")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**💸 Top 5 Dépenses**")
        top_depenses = df_periode[df_periode["type"] == "dépense"].nlargest(5, "montant")
        
        if not top_depenses.empty:
            for idx, trans in top_depenses.iterrows():
                with st.container():
                    col_a, col_b = st.columns([3, 2])
                    with col_a:
                        st.write(f"**{trans['categorie']}** → {trans['sous_categorie']}")
                        if trans.get('description'):
                            st.caption(f"📝 {trans['description']}")
                    with col_b:
                        st.markdown(f"<h4 style='color: #FF6B6B; text-align: right;'>-{trans['montant']:.2f} €</h4>", 
                                  unsafe_allow_html=True)
                    st.caption(f"📅 {trans['date'].strftime('%d/%m/%Y')}")
                    st.markdown("---")
        else:
            st.info("Aucune dépense significative")
    
    with col2:
        st.markdown("**💹 Top 5 Revenus**")
        top_revenus = df_periode[df_periode["type"] == "revenu"].nlargest(5, "montant")
        
        if not top_revenus.empty:
            for idx, trans in top_revenus.iterrows():
                with st.container():
                    col_a, col_b = st.columns([3, 2])
                    with col_a:
                        st.write(f"**{trans['categorie']}** → {trans['sous_categorie']}")
                        if trans.get('description'):
                            st.caption(f"📝 {trans['description']}")
                    with col_b:
                        st.markdown(f"<h4 style='color: #00D4AA; text-align: right;'>+{trans['montant']:.2f} €</h4>", 
                                  unsafe_allow_html=True)
                    st.caption(f"📅 {trans['date'].strftime('%d/%m/%Y')}")
                    st.markdown("---")
        else:
            st.info("Aucun revenu significatif")
    
    # 🔥 10 DERNIÈRES TRANSACTIONS
    st.markdown("---")
    st.subheader("🕒 10 Dernières Transactions")
    
    dernieres = df_periode.head(5)
    
    if not dernieres.empty:
        for idx, trans in dernieres.iterrows():
            with st.container():
                col1, col2, col3 = st.columns([1, 3, 2])
                
                with col1:
                    icon = "🟢" if trans["type"] == "revenu" else "🔴"
                    st.write(icon)
                
                with col2:
                    st.write(f"**{trans['categorie']}** → {trans['sous_categorie']}")
                    if trans.get('description'):
                        st.caption(f"📝 {trans['description']}")
                    st.caption(f"📅 {trans['date'].strftime('%d/%m/%Y')}")
                
                with col3:
                    montant_color = "#00D4AA" if trans["type"] == "revenu" else "#FF6B6B"
                    montant_prefix = "+" if trans["type"] == "revenu" else "-"
                    st.markdown(f"<h4 style='color: {montant_color}; text-align: right;'>{montant_prefix}{trans['montant']:.2f} €</h4>", 
                              unsafe_allow_html=True)
                
                st.markdown("---")
    else:
        st.info("Aucune transaction récente")

# ==============================
# ⚙️ TRAITEMENT DES TICKETS ET REVENUS V2
# ==============================
def process_all_tickets_in_folder():
    """
    Traite tous les tickets du dossier TO_SCAN_DIR :
    - OCR
    - extraction montants / date / infos clés
    - confirmation utilisateur
    - insertion en base + déplacement
    Version V2 avec conversions sécurisées.
    """
    print("\n" + "="*60)
    print("[DEBUG] FONCTION process_all_tickets_in_folder APPELEE")
    print("="*60 + "\n")

    st.subheader("🧾 Traitement des tickets à scanner V2")

    tickets = [f for f in os.listdir(TO_SCAN_DIR) if f.lower().endswith((".jpg", ".png", ".jpeg", ".pdf"))]

    print(f"[DEBUG] TO_SCAN_DIR : {TO_SCAN_DIR}")
    print(f"[DEBUG] Tickets trouves : {len(tickets)}")
    for t in tickets:
        print(f"  - {t}")
    print()

    if not tickets:
        st.info("📂 Aucun ticket à scanner pour le moment.")
        return

    st.write(f"🧮 {len(tickets)} ticket(s) détecté(s) dans le dossier à scanner.")

    for ticket_file in tickets:
        ticket_path = os.path.join(TO_SCAN_DIR, ticket_file)
        st.markdown("---")
        st.markdown(f"### 🧾 {ticket_file}")

        # --- OCR selon format ---
        try:
            if ticket_file.lower().endswith(".pdf"):
                text = extract_text_from_pdf(ticket_path)
                with st.expander(f"📄 Texte OCR extrait du PDF : {ticket_file}", expanded=False):
                    st.text_area("Contenu OCR :", text, height=200)
            else:
                text = full_ocr(ticket_path, show_ticket=True)
        except Exception as e:
            logger.error(f"OCR failed for {ticket_file}: {e}")
            toast_error(f"Erreur OCR sur {ticket_file} : {e}", 5000)
            continue

        # --- Analyse du texte OCR ---
        data = parse_ticket_metadata(text)

        montant_final = data.get("montant", 0.0)
        montants_possibles = data.get("montants_possibles", [montant_final])
        detected_date = data.get("date", datetime.now().date().isoformat())
        key_info = data.get("infos", "")

        # --- Déduction de la catégorie et sous-catégorie à partir du nom de fichier ---
        name = os.path.splitext(ticket_file)[0]
        parts = name.split(".")[1:]

        if len(parts) >= 2:
            categorie_auto = parts[1].capitalize()
            sous_categorie_auto = parts[0].capitalize()
        elif len(parts) == 1:
            categorie_auto = parts[0].capitalize()
            sous_categorie_auto = "Autre"
        else:
            categorie_auto = "Divers"
            sous_categorie_auto = "Autre"

        st.markdown(f"🧠 **Catégorie auto-détectée :** {categorie_auto} → {sous_categorie_auto}")

        with st.expander("📜 Aperçu OCR (lignes clés)"):
            st.text(key_info)

        with st.form(f"form_{ticket_file}"):
            col1, col2 = st.columns(2)
            with col1:
                categorie = st.text_input("Catégorie principale", categorie_auto)
                sous_categorie = st.text_input("Sous-catégorie (ex: supermarché, restaurant...)", sous_categorie_auto)
            with col2:
                montant_select = st.selectbox(
                    "Montant détecté",
                    options=[round(m, 2) for m in montants_possibles],
                    index=0 if montants_possibles else 0
                )
                montant_corrige = st.number_input(
                    "💶 Corriger le montant si besoin (€)",
                    value=float(montant_select) if montant_select else 0.0,
                    min_value=0.0,
                    step=0.01
                )
                date_ticket = st.date_input("📅 Date du ticket", safe_date_convert(detected_date))

            valider = st.form_submit_button("✅ Valider et enregistrer ce ticket")

        if valider:
            print(f"\n[DEBUG] FORMULAIRE VALIDE pour {ticket_file}")
            print(f"   Categorie: {categorie}")
            print(f"   Montant: {montant_corrige}")
            print(f"   Montants possibles: {montants_possibles}\n")

            if not categorie or montant_corrige <= 0:
                print(f"[DEBUG] VALIDATION ECHOUEE : categorie='{categorie}', montant={montant_corrige}")
                toast_error("Catégorie ou montant invalide")
                continue

            print("[DEBUG] Validation OK, insertion transaction...")
            # Insérer la transaction
            insert_transaction_batch([{
                "type": "dépense",
                "categorie": categorie.strip(),
                "sous_categorie": sous_categorie.strip(),
                "montant": safe_convert(montant_corrige),
                "date": date_ticket.isoformat(),
                "source": "OCR"
            }])

            # Déplacer le ticket
            move_ticket_to_sorted(ticket_path, categorie, sous_categorie)

            # === ENREGISTRER LES STATISTIQUES OCR ===
            # Déterminer le niveau de succès
            success_level = determine_success_level(montants_possibles, montant_corrige)

            # Extraire les patterns détectés du texte OCR
            patterns_detectes = []
            text_lower = text.lower()
            ticket_patterns = ['total', 'montant', 'ttc', 'cb', 'carte', 'espèces', 'esp']
            for pattern in ticket_patterns:
                if pattern in text_lower:
                    patterns_detectes.append(pattern)

            # Enregistrer le scan avec toutes les infos
            log_ocr_scan(
                document_type="ticket",
                filename=ticket_file,
                montants_detectes=montants_possibles,
                montant_choisi=montant_corrige,
                categorie=categorie.strip(),
                sous_categorie=sous_categorie.strip(),
                patterns_detectes=patterns_detectes,
                success_level=success_level
            )

            # Afficher un message selon le niveau de succès
            if success_level == "exact":
                toast_success(f"Ticket enregistré : {montant_corrige:.2f} € (montant exact détecté !)")
            elif success_level == "partial":
                toast_warning(f"Ticket enregistré : {montant_corrige:.2f} € (montant dans la liste)")
            else:
                toast_warning(f"Ticket enregistré : {montant_corrige:.2f} € (montant corrigé manuellement)", 4000)

def interface_process_all_revenues_in_folder():
    st.subheader("📥 Scanner et enregistrer tous les revenus depuis le dossier V2")

    src_folder = REVENUS_A_TRAITER 

    if "revenus_data" not in st.session_state:
        st.session_state["revenus_data"] = []

    if st.button("🚀 Scanner tous les revenus") and not st.session_state["revenus_data"]:
        pdfs = [os.path.join(root, f)
                for root, _, files in os.walk(src_folder)
                for f in files if f.lower().endswith(".pdf")]

        if not pdfs:
            toast_warning("Aucun PDF de revenu trouvé dans le dossier.")
            return

        data_list = []
        for pdf_path in pdfs:
            parent_folder = os.path.basename(os.path.dirname(pdf_path))

            if parent_folder.lower() in ["revenus_a_traiter", "revenus_traité", "revenus_traités"]:
                sous_dossier = "Revenus"
            else:
                sous_dossier = parent_folder

            try:
                if sous_dossier.lower() == "uber":
                    parsed = parse_uber_pdf(pdf_path)
                    # 🔥 V2: Uber tax already applied in parse_uber_pdf
                    toast_success("Uber PDF traité: {parsed.get('montant_brut', 0):.2f}€ → {parsed['montant']:.2f}€ net")
                else:
                    parsed = parse_fiche_paie(pdf_path)
            except Exception as e:
                logger.error(f"PDF parsing failed for {pdf_path}: {e}")
                parsed = {"montant": 0.0, "date": datetime.today().date(), "source": "PDF Auto"}

            date_val = parsed.get("date", datetime.today().date())
            if isinstance(date_val, str):
                date_val = safe_date_convert(date_val)
            mois_nom = numero_to_mois(f"{date_val.month:02d}")

            data_list.append({
                "file": os.path.basename(pdf_path),
                "path": pdf_path,
                "categorie": sous_dossier,
                "sous_categorie": mois_nom,
                "montant": parsed.get("montant", 0.0),
                "montant_initial": parsed.get("montant", 0.0),  # Sauvegarder le montant détecté par OCR
                "date": date_val,
                "source":"PDF"
            })

        st.session_state["revenus_data"] = data_list
        toast_success("Revenus scannés avec succès. Tu peux maintenant les modifier avant validation.")

    if st.session_state.get("revenus_data"):
        updated_list = []
        for idx, data in enumerate(st.session_state["revenus_data"]):
            st.markdown("---")
            st.write(f"📄 {data['file']}")
            col1, col2 = st.columns(2)
            with col1:
                cat = st.text_input(f"Catégorie ({data['file']})", value=data["categorie"], key=f"rev_cat_{idx}")
                souscat = st.text_input(f"Sous-catégorie ({data['file']})", value=data["sous_categorie"], key=f"rev_souscat_{idx}")
            with col2:
                montant_str = f"{data['montant']:.2f}" if data["montant"] else ""
                montant_edit = st.text_input(f"Montant (€) ({data['file']})", value=montant_str, key=f"rev_montant_{idx}")
                date_edit = st.date_input(f"Date ({data['file']})", value=data["date"], key=f"rev_date_{idx}")

            montant_val = safe_convert(montant_edit)

            updated_list.append({
                "file": data["file"],
                "path": data["path"],
                "categorie": cat.strip(),
                "sous_categorie": souscat.strip(),
                "montant": montant_val,
                "montant_initial": data.get("montant_initial", montant_val),  # Conserver le montant OCR initial
                "date": date_edit,
                "source": data["source"]
            })

        st.session_state["revenus_data"] = updated_list

        st.markdown("---")
        toast_warning("Vérifie bien les informations avant de confirmer l'enregistrement.")

        if st.button("✅ Confirmer et enregistrer tous les revenus"):
            conn = get_db_connection()
            cursor = conn.cursor()

            for data in st.session_state["revenus_data"]:
                # 🔥 V2: Application Uber tax si nécessaire
                transaction_data = {
                    "type": "revenu",
                    "categorie": data["categorie"],
                    "sous_categorie": data["sous_categorie"],
                    "montant": data["montant"],
                    "date": data["date"].isoformat(),
                    "source": data["source"]
                }

                # Traitement Uber
                transaction_data, uber_msg = process_uber_revenue(transaction_data)
                if uber_msg:
                    toast_success("{uber_msg}")

                cursor.execute("""
                    INSERT INTO transactions (type, categorie, sous_categorie, montant, date, source)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    "revenu",
                    transaction_data["categorie"],
                    transaction_data["sous_categorie"],
                    transaction_data["montant"],
                    transaction_data["date"],
                    transaction_data["source"]
                ))

                target_dir = os.path.join(REVENUS_TRAITES, data["categorie"], data["sous_categorie"])
                os.makedirs(target_dir, exist_ok=True)

                shutil.move(data["path"], os.path.join(target_dir, data["file"]))

                # === ENREGISTRER LES STATISTIQUES OCR ===
                # Comparer le montant initial (OCR) avec le montant final (choisi par l'utilisateur)
                montant_initial = data.get("montant_initial", data["montant"])
                montant_final = data["montant"]

                # Déterminer le niveau de succès
                success_level = determine_success_level([montant_initial], montant_final)

                # Patterns pour les revenus (basiques, on peut enrichir plus tard)
                patterns_detectes = []
                if data["categorie"].lower() == "uber":
                    patterns_detectes = ["uber", "revenu", "pdf"]
                else:
                    patterns_detectes = ["salaire", "revenu", "pdf"]

                # Enregistrer le scan
                log_ocr_scan(
                    document_type="revenu",
                    filename=data["file"],
                    montants_detectes=[montant_initial],
                    montant_choisi=montant_final,
                    categorie=data["categorie"],
                    sous_categorie=data["sous_categorie"],
                    patterns_detectes=patterns_detectes,
                    success_level=success_level
                )

            conn.commit()
            conn.close()
            toast_success("Tous les revenus ont été enregistrés et rangés avec succès !")
            st.session_state.pop("revenus_data")

# =============================
#   TRANSACTION MANUELLE V2
# =============================
TRANSACTIONS_CSV = Path(BASE_DIR)/Path(DATA_DIR)/"transactions.csv"
COLUMNS = ["date", "categorie", "sous_categorie", "description", "montant", "type"]

def interface_transactions_unifiee():
    st.subheader("📊 Gestion des transactions (manuel + CSV) V2")

    os.makedirs("data", exist_ok=True)
    if not os.path.exists(TRANSACTIONS_CSV):
        pd.DataFrame(columns=COLUMNS).to_csv(TRANSACTIONS_CSV, index=False, encoding="utf-8")
        st.info("🆕 Fichier `transactions.csv` créé automatiquement.")

    try:
        df_base = pd.read_csv(TRANSACTIONS_CSV, encoding="utf-8")
    except UnicodeDecodeError:
        df_base = pd.read_csv(TRANSACTIONS_CSV, encoding="ISO-8859-1")

    conn = get_db_connection()
    df_sqlite = pd.read_sql_query("""
        SELECT date, categorie, sous_categorie, description, montant, type, source, recurrence
        FROM transactions
    """, conn)
    conn.close()

    st.markdown("#### 📥 Importer un ou plusieurs fichiers CSV de transactions")
    st.info("Les colonnes doivent être écrites sous ce format : `date`, `categorie`, `sous_categorie`, `description`, `montant`, `type`")
    st.info("💡 La colonne `description` peut être vide.")

    uploaded_files = st.file_uploader(
        "Glissez un ou plusieurs fichiers CSV ici",
        type=["csv"],
        accept_multiple_files=True
    )

    all_new_rows = []

    if uploaded_files:
        for uploaded in uploaded_files:
            raw_data = uploaded.read()
            encoding = detect(raw_data)["encoding"] or "utf-8"
            uploaded.seek(0)

            try:
                df_new = pd.read_csv(uploaded, encoding=encoding)
                if "date" in df_new.columns:
                    df_new["date"] = df_new["date"].apply(normaliser_date)
                if "montant" in df_new.columns:
                    df_new["montant"] = df_new["montant"].apply(nettoyer_montant)
            except Exception as e:
                logger.error(f"CSV import failed for {uploaded.name}: {e}")
                toast_error("Erreur lors de la lecture de {uploaded.name} : {e}")
                continue

            required_cols = ["date", "categorie", "sous_categorie", "description", "montant"]
            missing = [c for c in required_cols if c not in df_new.columns]
            if missing:
                toast_error("{uploaded.name} : colonnes manquantes ({', '.join(missing)})")
                st.error("Vérifiez bien l'orthographe des colonnes.")
                toast_error("Les transaction n'ont pas pu être ajoutée. Vérifiez bien le format du csv",10000)
                continue

            all_new_rows.append(df_new)
            toast_success("{uploaded.name} importé avec succès ({len(df_new)} lignes).")

        if all_new_rows:
            df_new_total = pd.concat(all_new_rows, ignore_index=True)

            for df in [df_base, df_new_total, df_sqlite]:
                for col in ["categorie", "sous_categorie", "description"]:
                    if col in df.columns:
                        df[col] = df[col].fillna("").astype(str).str.strip().str.lower()

            for df in [df_new_total, df_sqlite]:
                if "montant" in df.columns:
                    df["montant"] = df["montant"].apply(lambda x: safe_convert(x, float, 0.0))

            df_new_total = df_new_total.drop_duplicates(
                subset=["date", "montant", "categorie", "sous_categorie", "description"],
                keep="first"
            )

            df_combined = pd.concat([df_base, df_new_total], ignore_index=True)

            duplicates_internal = df_combined.duplicated(
                subset=["date", "montant", "categorie", "sous_categorie", "description"],
                keep=False
            )
            df_dupes_internal = df_combined[duplicates_internal]

            df_merged = df_new_total.merge(
                df_sqlite,
                on=["date", "montant", "categorie", "sous_categorie", "description"],
                how="left",
                indicator=True
            )
            df_dupes_sqlite = df_merged[df_merged["_merge"] != "left_only"]

            df_new_clean = df_merged[df_merged["_merge"] == "left_only"].drop(columns=["_merge"])

            if not df_dupes_internal.empty or not df_dupes_sqlite.empty:
                toast_warning("Doublons détectés :")
                if not df_dupes_internal.empty:
                    st.caption("🔁 Dans les fichiers importés / CSV local :")
                    st.dataframe(df_dupes_internal)
                if not df_dupes_sqlite.empty:
                    st.caption("🗄️ Déjà présents dans la base SQLite :")
                    st.dataframe(df_dupes_sqlite)

                keep_dupes = st.radio(
                    "Souhaitez-vous quand même conserver les doublons internes ?",
                    ["Non", "Oui"],
                    horizontal=True,
                    key="keep_dupes_choice"
                )
            else:
                keep_dupes = "Non"

            if keep_dupes == "Non":
                df_final = df_combined.drop_duplicates(
                    subset=["date", "montant", "categorie", "sous_categorie", "description"],
                    keep="first"
                )
            else:
                df_final = df_combined

            df_final.to_csv(TRANSACTIONS_CSV, index=False, encoding="utf-8")

            if not df_new_clean.empty:
                if "type" not in df_new_clean.columns:
                    toast_warning("Colonne 'type' absente — les lignes seront marquées comme 'dépense'.")
                    df_new_clean["type"] = "dépense"

                transactions_to_insert = []
                for _, row in df_new_clean.iterrows():
                    transaction = {
                        "type": str(row.get("type", "dépense")).strip().lower(),
                        "categorie": str(row["categorie"]).strip().lower(),
                        "sous_categorie": str(row.get("sous_categorie", "")).strip().lower(),
                        "description": str(row.get("description", "")).strip(),
                        "montant": safe_convert(row["montant"]),
                        "date": row["date"],
                        "source": "import_csv"
                    }
                    
                    # 🔥 V2: Traitement Uber pour les revenus
                    if transaction["type"] == "revenu":
                        transaction, uber_msg = process_uber_revenue(transaction)
                        if uber_msg:
                            toast_success("{uber_msg}")
                    
                    transactions_to_insert.append(transaction)

                insert_transaction_batch(transactions_to_insert)
                toast_success(f"{len(df_new_clean)} transaction(s) importée(s)")
                toast_success("Pensez à bien actualiser la page", 5000)
            else:
                st.info("ℹ️ Aucune nouvelle transaction à insérer (toutes déjà présentes).")

    st.markdown("---")
    st.markdown("#### ✍️ Ajouter manuellement une transaction")

    with st.form("add_manual"):
        col1, col2, col3 = st.columns(3)
        with col1:
            date_tr = st.date_input("Date", value=date.today())
            type_tr = st.selectbox("Type", ["dépense", "revenu"])
        with col2:
            cat = st.text_input("Catégorie principale")
            sous_cat = st.text_input("Sous-catégorie")
        with col3:
            montant = st.number_input("Montant (€)", min_value=0.0, step=0.01, format="%.2f")
            desc = st.text_input("Description")

        valider = st.form_submit_button("💾 Ajouter la transaction")

    if valider:
        if not cat or montant <= 0:
            toast_error("Veuillez entrer au moins une catégorie et un montant valide.")
        else:
            transaction_data = {
                "type": type_tr,
                "categorie": cat.strip().lower(),
                "sous_categorie": sous_cat.strip().lower(),
                "description": desc.strip(),
                "montant": float(montant),
                "date": date_tr.isoformat(),
                "source": "manuel"
            }
            
            # 🔥 V2: Traitement Uber pour les revenus
            if type_tr == "revenu":
                transaction_data, uber_msg = process_uber_revenue(transaction_data)
                if uber_msg:
                    st.success(uber_msg)

            new_line = pd.DataFrame([transaction_data])

            df_updated = pd.concat([df_base, new_line], ignore_index=True).drop_duplicates(
                subset=["date", "montant", "categorie", "sous_categorie", "description"],
                keep="first"
            ).reset_index(drop=True)

            df_updated.to_csv(TRANSACTIONS_CSV, index=False, encoding="utf-8")

            insert_transaction_batch([transaction_data])

            toast_success(f"Transaction ajoutée : {cat} — {transaction_data['montant']:.2f} €")
            toast_success("Pense à bien rafraichir la page")

    df_latest = pd.read_csv(TRANSACTIONS_CSV, encoding="utf-8")
    csv_buf = BytesIO()
    csv_buf.write(df_latest.to_csv(index=False).encode("utf-8"))

    st.download_button(
        label="⬇️ Télécharger le fichier CSV complet",
        data=csv_buf.getvalue(),
        file_name="transactions.csv",
        mime="text/csv"
    )

# =============================
# 🔁 AJOUTER UNE TRANSACTION RÉCURRENTE V2
# =============================
def interface_transaction_recurrente():
    st.subheader("🔁 Ajouter une dépense récurrente V2")

    with st.form("ajouter_transaction_recurrente", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            categorie = st.text_input("Catégorie principale (ex: logement, assurance, abonnement)")
            sous_categorie = st.text_input("Sous-catégorie (ex: EDF, Netflix, Loyer)")
            montant = st.number_input("Montant (€)", min_value=0.0, format="%.2f", step=0.01)
        with col2:
            recurrence = st.selectbox("Fréquence", ["hebdomadaire", "mensuelle", "annuelle"])
            date_debut = st.date_input("Date de début", date.today())
            date_fin = st.date_input("Date de fin (facultatif)", None)
        submit_btn = st.form_submit_button("💾 Enregistrer la récurrence")

    if submit_btn:
        if not categorie or montant <= 0:
            toast_error("Veuillez entrer une catégorie et un montant valide.")
            return

        safe_categorie = re.sub(r'[<>:"/\\|?*]', "_", categorie.strip())
        safe_sous_categorie = re.sub(r'[<>:"/\\|?*]', "_", sous_categorie.strip()) if sous_categorie else ""

        today = date.today()
        occurrences = []
        current_date = date_debut
        while current_date <= today:
            occurrences.append(current_date)
            if recurrence == "hebdomadaire":
                current_date += timedelta(weeks=1)
            elif recurrence == "mensuelle":
                current_date += relativedelta(months=1)
            elif recurrence == "annuelle":
                current_date += relativedelta(years=1)
            if date_fin and current_date > date_fin:
                break

        transactions = [
            {
                "type": "dépense",
                "categorie": safe_categorie,
                "sous_categorie": safe_sous_categorie,
                "montant": montant,
                "date": date_debut.isoformat(),
                "source": "récurrente",
                "recurrence": recurrence,
                "date_fin": date_fin.isoformat() if date_fin else ""
            }
        ] + [
            {
                "type": "dépense",
                "categorie": safe_categorie,
                "sous_categorie": safe_sous_categorie,
                "montant": montant,
                "date": d.isoformat(),
                "source": "récurrente_auto",
                "recurrence": recurrence
            } for d in occurrences
        ]

        insert_transaction_batch(transactions)
        toast_success(f"Transaction récurrente ajoutée ({recurrence})")
        st.info(f"{len(occurrences)} occurrence(s) passée(s) ajoutée(s).")

# ==============================
# 💼 INTERFACE AJOUTER UN REVENU V2
# ==============================
def interface_ajouter_revenu():
    st.subheader("💼 Ajouter un revenu V2")

    mode = st.selectbox(
        "Choisir le mode d'ajout du revenu :",
        ["Sélectionner...", "Scanner depuis le dossier", "Ajouter manuellement", "Revenu récurrent"]
    )

    if mode == "Scanner depuis le dossier":
        interface_process_all_revenues_in_folder()

    elif mode == "Ajouter manuellement":
        with st.form("ajouter_revenu_manuel", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                categorie = st.text_input("Catégorie principale (ex: Uber, Animation, Salaire)")
                sous_categorie = st.text_input("Sous-catégorie (ex: septembre, octobre, etc.)")
            with col2:
                montant = st.number_input("Montant (€)", min_value=0.0, format="%.2f", step=0.01)
                date_revenu = st.date_input("Date du revenu", date.today())

            submit_btn = st.form_submit_button("💾 Enregistrer le revenu")

        if submit_btn:
            if not categorie or montant <= 0:
                toast_error("Veuillez entrer une catégorie et un montant valide.")
                return

            transaction_data = {
                "type": "revenu",
                "categorie": categorie.strip(),
                "sous_categorie": sous_categorie.strip(),
                "montant": montant,
                "date": date_revenu.isoformat(),
                "source": "manuel"
            }
            
            # 🔥 V2: Traitement Uber automatique
            transaction_data, uber_msg = process_uber_revenue(transaction_data)
            if uber_msg:
                st.success(uber_msg)

            insert_transaction_batch([transaction_data])
            toast_success("Revenu manuel ajouté avec succès !")

    elif mode == "Revenu récurrent":
        with st.form("ajouter_revenu_recurrent", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                categorie = st.text_input("Catégorie principale (ex: Salaire, Bourse, CAF)")
                sous_categorie = st.text_input("Sous-catégorie (ex: septembre, octobre, etc.)")
                montant = st.number_input("Montant du revenu (€)", min_value=0.0, format="%.2f", step=0.01)
            with col2:
                recurrence = st.selectbox("Fréquence", ["mensuelle", "hebdomadaire", "annuelle"])
                date_debut = st.date_input("Date de début", date.today())
                date_fin = st.date_input("Date de fin (facultatif)", None)

            submit_btn = st.form_submit_button("💾 Enregistrer la récurrence")

        if submit_btn:
            if not categorie or montant <= 0:
                toast_error("Veuillez entrer une catégorie et un montant valide.")
                return

            safe_categorie = re.sub(r'[<>:"/\\|?*]', "_", categorie.strip())
            safe_sous_categorie = re.sub(r'[<>:"/\\|?*]', "_", sous_categorie.strip()) if sous_categorie else ""

            today = date.today()
            occurrences = []
            current_date = date_debut
            while current_date <= today:
                occurrences.append(current_date)
                if recurrence == "hebdomadaire":
                    current_date += timedelta(weeks=1)
                elif recurrence == "mensuelle":
                    current_date += relativedelta(months=1)
                elif recurrence == "annuelle":
                    current_date += relativedelta(years=1)
                if date_fin and current_date > date_fin:
                    break

            transactions = [
                {"type": "revenu", "categorie": safe_categorie, "sous_categorie": safe_sous_categorie,
                 "montant": montant, "date": date_debut.isoformat(), "source": "récurrente", "recurrence": recurrence,
                 "date_fin": date_fin.isoformat() if date_fin else ""}
            ] + [
                {"type": "revenu", "categorie": safe_categorie, "sous_categorie": safe_sous_categorie,
                 "montant": montant, "date": d.isoformat(), "source": "récurrente_auto", "recurrence": recurrence}
                for d in occurrences
            ]
            
            # 🔥 V2: Traitement Uber pour tous les revenus récurrents
            processed_transactions = []
            for transaction in transactions:
                if transaction["type"] == "revenu":
                    processed_transaction, uber_msg = process_uber_revenue(transaction)
                    if uber_msg and transaction is transactions[0]:  # Afficher seulement pour le modèle
                        st.success(uber_msg)
                    processed_transactions.append(processed_transaction)
                else:
                    processed_transactions.append(transaction)
            
            insert_transaction_batch(processed_transactions)
            toast_success(f"Revenu récurrent ({recurrence}) ajouté avec succès.")
            st.info(f"{len(occurrences)} versement(s) passé(s) ajouté(s).")

# =============================
# 🔁 GERER LES RECURRENCES V3
# =============================
def interface_gerer_recurrences():
    st.subheader("🔁 Gérer les transactions récurrentes V3 - Avec historique")
    
    # Tab pour séparer gestion et historique
    tab1, tab2 = st.tabs(["📝 Gérer les récurrences", "📊 Historique des versions"])
    
    with tab1:
        df = load_recurrent_transactions()

        if df.empty:
            st.info("Aucune transaction récurrente trouvée.")
            return

        # Grouper par catégorie/sous-catégorie pour avoir une vue unique par récurrence
        df_grouped = df.groupby(['categorie', 'sous_categorie']).agg({
            'id': 'first',
            'type': 'first',
            'montant': 'first',
            'recurrence': 'first',
            'date': 'first',
            'date_fin': 'first'
        }).reset_index()
        
        st.markdown("### 📋 Liste des récurrences actives")
        
        # Afficher les récurrences sous forme de cartes
        for idx, row in df_grouped.iterrows():
            with st.expander(f"{'🟢' if row['type'] == 'revenu' else '🔴'} {row['categorie']} → {row['sous_categorie']}", expanded=False):
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    st.metric("💰 Montant actuel", f"{safe_convert(row['montant'], float, 0.0):.2f} €")
                    st.caption(f"🔁 Récurrence : {row['recurrence']}")
                
                with col2:
                    date_debut = safe_date_convert(row['date'])
                    date_fin = safe_date_convert(row['date_fin']) if row['date_fin'] else None
                    st.caption(f"📅 Début : {date_debut.strftime('%d/%m/%Y')}")
                    if date_fin:
                        st.caption(f"📅 Fin : {date_fin.strftime('%d/%m/%Y')}")
                    else:
                        st.caption("📅 Fin : Indéterminée")
                
                with col3:
                    st.caption(f"Type : {row['type']}")
                
                st.markdown("---")
                st.markdown("#### ✏️ Modifier cette récurrence")
                
                # Formulaire de modification
                col_form1, col_form2 = st.columns(2)
                
                with col_form1:
                    new_montant = st.number_input(
                        "Nouveau montant (€)",
                        value=float(safe_convert(row['montant'], float, 0.0)),
                        step=0.01,
                        key=f"montant_{idx}"
                    )
                    
                    new_recurrence = st.selectbox(
                        "Récurrence",
                        ["hebdomadaire", "mensuelle", "annuelle"],
                        index=["hebdomadaire", "mensuelle", "annuelle"].index(row["recurrence"]),
                        key=f"rec_{idx}"
                    )
                
                with col_form2:
                    date_application = st.date_input(
                        "📅 Appliquer à partir du",
                        value=datetime.now().date(),
                        help="Les occurrences avant cette date garderont l'ancien montant",
                        key=f"date_app_{idx}"
                    )
                    
                    nouvelle_date_fin = st.date_input(
                        "📅 Date de fin",
                        value=date_fin if date_fin else datetime.now().date() + timedelta(days=365),
                        key=f"date_fin_{idx}"
                    )
                
                # Calcul de l'impact
                montant_actuel = safe_convert(row['montant'], float, 0.0)
                difference = new_montant - montant_actuel
                
                if difference != 0:
                    st.markdown("#### 💹 Impact prévisionnel")
                    
                    # Calculer l'impact sur 12 mois
                    if new_recurrence == "hebdomadaire":
                        occurrences_par_an = 52
                    elif new_recurrence == "mensuelle":
                        occurrences_par_an = 12
                    else:  # annuelle
                        occurrences_par_an = 1
                    
                    impact_annuel = difference * occurrences_par_an
                    impact_color = "green" if impact_annuel > 0 else "red"
                    impact_icon = "📈" if impact_annuel > 0 else "📉"
                    
                    col_imp1, col_imp2, col_imp3 = st.columns(3)
                    
                    with col_imp1:
                        st.metric("Différence par occurrence", f"{difference:+.2f} €")
                    
                    with col_imp2:
                        st.metric("Impact mensuel", f"{(difference * occurrences_par_an / 12):+.2f} €")
                    
                    with col_imp3:
                        st.metric("Impact annuel", f"{impact_annuel:+.2f} €")
                    
                    st.markdown(f"""
                    <div style='background: linear-gradient(135deg, {"#d1fae5" if impact_annuel > 0 else "#fee2e2"} 0%, {"#a7f3d0" if impact_annuel > 0 else "#fecaca"} 100%);
                         padding: 15px; border-radius: 10px; margin: 10px 0;
                         border-left: 5px solid {impact_color};'>
                        <strong>{impact_icon} Impact sur 12 mois : {impact_annuel:+.2f} €</strong>
                        <br><small>Cette modification {"augmentera" if impact_annuel > 0 else "réduira"} votre solde de {abs(impact_annuel):.2f}€ par an</small>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("---")
                
                # Boutons d'action
                col_btn1, col_btn2, col_btn3 = st.columns(3)
                
                with col_btn1:
                    if st.button("💾 Créer nouvelle version", key=f"save_{idx}", type="primary"):
                        # Créer une nouvelle version
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        
                        # 1. Mettre à jour l'ancienne version avec une date de fin
                        cursor.execute("""
                            UPDATE transactions 
                            SET date_fin = ?
                            WHERE source='récurrente_auto' 
                            AND categorie = ? 
                            AND sous_categorie = ?
                            AND (date_fin IS NULL OR date_fin > ?)
                        """, (
                            date_application.isoformat(),
                            row['categorie'],
                            row['sous_categorie'],
                            date_application.isoformat()
                        ))
                        
                        # 2. Créer la nouvelle version
                        cursor.execute("""
                            INSERT INTO transactions 
                            (type, categorie, sous_categorie, montant, date, source, recurrence, date_fin, description)
                            VALUES (?, ?, ?, ?, ?, 'récurrente_auto', ?, ?, ?)
                        """, (
                            row['type'],
                            row['categorie'],
                            row['sous_categorie'],
                            new_montant,
                            date_application.isoformat(),
                            new_recurrence,
                            nouvelle_date_fin.isoformat(),
                            f"Version créée le {datetime.now().strftime('%d/%m/%Y')} - Ancien montant: {montant_actuel:.2f}€"
                        ))
                        
                        conn.commit()
                        conn.close()
                        
                        st.success(f"""
                        ✅ **Nouvelle version créée !**
                        - Ancien montant : {montant_actuel:.2f}€ (jusqu'au {(date_application - timedelta(days=1)).strftime('%d/%m/%Y')})
                        - Nouveau montant : {new_montant:.2f}€ (à partir du {date_application.strftime('%d/%m/%Y')})
                        
                        Les transactions futures seront créées avec le nouveau montant.
                        """)
                        toast_success("c'est dur la france de Macron")
                        refresh_and_rerun()
                
                with col_btn2:
                    if st.button("🔄 Modifier toutes les occurrences", key=f"update_all_{idx}"):
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        
                        # Modifier toutes les occurrences (passées et futures)
                        cursor.execute("""
                            UPDATE transactions 
                            SET montant = ?, recurrence = ?, date_fin = ?
                            WHERE (source LIKE 'récurrente%' OR source = 'récurrence_auto')
                            AND categorie = ? 
                            AND sous_categorie = ?
                        """, (
                            new_montant,
                            new_recurrence,
                            nouvelle_date_fin.isoformat(),
                            row['categorie'],
                            row['sous_categorie']
                        ))
                        
                        conn.commit()
                        conn.close()
                        
                        st.success(f"""
                        ✅ **Toutes les occurrences modifiées !**
                        - Nouveau montant : {new_montant:.2f}€
                        - Récurrence : {new_recurrence}
                        
                        ⚠️ L'historique a été modifié.
                        """)
                        refresh_and_rerun()
                
                with col_btn3:
                    if st.button("🗑️ Supprimer", key=f"delete_{idx}"):
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        
                        cursor.execute("""
                            DELETE FROM transactions 
                            WHERE (source LIKE 'récurrente%' OR source = 'récurrence_auto')
                            AND categorie = ? 
                            AND sous_categorie = ?
                        """, (row['categorie'], row['sous_categorie']))
                        
                        conn.commit()
                        conn.close()
                        
                        st.success("🗑️ Récurrence supprimée entièrement.")
                        refresh_and_rerun()
    
    with tab2:
        st.markdown("### 📊 Historique des versions de récurrences")
        
        conn = get_db_connection()
        df_all = pd.read_sql_query("""
            SELECT * FROM transactions 
            WHERE source='récurrente_auto' 
            ORDER BY categorie, sous_categorie, date ASC
        """, conn)
        conn.close()
        
        if df_all.empty:
            st.info("Aucun historique disponible.")
            return
        
        # Grouper par catégorie/sous-catégorie
        for (cat, souscat), group in df_all.groupby(['categorie', 'sous_categorie']):
            st.markdown(f"#### {cat} → {souscat}")
            
            # Afficher l'historique des versions
            versions = []
            for idx, row in group.iterrows():
                date_debut = safe_date_convert(row['date'])
                date_fin = safe_date_convert(row['date_fin']) if row['date_fin'] else None
                montant = safe_convert(row['montant'], float, 0.0)
                
                versions.append({
                    'Version': f"V{len(versions) + 1}",
                    'Période': f"{date_debut.strftime('%d/%m/%Y')} → {date_fin.strftime('%d/%m/%Y') if date_fin else 'En cours'}",
                    'Montant': f"{montant:.2f} €",
                    'Récurrence': row['recurrence'],
                    'Type': row['type']
                })
            
            df_versions = pd.DataFrame(versions)
            st.dataframe(df_versions, use_container_width=True, hide_index=True)
            
            # Graphique d'évolution du montant
            if len(versions) > 1:
                st.markdown("##### 📈 Évolution du montant")
                
                fig, ax = plt.subplots(figsize=(10, 3))
                montants = [safe_convert(row['montant'], float, 0.0) for _, row in group.iterrows()]
                dates = [safe_date_convert(row['date']) for _, row in group.iterrows()]
                
                ax.plot(dates, montants, marker='o', linewidth=2, markersize=8, color='#667eea')
                ax.set_xlabel("Date", fontweight='bold')
                ax.set_ylabel("Montant (€)", fontweight='bold')
                ax.set_title(f"Évolution du montant - {cat}", fontweight='bold')
                ax.grid(True, alpha=0.3)
                plt.xticks(rotation=45)
                plt.tight_layout()
                
                st.pyplot(fig)
            
            st.markdown("---")

# =============================
# 🛠️ GERER LES TRANSACTIONS V2
# =============================
def interface_gerer_transactions():
    st.subheader("🛠️ Gérer les transactions (modifier ou supprimer) V2")

    df_all = load_transactions()

    if df_all.empty:
        st.info("Aucune transaction à gérer pour le moment.")
        return

    type_filter = st.selectbox("Type", ["Toutes", "revenu", "dépense"], key="type_filtre_gerer_v2")
    
    df_for_cat = df_all.copy()
    if type_filter != "Toutes":
        df_for_cat = df_for_cat[df_for_cat["type"] == type_filter]
    
    cat_filter = st.selectbox("Catégorie", ["Toutes"] + sorted(df_for_cat["categorie"].dropna().unique().tolist()), key="cat_filtre_gerer_v2")
    
    df_for_souscat = df_for_cat.copy()
    if cat_filter != "Toutes":
        df_for_souscat = df_for_souscat[df_for_souscat["categorie"] == cat_filter]
    
    souscat_filter = st.selectbox("Sous-catégorie", ["Toutes"] + sorted(df_for_souscat["sous_categorie"].dropna().unique().tolist()), key="souscat_filtre_gerer_v2")

    df = df_all.copy()
    if type_filter != "Toutes": 
        df = df[df["type"] == type_filter]
    if cat_filter != "Toutes": 
        df = df[df["categorie"] == cat_filter]
    if souscat_filter != "Toutes": 
        df = df[df["sous_categorie"] == souscat_filter]

    if df.empty:
        st.warning("Aucune transaction trouvée avec ces filtres.")
        return

    st.markdown("---")
    st.info(f"💡 **{len(df)} transaction(s) trouvée(s)** - Modifie les valeurs directement ou coche les lignes à supprimer.")
    
    df["🗑️ Supprimer"] = False
    
    df_edit = st.data_editor(
        df, 
        use_container_width=True, 
        num_rows="fixed", 
        key="editor_transactions_v2",
        hide_index=True,
        column_config={
            "id": st.column_config.NumberColumn("ID", disabled=True),
            "type": st.column_config.SelectboxColumn("Type", options=["dépense", "revenu"]),
            "categorie": st.column_config.TextColumn("Catégorie"),
            "sous_categorie": st.column_config.TextColumn("Sous-catégorie"),
            "description": st.column_config.TextColumn("Description"),
            "montant": st.column_config.NumberColumn("Montant (€)", format="%.2f"),
            "date": st.column_config.DateColumn("Date", format="DD/MM/YYYY"),
            "source": st.column_config.TextColumn("Source", disabled=True),
            "recurrence": st.column_config.TextColumn("Récurrence", disabled=True),
            "date_fin": st.column_config.TextColumn("Date fin", disabled=True),
            "🗑️ Supprimer": st.column_config.CheckboxColumn("🗑️ Supprimer")
        }
    )

    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💾 Enregistrer les modifications", type="primary"):
            conn = get_db_connection()
            cursor = conn.cursor()
            modified_count = 0
            
            for idx, row in df_edit.iterrows():
                original_row = df[df["id"] == row["id"]].iloc[0]
                
                has_changes = False
                for col in ["categorie", "sous_categorie", "description", "montant", "date", "type"]:
                    if str(row[col]) != str(original_row[col]):
                        has_changes = True
                        break
                
                if has_changes:
                    transaction_data = {
                        'type': row['type'],
                        'categorie': row['categorie'],
                        'sous_categorie': row['sous_categorie'],
                        'description': row['description'],
                        'montant': safe_convert(row['montant']),
                        'date': safe_date_convert(row['date']).isoformat(),
                        'recurrence': row.get('recurrence', '')
                    }
                    
                    # 🔥 V2: Validation des données
                    errors = validate_transaction_data(transaction_data)
                    if errors:
                        st.warning(f"Ligne {row['id']} invalide: {', '.join(errors)}")
                        continue
                    
                    # 🔥 V2: Traitement Uber pour les revenus
                    if transaction_data['type'] == 'revenu':
                        transaction_data, uber_msg = process_uber_revenue(transaction_data)
                        if uber_msg:
                            toast_success("Revenu Uber ajusté: {uber_msg}")
                    
                    cursor.execute("""
                        UPDATE transactions 
                        SET type=?, categorie=?, sous_categorie=?, description=?, montant=?, date=?, recurrence=?
                        WHERE id=?
                    """, (
                        transaction_data['type'], transaction_data['categorie'],
                        transaction_data['sous_categorie'], transaction_data['description'],
                        transaction_data['montant'], transaction_data['date'],
                        transaction_data['recurrence'], row['id']
                    ))
                    
                    modified_count += 1

            conn.commit()
            conn.close()
            
            if modified_count > 0:
                toast_success("{modified_count} transaction(s) mise(s) à jour avec succès")
                refresh_and_rerun()
            else:
                st.info("ℹ️ Aucune modification validée")

    with col2:
        if st.button("🚮 Supprimer les transactions cochées", type="secondary"):
            if "🗑️ Supprimer" in df_edit.columns:
                to_delete = df_edit[df_edit["🗑️ Supprimer"] == True]
            else:
                to_delete = pd.DataFrame()
            
            if not to_delete.empty:
                conn = get_db_connection()
                cursor = conn.cursor()
                for _, row in to_delete.iterrows():
                    cursor.execute("DELETE FROM transactions WHERE id=?", (row["id"],))
                conn.commit()
                conn.close()
                toast_success(f"{len(to_delete)} transaction(s) supprimée(s)")
                refresh_and_rerun()
            else:
                toast_warning("Coche au moins une transaction avant de supprimer.")

# =============================
# 📊 VOIR TOUTES LES TRANSACTIONS V2
# =============================
def interface_voir_transactions():
    st.subheader("📊 Voir toutes les transactions V2")
    
    backfill_recurrences_to_today(DB_PATH)

    df = load_transactions()

    if df.empty:
        st.info("Aucune transaction enregistrée pour le moment.")
        return

    st.markdown("### 🎯 Filtres rapides")
    
    # 🔥 NOUVEAU : FILTRE DE PÉRIODE
    st.markdown("#### 📅 Période d'analyse")
    
    col_p1, col_p2, col_p3 = st.columns([2, 2, 2])
    
    with col_p1:
        periode_rapide = st.selectbox(
            "**Période rapide**",
            [
                "📅 Tout voir",
                "📆 Ce mois-ci",
                "📆 Mois dernier", 
                "📆 30 derniers jours",
                "📆 90 derniers jours",
                "📆 Cette année",
                "📆 Année dernière",
                "🎯 Personnalisée"
            ]
        )
    
    # Calculer les dates selon la période sélectionnée
    today = datetime.now().date()
    
    if periode_rapide == "📅 Tout voir":
        date_debut_filtre = None
        date_fin_filtre = None
    elif periode_rapide == "📆 Ce mois-ci":
        date_debut_filtre = today.replace(day=1)
        date_fin_filtre = today
    elif periode_rapide == "📆 Mois dernier":
        premier_jour_mois = today.replace(day=1)
        dernier_jour_mois_dernier = premier_jour_mois - timedelta(days=1)
        date_debut_filtre = dernier_jour_mois_dernier.replace(day=1)
        date_fin_filtre = dernier_jour_mois_dernier
    elif periode_rapide == "📆 30 derniers jours":
        date_debut_filtre = today - timedelta(days=30)
        date_fin_filtre = today
    elif periode_rapide == "📆 90 derniers jours":
        date_debut_filtre = today - timedelta(days=90)
        date_fin_filtre = today
    elif periode_rapide == "📆 Cette année":
        date_debut_filtre = today.replace(month=1, day=1)
        date_fin_filtre = today
    elif periode_rapide == "📆 Année dernière":
        date_debut_filtre = today.replace(year=today.year-1, month=1, day=1)
        date_fin_filtre = today.replace(year=today.year-1, month=12, day=31)
    else:  # Personnalisée
        date_debut_filtre = None
        date_fin_filtre = None
    
    # Si période personnalisée, afficher les sélecteurs de date
    if periode_rapide == "🎯 Personnalisée":
        with col_p2:
            date_debut_filtre = st.date_input(
                "**Date début**",
                value=today - timedelta(days=30),
                max_value=today
            )
        with col_p3:
            date_fin_filtre = st.date_input(
                "**Date fin**",
                value=today,
                max_value=today
            )
    else:
        with col_p2:
            if date_debut_filtre:
                st.metric("**Date début**", date_debut_filtre.strftime("%d/%m/%Y"))
            else:
                st.metric("**Date début**", "Début")
        with col_p3:
            if date_fin_filtre:
                st.metric("**Date fin**", date_fin_filtre.strftime("%d/%m/%Y"))
            else:
                st.metric("**Date fin**", "Aujourd'hui")
    
    st.markdown("---")
    st.markdown("#### 🔢 Tri et affichage")
    
    col_t1, col_t2 = st.columns([3, 3])
    
    with col_t1:
        tri_option = st.selectbox(
            "**📊 Trier par**",
            [
                "📅 Date (plus récent → plus ancien)",
                "📅 Date (plus ancien → plus récent)",
                "💰 Montant (plus élevé → plus bas)",
                "💰 Montant (plus bas → plus élevé)"
            ],
            index=0  # Par défaut : Date décroissante
        )
    
    with col_t2:
        limit_display = st.checkbox("📋 Limiter affichage", value=False)
        if limit_display:
            nb_lignes = st.number_input("Nombre de lignes", min_value=5, max_value=100, value=10, step=5)
    
    st.markdown("---")
    st.markdown("#### 🔍 Autres filtres")
    
    col1, col2, col3 = st.columns([2, 2, 2])
    
    with col1:
        type_filter = st.selectbox("**Type**", ["Toutes", "revenu", "dépense"])
        
    with col2:
        categories = ["Toutes"] + sorted(df["categorie"].dropna().unique().tolist())
        cat_filter = st.selectbox("**Catégorie**", categories)
        
    with col3:
        filtre_documents = st.selectbox(
            "**Documents**",
            ["Tous", "🧾 Tickets", "💼 Bulletins", "📄 Factures", "📝 Sans docs"]
        )

    # 🔥 APPLIQUER LE FILTRE DE PÉRIODE
    df_filtered = df.copy()
    
    # Convertir la colonne date en datetime pour le filtrage
    df_filtered["date"] = pd.to_datetime(df_filtered["date"])
    
    if date_debut_filtre and date_fin_filtre:
        df_filtered = df_filtered[
            (df_filtered["date"].dt.date >= date_debut_filtre) &
            (df_filtered["date"].dt.date <= date_fin_filtre)
        ]
    elif date_debut_filtre:
        df_filtered = df_filtered[df_filtered["date"].dt.date >= date_debut_filtre]
    elif date_fin_filtre:
        df_filtered = df_filtered[df_filtered["date"].dt.date <= date_fin_filtre]
    
    # Autres filtres
    if type_filter != "Toutes": 
        df_filtered = df_filtered[df_filtered["type"] == type_filter]
    if cat_filter != "Toutes": 
        df_filtered = df_filtered[df_filtered["categorie"] == cat_filter]

    if filtre_documents == "🧾 Tickets":
        df_filtered = df_filtered[df_filtered["source"] == "OCR"]
    elif filtre_documents == "💼 Bulletins":
        df_filtered = df_filtered[(df_filtered["source"] == "PDF") & (df_filtered["type"] == "revenu")]
    elif filtre_documents == "📄 Factures":
        df_filtered = df_filtered[(df_filtered["source"] == "PDF") & (df_filtered["type"] == "dépense")]
    elif filtre_documents == "📝 Sans docs":
        df_filtered = df_filtered[~df_filtered["source"].isin(["OCR", "PDF"])]

    # 🔥 APPLIQUER LE TRI SELON LE CHOIX DE L'UTILISATEUR
    if tri_option == "📅 Date (plus récent → plus ancien)":
        df_filtered = df_filtered.sort_values("date", ascending=False)
    elif tri_option == "📅 Date (plus ancien → plus récent)":
        df_filtered = df_filtered.sort_values("date", ascending=True)
    elif tri_option == "💰 Montant (plus élevé → plus bas)":
        df_filtered = df_filtered.sort_values("montant", ascending=False)
    elif tri_option == "💰 Montant (plus bas → plus élevé)":
        df_filtered = df_filtered.sort_values("montant", ascending=True)
    
    # 🔥 APPLIQUER LA LIMITATION APRÈS LE TRI
    if limit_display and len(df_filtered) > nb_lignes:
        df_display = df_filtered.head(nb_lignes)
        st.info(f"📋 Affichage des {nb_lignes} premières transactions (selon le tri : {tri_option}) sur {len(df_filtered)} trouvées")
    else:
        df_display = df_filtered

    if df_display.empty:
        st.warning("🎯 Aucune transaction trouvée avec ces filtres.")
        return


    # 🔥 STATISTIQUES DE LA PÉRIODE
    if not df_filtered.empty and (date_debut_filtre or date_fin_filtre):
        st.markdown("---")
        st.markdown("### 📊 Résumé de la période")
        
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        
        with col_s1:
            nb_jours = (date_fin_filtre - date_debut_filtre).days + 1 if date_debut_filtre and date_fin_filtre else len(df_filtered)
            st.metric("📅 Durée", f"{nb_jours} jours")
        
        with col_s2:
            total_revenus_periode = df_filtered[df_filtered["type"] == "revenu"]["montant"].sum()
            st.metric("💰 Revenus", f"{total_revenus_periode:,.2f} €")
        
        with col_s3:
            total_depenses_periode = df_filtered[df_filtered["type"] == "dépense"]["montant"].sum()
            st.metric("💸 Dépenses", f"{total_depenses_periode:,.2f} €")
        
        with col_s4:
            solde_periode = total_revenus_periode - total_depenses_periode
            delta_color = "normal" if solde_periode >= 0 else "inverse"

    st.markdown("### 📋 Transactions récentes")
    
    df_table = df_display.copy()
    # 🔥 CORRECTION : Convertir montant en float AVANT tout traitement
    df_table["montant"] = df_table["montant"].apply(lambda x: safe_convert(x, float, 0.0))
    
    def get_type_icon(row_type):
        return "🟢" if row_type == "revenu" else "🔴"
    
    df_table["Type"] = df_table["type"].apply(get_type_icon)
    
    def get_doc_icon(source):
        if source == "OCR":
            return "🧾"
        elif source == "PDF":
            return "📄"
        else:
            return "📝"
    
    df_table["Doc"] = df_table["source"].apply(get_doc_icon)
    
    # 🔥 CORRECTION : Créer une colonne montant_signed pour le tri numérique correct
    # Les dépenses deviennent négatives pour un tri cohérent
    df_table["montant_signed"] = df_table.apply(
        lambda row: row["montant"] if row["type"] == "revenu" else -row["montant"], 
        axis=1
    )
    
    df_table["Date"] = pd.to_datetime(df_table["date"]).dt.strftime("%d/%m/%Y")
    
    display_columns = {
        "Type": "Type",
        "Doc": "Doc",
        "Date": "Date", 
        "categorie": "Catégorie",
        "sous_categorie": "Sous-catégorie",
        "montant_signed": "Montant (€)",
        "description": "Description"
    }
    
    st.dataframe(
        df_table[list(display_columns.keys())].rename(columns=display_columns),
        use_container_width=True,
        height=400,
        hide_index=True,
        column_config={
            "Montant (€)": st.column_config.NumberColumn(
                "Montant (€)",
                format="%.2f €"
            )
        }
    )

    st.markdown("---")
    
    df_display["montant"] = df_display["montant"].apply(lambda x: safe_convert(x, float, 0.0))
    
    total_revenus = df_display[df_display["type"]=="revenu"]["montant"].sum()
    total_depenses = df_display[df_display["type"]=="dépense"]["montant"].sum()
    solde = total_revenus - total_depenses
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Transactions", len(df_display))
    
    with col2:
        avec_docs = len(df_display[df_display["source"].isin(["OCR", "PDF"])])
        st.metric("📎 Avec documents", avec_docs)
    
    with col3:
        st.metric("💸 Revenus", f"{total_revenus:.2f} €")
    
    with col4:
        st.metric("💳 Dépenses", f"{total_depenses:.2f} €")

    solde_color = "green" if solde >= 0 else "red"
    solde_icon = "📈" if solde >= 0 else "📉"
    
    st.markdown(f"""
    <div style='text-align: center; padding: 20px; background-color: #f8f9fa; border-radius: 10px; margin: 20px 0;'>
        <h2 style='color: {solde_color}; margin: 0;'>
            {solde_icon} Solde : {solde:+.2f} €
        </h2>
    </div>
    """, unsafe_allow_html=True)

    if len(df_display) > 0:
        with st.expander("🔍 Voir les détails et documents", expanded=False):
            st.markdown("### 📋 Détails des transactions")
            
            for idx, transaction in df_display.iterrows():
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 1])
                    
                    with col1:
                        source = transaction['source']
                        if source == "OCR":
                            badge = "🧾 Ticket de caisse"
                            couleur = "#1f77b4"
                        elif source == "PDF":
                            if transaction['type'] == "revenu":
                                badge = "💼 Bulletin de paie"
                                couleur = "#2ca02c"
                            else:
                                badge = "📄 Facture"
                                couleur = "#ff7f0e"
                        else:
                            badge = "📝 Transaction manuelle"
                            couleur = "#7f7f7f"
                        
                        st.markdown(f"<span style='background-color: {couleur}; color: white; padding: 4px 12px; border-radius: 16px; font-size: 0.8em; font-weight: bold;'>{badge}</span>", 
                                   unsafe_allow_html=True)
                        
                        st.write(f"**{transaction['categorie']}** → {transaction['sous_categorie']}")
                        if transaction.get('description'):
                            st.caption(f"📝 {transaction['description']}")
                            
                    with col2:
                        st.write(f"📅 {transaction['date']}")
                        if transaction.get('recurrence'):
                            st.caption(f"🔁 {transaction['recurrence']}")
                            
                    with col3:
                        montant_val = safe_convert(transaction['montant'], float, 0.0)
                        montant_color = "green" if transaction['type'] == 'revenu' else "red"
                        montant_prefix = "+" if transaction['type'] == 'revenu' else "-"
                        st.markdown(f"<h4 style='color: {montant_color}; text-align: right;'>{montant_prefix}{montant_val:.2f} €</h4>", unsafe_allow_html=True)
                    
                    if transaction['source'] in ['OCR', 'PDF']:
                        if st.button("👀 Voir les documents", key=f"view_{idx}", type="secondary"):
                            st.session_state[f'selected_transaction_{idx}'] = transaction.to_dict()
                    
                    if f'selected_transaction_{idx}' in st.session_state:
                        st.markdown("---")
                        st.markdown("#### 📎 Documents associés")
                        afficher_documents_associes(st.session_state[f'selected_transaction_{idx}'])
                        
                        if st.button("❌ Fermer", key=f"close_{idx}"):
                            del st.session_state[f'selected_transaction_{idx}']
                            refresh_and_rerun()
                    
                    st.markdown("---")
# =============================
# 💹 Solde prévisionnel V2
# =============================
def interface_solde_previsionnel():
    st.header("💹 Solde prévisionnel V2")

    tab1, tab2, tab3 = st.tabs([
        "📈 Analyse prévisionnelle",
        "🧮 Ajouter des prévisions", 
        "📊 Suivi du portefeuille"
    ])

    with tab1:
        st.subheader("📊 Analyse prévisionnelle V2")

        df = load_transactions()

        if df.empty:
            st.info("Aucune transaction enregistrée pour le moment.")
        else:
            revenus = df[df["type"] == "revenu"]["montant"].sum()
            depenses = df[df["type"] == "dépense"]["montant"].sum()
            solde_actuel = revenus - depenses

            st.metric("💰 Solde actuel", f"{solde_actuel:,.2f} €")

            date_projection = st.date_input(
                "Date de projection", 
                value=date.today() + timedelta(days=90)
            )
            proj_ts = pd.Timestamp(date_projection)
            today_ts = pd.Timestamp(datetime.now().date())

            rec_df = df[
                (df["recurrence"].notna()) &
                (df["source"].isin(["récurrence_auto", "récurrente_auto"]))
            ]

            occurrences = []

            for _, row in rec_df.iterrows():
                start_date = row["date"]
                recurrence = row["recurrence"]
                current_date = pd.Timestamp(start_date)

                while current_date <= proj_ts:
                    if current_date >= today_ts:
                        occurrences.append({
                            "date": current_date,
                            "type": row["type"],
                            "categorie": row["categorie"],
                            "sous_categorie": row["sous_categorie"],
                            "montant": safe_convert(row["montant"]),
                            "description": row.get("description", "")
                        })

                    if recurrence == "hebdomadaire":
                        current_date += pd.Timedelta(weeks=1)
                    elif recurrence == "mensuelle":
                        current_date += pd.DateOffset(months=1)
                    elif recurrence == "annuelle":
                        current_date += pd.DateOffset(years=1)
                    else:
                        break

            if occurrences:
                occ_df = pd.DataFrame(occurrences)

                occ_df = occ_df.drop_duplicates(
                    subset=["date", "type", "categorie", "sous_categorie", "montant"]
                )

                occ_df = occ_df.sort_values("date").reset_index(drop=True)
                solde_cum = [solde_actuel]
                for _, row in occ_df.iterrows():
                    dernier_solde = solde_cum[-1]
                    if row["type"] == "revenu":
                        solde_cum.append(dernier_solde + safe_convert(row["montant"]))
                    else:
                        solde_cum.append(dernier_solde - safe_convert(row["montant"]))
                occ_df["solde_previsionnel"] = solde_cum[1:]

                st.subheader("📅 Occurrences futures des transactions récurrentes")
                st.dataframe(
                    occ_df[["date", "type", "categorie", "sous_categorie", "montant", "solde_previsionnel"]],
                    use_container_width=True
                )

                st.metric(
                    "💹 Solde prévisionnel au " + date_projection.strftime("%d/%m/%Y"),
                    f"{solde_cum[-1]:,.2f} €"
                )

                st.subheader("📈 Évolution du solde prévisionnel")
                fig, ax = plt.subplots(figsize=(8, 4))
                ax.plot(occ_df["date"], occ_df["solde_previsionnel"], marker="o", linestyle="-")
                ax.axhline(0, color="gray", linewidth=0.8, linestyle="--")
                ax.set_xlabel("Date")
                ax.set_ylabel("Solde (€)")
                ax.set_title("Variation du solde prévisionnel dans le temps")
                plt.xticks(rotation=45)
                plt.tight_layout()
                st.pyplot(fig)

            else:
                st.info("Aucune transaction récurrente à venir trouvée jusqu'à la date de projection.")

    with tab2:
        st.subheader("🧮 Ajouter des prévisions temporaires")
        with st.form("form_prevision"):
            type_prevision = st.selectbox("Type de prévision", ["revenu","dépense"])
            categorie = st.text_input("Catégorie")
            sous_categorie = st.text_input("Sous-catégorie")
            montant = st.number_input("Montant (€)", min_value=0.0, step=10.0)
            date_prevision = st.date_input("Date de la prévision", value=date.today()+timedelta(days=30))
            submit_prevision = st.form_submit_button("Ajouter la prévision")
        
        if submit_prevision:
            transaction_data = {
                "type": type_prevision,
                "categorie": categorie,
                "sous_categorie": sous_categorie, 
                "montant": montant,
                "date": date_prevision.isoformat(),
                "source": "prévision_temp"
            }
            
            # 🔥 V2: Traitement Uber pour les revenus
            if type_prevision == "revenu":
                transaction_data, uber_msg = process_uber_revenue(transaction_data)
                if uber_msg:
                    st.success(uber_msg)
            
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""INSERT INTO transactions (type, categorie, sous_categorie, montant, date, source) VALUES (?,?,?,?,?,?)""",
                         (transaction_data["type"], transaction_data["categorie"], transaction_data["sous_categorie"], 
                          transaction_data["montant"], transaction_data["date"], transaction_data["source"]))
            conn.commit()
            conn.close()
            toast_success("Prévision {type_prevision} ajoutée pour le {date_prevision.strftime('%d/%m/%Y')}")

    with tab3:
        st.subheader("💹 Suivi du portefeuille V2")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS portefeuille (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                valeur_reelle REAL
            )
        """)
        conn.commit()

        df_portefeuille = pd.read_sql_query("SELECT * FROM portefeuille ORDER BY date ASC", conn)
        if not df_portefeuille.empty:
            df_portefeuille["date"] = pd.to_datetime(df_portefeuille["date"]).dt.date

        sous_tab1, sous_tab2, sous_tab3 = st.tabs([
            "📈 Simulation théorique",
            "💰 Valeur actuelle du portefeuille", 
            "🚀 Stratégie de rattrapage"
        ])

        with sous_tab1:
            st.markdown("### 📈 Simulation de l'évolution théorique")
            capital_depart_theo = st.number_input("💵 Capital de départ (€)", value=1625.0, step=100.0, key="capital_depart_theo_v2")
            rendement_cible_theo = st.number_input("🎯 Rendement cible annuel (%)", value=8.0, step=0.1, key="rendement_theo_v2")
            versement_mensuel_theo = st.number_input("📆 Versement mensuel (€)", value=430.0, step=10.0, key="versement_theo_v2")
            duree_annees_theo = st.slider("Durée de la simulation (années)", 1, 10, 2, key="duree_theo_v2")

            taux_mensuel = rendement_cible_theo / 100 / 12
            dates_sim = pd.date_range(start=date.today(), periods=duree_annees_theo * 12, freq='MS')

            valeurs_theoriques = []
            valeur = capital_depart_theo
            for _ in dates_sim:
                valeurs_theoriques.append(round(valeur, 2))
                valeur = valeur * (1 + taux_mensuel) + versement_mensuel_theo

            fig, ax = plt.subplots(figsize=(10, 5))
            ax.plot(dates_sim, valeurs_theoriques, label="Courbe théorique", color="blue", linewidth=2)
            ax.set_title("Simulation théorique de l'évolution du portefeuille")
            ax.set_xlabel("Date")
            ax.set_ylabel("Valeur (€)")
            ax.grid(True, linestyle="--", alpha=0.5)
            ax.legend()
            st.pyplot(fig)

            st.info(f"Valeur projetée après {duree_annees_theo} ans : **{valeurs_theoriques[-1]:,.2f} €**")

        with sous_tab2:
            st.markdown("### 💰 Enregistrement de la valeur réelle du portefeuille")

            mode_saisie = st.radio(
                "Choisir le type d'enregistrement :",
                ["📅 Ajouter une valeur pour aujourd'hui", "🕒 Ajouter une valeur pour une autre date"],
                horizontal=True,
                key="mode_saisie_v2"
            )

            if mode_saisie == "📅 Ajouter une valeur pour aujourd'hui":
                date_saisie = datetime.now().date()
            else:
                date_saisie = st.date_input("📆 Sélectionner la date", value=datetime.now().date(), key="date_saisie_v2")

            valeur_actuelle = st.number_input("💶 Valeur réelle (€)", value=0.0, step=10.0, key="valeur_actuelle_v2")

            btn_valider = st.button("💾 Enregistrer cette valeur", key="btn_valider_v2")

            if btn_valider:
                if valeur_actuelle <= 0:
                    toast_warning("Merci d'entrer une valeur supérieure à 0.")
                else:
                    cursor.execute("SELECT valeur_reelle FROM portefeuille WHERE date = ?", (date_saisie.isoformat(),))
                    existing = cursor.fetchone()

                    if existing:
                        toast_warning("Une valeur existe déjà pour le {date_saisie.strftime('%d/%m/%Y')} ({existing[0]:,.2f} €)")
                        if st.button("📝 Remplacer la valeur existante"):
                            cursor.execute(
                                "UPDATE portefeuille SET valeur_reelle = ? WHERE date = ?",
                                (valeur_actuelle, date_saisie.isoformat())
                            )
                            conn.commit()
                            toast_success("Valeur mise à jour pour le {date_saisie.strftime('%d/%m/%Y')} ({valeur_actuelle:,.2f} €)")
                    else:
                        cursor.execute(
                            "INSERT INTO portefeuille (date, valeur_reelle) VALUES (?, ?)",
                            (date_saisie.isoformat(), valeur_actuelle)
                        )
                        conn.commit()
                        toast_success("Valeur enregistrée ({valeur_actuelle:,.2f} €) le {date_saisie.strftime('%d/%m/%Y')}")

                df_portefeuille = pd.read_sql_query("SELECT * FROM portefeuille ORDER BY date ASC", conn)
                if not df_portefeuille.empty:
                    df_portefeuille["date"] = pd.to_datetime(df_portefeuille["date"]).dt.date

            if df_portefeuille.empty:
                st.info("Aucune valeur réelle enregistrée pour le moment.")
            else:
                st.line_chart(df_portefeuille.set_index("date")["valeur_reelle"])

        with sous_tab3:
            st.markdown("### 🚀 Stratégie de rattrapage (deux modes)")

            if df_portefeuille.empty:
                toast_warning("Enregistre d'abord au moins une valeur réelle dans l'onglet précédent.")
            else:
                montant_depart = safe_convert(df_portefeuille["valeur_reelle"].iloc[-1], float, 0.0)
                date_depart = df_portefeuille["date"].iloc[-1]
                st.info(f"Dernière valeur enregistrée : {montant_depart:,.2f} € ({date_depart.strftime('%d/%m/%Y')})")

                mode = st.radio("Choisir le mode :", 
                                ("Entrer un montant → calculer la date (mode montant→date)",
                                 "Entrer une date → calculer le montant (mode date→montant)"),
                                key="rattrap_mode_v2")

                capital_theo = st.number_input("💵 Capital théorique actuel (€)", value=2800.0, step=100.0, key="r_capital_theo_v2")
                rendement_cible = st.number_input("🎯 Rendement cible annuel (%)", value=8.0, step=0.1, key="r_rendement_v2")
                versement_mensuel = st.number_input("📆 Versement mensuel (€)", value=430.0, step=10.0, key="r_versement_mensuel_v2")
                freq_common = st.selectbox("📅 Fréquence du versement supplémentaire", 
                                           ["Journalière", "Hebdomadaire", "Mensuelle", "Annuelle"], key="r_freq_common_v2")

                taux_journalier = (1 + rendement_cible / 100) ** (1 / 365) - 1
                freq_to_days = {"Journalière": 1, "Hebdomadaire": 7, "Mensuelle": 30, "Annuelle": 365}
                pas_days_common = freq_to_days[freq_common]

                if mode.startswith("Entrer un montant"):
                    st.subheader("Mode : montant → date (combien de temps pour rattraper ?)")

                    montant_suppl = st.number_input("💸 Montant supplémentaire par période (selon la fréquence choisie)", 
                                                    value=10.0, step=1.0, key="r_montant_suppl_modeA_v2")
                    max_days = st.number_input("Limite maximale de simulation (jours)", value=2000, step=1, key="r_max_days_v2")

                    if st.button("⚡ Calculer la date de rattrapage", key="btn_calc_date_rattrap_v2"):
                        montant_reel = montant_depart
                        montant_theo = capital_theo
                        montant_rattrap = montant_depart
                        jours = 0
                        dates, theo_series, reel_series, rattrap_series = [], [], [], []

                        if montant_rattrap >= montant_theo:
                            toast_success("Tu es déjà au-dessus de la courbe théorique.")
                        else:
                            while montant_rattrap < montant_theo and jours < int(max_days):
                                current_date = date.today() + timedelta(days=jours)
                                dates.append(current_date)

                                montant_reel *= (1 + taux_journalier)
                                montant_theo *= (1 + taux_journalier)
                                montant_rattrap *= (1 + taux_journalier)

                                if jours % 30 == 0 and jours > 0:
                                    montant_reel += versement_mensuel
                                    montant_theo += versement_mensuel
                                    montant_rattrap += versement_mensuel

                                if jours % pas_days_common == 0:
                                    montant_rattrap += montant_suppl

                                theo_series.append(montant_theo)
                                reel_series.append(montant_reel)
                                rattrap_series.append(montant_rattrap)
                                jours += 1

                            if montant_rattrap >= montant_theo:
                                date_rattrap = date.today() + timedelta(days=jours-1)
                                delta = date_rattrap - date.today()
                                jours_tot = delta.days
                                mois = jours_tot // 30
                                semaines = jours_tot // 7
                                st.success(f"🎯 Rattrapage atteint en environ {mois} mois ({semaines} semaines / {jours_tot} jours) — le {date_rattrap.strftime('%d/%m/%Y')}.")
                            else:
                                toast_warning("Rattrapage non atteint dans la limite de jours spécifiée.")

                            fig, ax = plt.subplots(figsize=(10,5))
                            ax.plot(dates, theo_series, label="Simulation théorique", color="blue", linewidth=2)
                            ax.plot(dates, reel_series, label="Valeur réelle (sans supplément)", color="orange", linewidth=2)
                            ax.plot(dates, rattrap_series, label=f"Rattrapage ({freq_common.lower()})", color="red", linestyle="--", linewidth=2)
                            ax.set_xlabel("Date")
                            ax.set_ylabel("Valeur (€)")
                            ax.set_title("📊 Simulation : rattrapage (montant → date)")
                            ax.grid(True, linestyle="--", alpha=0.5)
                            ax.legend()
                            st.pyplot(fig)

                else:
                    st.subheader("Mode : date → montant (quel montant par période pour rattraper ?)")

                    date_cible = st.date_input("📅 Date cible de rattrapage", value=date.today() + timedelta(days=120), key="r_date_cible_v2")
                    nb_jours = (date_cible - date.today()).days
                    if nb_jours <= 0:
                        st.warning("Choisis une date cible dans le futur.")
                    else:
                        montant_theo_future = capital_theo
                        for j in range(nb_jours):
                            montant_theo_future *= (1 + taux_journalier)
                            if j % 30 == 0 and j > 0:
                                montant_theo_future += versement_mensuel

                        montant_reel_future = montant_depart
                        for j in range(nb_jours):
                            montant_reel_future *= (1 + taux_journalier)
                            if j % 30 == 0 and j > 0:
                                montant_reel_future += versement_mensuel

                        per_days = pas_days_common
                        n_periodes = (nb_jours + per_days - 1) // per_days
                        r_periode = (1 + taux_journalier) ** per_days - 1

                        if r_periode == 0:
                            facteur = n_periodes
                        else:
                            facteur = ((1 + r_periode) ** n_periodes - 1) / r_periode

                        denom = facteur
                        numer = montant_theo_future - montant_reel_future
                        versement_par_periode = numer / denom if denom != 0 else float('inf')

                        if versement_par_periode <= 0:
                            toast_success("Tu es déjà au-dessus ou égal à la courbe théorique à la date choisie.")
                        else:
                            total_verse = versement_par_periode * n_periodes
                            st.success(f"💡 Il faut verser **{versement_par_periode:.2f} € par {freq_common.lower()}** pour rattraper la courbe le {date_cible.strftime('%d/%m/%Y')}.")
                            st.info(f"🔢 Nombre de versements : {n_periodes} → Total versé ~ {total_verse:,.2f} €")

                        dates_sim, theo_series, reel_series, rattrap_series = [], [], [], []
                        montant_theo = capital_theo
                        montant_reel = montant_depart
                        montant_rattrap = montant_depart

                        for j in range(nb_jours):
                            current_date = date.today() + timedelta(days=j)
                            dates_sim.append(current_date)

                            montant_theo *= (1 + taux_journalier)
                            montant_reel *= (1 + taux_journalier)
                            montant_rattrap *= (1 + taux_journalier)

                            if j % 30 == 0 and j > 0:
                                montant_theo += versement_mensuel
                                montant_reel += versement_mensuel
                                montant_rattrap += versement_mensuel

                            if (freq_common == "Journalière") or \
                               (freq_common == "Hebdomadaire" and j % 7 == 0) or \
                               (freq_common == "Mensuelle" and j % 30 == 0) or \
                               (freq_common == "Annuelle" and j % 365 == 0):
                                montant_rattrap += max(0, versement_par_periode)

                            theo_series.append(montant_theo)
                            reel_series.append(montant_reel)
                            rattrap_series.append(montant_rattrap)

                        fig, ax = plt.subplots(figsize=(10,5))
                        ax.plot(dates_sim, theo_series, label="Simulation théorique", color="blue", linewidth=2)
                        ax.plot(dates_sim, reel_series, label="Valeur réelle (sans supplément)", color="orange", linewidth=2)
                        ax.plot(dates_sim, rattrap_series, label=f"Rattrapage ({freq_common.lower()})", color="red", linestyle="--", linewidth=2)
                        ax.set_xlabel("Date")
                        ax.set_ylabel("Valeur (€)")
                        ax.set_title("📊 Simulation : date → montant")
                        ax.grid(True, linestyle="--", alpha=0.5)
                        ax.legend()
                        st.pyplot(fig)

        conn.close()

# ==============================
# 💹 Sous onglet voir les investissement V2
# ==============================
def interface_voir_investissements_alpha():
    st.subheader("📊 Performances de ton portefeuille (Trade Republic + Alpha Vantage) V2")

    api_key = st.text_input("🔑 Entre ta clé API Alpha Vantage :", type="password")
    if not api_key:
        st.info("Entre ta clé API Alpha Vantage pour continuer.")
        return
    ts = TimeSeries(key=api_key, output_format='pandas')

    uploaded_file = st.file_uploader("📥 Importer ton fichier CSV Trade Republic", type=["csv"])
    if uploaded_file is None:
        st.info("Importe ton CSV pour analyser ton portefeuille.")
        return

    df_tr = pd.read_csv(uploaded_file)
    st.markdown("### 💼 Données importées depuis Trade Republic")
    st.dataframe(df_tr, use_container_width=True, height=250)

    required_cols = {"Ticker", "Quantité", "Prix d'achat (€)"}
    if not required_cols.issubset(df_tr.columns):
        toast_error(f"Le fichier doit contenir les colonnes : {', '.join(required_cols)}")
        return

    tickers = df_tr["Ticker"].dropna().unique().tolist()

    st.markdown("### 📈 Données de marché en direct (Alpha Vantage)")
    data = {}
    for t in tickers:
        try:
            df, meta = ts.get_daily(symbol=t, outputsize='compact')
            df = df.rename(columns={
                '1. open': 'Open', '2. high': 'High',
                '3. low': 'Low', '4. close': 'Close', 
                '5. volume': 'Volume'
            })
            data[t] = df
        except Exception as e:
            logger.error(f"Alpha Vantage failed for {t}: {e}")
            toast_warning(f"Impossible de récupérer {t} ({e})")

    if not data:
        st.warning("Aucune donnée récupérée depuis Alpha Vantage.")
        return

    results = []
    for _, row in df_tr.iterrows():
        t = row["Ticker"]
        qte = safe_convert(row["Quantité"], float, 0.0)
        prix_achat = safe_convert(row["Prix d'achat (€)"], float, 0.0)
        if t not in data or data[t].empty:
            continue
        prix_actuel = data[t]['Close'].iloc[-1]
        perf = ((prix_actuel - prix_achat) / prix_achat) * 100
        valeur_totale = prix_actuel * qte
        results.append({
            "Symbole": t,
            "Quantité": qte,
            "Prix d'achat (€)": prix_achat,
            "Cours actuel (€)": round(prix_actuel, 2),
            "Performance (%)": round(perf, 2),
            "Valeur totale (€)": round(valeur_totale, 2)
        })

    df_results = pd.DataFrame(results)
    st.markdown("### 💹 Performance actuelle de ton portefeuille")
    st.dataframe(df_results, use_container_width=True, height=300)

    valeur_totale_portefeuille = df_results["Valeur totale (€)"].sum()
    perf_moyenne = df_results["Performance (%)"].mean()
    st.metric("💰 Valeur totale du portefeuille", f"{valeur_totale_portefeuille:,.2f} €", f"{perf_moyenne:.2f}%")

    premier_titre = df_results["Symbole"].iloc[0] if not df_results.empty else None
    if premier_titre and premier_titre in data:
        st.markdown(f"### 📊 Évolution récente de {premier_titre}")
        fig, ax = plt.subplots()
        ax.plot(data[premier_titre].index, data[premier_titre]["Close"], label=premier_titre)
        ax.set_title(f"Historique de {premier_titre}")
        ax.set_xlabel("Date")
        ax.set_ylabel("Cours (€)")
        ax.legend()
        st.pyplot(fig)

    toast_success("Portefeuille analysé avec succès !")

# ==============================
# 📊 INTERFACE PRINCIPALE
# ==============================

def interface_ocr_analysis_complete():
    """Interface complète d'analyse OCR avec support logs externes."""
    
    st.title("🔍 Analyse OCR Complète - Tour de Contrôle")
    st.markdown("Analysez vos propres scans ou diagnostiquez les logs de vos utilisateurs")
    
    # Choix du mode
    tab1,tab2,tab3,tab4 = st.tabs([
        "📊 Mes propres scans", "🔬 Analyser logs externes", "📈 Comparaison", "🛠️ Diagnostic complet"
    ])
    
    with tab1:
        # Interface existante pour vos propres logs
        interface_own_scans()
    
    with tab2:
        # Nouvelle interface pour analyser les logs des utilisateurs
        interface_external_logs()
    
    with tab3:
        # Comparaison entre différents logs
        interface_comparison()
    
    with tab4:
        # Diagnostic approfondi avec recommandations
        interface_diagnostic()

def interface_own_scans():
    """Analyse de vos propres scans (interface originale améliorée)."""
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Performance",
        "✅ Patterns fiables", 
        "⚠️ Patterns à corriger",
        "📋 Historique",
        "📊 Statistiques détaillées"
    ])
    
    with tab1:
        st.subheader("📊 Performance Globale")
        
        # Charger les stats depuis vos fichiers locaux
        perf = get_ocr_performance_report()
        
        # Vérifier si des données existent
        if not perf or (not perf.get('ticket') and not perf.get('revenu')):
            st.info("📊 **Aucune donnée OCR disponible pour le moment**")
            st.markdown("""
            ### 💡 Comment générer des statistiques ?
            
            Les statistiques OCR sont générées automatiquement lorsque vous :
            - 🧾 Scannez des tickets via l'interface OCR
            - 💼 Ajoutez des revenus avec OCR
            - 📸 Utilisez la fonction d'analyse de documents
            
            **Fichiers requis :**
            - `data/ocr_logs/performance_stats.json` - Statistiques de performance
            - `data/ocr_logs/pattern_stats.json` - Statistiques des patterns
            - `data/ocr_logs/scan_history.jsonl` - Historique des scans
            
            **📍 Localisation actuelle :**
            - Performance: `{}`
            - Patterns: `{}`
            - Historique: `{}`
            
            🚀 **Commencez à scanner des documents pour voir les statistiques !**
            """.format(
                "✅ Existe" if os.path.exists(OCR_PERFORMANCE_LOG) else "❌ Inexistant",
                "✅ Existe" if os.path.exists(PATTERN_STATS_LOG) else "❌ Inexistant",
                "✅ Existe" if os.path.exists(OCR_SCAN_LOG) else "❌ Inexistant"
            ))
        else:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("### 🧾 Tickets")
                if 'ticket' in perf:
                    ticket_stats = perf['ticket']
                    st.metric("Total scannés", ticket_stats.get('total', 0))
                    st.metric("Taux succès", f"{ticket_stats.get('success_rate', 0):.1f}%")
                    st.metric("Corrections", f"{ticket_stats.get('correction_rate', 0):.1f}%")
                else:
                    st.info("📭 Aucun ticket scanné")
            
            with col2:
                st.markdown("### 💼 Revenus")
                if 'revenu' in perf:
                    revenu_stats = perf['revenu']
                    st.metric("Total scannés", revenu_stats.get('total', 0))
                    st.metric("Taux succès", f"{revenu_stats.get('success_rate', 0):.1f}%")
                    st.metric("Corrections", f"{revenu_stats.get('correction_rate', 0):.1f}%")
                else:
                    st.info("📭 Aucun revenu scanné")
            
            with col3:
                st.markdown("### 📊 Global")
                total_scans = perf.get('ticket', {}).get('total', 0) + perf.get('revenu', {}).get('total', 0)
                
                if total_scans > 0:
                    avg_success = (
                        (perf.get('ticket', {}).get('success', 0) + perf.get('revenu', {}).get('success', 0)) 
                        / total_scans * 100
                    )
                    st.metric("Total documents", total_scans)
                    st.metric("Succès moyen", f"{avg_success:.1f}%")
                    st.metric("Dernière MAJ", perf.get('last_updated', 'N/A')[:10])
                else:
                    st.info("📭 Aucune donnée")
    
    with tab2:
        st.subheader("✅ Patterns les plus fiables")
        
        min_detections = st.slider("🔢 Détections minimum", 1, 20, 5, key="min_detections_slider")
        min_success = st.slider("📈 Taux succès minimum (%)", 50, 100, 70, key="min_success_slider")
        
        best = get_best_patterns(min_detections, min_success)
        
        if best:
            st.success(f"✨ **{len(best)} patterns fiables trouvés** avec au moins {min_detections} détections et {min_success}% de succès")
            
            df = pd.DataFrame(best)
            
            # Graphique
            fig = px.bar(
                df.head(20), 
                x='pattern', 
                y='reliability_score',
                color='success_rate',
                title='🏆 Top 20 Patterns Fiables',
                labels={'reliability_score': 'Score de fiabilité', 'pattern': 'Pattern'},
                color_continuous_scale='Greens'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Tableau
            st.dataframe(df, use_container_width=True)
        else:
            st.info("📊 **Aucun pattern fiable avec ces critères**")
            st.markdown("""
            ### 💡 Pourquoi aucun pattern n'est affiché ?
            
            **Raisons possibles :**
            - 📭 Aucun document n'a encore été scanné
            - 🔍 Les critères de filtrage sont trop stricts
            - 📉 Les patterns détectés n'atteignent pas les seuils minimum
            
            **Solutions :**
            1. 🔧 Réduisez les critères de filtrage ci-dessus
            2. 🧾 Scannez plus de documents pour générer des statistiques
            3. 📍 Vérifiez que le fichier `data/ocr_logs/pattern_stats.json` existe
            
            **État actuel :**
            - Fichier patterns: `{}`
            
            🚀 **Astuce :** Commencez par scanner quelques tickets pour alimenter les statistiques !
            """.format(
                "✅ Existe" if os.path.exists(PATTERN_STATS_LOG) else "❌ Inexistant - Créez-le en scannant des documents"
            ))
    
    with tab3:
        st.subheader("⚠️ Patterns problématiques")
        
        worst = get_worst_patterns(3, 50)
        
        if worst:
            df = pd.DataFrame(worst)
            
            # Alerte
            st.warning(f"🚨 **{len(worst)} patterns nécessitent une amélioration**")
            
            # Graphique des échecs
            fig = px.scatter(
                df,
                x='detections',
                y='success_rate',
                size='corrections',
                color='success_rate',
                hover_data=['pattern'],
                title='⚠️ Patterns Problématiques (taille = corrections)',
                labels={'success_rate': 'Taux de succès (%)', 'detections': 'Nombre de détections'},
                color_continuous_scale='RdYlGn'
            )
            fig.add_hline(y=50, line_dash="dash", line_color="red", annotation_text="🚨 Seuil critique")
            st.plotly_chart(fig, use_container_width=True)
            
            # Recommandations
            st.markdown("### 💡 Recommandations d'Amélioration")
            for idx, row in df.iterrows():
                if row['success_rate'] < 30:
                    st.error(f"🔴 **{row['pattern']}** : Taux d'échec critique ({row['success_rate']:.1f}%) - {row['detections']} détections")
                elif row['success_rate'] < 40:
                    st.warning(f"🟠 **{row['pattern']}** : Nécessite attention urgente ({row['success_rate']:.1f}%) - {row['detections']} détections")
                else:
                    st.info(f"🟡 **{row['pattern']}** : À améliorer ({row['success_rate']:.1f}%) - {row['detections']} détections")
        else:
            toast_success("**Aucun pattern problématique détecté !**")
            st.markdown("""
            ### 🎉 Excellent travail !
            
            **Statut actuel :**
            - ✅ Tous les patterns détectés fonctionnent correctement
            - ✅ Aucun pattern n'a un taux d'échec supérieur à 50%
            - ✅ L'OCR fonctionne de manière optimale
            
            **Ou bien :**
            - 📭 Aucune donnée disponible (fichiers logs vides)
            - 🔍 Les patterns n'ont pas encore été testés suffisamment
            
            **Fichier patterns :**
            - État: `{}`
            
            💡 **Conseil :** Continuez à scanner des documents pour maintenir ces bonnes performances !
            """.format(
                "✅ Existe" if os.path.exists(PATTERN_STATS_LOG) else "❌ Inexistant - Commencez à scanner pour générer des stats"
            ))
    
    with tab4:
        st.subheader("📋 Historique des scans")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            doc_type = st.selectbox("🗂️ Type de document", ["Tous", "ticket", "revenu"], key="doc_type_select")
        with col2:
            limit = st.number_input("📊 Nombre max", 10, 500, 50, step=10, key="limit_input")
        
        scans = get_scan_history(None if doc_type == "Tous" else doc_type, limit)
        
        if scans:
            # Conversion en DataFrame
            df_scans = pd.DataFrame(scans)
            
            toast_success("**{len(df_scans)} scans trouvés** dans l'historique")
            
            # Graphique temporel
            if 'timestamp' in df_scans.columns:
                df_scans['timestamp'] = pd.to_datetime(df_scans['timestamp'])
                df_scans['success'] = df_scans['result'].apply(lambda x: x.get('success', False))
                
                # Évolution du taux de succès dans le temps
                daily_stats = df_scans.set_index('timestamp').resample('D')['success'].agg(['sum', 'count'])
                daily_stats['success_rate'] = daily_stats['sum'] / daily_stats['count'] * 100
                
                fig = px.line(
                    daily_stats.reset_index(),
                    x='timestamp',
                    y='success_rate',
                    title='📈 Évolution du Taux de Succès OCR',
                    labels={'success_rate': 'Taux de succès (%)', 'timestamp': 'Date'},
                    markers=True
                )
                fig.update_traces(line_color='#10b981', line_width=3)
                st.plotly_chart(fig, use_container_width=True)
            
            # Tableau détaillé
            st.markdown("### 📊 Derniers Scans")
            st.dataframe(df_scans[['timestamp', 'document_type', 'filename']].head(20), use_container_width=True)
        else:
            st.info("📭 **Aucun scan dans l'historique**")
            st.markdown("""
            ### 💡 Comment générer un historique ?
            
            **L'historique des scans se remplit automatiquement lorsque vous :**
            - 🧾 Scannez des tickets de caisse
            - 💼 Ajoutez des revenus avec reconnaissance OCR
            - 📸 Utilisez n'importe quelle fonction d'analyse de documents
            
            **Fichier d'historique :**
            - Chemin: `data/ocr_logs/scan_history.jsonl`
            - État: `{}`
            
            **Structure attendue :**
            Chaque scan génère une entrée avec :
            - 📅 Timestamp (date et heure)
            - 📄 Type de document (ticket/revenu)
            - 📝 Nom du fichier
            - ✅ Résultat (succès/échec)
            
            🚀 **Commencez à scanner pour voir l'historique se remplir !**
            """.format(
                "✅ Existe" if os.path.exists(OCR_SCAN_LOG) else "❌ Inexistant - Sera créé au premier scan"
            ))
    
    with tab5:
        st.subheader("📊 Statistiques détaillées")
        
        # Analyses avancées
        scans = get_scan_history(limit=1000)
        
        if scans:
            df = pd.DataFrame(scans)
            
            st.success(f"📈 **Analyse de {len(df)} scans** (limité à 1000 les plus récents)")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Distribution des montants
                st.markdown("### 💰 Distribution des montants")
                
                montants = []
                for scan in scans:
                    if 'extraction' in scan:
                        montant = scan['extraction'].get('montant_final', 0)
                        if montant > 0:
                            montants.append(montant)
                
                if montants:
                    fig = px.histogram(
                        montants,
                        nbins=30,
                        title="💵 Distribution des montants scannés",
                        labels={'value': 'Montant (€)', 'count': 'Fréquence'},
                        color_discrete_sequence=['#10b981']
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Statistiques
                    st.markdown(f"""
                    **📊 Statistiques des montants :**
                    - 💰 Total: {sum(montants):.2f} €
                    - 📊 Moyenne: {sum(montants)/len(montants):.2f} €
                    - 📈 Maximum: {max(montants):.2f} €
                    - 📉 Minimum: {min(montants):.2f} €
                    """)
                else:
                    st.info("💭 Aucun montant valide extrait des scans")
            
            with col2:
                # Catégories les plus fréquentes
                st.markdown("### 📂 Catégories détectées")
                
                categories = []
                for scan in scans:
                    if 'extraction' in scan:
                        cat = scan['extraction'].get('categorie_final', 'autres')
                        if cat:
                            categories.append(cat)
                
                if categories:
                    cat_counts = pd.Series(categories).value_counts().head(10)
                    
                    fig = px.pie(
                        values=cat_counts.values,
                        names=cat_counts.index,
                        title="🏆 Top 10 Catégories",
                        color_discrete_sequence=px.colors.sequential.Greens_r
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.markdown(f"""
                    **📋 Répartition :**
                    - 🔢 Catégories uniques: {len(cat_counts)}
                    - 👑 Plus fréquente: {cat_counts.index[0]} ({cat_counts.values[0]} fois)
                    """)
                else:
                    st.info("💭 Aucune catégorie détectée dans les scans")
            
            # Graphique temporel additionnel
            st.markdown("### 📅 Activité de Scan")
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df['date'] = df['timestamp'].dt.date
                
                daily_counts = df.groupby('date').size().reset_index(name='count')
                
                fig = px.bar(
                    daily_counts,
                    x='date',
                    y='count',
                    title='📊 Nombre de scans par jour',
                    labels={'date': 'Date', 'count': 'Nombre de scans'},
                    color='count',
                    color_continuous_scale='Greens'
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📭 **Aucune statistique détaillée disponible**")
            st.markdown("""
            ### 💡 Génération des statistiques détaillées
            
            **Cette section affiche :**
            - 💰 Distribution des montants extraits par OCR
            - 📂 Répartition par catégories automatiques
            - 📅 Activité de scan journalière
            - 📈 Tendances et patterns d'utilisation
            
            **Pour générer ces statistiques :**
            1. 🧾 Scannez des tickets de caisse
            2. 💼 Ajoutez des revenus avec OCR
            3. 📸 Utilisez l'extraction automatique de données
            
            **Fichier requis :**
            - Chemin: `data/ocr_logs/scan_history.jsonl`
            - État: `{}`
            - Format: JSONL (une ligne JSON par scan)
            
            **Données extraites par scan :**
            - 📅 Timestamp
            - 💰 Montant (montant_final)
            - 📂 Catégorie (categorie_final)
            - ✅ Statut de réussite
            
            🚀 **Commencez à scanner pour voir des statistiques riches !**
            """.format(
                "✅ Existe" if os.path.exists(OCR_SCAN_LOG) else "❌ Inexistant - Créé automatiquement au premier scan"
            ))

def interface_external_logs():
    """Interface pour analyser les logs externes des utilisateurs."""

    st.subheader("🔬 Analyse de Logs Externes")
    st.info("💡 **Fonctionnalité en développement**")
    st.markdown("""
    ### 📤 Upload de Logs Utilisateurs

    Cette section permettra d'analyser les logs OCR de vos utilisateurs pour :
    - 🔍 Diagnostiquer les problèmes d'OCR
    - 📊 Comparer les performances entre utilisateurs
    - 🐛 Identifier les patterns problématiques

    **Formats supportés :**
    - `pattern_log.json` - Statistiques des patterns
    - `scan_history.jsonl` - Historique des scans
    - `performance_stats.json` - Métriques de performance

    🚧 **Statut :** En cours de développement
    """)

    # Interface basique d'upload
    uploaded_file = st.file_uploader(
        "📁 Uploader un fichier de logs (JSON/JSONL)",
        type=['json', 'jsonl', 'txt'],
        help="Uploadez les logs d'un utilisateur pour analyse"
    )

    if uploaded_file:
        toast_success("Fichier '{uploaded_file.name}' uploadé avec succès !")

        # Analyser le fichier uploadé
        data = analyze_external_log(uploaded_file)

        if data:
            # Diagnostic des données
            diagnostics = diagnose_ocr_patterns(data)

            # Métriques principales
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total scans", diagnostics.get('total_scans', 0))

            with col2:
                success_rate = diagnostics.get('success_rate', 0)
                st.metric(
                    "Taux de succès",
                    f"{success_rate:.1f}%",
                    delta=f"{success_rate - 70:.1f}%" if success_rate > 0 else None
                )

            with col3:
                st.metric(
                    "Patterns fiables",
                    len(diagnostics.get('reliable_patterns', []))
                )

            with col4:
                st.metric(
                    "Patterns problématiques",
                    len(diagnostics.get('problematic_patterns', []))
                )

            # Affichage selon le type
            if isinstance(data, dict) and data.get('type') == 'pattern_counts':
                st.markdown("#### 📊 Compteurs de patterns")

                patterns = data['data']
                df = pd.DataFrame([
                    {'Pattern': k, 'Détections': v}
                    for k, v in sorted(patterns.items(), key=lambda x: x[1], reverse=True)
                ])

                # Graphique
                fig = px.bar(
                    df.head(20),
                    x='Pattern',
                    y='Détections',
                    title='Top 20 Patterns Détectés'
                )
                st.plotly_chart(fig, use_container_width=True)

                # Tableau complet
                st.dataframe(df, use_container_width=True)

            elif isinstance(data, list):
                st.markdown("#### 📋 Analyse détaillée des scans")

                # Patterns problématiques
                if diagnostics.get('problematic_patterns'):
                    toast_error("Patterns problématiques détectés :")

                    for pattern_info in diagnostics['problematic_patterns']:
                        st.warning(
                            f"⚠️ **{pattern_info['pattern']}** : "
                            f"Succès {pattern_info['success_rate']:.1f}% sur {pattern_info['detections']} détections"
                        )

                # Patterns fiables
                if diagnostics.get('reliable_patterns'):
                    toast_success("Patterns fiables :")

                    for pattern_info in diagnostics['reliable_patterns']:
                        st.info(
                            f"✓ **{pattern_info['pattern']}** : "
                            f"Succès {pattern_info['success_rate']:.1f}% sur {pattern_info['detections']} détections"
                        )

            # Recommandations
            if diagnostics.get('recommendations'):
                st.markdown("### 💡 Recommandations")
                for rec in diagnostics['recommendations']:
                    st.markdown(f"- {rec}")

            # Export du diagnostic
            if st.button(f"💾 Exporter diagnostic - {uploaded_file.name}"):
                diagnostic_json = json.dumps(diagnostics, indent=2, ensure_ascii=False)
                st.download_button(
                    "📥 Télécharger le diagnostic",
                    diagnostic_json,
                    f"diagnostic_{uploaded_file.name}",
                    mime="application/json"
                )
        else:
            toast_error("Impossible d'analyser {uploaded_file.name}")

    else:
        st.info("👆 Uploadez les fichiers de logs pour commencer l'analyse")

        # Instructions
        with st.expander("📖 Instructions pour les utilisateurs"):
            st.markdown("""
            ### Comment récupérer vos logs OCR :

            1. **pattern_log.json** : Compteurs de patterns détectés
               - Chemin : `data/ocr_logs/pattern_log.json`

            2. **scan_history.jsonl** : Historique complet des scans
               - Chemin : `data/ocr_logs/scan_history.jsonl`

            3. **performance_stats.json** : Statistiques de performance
               - Chemin : `data/ocr_logs/performance_stats.json`

            4. **pattern_stats.json** : Statistiques détaillées par pattern
               - Chemin : `data/ocr_logs/pattern_stats.json`

            ### Format des logs :
            - JSON : Fichiers structurés avec statistiques
            - JSONL : Une ligne JSON par scan (historique)
            - TXT : Extraction basique de patterns
            """)

def interface_comparison():
    """Comparaison entre différents logs/utilisateurs."""

    st.subheader("📈 Comparaison Multi-Sources")
    st.info("💡 **Fonctionnalité en développement**")
    st.markdown("""
    ### 🔀 Analyse Comparative

    Cette section permettra de comparer :
    - 👥 Performances entre différents utilisateurs
    - 📅 Évolution dans le temps
    - 🏢 Comparaison entre succursales/équipes
    - 🌍 Analyse géographique

    **Métriques comparées :**
    - 📊 Taux de succès OCR
    - 🎯 Patterns les plus fiables
    - ⚠️ Patterns problématiques
    - 💰 Montants moyens détectés
    - ⏱️ Temps de traitement

    **Visualisations :**
    - 📊 Graphiques comparatifs
    - 📈 Tendances temporelles
    - 🎯 Heatmaps de performance

    🚧 **Statut :** En cours de développement
    """)

    # Interface basique
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 📁 Source 1")
        file1 = st.file_uploader("Logs utilisateur 1", type=['json', 'jsonl'], key="comp1")
    with col2:
        st.markdown("#### 📁 Source 2")
        file2 = st.file_uploader("Logs utilisateur 2", type=['json', 'jsonl'], key="comp2")

    # Si au moins 2 fichiers sont uploadés
    if file1 and file2:
        toast_success("Analyse comparative de 2 sources")

        # Analyser les deux fichiers
        data1 = analyze_external_log(file1)
        data2 = analyze_external_log(file2)

        if data1 and data2:
            # Diagnostics
            diag1 = diagnose_ocr_patterns(data1)
            diag2 = diagnose_ocr_patterns(data2)

            comparisons = {
                file1.name: diag1,
                file2.name: diag2
            }

            # Tableau comparatif
            comparison_data = []
            for filename, diag in comparisons.items():
                comparison_data.append({
                    'Fichier': filename[:30],
                    'Scans': diag.get('total_scans', 0),
                    'Succès (%)': f"{diag.get('success_rate', 0):.1f}",
                    'Patterns OK': len(diag.get('reliable_patterns', [])),
                    'Patterns KO': len(diag.get('problematic_patterns', []))
                })

            df_comp = pd.DataFrame(comparison_data)
            st.dataframe(df_comp, use_container_width=True)

            # Graphiques comparatifs
            col1, col2 = st.columns(2)

            with col1:
                # Taux de succès
                fig = px.bar(
                    df_comp,
                    x='Fichier',
                    y='Succès (%)',
                    title='Comparaison Taux de Succès',
                    color='Succès (%)'
                )
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                # Patterns problématiques
                fig = px.bar(
                    df_comp,
                    x='Fichier',
                    y=['Patterns OK', 'Patterns KO'],
                    title='Patterns Fiables vs Problématiques',
                    barmode='group'
                )
                st.plotly_chart(fig, use_container_width=True)

            # Patterns communs problématiques
            st.markdown("### 🔍 Patterns problématiques communs")

            all_problematic = {}
            for filename, diag in comparisons.items():
                for pattern_info in diag.get('problematic_patterns', []):
                    pattern = pattern_info['pattern']
                    if pattern not in all_problematic:
                        all_problematic[pattern] = []
                    all_problematic[pattern].append(filename)

            # Afficher les patterns présents dans plusieurs fichiers
            common_problems = {k: v for k, v in all_problematic.items() if len(v) > 1}

            if common_problems:
                for pattern, files in common_problems.items():
                    toast_warning("**{pattern}** problématique dans : {', '.join(files)}")
            else:
                toast_success("Aucun pattern problématique commun")
        else:
            toast_error("Erreur lors de l'analyse des fichiers")
    else:
        st.info("👆 Uploadez au moins 2 fichiers pour comparer")

def interface_diagnostic():
    """Diagnostic approfondi avec recommandations détaillées."""

    st.subheader("🛠️ Diagnostic Complet OCR")
    st.info("💡 **Fonctionnalité en développement**")

    st.markdown("""
    ### 🔍 Analyse Approfondie

    Cette section fournira un diagnostic complet de votre système OCR :

    **Analyses incluses :**
    - 🎯 Taux de succès global et par type
    - 📊 Performance par pattern
    - ⚠️ Identification des points faibles
    - 💡 Recommandations d'amélioration
    - 🔧 Suggestions de configuration

    **Niveaux de diagnostic :**
    - ⚡ **Rapide** : Vue d'ensemble (1-2 min)
    - 📊 **Standard** : Analyse détaillée (3-5 min)
    - 🔬 **Approfondie** : Audit complet (5-10 min)

    **Rapports générés :**
    - 📄 Résumé exécutif
    - 📈 Graphiques de tendances
    - 🎯 Liste d'actions prioritaires
    - 📋 Guide d'optimisation

    🚧 **Statut :** En cours de développement
    """)

    # Interface basique de sélection
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📊 Source des données")
        source = st.radio(
            "Sélectionner",
            ["💾 Mes logs locaux", "📤 Upload fichier externe"],
            label_visibility="collapsed"
        )

    with col2:
        st.markdown("#### 🔍 Profondeur d'analyse")
        depth = st.select_slider(
            "Niveau",
            ["⚡ Rapide", "📊 Standard", "🔬 Approfondie"],
            label_visibility="collapsed"
        )

    st.info(f"🔧 Analyse {depth} en cours d'implémentation...")

    # Aperçu de ce qui sera disponible
    with st.expander("👀 Aperçu du futur rapport"):
        st.markdown("""
        **Le diagnostic complet inclura :**

        1. **📊 Vue d'ensemble**
           - Nombre total de scans
           - Taux de succès global
           - Tendances sur 7/30 jours

        2. **🎯 Analyse par Pattern**
           - Top 10 patterns fiables
           - Top 10 patterns problématiques
           - Suggestions d'optimisation

        3. **⚠️ Points d'attention**
           - Erreurs critiques
           - Dégradations de performance
           - Patterns à surveiller

        4. **💡 Recommandations**
           - Actions prioritaires
           - Ajustements de configuration
           - Formation recommandée

        5. **📈 Projections**
           - Évolution attendue
           - Objectifs réalistes
           - ROI estimé
        """)

# Liste de catégories valides connues (tu peux l'étendre à volonté)
KNOWN_CATEGORIES = [
    "essence", "alimentation", "supermarché", "carrefour", "auchan",
    "restaurant", "boulangerie", "loisirs", "santé", "logement", "transport"
]

def correct_category_name(name):
    """Corrige les fautes simples dans les noms de catégorie/sous-catégorie."""
    if not name:
        return name
    name = name.lower().strip()
    matches = get_close_matches(name, KNOWN_CATEGORIES, n=1, cutoff=0.8)
    return matches[0] if matches else name

# ==============================
# 📋 MENU LATÉRAL V2
# ==============================
def main():
    """Fonction principale V2"""
    try:
        # Initialisation
        init_db()
        migrate_database_schema()
        
        with st.sidebar:
            st.title("📂 Menu Principal V2")
            st.success("🚀 Version 2 - Stabilisée & Uber 79%")
            
            st.markdown("---")
            
            page = st.radio(
                "Navigation",
                ["🏠 Accueil", "💸 Transactions", "📊 Voir Transactions", "📈 Solde prévisionnel"," Analyse"]
            )
            
            # 🔄 BOUTON DE RAFRAÎCHISSEMENT DES DONNÉES (discret en bas)
            st.markdown("---")
            if st.button("🔄 Actualiser", key="refresh_btn"):
                # Vider tous les caches et recharger
                refresh_and_rerun()
            
            st.caption("💡 Actualise après avoir ajouté/modifié une transaction")
        
        # Routage
        if page == "🏠 Accueil":
            interface_accueil()
        elif page == "💸 Transactions":
            st.header("💸 Transactions V2")
            
            tab1, tab2, tab3, tab4 = st.tabs([
                "🧾 Ajouter un ticket",
                "✍️ Ajouter une dépense manuelle", 
                "🔁 Dépense récurrente",
                "💰 Ajouter un revenu"
            ])

            with tab1:
                st.header("📸 Scanner les tickets automatiquement V2")
                st.info(f"Dépose tes tickets à scanner dans : `{TO_SCAN_DIR}`")
                process_all_tickets_in_folder()
            
            with tab2:
                interface_transactions_unifiee()

            with tab3:
                interface_transaction_recurrente()
            
            with tab4:
                interface_ajouter_revenu()
                
        elif page == "📊 Voir Transactions":
            st.header("📊 Voir Transactions V2")
            
            tab1, tab2, tab3 = st.tabs([
                "📋 Transactions",
                "🗑️ Gérer les transactions", 
                "🔁 Gérer les récurrences"
            ])

            with tab1:
                interface_voir_transactions()

            with tab2:
                interface_gerer_transactions()

            with tab3:
                interface_gerer_recurrences()
                
        elif page == "📈 Solde prévisionnel":
            interface_solde_previsionnel()
        
        elif page == "Analyse" : 
            interface_ocr_analysis_complete()
            
    except Exception as e:
        logger.critical(f"Application V2 failed: {e}")
        st.error(f"""
        ❌ L'application V2 a rencontré une erreur critique: {e}
        
        **Solutions possibles :**
        1. Vérifiez les logs (gestio_app.log)
        2. Redémarrez l'application  
        3. Contactez le support si le problème persiste
        """)

if __name__ == "__main__":
    main()


# ==============================
# 📱 CSS RESPONSIVE & MODERNE
# ==============================
st.markdown("""
<style>
/* 🎨 Variables de design moderne */
:root {
    --primary-color: #10b981;
    --secondary-color: #3b82f6;
    --danger-color: #ef4444;
    --warning-color: #f59e0b;
    --background-light: #f9fafb;
    --text-primary: #1f2937;
    --text-secondary: #6b7280;
    --border-radius: 12px;
    --box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

/* 📱 Container principal responsive */
.main .block-container {
    padding: 1rem 2rem;
    max-width: 1400px;
    margin: 0 auto;
}

/* 📊 DataFrames modernes */
div[data-testid="stDataFrame"] {
    border-radius: var(--border-radius);
    overflow: hidden;
    box-shadow: var(--box-shadow);
}

div[data-testid="stDataFrame"] div[role="gridcell"] {
    font-size: 15px !important;
    padding: 10px !important;
    border-bottom: 1px solid #e5e7eb;
}

/* 🎯 Métriques améliorées */
div[data-testid="stMetricValue"] {
    font-size: 2rem;
    font-weight: 700;
    color: var(--primary-color);
}

div[data-testid="stMetricDelta"] {
    font-size: 1rem;
    font-weight: 600;
}

/* 🔘 Boutons modernes */
.stButton > button {
    border-radius: var(--border-radius);
    font-weight: 600;
    padding: 0.5rem 1.5rem;
    transition: all 0.3s ease;
    border: none;
    box-shadow: var(--box-shadow);
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
}

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--primary-color) 0%, #059669 100%);
}

.stButton > button[kind="secondary"] {
    background: linear-gradient(135deg, var(--danger-color) 0%, #dc2626 100%);
}

/* 📝 Inputs et selectbox */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stSelectbox > div > div > select {
    border-radius: var(--border-radius);
    border: 2px solid #e5e7eb;
    padding: 0.5rem 1rem;
    font-size: 1rem;
    transition: border-color 0.3s ease;
}

.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus,
.stSelectbox > div > div > select:focus {
    border-color: var(--primary-color);
    box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1);
}

/* 🎨 Expanders modernes */
.streamlit-expanderHeader {
    border-radius: var(--border-radius);
    background-color: var(--background-light);
    font-weight: 600;
    padding: 1rem;
    border: 1px solid #e5e7eb;
}

/* 📊 Graphiques */
.stPlotlyChart, .stPyplot {
    border-radius: var(--border-radius);
    box-shadow: var(--box-shadow);
    padding: 1rem;
    background-color: white;
}

/* 💬 Messages (success, error, warning, info) */
.stSuccess, .stError, .stWarning, .stInfo {
    border-radius: var(--border-radius);
    padding: 1rem;
    margin: 1rem 0;
    border-left: 4px solid;
}

.stSuccess {
    border-left-color: var(--primary-color);
    background-color: #d1fae5;
}

.stError {
    border-left-color: var(--danger-color);
    background-color: #fee2e2;
}

.stWarning {
    border-left-color: var(--warning-color);
    background-color: #fef3c7;
}

.stInfo {
    border-left-color: var(--secondary-color);
    background-color: #dbeafe;
}

/* 🎯 Sidebar moderne */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1f2937 0%, #111827 100%);
}

section[data-testid="stSidebar"] .stRadio > label {
    color: white !important;
    font-weight: 600;
}

/* 📱 RESPONSIVE MOBILE */
@media (max-width: 768px) {
    .main .block-container {
        padding: 0.5rem 1rem;
    }
    
    div[data-testid="stMetricValue"] {
        font-size: 1.5rem;
    }
    
    .stButton > button {
        width: 100%;
        margin: 0.5rem 0;
    }
    
    div[data-testid="stDataFrame"] div[role="gridcell"] {
        font-size: 13px !important;
        padding: 6px !important;
    }
}

/* 📱 RESPONSIVE TABLET */
@media (min-width: 769px) and (max-width: 1024px) {
    .main .block-container {
        padding: 1rem;
        max-width: 100%;
    }
}

/* 🖥️ RESPONSIVE DESKTOP LARGE */
@media (min-width: 1400px) {
    .main .block-container {
        max-width: 1600px;
    }
}

/* ✨ Animations */
@keyframes slideIn {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.stButton, .stMetric, div[data-testid="stDataFrame"] {
    animation: slideIn 0.3s ease-out;
}

/* 🎨 Scrollbar personnalisée */
::-webkit-scrollbar {
    width: 10px;
    height: 10px;
}

::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 10px;
}

::-webkit-scrollbar-thumb {
    background: var(--primary-color);
    border-radius: 10px;
}

::-webkit-scrollbar-thumb:hover {
    background: #059669;
}

/* 🌙 Dark mode support */
@media (prefers-color-scheme: dark) {
    :root {
        --background-light: #1f2937;
        --text-primary: #f9fafb;
        --text-secondary: #d1d5db;
    }
}
</style>
""", unsafe_allow_html=True)
