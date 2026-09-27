# Z-FORGE Plan Rules

These rules apply when Bob Plan mode is used for Z-FORGE architecture and design work.

## Architecture Principles
- Engine (`packages/engine/`) is the only layer with domain logic. API and MCP are thin wrappers.
- AFP module (`zforge/afp/`) is fully isolated — no imports from it outside the module.
- Runtime adapters are optional. `LocalSyntaxAdapter` and `DeterministicScenarioAdapter` are always available. Everything else is gated by `is_available()`.
- All workspace mutations write to `snapshots/`. Original imported artifacts are immutable.

## Planning a Change Workflow
Before implementing any change, plan:
1. Which artifacts are in the blast radius (topological order)?
2. What adapter validates each artifact?
3. What adversarial scenarios does the `DeterministicScenarioAdapter` need to cover?
4. What snapshots are created and in what sequence?
5. What does the tamper-evident report hash?

## Task Order
T1 → T2 → T3 → T4 → T5 → T6 → T7 → T8 → T9 → T10 → T11.
Do not skip ahead — later tasks depend on earlier ones being complete.

## Blast Radius Result Schema
The `BlastRadiusResult` has three buckets: `impacted`, `inspected_unchanged`, `adversarial_findings`.
Plans must account for all three — not just the impacted count.

## Evidence Report
Plans for the report must specify:
- Which SHA-256 hashes are computed and over what content
- That the word "signed" is NOT used unless a real key pair is implemented
- That "tamper-evident" is the correct term for hash-based integrity
