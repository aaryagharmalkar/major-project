# Start ComfyUI server with low-VRAM flags for Wan 1.3B generation.
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$ComfyDir = Join-Path $Root "vendor\ComfyUI"
$Python = Join-Path $ComfyDir "venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    Write-Error "ComfyUI venv not found. Run setup_comfyui.ps1 first."
}

Write-Host "Starting ComfyUI at http://127.0.0.1:8188" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop."
Set-Location $ComfyDir
& $Python main.py --lowvram --preview-method none
