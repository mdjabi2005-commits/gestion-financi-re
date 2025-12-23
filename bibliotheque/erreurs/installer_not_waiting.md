# Erreur : Installateur PowerShell ne bloque pas le script Python

**Symptôme**
- Le script Python continue immédiatement après le lancement de l'installateur.
- Message "Installation terminée" affiché trop tôt.

**Cause**
- Utilisation de `& powershell … -Wait` qui n’attend pas le processus.

**Solution appliquée**
```powershell
Start-Process -FilePath "powershell" \
    -ArgumentList "-ExecutionPolicy", "Bypass", "-File", "`"$installerPath`"" \
    -Wait \
    -NoNewWindow
```
- Le processus est maintenant réellement bloquant.

**Impact**
- Installation fiable, l'utilisateur sait quand relancer l'application.
