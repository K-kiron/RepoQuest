"""Read selected Git blobs without checkout, hooks, or repository code execution."""

from pathlib import Path
import json
import subprocess

from .core import QuestError, relative_path, require


def git(repo, *args):
    try:
        result = subprocess.run(["git", "--no-replace-objects", "-C", str(repo), *args],
                                capture_output=True, timeout=15)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise QuestError(f"Cannot read Git repository: {exc}") from exc
    if result.returncode:
        raise QuestError("Git read failed: " + result.stderr.decode("utf-8", errors="replace")[:1000])
    return result.stdout


def resolve(repo, revision):
    require(isinstance(revision, str) and not revision.startswith("-"), "Invalid Git revision")
    return git(repo, "rev-parse", "--verify", "--end-of-options", revision + "^{commit}").decode().strip()


def blob(repo, revision, path):
    relative_path(path)
    listing = git(repo, "ls-tree", "-z", revision, "--", path).decode("utf-8")
    require(listing.startswith(("100644 blob ", "100755 blob ")), f"Expected regular Git file: {path}")
    oid = listing.split("\t")[0].split()[2]
    require(int(git(repo, "cat-file", "-s", oid)) <= 1_000_000, f"Git file exceeds 1 MB: {path}")
    data = git(repo, "cat-file", "blob", oid)
    try:
        data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise QuestError(f"Git file is not UTF-8: {path}") from exc
    return data


def import_git(repo, before, after, files, contract, license_file, license_name, origin, output):
    """Import bytes and a draft. The author must curate the narrative before verification."""
    output = Path(output).resolve()
    require(not output.exists(), "Import destination already exists; choose a new directory")
    require(1 <= len(files) <= 20 and len({p.lower() for p in files}) == len(files), "Select 1–20 unique Python files")
    require(all(relative_path(p).endswith(".py") and not p.startswith("__rq_") for p in files), "Select Python files only")
    require(bool(license_name.strip()) and bool(origin.strip()), "Provide license name and source attribution")
    revisions = {"before": resolve(repo, before), "after": resolve(repo, after)}
    require(revisions["before"] != revisions["after"], "Select two different commits")
    data = {}
    for version, revision in revisions.items():
        for file in files:
            data[f"{version}/{file}"] = blob(repo, revision, file)
        data[f"{version}-LICENSE.txt"] = blob(repo, revision, license_file)
    contract = Path(contract)
    require(contract.is_file() and contract.stat().st_size <= 1_000_000, "Provide a UTF-8 contract of at most 1 MB")
    data["contract.py"] = contract.read_bytes()
    data["contract.py"].decode("utf-8")
    require(any(data[f"before/{p}"] != data[f"after/{p}"] for p in files), "Selected files did not change")
    draft = {"schema": 1, "id": "imported-quest", "title": "", "brief": "", "brief_refs": [],
             "objective": "Identify the responsible function and explain the failing behavior.",
             "provenance": {"kind": "git-import", "origin": origin, "license": license_name,
                            "license_files": ["before-LICENSE.txt", "after-LICENSE.txt"],
                            "before_commit": revisions["before"], "after_commit": revisions["after"]},
             "files": files, "contract": "contract.py", "evidence": [], "suspects": [], "hints": [],
             "solution": {"function": "", "text": "", "refs": []}}
    # Validate all reads first, so a failed import never leaves a plausible draft.
    output.mkdir(parents=True)
    for name, content in data.items():
        destination = output / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
    (output / "case.json").write_text(json.dumps(draft, indent=2) + "\n", encoding="utf-8")
    return output / "case.json"
