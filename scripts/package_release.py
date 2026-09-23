"""Package the tracked skill and verified demo; never run case code or publish."""

import hashlib
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/repoquest/scripts"))
from repoquest import __version__
from repoquest.core import QuestError
from repoquest.render import render


def package_release(root, destination):
    root, destination = Path(root).resolve(), Path(destination).resolve()
    skill = root / "skills/repoquest"
    tracked = subprocess.check_output(["git", "-C", str(root), "ls-files", "-z", "--", "skills/repoquest"])
    paths = [Path(p) for p in tracked.decode("utf-8").split("\0") if p]
    names = {p.relative_to("skills").as_posix() for p in paths}
    required = {"repoquest/SKILL.md", "repoquest/LICENSE.txt", "repoquest/scripts/quest.py",
                "repoquest/scripts/repoquest/page.html", "repoquest/references/case-format.md"}
    if not required <= names:
        raise QuestError("Required skill files are not tracked; inspect and stage them before packaging")
    page = render(root / "examples/borrowed-menu/case.json")
    destination.mkdir(parents=True, exist_ok=True)
    archive_path = destination / f"repoquest-skill-{__version__}.zip"
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(paths):
            source = root / path
            if source.is_symlink() or not source.resolve().is_relative_to(skill.resolve()):
                raise QuestError(f"Skill files must be regular in-tree files: {path}")
            info = zipfile.ZipInfo(path.relative_to("skills").as_posix(), date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, source.read_bytes())
    demo_path = destination / f"repoquest-demo-{__version__}.html"
    demo_path.write_bytes(page.encode("utf-8"))
    artifacts = [archive_path, demo_path]
    wheel = destination / f"repoquest-{__version__}-py3-none-any.whl"
    if wheel.is_file():
        artifacts.append(wheel)
    checksum_path = destination / "SHA256SUMS"
    checksum_path.write_bytes(''.join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n" for p in artifacts).encode("ascii"))
    return [*artifacts, checksum_path]


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    try:
        for artifact in package_release(ROOT, args.output):
            print(artifact)
    except (QuestError, OSError, subprocess.CalledProcessError) as exc:
        parser.exit(2, f"package-release: {exc}\n")
