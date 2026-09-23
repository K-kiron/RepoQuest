# Verification scope

This record describes the 0.1.0 verification scope. It is evidence of the checked paths, not a benchmark of learning outcomes or model quality.

## Observed environment

Local checks used Windows, Python 3.11.5, Git 2.42.0; Codex CLI 0.147.0 for skill discovery; and the Codex in-app Chromium browser for rendered interaction checks. The [hosted CI records](https://github.com/K-kiron/RepoQuest/actions/workflows/ci.yml) show results for Python 3.10 and 3.13 on Ubuntu and Windows, plus installation through the Skills CLI.

## Core paths

Run from the repository root:

```sh
python -m unittest discover -s tests -v
python skills/repoquest/scripts/quest.py check examples/borrowed-menu/case.json
python skills/repoquest/scripts/quest.py verify examples/borrowed-menu/case.json --trust-code
python skills/repoquest/scripts/quest.py build examples/borrowed-menu/case.json --output demo/index.html
```

The test suite covers actual subprocess execution, the common contract, stale-input rejection, unsafe paths, invalid line citations, case collisions, missing trust acknowledgement, failing fixes, passing before versions, import errors, test errors, empty suites, skips, different executed tests, timeouts, escaped markup, and Git import from locally created commits.

The included cafe fixture ran four tests per snapshot: two assertion failures before, four passing tests after. Exact logs and SHA-256 inputs are in [`verification.json`](../examples/borrowed-menu/verification.json). Generated HTML includes those logs and cited excerpts.

A separate forward-test used a different self-authored bug: an explicitly configured zero-retry value fell back to the default. Two local commits were imported, the draft was manually curated using the skill, and the resulting contract produced one failing assertion before and three passes after. Mutating any manifest, code, contract, or license input invalidated its report. This verifies the commit-import workflow; it is not evidence about a third-party historical incident or a controlled skill-versus-prompt comparison.

## Installation

The full skill folder was copied into a fresh temporary project's `.agents/skills/repoquest`. Codex's `skills/list` returned exactly one enabled `repoquest` with repository scope and the copied `SKILL.md` path. The copied helper successfully checked the bundled case. No global skill installation was needed.

Skills CLI 1.7.0 was also run against the local repository in an isolated project with `--skill repoquest --agent codex --copy --yes`. It found and installed one skill; the installed helper checked the bundled case. The distribution test builds the ZIP twice, compares bytes, verifies checksums, extracts it, and builds the demo through the extracted helper.

A wheel was built locally with `pip install . --no-build-isolation --no-deps --target <temporary-directory>`. Importing the installed package and rendering the bundled case succeeded, including access to its packaged HTML template. The primary supported path remains the dependency-free portable script. Other agent hosts were not tested.

## Browser checks

The generated page was served on a loopback-only ephemeral port. Desktop and 390-pixel mobile viewport checks covered:

- Zero hint entries and an empty, hidden solution region on initial load.
- Enter to open exactly one hint at a time; the button disables after the final hint.
- Keyboard selection of a candidate and scratchpad entry.
- Reveal dialog focuses “Keep investigating”; Escape cancels without showing an answer.
- Explicit confirmation renders the patch, the two-failing/four-passing result, and passing test log; focus moves to the solution heading.
- All observed citation anchors resolve; source line numbers are linked.
- Mobile document width equals viewport content width after fixing grid overflow, both before and after reveal.
- No captured browser warnings or errors during the desktop interaction flow.

The in-app browser's URL policy blocked direct `file://` navigation. That browser path was not bypassed or verified; browser interactions used the existing localhost page. The generated artifact embeds all assets and requires no fetches, external fonts, modules, or server APIs, but direct file opening still needs a manual check in a browser that permits local files.

[`demo/preview.png`](../demo/preview.png) is a captured browser image of the initial case. To repeat the manual browser checks, open the demo and walk through the controls above. The scratchpad intentionally resets on reload.

## Remaining limits

Execution inherits the invoking user's local access. The timeout does not provide process-tree, filesystem, network, or memory isolation. Use a separately managed disposable environment for untrusted cases. Reports are local integrity records, not signed attestations; the narrative and license declaration require author review. No third-party case evaluation or measured skill uplift is claimed.
