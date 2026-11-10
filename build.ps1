<#
Build script: produces dist\Setup.exe.

Steps:
  1. Create a clean build venv at .build-venv (Python 3.12).
  2. Install pinned dependencies from requirements-lock.txt.
  3. Install Playwright Chromium into .\playwright-browsers\.
  4. Run PyInstaller against r-bot.spec → dist\R-Bot\R-Bot.exe.
  5. Copy .\playwright-browsers\ into dist\R-Bot\playwright-browsers\.
  6. Run Inno Setup (ISCC.exe) against installer.iss → dist\Setup.exe.

Usage:
  powershell -ExecutionPolicy Bypass -File build.ps1
  powershell -ExecutionPolicy Bypass -File build.ps1 -SkipChromium   # reuse existing chromium folder
  powershell -ExecutionPolicy Bypass -File build.ps1 -SkipInstaller  # stop after PyInstaller
#>

param(
  [string]$Python = "",            # path to python.exe; auto-detected if empty
  [switch]$SkipChromium,
  [switch]$SkipInstaller,
  [switch]$Clean
)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

function Resolve-Python {
  if ($Python) { if (Test-Path $Python) { return $Python } else { throw "Python not found at $Python" } }
  $candidates = @(
    "C:\Users\$env:USERNAME\py312\python.exe",
    "C:\Python312\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
  )
  foreach ($c in $candidates) { if (Test-Path $c) { return $c } }
  $cmd = Get-Command python -ErrorAction SilentlyContinue
  if ($cmd -and $cmd.Source -notlike "*WindowsApps*") { return $cmd.Source }
  throw "No usable Python 3.12 found. Pass -Python <path> or install Python 3.12 64-bit."
}

function Resolve-ISCC {
  $candidates = @(
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles}\Inno Setup 6\ISCC.exe",
    "C:\Tools\InnoSetup6\ISCC.exe"
  )
  foreach ($c in $candidates) { if (Test-Path $c) { return $c } }
  $cmd = Get-Command ISCC.exe -ErrorAction SilentlyContinue
  if ($cmd) { return $cmd.Source }
  return $null
}

$py = Resolve-Python
Write-Host "==> Using Python: $py"

if ($Clean) {
  Write-Host "==> Cleaning build/, dist/, .build-venv/, playwright-browsers/"
  Remove-Item -Recurse -Force build, dist, .build-venv, playwright-browsers -ErrorAction SilentlyContinue
}

# 1. Build venv -------------------------------------------------------------
if (-not (Test-Path ".build-venv\Scripts\python.exe")) {
  Write-Host "==> Creating build venv (.build-venv)"
  & $py -m venv .build-venv
}
$venvPy = Resolve-Path ".build-venv\Scripts\python.exe"
Write-Host "==> Venv Python: $venvPy"

# 2. Pinned deps ------------------------------------------------------------
Write-Host "==> Installing pinned dependencies"
& $venvPy -m pip install --upgrade pip wheel
& $venvPy -m pip install -r requirements-lock.txt
if ($LASTEXITCODE -ne 0) { throw "pip install failed" }

# 3. Chromium ---------------------------------------------------------------
if (-not $SkipChromium) {
  Write-Host "==> Installing Playwright Chromium into .\playwright-browsers\"
  $env:PLAYWRIGHT_BROWSERS_PATH = (Resolve-Path .).Path + "\playwright-browsers"
  New-Item -ItemType Directory -Force -Path $env:PLAYWRIGHT_BROWSERS_PATH | Out-Null
  & $venvPy -m playwright install chromium
  if ($LASTEXITCODE -ne 0) { throw "playwright install chromium failed" }
} else {
  Write-Host "==> Skipping Chromium install"
}

# 4. PyInstaller ------------------------------------------------------------
Write-Host "==> Running PyInstaller"
Remove-Item -Recurse -Force build, dist\R-Bot -ErrorAction SilentlyContinue
& $venvPy -m PyInstaller --noconfirm --clean r-bot.spec
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed" }
if (-not (Test-Path "dist\R-Bot\R-Bot.exe")) { throw "PyInstaller did not produce dist\R-Bot\R-Bot.exe" }

# 5. Copy Chromium into the dist ------------------------------------------
if (Test-Path "playwright-browsers") {
  Write-Host "==> Copying playwright-browsers into dist\R-Bot\playwright-browsers"
  Remove-Item -Recurse -Force "dist\R-Bot\playwright-browsers" -ErrorAction SilentlyContinue
  Copy-Item -Recurse -Force "playwright-browsers" "dist\R-Bot\playwright-browsers"
} else {
  Write-Host "==> WARNING: playwright-browsers folder is missing; the installed app will fall back to %LOCALAPPDATA%\ms-playwright on the target machine (which won't exist)."
}

# 6. Inno Setup -------------------------------------------------------------
if ($SkipInstaller) { Write-Host "==> Skipping Inno Setup"; exit 0 }

$iscc = Resolve-ISCC
if (-not $iscc) {
  Write-Host ""
  Write-Host "==> Inno Setup Compiler (ISCC.exe) not found."
  Write-Host "    Install it (https://jrsoftware.org/isdl.php) or run:"
  Write-Host "      winget install --id JRSoftware.InnoSetup --silent"
  Write-Host "    Then re-run this script."
  exit 2
}

Write-Host "==> Running Inno Setup: $iscc"
& $iscc installer.iss
if ($LASTEXITCODE -ne 0) { throw "Inno Setup failed" }

Write-Host ""
Write-Host "==> SUCCESS. Installer is at: $((Resolve-Path dist\Setup.exe).Path)"
