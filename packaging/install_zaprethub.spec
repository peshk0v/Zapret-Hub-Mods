# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

project_root = Path(SPECPATH).resolve().parent

datas = [
    (str(project_root / "installer_payload"), "installer_payload"),
    (str(project_root / "ui_assets"), "ui_assets"),
]

a = Analysis(
    [str(project_root / "installer" / "install_zaprethub.py")],
    pathex=[str(project_root / "src")],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    name="install_zaprethub",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    exclude_binaries=False,
    icon=str(project_root / "ui_assets" / "icons" / "app.ico"),
)
