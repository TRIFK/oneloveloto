# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\stask\\Desktop\\MusicalLoto\\build\\..\\musical_loto.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\stask\\Desktop\\MusicalLoto\\build\\..\\resources', 'resources')],
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
    name='musical_loto',
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
    icon=['C:\\Users\\stask\\Desktop\\MusicalLoto\\resources\\icon.ico'],
)
