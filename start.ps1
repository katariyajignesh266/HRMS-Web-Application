$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = if (Test-Path (Join-Path $scriptDir "docker-compose.yml")) { $scriptDir } else { Split-Path -Parent $scriptDir }
$envPath = Join-Path $repoRoot ".env"

Write-Host "Starting HRMS services..." -ForegroundColor Cyan

$composeArgs = @("compose", "-f", (Join-Path $repoRoot "docker-compose.yml"))
if (Test-Path $envPath) { $composeArgs += @("--env-file", $envPath) }
$composeArgs += @("up", "-d")

& docker @composeArgs
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to start HRMS services."
    exit 1
}

# Read configured port
$webPort = 8000
if (Test-Path $envPath) {
    Get-Content $envPath | ForEach-Object {
        if ($_ -match "^\s*HRMS_WEB_PORT\s*=\s*(\d+)") { $webPort = [int]$matches[1] }
    }
}

Write-Host -NoNewline "Verifying service availability" -ForegroundColor Yellow
$ready = $false
for ($i = 0; $i -lt 30; $i++) {
    try {
        $resp = Invoke-WebRequest -Uri "http://localhost:$webPort/api/method/frappe.ping" -UseBasicParsing -TimeoutSec 3 -ErrorAction SilentlyContinue
        if ($resp.StatusCode -eq 200) {
            $ready = $true
            break
        }
    } catch {}
    Write-Host -NoNewline "." -ForegroundColor Yellow
    Start-Sleep -Seconds 2
}
Write-Host ""

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "                 HRMS IS RUNNING                          " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  MAIN HRMS APPLICATION URL:" -ForegroundColor Yellow
Write-Host "  http://localhost:$webPort/hrms" -ForegroundColor White
Write-Host ""
Write-Host "  Frappe Desk / Admin Portal:" -ForegroundColor Yellow
Write-Host "  http://localhost:$webPort/app" -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Cyan

