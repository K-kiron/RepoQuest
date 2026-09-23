# Releasing RepoQuest

Releases contain a portable skill ZIP, standalone HTML demo, Python wheel, and `SHA256SUMS`. The GitHub source archive contains the full examples and tests. Python packages are distributed through GitHub releases; no PyPI publication is configured.

## Build and inspect

Start from a clean checkout of the intended release commit. Run the tests and review the exact source and case notices before building:

```sh
python -m unittest discover -s tests -v
python skills/repoquest/scripts/quest.py build examples/borrowed-menu/case.json --output demo/index.html
python -m pip wheel . --no-deps --wheel-dir dist
python scripts/package_release.py
```

The packager includes only Git-tracked files under `skills/repoquest`, preserves their paths and license, and excludes untracked caches or working notes. It renders the demo from the current verified case. Archive member timestamps are fixed so unchanged skill bytes produce the same ZIP. If the matching wheel exists in the output directory, it is included in `SHA256SUMS`; otherwise the manifest covers the ZIP and HTML only.

Extract the skill ZIP into a fresh project and run its helper. Install the wheel into a fresh virtual environment and build the same case. Review the HTML in a browser and verify the checksums. The CI workflow performs behavior and distribution checks across Windows and Linux.

If case source or metadata changes, re-run `verify --trust-code` after reviewing the code, then build the demo. Commit the updated case, record, and demo together. Do not edit evidence logs to obtain a desired outcome.

## Publish

Publication is a maintainer action. After the intended commit passes hosted CI, tag that exact commit and publish the four release assets. Release notes should describe concrete behavior, verification scope, and known limitations. Do not infer learning gains from the fixture tests.

The Pages workflow publishes the committed `demo/` directory from `main`. It requires GitHub Pages to use GitHub Actions as its source. Changes to the generated demo trigger a deployment; documentation-only commits can leave the existing demo unchanged.

After publication, verify the public README, demo, release downloads, and the actual install command in an empty project:

```sh
npx skills add K-kiron/RepoQuest --skill repoquest --agent codex --copy --yes
```

Keep the package version in `pyproject.toml` and `skills/repoquest/scripts/repoquest/__init__.py` aligned. Never replace assets under an existing release tag to silently change a published version.
