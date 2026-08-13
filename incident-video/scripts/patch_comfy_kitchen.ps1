# Patch comfy_kitchen for torch 2.6 custom_op compatibility.
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$ComfyDir = Join-Path $Root "vendor\ComfyUI"
$Python = Join-Path $Root ".venv\Scripts\python.exe"

if (-not (Test-Path $ComfyDir)) {
    Write-Error "ComfyUI not found. Run setup_comfyui.ps1 first."
}

if (-not (Test-Path $Python)) {
    python -m venv (Join-Path $Root ".venv")
    & (Join-Path $Root ".venv\Scripts\pip.exe") install "huggingface-hub>=0.23.0" -q
}

& $Python (Join-Path $PSScriptRoot "patch_comfy_kitchen.py") $ComfyDir
if ($LASTEXITCODE -ne 0) {
    Write-Error "Patch failed with exit code $LASTEXITCODE"
}

Write-Host "comfy_kitchen patch complete. Re-run: .\scripts\start_comfyui.ps1" -ForegroundColor Green
