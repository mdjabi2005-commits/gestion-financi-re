# 💾 Sauvegarde Automatique des Conversations Claude Code

Ce dossier contient des scripts PowerShell pour sauvegarder automatiquement vos conversations Claude Code vers un dépôt GitHub.

## 📋 Table des matières

- [Pourquoi ce système ?](#pourquoi-ce-système-)
- [Prérequis](#prérequis)
- [Installation rapide](#installation-rapide)
- [Utilisation](#utilisation)
- [Configuration avancée](#configuration-avancée)
- [Restauration](#restauration)
- [Dépannage](#dépannage)

## 🤔 Pourquoi ce système ?

### Problème
- Claude Code sauvegarde vos conversations dans `C:\Users\VOTRE-NOM\.claude\sessions\`
- Si vous perdez ces fichiers (crash disque, réinstallation Windows), vous perdez toutes vos conversations
- Pas de synchronisation entre plusieurs ordinateurs

### Solution
- Sauvegarde automatique vers GitHub
- Historique complet de toutes vos modifications
- Accessible depuis n'importe où
- Restauration facile en cas de problème

## ✅ Prérequis

1. **Git installé** ([télécharger](https://git-scm.com/downloads))
2. **Compte GitHub** ([créer](https://github.com/signup))
3. **PowerShell** (déjà installé sur Windows)
4. **Claude Code CLI** avec au moins une conversation existante

## 🚀 Installation rapide

### Étape 1: Copier les scripts

Ces scripts sont dans votre dépôt Gestio sous `/home/user/gestion-financi-re/backup-scripts/` (WSL).

Pour les utiliser sous Windows, copiez-les:

```powershell
# Depuis PowerShell Windows:
# Option 1: Via WSL (si vous avez WSL installé)
wsl cp /home/user/gestion-financi-re/backup-scripts/*.ps1 /mnt/c/Users/$env:USERNAME/Downloads/

# Option 2: Créez le dossier et copiez manuellement
mkdir C:\claude-backup-scripts
# Puis copiez backup-claude-to-github.ps1 et setup-auto-backup.ps1 dans ce dossier
```

### Étape 2: Créer un dépôt GitHub

1. Allez sur [github.com](https://github.com) et connectez-vous
2. Cliquez sur le **+** en haut à droite → **New repository**
3. Nommez-le: `claude-sessions-backup`
4. **Important**: Cochez **Private** (vos conversations sont privées !)
5. Ne cochez rien d'autre
6. Cliquez **Create repository**

### Étape 3: Premier lancement

```powershell
# Ouvrez PowerShell et allez dans le dossier des scripts
cd C:\claude-backup-scripts

# Lancez le script de backup (première fois)
.\backup-claude-to-github.ps1
```

**Ce qui va se passer:**
- Création du dossier `C:\Users\VOTRE-NOM\claude-sessions-backup`
- Initialisation d'un dépôt Git
- Affichage des commandes à exécuter pour lier à GitHub

### Étape 4: Lier au dépôt GitHub

Le script vous donnera des commandes à exécuter. Exemple:

```powershell
cd "C:\Users\VOTRE-NOM\claude-sessions-backup"
git remote add origin https://github.com/VOTRE-USERNAME/claude-sessions-backup.git
git branch -M main
git push -u origin main
```

**Remplacez `VOTRE-USERNAME` par votre nom d'utilisateur GitHub !**

### Étape 5: Configurer l'authentification GitHub

Lors du premier push, Windows vous demandera de vous authentifier:

1. **Méthode recommandée**: Utilisez un **Personal Access Token**
   - Allez sur GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Generate new token → Cochez `repo` → Generate
   - Copiez le token (format: `ghp_...`)
   - Utilisez-le comme mot de passe

2. **Ou**: Utilisez GitHub Desktop ou GitHub CLI

### Étape 6: Tester la sauvegarde

```powershell
# Relancez le script
.\backup-claude-to-github.ps1
```

Vous devriez voir:
```
✅ Copie terminée: X fichiers traités
✅ Commit créé
✅ Push réussi vers GitHub!
```

### Étape 7: Automatisation (optionnel)

Pour sauvegarder automatiquement tous les jours:

```powershell
# Ouvrez PowerShell en ADMINISTRATEUR
cd C:\claude-backup-scripts

# Lancez le script de configuration
.\setup-auto-backup.ps1 -Frequency Daily -Time "20:00"
```

Options:
- `-Frequency Daily` : Tous les jours (défaut)
- `-Frequency Hourly` : Toutes les heures
- `-Frequency OnStartup` : Au démarrage de Windows
- `-Frequency OnLogon` : À chaque connexion
- `-Time "20:00"` : Heure pour Daily (format 24h)

## 📖 Utilisation

### Sauvegarde manuelle

```powershell
# Sauvegarde simple
.\backup-claude-to-github.ps1

# Avec affichage détaillé
.\backup-claude-to-github.ps1 -Verbose

# Vers un autre dossier
.\backup-claude-to-github.ps1 -BackupPath "D:\MesSauvegardes\Claude"

# Sans commit/push automatique (juste copie)
.\backup-claude-to-github.ps1 -AutoCommit:$false
```

### Vérifier la tâche automatique

```powershell
# Voir l'état de la tâche
Get-ScheduledTask -TaskName "ClaudeCodeBackup"

# Voir la dernière exécution
Get-ScheduledTaskInfo -TaskName "ClaudeCodeBackup"

# Exécuter manuellement
Start-ScheduledTask -TaskName "ClaudeCodeBackup"

# Désactiver temporairement
Disable-ScheduledTask -TaskName "ClaudeCodeBackup"

# Réactiver
Enable-ScheduledTask -TaskName "ClaudeCodeBackup"

# Supprimer la tâche
Unregister-ScheduledTask -TaskName "ClaudeCodeBackup"
```

### Voir les sauvegardes sur GitHub

1. Allez sur votre dépôt: `https://github.com/VOTRE-USERNAME/claude-sessions-backup`
2. Vous verrez tous vos fichiers de sessions
3. Cliquez sur **Commits** pour voir l'historique

## 🔧 Configuration avancée

### Personnaliser le chemin de backup

Modifiez le paramètre par défaut dans le script:

```powershell
# Au lieu de C:\Users\...\claude-sessions-backup
.\backup-claude-to-github.ps1 -BackupPath "D:\MesSauvegardes\Claude"
```

### Changer la fréquence d'automatisation

Relancez simplement `setup-auto-backup.ps1` avec de nouveaux paramètres:

```powershell
# Passer de Daily à Hourly
.\setup-auto-backup.ps1 -Frequency Hourly
```

### Utiliser plusieurs dépôts

Vous pouvez créer plusieurs tâches avec différents paramètres:

```powershell
# Modifier le nom de la tâche dans setup-auto-backup.ps1
# Ligne 54: $taskName = "ClaudeCodeBackup"
# Changez en: $taskName = "ClaudeCodeBackup-Hourly"
```

### Exclure certains fichiers

Créez un fichier `.gitignore` dans le dossier de backup:

```bash
cd "C:\Users\VOTRE-NOM\claude-sessions-backup"
echo "temp*" > .gitignore
echo "*.tmp" >> .gitignore
git add .gitignore
git commit -m "Add gitignore"
```

## 🔄 Restauration

### Restaurer sur le même PC

1. Clonez votre dépôt de backup:
   ```powershell
   cd C:\Users\VOTRE-NOM
   git clone https://github.com/VOTRE-USERNAME/claude-sessions-backup.git claude-sessions-restore
   ```

2. Copiez les sessions:
   ```powershell
   # Sauvegardez d'abord les sessions actuelles (au cas où)
   Copy-Item -Path "$env:USERPROFILE\.claude\sessions" -Destination "$env:USERPROFILE\.claude\sessions.backup" -Recurse

   # Restaurez depuis GitHub
   Copy-Item -Path "C:\Users\VOTRE-NOM\claude-sessions-restore\*" -Destination "$env:USERPROFILE\.claude\sessions\" -Force -Exclude ".git","README.md"
   ```

3. Redémarrez Claude Code

### Restaurer sur un nouveau PC

```powershell
# 1. Installez Claude Code
# 2. Lancez-le une fois pour créer les dossiers
# 3. Clonez vos sauvegardes
git clone https://github.com/VOTRE-USERNAME/claude-sessions-backup.git

# 4. Copiez les sessions
Copy-Item -Path "claude-sessions-backup\*" -Destination "$env:USERPROFILE\.claude\sessions\" -Force -Exclude ".git","README.md"
```

### Restaurer une conversation spécifique

```powershell
# Voir l'historique sur GitHub et trouver le commit
# Puis restaurer un fichier spécifique:
cd claude-sessions-backup
git checkout COMMIT-HASH -- nom-du-fichier.json
Copy-Item nom-du-fichier.json -Destination "$env:USERPROFILE\.claude\sessions\"
```

## 🔍 Dépannage

### Erreur: "Le dossier Claude sessions n'existe pas"

**Cause**: Claude Code n'a pas encore créé de sessions.

**Solution**: Lancez Claude Code et créez au moins une conversation:
```bash
claude
# Tapez quelque chose, puis quittez
```

### Erreur: "Aucun dépôt distant configuré"

**Cause**: Vous n'avez pas lié le dépôt local à GitHub.

**Solution**: Exécutez les commandes affichées par le script:
```powershell
cd "C:\Users\VOTRE-NOM\claude-sessions-backup"
git remote add origin https://github.com/VOTRE-USERNAME/claude-sessions-backup.git
git branch -M main
git push -u origin main
```

### Erreur: "Push failed: 403"

**Cause**: Problème d'authentification GitHub.

**Solutions**:
1. Vérifiez votre token d'accès personnel
2. Utilisez GitHub CLI: `gh auth login`
3. Ou configurez Git Credential Manager:
   ```powershell
   git config --global credential.helper manager
   ```

### Erreur: "Push failed: Network error"

**Cause**: Problème réseau temporaire.

**Solution**: Le script réessaie automatiquement 4 fois. Si ça échoue:
```powershell
cd "C:\Users\VOTRE-NOM\claude-sessions-backup"
git push
```

### La tâche automatique ne s'exécute pas

**Vérifications**:
```powershell
# 1. Vérifier que la tâche existe
Get-ScheduledTask -TaskName "ClaudeCodeBackup"

# 2. Voir la dernière exécution et les erreurs
Get-ScheduledTaskInfo -TaskName "ClaudeCodeBackup"

# 3. Tester manuellement
Start-ScheduledTask -TaskName "ClaudeCodeBackup"

# 4. Voir les logs dans l'Observateur d'événements
# Ouvrez: eventvwr.msc
# Allez dans: Applications and Services Logs > Microsoft > Windows > TaskScheduler
```

### Les fichiers ne sont pas copiés

**Vérifications**:
```powershell
# Vérifier que les sessions existent
dir "$env:USERPROFILE\.claude\sessions"

# Vérifier le dossier de backup
dir "$env:USERPROFILE\claude-sessions-backup"

# Lancer avec verbose pour voir les détails
.\backup-claude-to-github.ps1 -Verbose
```

### Conflit Git (diverged branches)

**Cause**: Modifications sur GitHub et en local.

**Solution**:
```powershell
cd "$env:USERPROFILE\claude-sessions-backup"

# Option 1: Forcer avec les fichiers locaux (recommandé)
git push --force

# Option 2: Merger (si vous avez modifié sur GitHub)
git pull --rebase
git push
```

### Supprimer et recommencer

Si tout est cassé, recommencez à zéro:

```powershell
# 1. Sauvegarder les sessions actuelles
Copy-Item "$env:USERPROFILE\.claude\sessions" -Destination "C:\claude-sessions-manual-backup" -Recurse

# 2. Supprimer le dépôt local
Remove-Item "$env:USERPROFILE\claude-sessions-backup" -Recurse -Force

# 3. Supprimer la tâche
Unregister-ScheduledTask -TaskName "ClaudeCodeBackup" -Confirm:$false

# 4. Relancer depuis l'étape 3 de l'installation
.\backup-claude-to-github.ps1
```

## 📊 Structure du backup

```
claude-sessions-backup/
├── .git/                          # Dépôt Git (historique)
├── README.md                      # Info sur le backup
├── session-XXXXX-XXXXX.json      # Vos conversations Claude
├── session-YYYYY-YYYYY.json
└── ...
```

Chaque fichier JSON contient:
- L'historique complet d'une conversation
- Les messages de l'utilisateur et de Claude
- Les actions effectuées (fichiers modifiés, commandes, etc.)
- Les métadonnées (date, modèle utilisé, etc.)

## 🔒 Sécurité

### Données sensibles

**Important**: Vos conversations peuvent contenir:
- Des chemins de fichiers
- Du code source
- Des clés API (si vous les avez partagées avec Claude)
- Des informations personnelles

**Recommandations**:
1. ✅ **Utilisez un dépôt PRIVÉ** (pas public !)
2. ✅ Ne partagez jamais votre token GitHub
3. ✅ Utilisez 2FA sur votre compte GitHub
4. ⚠️  Avant de partager une conversation, vérifiez qu'elle ne contient pas de secrets

### Nettoyer les données sensibles

Si vous avez accidentellement commité des secrets:

```powershell
cd "$env:USERPROFILE\claude-sessions-backup"

# Supprimer un fichier de l'historique Git
git filter-branch --force --index-filter "git rm --cached --ignore-unmatch session-avec-secrets.json" --prune-empty --tag-name-filter cat -- --all

# Forcer le push
git push --force
```

**Attention**: Les secrets ont déjà été exposés ! Révoquez-les immédiatement.

## 💡 Astuces

### Voir la taille du backup

```powershell
$path = "$env:USERPROFILE\claude-sessions-backup"
$size = (Get-ChildItem -Path $path -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB
Write-Host "Taille totale: $([math]::Round($size, 2)) MB"
```

### Rechercher dans vos conversations

```powershell
cd "$env:USERPROFILE\claude-sessions-backup"

# Rechercher un mot-clé
Select-String -Path "*.json" -Pattern "gestiov4"

# Compter les conversations
(Get-ChildItem -Filter "*.json").Count
```

### Synchroniser plusieurs PCs

1. PC 1: Configurez le backup automatique
2. PC 2: Clonez le dépôt dans `~/.claude/sessions`
3. PC 2: Configurez aussi le backup automatique
4. Les deux PCs pousseront leurs changements vers GitHub

**Note**: Attention aux conflits si vous utilisez la même conversation sur 2 PCs en même temps !

### Backup avant une mise à jour Windows

```powershell
# Forcez un backup immédiat
.\backup-claude-to-github.ps1

# Vérifiez qu'il a réussi
cd "$env:USERPROFILE\claude-sessions-backup"
git log -1
```

## 🆘 Support

### Problèmes avec les scripts

1. Vérifiez que vous avez la dernière version
2. Consultez la section [Dépannage](#dépannage)
3. Ouvrez une issue sur GitHub du projet Gestio

### Problèmes avec Claude Code

- Documentation officielle: https://docs.claude.com/
- GitHub: https://github.com/anthropics/claude-code

## 📝 Changelog

### Version 1.0 (2025-11-19)
- Script de backup initial
- Script de configuration automatique
- Documentation complète
- Gestion des erreurs réseau avec retry
- Support de plusieurs fréquences de backup

## 📄 Licence

Ces scripts sont fournis "tels quels" sans garantie.
Vous êtes libre de les modifier et les partager.

---

**Créé avec ❤️ par Claude Code pour sauvegarder vos conversations !**
