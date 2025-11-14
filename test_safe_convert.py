#!/usr/bin/env python3
"""Script de test pour la fonction safe_convert améliorée."""

import re

def safe_convert(value, convert_type=float, default=0.0):
    """
    Conversion sécurisée des valeurs avec gestion d'erreurs robuste.
    Gère les formats européen (1.234,56) et américain (1,234.56).
    """
    try:
        if value is None or str(value).strip() == "":
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
        print(f"Conversion failed for value '{value}': {e}")
        return default

# === TESTS ===
print("=== TEST DE LA FONCTION safe_convert ===\n")

test_cases = [
    # Format européen
    ("1.234,56", 1234.56, "Format européen avec milliers"),
    ("1234,56", 1234.56, "Format européen sans milliers"),
    ("48,08", 48.08, "Format européen simple"),
    ("12.345.678,99", 12345678.99, "Format européen multi-milliers"),

    # Format américain
    ("1,234.56", 1234.56, "Format américain avec milliers"),
    ("1234.56", 1234.56, "Format américain sans milliers"),
    ("48.08", 48.08, "Format américain simple"),
    ("12,345,678.99", 12345678.99, "Format américain multi-milliers"),

    # Cas edge
    ("1234", 1234.0, "Sans décimales"),
    ("0,50", 0.50, "Centimes européen"),
    ("0.50", 0.50, "Centimes américain"),
    ("15,00", 15.0, "Montant rond européen"),
    ("15.00", 15.0, "Montant rond américain"),

    # Avec symboles monétaires
    ("48,08 €", 48.08, "Avec euro européen"),
    ("$1,234.56", 1234.56, "Avec dollar américain"),
    ("1 234,56", 1234.56, "Avec espaces (français)"),
]

passed = 0
failed = 0

for value, expected, description in test_cases:
    result = safe_convert(value)
    status = "✓ PASS" if result == expected else "✗ FAIL"

    if result == expected:
        passed += 1
        print(f"{status} | {description:40s} | '{value:20s}' → {result:12.2f} (attendu: {expected:12.2f})")
    else:
        failed += 1
        print(f"{status} | {description:40s} | '{value:20s}' → {result:12.2f} (attendu: {expected:12.2f}) *** ERREUR ***")

print(f"\n=== RÉSULTATS ===")
print(f"Tests réussis : {passed}/{len(test_cases)}")
print(f"Tests échoués : {failed}/{len(test_cases)}")

if failed == 0:
    print("\n✓ Tous les tests sont passés ! La fonction est prête.")
else:
    print(f"\n✗ {failed} test(s) échoué(s). Vérifier la logique.")
