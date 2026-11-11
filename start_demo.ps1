# Lance EduAgentic : MCP + agents A2A + orchestrateur + dashboard.
# Usage : .\start_demo.ps1
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root
$python = (Get-Command python -ErrorAction SilentlyContinue)
if (-not $python) {
    $candidate = "$env:LOCALAPPDATA\Python\pythoncore-3.15-64\python.exe"
    if (Test-Path $candidate) { $python = $candidate } else { throw "Python introuvable." }
} else { $python = $python.Source }
Write-Host "EduAgentic : démarrage..." -ForegroundColor Cyan
& $python "a2a/run_all.py" --with-dashboard
