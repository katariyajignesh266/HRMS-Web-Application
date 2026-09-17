param(
    [Parameter(Mandatory = $true)]
    [string]$BackupDirectory,
    [string]$TargetSite = "hrms.restore.localhost"
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$dbRootPassword = if ($env:MARIADB_ROOT_PASSWORD) { $env:MARIADB_ROOT_PASSWORD } else { "123" }
$adminPassword = if ($env:FRAPPE_ADMIN_PASSWORD) { $env:FRAPPE_ADMIN_PASSWORD } else { "admin" }
$backupPath = (Resolve-Path $BackupDirectory).Path
$sqlFile = Get-ChildItem $backupPath -File | Where-Object { $_.Name -match '\.(sql|sql\.gz)$' } | Select-Object -First 1
$publicFile = Get-ChildItem $backupPath -File | Where-Object { $_.Name -match '(?<!private)-files\.tgz$' } | Select-Object -First 1
$privateFile = Get-ChildItem $backupPath -File | Where-Object { $_.Name -match '-private-files\.tgz$' } | Select-Object -First 1

if (-not $sqlFile) { throw "No SQL backup found in $backupPath" }
if ($TargetSite -eq "hrms.localhost") { throw "Use a disposable target site for restore validation, not the development site." }

$composeArgs = @("compose", "-f", (Join-Path $repoRoot "docker/docker-compose.yml"))
if (Test-Path (Join-Path $repoRoot ".env")) { $composeArgs += @("--env-file", (Join-Path $repoRoot ".env")) }
$containerBackup = "/tmp/$($sqlFile.Name)"
& docker @composeArgs cp $sqlFile.FullName "frappe:$containerBackup"
$siteExists = & docker @composeArgs exec -T frappe bash -lc "test -d '/home/frappe/frappe-bench/sites/$TargetSite'"
if ($LASTEXITCODE -eq 0) { throw "Target site already exists; refusing overwrite: $TargetSite" }
$createSite = "cd /home/frappe/frappe-bench; runuser -u frappe -- env PYTHONPATH=/home/frappe/.bench:/home/frappe/.local/lib/python3.14/site-packages:/home/frappe/frappe-bench/apps /home/frappe/.local/bin/bench new-site '$TargetSite' --mariadb-root-password '$dbRootPassword' --admin-password '$adminPassword' --no-mariadb-socket"
& docker @composeArgs exec -T frappe bash -lc $createSite
if ($LASTEXITCODE -ne 0) { throw "Could not create disposable restore site: $TargetSite" }
$fileArgs = ""
if ($publicFile) { & docker @composeArgs cp $publicFile.FullName "frappe:/tmp/$($publicFile.Name)"; $fileArgs += " --with-public-files '/tmp/$($publicFile.Name)'" }
if ($privateFile) { & docker @composeArgs cp $privateFile.FullName "frappe:/tmp/$($privateFile.Name)"; $fileArgs += " --with-private-files '/tmp/$($privateFile.Name)'" }

& docker @composeArgs exec -T frappe bash -lc "cd /home/frappe/frappe-bench; runuser -u frappe -- env PYTHONPATH=/home/frappe/.bench:/home/frappe/.local/lib/python3.14/site-packages:/home/frappe/frappe-bench/apps /home/frappe/.local/bin/bench --site '$TargetSite' restore '$containerBackup' --db-root-password '$dbRootPassword' --admin-password '$adminPassword' --install-app hrms --non-interactive $fileArgs"
if ($LASTEXITCODE -ne 0) { throw "Restore failed for disposable site: $TargetSite" }
Write-Output "Restore completed into disposable site $TargetSite"