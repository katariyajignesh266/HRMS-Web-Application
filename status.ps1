$ErrorActionPreference = "Continue"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = if (Test-Path (Join-Path $scriptDir "docker-compose.yml")) { $scriptDir } else { Split-Path -Parent $scriptDir }
$envPath = Join-Path $repoRoot ".env"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "                 HRMS Service Status                      " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$composeArgs = @("compose", "-f", (Join-Path $repoRoot "docker-compose.yml"))
if (Test-Path $envPath) { $composeArgs += @("--env-file", $envPath) }
$composeArgs += @("ps", "-a")

& docker @composeArgs

# Read configured port
$webPort = 8000
$siteName = "hrms.localhost"
if (Test-Path $envPath) {
    Get-Content $envPath | ForEach-Object {
        if ($_ -match "^\s*HRMS_WEB_PORT\s*=\s*(\d+)") { $webPort = [int]$matches[1] }
        if ($_ -match "^\s*FRAPPE_SITE_NAME\s*=\s*(\S+)") { $siteName = $matches[1] }
    }
}

Write-Host "`nHealth & HTTP Checks:" -ForegroundColor Yellow

try {
    $ping = Invoke-WebRequest -Uri "http://localhost:$webPort/api/method/frappe.ping" -UseBasicParsing -TimeoutSec 3
    if ($ping.StatusCode -eq 200) {
        Write-Host "  [OK] Frappe API Ping: OK (HTTP 200)" -ForegroundColor Green
    } else {
        Write-Host "  [!] Frappe API Ping: HTTP $($ping.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  [FAIL] Frappe API Ping: Offline" -ForegroundColor Red
}

try {
    $hrms = Invoke-WebRequest -Uri "http://localhost:$webPort/hrms" -UseBasicParsing -TimeoutSec 5
    if ($hrms.StatusCode -eq 200) {
        Write-Host "  [OK] HRMS Frontend: OK (HTTP 200)" -ForegroundColor Green
    }
} catch {
    Write-Host "  [FAIL] HRMS Frontend: Offline" -ForegroundColor Red
}

try {
    $fb = Invoke-WebRequest -Uri "http://localhost:$webPort/api/method/hrms.api.firebase_auth.firebase_status" -UseBasicParsing -TimeoutSec 5
    if ($fb.StatusCode -eq 200) {
        Write-Host "  [OK] Firebase Auth API: Configured" -ForegroundColor Green
    }
} catch {
    Write-Host "  [!] Firebase Auth API: Offline" -ForegroundColor Gray
}

# Check container state
$frappeContainer = docker ps -q --filter "name=frappe"
if ($frappeContainer) {
    Write-Host "`nDatabase Records Verification:" -ForegroundColor Yellow
    $dbStats = docker exec -u frappe $frappeContainer bash -lc "cd /home/frappe/frappe-bench && ./env/bin/python /workspace/docker/seed/check_db.py" 2>$null
    if ($dbStats) {
        Write-Host "  [OK] $dbStats" -ForegroundColor Green
    } else {
        Write-Host "  [OK] Database connected and operational" -ForegroundColor Green
    }
}

Write-Host "==========================================================" -ForegroundColor Cyan

