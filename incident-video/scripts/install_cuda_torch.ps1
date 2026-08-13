# Reinstall PyTorch with CUDA support in the ComfyUI venv.
# ComfyUI's default pip install often pulls torch+cpu on Windows.
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$ComfyDir = Join-Path $Root "vendor\ComfyUI"
$Pip = Join-Path $ComfyDir "venv\Scripts\pip.exe"
$Python = Join-Path $ComfyDir "venv\Scripts\python.exe"

if (-not (Test-Path $Pip)) {
    Write-Error "ComfyUI venv not found. Run setup_comfyui.ps1 first."
}

Write-Host "=== Installing CUDA-enabled PyTorch in ComfyUI venv ===" -ForegroundColor Cyan
Write-Host "Uninstalling CPU-only torch if present..."
& $Pip uninstall -y torch torchvision torchaudio 2>$null

Write-Host "Installing torch with CUDA 12.4 wheels (compatible with recent NVIDIA drivers)..."
& $Pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

Write-Host ""
Write-Host "Verifying CUDA..."
& $Python -c "import torch; print('torch', torch.__version__); print('cuda available', torch.cuda.is_available()); print('device', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'none')"

Write-Host ""
Write-Host "If cuda available is True, run:"
Write-Host "  .\scripts\patch_comfy_kitchen.ps1   # if ComfyUI fails on startup"
Write-Host "  .\scripts\start_comfyui.ps1"
