"""Validate curated evidence and capture the same contract against two snapshots."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone


class QuestError(ValueError):
    """An actionable input, evidence, or execution error."""


def relative_path(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_./-]+", value):
        raise QuestError(f"Unsafe relative path: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or str(path) != value or any(p in (".", "..", ".git") for p in path.parts):
        raise QuestError(f"Unsafe relative path: {value!r}")
    for part in path.parts:
        if part.endswith(".") or re.fullmatch(r"(?i)(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?", part):
            raise QuestError(f"Nonportable path: {value!r}")
    return value


def read_file(root, relative):
    relative_path(relative)
    root = root.resolve()
    path = root / relative
    if any(p.is_symlink() for p in [path, *path.parents] if p != root and root in p.parents):
        raise QuestError(f"Symlinks are not supported: {relative}")
    if not path.resolve().is_relative_to(root) or not path.is_file():
        raise QuestError(f"Missing or escaped file: {relative}")
    if path.stat().st_size > 1_000_000:
        raise QuestError(f"File exceeds 1 MB: {relative}")
    raw = path.read_bytes()
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise QuestError(f"Expected UTF-8 text: {relative}") from exc
    return raw


def require(condition, message):
    if not condition:
        raise QuestError(message)


def text_field(value, label):
    require(isinstance(value, str) and bool(value.strip()), f"{label} must be nonempty text")
    return value


def load_case(path):
    path = Path(path).resolve()
    raw = read_file(path.parent, path.name)
    try:
        case = json.loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise QuestError("case.json must contain valid UTF-8 JSON") from exc
    require(isinstance(case, dict) and case.get("schema") == 1, "Expected case schema 1")
    for key in ("id", "title", "brief", "objective"):
        text_field(case.get(key), key)
    require(re.fullmatch(r"[a-z0-9-]+", case["id"]), "id must use lowercase letters, digits, and hyphens")
    files = case.get("files")
    require(isinstance(files, list) and 0 < len(files) <= 20, "files must contain 1–20 Python paths")
    require(all(isinstance(p, str) for p in files), "files must contain text paths")
    require(len({p.lower() for p in files}) == len(files), "Duplicate or case-colliding file paths")
    blobs = {path.name: raw}
    for file in files:
        relative_path(file)
        require(file.endswith(".py") and not file.startswith("__rq_"), "Only Python source files are supported")
        for version in ("before", "after"):
            name = f"{version}/{file}"
            blobs[name] = read_file(path.parent, name)
    contract = relative_path(case.get("contract"))
    require(contract.endswith(".py") and contract not in blobs, "Use a separate Python contract")
    blobs[contract] = read_file(path.parent, contract)
    provenance = case.get("provenance", {})
    require(isinstance(provenance, dict), "provenance must be an object")
    require(provenance.get("kind") in ("self-authored", "git-import"), "Declare self-authored or git-import provenance")
    for key in ("origin", "license"):
        text_field(provenance.get(key), f"provenance.{key}")
    notices = provenance.get("license_files")
    require(isinstance(notices, list) and 0 < len(notices) <= 4, "Preserve 1–4 license/notice files")
    for name in notices:
        relative_path(name)
        require(name not in blobs, "License paths must be separate from code and manifest")
        blobs[name] = read_file(path.parent, name)
    require("verification.json" not in {name.casefold() for name in blobs},
            "verification.json is reserved for generated evidence; do not use it as an input")
    if provenance["kind"] == "git-import":
        for key in ("before_commit", "after_commit"):
            require(re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", str(provenance.get(key, ""))), f"Missing full {key}")
    evidence = case.get("evidence")
    require(isinstance(evidence, list) and 0 < len(evidence) <= 40, "Provide 1–40 evidence excerpts")
    ids = set()
    for item in evidence:
        require(isinstance(item, dict), "Each evidence excerpt must be an object")
        eid = item.get("id", "")
        require(isinstance(eid, str) and re.fullmatch(r"[a-z][a-z0-9-]*", eid) and eid not in ids, "Evidence IDs must be unique slugs")
        ids.add(eid)
        text_field(item.get("label"), "evidence.label")
        require(item.get("path") in [f"before/{p}" for p in files] + [contract], "Public evidence must reference before code or the common contract")
        lines = blobs[item["path"]].decode("utf-8").splitlines()
        start, end = item.get("start"), item.get("end")
        require(type(start) is int and type(end) is int and 1 <= start <= end <= len(lines), "Evidence line range is outside its source")

    def refs(values):
        require(isinstance(values, list) and values and all(isinstance(v, str) and v in ids for v in values), "Every claim must cite existing evidence IDs")

    refs(case.get("brief_refs"))
    hints = case.get("hints")
    require(isinstance(hints, list) and 1 <= len(hints) <= 5, "Provide 1–5 progressive hints")
    solution = case.get("solution")
    require(isinstance(solution, dict), "Provide a solution object")
    text_field(solution.get("function"), "solution.function")
    for item in [*hints, solution]:
        require(isinstance(item, dict), "Hints and solution must be objects")
        text_field(item.get("text"), "hint/solution.text")
        refs(item.get("refs"))
    suspects = case.get("suspects")
    require(isinstance(suspects, list) and 2 <= len(suspects) <= 6, "Provide 2–6 candidate functions")
    for suspect in suspects:
        require(isinstance(suspect, dict), "Each suspect must be an object")
        text_field(suspect.get("name"), "suspect.name")
        require(isinstance(suspect.get("ref"), str) and suspect["ref"] in ids, "Suspects must cite an evidence ID")
    names = [s["name"] for s in suspects]
    require(len(set(names)) == len(names) and solution["function"] in names, "Solution must match a unique candidate function")
    require(any(blobs[f"before/{p}"] != blobs[f"after/{p}"] for p in files), "Before and after snapshots are identical")
    return case, blobs


def fingerprint(blobs):
    return {path: hashlib.sha256(data).hexdigest() for path, data in sorted(blobs.items())}


# This is an execution harness, not a sandbox. Only trusted inputs may reach it.
RUNNER = r'''
import contextlib, importlib.util, io, json, pathlib, sys, unittest
root, destination = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
sys.path.insert(0, str(root))
stream = io.StringIO()
class Result(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ids = []
    def startTest(self, test):
        self.ids.append(test.id())
        super().startTest(test)
with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
    spec = importlib.util.spec_from_file_location("quest_contract", root / "__rq_contract__.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    suite = unittest.defaultTestLoader.loadTestsFromModule(module)
    result = unittest.TextTestRunner(stream=stream, verbosity=2, resultclass=Result).run(suite)
destination.write_text(json.dumps({
    "tests": result.testsRun, "test_ids": result.ids,
    "failures": [test.id() for test, _ in result.failures],
    "errors": [test.id() for test, _ in result.errors],
    "skipped": len(result.skipped), "expected_failures": len(result.expectedFailures),
    "unexpected_successes": len(result.unexpectedSuccesses), "log": stream.getvalue()
}), encoding="utf-8")
'''


def run_snapshot(case, blobs, version, timeout):
    with tempfile.TemporaryDirectory(prefix="repoquest-run-") as directory:
        root = Path(directory)
        snapshot = root / "snapshot"
        snapshot.mkdir()
        for file in case["files"]:
            target = snapshot / file
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(blobs[f"{version}/{file}"])
        (snapshot / "__rq_contract__.py").write_bytes(blobs[case["contract"]])
        runner, result_path = root / "runner.py", root / "result.json"
        runner.write_text(RUNNER, encoding="utf-8")
        try:
            proc = subprocess.run([sys.executable, "-I", str(runner), str(snapshot), str(result_path)],
                                  cwd=snapshot, capture_output=True, timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            raise QuestError(f"{version}: contract timed out after {timeout:g}s; no verified result") from exc
        if proc.returncode != 0 or not result_path.exists():
            detail = proc.stderr.decode("utf-8", errors="replace")[-2000:]
            raise QuestError(f"{version}: contract/harness error, not a reproduced assertion failure:\n{detail}")
        result = json.loads(result_path.read_text(encoding="utf-8"))
        # Temporary paths are irrelevant to the portable evidence.
        result["log"] = result["log"].replace(str(snapshot), "<snapshot>")
        return result


def validate_results(report):
    try:
        for key in ("captured_at", "python", "platform"):
            text_field(report.get(key), f"verification.{key}")
        before, after = report["before"], report["after"]
        for label, result in (("before", before), ("after", after)):
            require(isinstance(result, dict), f"{label}: malformed test result")
            text_field(result.get("log"), f"{label}.log")
            require(type(result["tests"]) is int and result["tests"] > 0, f"{label}: no tests ran")
            for key in ("test_ids", "failures", "errors"):
                require(isinstance(result[key], list) and all(isinstance(v, str) for v in result[key]),
                        f"{label}: malformed {key}")
            require(len(result["test_ids"]) == result["tests"], f"{label}: test count does not match IDs")
            for key in ("skipped", "expected_failures", "unexpected_successes"):
                require(type(result[key]) is int and result[key] >= 0, f"{label}: malformed {key}")
            require(not result["errors"], f"{label}: test errors do not count as a reproduced bug")
            require(not any(result[k] for k in ("skipped", "expected_failures", "unexpected_successes")), f"{label}: skipped or expected-failure tests cannot verify a quest")
        require(before["failures"], "before: expected an assertion failure, but all tests passed")
        require(not after["failures"], "after: the behavior contract still fails")
        require(before["test_ids"] == after["test_ids"] and before["tests"] == after["tests"], "Both snapshots must execute the same tests")
    except (KeyError, TypeError) as exc:
        raise QuestError("Malformed verification report; run verify again") from exc


def verify(path, trust_code=False, timeout=10):
    require(trust_code, "Execution is disabled. Review source and contract, then pass --trust-code. This is not a sandbox.")
    require(0 < timeout <= 120, "timeout must be greater than 0 and at most 120 seconds")
    case, blobs = load_case(path)
    report = {"schema": 1, "case_id": case["id"], "inputs": fingerprint(blobs),
              "captured_at": datetime.now(timezone.utc).isoformat(),
              "python": sys.version.split()[0], "platform": sys.platform}
    for version in ("before", "after"):
        report[version] = run_snapshot(case, blobs, version, timeout)
    validate_results(report)
    destination = Path(path).resolve().parent / "verification.json"
    require(not destination.is_symlink(), "verification.json must not be a symlink")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n",
                                         dir=destination.parent, prefix=".repoquest-",
                                         suffix=".json", delete=False) as handle:
            temporary = Path(handle.name)
            json.dump(report, handle, indent=2)
            handle.write("\n")
        # Replacing the directory entry never truncates a hard-linked target.
        temporary.replace(destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return report


def load_verified(path):
    case, blobs = load_case(path)
    try:
        report = json.loads(read_file(Path(path).resolve().parent, "verification.json"))
    except (OSError, ValueError) as exc:
        raise QuestError("Missing or invalid verification.json; run verify first") from exc
    require(isinstance(report, dict) and report.get("schema") == 1, "Unsupported verification report")
    require(report.get("case_id") == case["id"] and report.get("inputs") == fingerprint(blobs), "Evidence changed since verification; run verify again")
    validate_results(report)
    return case, blobs, report
