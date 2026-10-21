# Build dist\OCR-PDF.exe: venv, Python packages, bundled programs, license
# notices, PyInstaller.
# Needs: Python 3.11+ and 7-Zip on PATH.
# Run: powershell -ExecutionPolicy Bypass -File build.ps1
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

function Invoke-Step {
    & $args[0] $args[1..($args.Count - 1)]
    if ($LASTEXITCODE -ne 0) { throw "Failed ($LASTEXITCODE): $args" }
}

$python = '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) { Invoke-Step python -m venv .venv }
Invoke-Step $python -m pip install --upgrade pip
Invoke-Step $python -m pip install -r requirements.txt
Invoke-Step $python tools\fetch_vendor.py
Invoke-Step $python tools\collect_licenses.py
Invoke-Step $python tools\make_assets.py
Invoke-Step $python -m PyInstaller --noconfirm --clean ocr_app.spec
Copy-Item build\THIRD-PARTY-NOTICES.txt, LICENSE dist\

$exe = Get-Item dist\OCR-PDF.exe
'Built {0} ({1:N0} MB)' -f $exe.FullName, ($exe.Length / 1MB)
