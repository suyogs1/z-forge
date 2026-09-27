# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Project

Z-FORGE — AI Change Engineering platform for IBM Z (IBM Bob 2.0 Hackathon).  
See [`z-forge-plan.md`](z-forge-plan.md) for the full implementation blueprint.

## Stack

- **Backend/Engine:** Python 3.11+, FastAPI, uv (package manager), pytest, ruff, mypy
- **MCP Server:** Python (Bob v2 `registerTool` API)
- **Frontend:** React + TypeScript + Vite + Tailwind
- **Workspace format:** Z-PACK (local filesystem, no cloud)
- **Bob custom mode:** `zforge` (`.bob/modes/zforge-mode.yaml`)

## Critical Rules

- **All original imported artifacts anywhere under `workspace/synthetic-banking/` are immutable.** This includes `cobol/`, `copybooks/`, `hlasm/`, `jcl/`, `datasets/`, and `afp/` subdirectories. All changes go into `workspace/synthetic-banking/snapshots/`.
- **No real client/employer data ever.** Only synthetic artifacts.
- **Runtime adapters must be optional.** Core demo must work with `LocalSyntaxAdapter` and `DeterministicScenarioAdapter` only (no Hercules, no z/OS, no `cobc` required).
- **AFP module is isolated.** Nothing outside `packages/engine/zforge/afp/` imports from it. AFP failure must not break core workflow.
- **Proposals must be in topological order** (copybooks before programs, programs before JCL, datasets last).

## Runtime Adapters

Two adapters are always available (no external tools required):

- **`LocalSyntaxAdapter`** — structural/syntax checks using the Python parser and regex-based validators.
- **`DeterministicScenarioAdapter`** — runs deterministic synthetic execution scenarios to detect data-layout problems (e.g. writing 12 bytes into an 8-byte field). It does NOT pretend to be z/OS and makes no claim of mainframe fidelity. It is always available and is what surfaces the planted failure in ACCTPROG.

Optional adapters gated by `is_available()`: `GnuCOBOLAdapter`, `HerculesAdapter`.

## Blast Radius Results

`BlastRadiusResult` has three buckets — always report all three:

- `impacted` — artifacts that require modification
- `inspected_unchanged` — artifacts reviewed but not requiring modification  
- `adversarial_findings` — issues found during the critic pass

Do not hard-code a single artifact count. The count depends on the scenario and workspace.

## Evidence Report

Use **"tamper-evident evidence report"** — SHA-256 hashes covering workspace, snapshot, and report content. Do NOT use "signed" or "cryptographically signed" unless a private key and signature are actually implemented in code. We use deterministic hashes for integrity verification only.

## Commands

```bash
# Engine tests (from packages/engine/)
uv run pytest tests/ -v
uv run pytest tests/test_blast_radius.py::test_customer_id_blast_radius -v   # single test

# Lint / type check
uv run ruff check .
uv run mypy .

# API tests (from packages/api/)
uv run pytest tests/ -v

# UI dev (from packages/ui/)
npm run dev
```

## Key Non-Obvious Patterns

- **Planted failure:** `ACCTPROG.CBL` contains a local `WS-ACCT-CUST-ID PIC X(8)` that is NOT in a copybook. The blast-radius engine finds ACCTPROG via the copybook chain, but a naïve change strategy misses this local variable. The adversarial critic (and `DeterministicScenarioAdapter`) must catch it.
- **Semantic diff is structured, not textual.** `SemanticChange` records have typed `ChangeKind` values (FIELD_RESIZE, OFFSET_SHIFT, etc.) — not line diffs.
- **Snapshots are new writes, never overwrites.** `apply_proposals` creates a new snapshot directory; `rollback` also creates a new snapshot.
- **Bobcoin budget is ~25–39 of 40.** Parallel subagents in the same turn count as one interaction. Design skills to minimize LLM turns.
- **Bob mode `zforge` restricts to MCP tools only.** Direct file edits from Bob are wrong in this mode — all changes must go through `propose_changes` → `apply_proposals`.

## Future Bob Integration Point

The future Bob integration should call the existing Z-FORGE workflow entry point (`zforge.orchestration.execute_workflow` / `run_change_workflow`) rather than reimplementing change analysis, validation, or remediation.

