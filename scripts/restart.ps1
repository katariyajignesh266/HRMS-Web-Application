$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = if (Test-Path (Join-Path $scriptDir "docker-compose.yml")) { $scriptDir } else { Split-Path -Parent $scriptDir }

Write-Host "Restarting HRMS services..." -ForegroundColor Cyan
& (Join-Path $repoRoot "stop.ps1")
& (Join-Path $repoRoot "start.ps1")
