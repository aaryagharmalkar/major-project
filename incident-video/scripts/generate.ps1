# Generate incident simulation video (runs from incident-video root).
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    Write-Error "incident-video venv not found. Run: python -m venv .venv && pip install -r requirements.txt"
}

& $Python -m src.generate @args
exit $LASTEXITCODE
