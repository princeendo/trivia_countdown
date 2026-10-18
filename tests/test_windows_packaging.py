"""Check PowerShell build failure handling without invoking a real package build."""

import os
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory
import unittest


def windows_powershell_environment():
    # CI invokes Python from PowerShell 7. Its module path is incompatible with
    # the Windows PowerShell 5.1 children used here (even Get-FileHash can fail).
    # Let each child initialize its own default module search path.
    return {name: value for name, value in os.environ.items() if name.upper() != "PSMODULEPATH"}


@unittest.skipUnless(os.name == "nt", "Windows PowerShell packaging checks")
class WindowsPackagingTests(unittest.TestCase):
    def test_source_build_cache_verifies_binaries_and_source_archive(self):
        repository = Path(__file__).resolve().parents[1]
        with TemporaryDirectory() as directory:
            root = Path(directory)
            scripts = root / "scripts"
            scripts.mkdir()
            packaging = root / "packaging"
            packaging.mkdir()
            names = ("build_ffmpeg_windows.sh", "compile_ffmpeg_windows.sh", "build_ffmpeg_windows.ps1")
            for name in names:
                shutil.copyfile(repository / "scripts" / name, scripts / name)
            readme = packaging / "FFMPEG_WINDOWS_SOURCE_README.md"
            shutil.copyfile(repository / "packaging" / readme.name, readme)
            inputs = [scripts / name for name in names] + [readme]
            key = ":".join(hashlib.sha256(path.read_bytes()).hexdigest().upper() for path in inputs)
            vendor = root / "build" / "vendor" / "windows"
            (vendor / "bin").mkdir(parents=True)
            (root / "dist").mkdir()
            outputs = {
                "ffmpeg": vendor / "bin" / "ffmpeg.exe",
                "ffprobe": vendor / "bin" / "ffprobe.exe",
                "sources": root / "dist" / "Trivia-Countdown-FFmpeg-9.0.1-Windows-x64-sources.tar.gz",
            }
            for path in outputs.values():
                path.write_bytes(b"test cache fixture")
            manifest = {
                "inputKey": key,
                "hashes": {name: hashlib.sha256(path.read_bytes()).hexdigest().upper() for name, path in outputs.items()},
            }
            (vendor / "build-manifest.json").write_text(json.dumps(manifest), encoding="ascii")

            def invoke():
                return subprocess.run(
                    ["powershell.exe", "-NoProfile", "-NonInteractive", "-File", str(scripts / names[2])],
                    env=windows_powershell_environment(), capture_output=True, text=True, timeout=30,
                )

            result = invoke()
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("Reusing verified", result.stdout)
            for name, path in outputs.items():
                with self.subTest(corrupt=name):
                    path.write_bytes(b"corrupted cache")
                    result = invoke()
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("MSYS2 build tools are missing", result.stderr)
                    path.write_bytes(b"test cache fixture")
            (scripts / names[1]).write_text("# changed recipe\n", encoding="ascii")
            self.assertNotEqual(invoke().returncode, 0)

    def test_failed_native_build_step_stops_and_restores_working_directory(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            scripts = root / "scripts"
            scripts.mkdir()
            shutil.copyfile(
                Path(__file__).resolve().parents[1] / "scripts" / "build_windows_installer.ps1",
                scripts / "build_windows_installer.ps1",
            )
            for name in ("build_ffmpeg_windows.ps1", "collect_runtime_licenses.ps1"):
                (scripts / name).write_text("# No downloads or license collection in this test\n", encoding="utf-8")
            (scripts / "verify_windows_package.ps1").write_text("throw 'Should not reach verification'\n", encoding="utf-8")
            compiler = root / "ISCC.exe"
            compiler.touch()
            quoted_root = str(root).replace("'", "''")
            command = rf"""
$ErrorActionPreference = 'Stop'
function global:uv {{ $global:LASTEXITCODE = 42 }}
$before = (Get-Location).Path
try {{
    & '{quoted_root}\scripts\build_windows_installer.ps1' -IsccPath '{quoted_root}\ISCC.exe'
    throw 'Build unexpectedly succeeded'
}} catch {{
    if ($_.Exception.Message -notlike '*uv failed with exit code 42*') {{ throw }}
}}
if ((Get-Location).Path -ne $before) {{ throw 'Working directory was not restored' }}
"""
            result = subprocess.run(
                ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
                env=windows_powershell_environment(), capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
