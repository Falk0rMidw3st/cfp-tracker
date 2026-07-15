# CFP Tracker

A CLI for tracking conference talk submissions: deadlines, which talk
version went where, and what's still open. Built for the "what CFPs are due" problem every conference speaker has.

## Install

```bash
pip install -e .
```

## Usage

```bash
# Register a talk and its versions
cfp talk add "Adversary Emulation 101" --version v1
cfp talk add "Adversary Emulation 101" --version v2-45min

# Track a CFP
cfp add --conference "BSides Madison 2026" --deadline 2026-08-15 \
  --event-date 2026-10-03 --talk "Adversary Emulation 101" --version v1 \
  --url https://cfp.bsidesmadison.org

# See everything due this month, plus anything overdue
cfp due

# Update status as things move
cfp status bsides-madison-2026 submitted
cfp status bsides-madison-2026 accepted

# List / filter
cfp list --open
cfp list --status accepted

# Export a Markdown summary
cfp export --output cfp-summary.md
```

State lives in `cfp_state.json` in the current directory by default
(override with `--state-file`).

## Status lifecycle

`watching` → `drafted` → `submitted` → `accepted` / `rejected` (or
`withdrawn` at any point). `cfp due` only surfaces `watching`/`drafted`
items; once something's submitted it drops off the "still need to act on
this" report.

## Development

```bash
pip install -e ".[dev]"
pytest
```
