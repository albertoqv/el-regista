<#
Instala la sincronización con Transfermarkt desde este PC (una sola vez).

    .\scripts\home_sync_install.ps1

Pide la clave de ingesta sin mostrarla, la guarda como variable de usuario y crea la
tarea programada "El Regista - Transfermarkt": martes y viernes a las 21:00 y, si el
PC estaba apagado a esa hora, en cuanto se encienda. Para quitarla:
    Unregister-ScheduledTask -TaskName "El Regista - Transfermarkt" -Confirm:$false
#>
$secure = Read-Host "Clave de ingesta (INGESTION_API_KEY)" -AsSecureString
$key = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure))
if (-not $key) { Write-Error "Sin clave no se instala nada."; exit 1 }
[Environment]::SetEnvironmentVariable("INGESTION_API_KEY", $key, "User")

$script = Join-Path $PSScriptRoot "home_sync.ps1"
$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$script`""
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Tuesday, Friday -At 21:00
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Hours 2)
Register-ScheduledTask -TaskName "El Regista - Transfermarkt" -Action $action `
    -Trigger $trigger -Settings $settings -Force | Out-Null
Write-Output "Instalado. Primera ejecución ahora mismo..."
Start-ScheduledTask -TaskName "El Regista - Transfermarkt"
Write-Output "En marcha. Registro: .cache\home-sync.log"
