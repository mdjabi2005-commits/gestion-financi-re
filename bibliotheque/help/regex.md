# 📚 Bibliothèque : regex (expressions régulières)

## 🎯 Qu'est-ce que regex ?

Le module **regex** est une version améliorée du module standard **re** de Python. Il offre des fonctionnalités supplémentaires pour les expressions régulières, notamment le support Unicode avancé et les lookbehinds de longueur variable.

**PyPI** : https://pypi.org/project/regex/  
**Documentation** : https://github.com/mrabarnett/mrab-regex

---

## 💡 Pourquoi regex dans notre projet ?

1. **Parsing OCR** : Extraction montants, dates des tickets scannés
2. **Patterns flexibles** : Gestion variations OCR (erreurs de reconnaissance)
3. **Validation** : Format dates, montants, IBAN
4. **Nettoyage texte** : Supprimer caractères parasites
5. **Support Unicode** : Accents, caractères spéciaux dans les tickets

---

## 🔧 Concepts de base

### 1. Recherche simple

```python
import re

text = "Montant total : 45.50 EUR"

# Chercher un pattern
match = re.search(r"(\d+\.\d+)", text)
if match:
    montant = match.group(1)  # "45.50"
    print(f"Montant trouvé : {montant}€")
```

### 2. Extraire toutes les occurrences

```python
text = "Prix: 12.50€, Taxe: 2.50€, Total: 15.00€"

# Trouver tous les montants
montants = re.findall(r"(\d+\.\d+)", text)
print(montants)  # ['12.50', '2.50', '15.00']
```

### 3. Vérifier un format

```python
# Valider une date (format DD/MM/YYYY)
def is_valid_date(date_str):
    pattern = r"^\d{2}/\d{2}/\d{4}$"
    return bool(re.match(pattern, date_str))

print(is_valid_date("23/12/2024"))  # True
print(is_valid_date("2024-12-23"))  # False
```

---

## 📊 Exemples concrets de notre app

### Extraction montant depuis OCR (`parsers.py`)

```python
import re

def extract_amount_from_line(line: str) -> float:
    """
    Extrait un montant d'une ligne de texte OCR.
    Gère les formats : 12.34, 12,34, 12.34€, 12,34 EUR
    """
    # Pattern flexible pour montants
    pattern = r"""
        (?P<montant>
            \d{1,3}                # 1-3 chiffres
            (?:[,.\s]\d{3})*       # Milliers optionnels (1,234 ou 1.234)
            [,.]                   # Séparateur décimal
            \d{2}                  # 2 décimales
        )
        \s*                        # Espaces optionnels
        (?:€|EUR|EUROS?)?          # Devise optionnelle
    """
    
    match = re.search(pattern, line, re.VERBOSE | re.IGNORECASE)
    
    if match:
        montant_str = match.group('montant')
        # Normaliser: remplacer virgule par point
        montant_str = montant_str.replace(',', '.').replace(' ', '')
        return float(montant_str)
    
    return 0.0

# Exemples
print(extract_amount_from_line("TOTAL: 45,50 €"))      # 45.50
print(extract_amount_from_line("Montant  123.45EUR"))  # 123.45
print(extract_amount_from_line("CB DEBIT 1,234.56"))   # 1234.56
```

### Détecter patterns dans tickets (`pattern_manager.py`)

```python
import re
from typing import List, Tuple

def find_amount_patterns(text: str, patterns: List[str]) -> List[Tuple[str, float]]:
    """
    Cherche des patterns de montants dans le texte OCR.
    Retourne (pattern_matché, montant)
    """
    results = []
    lines = text.split('\n')
    
    for pattern in patterns:
        # Compiler une seule fois pour performance
        compiled = re.compile(pattern, re.IGNORECASE)
        
        for i, line in enumerate(lines):
            if compiled.search(line):
                # Pattern trouvé, extraire montant de cette ligne OU suivante
                montant = extract_amount_from_line(line)
                
                if montant == 0.0 and i + 1 < len(lines):
                    # Essayer ligne suivante
                    montant = extract_amount_from_line(lines[i+1])
                
                if montant > 0:
                    results.append((pattern, montant))
    
    return results

# Exemple OCR
ocr_text = """
SUPER MARCHE LECLERC
12/12/2024
TOTAL TTC
45.50 EUR
CB DEBIT
"""

patterns = [
    r"TOTAL\s*(TTC|TIC)",
    r"CB\s*DEBIT",
    r"MONTANT"
]

found = find_amount_patterns(ocr_text, patterns)
for pattern, amount in found:
    print(f"Pattern '{pattern}' → {amount}€")
```

### Normaliser catégorie (`service.py`)

```python
import re

def normalize_category(category: str) -> str:
    """
    Nettoie et normalise une catégorie.
    """
    if not category:
        return "Autres"
    
    # Supprimer accents (simple)
    category = category.strip()
    
    # Remplacer espaces multiples par un seul
    category = re.sub(r'\s+', ' ', category)
    
    # Capitaliser première lettre
    category = category.capitalize()
    
    # Retirer caractères spéciaux
    category = re.sub(r'[^\w\s-]', '', category)
    
    return category

print(normalize_category("  alimentation   "))     # "Alimentation"
print(normalize_category("Transport/Essence"))     # "TransportEssence"
```

### Valider IBAN

```python
import re

def validate_iban(iban: str) -> bool:
    """
    Valide un IBAN français (commence par FR).
    """
    # Supprimer espaces
    iban = iban.replace(' ', '')
    
    # Pattern IBAN français: FR + 2 chiffres + 23 caractères alphanumériques
    pattern = r'^FR\d{2}[A-Z0-9]{23}$'
    
    if not re.match(pattern, iban, re.IGNORECASE):
        return False
    
    # Validation checksum (simplifié ici)
    return True

print(validate_iban("FR76 1234 5678 9012 3456 7890 123"))  # True
print(validate_iban("US12345"))                             # False
```

---

## ⚠️ Pièges courants

### 1. Groupes de capture vs non-capture

```python
# ❌ Groupe de capture inutile
pattern = r"(\d+),(\d+)"
match = re.search(pattern, "Prix: 12,50")
# match.groups() = ('12', '50')

# ✅ Groupe non-capturant si pas besoin
pattern = r"\d+,\d+"  # Plus simple
# OU
pattern = r"(?:\d+),(?:\d+)"  # Non-capturant explicite
```

### 2. Greedy vs non-greedy

```python
text = "<div>Item 1</div><div>Item 2</div>"

# ❌ Greedy - prend tout jusqu'au dernier </div>
pattern = r"<div>.*</div>"
match = re.search(pattern, text)
print(match.group())  # "<div>Item 1</div><div>Item 2</div>"

# ✅ Non-greedy - s'arrête au premier </div>
pattern = r"<div>.*?</div>"
match = re.search(pattern, text)
print(match.group())  # "<div>Item 1</div>"
```

### 3. Raw strings pour regex

```python
# ❌ Backslash doublé
pattern = "\\d+\\.\\d+"

# ✅ Raw string r"..."
pattern = r"\d+\.\d+"
```

### 4. Case sensitivity

```python
# ❌ Casse stricte
pattern = r"TOTAL"
re.search(pattern, "total")  # None

# ✅ Insensible à la casse
pattern = r"TOTAL"
re.search(pattern, "total", re.IGNORECASE)  # Match!

# ✅ Dans le pattern (regex avancé)
pattern = r"(?i)total"  # i = ignore case
```

---

## 🔥 Opérations avancées

### Lookahead et Lookbehind

```python
# Lookahead positif (?=...)
# Trouver montant AVANT "EUR"
pattern = r"\d+\.\d+(?=\s*EUR)"
re.search(pattern, "45.50 EUR")  # Match "45.50"

# Lookbehind positif (?<=...)
# Trouver montant APRÈS "TOTAL:"
pattern = r"(?<=TOTAL:\s)\d+\.\d+"
re.search(pattern, "TOTAL: 45.50")  # Match "45.50"

# Combiné
pattern = r"(?<=TOTAL:\s)\d+\.\d+(?=\s*EUR)"
re.search(pattern, "TOTAL: 45.50 EUR")  # Match "45.50"
```

### Named groups

```python
pattern = r"""
    (?P<jour>\d{2})/
    (?P<mois>\d{2})/
    (?P<annee>\d{4})
"""

match = re.search(pattern, "Date: 23/12/2024", re.VERBOSE)
if match:
    print(match.group('jour'))   # "23"
    print(match.group('mois'))   # "12"
    print(match.group('annee'))  # "2024"
    
    # Ou dict
    print(match.groupdict())
    # {'jour': '23', 'mois': '12', 'annee': '2024'}
```

---

## 📖 Ressources

- **Module re** : https://docs.python.org/3/library/re.html
- **Regex module** : https://github.com/mrabarnett/mrab-regex
- **Regex101** (tester) : https://regex101.com/
- **RegExr** (visualiser) : https://regexr.com/

---

## 💡 regex dans notre projet

| Fichier | Utilisation |
|---------|------------|
| `parsers.py` | Extraction montants/dates tickets OCR |
| `pattern_manager.py` | Matching patterns configurables |
| `services.py` | Normalisation catégories |
| `utils.py` | Validation formats (dates, IBAN) |
| `files.py` | Recherche fichiers par pattern |

**Commande d'installation** :
```bash
pip install regex
```

**Bonnes pratiques** :
- ✅ Utiliser raw strings `r"pattern"`  
- ✅ Compiler patterns réutilisés (`re.compile`)
- ✅ Utiliser `re.IGNORECASE` pour OCR
- ✅ Tester sur https://regex101.com
- ❌ Éviter regex trop complexes (illisibles)
- ❌ Ne pas parser HTML/XML avec regex (utiliser parser dédié)
