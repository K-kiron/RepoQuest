# RepoQuest

**Read the code. Follow the evidence. Solve the bug.**

RepoQuest turns a fixed Python bug into a playable debugging mystery. Authors use an **Agent Skill or Python CLI** to curate code, clues, and a shared test contract into **one offline HTML case file**. Players investigate the failure before revealing the fix.

[![Verify quests](https://github.com/K-kiron/RepoQuest/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/K-kiron/RepoQuest/actions/workflows/ci.yml)
[![MIT license](https://img.shields.io/badge/license-MIT-194f41)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-194f41)](pyproject.toml)

**[Play the demo →](https://k-kiron.github.io/RepoQuest/)** · **[Install the skill](#install-the-skill)** · **[Create a case](#make-another-case)** · **[Download v0.1.0](https://github.com/K-kiron/RepoQuest/releases/tag/v0.1.0)**

<a href="https://k-kiron.github.io/RepoQuest/">
  <picture>
    <source media="(max-width: 600px)" srcset="docs/assets/overview-mobile.svg">
    <img src="docs/assets/overview.svg" width="100%" alt="RepoQuest workflow: prepare before and after code with one test contract; investigate cited code, failing tests, and progressive hints; reveal the exact patch and passing tests. Share the case as one offline HTML file.">
  </picture>
</a>

*Workflow overview. [Open the interactive case](https://k-kiron.github.io/RepoQuest/) to use the evidence, hints, and reveal controls.*

## What you can do

1. **Prepare a case.** Supply broken and fixed Python snapshots, one shared `unittest` contract, and source/license details. Curate the story, cited excerpts, candidate functions, and hints. Verify the reproduction, then build the HTML.
2. **Investigate the bug.** Read the failing test log and source excerpts. Follow file and line citations, choose a candidate function, and write a theory. Open progressively stronger hints when needed.
3. **Reveal the explanation.** Confirm when ready to see the responsible function, exact patch, and the same tests passing after the fix. Compare the explanation with your reasoning.

**For players:** a browser is enough. Downloaded cases need no account, installation, server, or network connection. **For authors:** Python 3.10+ is required; the portable CLI has no third-party dependencies.

## Play the first case

### Who ordered the extra cake?

A customer's special order appears on the next customer's receipt. Follow the requests, inspect the code, and find what crossed the counter. Allow about five minutes; there is no timer.

| The case | The evidence |
|---|---|
| Original, fictional cafe scenario | Reproducible Python behavior, not a historical third-party incident |
| Four behavior tests, unchanged across snapshots | **Before: 2 failures / 4 tests. After: 4 passes / 4 tests.** |
| Source, contract, manifest, and license | Exact bytes bound by the captured [verification record](examples/borrowed-menu/verification.json) |

**[Start the investigation →](https://k-kiron.github.io/RepoQuest/)** or download `repoquest-demo-0.1.0.html` from the [release](https://github.com/K-kiron/RepoQuest/releases/tag/v0.1.0). The repository's [demo/index.html](demo/index.html) contains the same case; GitHub's file viewer does not execute it.

## Install the skill

From the project where you want to use RepoQuest, run:

```sh
npx skills add K-kiron/RepoQuest --skill repoquest --agent codex
```

Then start a fresh task in that project:

```text
Use $repoquest to turn this fixed Python bug into a debugging mystery.
Use the before and after snapshots in <case-directory> and preserve their provenance.
```

The [Skills CLI](https://github.com/vercel-labs/skills) needs Node.js; RepoQuest's helper needs Python 3.10+. To install without Node.js, extract the release's `repoquest` skill folder into your project's `.agents/skills/` directory. Installation and discovery have been tested with Codex. Other hosts have not been validated.

## Run it locally

Requires Python 3.10+. The portable script has **no third-party dependencies**. Run these commands from this repository:

```sh
python skills/repoquest/scripts/quest.py check examples/borrowed-menu/case.json
python skills/repoquest/scripts/quest.py verify examples/borrowed-menu/case.json --trust-code
python skills/repoquest/scripts/quest.py build examples/borrowed-menu/case.json --output demo/index.html
```

The included fixture is small enough to inspect before executing. `check` and `build` never execute case code. `verify` executes both snapshots and the shared contract locally; `--trust-code` acknowledges that execution. It is **not a security sandbox**.

For an optional CLI installation inside your own virtual environment:

```sh
python -m pip install .
repoquest --help
```

The package contains the same renderer and CLI as the portable skill. No package has been published to a registry.

<details>
<summary>Manual installation from a clone (including PowerShell)</summary>

Copy the **entire** `skills/repoquest` directory into a target project's `.agents/skills/` directory. Keep `SKILL.md`, `scripts/`, `references/`, and `agents/` together.

PowerShell, from this repository:

```powershell
$target = 'C:\path\to\your-project\.agents\skills'
New-Item -ItemType Directory -Force -Path $target | Out-Null
Copy-Item -Recurse -LiteralPath .\skills\repoquest -Destination $target
```

Use a destination without an existing `repoquest` skill; review an existing installation before replacing it. Start a fresh Codex task in that project and invoke:

```text
Use $repoquest to turn this fixed Python bug into a debugging quest.
Use the before and after snapshots in <case-directory> and preserve their provenance.
```

The [skill entry point](skills/repoquest/SKILL.md) tells the agent how to select evidence, curate hints, run the verifier, and check the resulting page. Current host verification is recorded in [docs/verification.md](docs/verification.md).

</details>

## Make another case

Copy `examples/borrowed-menu` to a new local directory. Replace the before/after Python files and common `unittest` contract. Update the title, source attribution, line ranges, candidate functions, hints, and root-cause explanation in `case.json`. Then run `check`, `verify`, and `build` against the new manifest. The previous verification record is rejected as soon as an input changes.

To import a real pair of local Git commits without checking them out or running their code:

```sh
python skills/repoquest/scripts/quest.py import-git /path/to/repo --before PARENT_SHA --after FIX_SHA --file package/module.py --file package/__init__.py --contract /path/to/contract.py --license-file LICENSE --license-name MIT --origin "Project name, source URL, and case attribution" --output /path/to/new-case
```

The importer preserves selected regular Git blobs, full commit IDs, and license text from both revisions. It creates an intentionally incomplete manifest. Curate its narrative and line citations before verification. Include every local import required by the selected code. See the complete [case format](skills/repoquest/references/case-format.md).

## What the first version guarantees

- The verifier requires actual assertion failures before the fix and a passing, nonempty suite after it, with matching test IDs. Import errors, skips, and timeouts cannot count as a reproduced bug.
- Evidence excerpts come from specific fixture paths and line ranges. Changed inputs invalidate the verification record.
- Hints appear sequentially. A confirmation step protects the patch reveal. Native controls support keyboard use, and the page adapts to narrow screens.
- Generated pages escape case text, make no network requests, and contain their code, logs, styling, and interaction script in one file.

These checks validate a curated reproduction, not a universal root-cause claim. Authors still need to review the narrative, licensing, and completeness of their contract. Reports are not signed attestations. The answer is embedded in the HTML and can be found by inspecting its source; this is a learning game, not an anti-cheating system. Scratchpad notes are neither transmitted nor persisted.

The first version supports small Python cases using the standard library. It does not install case dependencies, mine arbitrary repository history, run remote code, or promise measured learning or productivity improvements. Unknown code belongs in a separately managed disposable environment; the timeout is not a process-tree or resource sandbox.

## Maintain and verify

```sh
python -m unittest discover -s tests -v
```

Tests exercise the real before/after path, local Git commit import, execution consent, stale evidence, invalid citations, failure classification, timeout handling, and escaping. See [verification scope](docs/verification.md) for the observed environment and browser checks. To refresh the committed demo after changing case inputs, run `verify` followed by `build`.

Contributions should improve a complete investigation or add a reproducible case. See [CONTRIBUTING.md](CONTRIBUTING.md), the [case proposal form](https://github.com/K-kiron/RepoQuest/issues/new?template=case-proposal.yml), and the [changelog](CHANGELOG.md). Release artifacts can be rebuilt with [the release instructions](docs/releasing.md).

Related work: [codebase-to-course](https://github.com/zarazhangrui/codebase-to-course) turns repositories into interactive courses. RepoQuest focuses on one reproducible failure, cited reasoning, and a verified patch reveal. Its implementation and skill text are original.

Repository organization draws on the self-contained skills in [anthropics/skills](https://github.com/anthropics/skills), the installation and distribution approach of [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills), and the explicit host guidance in [obra/superpowers](https://github.com/obra/superpowers). References describe design influences, not endorsements.

Licensed under [MIT](LICENSE). Imported cases retain their original notices and may have different redistribution terms.
