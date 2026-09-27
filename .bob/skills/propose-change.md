---
name: propose-change
description: Guide Z-FORGE through converting a blast-radius result into concrete per-artifact change proposals with semantic diffs. Requires analyze-workspace to have run first.
---

# propose-change skill

## Purpose
Convert a blast-radius result into a `ChangeSet` of per-artifact proposals, present the semantic diff for each, and ask for user confirmation before applying.

## Steps

1. **Receive blast-radius result** — confirm the ordered list of impacted artifacts.
2. **Generate proposals** — call `propose_changes(workspace_path, blast_radius_result)`. Proposals are in topological order: copybooks → COBOL programs → HLASM → JCL → dataset schemas.
3. **Present semantic diff per artifact** — for each proposal, show:
   - Artifact name and type
   - `SemanticChange` records (FIELD_RESIZE, OFFSET_SHIFT, JCL_PARAM, etc.)
   - Rationale and confidence score
4. **Highlight the planted failure scenario** — ACCTPROG.CBL has a local `WS-ACCT-CUST-ID PIC X(8)` that is NOT in a copybook. The actor validation may pass (syntax valid) but the `DeterministicScenarioAdapter` will catch that a MOVE writes 12 bytes into an 8-byte field after the expansion.
5. **Confirm with user** — do not call `apply_proposals` without user approval.
6. **Apply** — call `apply_proposals(workspace_path, change_set_id)`. This creates a new snapshot, never modifies originals.

## Rules
- Proposals MUST be in topological order.
- Never apply proposals to the original imported artifacts under `workspace/synthetic-banking/` — snapshots only.
- Confidence < 0.8 must be flagged for human review before applying.
