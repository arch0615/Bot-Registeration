# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for R-Bot — One-Folder (--onedir) Windows build.

Bundles:
  - ui/ (index.html + per-site panels)
  - All steps_site*.py modules (dynamically imported through sites.py)
  - Playwright Python package (incl. node driver)
  - pywebview / clr-loader / pythonnet native assets

Does NOT bundle Chromium itself — the Inno Setup installer installs it next
to the exe under <install>/playwright-browsers/ and app.py points the
PLAYWRIGHT_BROWSERS_PATH env var at it at startup.

Build:    pyinstaller --noconfirm r-bot.spec
Output:   dist/R-Bot/R-Bot.exe
"""
from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_submodules

HERE = Path(SPECPATH).resolve()

# App-owned resource files that must ship read-only inside the bundle
datas = [
    (str(HERE / "ui" / "index.html"), "ui"),
    (str(HERE / "ui" / "sites"),      "ui/sites"),
]

# Dynamic step modules — sites.py imports them by name, not by discovery
hiddenimports = [
    "sites",
    "steps_config",
    "steps_site2",
    "steps_site3",
    "steps_site4",
    "steps_site5",
    "gologin",
]
binaries = []

# Pull in Playwright + its node driver, pywebview's edge-chromium backend, and
# the .NET bridge pywebview loads lazily on Windows.
for pkg in ("playwright", "webview", "clr_loader", "pythonnet"):
    try:
        d, b, h = collect_all(pkg)
        datas       += d
        binaries    += b
        hiddenimports += h
    except Exception:
        pass

hiddenimports += collect_submodules("playwright")

block_cipher = None

a = Analysis(
    ["app.py"],
    pathex=[str(HERE)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "numpy", "pandas", "pytest"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="R-Bot",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,            # windowed app — no cmd window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(HERE / "ui" / "icon.ico") if (HERE / "ui" / "icon.ico").exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="R-Bot",
)
