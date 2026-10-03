<#
Runs the model lab as its own process: it keeps going if the terminal or the
Claude session closes, and resumes from .cache/model_lab if it is ever killed.

Uso:
    .\scripts\model_lab_background.ps1            # run all
    .\scripts\model_lab_background.ps1 promoted   # one experiment

Progress: .cache\model_lab\run.log · results: .cache\model_lab\results.json
#>
param([string[]]$Experiments = @("all"))

$Root = Split-Path -Parent $PSScriptRoot
$Cache = Join-Path $Root ".cache\model_lab"
New-Item -ItemType Directory -Force $Cache | Out-Null
$Arguments = @("run", "python", "scripts/model_lab.py", "run") + $Experiments
Start-Process -WindowStyle Hidden -WorkingDirectory $Root -FilePath "uv" -ArgumentList $Arguments `
    -RedirectStandardOutput (Join-Path $Cache "run.log") -RedirectStandardError (Join-Path $Cache "run.err")
Write-Output "Model lab running in the background. Log: $Cache\run.log"
