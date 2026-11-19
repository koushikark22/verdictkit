param([int]$Port = 8000)
$ErrorActionPreference = 'Stop'
$repo = Split-Path $PSScriptRoot -Parent
Set-Location $repo
$env:PYTHONPATH = "$repo\core\src;$repo\apps\quote-autopsy\src;$repo\apps\reel-autopsy\src"
$env:VK_JUDGE_MODE = '0'
Remove-Item Env:VK_ISOLATION -ErrorAction SilentlyContinue
Remove-Item Env:VK_EXAMINER_SOCKET -ErrorAction SilentlyContinue
py -3 -m uvicorn verdictkit.api.server:create_app --factory --host 127.0.0.1 --port $Port
