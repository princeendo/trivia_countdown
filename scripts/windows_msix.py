"""Stage and inspect the Store package. Build tooling requires Python 3.12."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import tomllib
import xml.etree.ElementTree as ET
from zipfile import ZipFile

from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parents[1]
FOUNDATION = "http://schemas.microsoft.com/appx/manifest/foundation/windows10"
UAP = "http://schemas.microsoft.com/appx/manifest/uap/windows10"
IDENTITY_NAME = "ColinWhite.TriviaCountdown"
PUBLISHER = "CN=49A512EA-D5D6-441A-8499-B44017F81C7D"
STORE_ID = "9PBDS94C8XD0"
SOURCE_NAME = "Trivia-Countdown-FFmpeg-9.0.1-Windows-x64-sources.tar.gz"
SAMPLE = Path("sample_objects/sample_of_5_trivia_questions.csv")


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def versions(root: Path) -> tuple[str, str]:
    with (root / "pyproject.toml").open("rb") as stream:
        project = tomllib.load(stream)
    app = project["project"]["version"]
    settings = project["tool"]["trivia-countdown"]["windows-store"]
    if settings["app-version"] != app:
        raise ValueError("Update windows-store.app-version and package-version for this app release.")
    package = settings["package-version"]
    if not re.fullmatch(r"[1-9][0-9]*\.[0-9]+\.[0-9]+\.0", package) or any(
        int(part) > 65535 for part in package.split(".")
    ):
        raise ValueError("Store package version needs four integers <= 65535, a nonzero major, and revision 0.")
    return app, package


def validate_manifest(data: bytes, package_version: str) -> ET.Element:
    manifest = ET.fromstring(data)
    identity = manifest.find(f"{{{FOUNDATION}}}Identity")
    expected = {"Name": IDENTITY_NAME, "Publisher": PUBLISHER,
                "Version": package_version, "ProcessorArchitecture": "x64"}
    if identity is None or identity.attrib != expected:
        raise ValueError("MSIX identity does not match the reserved Store product/version/x64 architecture.")
    publisher = manifest.find(f"{{{FOUNDATION}}}Properties/{{{FOUNDATION}}}PublisherDisplayName")
    if publisher is None or publisher.text != "Colin White":
        raise ValueError("MSIX publisher display name does not match Partner Center.")
    return manifest


def stage(root: Path, application: Path) -> Path:
    app_version, package_version = versions(root)
    destination = root / "build/windows/msix"
    application = application.resolve()
    if (application == destination.resolve() or destination.resolve() in application.parents
            or application in destination.resolve().parents):
        raise ValueError("The application directory must be outside the generated MSIX staging directory.")
    required = (
        "Trivia Countdown.exe", "_internal/bin/ffmpeg.exe", "_internal/bin/ffprobe.exe",
        "_internal/assets/fonts/NotoSans-Regular.ttf", "_internal/assets/fonts/NotoSans-Bold.ttf",
        "_internal/LICENSE", "_internal/THIRD_PARTY_NOTICES.md",
        f"_internal/{SAMPLE.as_posix()}", "_internal/build_metadata/pyproject.toml",
    )
    for name in required:
        if not (application / name).is_file():
            raise ValueError(f"Missing packaged resource: {name}. Rebuild the Windows application first.")
    if not any((application / "_internal/licenses").glob("**/*.*")):
        raise ValueError("Packaged third-party licenses are missing.")
    if (application / "_internal/build_metadata/pyproject.toml").read_bytes() != (root / "pyproject.toml").read_bytes():
        raise ValueError("Frozen build metadata differs from pyproject.toml. Rebuild the application first.")
    if (application / "_internal" / SAMPLE).read_bytes() != (root / SAMPLE).read_bytes():
        raise ValueError("Packaged sample CSV differs from the current source sample.")
    sources = root / "dist" / SOURCE_NAME
    build = json.loads((root / "build/vendor/windows/build-manifest.json").read_text(encoding="utf-8-sig"))
    for name, path in {"ffmpeg": application / "_internal/bin/ffmpeg.exe",
                       "ffprobe": application / "_internal/bin/ffprobe.exe", "sources": sources}.items():
        if sha256(path).lower() != build["hashes"][name].lower():
            raise ValueError(f"Packaged {name} does not match the FFmpeg source-build manifest.")
    manifest = (root / "packaging/windows-store/AppxManifest.xml").read_bytes().replace(
        b"__PACKAGE_VERSION__", package_version.encode("ascii")
    )
    validate_manifest(manifest, package_version)
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    shutil.copytree(application, destination / "app")
    (destination / "AppxManifest.xml").write_bytes(manifest)
    assets = destination / "Assets"
    assets.mkdir()
    # Unqualified PNGs avoid a PRI dependency. Windows scales these base assets;
    # DPI/icon appearance is still a required live-system qualification check.
    with Image.open(root / "assets/app_icon.png") as source:
        for name, size in (("StoreLogo", 50), ("Square44x44Logo", 44), ("Square150x150Logo", 150)):
            image = ImageOps.contain(source.convert("RGBA"), (size, size), Image.Resampling.LANCZOS)
            canvas = Image.new("RGBA", (size, size))
            canvas.alpha_composite(image, ((size - image.width) // 2, (size - image.height) // 2))
            canvas.save(assets / f"{name}.png")
    metadata = {"app_version": app_version, "package_version": package_version, "store_id": STORE_ID,
                "source_archive": SOURCE_NAME, "source_sha256": sha256(sources)}
    (destination / "StoreBuild.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return destination


def verify(root: Path, package: Path) -> dict:
    """Compare every staged payload byte with the produced, unsigned Store MSIX."""
    app_version, package_version = versions(root)
    stage_path = root / "build/windows/msix"
    with ZipFile(package) as archive:
        if len(archive.namelist()) != len(set(archive.namelist())):
            raise ValueError("MSIX contains duplicate ZIP entries.")
        if "AppxSignature.p7x" in archive.namelist():
            raise ValueError("Verify the original unsigned Store package, not a locally signed test copy.")
        manifest = validate_manifest(archive.read("AppxManifest.xml"), package_version)
        application = manifest.find(f"{{{FOUNDATION}}}Applications/{{{FOUNDATION}}}Application")
        visuals = application.find(f"{{{UAP}}}VisualElements")
        referenced = [application.attrib["Executable"],
                      manifest.find(f"{{{FOUNDATION}}}Properties/{{{FOUNDATION}}}Logo").text,
                      visuals.attrib["Square44x44Logo"], visuals.attrib["Square150x150Logo"]]
        for name in referenced:
            archive.getinfo(name.replace("\\", "/"))
        for path in stage_path.rglob("*"):
            if path.is_file():
                name = path.relative_to(stage_path).as_posix()
                with archive.open(name) as stream:
                    actual = hashlib.file_digest(stream, "sha256").hexdigest()
                if actual != sha256(path):
                    raise ValueError(f"MSIX payload differs from staging: {name}")
        expected_names = {path.relative_to(stage_path).as_posix() for path in stage_path.rglob("*") if path.is_file()}
        extras = set(archive.namelist()) - expected_names - {"AppxBlockMap.xml", "[Content_Types].xml"}
        if extras:
            raise ValueError(f"Unexpected MSIX payload: {sorted(extras)}")
        # MakeAppx is responsible for schema/semantic validation and block map generation.
        archive.getinfo("AppxBlockMap.xml")
        archive.getinfo("[Content_Types].xml")
        metadata = json.loads(archive.read("StoreBuild.json"))
        if metadata["source_sha256"] != sha256(root / "dist" / SOURCE_NAME):
            raise ValueError("MSIX corresponding-source archive has changed since staging.")
    report = {"status": "passed", "scope": "structure-and-payload-only", "app_version": app_version,
              "package_version": package_version, "store_id": STORE_ID,
              "package": package.name, "sha256": sha256(package),
              "source_archive": SOURCE_NAME, "source_sha256": metadata["source_sha256"]}
    reports = root / "build/verification"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "STORE-002-msix.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("versions")
    staging = commands.add_parser("stage")
    staging.add_argument("--application-directory", type=Path, default=ROOT / "dist/Trivia Countdown")
    verification = commands.add_parser("verify")
    verification.add_argument("--package", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "versions":
            app, package = versions(ROOT)
            print(json.dumps({"app": app, "package": package}))
        elif args.command == "stage":
            print(stage(ROOT, args.application_directory))
        else:
            print(json.dumps(verify(ROOT, args.package), indent=2))
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(1, f"error: {exc}\n")


if __name__ == "__main__":
    main()
