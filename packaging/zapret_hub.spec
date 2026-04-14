# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

project_root = Path(SPECPATH).resolve().parent
datas = [
    (str(project_root / "sample_data"), "sample_data"),
    (str(project_root / "runtime"), "runtime"),
    (str(project_root / "ui_assets"), "ui_assets"),
]
crypto_hiddenimports = collect_submodules("cryptography")

a = Analysis(
    [str(project_root / "src" / "zapret_hub" / "main.py")],
    pathex=[str(project_root / "src")],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "asyncio",
        "asyncio.base_events",
        "asyncio.base_futures",
        "asyncio.base_subprocess",
        "asyncio.events",
        "asyncio.futures",
        "asyncio.locks",
        "asyncio.protocols",
        "asyncio.queues",
        "asyncio.runners",
        "asyncio.selector_events",
        "asyncio.streams",
        "asyncio.subprocess",
        "asyncio.tasks",
        "asyncio.transports",
        "argparse",
        "base64",
        "collections",
        "dataclasses",
        "hashlib",
        "hmac",
        "logging",
        "logging.handlers",
        "os",
        "random",
        "socket",
        "ssl",
        "string",
        "struct",
        "threading",
        "typing",
        "urllib",
        "urllib.request",
    ] + crypto_hiddenimports,
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
    [],
    name="zapret_hub",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    exclude_binaries=True,
    icon=str(project_root / "ui_assets" / "icons" / "app.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    name="zapret_hub",
)
