from pathlib import Path


ROOT = Path(SPECPATH).parent
ICON = ROOT / "build" / "windows" / "TriviaCountdown.ico"
BINARIES = ROOT / "build" / "vendor" / "windows" / "bin"

a = Analysis(
    [str(ROOT / "make_trivia_countdown_gui.py")],
    pathex=[str(ROOT)],
    binaries=[
        (str(BINARIES / "ffmpeg.exe"), "bin"),
        (str(BINARIES / "ffprobe.exe"), "bin"),
    ],
    datas=[
        (str(ROOT / "assets" / "app_icon.png"), "assets"),
        (str(ROOT / "assets" / "fonts"), "assets/fonts"),
        (str(ROOT / "LICENSE"), "."),
        (str(ROOT / "THIRD_PARTY_NOTICES.md"), "."),
        (str(ROOT / "build" / "vendor" / "licenses"), "licenses"),
    ],
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
    [],
    exclude_binaries=True,
    name="Trivia Countdown",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=str(ICON),
)

COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Trivia Countdown",
)
