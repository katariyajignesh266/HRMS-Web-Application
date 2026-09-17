param(
    [switch]$Seed
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$siteName = if ($env:FRAPPE_SITE_NAME) { $env:FRAPPE_SITE_NAME } else { "hrms.localhost" }
$backupRoot = Join-Path $repoRoot ".backups"
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupDir = Join-Path $backupRoot "$siteName-$timestamp"
$composeArgs = @("compose", "-f", (Join-Path $repoRoot "docker/docker-compose.yml"))
if (Test-Path (Join-Path $repoRoot ".env")) { $composeArgs += @("--env-file", (Join-Path $repoRoot ".env")) }

New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
& docker @composeArgs exec -T frappe bash -lc "cd /home/frappe/frappe-bench && runuser -u frappe -- env PYTHONPATH=/home/frappe/.bench:/home/frappe/.local/lib/python3.14/site-packages:/home/frappe/frappe-bench/apps /home/frappe/.local/bin/bench --site '$siteName' backup --with-files --compress"
& docker @composeArgs cp "frappe:/home/frappe/frappe-bench/sites/$siteName/private/backups/." $backupDir
Write-Output "Backup created at $backupDir"

if ($Seed) {
    $seedRoot = Join-Path $repoRoot "docker/seed"
    $seedDir = Join-Path $seedRoot "$siteName-$timestamp"
    New-Item -ItemType Directory -Force -Path $seedDir | Out-Null
    Copy-Item -Path (Join-Path $backupDir "*") -Destination $seedDir -Force
    Write-Output "Seed backup copied to $seedDir"
    Write-Output "Review this folder before committing. Do not commit real employee data or secrets."
}
