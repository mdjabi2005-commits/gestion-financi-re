# Erreur : Flag créé trop tôt

**Symptôme**
- Le fichier `.gestio_v4_setup_done` était présent même si l'installation des dépendances avait échoué.
- L'application démarrait ensuite sans les packages requis, provoquant des erreurs `ModuleNotFoundError`.

**Cause**
- Le flag était créé immédiatement après le lancement de l'installateur, sans attendre le code de retour.

**Solution appliquée**
```python
# Dans gui_launcher.py
if verification_exit_code == 0:
    flag_file.touch()  # crée le flag uniquement si tout est OK
else:
    # ne crée pas le flag, l'utilisateur doit relancer l'app
    print("⚠️ Installation incomplète – relancez l'application.")
```
- Le flag n’est maintenant créé que lorsque le script de vérification renvoie **0**.

**Impact**
- Évite les lancements prématurés et les erreurs de module.
