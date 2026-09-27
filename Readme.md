# Z-FORGE

**AI Change Engineering platform for IBM Z** — IBM Bob 2.0 Hackathon entry.

Z-FORGE is a local-first intelligence and validation layer for IBM Z development artifacts. It ingests COBOL, HLASM, copybooks, JCL, and flat datasets; reconstructs their dependency and data-lineage graph; proposes safe, evidence-backed changes; validates them against local runtime adapters; attacks them adversarially; and produces a versioned, tamper-evident evidence trail — all before any artifact touches a real z/OS system.

## Quick Start

```bash
# Engine (from packages/engine/)
uv run pytest tests/ -v

# API (from packages/api/)
uv run uvicorn app.main:app --reload

# MCP server (from packages/mcp/)
uv run python server.py

# UI (from packages/ui/)
npm install && npm run dev
```

## Structure

```
packages/
  engine/    Python: core analysis + change engine
  api/       Python: FastAPI REST backend
  mcp/       Python: MCP server for IBM Bob
  ui/        React + TypeScript + Vite + Tailwind

workspace/
  synthetic-banking/    Demo workspace (synthetic data only)

.bob/
  modes/     zforge custom Bob mode
  skills/    analyze-workspace, propose-change, run-validation, generate-report
  rules-*/   Mode-specific agent rules
```

## Demo Scenario

Import the synthetic banking workspace → ask Bob to expand `CUSTOMER-ID` from 8 to 12 bytes → watch Z-FORGE find every impacted artifact, propose changes, validate, catch a planted failure (`WS-ACCT-CUST-ID PIC X(8)` in `ACCTPROG.CBL`), remediate, and emit a tamper-evident evidence report.

## Implementation Status

| Task | Description | Status |
|------|-------------|--------|
| T1 | Repository scaffolding | ✅ Done |
| T2 | Synthetic banking workspace | ✅ Done |
| T3 | Ingestion pipeline | ⏳ Pending |
| T4 | Dependency / lineage graph | ⏳ Pending |
| T5 | Change engine + semantic diff | ⏳ Pending |
| T6 | Runtime abstraction + adversarial validator | ⏳ Pending |
| T7 | FastAPI backend | ⏳ Pending |
| T8 | MCP server | ⏳ Pending |
| T9 | Bob mode, skills, subagent design | ⏳ Pending |
| T10 | React UI evidence report | ⏳ Pending |
| T11 | AFP module (optional) | ⏳ Pending |

See [`z-forge-plan.md`](z-forge-plan.md) for the full implementation blueprint.

## Key Rules

- **Original artifacts are immutable.** All changes under `workspace/synthetic-banking/` go into `snapshots/`.
- **No real client data.** Only synthetic artifacts.
- **Runtime adapters are optional.** `LocalSyntaxAdapter` and `DeterministicScenarioAdapter` are always available.
- **AFP is isolated.** `zforge.afp` is only imported from the API layer.
- **Evidence report is tamper-evident** (SHA-256 hashes), not cryptographically signed.
