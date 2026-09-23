"""Behavior checks for the executable evidence boundary and portable output."""

import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/repoquest/scripts"))
from repoquest.cli import main
from repoquest.core import QuestError, load_case, load_verified, verify
from repoquest.importer import import_git
from repoquest.render import render


class QuestTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="repoquest-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.case_dir = self.root / "case"
        shutil.copytree(ROOT / "examples/borrowed-menu", self.case_dir)
        self.path = self.case_dir / "case.json"

    def update(self, transform):
        data = json.loads(self.path.read_text(encoding="utf-8"))
        transform(data)
        self.path.write_text(json.dumps(data), encoding="utf-8")

    def test_same_contract_reproduces_and_fixes_bug(self):
        report = verify(self.path, trust_code=True)
        self.assertEqual(report["before"]["tests"], 4)
        self.assertEqual(len(report["before"]["failures"]), 2)
        self.assertEqual(report["after"]["failures"], [])
        self.assertEqual(report["before"]["test_ids"], report["after"]["test_ids"])
        self.assertEqual(load_verified(self.path)[2], report)
        page = render(self.path)
        self.assertIn("One file. Zero network requests.", page)
        self.assertNotIn("dict.copy() copies", page)  # Spoiler text stays encoded until requested.
        self.assertNotIn("<script src=", page)

    def test_execution_requires_explicit_trust(self):
        with self.assertRaisesRegex(QuestError, "Execution is disabled"):
            verify(self.path)

    def test_report_name_cannot_be_used_for_input_evidence(self):
        original = (self.case_dir / "verification.json").read_bytes()
        self.update(lambda d: d["provenance"]["license_files"].append("verification.json"))
        with self.assertRaisesRegex(QuestError, "reserved"):
            verify(self.path, True)
        self.assertEqual((self.case_dir / "verification.json").read_bytes(), original)

    def test_atomic_report_write_preserves_hard_link_target(self):
        target = self.root / "unrelated.txt"
        target.write_text("Preserve this file.", encoding="utf-8")
        report = self.case_dir / "verification.json"
        report.unlink()
        os.link(target, report)
        verify(self.path, True)
        self.assertEqual(target.read_text(encoding="utf-8"), "Preserve this file.")
        self.assertEqual(load_verified(self.path)[2]["after"]["tests"], 4)

    def test_malformed_candidate_reference_returns_clean_error(self):
        self.update(lambda d: d["suspects"][0].update(ref=[]))
        output = io.StringIO()
        with contextlib.redirect_stderr(output):
            self.assertEqual(main(["check", str(self.path)]), 2)
        self.assertIn("evidence ID", output.getvalue())

    def test_incomplete_reports_are_rejected_before_rendering(self):
        path = self.case_dir / "verification.json"
        original = path.read_text(encoding="utf-8")
        for section, field in ((None, "captured_at"), (None, "python"), (None, "platform"),
                               ("before", "log"), ("after", "log")):
            with self.subTest(section=section, field=field):
                report = json.loads(original)
                del (report[section] if section else report)[field]
                path.write_text(json.dumps(report), encoding="utf-8")
                output = io.StringIO()
                with contextlib.redirect_stderr(output):
                    self.assertEqual(main(["build", str(self.path), "--output", str(self.root / "bad.html")]), 2)
                self.assertFalse((self.root / "bad.html").exists())

    def test_check_and_build_never_execute_fixture(self):
        marker = self.root / "executed"
        source = self.case_dir / "before/cafe.py"
        source.write_text(source.read_text() + f"\nopen({str(marker)!r}, 'w').write('executed')\n", encoding="utf-8")
        load_case(self.path)
        with self.assertRaisesRegex(QuestError, "changed since"):
            render(self.path)
        self.assertFalse(marker.exists())

    def test_stale_manifest_code_contract_or_license_rejected(self):
        for name in ("case.json", "before/cafe.py", "after/cafe.py", "contract.py", "LICENSE.txt"):
            with self.subTest(name=name):
                file = self.case_dir / name
                original = file.read_bytes()
                file.write_bytes(original + b"\n")
                with self.assertRaisesRegex(QuestError, "changed since"):
                    load_verified(self.path)
                file.write_bytes(original)

    def test_invalid_citations_and_paths_rejected(self):
        original = self.path.read_bytes()
        for mutate in (lambda d: d["files"].append("../outside.py"),
                       lambda d: d["evidence"][0].update(end=9999),
                       lambda d: d["hints"][0].update(refs=["made-up"]),
                       lambda d: d["evidence"][0].update(path="after/cafe.py"),
                       lambda d: d["files"].append("CAFE.py")):
            with self.subTest(mutate=mutate):
                self.update(mutate)
                with self.assertRaises(QuestError):
                    load_case(self.path)
                self.path.write_bytes(original)

    def test_import_error_does_not_count_as_bug(self):
        file = self.case_dir / "before/cafe.py"
        file.write_text(file.read_text() + "\nimport package_that_does_not_exist_quest\n")
        with self.assertRaisesRegex(QuestError, "contract/harness error"):
            verify(self.path, True)

    def test_test_error_does_not_count_as_assertion_failure(self):
        file = self.case_dir / "before/cafe.py"
        file.write_text(file.read_text().replace('menu = self._menu.copy()', 'raise RuntimeError("broken environment")'))
        with self.assertRaisesRegex(QuestError, "test errors"):
            verify(self.path, True)

    def test_failing_fix_is_rejected(self):
        file = self.case_dir / "after/cafe.py"
        file.write_bytes((self.case_dir / "before/cafe.py").read_bytes() + b"\n# Still broken\n")
        with self.assertRaisesRegex(QuestError, "after: the behavior contract still fails"):
            verify(self.path, True)

    def test_passing_before_is_rejected(self):
        file = self.case_dir / "before/cafe.py"
        file.write_bytes((self.case_dir / "after/cafe.py").read_bytes() + b"\n# Already fixed\n")
        with self.assertRaisesRegex(QuestError, "before: expected an assertion failure"):
            verify(self.path, True)

    def test_skips_are_not_evidence(self):
        file = self.case_dir / "contract.py"
        file.write_text(file.read_text() + '\nMenuContract = unittest.skip("unavailable")(MenuContract)\n')
        with self.assertRaisesRegex(QuestError, "skipped"):
            verify(self.path, True)

    def test_empty_suite_is_rejected(self):
        file = self.case_dir / "contract.py"
        file.write_text('# No actual tests\n' * 30)
        with self.assertRaisesRegex(QuestError, "no tests ran"):
            verify(self.path, True)

    def test_snapshot_dependent_test_selection_is_rejected(self):
        file = self.case_dir / "contract.py"
        file.write_text(file.read_text() + '\nservice = MenuService()\nservice.menu_for("cake")\nif receipt(service.menu_for()) == "soup, bread":\n    del MenuContract.test_default_menu\n')
        with self.assertRaisesRegex(QuestError, "same tests"):
            verify(self.path, True)

    def test_timeout_does_not_produce_verification(self):
        file = self.case_dir / "before/cafe.py"
        file.write_text(file.read_text() + "\nwhile True: pass\n")
        with self.assertRaisesRegex(QuestError, "timed out"):
            verify(self.path, True, timeout=.15)
        with self.assertRaisesRegex(QuestError, "changed since"):
            load_verified(self.path)

    def test_untrusted_markup_is_escaped(self):
        attack = '<img src=x onerror="alert(1)">@@EVIDENCE@@</script>'
        self.update(lambda d: d.update(title=attack))
        verify(self.path, True)
        page = render(self.path)
        self.assertNotIn(attack, page)
        self.assertIn('&lt;img src=x onerror=&quot;alert(1)&quot;&gt;@@EVIDENCE@@&lt;/script&gt;', page)

    def test_cli_reports_actionable_failure(self):
        output = io.StringIO()
        with contextlib.redirect_stderr(output):
            self.assertEqual(main(["verify", str(self.path)]), 2)
        self.assertIn("--trust-code", output.getvalue())

    @unittest.skipUnless(shutil.which("git"), "Git is required for import integration")
    def test_real_git_commits_import_without_checkout_or_execution(self):
        repo = self.root / "history"
        repo.mkdir()

        def git(*args):
            return subprocess.check_output(["git", "-C", str(repo), *args], stderr=subprocess.STDOUT).decode().strip()

        git("init", "-b", "main")
        (repo / "LICENSE").write_text("MIT test fixture license", encoding="utf-8")
        for version in ("before", "after"):
            shutil.copyfile(self.case_dir / version / "cafe.py", repo / "cafe.py")
            git("add", "cafe.py", "LICENSE")
            git("-c", "user.name=RepoQuest test", "-c", "user.email=test@example.invalid", "-c", "commit.gpgsign=false", "commit", "-m", version)
        head = git("rev-parse", "HEAD")
        path = import_git(repo, "HEAD^", "HEAD", ["cafe.py"], self.case_dir / "contract.py",
                          "LICENSE", "MIT", "Self-authored integration fixture", self.root / "imported")
        manifest = json.loads(path.read_text())
        self.assertEqual(manifest["provenance"]["after_commit"], head)
        self.assertEqual(git("rev-parse", "HEAD"), head)
        self.assertEqual(git("status", "--porcelain"), "")
        self.assertEqual((path.parent / "before/cafe.py").read_bytes(), (self.case_dir / "before/cafe.py").read_bytes())
        with self.assertRaisesRegex(QuestError, "title must"):
            load_case(path)
        curated = json.loads(self.path.read_text())
        curated["provenance"] = manifest["provenance"]
        path.write_text(json.dumps(curated))
        report = verify(path, True)
        self.assertEqual(report["after"]["tests"], 4)
        self.assertIn(head, render(path))
        with self.assertRaisesRegex(QuestError, "already exists"):
            import_git(repo, "HEAD^", "HEAD", ["cafe.py"], self.case_dir / "contract.py",
                       "LICENSE", "MIT", "Fixture", path.parent)


if __name__ == "__main__":
    unittest.main()
