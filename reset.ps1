param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = if (Test-Path (Join-Path $scriptDir "docker-compose.yml")) { $scriptDir } else { Split-Path -Parent $scriptDir }
$envPath = Join-Path $repoRoot ".env"

Write-Host "==========================================================" -ForegroundColor Red
Write-Host "           HRMS Complete Environment Reset                " -ForegroundColor Red
Write-Host "==========================================================" -ForegroundColor Red
Write-Host ""
Write-Host "CAUTION: This command will permanently delete all HRMS Docker" -ForegroundColor Red
Write-Host "containers and persistent volumes (mariadb-data, frappe-bench)." -ForegroundColor Red
Write-Host "Any non-backed-up data created after the last seed backup will be lost." -ForegroundColor Yellow
Write-Host ""

if (-not $Force) {
    $confirm = Read-Host "Type 'RESET' to permanently delete containers and volumes"
    if ($confirm -ne "RESET") {
        Write-Host "Reset canceled by user." -ForegroundColor Gray
        exit 0
    }
}

Write-Host "`nStopping containers and deleting volumes..." -ForegroundColor Yellow
$composeArgs = @("compose", "-f", (Join-Path $repoRoot "docker-compose.yml"))
if (Test-Path $envPath) { $composeArgs += @("--env-file", $envPath) }
$composeArgs += @("down", "-v")

& docker @composeArgs

Write-Host "`n[✓] Environment reset successfully." -ForegroundColor Green
Write-Host "To recreate and bootstrap the environment with seed data, run:" -ForegroundColor White
Write-Host "  .\setup.ps1" -ForegroundColor Yellow

