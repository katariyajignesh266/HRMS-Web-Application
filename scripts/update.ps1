param(
    [switch]$Pull
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = if (Test-Path (Join-Path $scriptDir "docker-compose.yml")) { $scriptDir } else { Split-Path -Parent $scriptDir }
$envPath = Join-Path $repoRoot ".env"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "                 HRMS Safe Update                         " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

if ($Pull) {
    if (Get-Command git -ErrorAction SilentlyContinue) {
        Write-Host "Pulling latest git changes..." -ForegroundColor Yellow
        git pull
    } else {
        Write-Warning "git command not found; skipping git pull."
    }
}

Write-Host "Updating containers (rebuilding changed configurations)..." -ForegroundColor Yellow
$composeArgs = @("compose", "-f", (Join-Path $repoRoot "docker-compose.yml"))
if (Test-Path $envPath) { $composeArgs += @("--env-file", $envPath) }

& docker @composeArgs up -d --build
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to update containers."
    exit 1
}

# Run migrations safely
$siteName = "hrms.localhost"
if (Test-Path $envPath) {
    Get-Content $envPath | ForEach-Object {
        if ($_ -match "^\s*FRAPPE_SITE_NAME\s*=\s*(\S+)") { $siteName = $matches[1] }
    }
}

Write-Host "Applying database migrations and patches safely..." -ForegroundColor Yellow
$frappeContainer = docker ps -q --filter "name=frappe"
if ($frappeContainer) {
    docker exec $frappeContainer bash -lc "cd /home/frappe/frappe-bench && runuser -u frappe -- /home/frappe/.local/bin/bench --site '$siteName' migrate --skip-failing"
}

Write-Host "`nUpdate complete! Verifying status..." -ForegroundColor Green
& (Join-Path $repoRoot "status.ps1")
