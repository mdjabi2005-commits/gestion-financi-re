# 📚 Bibliothèque : pdfminer.six

## 🎯 Qu'est-ce que pdfminer.six ?

**pdfminer.six** est une bibliothèque pure Python pour extraire du texte, des métadonnées et analyser la mise en page de fichiers PDF. C'est un fork maintenu de pdfminer, compatible Python 3.

**PyPI** : https://pypi.org/project/pdfminer.six/  
**Documentation** : https://pdfminer-docs.readthedocs.io

---

## 💡 Pourquoi pdfminer.six dans notre projet ?

1. **Extraction factures PDF** : Lire fiches de paie, factures Uber
2. **Pas d'OCR si texte** : Plus rapide et précis que Tesseract pour PDF texte
3. **Pure Python** : Facile à déployer, pas de dépendances système
4. **Analyse structure** : Préserver mise en page pour parsing
5. **Métadonnées** : Extraire titre, auteur, dates du PDF

---

## 🔧 Concepts de base

### 1. Extraction simple de texte

```python
from pdfminer.high_level import extract_text

# Extraire tout le texte d'un PDF
text = extract_text('facture.pdf')
print(text)
```

### 2. Extraire une page spécifique

```python
from pdfminer.high_level import extract_pages
from pdfminer.layout import LAParams, LTTextContainer

def extract_text_from_page(pdf_path: str, page_num: int = 0) -> str:
    """
    Extrait le texte d'une page spécifique (0-indexed).
    """
    text_parts = []
    
    for i, page_layout in enumerate(extract_pages(pdf_path)):
        if i == page_num:
            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    text_parts.append(element.get_text())
            break
    
    return ''.join(text_parts)

# Première page seulement
first_page_text = extract_text_from_page('facture.pdf', 0)
```

### 3. Extraire avec paramètres de mise en page

```python
from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams

# Configurer analyse de layout
laparams = LAParams(
    line_margin=0.5,        # Marge entre lignes
    word_margin=0.1,        # Marge entre mots
    char_margin=2.0,        # Marge entre caractères
    detect_vertical=True    # Détecter texte vertical
)

text = extract_text('facture.pdf', laparams=laparams)
```

---

## 📊 Exemples concrets de notre app

### Parser fiche de paie Uber (`revenues_service.py`)

```python
from pdfminer.high_level import extract_text
from pathlib import Path
import re

def parse_uber_pdf(pdf_path: Path) -> dict:
    """
    Extrait les données d'une fiche de paie Uber (PDF).
    
    Returns:
        dict: {
            'montant_brut': float,
            'montant_net': float,
            'periode': str,
            'date': str
        }
    """
    # Extraire le texte complet
    try:
        text = extract_text(str(pdf_path))
    except Exception as e:
        print(f"❌ Erreur extraction PDF: {e}")
        return None
    
    # Nettoyer le texte
    text = text.replace('\n', ' ').strip()
    
    # Parser les informations
    data = {}
    
    # Montant brut (ex: "Gains de la semaine : 456.78 €")
    brut_match = re.search(r"Gains.*?(\d+[.,]\d{2})\s*€", text, re.IGNORECASE)
    if brut_match:
        montant_str = brut_match.group(1).replace(',', '.')
        data['montant_brut'] = float(montant_str)
    
    # Période (ex: "Du 15/12/2024 au 21/12/2024")
    periode_match = re.search(
        r"Du\s+(\d{2}/\d{2}/\d{4})\s+au\s+(\d{2}/\d{2}/\d{4})",
        text,
        re.IGNORECASE
    )
    if periode_match:
        data['periode'] = f"{periode_match.group(1)} - {periode_match.group(2)}"
        data['date'] = periode_match.group(2)  # Date de fin
    
    # Calculer net (après prélèvement 21%)
    if 'montant_brut' in data:
        from config import UBER_TAX_RATE
        data['montant_net'] = data['montant_brut'] * (1 - UBER_TAX_RATE)
    
    return data

# Utilisation
uber_data = parse_uber_pdf(Path("revenus/uber_2024_12.pdf"))
if uber_data:
    print(f"Brut: {uber_data['montant_brut']}€")
    print(f"Net: {uber_data['montant_net']}€")
    print(f"Période: {uber_data['periode']}")
```

### Parser facture générique

```python
from pdfminer.high_level import extract_text
from pathlib import Path
import re
from datetime import datetime

def parse_facture_pdf(pdf_path: Path) -> dict:
    """
    Extrait données d'une facture PDF générique.
    Cherche: numéro facture, date, montant total, émetteur
    """
    text = extract_text(str(pdf_path))
    
    data = {
        'numero': None,
        'date': None,
        'montant_total': None,
        'emetteur': None
    }
    
    # Numéro de facture
    numero_patterns = [
        r"Facture\s*N°?\s*[:\-]?\s*([A-Z0-9\-]+)",
        r"Invoice\s*#?\s*([A-Z0-9\-]+)",
        r"N°\s*facture\s*[:\-]?\s*([A-Z0-9\-]+)"
    ]
    
    for pattern in numero_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            data['numero'] = match.group(1)
            break
    
    # Date
    date_patterns = [
        r"Date\s*[:\-]?\s*(\d{2}[/\-]\d{2}[/\-]\d{4})",
        r"(\d{2}[/\-]\d{2}[/\-]\d{4})"
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            date_str = match.group(1)
            # Normaliser format
            date_str = date_str.replace('-', '/')
            data['date'] = date_str
            break
    
    # Montant total
    total_patterns = [
        r"Total\s*TTC\s*[:\-]?\s*(\d+[.,]\d{2})\s*€",
        r"Montant\s*total\s*[:\-]?\s*(\d+[.,]\d{2})\s*€",
        r"Total\s*[:\-]?\s*(\d+[.,]\d{2})\s*€"
    ]
    
    for pattern in total_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            montant_str = match.group(1).replace(',', '.')
            data['montant_total'] = float(montant_str)
            break
    
    return data
```

### Combiner PDF + OCR pour images scannées

```python
from pdfminer.high_level import extract_text
from pathlib import Path
import pytesseract
from PIL import Image
import pdf2image

def extract_text_hybrid(pdf_path: Path) -> str:
    """
    Essaie d'abord pdfminer, puis OCR si PDF scanné.
    """
    # Tentative 1: pdfminer (PDF texte)
    try:
        text = extract_text(str(pdf_path))
        
        # Vérifier si texte significatif extrait
        text_clean = text.strip()
        if len(text_clean) > 50:  # Au moins 50 caractères
            return text_clean
    except Exception as e:
        print(f"⚠️ pdfminer échoué: {e}")
    
    # Tentative 2: OCR (PDF scanné/image)
    print("📸 PDF scanné détecté, utilisation OCR...")
    try:
        # Convertir PDF en images
        images = pdf2image.convert_from_path(str(pdf_path))
        
        # OCR sur chaque page
        ocr_texts = []
        for i, img in enumerate(images):
            print(f"OCR page {i+1}/{len(images)}...")
            text = pytesseract.image_to_string(img, lang='fra+eng')
            ocr_texts.append(text)
        
        return '\n\n--- PAGE BREAK ---\n\n'.join(ocr_texts)
        
    except Exception as e:
        print(f"❌ OCR échoué: {e}")
        return ""
```

---

## ⚠️ Pièges courants

### 1. PDF corrompus ou protégés

```python
from pdfminer.high_level import extract_text
from pdfminer.pdfparser import PDFSyntaxError

# ❌ Crash si PDF corrompu
text = extract_text('corrupted.pdf')

# ✅ Gérer l'exception
try:
    text = extract_text('document.pdf')
except PDFSyntaxError:
    print("❌ PDF corrompu ou invalide")
    text = ""
except Exception as e:
    print(f"❌ Erreur: {e}")
    text = ""
```

### 2. PDF scannés (images)

```python
from pdfminer.high_level import extract_text

# ❌ pdfminer ne peut pas lire les images!
text = extract_text('scan.pdf')
# text == "" ou très peu de contenu

# ✅ Vérifier et basculer vers OCR si nécessaire
text = extract_text('document.pdf')
if len(text.strip()) < 50:
    # Probablement un scan, utiliser OCR
    text = extract_with_ocr('document.pdf')
```

### 3. Encodage et caractères spéciaux

```python
from pdfminer.high_level import extract_text

# ❌ Peut avoir des problèmes d'encodage
text = extract_text('facture.pdf')

# ✅ Nettoyer les caractères de contrôle
import re

text = extract_text('facture.pdf')
# Supprimer caractères de contrôle
text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
# Normaliser espaces
text = re.sub(r'\s+', ' ', text)
```

### 4. Performance sur gros PDF

```python
from pdfminer.high_level import extract_text

# ❌ Lent sur gros PDF (100+ pages)
text = extract_text('rapport_annuel.pdf')

# ✅ Extraire seulement les pages nécessaires
from pdfminer.high_level import extract_pages

def extract_first_n_pages(pdf_path: str, n: int = 5) -> str:
    texts = []
    for i, page in enumerate(extract_pages(pdf_path)):
        if i >= n:
            break
        # Extraire texte de cette page
        # ...
    return '\n'.join(texts)
```

---

## 🔥 Opérations avancées

### Extraire métadonnées PDF

```python
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument

def get_pdf_metadata(pdf_path: str) -> dict:
    """
    Extrait les métadonnées d'un PDF.
    """
    with open(pdf_path, 'rb') as f:
        parser = PDFParser(f)
        doc = PDFDocument(parser)
        
        metadata = {}
        
        if doc.info:
            for info in doc.info:
                for key, value in info.items():
                    # Décoder bytes en string
                    if isinstance(value, bytes):
                        try:
                            value = value.decode('utf-8')
                        except:
                            value = str(value)
                    metadata[key.decode() if isinstance(key, bytes) else key] = value
        
        return metadata

# Utilisation
meta = get_pdf_metadata('facture.pdf')
print(f"Titre: {meta.get('Title', 'N/A')}")
print(f"Auteur: {meta.get('Author', 'N/A')}")
print(f"Créé le: {meta.get('CreationDate', 'N/A')}")
```

### Analyser structure et layout

```python
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextBox, LTFigure, LTImage

def analyze_pdf_structure(pdf_path: str):
    """
    Analyse la structure d'un PDF (texte, images, etc.)
    """
    for page_num, page_layout in enumerate(extract_pages(pdf_path)):
        print(f"\n=== Page {page_num + 1} ===")
        
        for element in page_layout:
            if isinstance(element, LTTextBox):
                print(f"Texte: {element.get_text()[:50]}...")
            elif isinstance(element, LTImage):
                print(f"Image: {element.name}")
            elif isinstance(element, LTFigure):
                print(f"Figure: {element}")
```

---

## 📖 Ressources

- **Documentation** : https://pdfminer-docs.readthedocs.io
- **PyPI** : https://pypi.org/project/pdfminer.six/
- **GitHub** : https://github.com/pdfminer/pdfminer.six

---

## 💡 pdfminer.six dans notre projet

| Fichier | Utilisation |
|---------|------------|
| `revenues_service.py` | Parser fiches de paie Uber PDF |
| `domains/ocr/` | Extraction texte factures PDF (avant OCR fallback) |
| `revenues_db.py` | Traitement automatique revenus PDF |

**Commande d'installation** :
```bash
pip install pdfminer.six
```

**Workflow recommandé** :
1. Essayer `pdfminer.six` d'abord (rapide pour PDF texte)
2. Si texte insuffisant (\< 50 chars), basculer OCR
3. Parser le texte extrait avec regex
4. Valider et structurer les données

**Bonnes pratiques** :
- ✅ Toujours gérer `PDFSyntaxError`
- ✅ Vérifier longueur texte extrait
- ✅ Nettoyer caractères de contrôle
- ✅ Combiner avec OCR pour PDF scannés
- ❌ Ne pas utiliser sur PDF très lourds sans limite pages
- ❌ Ne pas assumer que le PDF contient du texte
