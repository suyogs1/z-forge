# Z-FORGE Agent Rules

These rules apply when Bob Agent mode is used for Z-FORGE implementation work.

## Immutability
- ALL original imported artifacts anywhere under `workspace/synthetic-banking/` are immutable.
- This includes `cobol/`, `copybooks/`, `hlasm/`, `jcl/`, `datasets/`, `afp/` subdirectories.
- The ONLY exception is writing new files to `workspace/synthetic-banking/snapshots/`, `workspace/synthetic-banking/graph/`, and `workspace/synthetic-banking/reports/`.
- Never modify `workspace/synthetic-banking/zforge.pack.json` after initial creation except to add snapshot/report refs.

## Packages
- `packages/engine/` — Python 3.11+, uv, pytest. Use `uv run pytest` to run tests.
- `packages/api/` — FastAPI. Use `uvicorn app.main:app` to run.
- `packages/mcp/` — MCP server. Use Bob v2 `registerTool` API.
- `packages/ui/` — React + TypeScript + Vite + Tailwind. Use `npm run dev`.

## Runtime Adapters
- `LocalSyntaxAdapter` is always available (no external tools required).
- `DeterministicScenarioAdapter` is always available — detects data-layout problems (e.g. writing 12 bytes into 8-byte field) using deterministic synthetic execution scenarios. It does NOT pretend to be z/OS.
- `GnuCOBOLAdapter` and `HerculesAdapter` are optional and gated by `is_available()`.

## Proposals & Ordering
- Change proposals MUST be in topological order: copybooks → COBOL programs → HLASM → JCL → dataset schemas.
- `apply_proposals` writes to `snapshots/<id>/`, never to the original artifact directories.
- Rollback creates a NEW snapshot; it never destructively overwrites.

## Evidence Report
- Use "tamper-evident evidence report" — SHA-256 hashes of workspace/snapshot/report content.
- Do NOT claim "signed" or "cryptographically signed" unless a private key and signature are actually implemented.

## Blast Radius Results
- Always report three buckets: `impacted` (need modification), `inspected_unchanged`, `adversarial_findings`.
- Do not hard-code a single artifact count. The count varies by scenario.

## AFP Isolation
- Nothing outside `packages/engine/zforge/afp/` imports from `zforge.afp`.
- AFP failure must not break any core workflow.

## Commands
```bash
# Engine
cd packages/engine && uv run pytest tests/ -v
uv run ruff check .
uv run mypy .

# API
cd packages/api && uv run pytest tests/ -v

# UI
cd packages/ui && npm run dev
```
