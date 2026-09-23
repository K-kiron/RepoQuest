"""One portable HTML file, without external assets or runtime dependencies."""

import base64
import difflib
from html import escape
import json
from pathlib import Path

from .core import load_verified


def e(value):
    return escape(str(value), quote=True)


def refs(ids):
    return ' '.join(f'<a class="ref" href="#e-{e(i)}">{e(i)}</a>' for i in ids)


def code_block(text, start=1, prefix="line"):
    lines = text.splitlines()
    content = ''.join(f'<span class="line" id="{e(prefix)}-{n}"><a class="ln" href="#{e(prefix)}-{n}" aria-label="Line {n}">{n}</a><code>{e(line)}</code></span>' for n, line in enumerate(lines, start))
    return '<pre class="code" tabindex="0" aria-label="Source code, scroll horizontally if needed">' + content + '</pre>'


def render(path):
    case, blobs, report = load_verified(path)
    source = case["provenance"]
    cards = []
    for item in case["evidence"]:
        lines = blobs[item["path"]].decode("utf-8").splitlines()
        snippet = '\n'.join(lines[item["start"] - 1:item["end"]])
        cards.append(f'<article class="evidence" id="e-{e(item["id"])}"><div class="evidence-head"><span class="eyebrow">{e(item["id"])}</span><h3>{e(item["label"])}</h3><p class="file">{e(item["path"])} : {item["start"]}–{item["end"]}</p></div>{code_block(snippet, item["start"], item["id"])}<p class="checksum">SHA-256 {report["inputs"][item["path"]]}</p></article>')
    suspects = ''.join(f'<label class="suspect"><input type="radio" name="suspect" value="{e(s["name"])}"><span>{e(s["name"])}</span><a href="#e-{e(s["ref"])}" aria-label="Evidence for {e(s["name"])}">↗</a></label>' for s in case["suspects"])
    differences = []
    for file in case["files"]:
        before = blobs[f"before/{file}"].decode("utf-8").splitlines(keepends=True)
        after = blobs[f"after/{file}"].decode("utf-8").splitlines(keepends=True)
        diff = ''.join(difflib.unified_diff(before, after, fromfile=f"before/{file}", tofile=f"after/{file}"))
        if diff:
            differences.append(f'<h3>{e(file)}</h3><pre class="diff" tabindex="0">{e(diff)}</pre>')
    answer = f'<h2 tabindex="-1" id="solution-heading">The reveal.</h2><p class="answer-function">{e(case["solution"]["function"])}</p><p>{e(case["solution"]["text"])}</p><p>{refs(case["solution"]["refs"])}</p><h3>The actual patch</h3>{"".join(differences)}<div class="result-row"><strong class="fail">BEFORE · {len(report["before"]["failures"])} failing</strong><strong class="pass">AFTER · {report["after"]["tests"]} passing</strong></div><p>The same {report["after"]["tests"]} behavior tests ran against both snapshots.</p><details><summary>Read the passing test log</summary><pre class="log">{e(report["after"]["log"])}</pre></details>'
    payload = {"hints": [{"html": f'<p>{e(h["text"])}</p><p>{refs(h["refs"])}</p>'} for h in case["hints"]], "answer": answer, "function": case["solution"]["function"]}
    encoded = base64.b64encode(json.dumps(payload, ensure_ascii=False).encode("utf-8")).decode("ascii")
    notice = ''.join(f'<details><summary>{e(name)}</summary><pre class="log">{e(blobs[name].decode("utf-8"))}</pre></details>' for name in source["license_files"])
    revisions = ''
    if source["kind"] == "git-import":
        revisions = f'<p class="checksum">Before commit: {e(source["before_commit"])}<br>After commit: {e(source["after_commit"])}</p>'
    provenance = f'<p>{e(source["origin"])}</p><p>Declared license: {e(source["license"])}</p>{revisions}<p>Captured {e(report["captured_at"])} · Python {e(report["python"])} · {e(report["platform"])}</p><p>Snapshot and contract hashes bind this page to its local verification record. They are integrity checks, not independent attestations.</p>{notice}<details><summary>All evidence fingerprints</summary><pre class="log">{e(json.dumps(report["inputs"], indent=2))}</pre></details>'
    values = {"TITLE": e(case["title"]), "ID": e(case["id"]), "BRIEF": e(case["brief"]),
              "BRIEF_REFS": refs(case["brief_refs"]), "OBJECTIVE": e(case["objective"]),
              "KIND": "SELF-AUTHORED CASE" if source["kind"] == "self-authored" else "IMPORTED GIT HISTORY",
              "EVIDENCE": ''.join(cards), "SUSPECTS": suspects, "PAYLOAD": encoded,
              "BEFORE_LOG": e(report["before"]["log"]), "TEST_COUNT": str(report["before"]["tests"]),
              "FAIL_COUNT": str(len(report["before"]["failures"])), "PROVENANCE": provenance}
    template = Path(__file__).with_name("page.html").read_text(encoding="utf-8")
    # One pass prevents user text that resembles a marker from becoming markup.
    import re
    return re.sub(r"@@([A-Z_]+)@@", lambda m: values[m.group(1)], template)
