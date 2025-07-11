# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['clinometro3.py'],
    pathex=[],
    binaries=[],
    datas=[('mar.jpg', '.'), ('pitch.png', '.'), ('roll.png', '.'), ('alarma_babor.mp3', '.'), ('alarma_encabuzado.mp3', '.'), ('alarma_estribor.mp3', '.'), ('alarma_sentado.mp3', '.'), ('head_alarm.mp3', '.'), ('port_alarm.mp3', '.'), ('starboard_alarm.mp3', '.'), ('stern_alarm.mp3', '.'), ('license.json', '.')],
    hiddenimports=[],
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
    a.binaries,
    a.datas,
    [],
    name='clinometro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
