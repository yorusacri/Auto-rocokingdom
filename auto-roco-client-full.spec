# -*- mode: python ; coding: utf-8 -*-
import os

_project_root = os.getcwd()

a = Analysis(
    ['client_main.py'],
    pathex=[_project_root],
    binaries=[],
    datas=[
        (os.path.join(_project_root, 'templates'), 'templates'),
        (os.path.join(_project_root, 'web'), 'web'),
    ],
    hiddenimports=['gevent', 'gevent.websocket', 'bottle', 'bottle_websocket'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='auto-roco-client-full',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(_project_root, 'web', 'icon.svg'),
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='auto-roco-client-full',
)
