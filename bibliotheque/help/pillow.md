# Pillow

**Description** : Bibliothèque d'imagerie Python (fork de PIL). Permet de charger, transformer et enregistrer des images (PNG, JPEG, etc.). Utilisée dans Gestio V4 pour le redimensionnement et la génération de miniatures des tickets OCR.

**Installation** :
```bash
pip install Pillow
```

**Points d’attention** :
- Requiert `libjpeg`/`zlib` sur le système pour certains formats.
- Utiliser `Image.open(...).convert('RGB')` avant de sauvegarder en JPEG.
- Méthodes courantes : `Image.resize()`, `Image.thumbnail()`, `Image.save()`.

**Bonnes pratiques** :
- Toujours fermer les images (`img.close()`) ou utiliser le contexte `with Image.open(...) as img:`.
- Préférer `thumbnail()` pour garder le ratio d’aspect.
- Limiter la taille des images en mémoire (ex. `max_pixels = 10_000_000`).
