# Script de sauvegarde automatique des conversations Claude Code vers GitHub
# Auteur: Généré par Claude Code
# Date: 2025-11-19

param(
    [string]$BackupPath = "$env:USERPROFILE\claude-sessions-backup",
    [switch]$AutoCommit = $true,
    [switch]$Verbose = $false
)

# Couleurs pour l'output
function Write-Success { Write-Host $args -ForegroundColor Green }
function Write-Info { Write-Host $args -ForegroundColor Cyan }
function Write-Warning { Write-Host $args -ForegroundColor Yellow }
function Write-Error { Write-Host $args -ForegroundColor Red }

# Banner
Write-Host "`n============================================" -ForegroundColor Magenta
Write-Host "  Backup Claude Code Sessions → GitHub" -ForegroundColor Magenta
Write-Host "============================================`n" -ForegroundColor Magenta

# Chemins
$ClaudePath = "$env:USERPROFILE\.claude\sessions"
$BackupRepo = $BackupPath

# Vérifier que le dossier Claude existe
if (-Not (Test-Path $ClaudePath)) {
    Write-Error "❌ Erreur: Le dossier Claude sessions n'existe pas: $ClaudePath"
    Write-Warning "   Vérifiez que Claude Code est installé et que vous avez au moins une conversation."
    exit 1
}

# Vérifier/Créer le dossier de backup
if (-Not (Test-Path $BackupRepo)) {
    Write-Warning "⚠️  Le dossier de backup n'existe pas encore: $BackupRepo"
    Write-Info "📁 Création du dossier de backup..."
    New-Item -ItemType Directory -Path $BackupRepo -Force | Out-Null

    # Initialiser le repo Git
    Write-Info "🔧 Initialisation du dépôt Git..."
    Push-Location $BackupRepo
    git init

    # Créer un README
    @"
# Claude Code Sessions Backup

Ce dépôt contient les sauvegardes automatiques de mes conversations Claude Code.

## Structure

- Chaque conversation est sauvegardée dans un fichier JSON
- Les conversations sont organisées par date
- Les sauvegardes sont automatiques via le script PowerShell

## Restauration

Pour restaurer vos conversations:
1. Copiez le contenu de ce dépôt dans ``$env:USERPROFILE\.claude\sessions\``
2. Redémarrez Claude Code
3. Vos conversations seront disponibles

## Sauvegarde automatique

Le script ``backup-claude-to-github.ps1`` effectue:
- Copie des sessions Claude vers ce dépôt
- Commit automatique des changements
- Push vers GitHub

Dernière sauvegarde: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
"@ | Out-File -FilePath "README.md" -Encoding utf8

    git add README.md
    git commit -m "Initial commit: Setup Claude Code backup repository"

    Write-Success "✅ Dépôt Git initialisé avec succès!"
    Write-Warning "`n⚠️  IMPORTANT: Configurez maintenant votre dépôt GitHub distant:"
    Write-Info "   1. Créez un nouveau dépôt sur GitHub (par exemple: claude-sessions-backup)"
    Write-Info "   2. Exécutez ces commandes dans PowerShell:"
    Write-Host "      cd `"$BackupRepo`"" -ForegroundColor Yellow
    Write-Host "      git remote add origin https://github.com/VOTRE-USERNAME/claude-sessions-backup.git" -ForegroundColor Yellow
    Write-Host "      git branch -M main" -ForegroundColor Yellow
    Write-Host "      git push -u origin main" -ForegroundColor Yellow
    Write-Info "`n   3. Puis relancez ce script pour la première sauvegarde`n"

    Pop-Location
    exit 0
}

# Vérifier que c'est un dépôt Git
Push-Location $BackupRepo
if (-Not (Test-Path ".git")) {
    Write-Error "❌ Erreur: $BackupRepo n'est pas un dépôt Git"
    Write-Info "   Supprimez le dossier et relancez le script pour l'initialiser."
    Pop-Location
    exit 1
}

# Vérifier la configuration Git remote
$remoteUrl = git remote get-url origin 2>$null
if (-Not $remoteUrl) {
    Write-Warning "⚠️  Aucun dépôt distant configuré!"
    Write-Info "   Configurez votre GitHub remote avec:"
    Write-Host "   git remote add origin https://github.com/VOTRE-USERNAME/claude-sessions-backup.git" -ForegroundColor Yellow
    Pop-Location
    exit 1
}

Write-Info "📂 Source:      $ClaudePath"
Write-Info "📁 Destination: $BackupRepo"
Write-Info "🔗 GitHub:      $remoteUrl`n"

# Compter les fichiers
$sessionFiles = Get-ChildItem -Path $ClaudePath -File
$sessionCount = $sessionFiles.Count

if ($sessionCount -eq 0) {
    Write-Warning "⚠️  Aucune session trouvée dans $ClaudePath"
    Pop-Location
    exit 0
}

Write-Info "📊 $sessionCount fichier(s) de session trouvé(s)"

# Copier les fichiers
Write-Info "📋 Copie des sessions..."
$copiedCount = 0
$updatedCount = 0
$newCount = 0

foreach ($file in $sessionFiles) {
    $destPath = Join-Path $BackupRepo $file.Name

    if (Test-Path $destPath) {
        # Comparer les fichiers
        $sourceHash = (Get-FileHash $file.FullName).Hash
        $destHash = (Get-FileHash $destPath).Hash

        if ($sourceHash -ne $destHash) {
            Copy-Item $file.FullName -Destination $destPath -Force
            $updatedCount++
            if ($Verbose) { Write-Host "   ↻ Mis à jour: $($file.Name)" -ForegroundColor Yellow }
        }
    } else {
        Copy-Item $file.FullName -Destination $destPath
        $newCount++
        if ($Verbose) { Write-Host "   + Nouveau: $($file.Name)" -ForegroundColor Green }
    }
    $copiedCount++
}

Write-Success "✅ Copie terminée: $copiedCount fichiers traités ($newCount nouveaux, $updatedCount mis à jour)"

# Mise à jour du README avec la date
$readmePath = Join-Path $BackupRepo "README.md"
if (Test-Path $readmePath) {
    $readme = Get-Content $readmePath -Raw
    $readme = $readme -replace "Dernière sauvegarde:.*", "Dernière sauvegarde: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    $readme | Out-File -FilePath $readmePath -Encoding utf8 -NoNewline
}

# Git operations
if ($AutoCommit) {
    Write-Info "`n🔄 Synchronisation Git..."

    # Ajouter tous les fichiers
    git add .

    # Vérifier s'il y a des changements
    $status = git status --porcelain

    if ($status) {
        # Commit
        $commitMsg = "Backup automatique: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - $sessionCount sessions"
        git commit -m $commitMsg | Out-Null
        Write-Success "✅ Commit créé: $commitMsg"

        # Push avec retry logic
        $maxRetries = 4
        $retryDelay = 2
        $pushed = $false

        for ($i = 1; $i -le $maxRetries; $i++) {
            Write-Info "📤 Push vers GitHub (tentative $i/$maxRetries)..."

            $pushResult = git push origin main 2>&1

            if ($LASTEXITCODE -eq 0) {
                Write-Success "✅ Push réussi vers GitHub!"
                $pushed = $true
                break
            } else {
                if ($i -lt $maxRetries) {
                    Write-Warning "⚠️  Échec du push, nouvelle tentative dans ${retryDelay}s..."
                    Start-Sleep -Seconds $retryDelay
                    $retryDelay *= 2
                } else {
                    Write-Error "❌ Échec du push après $maxRetries tentatives"
                    Write-Warning "   Erreur: $pushResult"
                    Write-Info "   Essayez de push manuellement plus tard avec:"
                    Write-Host "   cd `"$BackupRepo`" && git push" -ForegroundColor Yellow
                }
            }
        }
    } else {
        Write-Info "ℹ️  Aucun changement à sauvegarder"
    }
}

Pop-Location

Write-Host "`n============================================" -ForegroundColor Magenta
Write-Success "✅ Sauvegarde terminée avec succès!"
Write-Host "============================================`n" -ForegroundColor Magenta

# Statistiques finales
Write-Info "📊 Statistiques:"
Write-Host "   • Sessions totales:    $sessionCount" -ForegroundColor White
Write-Host "   • Nouvelles sessions:  $newCount" -ForegroundColor Green
Write-Host "   • Sessions mises à jour: $updatedCount" -ForegroundColor Yellow
Write-Host "   • Emplacement backup:  $BackupRepo" -ForegroundColor Cyan
Write-Host "   • GitHub:              $remoteUrl`n" -ForegroundColor Cyan
