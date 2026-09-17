param(
    [string]$Service,
    [int]$Tail = 100,
    [switch]$Follow
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = if (Test-Path (Join-Path $scriptDir "docker-compose.yml")) { $scriptDir } else { Split-Path -Parent $scriptDir }
$envPath = Join-Path $repoRoot ".env"

$composeArgs = @("compose", "-f", (Join-Path $repoRoot "docker-compose.yml"))
if (Test-Path $envPath) { $composeArgs += @("--env-file", $envPath) }
$composeArgs += @("logs", "--tail", $Tail)
if ($Follow) { $composeArgs += @("-f") }
if ($Service) { $composeArgs += @($Service) }

& docker @composeArgs
