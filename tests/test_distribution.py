"""A packaged skill must work after extraction without the source checkout."""

import hashlib
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("package_release", ROOT / "scripts/package_release.py")
packager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(packager)


class DistributionTests(unittest.TestCase):
    def test_reproducible_archive_and_extracted_helper(self):
        with tempfile.TemporaryDirectory(prefix="repoquest-distribution-") as directory:
            root = Path(directory)
            first = packager.package_release(ROOT, root / "first")
            second = packager.package_release(ROOT, root / "second")
            self.assertEqual(first[0].read_bytes(), second[0].read_bytes())
            with zipfile.ZipFile(first[0]) as archive:
                self.assertIn("repoquest/LICENSE.txt", archive.namelist())
                self.assertFalse(any("__pycache__" in name or ".git/" in name for name in archive.namelist()))
                archive.extractall(root / "installed")
            output = root / "installed.html"
            process = subprocess.run([sys.executable, str(root / "installed/repoquest/scripts/quest.py"),
                                      "build", str(ROOT / "examples/borrowed-menu/case.json"), "--output", str(output)],
                                     cwd=root, capture_output=True, text=True, timeout=15)
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertEqual(output.read_text(encoding="utf-8"), first[1].read_text(encoding="utf-8"))
            for line in first[-1].read_text().splitlines():
                digest, name = line.split("  ", 1)
                self.assertEqual(digest, hashlib.sha256((first[-1].parent / name).read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
