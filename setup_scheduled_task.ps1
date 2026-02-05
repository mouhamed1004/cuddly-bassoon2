# Script PowerShell pour configurer la tâche planifiée de synchronisation Shopify
# Exécuter en tant qu'administrateur

$TaskName = "BLIZZ-Shopify-Sync"
$TaskDescription = "Synchronisation automatique des prix Shopify pour BLIZZ"
$ScriptPath = "C:\Users\Mouhamed\Desktop\fuzzy-octo-robot-main\sync_shopify_task.bat"
$LogPath = "C:\Users\Mouhamed\Desktop\fuzzy-octo-robot-main\sync_shopify.log"

# Vérifier si la tâche existe déjà
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if ($ExistingTask) {
    Write-Host "Suppression de la tâche existante..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Créer l'action (exécuter le script)
$Action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$ScriptPath`""

# Créer le déclencheur (toutes les 15 minutes)
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 15) -RepetitionDuration (New-TimeSpan -Days 365)

# Créer les paramètres de la tâche
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable

# Créer le principal (utilisateur actuel)
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive

# Enregistrer la tâche
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Description $TaskDescription

Write-Host "Tâche planifiée '$TaskName' créée avec succès!" -ForegroundColor Green
Write-Host "La synchronisation s'exécutera toutes les 6 heures à partir de 9h00" -ForegroundColor Cyan
Write-Host "Logs disponibles dans: $LogPath" -ForegroundColor Cyan

# Tester la tâche immédiatement
Write-Host "Test de la tâche..." -ForegroundColor Yellow
Start-ScheduledTask -TaskName $TaskName

Write-Host "Configuration terminée!" -ForegroundColor Green
