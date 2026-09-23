# Contributing

Useful contributions make a small debugging investigation more reliable, accessible, or interesting. Start with an issue for a new feature or case so the intended behavior and scope can be discussed. Small corrections can go directly to a pull request.

## Local development

Python 3.10+ and Git are sufficient for the portable CLI and tests. The runtime has no third-party Python dependencies.

```sh
python -m unittest discover -s tests -v
python skills/repoquest/scripts/quest.py check examples/borrowed-menu/case.json
python skills/repoquest/scripts/quest.py verify examples/borrowed-menu/case.json --trust-code
python skills/repoquest/scripts/quest.py build examples/borrowed-menu/case.json --output demo/index.html
```

Use `--trust-code` only after reviewing the code being executed. This harness is not a sandbox.

The skill's source lives in `skills/repoquest/`. Its `scripts/repoquest` package is also the source of the optional Python wheel. Keep the portable copy functional without installation. The single-file page template is `scripts/repoquest/page.html`; regenerate the demo after changing it.

## New cases

Submit one narrow, reproducible failure with:

- Before and after Python snapshots, one unchanged `unittest` behavior contract, and accurate line citations.
- Failing assertions before the fix and a passing suite after it, using the same tests.
- Source attribution and complete applicable license notices. Include full commit IDs for imported history.
- A brief without spoilers, plausible function candidates, progressive hints, and an explanation grounded in the evidence.
- A clear `self-authored` label for fictional teaching incidents. Do not present them as third-party history.

Use the [case format](skills/repoquest/references/case-format.md). Do not include private source code, personal data, credentials, production logs, or material that cannot be redistributed. A case proposal can describe the failure without submitting source material.

## Pull requests

Describe the problem, resulting behavior, and the checks actually run. Link the relevant issue with `Closes #N` when the change resolves it. Add regression tests for observable failures. For UI changes, check keyboard navigation, spoiler visibility, and narrow-screen layout in a browser. Keep temporary plans and investigation notes outside the repository.

Use precise, respectful English in public project documentation and discussions. Maintain truthful compatibility and evaluation claims. A passing curated case is not proof of learning gains or universal bug-diagnosis quality.
