---
name: generate-report
description: Guide Z-FORGE through generating the tamper-evident evidence report and presenting it in the React UI.
---

# generate-report skill

## Purpose
Generate the final evidence report JSON with SHA-256 integrity hashes, open the React UI, and summarize the demo metrics.

## Steps

1. **Generate report** — call `generate_report(workspace_path)`. The report includes:
   - Artifact inventory (total, by type)
   - Blast-radius summary: impacted count, inspected-unchanged count
   - Change proposals: total, validated, failed, merged
   - Adversarial findings: total caught, total remediated
   - Tamper-evident hashes: SHA-256 of workspace root, each snapshot, and the report itself
   - Measurable before/after metrics
2. **Open UI** — call `open_ui(workspace_path)` and share the localhost URL.
3. **Summarize** — present the metrics table from the report inline in chat:
   | Metric | Before | After |
   |---|---|---|
   | Artifacts automated | 0 | N |
   | Blast radius discovered | manual/unknown | N artifacts |
   | Dangerous changes caught | 0 | 1 (ACCTPROG truncation) |
   | Time to verified change | hours | < 3 min |

## Rules
- The report uses **tamper-evident SHA-256 hashes** — do NOT claim cryptographic signing. We do not have private keys.
- All hashes cover workspace + snapshot + report content at report-generation time.
- The report JSON must be readable without Z-FORGE installed (plain JSON).
