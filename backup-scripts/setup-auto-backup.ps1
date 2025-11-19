# Script de configuration de la sauvegarde automatique
# Configure Task Scheduler pour exécuter la sauvegarde régulièrement
# Auteur: Généré par Claude Code
# Date: 2025-11-19

#Requires -RunAsAdministrator

param(
    [ValidateSet("Hourly", "Daily", "OnStartup", "OnLogon")]
    [string]$Frequency = "Daily",
    [string]$BackupPath = "$env:USERPROFILE\claude-sessions-backup",
    [string]$Time = "20:00"  # Heure pour Daily (format 24h)
)

Write-Host "`n============================================" -ForegroundColor Magenta
Write-Host "  Configuration Backup Automatique Claude" -ForegroundColor Magenta
Write-Host "============================================`n" -ForegroundColor Magenta

# Vérifier les droits administrateur
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
$isAdmin = $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-Not $isAdmin) {
    Write-Host "❌ Ce script nécessite les droits administrateur!" -ForegroundColor Red
    Write-Host "   Relancez PowerShell en tant qu'administrateur et réexécutez ce script." -ForegroundColor Yellow
    exit 1
}

# Chemin du script de backup
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$backupScript = Join-Path $scriptDir "backup-claude-to-github.ps1"

if (-Not (Test-Path $backupScript)) {
    Write-Host "❌ Script de backup introuvable: $backupScript" -ForegroundColor Red
    exit 1
}

Write-Host "📁 Script de backup: $backupScript" -ForegroundColor Cyan
Write-Host "📂 Dossier de backup: $BackupPath" -ForegroundColor Cyan
Write-Host "⏱️  Fréquence: $Frequency" -ForegroundColor Cyan

if ($Frequency -eq "Daily") {
    Write-Host "🕐 Heure: $Time" -ForegroundColor Cyan
}

Write-Host ""

# Nom de la tâche
$taskName = "ClaudeCodeBackup"

# Vérifier si la tâche existe déjà
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue

if ($existingTask) {
    Write-Host "⚠️  Une tâche '$taskName' existe déjà." -ForegroundColor Yellow
    $response = Read-Host "Voulez-vous la remplacer? (O/N)"

    if ($response -ne "O" -and $response -ne "o") {
        Write-Host "❌ Configuration annulée." -ForegroundColor Red
        exit 0
    }

    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Write-Host "✅ Ancienne tâche supprimée" -ForegroundColor Green
}

# Créer l'action
$action = New-ScheduledTaskAction `
    -Execute "PowerShell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$backupScript`" -BackupPath `"$BackupPath`""

# Créer le trigger selon la fréquence
switch ($Frequency) {
    "Hourly" {
        $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 1) -RepetitionDuration ([TimeSpan]::MaxValue)
        Write-Host "⏰ Backup programmé toutes les heures" -ForegroundColor Green
    }
    "Daily" {
        $trigger = New-ScheduledTaskTrigger -Daily -At $Time
        Write-Host "⏰ Backup programmé chaque jour à $Time" -ForegroundColor Green
    }
    "OnStartup" {
        $trigger = New-ScheduledTaskTrigger -AtStartup
        Write-Host "⏰ Backup programmé au démarrage de Windows" -ForegroundColor Green
    }
    "OnLogon" {
        $trigger = New-ScheduledTaskTrigger -AtLogOn
        Write-Host "⏰ Backup programmé à la connexion utilisateur" -ForegroundColor Green
    }
}

# Paramètres de la tâche
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType InteractiveOrPassword -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 10)

# Enregistrer la tâche
try {
    Register-ScheduledTask `
        -TaskName $taskName `
        -Action $action `
        -Trigger $trigger `
        -Principal $principal `
        -Settings $settings `
        -Description "Sauvegarde automatique des conversations Claude Code vers GitHub" | Out-Null

    Write-Host "`n✅ Tâche planifiée créée avec succès!" -ForegroundColor Green

    # Afficher les informations
    Write-Host "`n============================================" -ForegroundColor Magenta
    Write-Host "  Configuration terminée" -ForegroundColor Magenta
    Write-Host "============================================`n" -ForegroundColor Magenta

    Write-Host "📋 Nom de la tâche: $taskName" -ForegroundColor White
    Write-Host "📂 Backup vers: $BackupPath" -ForegroundColor White
    Write-Host "⏱️  Fréquence: $Frequency" -ForegroundColor White

    Write-Host "`n🔧 Gestion de la tâche:" -ForegroundColor Cyan
    Write-Host "   • Voir la tâche:      taskschd.msc" -ForegroundColor Yellow
    Write-Host "   • Tester maintenant:  " -NoNewline -ForegroundColor Yellow
    Write-Host "Start-ScheduledTask -TaskName '$taskName'" -ForegroundColor White
    Write-Host "   • Désactiver:         " -NoNewline -ForegroundColor Yellow
    Write-Host "Disable-ScheduledTask -TaskName '$taskName'" -ForegroundColor White
    Write-Host "   • Supprimer:          " -NoNewline -ForegroundColor Yellow
    Write-Host "Unregister-ScheduledTask -TaskName '$taskName'" -ForegroundColor White

    Write-Host "`n💡 Pour tester immédiatement:" -ForegroundColor Cyan
    $testNow = Read-Host "Voulez-vous exécuter un backup maintenant pour tester? (O/N)"

    if ($testNow -eq "O" -or $testNow -eq "o") {
        Write-Host "`n🚀 Lancement du backup de test...`n" -ForegroundColor Green
        Start-ScheduledTask -TaskName $taskName
        Start-Sleep -Seconds 2

        # Vérifier le résultat
        $task = Get-ScheduledTask -TaskName $taskName
        $taskInfo = Get-ScheduledTaskInfo -TaskName $taskName

        Write-Host "`n📊 Résultat de la dernière exécution:" -ForegroundColor Cyan
        Write-Host "   • Dernière exécution: $($taskInfo.LastRunTime)" -ForegroundColor White
        Write-Host "   • Code de sortie: $($taskInfo.LastTaskResult)" -ForegroundColor White

        if ($taskInfo.LastTaskResult -eq 0) {
            Write-Host "`n✅ Test réussi! La sauvegarde automatique est opérationnelle." -ForegroundColor Green
        } else {
            Write-Host "`n⚠️  Le test a échoué. Vérifiez les logs dans l'Observateur d'événements." -ForegroundColor Yellow
        }
    }

} catch {
    Write-Host "`n❌ Erreur lors de la création de la tâche:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

Write-Host "`n"
