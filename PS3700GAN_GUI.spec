# -*- mode: python ; coding: utf-8 -*-
import sys; sys.setrecursionlimit(10000)


block_cipher = None


a = Analysis(
    ['PS3700GAN_GUI.py'],
    pathex=[],
    binaries=[],
    datas=[('baudrate.ini', '.'), ('Logo_LRTME.png', '.'), ('git_commit_sha.txt', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
splash = Splash(
    'LRTME_splash.png',
    binaries=a.binaries,
    datas=a.datas,
    text_pos=(250, 460),
    text_size=12,
    text_color='black',
    text_default='Author: Mitja Nemec\nInitializing',
    minify_script=True,
    always_on_top=True,
)

exe = EXE(
    pyz,
    a.scripts,
    splash,
    [],
    exclude_binaries=True,
    name='PS3700GAN_GUI',
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
    icon=['Logo_LRTME.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    splash.binaries,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PS3700GAN_GUI',
)
