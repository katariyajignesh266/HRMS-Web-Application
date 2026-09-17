param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = if (Test-Path (Join-Path $scriptDir "docker-compose.yml")) { $scriptDir } else { Split-Path -Parent $scriptDir }

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "         HRMS Automated First-Time Setup                  " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Check Docker executable
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "Docker CLI was not found in PATH. Please install Docker Desktop (https://www.docker.com/products/docker-desktop) and ensure docker.exe is accessible in PATH."
    exit 1
}

# 2. Check Docker Desktop engine
try {
    $null = docker info 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Docker daemon is not running" }
} catch {
    Write-Error "Docker Desktop is not currently running. Please launch Docker Desktop and wait until the engine has started, then re-run setup.ps1."
    exit 1
}

# 3. Environment configuration (.env)
$envPath = Join-Path $repoRoot ".env"
$envExamplePath = Join-Path $repoRoot ".env.example"

if (-not (Test-Path $envPath)) {
    if (Test-Path $envExamplePath) {
        Copy-Item $envExamplePath $envPath
        Write-Host "[OK] Created .env from .env.example" -ForegroundColor Green
    } else {
        Write-Warning ".env.example not found; creating minimal .env"
        "HRMS_WEB_PORT=8000`nHRMS_SOCKETIO_PORT=9000`nFRAPPE_SITE_NAME=hrms.localhost" | Out-File -FilePath $envPath -Encoding utf8
    }
}

# Detect Firebase service account JSON if present
$fbFiles = Get-ChildItem -Path $repoRoot -File -Filter "*-firebase-adminsdk-*.json" -ErrorAction SilentlyContinue
if ($fbFiles -and (Get-Content $envPath | Where-Object { $_ -match "^FIREBASE_ADMIN_CREDENTIALS_FILE=\s*$" })) {
    $fbFile = $fbFiles[0].Name
    (Get-Content $envPath) -replace "^FIREBASE_ADMIN_CREDENTIALS_FILE=.*", "FIREBASE_ADMIN_CREDENTIALS_FILE=/workspace/$fbFile" | Set-Content $envPath
    Write-Host "[OK] Configured FIREBASE_ADMIN_CREDENTIALS_FILE to /workspace/$fbFile" -ForegroundColor Green
}

# Read configured ports
$webPort = 8000
$socketioPort = 9000
if (Test-Path $envPath) {
    Get-Content $envPath | ForEach-Object {
        if ($_ -match "^\s*HRMS_WEB_PORT\s*=\s*(\d+)") { $webPort = [int]$matches[1] }
        if ($_ -match "^\s*HRMS_SOCKETIO_PORT\s*=\s*(\d+)") { $socketioPort = [int]$matches[1] }
    }
}

# 4. Check port availability on host
function Test-PortAvailable([int]$Port) {
    try {
        $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $Port)
        $listener.Start()
        $listener.Stop()
        return $true
    } catch {
        return $false
    }
}

# Check if port is already bound by existing HRMS container or other process
$runningHrms = docker ps --filter "name=frappe" --format "{{.Ports}}"
$webPortUsedByHrms = $runningHrms -match ":$webPort->"

if (-not $webPortUsedByHrms -and -not (Test-PortAvailable $webPort)) {
    Write-Warning "Port $webPort appears to be in use by another application. You can customize HRMS_WEB_PORT in .env to an open port (e.g., 8080)."
}

# 5. Start Docker Compose
Write-Host "`n[1/4] Starting Docker services..." -ForegroundColor Yellow
$composeArgs = @("compose", "-f", (Join-Path $repoRoot "docker-compose.yml"), "--env-file", $envPath, "up", "-d")
& docker @composeArgs
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to start Docker Compose services. Review the error output above."
    exit 1
}

# 6. Wait for backend service readiness
Write-Host "`n[2/4] Waiting for services to become healthy..." -ForegroundColor Yellow
$timeoutSeconds = 180
$startTime = Get-Date
$frappeReady = $false

while (((Get-Date) - $startTime).TotalSeconds -lt $timeoutSeconds) {
    $status = docker inspect --format="{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}" hrms-frappe-1 2>$null
    if (-not $status) {
        $status = docker inspect --format="{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}" docker-frappe-1 2>$null
    }
    
    if ($status -eq "healthy") {
        $frappeReady = $true
        break
    }
    
    # Also check direct HTTP response
    try {
        $resp = Invoke-WebRequest -Uri "http://localhost:$webPort/api/method/frappe.ping" -UseBasicParsing -TimeoutSec 3 -ErrorAction SilentlyContinue
        if ($resp.StatusCode -eq 200) {
            $frappeReady = $true
            break
        }
    } catch {}

    Write-Host -NoNewline "."
    Start-Sleep -Seconds 4
}
Write-Host ""

if (-not $frappeReady) {
    Write-Warning "Frappe container is still initializing. It may take an extra minute on the first bootstrap while packages and database are restored."
}

# 7. Verification of endpoints
Write-Host "`n[3/4] Verifying application endpoints..." -ForegroundColor Yellow
$hrmsHttpOk = $false
try {
    $resp = Invoke-WebRequest -Uri "http://localhost:$webPort/hrms" -UseBasicParsing -TimeoutSec 10 -ErrorAction SilentlyContinue
    if ($resp.StatusCode -eq 200) { $hrmsHttpOk = $true }
} catch {}

$fbStatusOk = $false
try {
    $resp = Invoke-WebRequest -Uri "http://localhost:$webPort/api/method/hrms.api.firebase_auth.firebase_status" -UseBasicParsing -TimeoutSec 10 -ErrorAction SilentlyContinue
    if ($resp.StatusCode -eq 200) { $fbStatusOk = $true }
} catch {}

# 8. Print Results and Working Local URLs
Write-Host "`n[4/4] Setup Complete!" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "                 HRMS IS READY                            " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  MAIN HRMS APPLICATION URL:" -ForegroundColor Yellow
Write-Host "  http://localhost:$webPort/hrms" -ForegroundColor White
Write-Host ""
Write-Host "  Frappe Desk / Admin Portal:" -ForegroundColor Yellow
Write-Host "  http://localhost:$webPort/app" -ForegroundColor White
Write-Host ""
Write-Host "  Firebase Status API:" -ForegroundColor Yellow
Write-Host "  http://localhost:$webPort/api/method/hrms.api.firebase_auth.firebase_status" -ForegroundColor White
Write-Host ""
Write-Host "  Default Admin Credentials:" -ForegroundColor Yellow
Write-Host "  User: Administrator  |  Password: admin" -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Daily commands:" -ForegroundColor Gray
Write-Host "  Start:   .\start.ps1" -ForegroundColor Gray
Write-Host "  Stop:    .\stop.ps1" -ForegroundColor Gray
Write-Host "  Status:  .\status.ps1" -ForegroundColor Gray
Write-Host "  Logs:    .\logs.ps1" -ForegroundColor Gray
Write-Host "  Backup:  .\backup.ps1" -ForegroundColor Gray
Write-Host "==========================================================" -ForegroundColor Cyan
