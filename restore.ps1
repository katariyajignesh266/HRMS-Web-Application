param(
    [string]$BackupDir,
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = if (Test-Path (Join-Path $scriptDir "docker-compose.yml")) { $scriptDir } else { Split-Path -Parent $scriptDir }
$envPath = Join-Path $repoRoot ".env"

$siteName = "hrms.localhost"
$dbRootPassword = "123"
$adminPassword = "admin"

if (Test-Path $envPath) {
    Get-Content $envPath | ForEach-Object {
        if ($_ -match "^\s*FRAPPE_SITE_NAME\s*=\s*(\S+)") { $siteName = $matches[1] }
        if ($_ -match "^\s*MARIADB_ROOT_PASSWORD\s*=\s*(\S+)") { $dbRootPassword = $matches[1] }
        if ($_ -match "^\s*FRAPPE_ADMIN_PASSWORD\s*=\s*(\S+)") { $adminPassword = $matches[1] }
    }
}

# If no backup dir specified, find the newest in backups/seed or .backups
if (-not $BackupDir) {
    $candidates = @()
    if (Test-Path (Join-Path $repoRoot "backups/seed")) { $candidates += (Join-Path $repoRoot "backups/seed") }
    if (Test-Path (Join-Path $repoRoot ".backups")) {
        $subdirs = Get-ChildItem (Join-Path $repoRoot ".backups") -Directory | Sort-Object LastWriteTime -Descending
        if ($subdirs) { $candidates += $subdirs[0].FullName }
    }
    
    foreach ($cand in $candidates) {
        if (Get-ChildItem $cand -File | Where-Object { $_.Name -match '\.(sql|sql\.gz)$' }) {
            $BackupDir = $cand
            break
        }
    }
}

if (-not $BackupDir -or -not (Test-Path $BackupDir)) {
    Write-Error "No backup directory specified or found. Provide a path with -BackupDir <path>."
    exit 1
}

$sqlFile = Get-ChildItem $BackupDir -File | Where-Object { $_.Name -match '\.(sql|sql\.gz)$' } | Select-Object -First 1
$publicFile = Get-ChildItem $BackupDir -File | Where-Object { $_.Name -match '(?<!private)-files\.tgz$' } | Select-Object -First 1
$privateFile = Get-ChildItem $BackupDir -File | Where-Object { $_.Name -match '-private-files\.tgz$' } | Select-Object -First 1

if (-not $sqlFile) {
    Write-Error "No SQL dump (.sql or .sql.gz) found in $BackupDir."
    exit 1
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "                 HRMS Database Restore                    " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Backup source: $BackupDir" -ForegroundColor Yellow
Write-Host "SQL dump:      $($sqlFile.Name)" -ForegroundColor Yellow
Write-Host "Target site:   $siteName" -ForegroundColor Yellow
Write-Host ""

if (-not $Force) {
    Write-Host "WARNING: This will overwrite the existing database for '$siteName'!" -ForegroundColor Red
    $confirmation = Read-Host "Type 'YES' to proceed with restore"
    if ($confirmation -ne "YES") {
        Write-Host "Restore canceled by user." -ForegroundColor Gray
        exit 0
    }
}

$frappeContainer = docker ps -q --filter "name=frappe"
if (-not $frappeContainer) {
    Write-Error "HRMS frappe container is not running. Start services first with .\start.ps1."
    exit 1
}

Write-Host "Copying backup files to container..." -ForegroundColor Cyan
docker cp $sqlFile.FullName "$($frappeContainer):/tmp/$($sqlFile.Name)"
$fileArgs = ""
if ($publicFile) {
    docker cp $publicFile.FullName "$($frappeContainer):/tmp/$($publicFile.Name)"
    $fileArgs += " --with-public-files '/tmp/$($publicFile.Name)'"
}
if ($privateFile) {
    docker cp $privateFile.FullName "$($frappeContainer):/tmp/$($privateFile.Name)"
    $fileArgs += " --with-private-files '/tmp/$($privateFile.Name)'"
}

Write-Host "Executing site restore inside container..." -ForegroundColor Cyan
$restoreCmd = "cd /home/frappe/frappe-bench && runuser -u frappe -- /home/frappe/.local/bin/bench --site '$siteName' restore '/tmp/$($sqlFile.Name)' --db-root-password '$dbRootPassword' --admin-password '$adminPassword' --install-app hrms --non-interactive $fileArgs"
docker exec $frappeContainer bash -lc $restoreCmd

Write-Host "Running migrations on restored site..." -ForegroundColor Cyan
docker exec $frappeContainer bash -lc "cd /home/frappe/frappe-bench && runuser -u frappe -- /home/frappe/.local/bin/bench --site '$siteName' migrate --skip-failing"

Write-Host "`n[OK] Restore completed successfully!" -ForegroundColor Green
& (Join-Path $repoRoot "status.ps1")
