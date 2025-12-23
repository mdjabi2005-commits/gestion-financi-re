# Erreur : Mapping incorrect des noms de packages Python

**Symptôme**
- `pip install PIL` ou `pip install cv2` échoue.
- L'application ne trouve pas les modules `PIL` ou `cv2`.

**Cause**
- Le nom du module importé ne correspond pas au nom du package PyPI.
  - `PIL` → `Pillow`
  - `cv2` → `opencv-python-headless`
  - `dateutil` → `python-dateutil`
  - `pdfminer` → `pdfminer.six`
  - `yaml` → `PyYAML`

**Solution appliquée**
```powershell
$packageMapping = @{
    "PIL"       = "Pillow"
    "cv2"       = "opencv-python-headless"
    "dateutil"  = "python-dateutil"
    "pdfminer"  = "pdfminer.six"
    "yaml"      = "PyYAML"
}
```
- Le script utilise ce dictionnaire pour installer le bon package.
- Après correction, l'installation se fait sans erreur.
