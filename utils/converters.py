# -*- coding: utf-8 -*-
"""
Module converters - Partie de l'application gestiov4
Généré automatiquement par migrate_to_modular.py
"""

import re
from datetime import datetime, date
from dateutil import parser


def safe_convert(value, convert_type=float, default=0.0):
    """
    Conversion sécurisée des valeurs avec gestion d'erreurs robuste.
    Gère les formats européen (1.234,56) et américain (1,234.56).
    """
    try:
        if pd.isna(value) or value is None or str(value).strip() == "":
            return default

        value_str = str(value).strip()

        if convert_type == float:
            # Nettoyage complet pour les montants
            value_str = value_str.replace(' ', '').replace('€', '').replace('"', '').replace("'", "")

            # === DÉTECTION AUTOMATIQUE DU FORMAT ===
            # Règle : Le DERNIER symbole (. ou ,) est le séparateur de décimales

            last_comma = value_str.rfind(',')
            last_dot = value_str.rfind('.')

            if last_comma > last_dot:
                # Format européen : 1.234,56 ou 1234,56
                # La virgule est le séparateur de décimales
                value_str = value_str.replace('.', '')  # Supprimer séparateurs de milliers
                value_str = value_str.replace(',', '.')  # Virgule → point pour Python
            elif last_dot > last_comma:
                # Format américain : 1,234.56 ou 1234.56
                # Le point est le séparateur de décimales
                value_str = value_str.replace(',', '')  # Supprimer séparateurs de milliers
                # Le point reste tel quel
            else:
                # Un seul symbole ou aucun
                # Si c'est une virgule, on suppose format européen
                if ',' in value_str:
                    value_str = value_str.replace(',', '.')

            # Nettoyer tout ce qui n'est pas chiffre, point ou signe moins
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


def normaliser_date(date_str):
    """
    Convertit une date (JJ/MM/AAAA, JJ/MM/AA, AAAA-MM-JJ, etc.)
    en format ISO (AAAA-MM-JJ) pour la base SQLite.
    """
    return safe_date_convert(date_str).isoformat()


def numero_to_mois(num: str) -> str:
    for mois, numero in mois_dict.items():
        if numero == num:
            return mois
    return "inconnu"


