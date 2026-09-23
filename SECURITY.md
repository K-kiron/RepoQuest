# Security boundaries

`check`, `build`, and `import-git` read case data; they do not execute case Python code. `verify --trust-code` executes the selected snapshots and contract with the invoking user's access. It is not a filesystem, network, memory, or process sandbox. Review case code before execution, or use an independently managed disposable environment.

Generated HTML includes source excerpts, logs, the patch, and the answer. Review all content before sharing. Answers are hidden from the normal interface until requested, but remain inspectable in the HTML source. Verification fingerprints detect changed inputs; reports are not signed attestations.

## Reporting a vulnerability

Do not put credentials, private source, or sensitive reproduction data in a public issue. If GitHub's **Report a vulnerability** option is available in this repository's Security tab, use it for a private report. Otherwise, open a minimal issue requesting a private reporting channel without disclosing exploit details or sensitive information.

Include the affected version, operating system, minimal sanitized reproduction, and observed impact. The project is an early release and does not offer a guaranteed response time.
