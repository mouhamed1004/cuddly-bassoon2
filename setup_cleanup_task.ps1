# Script de configuration de tâche planifiée pour BLIZZ Game
# Nettoyage automatique des transactions abandonnées

$TaskName = "BLIZZ-Game-Cleanup-Transactions"
$ScriptPath = "C:\Users\Core\Downloads\fuzzy-octo-robot-main"
$PythonPath = "C:\Users\Core\AppData\Local\Programs\Python\Python313\python.exe"

# Supprimer la tâche existante si elle existe
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Ancienne tache supprimee"
}

# Créer l'action
$Action = New-ScheduledTaskAction -Execute $PythonPath -Argument "manage.py cleanup_expired_transactions --timeout-minutes=30" -WorkingDirectory $ScriptPath

# Créer le déclencheur (toutes les 10 minutes)
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 10)

# Créer les paramètres
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# Créer la tâche
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "Nettoie automatiquement les transactions abandonnées de BLIZZ Game toutes les 10 minutes"

Write-Host "Tache planifiee creee: $TaskName"
Write-Host "La tache s'executera toutes les 10 minutes"
Write-Host "Verifiez dans le Planificateur de taches Windows"
