# Setup ComfyUI + calcuis gguf node for Wan 1.3B incident video generation.
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Vendor = Join-Path $Root "vendor"
$ComfyDir = Join-Path $Vendor "ComfyUI"
$CustomNodes = Join-Path $ComfyDir "custom_nodes"
$GgufNode = Join-Path $CustomNodes "gguf"

Write-Host "=== Incident Video: ComfyUI Setup ===" -ForegroundColor Cyan

New-Item -ItemType Directory -Force -Path $Vendor | Out-Null

if (-not (Test-Path $ComfyDir)) {
    Write-Host "Cloning ComfyUI..."
    git clone https://github.com/comfyanonymous/ComfyUI.git $ComfyDir
} else {
    Write-Host "ComfyUI already exists at $ComfyDir"
}

if (-not (Test-Path $GgufNode)) {
    Write-Host "Cloning calcuis gguf custom node..."
    New-Item -ItemType Directory -Force -Path $CustomNodes | Out-Null
    git clone https://github.com/calcuis/gguf.git $GgufNode
} else {
    Write-Host "gguf node already exists at $GgufNode"
}

$VenvDir = Join-Path $ComfyDir "venv"
if (-not (Test-Path $VenvDir)) {
    Write-Host "Creating ComfyUI virtual environment..."
    python -m venv $VenvDir
}

$Python = Join-Path $VenvDir "Scripts\python.exe"
$Pip = Join-Path $VenvDir "Scripts\pip.exe"

Write-Host "Installing ComfyUI dependencies (this may take several minutes)..."
& $Pip install --upgrade pip
& $Pip install -r (Join-Path $ComfyDir "requirements.txt")
& $Pip install protobuf

Write-Host "Installing CUDA-enabled PyTorch (required for GPU video generation)..."
& $Pip uninstall -y torch torchvision torchaudio 2>$null
& $Pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

Write-Host "Patching comfy_kitchen for torch 2.6 compatibility..."
$PatchPy = Join-Path (Split-Path -Parent $PSScriptRoot) ".venv\Scripts\python.exe"
if (-not (Test-Path $PatchPy)) {
    python -m venv (Join-Path (Split-Path -Parent $PSScriptRoot) ".venv")
    & (Join-Path (Split-Path -Parent $PSScriptRoot) ".venv\Scripts\pip.exe") install "huggingface-hub>=0.23.0" -q
}
& $PatchPy (Join-Path $PSScriptRoot "patch_comfy_kitchen.py") $ComfyDir

# Ensure model directories exist
$ModelDirs = @(
    "models\diffusion_models",
    "models\text_encoders",
    "models\vae",
    "models\clip",
    "input",
    "output"
)
foreach ($Dir in $ModelDirs) {
    New-Item -ItemType Directory -Force -Path (Join-Path $ComfyDir $Dir) | Out-Null
}

Write-Host ""
Write-Host "Setup complete." -ForegroundColor Green
Write-Host "Next steps:"
Write-Host "  1. .\scripts\download_models.ps1"
Write-Host "  2. If ComfyUI fails with 'Torch not compiled with CUDA enabled', run .\scripts\install_cuda_torch.ps1"
Write-Host "  3. .\scripts\start_comfyui.ps1"
Write-Host "  4. python -m src.generate --input <case.json> --dry-run"
