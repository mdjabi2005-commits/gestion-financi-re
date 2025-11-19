# ⚡ Démarrage Rapide - Backup Claude Code

Guide ultra-rapide pour sauvegarder vos conversations Claude Code sur GitHub en 5 minutes.

## 📋 Ce dont vous avez besoin

- [ ] Windows avec PowerShell
- [ ] Git installé ([télécharger](https://git-scm.com/downloads))
- [ ] Compte GitHub ([créer](https://github.com/signup))
- [ ] Au moins une conversation Claude Code existante

## 🚀 Installation en 5 étapes

### 1️⃣ Copier les scripts (1 min)

```powershell
# Ouvrez PowerShell et créez un dossier
mkdir C:\claude-backup-scripts
cd C:\claude-backup-scripts
```

Copiez ces 2 fichiers depuis votre dépôt Gestio vers `C:\claude-backup-scripts\`:
- `backup-claude-to-github.ps1`
- `setup-auto-backup.ps1`

### 2️⃣ Créer un dépôt GitHub (1 min)

1. Allez sur [github.com/new](https://github.com/new)
2. Nom: `claude-sessions-backup`
3. **IMPORTANT**: Cochez **Private** ✅
4. Cliquez **Create repository**

### 3️⃣ Premier backup (1 min)

```powershell
# Dans PowerShell
cd C:\claude-backup-scripts
.\backup-claude-to-github.ps1
```

Le script va:
- Créer `C:\Users\VOTRE-NOM\claude-sessions-backup\`
- Copier vos sessions
- Vous donner des commandes à exécuter

### 4️⃣ Lier à GitHub (1 min)

Copiez-collez les commandes affichées (remplacez `VOTRE-USERNAME`):

```powershell
cd "C:\Users\VOTRE-NOM\claude-sessions-backup"
git remote add origin https://github.com/VOTRE-USERNAME/claude-sessions-backup.git
git branch -M main
git push -u origin main
```

**À la demande de mot de passe:**
1. Allez sur GitHub → Settings → Developer settings → Personal access tokens
2. Generate new token (classic) → Cochez `repo` → Generate
3. Copiez le token (`ghp_...`)
4. Collez-le comme mot de passe

### 5️⃣ Automatiser (1 min) - OPTIONNEL

```powershell
# Ouvrez PowerShell EN ADMINISTRATEUR
cd C:\claude-backup-scripts
.\setup-auto-backup.ps1
```

✅ Backup automatique configuré ! (tous les jours à 20h par défaut)

## 🎉 C'est fait !

Vos conversations sont maintenant sauvegardées sur GitHub !

### Vérifier que ça marche

```powershell
# Relancez le script
.\backup-claude-to-github.ps1

# Vous devriez voir:
# ✅ Copie terminée
# ✅ Commit créé
# ✅ Push réussi vers GitHub!
```

### Voir vos sauvegardes

Allez sur: `https://github.com/VOTRE-USERNAME/claude-sessions-backup`

## 📖 Utilisation quotidienne

### Backup manuel

```powershell
cd C:\claude-backup-scripts
.\backup-claude-to-github.ps1
```

### Restaurer vos conversations

```powershell
# Cloner le backup
git clone https://github.com/VOTRE-USERNAME/claude-sessions-backup.git

# Copier dans Claude
Copy-Item -Path "claude-sessions-backup\*" -Destination "$env:USERPROFILE\.claude\sessions\" -Force -Exclude ".git","README.md"
```

### Gérer l'automatisation

```powershell
# Voir l'état
Get-ScheduledTask -TaskName "ClaudeCodeBackup"

# Lancer maintenant
Start-ScheduledTask -TaskName "ClaudeCodeBackup"

# Désactiver
Disable-ScheduledTask -TaskName "ClaudeCodeBackup"

# Supprimer
Unregister-ScheduledTask -TaskName "ClaudeCodeBackup"
```

## ❓ Problèmes fréquents

### "Le dossier Claude sessions n'existe pas"

➡️ Lancez Claude Code et créez au moins une conversation

### "Aucun dépôt distant configuré"

➡️ Vous avez oublié l'étape 4, exécutez les commandes `git remote add origin...`

### "Push failed: 403"

➡️ Problème d'authentification, vérifiez votre token GitHub

### Le backup automatique ne marche pas

```powershell
# Tester manuellement
Start-ScheduledTask -TaskName "ClaudeCodeBackup"

# Voir les erreurs
Get-ScheduledTaskInfo -TaskName "ClaudeCodeBackup"
```

## 🔧 Options avancées

### Changer la fréquence

```powershell
# Toutes les heures
.\setup-auto-backup.ps1 -Frequency Hourly

# Au démarrage
.\setup-auto-backup.ps1 -Frequency OnStartup

# À chaque connexion
.\setup-auto-backup.ps1 -Frequency OnLogon

# Tous les jours à 22h
.\setup-auto-backup.ps1 -Frequency Daily -Time "22:00"
```

### Backup vers un autre dossier

```powershell
.\backup-claude-to-github.ps1 -BackupPath "D:\MesSauvegardes\Claude"
```

### Voir les détails pendant le backup

```powershell
.\backup-claude-to-github.ps1 -Verbose
```

## 📚 Documentation complète

Pour plus de détails, consultez [README.md](README.md)

## 🆘 Aide

- Problème avec les scripts ? → [README.md - Dépannage](README.md#dépannage)
- Problème avec Claude Code ? → https://docs.claude.com/

---

**🎯 Mission accomplie ! Vos conversations sont en sécurité sur GitHub.**
