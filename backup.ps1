param(
    [switch]$Seed
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = if (Test-Path (Join-Path $scriptDir "docker-compose.yml")) { $scriptDir } else { Split-Path -Parent $scriptDir }
$envPath = Join-Path $repoRoot ".env"

$siteName = "hrms.localhost"
if (Test-Path $envPath) {
    Get-Content $envPath | ForEach-Object {
        if ($_ -match "^\s*FRAPPE_SITE_NAME\s*=\s*(\S+)") { $siteName = $matches[1] }
    }
}

$backupRoot = Join-Path $repoRoot ".backups"
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupDir = Join-Path $backupRoot "$siteName-$timestamp"

$frappeContainer = docker ps -q --filter "name=frappe"
if (-not $frappeContainer) {
    Write-Error "HRMS frappe container is not running. Please run .\start.ps1 before creating a backup."
    exit 1
}

Write-Host "Creating backup for site '$siteName' inside container..." -ForegroundColor Cyan
docker exec $frappeContainer bash -lc "cd /home/frappe/frappe-bench && runuser -u frappe -- /home/frappe/.local/bin/bench --site '$siteName' backup --with-files --compress"
if ($LASTEXITCODE -ne 0) {
    Write-Error "Backup command failed inside container."
    exit 1
}

New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
docker cp "$($frappeContainer):/home/frappe/frappe-bench/sites/$siteName/private/backups/." $backupDir

Write-Host "`n[OK] Backup created successfully at:" -ForegroundColor Green
Write-Host "    $backupDir" -ForegroundColor White

if ($Seed) {
    $seedDir = Join-Path $repoRoot "backups/seed"
    New-Item -ItemType Directory -Force -Path $seedDir | Out-Null
    
    # Remove old sql and files from seed before copying newest
    Remove-Item (Join-Path $seedDir "*") -Force -Recurse -ErrorAction SilentlyContinue
    Copy-Item -Path (Join-Path $backupDir "*") -Destination $seedDir -Force
    
    # Also update docker/seed for backwards compatibility
    $dockerSeed = Join-Path $repoRoot "docker/seed/$siteName-$timestamp"
    New-Item -ItemType Directory -Force -Path $dockerSeed | Out-Null
    Copy-Item -Path (Join-Path $backupDir "*") -Destination $dockerSeed -Force

    Write-Host "`n[OK] Portable seed updated at:" -ForegroundColor Green
    Write-Host "    $seedDir" -ForegroundColor White
    Write-Host "    This seed will be used by any fresh machine during setup.ps1." -ForegroundColor Gray
}
