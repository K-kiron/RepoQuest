# Case format (schema 1)

Each case is a directory with `case.json`, `before/`, `after/`, a common Python contract, and license notices. Both snapshot directories contain the same 1–20 selected UTF-8 `.py` paths. Include local imports and package `__init__.py` files. Only selected files are copied into the execution directory. Data files, dependency installation, arbitrary commands, and automatic history mining are outside this version.

The manifest fields are:

| Field | Meaning |
|---|---|
| `schema` | The integer `1` |
| `id`, `title` | Stable lowercase slug and reader-facing title |
| `brief`, `brief_refs` | Incident narrative and supporting evidence IDs |
| `objective` | What the investigator should locate and explain |
| `provenance` | `kind`: `self-authored` or `git-import`; `origin`: truthful attribution; `license`: declared license; `license_files`: 1–4 preserved text files |
| `provenance.before_commit`, `after_commit` | Full Git object IDs, required for imports |
| `files` | Relative Python file paths present in both snapshots |
| `contract` | Path to the single shared `unittest` module |
| `evidence` | 1–40 objects: unique slug `id`, `label`, `path`, inclusive one-based `start` and `end` lines. Paths must be a before file or the common contract |
| `suspects` | 2–6 objects with `name` and evidence `ref`; names are manually checked against source |
| `hints` | 1–5 objects with `text` and evidence `refs`, ordered from gentle to explicit |
| `solution` | Responsible candidate `function`, root-cause `text`, and evidence `refs` |

Use plain text in every narrative field; HTML is escaped. Citations validate locations, not the truth of an explanation. Review the narrative against the raw source. Prefer deterministic, small tests with clear normal and failure paths. Do not skip tests or mark expected failures. The runner loads the contract as `quest_contract`, discovers `unittest.TestCase` classes, and executes them in both snapshots using the same interpreter. It does not run a module's `if __name__ == '__main__'` block.

## Import a fixed bug from local Git history

```text
python <skill>/scripts/quest.py import-git <repo> --before <parent-sha> --after <fix-sha> --file module.py --contract <contract.py> --license-file LICENSE --license-name MIT --origin "Project name; source URL; case attribution" --output <new-case-directory>
```

Repeat `--file` for local imports. The destination must not exist. Files are read directly from regular Git blobs, with no checkout or hooks. Preserve license notices from both commits. If extra copyright/NOTICE files are required, add them and list them in `license_files` before sharing. The declared license label is supplied by the author and is not legal clearance.

The generated manifest deliberately has empty narrative fields and fails `check` until curated. Fill the brief, evidence ranges, candidates, hints, and explanation by inspecting the imported files. Then:

```text
python <skill>/scripts/quest.py check <case.json>
python <skill>/scripts/quest.py verify <case.json> --trust-code
python <skill>/scripts/quest.py build <case.json> --output <quest.html>
```

`verify` writes `verification.json` after both runs meet the contract. Its SHA-256 map covers the exact manifest, code, contract, and license bytes. `build` refuses missing or stale records. Reports are local records, not signed attestations; trusted code can interfere with its runner. Review stdout for sensitive information before sharing the generated HTML.
