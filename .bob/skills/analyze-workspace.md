---
name: analyze-workspace
description: Guide Z-FORGE through workspace ingestion, blast-radius analysis, and impact reporting. Use before any change workflow.
---

# analyze-workspace skill

## Purpose
Walk Bob through: `ingest_workspace` → `blast_radius` → present findings clearly, distinguishing impacted, inspected-unchanged, and any adversarial findings.

## Steps

1. **Ingest** — call `ingest_workspace(workspace_path)`. Confirm artifact count by type.
2. **Blast radius** — call `blast_radius(workspace_path, field_name, change_description)`. The result has three buckets:
   - `impacted` — artifacts that require modification
   - `inspected_unchanged` — artifacts reviewed but not requiring modification
   - `adversarial_findings` — issues found during critic pass (may be empty at this stage)
3. **Present findings** — show a table: artifact name | type | impact reason | details.
4. **Ask for confirmation** before proceeding to `propose-change`.

## Rules
- Never skip ingestion — graph must be fresh before blast-radius.
- Report all three result categories, not just impacted.
- Do not modify artifacts directly; all changes go through proposals.
