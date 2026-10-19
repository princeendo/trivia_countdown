"""Exercise Store payload/source pairing and archive integrity without a Windows SDK."""

import json
import os
from pathlib import Path
import shutil
import sys
import subprocess
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch
from zipfile import ZipFile

from PIL import Image

if sys.version_info >= (3, 11):
    from scripts.windows_msix import SOURCE_NAME, SAMPLE, sha256, stage, verify, versions


REPOSITORY = Path(__file__).resolve().parents[1]
POWERSHELL = shutil.which("powershell.exe") if os.name == "nt" else shutil.which("pwsh")


@unittest.skipUnless(sys.version_info >= (3, 11), "MSIX build tools use Python 3.12; source runtime supports 3.9+")
class WindowsMsixTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.application = self.root / "dist/Trivia Countdown"
        for name in ("pyproject.toml", "packaging/windows-store/AppxManifest.xml", "assets/app_icon.png", SAMPLE):
            destination = self.root / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPOSITORY / name, destination)
        payload = (
            "Trivia Countdown.exe", "_internal/bin/ffmpeg.exe", "_internal/bin/ffprobe.exe",
            "_internal/assets/fonts/NotoSans-Regular.ttf", "_internal/assets/fonts/NotoSans-Bold.ttf",
            "_internal/LICENSE", "_internal/THIRD_PARTY_NOTICES.md", "_internal/licenses/test.txt",
        )
        for name in payload:
            path = self.application / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(f"fixture for {name}".encode())
        for source, destination in ((self.root / "pyproject.toml", "_internal/build_metadata/pyproject.toml"),
                                    (self.root / SAMPLE, f"_internal/{SAMPLE.as_posix()}")):
            path = self.application / destination
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, path)
        (self.root / "dist" / SOURCE_NAME).write_bytes(b"matching source archive fixture")
        manifest = self.root / "build/vendor/windows/build-manifest.json"
        manifest.parent.mkdir(parents=True)
        manifest.write_text(json.dumps({"hashes": {
            "ffmpeg": sha256(self.application / "_internal/bin/ffmpeg.exe"),
            "ffprobe": sha256(self.application / "_internal/bin/ffprobe.exe"),
            "sources": sha256(self.root / "dist" / SOURCE_NAME),
        }}), encoding="utf-8")

    def package(self, *, replace=None, extra=None):
        staged = stage(self.root, self.application)
        package = self.root / "dist/test.msix"
        with ZipFile(package, "w") as archive:
            for path in staged.rglob("*"):
                if path.is_file():
                    name = path.relative_to(staged).as_posix()
                    archive.writestr(name, replace[name] if replace and name in replace else path.read_bytes())
            archive.writestr("AppxBlockMap.xml", "<BlockMap />")
            archive.writestr("[Content_Types].xml", "<Types />")
            for name, content in (extra or {}).items():
                archive.writestr(name, content)
        return package

    def test_stage_and_archive_pair_the_exact_binaries_sources_and_store_identity(self):
        result = verify(self.root, self.package())
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["scope"], "structure-and-payload-only")
        self.assertEqual((result["app_version"], result["package_version"]), ("0.1.1", "1.0.1.0"))
        self.assertEqual(result["source_sha256"], sha256(self.root / "dist" / SOURCE_NAME))
        staged = self.root / "build/windows/msix"
        for name, size in (("StoreLogo", 50), ("Square44x44Logo", 44), ("Square150x150Logo", 150)):
            with Image.open(staged / f"Assets/{name}.png") as image:
                self.assertEqual(image.size, (size, size))
        self.assertEqual((staged / "app/_internal" / SAMPLE).read_bytes(), (self.root / SAMPLE).read_bytes())

    def test_stage_rejects_missing_or_stale_runtime_and_mismatched_media_sources(self):
        changes = (
            (self.application / "_internal/bin/ffmpeg.exe", "does not match"),
            (self.root / "dist" / SOURCE_NAME, "does not match"),
            (self.application / "_internal/build_metadata/pyproject.toml", "metadata differs"),
            (self.application / "_internal" / SAMPLE, "sample CSV differs"),
        )
        for path, message in changes:
            original = path.read_bytes()
            with self.subTest(path=path):
                path.write_bytes(b"stale or unrelated content")
                with self.assertRaisesRegex(ValueError, message):
                    stage(self.root, self.application)
                path.write_bytes(original)
        (self.application / "_internal/bin/ffprobe.exe").unlink()
        with self.assertRaisesRegex(ValueError, "Missing packaged resource"):
            stage(self.root, self.application)

    def test_package_rejects_payload_tampering_wrong_identity_and_unexpected_files(self):
        for replacement in ({"app/Trivia Countdown.exe": b"different executable"},
                            {"AppxManifest.xml": (self.root / "packaging/windows-store/AppxManifest.xml").read_bytes()
                             .replace(b"__PACKAGE_VERSION__", b"1.0.1.0")
                             .replace(b"ColinWhite.TriviaCountdown", b"Other.Product")}):
            with self.subTest(replacement=list(replacement)), self.assertRaises(ValueError):
                verify(self.root, self.package(replace=replacement))
        for extra in ({"AppxSignature.p7x": b"local signature"}, {"unrelated.exe": b"unexpected"}):
            with self.subTest(extra=list(extra)), self.assertRaises(ValueError):
                verify(self.root, self.package(extra=extra))
        package = self.package()
        (self.root / "dist" / SOURCE_NAME).write_bytes(b"changed sources")
        with self.assertRaisesRegex(ValueError, "source archive has changed"):
            verify(self.root, package)

    def test_version_validation_prevents_zero_major_reserved_revision_and_metadata_drift(self):
        path = self.root / "pyproject.toml"
        original = path.read_text()
        for version in ("0.1.1.0", "1.0.1.1", "1.65536.1.0", "1.0.1", "1.0.1.0-beta"):
            path.write_text(original.replace('package-version = "1.0.1.0"', f'package-version = "{version}"'))
            with self.subTest(version=version), self.assertRaises(ValueError):
                versions(self.root)
        path.write_text(original.replace('app-version = "0.1.1"', 'app-version = "0.1.0"'))
        with self.assertRaisesRegex(ValueError, "Update windows-store"):
            versions(self.root)

    def test_sample_export_selects_a_writable_user_copy_and_handles_cancel_and_errors(self):
        from trivia_countdown.gui import TriviaCountdownApp

        app = Mock()
        output = self.root / "Sample Trivia Questions.csv"
        with patch("trivia_countdown.gui.filedialog.asksaveasfilename", return_value=str(output)), patch(
            "trivia_countdown.gui.resource_path", return_value=self.root / SAMPLE
        ):
            TriviaCountdownApp._save_sample_csv(app)
        self.assertEqual(output.read_bytes(), (self.root / SAMPLE).read_bytes())
        app.trivia_path.set.assert_called_once_with(str(output))
        app._questions_changed.assert_called_once()
        app.reset_mock()
        with patch("trivia_countdown.gui.filedialog.asksaveasfilename", return_value=""):
            TriviaCountdownApp._save_sample_csv(app)
        app.trivia_path.set.assert_not_called()
        with patch("trivia_countdown.gui.filedialog.asksaveasfilename", return_value=str(output)), patch(
            "trivia_countdown.gui.shutil.copyfile", side_effect=PermissionError("read-only location")
        ), patch("trivia_countdown.gui.messagebox.showerror") as error:
            TriviaCountdownApp._save_sample_csv(app)
        error.assert_called_once()
        app.trivia_path.set.assert_not_called()


@unittest.skipUnless(POWERSHELL, "PowerShell is required for build failure handling checks")
class MsixPowerShellTests(unittest.TestCase):
    def test_failed_staging_removes_stale_outputs_stops_before_packaging_and_restores_directory(self):
        with TemporaryDirectory(prefix="MSIX's build ") as directory:
            root = Path(directory)
            (root / "scripts").mkdir()
            (root / "app").mkdir()
            (root / "dist").mkdir()
            (root / "build/verification").mkdir(parents=True)
            shutil.copyfile(REPOSITORY / "scripts/build_windows_msix.ps1", root / "scripts/build_windows_msix.ps1")
            (root / "scripts/verify_windows_package.ps1").write_text("throw 'Must not reach verification'\n")
            compiler = root / "makeappx.exe"
            compiler.touch()
            outputs = (root / "dist/Trivia-Countdown-1.0.1.0-Windows-x64.msix",
                       root / "dist/Trivia-Countdown-1.0.1.0-Windows-x64-MSIX-SHA256SUMS.txt",
                       root / "build/verification/STORE-002-msix.json")
            for output in outputs:
                output.write_text("stale successful output")
            quoted = str(root).replace("'", "''")
            command = rf"""
$ErrorActionPreference = 'Stop'
$env:OS = 'Windows_NT'
function global:uv {{
    if ($args[-1] -eq 'versions') {{
        '{{"app":"0.1.1","package":"1.0.1.0"}}'
        $global:LASTEXITCODE = 0
    }} else {{
        if ($args -notcontains 'stage') {{ throw 'Unexpected build command' }}
        $global:LASTEXITCODE = 42
    }}
}}
$before = (Get-Location).Path
try {{
    & '{quoted}/scripts/build_windows_msix.ps1' -ApplicationDirectory '{quoted}/app' -MakeAppxPath '{quoted}/makeappx.exe'
    throw 'Build unexpectedly succeeded'
}} catch {{
    if ($_.Exception.Message -ne 'uv failed with exit code 42.') {{ throw }}
}}
if ((Get-Location).Path -ne $before) {{ throw 'Working directory was not restored' }}
"""
            env = {key: value for key, value in os.environ.items() if key.upper() != "PSMODULEPATH"}
            result = subprocess.run(
                [POWERSHELL, "-NoProfile", "-NonInteractive", "-Command", command],
                env=env, capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue(all(not output.exists() for output in outputs))


if __name__ == "__main__":
    unittest.main()
