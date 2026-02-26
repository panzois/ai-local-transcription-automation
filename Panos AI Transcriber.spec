# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files

datas = [('./assets', 'assets')]
datas += collect_data_files('whisper')


a = Analysis(
    ['app/gui_app.py'],
    pathex=[],
    binaries=[('/opt/homebrew/Cellar/ffmpeg/8.0.1_4/bin/ffmpeg', '.'), ('/opt/homebrew/Cellar/ffmpeg/8.0.1_4/bin/ffprobe', '.')],
    datas=datas,
    hiddenimports=['whisper'],
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
    name='Panos AI Transcriber',
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
    icon=['assets/panos_whisper_logo_last.icns'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Panos AI Transcriber',
)
app = BUNDLE(
    coll,
    name='Panos AI Transcriber.app',
    icon='./assets/panos_whisper_logo_last.icns',
    bundle_identifier=None,
)
