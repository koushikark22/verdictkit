<#
.SYNOPSIS
  Stops what Start-VerdictKit.ps1 started, and nothing else.

.DESCRIPTION
  Removes the labelled VerdictKit backend container and ends the gateway process recorded in
  .verdictkit-run\state.json, after checking that the process really is this repository's gateway.
  Unrelated processes and containers are never touched.
#>
$ErrorActionPreference = 'Continue'
$Repo = Split-Path -Parent $PSScriptRoot
$StateFile = Join-Path (Join-Path $Repo '.verdictkit-run') 'state.json'
$ContainerName = 'vk-batch2-backend'

$state = $null
if (Test-Path $StateFile) { try { $state = Get-Content $StateFile -Raw | ConvertFrom-Json } catch { $state = $null } }

if ($state -and $state.gatewayPid) {
    $proc = Get-CimInstance Win32_Process -Filter ('ProcessId=' + [int]$state.gatewayPid) -ErrorAction SilentlyContinue
    if ($proc -and $proc.CommandLine -like '*gateway.mjs*' -and $proc.CommandLine -like ('*' + $Repo + '*')) {
        Stop-Process -Id $proc.ProcessId -Force
        Write-Host ('stopped gateway (pid ' + $proc.ProcessId + ')')
    } else { Write-Host 'no running VerdictKit gateway found (nothing stopped)' }
}

if (Get-Command docker -ErrorAction SilentlyContinue) {
    $owned = & docker ps -a --filter ('name=^/' + $ContainerName + '$') --filter 'label=com.verdictkit.managed=1' --format '{{.ID}}' 2>$null
    if ($owned) { & docker rm -f $ContainerName 2>$null | Out-Null; Write-Host ('removed container ' + $ContainerName) }
    else { Write-Host 'no VerdictKit backend container found (nothing removed)' }
}
if (Test-Path $StateFile) { Remove-Item $StateFile -Force }
