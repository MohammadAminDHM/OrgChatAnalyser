# OrgChat Check

A lightweight CLI to check production-readiness of an organization chatbot project before delivery.

Main command:

```bash
orgchat check
```

## Quick Start

Requirements:
- Node.js 16+
- Python 3.11+

Then:

```bash
cd your-chatbot
npx orgchat check
```

No clone.
No global OrgChat installation.
No manual virtualenv setup.
No mandatory orgchat.toml.

If you already have the repo:

```bash
pip install -e .
orgchat check
```

It runs seven important checks:

1. Where is the data and how is it refreshed?
2. Who has access to what information?
3. How do we measure correct answers?
4. What happens if the model doesn't know the answer?
5. How do we observe cost and latency?
6. Who restores the system when it breaks?
7. Who maintains the system after delivery?

## Local install

Requires Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate       # Linux/macOS
# .venv\Scripts\activate       # Windows PowerShell
pip install -e .
```

## Run without cloning (PyPI / uvx)

No local install or clone needed:

```bash
uvx orgchat check --config ./orgchat.toml
# or global install
pip install orgchat
orgchat check
```

## Quick start

In the root of the project you want to check:

```bash
orgchat init
```

Fill in `orgchat.toml` values, then:

```bash
orgchat check
```

For file output:

```bash
orgchat check --format markdown --output orgchat-report.md
orgchat check --format json --output orgchat-report.json
```

To check a different path:

```bash
orgchat check --path ./my-chatbot
```

For CI:

```bash
orgchat check --strict
```

Exit codes:

- `0`: All checks pass or only non-strict warnings exist.
- `1`: At least one check failed, or warnings exist in `--strict` mode.
- `2`: Input, path, or settings error.

## Report logic

`orgchat.toml` is the main evaluation source. Explicit `false` values or wrong paths cause `FAIL`. Unset values get `WARN`. The CLI also looks for common files/folders (`evals`, `retrieval`, `monitoring`, `runbook`) as supporting evidence.

Discovered evidence alone does not replace explicit configuration; its purpose is to provide a useful initial report from the existing project and show the path to completion.

## Example output

```text
ORGCHAT CHECK
Project: Enterprise Support Chatbot
Overall: WARN | Score: 64.5/100

Checks:
  [PASS] 100.0/100  Data and freshness
  [WARN]  55.0/100  Quality evaluation
  [FAIL]  40.0/100  Access and security

Next actions:
  1. Access and security: filter retrieval with the same user's permissions.
```

## Project structure

```text
src/orgchat/
  checker.py    # seven-check logic
  config.py     # TOML and path reading
  report.py     # terminal/json/markdown output
  cli.py        # orgchat check and orgchat init commands
tests/
examples/
```

This release reports operational readiness status; it is not a replacement for security testing, model evaluation, or full organizational audit.
