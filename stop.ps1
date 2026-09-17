$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = if (Test-Path (Join-Path $scriptDir "docker-compose.yml")) { $scriptDir } else { Split-Path -Parent $scriptDir }
$envPath = Join-Path $repoRoot ".env"

Write-Host "Stopping HRMS services (preserving all database and application data)..." -ForegroundColor Yellow

$composeArgs = @("compose", "-f", (Join-Path $repoRoot "docker-compose.yml"))
if (Test-Path $envPath) { $composeArgs += @("--env-file", $envPath) }
$composeArgs += @("stop")

& docker @composeArgs
Write-Host "HRMS services stopped successfully. Database and files are safely preserved in persistent volumes." -ForegroundColor Green

