# Règles - Module OCR

## 🎯 Responsabilité

Extraction de texte depuis images et PDF, parsing tickets

---

## 📋 Règles strictes

### 1. Séparation extraction / parsing

**extractors/** : Extraire texte brut
```python
def extract_text_from_image(image_path: str) -> str:
    """Retourne texte brut"""
```

**parsers/** : Interpréter et structurer
```python
def parse_ticket(text: str) -> dict:
    """Retourne données structurées"""
```

---

### 2. Gestion des erreurs OCR

**TOUJOURS** gérer les erreurs :

```python
def extract_text_from_image(image_path: str) -> str:
    try:
        # Extraction
        text = pytesseract.image_to_string(image)
        return text
    except TesseractNotFoundError:
        logger.error("Tesseract non installé")
        return ""
    except Exception as e:
        logger.error(f"Erreur OCR: {e}")
        return ""
```

---

### 3. Logs OCR détaillés

**Emplacement** : `ocr_logs/`

**Format** :
```python
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Log handlers configurés dans le module
```

---

### 4. Validation des résultats

**TOUJOURS valider** après parsing :

```python
def parse_ticket(text: str) -> Optional[dict]:
    result = {
        'montant': extract_montant(text),
        'date': extract_date(text),
        'description': extract_description(text)
    }
    
    # Validation
    if not result['montant'] or result['montant'] <= 0:
        logger.warning("Montant invalide")
        return None
    
    return result
```

---

## 🏗️ Comment ajouter

### Ajouter un nouveau parser

1. **Créer parser** dans `parsers/`
```python
# parsers/mon_parser.py

import re
from typing import Optional

def parse_mon_format(text: str) -> Optional[dict]:
    """
    Parse un format spécifique de ticket.
    
    Args:
        text: Texte extrait par OCR
        
    Returns:
        Dict avec données structurées ou None
    """
    # Regex pour extraire infos
    montant_match = re.search(r'Total:?\s*(\d+[,.]?\d*)', text)
    
    if not montant_match:
        return None
    
    return {
        'montant': float(montant_match.group(1).replace(',', '.')),
        'date': extract_date(text),
        'description': extract_description(text)
    }
```

2. **Intégrer dans workflow**
```python
# Dans process_ticket()
result = parse_mon_format(text)
if result:
    return result
# Sinon, essayer autre parser
```

---

### Améliorer extraction

**Pré-traitement image** :

```python
from PIL import Image, ImageEnhance

def preprocess_image(image_path: str) -> Image:
    """Améliore qualité pour OCR"""
    img = Image.open(image_path)
    
    # Convertir en niveaux de gris
    img = img.convert('L')
    
    # Augmenter contraste
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2)
    
    # Augmenter netteté
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(2)
    
    return img
```


---

## ⚠️ LEÇONS CRITIQUES (Màj 17/12/2024)

### Leçon #1 : JAMAIS Normaliser O→0 Globalement

**INTERDIT** :
```python
text.replace("O", "0")  # Détruit MONTANT, TOTAL, etc.
```

**Pourquoi** :
```
MONTANT → M0NTANT  ❌ Pattern ne matche plus
TOTAL   → T0TAL    ❌ Pattern ne matche plus
```

**Conséquence historique** : A causé échec de 100% des patterns avant fix.

**Solution** :
- Ne PAS normaliser du tout en dehors de strip()
- OU normaliser SEULEMENT en contexte numérique strict

### Leçon #2 : Patterns Réels > Patterns Théoriques

Les tickets OCR produisent des variantes :
- `MONTANT KEEL` au lieu de `MONTANT REEL`
- `MONT ANT :` au lieu de `MONTANT :`
- `PATEMENT` au lieu de `PAIEMENT`

**Process obligatoire** :
1. Collecter tickets réels
2. Auditer (valeurs attendues)
3. Analyser texte OCR **BRUT**
4. Extraire patterns **réellement présents**
5. Créer regex flexibles avec variantes

**Ne JAMAIS** inventer patterns sans les avoir vus dans OCR réel.

### Leçon #3 : Tester Isolément Puis Production

Méthodologie debug en 2 étapes :
```python
# Étape 1: Test isolé
pattern = "MONTANT.*KEEL"
result = test_pattern(pattern, text)  # Fonctionne ?

# Étape 2: Reproduction production
result = parse_ticket_metadata_v2(text)  # Fonctionne aussi ?
```

Si **isolé OK** mais **production KO** → Bug dans la chaîne d'appels.

### Leçon #4 : Case-Insensitive Obligatoire

**TOUJOURS** :
```python
re.search(pattern, line, re.IGNORECASE)
```

OCR produit : `Total`, `TOTAL`, `total` de façon imprévisible.

---

## 🎯 Parsers existants


### ticket_parser.py
**Formats supportés** : Tickets généralistes

**Fonction principale** :
```python
def parse_ticket(text: str) -> Optional[dict]
```

**Extrait** :
- Montant (via regex)
- Date (via dateutil)
- Description (première ligne non vide)

---

### pdf_parser.py
**Formats supportés** : PDF Lydia, relevés bancaires

**Fonction principale** :
```python
def extract_text_from_pdf(pdf_path: str) -> str
```

---

## 🚨 Erreurs courantes

### Erreur #1 : Tesseract non installé

**Symptôme** :
```
TesseractNotFoundError: tesseract is not installed
```

**Solution** : Installer Tesseract OCR sur le système

### Erreur #2 : Mauvaise qualité image

**Problème** : OCR retourne texte vide ou incorrect

**Solutions** :
- Améliorer qualité image source
- Appliquer pré-traitement
- Utiliser config Tesseract adapté

### Erreur #3 : Regex trop stricte

**Problème** : Parser ne trouve rien

**Solution** : Assouplir regex
```python
# ❌ Trop strict
r'Total: (\d+\.\d{2})€'

# ✅ Plus flexible  
r'Total:?\s*(\d+[,.]?\d*)\s*€?'
```

---

## 📝 Checklist

Avant de commit un parser :
- [ ] Gestion d'erreurs complète
- [ ] Logs détaillés
- [ ] Validation résultats
- [ ] Testé sur plusieurs exemples
- [ ] Regex commentées
- [ ] Fallback si parsing échoue

---

## 🔗 Références

- [README module](../../v4/modules/ocr/README.md)
- [Guide implémentation](../guides/IMPLEMENTATION_GUIDE.md)
- [Documentation Tesseract](https://github.com/tesseract-ocr/tesseract)
