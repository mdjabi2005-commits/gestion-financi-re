# 📚 Bibliothèque : OpenCV (opencv-python-headless)

## 🎯 Qu'est-ce qu'OpenCV ?

**OpenCV** (Open Source Computer Vision) est LA bibliothèque de référence pour le traitement d'images et la vision par ordinateur. La version **opencv-python-headless** offre toutes les fonctionnalités sans les dépendances GUI, idéale pour les serveurs.

**Site officiel** : https://opencv.org  
**Documentation** : https://docs.opencv.org

---

## 💡 Pourquoi OpenCV dans notre projet ?

1. **Prétraitement OCR** : Améliorer qualité images avant Tesseract
2. **Binarisation** : Convertir en noir/blanc pour meilleure lecture
3. **Nettoyage** : Supprimer bruit, améliorer contraste
4. **Redimensionnement** : Adapter taille images
5. **Performance** : Traitement rapide et optimisé

---

## 🔧 Concepts de base

### 1. Lire et sauvegarder images

```python
import cv2

# Lire une image
img = cv2.imread('ticket.jpg')

# Lire en niveaux de gris directement
img_gray = cv2.imread('ticket.jpg', cv2.IMREAD_GRAYSCALE)

# Sauvegarder
cv2.imwrite('output.jpg', img)
```

### 2. Convertir en niveaux de gris

```python
import cv2

# Lire couleur
img = cv2.imread('ticket.jpg')

# Convertir en gris
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Sauvegarder
cv2.imwrite('ticket_gray.jpg', gray)
```

### 3. Redimensionner

```python
import cv2

img = cv2.imread('ticket.jpg')

# Redimensionner à une taille fixe
resized = cv2.resize(img, (800, 600))

# Redimensionner par facteur
scale_percent = 50  # 50% de la taille originale
width = int(img.shape[1] * scale_percent / 100)
height = int(img.shape[0] * scale_percent / 100)
resized = cv2.resize(img, (width, height))
```

---

## 📊 Exemples concrets de notre app

### Pipeline prétraitement OCR (`scanner.py`)

```python
import cv2
import numpy as np
from pathlib import Path

def preprocess_for_ocr(image_path: Path) -> np.ndarray:
    """
    Prétraite une image de ticket pour améliorer la précision OCR.
    
    Returns: Image prétraitée en niveaux de gris binarisée
    """
    # 1. Lecture robuste (gère chemins avec accents)
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
    
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        raise ValueError(f"Impossible de lire l'image: {image_path}")
    
    # 2. Conversion en niveaux de gris
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 3. Réduction du bruit avec flou gaussien
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    
    # 4. Binarisation adaptative (méthode Otsu)
    _, thresh = cv2.threshold(
        blurred,
        0,                      # Threshold (auto avec Otsu)
        255,                    # Valeur max
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    
    return thresh

# Utilisation
preprocessed = preprocess_for_ocr(Path("tickets/ticket_001.jpg"))
cv2.imwrite("tickets/ticket_001_preprocessed.jpg", preprocessed)
```

### Améliorer contraste (`scanner.py`)

```python
import cv2
import numpy as np

def enhance_contrast(img: np.ndarray) -> np.ndarray:
    """
    Améliore le contraste d'une image en niveaux de gris.
    Utilise l'égalisation d'histogramme.
    """
    # Égalisation d'histogramme
    enhanced = cv2.equalizeHist(img)
    
    return enhanced

# Alternative: CLAHE (Contrast Limited Adaptive Histogram Equalization)
def enhance_contrast_clahe(img: np.ndarray) -> np.ndarray:
    """
    Amélioration de contraste adaptative (meilleure pour tickets)
    """
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(img)
    
    return enhanced

# Utilisation
gray = cv2.imread('ticket.jpg', cv2.IMREAD_GRAYSCALE)
enhanced = enhance_contrast_clahe(gray)
cv2.imwrite('ticket_enhanced.jpg', enhanced)
```

### Redresser image inclinée

```python
import cv2
import numpy as np

def deskew_image(img: np.ndarray) -> np.ndarray:
    """
    Redresse une image inclinée (rotation automatique).
    """
    # Détection des contours
    coords = np.column_stack(np.where(img > 0))
    
    # Calculer l'angle de rotation
    angle = cv2.minAreaRect(coords)[-1]
    
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    
    # Appliquer la rotation
    (h, w) = img.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(
        img, M, (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE
    )
    
    return rotated
```

### Pipeline complet OCR

```python
import cv2
import pytesseract
from pathlib import Path

def full_ocr_pipeline(image_path: Path) -> str:
    """
    Pipeline complet: Prétraitement → OCR → Texte
    """
    # 1. Lire l'image
    img = cv2.imread(str(image_path))
    
    # 2. Convertir en gris
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 3. Flou pour réduire bruit
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    
    # 4. Binarisation Otsu
    _, thresh = cv2.threshold(
        blurred, 0, 255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    
    # 5. (Optionnel) Améliorer contraste
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(thresh)
    
    # 6. OCR avec Tesseract
    config = r'--oem 3 --psm 6'  # OCR Engine Mode + Page Segmentation
    text = pytesseract.image_to_string(
        enhanced,
        lang='fra+eng',
        config=config
    )
    
    return text.strip()

# Utilisation
ocr_text = full_ocr_pipeline(Path("tickets/ticket_restaurant.jpg"))
print(ocr_text)
```

---

## ⚠️ Pièges courants

### 1. Ordre des couleurs BGR (pas RGB!)

```python
import cv2

# ❌ OpenCV utilise BGR, pas RGB!
img = cv2.imread('image.jpg')
# img[:,:,0] = Blue
# img[:,:,1] = Green  
# img[:,:,2] = Red

# ✅ Convertir pour matplotlib/PIL
import matplotlib.pyplot as plt
img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
plt.imshow(img_rgb)
```

### 2. Vérifier que l'image est bien chargée

```python
import cv2

# ❌ Pas de vérification
img = cv2.imread('nonexistent.jpg')
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)  # CRASH!

# ✅ Toujours vérifier
img = cv2.imread('image.jpg')
if img is None:
    raise FileNotFoundError("Image non trouvée")

gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
```

### 3. Chemins avec accents (Windows)

```python
import cv2
import numpy as np

# ❌ Échoue avec chemins accentués sur Windows
img = cv2.imread('C:/Users/René/ticket.jpg')

# ✅ Solution : passer par numpy
with open('C:/Users/René/ticket.jpg', 'rb') as f:
    image_bytes = f.read()

nparr = np.frombuffer(image_bytes, np.uint8)
img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
```

### 4. Headless (pas de GUI)

```python
import cv2

# ❌ Ne fonctionne PAS avec opencv-python-headless
cv2.imshow('Image', img)
cv2.waitKey(0)

# ✅ Utiliser matplotlib ou PIL si besoin d'affichage
import matplotlib.pyplot as plt
plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
plt.show()
```

---

## 🔥 Opérations avancées

### Détection de contours

```python
import cv2

gray = cv2.imread('ticket.jpg', cv2.IMREAD_GRAYSCALE)

# Threshold
_, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)

# Trouver contours
contours, hierarchy = cv2.findContours(
    thresh,
    cv2.RETR_EXTERNAL,
    cv2.CHAIN_APPROX_SIMPLE
)

print(f"{len(contours)} contours trouvés")
```

### Morphologie (erosion/dilatation)

```python
import cv2
import numpy as np

# Kernel pour opérations morphologiques
kernel = np.ones((3,3), np.uint8)

# Erosion (rétrécit les objets blancs)
eroded = cv2.erode(img, kernel, iterations=1)

# Dilatation (agrandit les objets blancs)
dilated = cv2.dilate(img, kernel, iterations=1)

# Opening (erosion puis dilatation - supprime petits bruits)
opening = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)

# Closing (dilatation puis erosion - comble petits trous)
closing = cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel)
```

---

## 📖 Ressources

- **Documentation** : https://docs.opencv.org
- **Tutoriels** : https://docs.opencv.org/master/d9/df8/tutorial_root.html
- **PyPI headless** : https://pypi.org/project/opencv-python-headless/

---

## 💡 OpenCV dans notre projet

| Fichier | Utilisation |
|---------|------------|
| `scanner.py` | Prétraitement images avant OCR Tesseract |
| `domains/ocr/` | Pipeline complet de traitement d'images |

**Commande d'installation** :
```bash
pip install opencv-python-headless
```

**Pipeline OCR standard** :
1. Lecture image
2. Conversion niveaux de gris
3. Flou gaussien (réduction bruit)
4. Binarisation Otsu
5. (Optionnel) CLAHE pour contraste
6. Tesseract OCR

**Bonnes pratiques** :
- ✅ Toujours vérifier `img is not None`
- ✅ Utiliser `GaussianBlur` avant `threshold`
- ✅ Lire via numpy buffer pour chemins accentués
- ✅ Utiliser CLAHE pour tickets peu contrastés
- ❌ Ne pas oublier que OpenCV = BGR (pas RGB)
- ❌ Pas de `imshow` avec version headless
