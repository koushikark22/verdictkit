<#
.SYNOPSIS
  One command that starts all of VerdictKit locally and prints one entry URL.

.DESCRIPTION
  1. Starts the Docker backend (enforced OS-user isolation, judge mode, disposable demonstration signer).
  2. Verifies it: health must report ENFORCED isolation, judge mode and contract 1.2.0.
  3. Builds the portal, Quote Autopsy and Reel Autopsy UIs if needed.
  4. Starts one local gateway so the whole product shares a single origin.

  Everything listens on 127.0.0.1 only. An occupied port is never freed: the next free port is used.
  Only the container and the gateway process that this script itself started are ever stopped.
  No secret is created or printed by this script; the vault key and the demonstration signing key are
  generated inside the container and never leave it.

.PARAMETER ApiPort      Preferred host port for the backend (default 8000; the next free port is used if taken).
.PARAMETER GatewayPort  Preferred port for the entry URL (default 5170; the next free port is used if taken).
.PARAMETER Image        Docker image to run (default verdictkit:batch2).
.PARAMETER Rebuild      Rebuild the Docker image and the UIs first.
.PARAMETER NoBrowser    Do not open the browser.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts\Start-VerdictKit.ps1
#>
[CmdletBinding()]
param(
    [int]$ApiPort = 8000,
    [int]$GatewayPort = 5170,
    [string]$Image = 'verdictkit:batch2',
    [switch]$Rebuild,
    [switch]$NoBrowser
)

$ErrorActionPreference = 'Stop'
$Repo = Split-Path -Parent $PSScriptRoot
$RunDir = Join-Path $Repo '.verdictkit-run'
$StateFile = Join-Path $RunDir 'state.json'
$ContainerName = 'vk-batch2-backend'
$ManagedLabel = 'com.verdictkit.managed=1'
$ExpectedContract = '1.2.0'

function Write-Step([string]$Text) { Write-Host ('==> ' + $Text) -ForegroundColor Cyan }
function Write-Ok([string]$Text)   { Write-Host ('    ok  ' + $Text) -ForegroundColor Green }
function Write-Note([string]$Text) { Write-Host ('    ' + $Text) -ForegroundColor Yellow }
function Stop-WithError([string]$Text) { Write-Host ('FAILED: ' + $Text) -ForegroundColor Red; exit 1 }

# Run a native command without PowerShell turning its stderr into a terminating error.
function Invoke-Native([string]$Exe, [string[]]$Arguments) {
    $previous = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try { $output = & $Exe @Arguments 2>&1 | ForEach-Object { $_.ToString() }; $code = $LASTEXITCODE }
    finally { $ErrorActionPreference = $previous }
    return [pscustomobject]@{ Output = @($output); Code = $code }
}

function Test-PortFree([int]$Port) {
    if (Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue) { return $false }
    try {
        $listener = New-Object System.Net.Sockets.TcpListener([System.Net.IPAddress]::Loopback, $Port)
        $listener.Start(); $listener.Stop(); return $true
    } catch { return $false }
}

function Find-FreePort([int]$Preferred, [int[]]$Avoid = @()) {
    for ($p = $Preferred; $p -lt ($Preferred + 40); $p++) {
        if (($Avoid -notcontains $p) -and (Test-PortFree $p)) { return $p }
    }
    Stop-WithError ('no free port from ' + $Preferred + ' to ' + ($Preferred + 39))
}

function Get-OwnGatewayProcess($State) {
    # Only a process whose command line is this repository's gateway counts as ours.
    if (-not $State -or -not $State.gatewayPid) { return $null }
    $proc = Get-CimInstance Win32_Process -Filter ('ProcessId=' + [int]$State.gatewayPid) -ErrorAction SilentlyContinue
    if ($proc -and $proc.CommandLine -like '*gateway.mjs*' -and $proc.CommandLine -like ('*' + $Repo + '*')) { return $proc }
    return $null
}

Write-Host ''
Write-Host 'VerdictKit - Don''t trust the claim. Verify the evidence. Reproduce the verdict.' -ForegroundColor White
Write-Host ''

# ---- 1. preflight ---------------------------------------------------------------------------
Write-Step 'Checking prerequisites'
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { Stop-WithError 'Docker is not installed or not on PATH.' }
$info = Invoke-Native 'docker' @('info', '--format', '{{.ServerVersion}}')
if ($info.Code -ne 0) { Stop-WithError 'The Docker daemon is not running. Start Docker Desktop and run this script again.' }
Write-Ok ('docker server ' + ($info.Output -join ' '))
if (-not (Get-Command node -ErrorAction SilentlyContinue)) { Stop-WithError 'Node.js 20 or newer is required to build and serve the UIs.' }
$nodeMajor = [int]((node --version).TrimStart('v').Split('.')[0])
if ($nodeMajor -lt 20) { Stop-WithError ('Node.js 20 or newer is required (found ' + (node --version) + ').') }
Write-Ok ('node ' + (node --version))

# ---- 2. stop only what this script started earlier --------------------------------------------
$State = $null
if (Test-Path $StateFile) { try { $State = Get-Content $StateFile -Raw | ConvertFrom-Json } catch { $State = $null } }
$oldGateway = Get-OwnGatewayProcess $State
if ($oldGateway) { Write-Note ('stopping the gateway this script started earlier (pid ' + $oldGateway.ProcessId + ')'); Stop-Process -Id $oldGateway.ProcessId -Force }
$existing = Invoke-Native 'docker' @('ps', '-a', '--filter', ('name=^/' + $ContainerName + '$'), '--format', '{{.ID}}')
if ($existing.Output.Count -gt 0 -and $existing.Output[0]) {
    $owned = Invoke-Native 'docker' @('ps', '-a', '--filter', ('name=^/' + $ContainerName + '$'), '--filter', ('label=' + $ManagedLabel), '--format', '{{.ID}}')
    if (-not ($owned.Output.Count -gt 0 -and $owned.Output[0])) {
        Stop-WithError ('a container named ' + $ContainerName + ' exists but was not started by VerdictKit; it was left untouched. Remove or rename it and retry.')
    }
    Write-Note ('replacing the VerdictKit backend container from the previous run (' + $ContainerName + ')')
    [void](Invoke-Native 'docker' @('rm', '-f', $ContainerName))
}

# ---- 3. ports -------------------------------------------------------------------------------
Write-Step 'Choosing ports (nothing that is already running is touched)'
$api = Find-FreePort $ApiPort
if ($api -ne $ApiPort) { Write-Note ('port ' + $ApiPort + ' is in use; the backend will use ' + $api) }
$gateway = Find-FreePort $GatewayPort @($api)
if ($gateway -ne $GatewayPort) { Write-Note ('port ' + $GatewayPort + ' is in use; the entry URL will use ' + $gateway) }
Write-Ok ('backend 127.0.0.1:' + $api + ', entry 127.0.0.1:' + $gateway)

# ---- 4. image -------------------------------------------------------------------------------
Write-Step ('Docker image ' + $Image)
$have = Invoke-Native 'docker' @('image', 'inspect', $Image, '--format', '{{.Id}}')
if ($Rebuild -or $have.Code -ne 0) {
    Write-Note 'building the image (first build takes a few minutes)'
    Push-Location $Repo
    try { $build = Invoke-Native 'docker' @('build', '-t', $Image, '.') } finally { Pop-Location }
    if ($build.Code -ne 0) { $build.Output | Select-Object -Last 25 | ForEach-Object { Write-Host $_ }; Stop-WithError 'docker build failed.' }
}
Write-Ok 'image ready'

# ---- 5. backend -----------------------------------------------------------------------------
Write-Step 'Starting the backend (enforced isolation, judge mode, demonstration signer)'
$run = Invoke-Native 'docker' @('run', '-d', '--name', $ContainerName, '--label', $ManagedLabel, '--label', 'com.verdictkit.role=demo-backend',
    '-p', ('127.0.0.1:' + $api + ':8000'), $Image, 'demo')
if ($run.Code -ne 0) { $run.Output | ForEach-Object { Write-Host $_ }; Stop-WithError 'docker run failed.' }

$health = $null
$deadline = (Get-Date).AddSeconds(90)
while ((Get-Date) -lt $deadline -and -not $health) {
    try { $health = Invoke-RestMethod -Uri ('http://127.0.0.1:' + $api + '/api/v1/health') -TimeoutSec 4 } catch { Start-Sleep -Milliseconds 800 }
}
if (-not $health) {
    (Invoke-Native 'docker' @('logs', '--tail', '40', $ContainerName)).Output | ForEach-Object { Write-Host $_ }
    [void](Invoke-Native 'docker' @('rm', '-f', $ContainerName))
    Stop-WithError 'the backend did not become healthy within 90 seconds (container removed).'
}
if ($health.status -ne 'ok' -or $health.contractVersion -ne $ExpectedContract) { Stop-WithError ('unexpected health response (contract ' + $health.contractVersion + ').') }
if ($health.isolationMode -ne 'ENFORCED' -or -not $health.judgeMode) {
    [void](Invoke-Native 'docker' @('rm', '-f', $ContainerName))
    Stop-WithError ('isolation is ' + $health.isolationMode + ' and judge mode is ' + $health.judgeMode + '; refusing to continue (container removed).')
}
Write-Ok ('health ok: contract ' + $health.contractVersion + ', isolation ' + $health.isolationMode + ', judge mode ' + $health.judgeMode)
$lab = $null
try { $lab = Invoke-RestMethod -Uri ('http://127.0.0.1:' + $api + '/api/v1/demo/status') -TimeoutSec 5 } catch { }
if (-not $lab -or -not $lab.enabled -or -not $lab.signer) { Stop-WithError 'the demonstration signer is not active on the backend.' }
Write-Ok ('demonstration signer active, public key id ' + $lab.signer.keyId.Substring(0, 16) + '... (private key stays in the container)')

# ---- 6. UIs ---------------------------------------------------------------------------------
Write-Step 'Preparing the web UIs'
$dists = @('ui\hub\dist', 'apps\quote-autopsy\web\dist', 'apps\reel-autopsy\web\dist') | ForEach-Object { Join-Path $Repo $_ }
$missing = @($dists | Where-Object { -not (Test-Path (Join-Path $_ 'index.html')) })
if ($Rebuild -or $missing.Count -gt 0) {
    Push-Location $Repo
    try {
        if (-not (Test-Path (Join-Path $Repo 'node_modules'))) {
            Write-Note 'installing npm dependencies (npm ci)'
            $ci = Invoke-Native 'npm' @('ci', '--no-audit', '--no-fund')
            if ($ci.Code -ne 0) { $ci.Output | Select-Object -Last 20 | ForEach-Object { Write-Host $_ }; Stop-WithError 'npm ci failed.' }
        }
        Write-Note 'building the portal, Quote Autopsy and Reel Autopsy'
        $b = Invoke-Native 'npm' @('run', 'build:portal')
        if ($b.Code -ne 0) { $b.Output | Select-Object -Last 25 | ForEach-Object { Write-Host $_ }; Stop-WithError 'the UI build failed.' }
    } finally { Pop-Location }
}
Write-Ok 'UIs built'

# ---- 7. gateway -----------------------------------------------------------------------------
Write-Step 'Starting the local gateway'
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null
$err = Join-Path $RunDir 'gateway.log'
if (Test-Path $err) { Remove-Item $err -Force }
# No handle is redirected here on purpose: a redirected child inherits the caller's output pipe and keeps it open
# after this script ends, which hangs any tool that waits for the script's output. The gateway logs to --log itself.
$gwArgs = @(('"' + (Join-Path $Repo 'scripts\gateway.mjs') + '"'), '--port', "$gateway", '--api-port', "$api", '--image', ('"' + $Image + '"'), '--log', ('"' + $err + '"'))
$proc = Start-Process -FilePath 'node' -ArgumentList $gwArgs -WorkingDirectory $Repo -WindowStyle Hidden -PassThru
@{ gatewayPid = $proc.Id; gatewayPort = $gateway; apiPort = $api; container = $ContainerName; image = $Image; repo = $Repo } | ConvertTo-Json | Set-Content -Path $StateFile -Encoding ASCII
$up = $false
for ($i = 0; $i -lt 40 -and -not $up; $i++) {
    try { $g = Invoke-RestMethod -Uri ('http://127.0.0.1:' + $gateway + '/__gateway/health') -TimeoutSec 3; $up = [bool]$g.ok } catch { Start-Sleep -Milliseconds 250 }
}
if (-not $up) { Get-Content $err -ErrorAction SilentlyContinue | ForEach-Object { Write-Host $_ }; Stop-WithError 'the gateway did not start (see .verdictkit-run\gateway.log).' }
$through = Invoke-RestMethod -Uri ('http://127.0.0.1:' + $gateway + '/api/v1/health') -TimeoutSec 5
if ($through.contractVersion -ne $ExpectedContract) { Stop-WithError 'the gateway does not reach the backend.' }
Write-Ok ('gateway up, backend reachable through it (pid ' + $proc.Id + ')')

# ---- 8. summary -----------------------------------------------------------------------------
$entry = 'http://127.0.0.1:' + $gateway + '/'
Write-Host ''
Write-Host '  VerdictKit is running.' -ForegroundColor Green
Write-Host ''
Write-Host ('  Open this URL:   ' + $entry) -ForegroundColor White
Write-Host ''
Write-Host '  What to try'
Write-Host ('    Guided demo, contradicted worksheet   ' + $entry + 'quote/?demo=padded')
Write-Host ('    Guided demo, claim above the bound    ' + $entry + 'reel/?demo=fx_reel_impossible_sma')
Write-Host ('    Signed bundle, tampered scenario      ' + $entry + 'verify?auto=1&sample=lease-consistent&scenario=tampered-bundle')
Write-Host ''
Write-Host '  Status'
Write-Host ('    backend   127.0.0.1:' + $api + '  (container ' + $ContainerName + ', image ' + $Image + ')')
Write-Host ('    isolation ' + $health.isolationMode + ', judge mode on, contract ' + $health.contractVersion + ', engine ' + $health.engineVersion)
Write-Host ('    signer    disposable demonstration key ' + $lab.signer.keyId.Substring(0, 16) + '... (new at every start)')
Write-Host ('    logs      ' + (Join-Path $RunDir 'gateway.log') + '  |  docker logs ' + $ContainerName)
Write-Host ''
Write-Host '  Stop everything this script started:  scripts\Stop-VerdictKit.ps1'
Write-Host '  Everything listens on 127.0.0.1 only. This is a local demonstration, not a public service.'
Write-Host ''
if (-not $NoBrowser) { Start-Process $entry }
