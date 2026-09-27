---
name: run-validation
description: Guide Z-FORGE through the validation + adversarial-critic loop. Catches planted failures before any snapshot is declared safe.
---

# run-validation skill

## Purpose
Run `run_validation` (actor), then spawn the adversarial critic, and loop until all issues are remediated or escalated.

## Steps

1. **Actor validation** — call `run_validation(workspace_path, change_set_id)`. Report pass/fail per proposal with diagnostics. Note which adapter was used (`local-syntax`, `deterministic-scenario`, etc.).
2. **Spawn critic** — call `adversarial_validate(workspace_path, change_set_id)`. The critic looks for:
   - Offset arithmetic errors
   - Local variable re-declarations (e.g. `WS-ACCT-CUST-ID PIC X(8)` in ACCTPROG.CBL)
   - JCL LRECL mismatches
   - REDEFINES breakage
   - Copybook members used by programs not in the blast radius
3. **If critic finds issues** — call `remediate(workspace_path, issue)` per finding. Re-run both actor and critic.
4. **Loop** — repeat until `adversarial_validate` returns no findings or user chooses to escalate.
5. **Create snapshot** — call `snapshot(workspace_path, label)` only after all validations pass.

## Rules
- `DeterministicScenarioAdapter` is always available and specifically designed to catch data-layout problems (e.g. writing 12 bytes into an 8-byte field). Always use it.
- Never skip the critic pass. Even if actor validation passes, the critic may find the planted failure.
- A change is NOT safe until `adversarial_validate` returns empty findings.
