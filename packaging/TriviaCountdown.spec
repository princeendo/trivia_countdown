from pathlib import Path
import tomllib


ROOT = Path(SPECPATH).parent
VERSION = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
ICON = ROOT / "build" / "macos" / "TriviaCountdown.icns"
BINARIES = ROOT / "build" / "vendor" / "bin"

a = Analysis(
    [str(ROOT / "make_trivia_countdown_gui.py")],
    pathex=[str(ROOT)],
    binaries=[
        (str(BINARIES / "ffmpeg"), "bin"),
        (str(BINARIES / "ffprobe"), "bin"),
    ],
    datas=[
        (str(ROOT / "assets" / "app_icon.png"), "assets"),
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
    argv_emulation=False,
    target_arch="arm64",
    codesign_identity=None,
    entitlements_file=None,
)

collection = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Trivia Countdown",
)

app = BUNDLE(
    collection,
    name="Trivia Countdown.app",
    icon=str(ICON),
    bundle_identifier="com.princeendo.triviacountdown",
    version=VERSION,
    info_plist={
        "CFBundleDisplayName": "Trivia Countdown",
        "CFBundleName": "Trivia Countdown",
        "CFBundleShortVersionString": VERSION,
        "CFBundleVersion": VERSION,
        "LSMinimumSystemVersion": "14.0",
        "LSApplicationCategoryType": "public.app-category.video",
        "NSHighResolutionCapable": True,
    },
)
