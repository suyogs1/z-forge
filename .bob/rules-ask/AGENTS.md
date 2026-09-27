# Z-FORGE Ask Rules

These rules apply when Bob Ask mode is used for Z-FORGE questions.

## What Z-FORGE Is
- Z-FORGE is a local-first AI change engineering platform for IBM Z artifacts.
- It ingests COBOL, HLASM, copybooks, JCL, and flat datasets; builds a dependency/lineage graph; proposes changes; validates them; and produces a tamper-evident evidence trail.
- It is NOT a mainframe emulator and does NOT require z/OS connectivity.

## Key Concepts
- **Blast radius** — the set of artifacts impacted by a given field change, in topological order.
- **Semantic diff** — structured change records (FIELD_RESIZE, OFFSET_SHIFT, JCL_PARAM, etc.) — not a line diff.
- **Tamper-evident report** — SHA-256 hashes covering workspace, snapshot, and report content. Not cryptographic signing.
- **DeterministicScenarioAdapter** — detects data-layout issues (e.g. writing 12 bytes into 8-byte field) without requiring z/OS.
- **Z-PACK** — the portable self-describing workspace format; a directory with `zforge.pack.json` + plain files.

## Demo Scenario
- Change: `CUSTOMER-ID PIC X(8)` → `PIC X(12)` in synthetic banking workspace.
- Planted failure: `ACCTPROG.CBL` has local `WS-ACCT-CUST-ID PIC X(8)` — the critic catches the truncation.

## Source of Truth
- Blueprint: `z-forge-plan.md`
- Engine domain model: `packages/engine/zforge/models.py`
- Synthetic artifacts: `workspace/synthetic-banking/`
