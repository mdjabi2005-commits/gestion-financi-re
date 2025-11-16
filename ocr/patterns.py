# -*- coding: utf-8 -*-
"""
Module patterns - Partie de l'application gestiov4
Généré automatiquement par migrate_to_modular.py
"""

import re
import pandas as pd
from datetime import datetime


from config import BASE_DIR, DATA_DIR, DB_PATH, TO_SCAN_DIR, SORTED_DIR, REVENUS_A_TRAITER, REVENUS_TRAITES
# Créer les dossiers de logs OCR
OCR_LOGS_DIR = os.path.join(DATA_DIR, "ocr_logs")
os.makedirs(OCR_LOGS_DIR, exist_ok=True)
LOG_PATH = os.path.join(OCR_LOGS_DIR, "pattern_log.json")
OCR_PERFORMANCE_LOG = os.path.join(OCR_LOGS_DIR, "performance_stats.json")
PATTERN_STATS_LOG = os.path.join(OCR_LOGS_DIR, "pattern_stats.json")
OCR_SCAN_LOG = os.path.join(OCR_LOGS_DIR, "scan_history.jsonl")
# === JOURNAL OCR ===

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


