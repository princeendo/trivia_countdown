"""Exercise the real draft-release shell blocks without contacting GitHub."""

import os
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory
import textwrap
import unittest


BASH = (
    str(Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Git" / "bin" / "bash.exe")
    if os.name == "nt" else shutil.which("bash")
)


@unittest.skipUnless(BASH and Path(BASH).is_file(), "Bash is required for release guard checks")
class ReleaseWorkflowTests(unittest.TestCase):
    def test_release_blocks_create_only_drafts_and_never_modify_published_releases(self):
        repository = Path(__file__).resolve().parents[1]
        mock = """
gh() {
    if [[ "$1" == api ]]; then
        case "$TEST_RELEASE_STATE" in
            absent) return 0 ;;
            draft) echo true ;;
            published) echo false ;;
            api_failure) return 42 ;;
        esac
    else
        printf '%s\\n' "$*" >> calls.txt
    fi
}
"""
        for workflow in ("windows-installer.yml", "macos-dmg.yml"):
            text = (repository / ".github" / "workflows" / workflow).read_text(encoding="utf-8")
            # Both workflows end with their draft-release run block. Execute
            # that exact block, not a reimplementation of its safety logic.
            release = textwrap.dedent(text.rsplit("        run: |\n", 1)[1])
            for state in ("absent", "draft", "published", "api_failure"):
                with self.subTest(workflow=workflow, state=state), TemporaryDirectory() as directory:
                    root = Path(directory)
                    script = root / "release.sh"
                    with script.open("w", encoding="utf-8", newline="\n") as stream:
                        stream.write(mock + release)
                    (root / "dist").mkdir()
                    (root / "dist" / "candidate.txt").write_text("fixture", encoding="ascii")
                    result = subprocess.run(
                        [BASH, "--noprofile", "--norc", "release.sh"], cwd=root,
                        env={**os.environ, "TEST_RELEASE_STATE": state,
                             "GITHUB_REPOSITORY": "test/local-only", "GITHUB_REF_NAME": "v0.0.0-test"},
                        capture_output=True, text=True, timeout=30,
                    )
                    calls = (root / "calls.txt").read_text() if (root / "calls.txt").exists() else ""
                    if state in {"published", "api_failure"}:
                        self.assertNotEqual(result.returncode, 0)
                        self.assertEqual(calls, "")
                        if state == "published":
                            self.assertIn("refusing to replace", result.stderr)
                    else:
                        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                        self.assertEqual(len(calls.splitlines()), 1)
                        if state == "absent":
                            self.assertIn("release create", calls)
                            for flag in ("--draft", "--prerelease", "--verify-tag"):
                                self.assertIn(flag, calls)
                        else:
                            self.assertIn("release upload", calls)
                            self.assertIn("--clobber", calls)


if __name__ == "__main__":
    unittest.main()
