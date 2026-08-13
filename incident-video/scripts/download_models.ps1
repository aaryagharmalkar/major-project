# Download Wan 1.3B GGUF model files from HuggingFace into ComfyUI model dirs.
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$ComfyDir = Join-Path $Root "vendor\ComfyUI"
$Repo = "calcuis/wan-1.3b-gguf"

if (-not (Test-Path $ComfyDir)) {
    Write-Error "ComfyUI not found. Run setup_comfyui.ps1 first."
}

Write-Host "=== Downloading Wan 1.3B + VACE I2V + SD1.5 keyframe models ===" -ForegroundColor Cyan

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    Write-Host "Creating incident-video venv for downloads..."
    python -m venv (Join-Path $Root ".venv")
    & (Join-Path $Root ".venv\Scripts\pip.exe") install "huggingface-hub>=0.23.0" -q
}

$DownloadPy = Join-Path $PSScriptRoot "download_models.py"
& $Python $DownloadPy $ComfyDir
if ($LASTEXITCODE -ne 0) {
    Write-Error "Model download failed with exit code $LASTEXITCODE"
}

Write-Host ""
Write-Host "Model download complete." -ForegroundColor Green
