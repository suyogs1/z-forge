# Z-FORGE Implementation Blueprint

**Hackathon:** IBM Bob 2.0  
**Budget:** ≤ 40 Bobcoins  
**Goal:** Produce a spectacular, reproducible 3–5 minute demo showing AI-assisted, evidence-backed mainframe change engineering — entirely locally, with synthetic data, with Bob as the primary interface.

---

## Top-Level Overview

Z-FORGE is a local-first intelligence and validation layer for IBM Z development artifacts. It is NOT a mainframe emulator. It ingests COBOL, HLASM, copybooks, JCL, and flat datasets; reconstructs their dependency and data-lineage graph; proposes safe, evidence-backed changes; validates them against a local runtime abstraction; attacks them adversarially; and produces a versioned evidence trail — all before any artifact touches a real z/OS system.

Bob is the primary UX. The MCP server exposes all Z-FORGE capabilities as Bob tools. A custom Bob mode (`zforge`) drives the Plan → Agent workflow. The backend is Python/FastAPI. The frontend is a React dashboard used only for the visual evidence report (blast-radius graph, semantic diff, AFP before/after).

**Demo in one sentence:** Import synthetic banking workspace → ask Bob to expand CUSTOMER-ID 8→12 bytes → watch Z-FORGE find every impacted artifact, propose changes, run validation, catch a planted failure, remediate, pass adversarial tests, and emit a signed evidence report.

---

## 1. Repository Structure

```
z-forge/
├── Readme.md
├── AGENTS.md
├── z-forge-plan.md
│
├── packages/
│   ├── engine/                  # Python: core analysis + change engine
│   │   ├── zforge/
│   │   │   ├── ingestion/       # parsers: COBOL, HLASM, JCL, copybook, dataset
│   │   │   ├── graph/           # dependency + lineage graph builder
│   │   │   ├── change/          # change proposal, semantic diff, patch engine
│   │   │   ├── runtime/         # local validation abstraction + adapters
│   │   │   ├── adversarial/     # critic/attack agent logic
│   │   │   ├── afp/             # AFP module (isolated, optional)
│   │   │   ├── versioning/      # Z-PACK format, snapshots, branch/merge
│   │   │   └── report/          # evidence report generator
│   │   ├── tests/
│   │   └── pyproject.toml
│   │
│   ├── api/                     # Python FastAPI: REST + WebSocket server
│   │   ├── app/
│   │   │   ├── routers/         # one router per domain area
│   │   │   └── schemas/         # Pydantic request/response models
│   │   └── pyproject.toml
│   │
│   ├── mcp/                     # Python MCP server exposing Z-FORGE to Bob
│   │   ├── server.py
│   │   ├── tools/               # one file per MCP tool group
│   │   └── pyproject.toml
│   │
│   └── ui/                      # React + TypeScript + Vite + Tailwind
│       ├── src/
│       │   ├── components/
│       │   │   ├── BlastRadiusGraph.tsx
│       │   │   ├── SemanticDiff.tsx
│       │   │   ├── EvidenceReport.tsx
│       │   │   └── AfpComparison.tsx
│       │   └── main.tsx
│       ├── package.json
│       └── vite.config.ts
│
├── workspace/                   # Z-PACK workspaces live here (gitignored except samples)
│   └── synthetic-banking/       # the demo workspace (committed, synthetic only)
│       ├── zforge.pack.json     # Z-PACK manifest
│       ├── cobol/
│       ├── copybooks/
│       ├── hlasm/
│       ├── jcl/
│       ├── datasets/
│       └── afp/
│
├── .bob/
│   ├── modes/
│   │   └── zforge-mode.yaml     # custom Bob mode
│   ├── skills/
│   │   ├── analyze-workspace.md
│   │   ├── propose-change.md
│   │   ├── run-validation.md
│   │   └── generate-report.md
│   ├── rules-agent/AGENTS.md
│   ├── rules-ask/AGENTS.md
│   └── rules-plan/AGENTS.md
│
└── docker-compose.yml           # optional: spins up api + mcp + ui together
```

**Key constraint:** `workspace/synthetic-banking/` is the only dataset committed. No real client data ever enters the repo.

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        IBM Bob IDE                          │
│  ┌──────────────┐  Plan→Agent  ┌───────────────────────┐   │
│  │ zforge mode  │◄────────────►│  Bob Agent + Skills   │   │
│  └──────────────┘              └──────────┬────────────┘   │
│                                           │ MCP calls       │
└───────────────────────────────────────────┼─────────────────┘
                                            │
                               ┌────────────▼────────────┐
                               │     MCP Server           │
                               │  (packages/mcp)          │
                               └────────────┬────────────┘
                                            │ HTTP
                               ┌────────────▼────────────┐
                               │    FastAPI Backend       │
                               │    (packages/api)        │
                               └────────────┬────────────┘
                                            │
                               ┌────────────▼────────────┐
                               │    Z-FORGE Engine        │
                               │  (packages/engine)       │
                               │                         │
                               │  Ingestion → Graph      │
                               │  Change → Runtime       │
                               │  Adversarial → Version  │
                               │  AFP (isolated)         │
                               │  Report                 │
                               └────────────┬────────────┘
                                            │
                               ┌────────────▼────────────┐
                               │  workspace/ (local fs)  │
                               │  Z-PACK workspaces      │
                               └─────────────────────────┘
                               
  React UI (packages/ui) ← reads evidence report JSON from api
```

**Data flow for the demo scenario:**

1. Bob (zforge mode) calls MCP tool `ingest_workspace` → engine parses all artifacts → graph persisted
2. Bob calls `blast_radius("CUSTOMER-ID", "8→12 bytes")` → engine traverses graph → returns affected nodes
3. Bob calls `propose_changes(blast_radius_result)` → engine generates per-artifact patch proposals
4. Bob calls `run_validation(proposals)` → runtime adapter executes local checks → returns pass/fail + diagnostics
5. Bob (critic subagent) calls `adversarial_validate(proposals)` → planted failure surfaces
6. Bob calls `remediate(failure)` → re-proposes + re-validates
7. Bob calls `snapshot_version("post-customerid-expansion")` → Z-PACK snapshot created
8. Bob calls `generate_report()` → evidence JSON → UI renders

---

## 3. Core Domain Model

```python
# All entities are plain Python dataclasses / Pydantic models

Artifact:
  id: str                    # stable hash of path + type
  path: str                  # relative to workspace root
  type: ArtifactType         # COBOL | HLASM | COPYBOOK | JCL | DATASET | AFP | UNKNOWN
  raw_content: str
  parsed: ArtifactAST | None # type-specific parsed representation
  metadata: dict             # e.g. PROGRAM-ID, section names, DCB attributes

ArtifactAST:                 # union type, one per artifact type
  CobolAST | HlasmAST | JclAST | DatasetSchema | AfpDocument

Dependency:
  source_id: str
  target_id: str
  kind: DependencyKind       # COPIES | CALLS | USES_DD | WRITES_TO | READS_FROM | INCLUDES
  location: SourceLocation   # line/column in source where dependency appears

DataLineageEdge:
  producer_id: str           # artifact that writes the dataset
  consumer_id: str           # artifact that reads the dataset
  dataset_name: str          # e.g. "CUST.MASTER.FILE"
  dd_name: str               # DD name in the JCL step

DependencyGraph:
  artifacts: dict[str, Artifact]
  edges: list[Dependency]
  lineage: list[DataLineageEdge]
  # methods: blast_radius(field, change), topological_sort(), subgraph(root)

ChangeProposal:
  id: str
  artifact_id: str
  description: str
  original_content: str
  proposed_content: str
  semantic_diff: SemanticDiff  # structured, not just textual
  rationale: str               # why this change is required
  confidence: float            # 0–1
  status: ProposalStatus       # PENDING | VALIDATED | FAILED | MERGED

SemanticDiff:
  changes: list[SemanticChange]

SemanticChange:
  kind: ChangeKind             # FIELD_RESIZE | OFFSET_SHIFT | INTERFACE_CHANGE | JCL_PARAM | ...
  location: SourceLocation
  before: str
  after: str
  impact_description: str

ValidationResult:
  proposal_id: str
  passed: bool
  diagnostics: list[Diagnostic]
  runtime_adapter: str         # "local-syntax" | "hercules" | "z390" | "none"

Snapshot:
  id: str
  label: str
  timestamp: str
  workspace_hash: str
  proposals_applied: list[str]
  artifacts: dict[str, str]    # artifact_id → content hash

ZPackManifest:
  version: str                 # "1.0"
  workspace_id: str
  name: str
  created_at: str
  artifacts: list[ArtifactRef]
  snapshots: list[SnapshotRef]
  lineage_graph_path: str
```

---

## 4. Z-PACK Format

Z-PACK is a portable, self-describing workspace container. It is a directory (or optionally a `.zpack` zip archive) with the following layout:

```
my-workspace.zpack/
├── zforge.pack.json          # manifest (see ZPackManifest above)
├── artifacts/
│   ├── cobol/
│   ├── copybooks/
│   ├── hlasm/
│   ├── jcl/
│   ├── datasets/             # schema descriptors (.dsd files) + sample data
│   └── afp/
├── graph/
│   ├── dependency.json       # serialized DependencyGraph
│   └── lineage.json          # serialized DataLineageEdge list
├── snapshots/
│   ├── <snapshot-id>.json    # one per Snapshot
│   └── <snapshot-id>/        # artifact content at that snapshot
└── reports/
    └── <timestamp>-evidence.json
```

**Rules:**
- Original imported artifacts are NEVER modified. All changes go into `snapshots/`.
- `zforge.pack.json` is the single source of truth for workspace identity.
- The format must be readable without Z-FORGE installed (plain JSON + plain text files).
- `.zpack` zip export is cosmetic only — internally it's the same directory layout.

---

## 5. Ingestion Pipeline

**Intent:** Parse every artifact type into a structured AST/schema so the graph engine has typed nodes to work with.

**Sub-tasks:**

### 5a. COBOL Parser
- **Input:** `.cbl`, `.cob`, `.cobol` files
- **Approach:** Use `cobol-parser` Python library or a minimal hand-written recursive-descent parser covering IDENTIFICATION, DATA DIVISION (especially WORKING-STORAGE, LINKAGE), PROCEDURE DIVISION, COPY statements, CALL statements
- **Key extractions:** PROGRAM-ID, all 01/05/88 level data definitions with PIC clauses and lengths, COPY statements (→ Dependency edges), CALL statements (→ Dependency edges), file assignments (SELECT … ASSIGN)
- **Output:** `CobolAST` — structured dict of data definitions with resolved byte sizes

### 5b. Copybook Parser
- **Input:** `.cpy`, `.copy` files
- **Approach:** Reuse COBOL DATA DIVISION parser; copybooks are pure data definitions
- **Output:** `CopybookAST` — same structure as CobolAST data section

### 5c. HLASM/DSECT Parser
- **Input:** `.asm`, `.hlasm` files
- **Approach:** Regex-based pass identifying DSECT, DS, DC, EQU, USING directives — not a full assembler
- **Key extractions:** DSECT names, field labels with DS operands (byte sizes), EQU offsets, COPY/COPYBOOK references
- **Output:** `HlasmAST` — list of DSECT definitions with fields and computed offsets

### 5d. JCL Parser
- **Input:** `.jcl` files
- **Approach:** Regex-based pass — JCL grammar is line-oriented and parseable without a full grammar
- **Key extractions:** JOB, EXEC (PGM=, PROC=), DD statements (DSN=, DISP=), dataset names used per step
- **Output:** `JclAST` — list of steps, each with input/output dataset references → DataLineageEdges

### 5e. Dataset Schema Parser
- **Input:** `.dsd` (Z-FORGE dataset schema descriptor, simple JSON) or flat fixed-length sample files
- **Approach:** JSON schema files that mirror the COBOL FD/01 layout; sample data files are binary-free fixed-width text
- **Output:** `DatasetSchema` — field list with offsets and lengths

### 5f. Ingestion Orchestrator
- Scans workspace directory tree, dispatches by file extension
- Resolves COPY member paths (searches copybook directories)
- Emits a `DependencyGraph` + `DataLineageEdge` list
- Persists to `graph/dependency.json` and `graph/lineage.json`

**Acceptance criteria:** After ingestion of the synthetic banking workspace, every COBOL program, copybook, HLASM DSECT, JCL step, and dataset is represented as a node in the graph with typed edges.

---

## 6. Dependency / Lineage Engine

**Intent:** Given a field name and a proposed change, compute the exact set of artifacts that must change, in dependency order.

### 6a. Graph Builder
- Constructs a directed graph (use `networkx` in Python) from `DependencyGraph` edges
- Nodes: `Artifact` instances
- Edges typed by `DependencyKind`

### 6b. Blast Radius Analysis
- Entry point: `blast_radius(field_name: str, change: FieldChange) → BlastRadiusResult`
- Algorithm:
  1. Find all artifacts that declare or reference `field_name` (COBOL PIC, HLASM DS, copybook, dataset schema)
  2. From each such artifact, do a reverse BFS/DFS to find all downstream consumers (via COPIES, CALLS, USES_DD, READS_FROM edges)
  3. For each affected artifact, compute: why it is affected, what must change (offset shift, PIC clause, DS operand), confidence
- Output: ordered list of `(Artifact, ImpactReason, ChangeType)` tuples, topologically sorted (change copybooks before programs)

### 6c. Data Lineage Traversal
- Separate traversal over `DataLineageEdge` list
- Given a dataset name, find all JCL steps that produce or consume it
- Shows "if CUST.MASTER.FILE record layout changes, these downstream JCL jobs and their programs are impacted"

### 6d. Visualization Export
- Emit a `blast_radius_graph.json` (nodes + edges with impact metadata) consumable by the React `BlastRadiusGraph.tsx` D3/force component
- This is what the UI renders as the dependency graph visualization

**Acceptance criteria:** Running blast-radius on `CUSTOMER-ID` in the synthetic workspace returns all 6+ affected artifacts in topological order with correct ImpactReason annotations.

---

## 7. Change Engine

**Intent:** For each artifact in the blast radius, generate a concrete, evidence-backed change proposal with a semantic diff.

### 7a. Change Proposal Generator
- Per artifact type, a `ChangeStrategy` class:
  - `CobolChangeStrategy`: rewrites PIC clauses, updates REDEFINES, adjusts VALUE clauses, updates MOVE/INSPECT references
  - `CopybookChangeStrategy`: same as COBOL data section
  - `HlasmChangeStrategy`: rewrites DS operands, recomputes EQU offsets
  - `JclChangeStrategy`: updates LRECL/BLKSIZE parameters in DD statements if record length changes
  - `DatasetSchemaChangeStrategy`: updates field length in `.dsd` file
- Each strategy emits a `ChangeProposal` with `original_content`, `proposed_content`, and a structured `SemanticDiff`

### 7b. Semantic Diff Engine
- **Not** a textual diff. Computes a list of `SemanticChange` records:
  - `FIELD_RESIZE`: field X changed from N to M bytes
  - `OFFSET_SHIFT`: field Y offset shifted by +4 due to upstream resize
  - `INTERFACE_CHANGE`: calling program must update its linkage section
  - `JCL_PARAM`: LRECL updated from 80 to 84
- The semantic diff is what enables meaningful evidence — "this change was made because CUSTOMER-ID expanded" not just a red/green line diff

### 7c. Proposal Ordering
- Proposals must be applied in topological order of the dependency graph
- Copybooks before programs; programs before JCL; datasets last
- The engine emits an ordered `ChangeSet` (list of proposals in safe application order)

### 7d. Patch Application
- `apply_proposals(change_set, workspace_path)` writes proposed content to `snapshots/<new-id>/`
- Never overwrites `artifacts/` (original imports)

**Acceptance criteria:** For the CUSTOMER-ID 8→12 expansion, the engine proposes changes to: CUSTMAST copybook (PIC X(8)→PIC X(12)), CUSTPROG COBOL program (WORKING-STORAGE + PROCEDURE references), CUSTRPT report program (MOVE statements), CUSTDSCT HLASM DSECT (DS CL8→DS CL12, EQU recomputation), CUSTLOAD JCL (LRECL update), CUST.MASTER.FILE dataset schema.

---

## 8. Runtime Abstraction

**Intent:** Validate proposals locally without requiring z/OS. Provide an adapter interface so TK5/Hercules/z390 can be plugged in optionally.

### 8a. Adapter Interface
```python
class RuntimeAdapter(Protocol):
    name: str
    def is_available(self) -> bool: ...
    def validate(self, artifact: Artifact, content: str) -> ValidationResult: ...
    def compile(self, artifact: Artifact, content: str) -> CompileResult: ...
```

### 8b. LocalSyntaxAdapter (always available)
- COBOL: call `cobc --syntax-only` (GnuCOBOL, if installed) or use the Python parser to check structural validity
- HLASM: regex/structural checks only (no assembler required)
- JCL: structural parse validation (no JES required)
- Dataset: schema consistency check
- This adapter is the fallback and is ALWAYS available — it is what makes the demo work without any runtime

### 8c. GnuCOBOLAdapter (optional)
- Requires `cobc` on PATH
- Compiles COBOL to native binary and runs a generated smoke test
- `is_available()` checks `shutil.which("cobc")`

### 8d. HerculesAdapter (optional)
- Requires Hercules/TK5 running and accessible via TCP
- Submits JCL via socket and polls for job completion
- `is_available()` checks TCP connectivity to configured address

### 8e. Adapter Selection
- `RuntimeAdapterRegistry.best_available()` returns the most capable available adapter
- Engine always reports which adapter was used in `ValidationResult.runtime_adapter`

**Acceptance criteria:** Demo runs end-to-end using only `LocalSyntaxAdapter` with no external runtime installed.

---

## 9. AFP Module Boundary

AFP is a **focused, isolated module**. It must not affect core MVP delivery. It is a bonus that enhances the demo if time permits.

**Boundary rules:**
- AFP code lives entirely in `packages/engine/zforge/afp/`
- No other module imports from `zforge.afp` — the AFP module is called only from the API layer as an optional endpoint
- The engine's `Artifact` type includes `AFP` as a value, but AFP artifacts are not included in blast radius traversal unless the AFP module is enabled
- AFP module failure must not affect any core workflow

**Scope of AFP module (MVP-scoped):**
- Parse a synthetic AFP file to extract structured page/field metadata (use a minimal AFP reader — AFP record format is well-documented binary with self-describing structured fields)
- Given a field expansion (CUSTOMER-ID 8→12), identify which AFP records reference that field name (via embedded PTOCA/NOP text data)
- Generate a "before/after" visual comparison as two PNG renders (use Python `Pillow` to render text pages from parsed AFP field data — no AFP viewer required)
- Expose as a single API endpoint: `POST /afp/compare` → returns before/after PNG paths

**Deferred:** Full AFP rendering fidelity, multi-page documents, AFP editing.

---

## 10. Versioning Model

**Intent:** Provide branch/snapshot/rollback semantics scoped to the Z-PACK workspace — not a full VCS.

### Concepts

| Concept | Meaning |
|---|---|
| Snapshot | An immutable point-in-time copy of all artifact contents, identified by a hash and a human label |
| Branch | A named pointer to a snapshot (lightweight; just a label + snapshot ID) |
| Diff | Semantic diff between two snapshots (uses the Semantic Diff Engine) |
| Merge | Apply a change set from one branch's snapshot onto another, with conflict detection |
| Rollback | Reset workspace to a prior snapshot's artifact contents |

### Implementation
- All snapshots stored in `workspace/<name>/snapshots/`
- Snapshot metadata in `zforge.pack.json`
- Rollback copies snapshot artifact contents back to a new "rollback" snapshot (never destructive — rollback is itself a new snapshot)
- `diff(snapshot_a, snapshot_b)` computes semantic diffs for every artifact that changed between the two
- Branch model is deliberately simple: no merge conflicts in the demo (the demo scenario is a linear change set)

### Demo version sequence
1. `initial` — snapshot on import
2. `pre-change` — snapshot before CUSTOMER-ID expansion
3. `proposed-expansion` — snapshot with all proposals applied
4. `post-remediation` — snapshot after critic-found failure is fixed
5. `verified` — snapshot after all validations pass

---

## 11. Bob Custom Mode / Skill / Subagent Design

### 11a. Custom Mode: `zforge`

File: `.bob/modes/zforge-mode.yaml`

```yaml
name: Z-FORGE Engineer
id: zforge
roleDefinition: |
  You are the Z-FORGE Change Engineer. Your job is to safely analyze, propose, 
  validate, and version changes to IBM Z mainframe artifacts. You operate 
  exclusively through Z-FORGE MCP tools. You never modify artifacts directly — 
  all changes go through proposals with evidence. You always run adversarial 
  validation before declaring a change safe.
groups:
  - read
  - mcp        # access to all Z-FORGE MCP tools
customInstructions: |
  - Always call ingest_workspace before any analysis
  - Always call blast_radius before proposing any change
  - Always spawn an adversarial critic subagent after validation
  - Never mark a change as safe unless adversarial_validate passes
  - Always call generate_report at the end of any change workflow
  - Prefer semantic_diff output over raw text diff in responses
```

### 11b. Skills

**`analyze-workspace` skill:** Guides Bob through: ingest → blast_radius → present findings. Used in Plan mode to understand scope before committing to a change.

**`propose-change` skill:** Guides Bob through: blast_radius result → propose_changes → show semantic diff per artifact → ask user to confirm before applying. Emphasizes the "evidence before action" principle.

**`run-validation` skill:** Guides Bob through: run_validation → if failures, spawn critic → if critic finds issues, call remediate → re-validate → loop until pass or escalate.

**`generate-report` skill:** Guides Bob through: generate_report → open UI report → summarize metrics (N artifacts analyzed, N changes proposed, N tests generated, N dangerous changes caught).

### 11c. Subagent Design

**Actor/Critic pattern for adversarial validation:**

- **Actor subagent:** Runs `propose_changes` and `run_validation`. Reports proposed change set and validation result.
- **Critic subagent:** Independently receives the same proposals and calls `adversarial_validate`. It is explicitly instructed to find ways the change could fail — not to confirm it works. It looks for: offset arithmetic errors, missed downstream consumers, JCL LRECL mismatches, REDEFINES breakage, copybook members used by programs not in the blast radius.

Both subagents are spawned in parallel where possible to save Bobcoins. The critic's findings gate the merge decision.

**Parallel investigation subagents (ingestion phase):**
- One subagent per artifact type (COBOL, HLASM, JCL, Copybook) can be spawned to investigate the blast radius in parallel, then results are merged. This is a strong Bob showcase but should be used judiciously given the 40-Bobcoin budget.

### 11d. Bobcoin Budget Estimate

| Phase | Bob Interactions | Estimated Coins |
|---|---|---|
| Plan: analyze workspace + blast radius | 2–3 | 4–6 |
| Agent: propose changes (actor) | 1 | 3–5 |
| Agent: critic adversarial validate | 1 (parallel) | 3–5 |
| Agent: remediate + re-validate | 1–2 | 3–5 |
| Agent: generate report + snapshot | 1 | 2–3 |
| Demo narration / iteration | buffer | 10–15 |
| **Total** | **~9–10 LLM turns** | **~25–39** |

Parallel subagents in the same turn count as one interaction. Design skills to minimize back-and-forth.

---

## 12. MCP Tool Design

MCP server: `packages/mcp/server.py` — exposes Z-FORGE API to Bob as tools.

### Tool Groups

**Workspace tools:**
```
ingest_workspace(workspace_path: str) → IngestResult
  Opens a Z-PACK workspace directory, runs the ingestion pipeline, persists graph.

list_artifacts(workspace_path: str, type_filter?: str) → list[ArtifactSummary]
  Lists all ingested artifacts with type and path.

get_artifact(artifact_id: str) → ArtifactDetail
  Returns parsed content, dependencies, and metadata for one artifact.
```

**Analysis tools:**
```
blast_radius(workspace_path: str, field_name: str, change_description: str) → BlastRadiusResult
  Returns ordered list of affected artifacts with impact reasons.

data_lineage(workspace_path: str, dataset_name: str) → LineageResult
  Returns producer/consumer chain for a named dataset.

semantic_diff(snapshot_a: str, snapshot_b: str) → SemanticDiffResult
  Computes structured semantic diff between two snapshots.
```

**Change tools:**
```
propose_changes(workspace_path: str, blast_radius_result: BlastRadiusResult) → ChangeSet
  Generates per-artifact proposals for the given blast radius.

apply_proposals(workspace_path: str, change_set_id: str) → SnapshotRef
  Applies approved proposals to a new snapshot (never modifies originals).
```

**Validation tools:**
```
run_validation(workspace_path: str, change_set_id: str) → list[ValidationResult]
  Runs the best-available runtime adapter on each proposed artifact.

adversarial_validate(workspace_path: str, change_set_id: str) → AdversarialResult
  Runs the adversarial validation pass — returns found issues with evidence.

remediate(workspace_path: str, issue: AdversarialIssue) → ChangeProposal
  Generates a fix proposal for a specific adversarial finding.
```

**Versioning tools:**
```
snapshot(workspace_path: str, label: str) → Snapshot
  Creates a named immutable snapshot of the current workspace state.

list_snapshots(workspace_path: str) → list[SnapshotRef]
  Lists all snapshots with labels and timestamps.

rollback(workspace_path: str, snapshot_id: str) → Snapshot
  Rolls back to a prior snapshot (creates a new snapshot, non-destructive).
```

**Report tools:**
```
generate_report(workspace_path: str) → EvidenceReport
  Generates the full evidence report JSON including metrics.

open_ui(workspace_path: str) → str
  Returns the localhost URL for the React evidence UI.
```

**AFP tools (optional module):**
```
afp_compare(workspace_path: str, field_name: str, change_description: str) → AfpComparisonResult
  Returns before/after AFP visual comparison paths.
```

---

## 13. Optional watsonx Orchestrate Integration Boundary

**Hard rule:** watsonx Orchestrate is NEVER a dependency. Core demo works without it.

**Boundary design:** A single thin adapter file: `packages/api/app/routers/orchestrate_adapter.py`

- Exposes the same endpoints as the MCP server but as OpenAPI-compatible REST tools consumable by watsonx Orchestrate skill definitions
- If `WATSONX_ORCHESTRATE_ENABLED=true` env var is set, this router is registered; otherwise it is never loaded
- The adapter adds no logic — it wraps the same engine calls

**What it would demonstrate (if time permits):** watsonx Orchestrate agent calling `blast_radius` and `generate_report` as skills in a multi-agent flow outside of Bob.

---

## 14. Synthetic Dataset Design

**Location:** `workspace/synthetic-banking/`

**Scenario:** A fictional bank "ZENITH BANK" runs a COBOL-based customer account management system on IBM Z.

### Artifacts

**Copybooks:**
- `CUSTMAST.CPY` — CUSTOMER-MASTER-RECORD with `CUSTOMER-ID PIC X(8)` (the field to expand)
- `ACCTMAST.CPY` — ACCOUNT-MASTER-RECORD, includes CUSTMAST
- `ERRCODE.CPY` — error code constants

**COBOL programs:**
- `CUSTPROG.CBL` — customer maintenance program; reads/writes CUST.MASTER.FILE; COPIES CUSTMAST
- `CUSTRPT.CBL` — customer report generator; reads CUST.MASTER.FILE; COPIES CUSTMAST; MOVEs CUSTOMER-ID to output
- `ACCTPROG.CBL` — account processing; COPIES ACCTMAST (which includes CUSTMAST); CALLS CUSTPROG

**HLASM:**
- `CUSTDSCT.ASM` — DSECT mirroring CUSTMAST layout for batch performance module; `CUSTID DS CL8`

**JCL:**
- `CUSTLOAD.JCL` — loads CUST.MASTER.FILE; DD statement with `LRECL=80`
- `CUSTRPT.JCL` — runs CUSTRPT program; references CUST.MASTER.FILE and CUST.REPORT.FILE
- `NIGHTLY.JCL` — nightly batch; runs CUSTPROG, ACCTPROG, CUSTRPT in sequence

**Dataset schemas (.dsd):**
- `CUST.MASTER.FILE.dsd` — `CUSTOMER-ID: {offset: 0, length: 8, type: "X"}`
- `CUST.REPORT.FILE.dsd` — output layout including CUSTOMER-ID field

**AFP:**
- `CUSTRPT.AFP` — synthetic AFP binary of a customer statement page; embeds CUSTOMER-ID in a PTOCA text field

**Sample data:**
- `CUST.MASTER.FILE.dat` — 10 fixed-length records (80 bytes each) with synthetic customer names/IDs

### Planted Demo Failure

Planted in `ACCTPROG.CBL`: A `MOVE CUSTOMER-ID TO WS-ACCT-CUST-ID` statement where `WS-ACCT-CUST-ID PIC X(8)` is declared in `ACCTPROG`'s own WORKING-STORAGE — NOT via a copybook. Because `ACCTPROG` COPIES `ACCTMAST` (which includes `CUSTMAST`), the blast-radius engine WILL find it via the copybook chain. However, the local variable `WS-ACCT-CUST-ID` is a direct declaration that a naïve proposal generator might miss (it would update the CUSTMAST copybook but not scan for local re-declarations of the same size).

**What the critic catches:** After the CUSTMAST copybook is updated to PIC X(12), ACCTPROG's local `WS-ACCT-CUST-ID PIC X(8)` will cause data truncation. The actor validation passes (syntax is valid), but the critic's adversarial scan finds the MOVE statement writing 12 bytes into an 8-byte field.

**Remediation:** Critic proposes updating `WS-ACCT-CUST-ID PIC X(8)` → `PIC X(12)` in ACCTPROG's WORKING-STORAGE.

---

## 15. Test Strategy

**Philosophy:** Tests exist to validate the engine logic, not to achieve coverage metrics. Every test uses synthetic data only.

### Engine unit tests (`packages/engine/tests/`)

| Test | What it validates |
|---|---|
| `test_cobol_parser.py` | Parses CUSTPROG.CBL, extracts CUSTOMER-ID field with correct PIC length |
| `test_copybook_parser.py` | Parses CUSTMAST.CPY, extracts all fields with correct byte sizes |
| `test_hlasm_parser.py` | Parses CUSTDSCT.ASM, extracts CUSTID DS CL8 with offset 0 |
| `test_jcl_parser.py` | Parses CUSTLOAD.JCL, extracts LRECL=80 and DSN=CUST.MASTER.FILE |
| `test_graph_builder.py` | Ingests full synthetic workspace, asserts correct edge count and types |
| `test_blast_radius.py` | Asserts CUSTOMER-ID blast radius returns exactly the 6 expected artifacts |
| `test_change_proposals.py` | Asserts correct proposals generated for each artifact type |
| `test_semantic_diff.py` | Asserts FIELD_RESIZE and OFFSET_SHIFT events for CUSTMAST expansion |
| `test_adversarial.py` | Asserts critic finds the planted WS-ACCT-CUST-ID truncation failure |
| `test_versioning.py` | Creates snapshot, rolls back, asserts content matches original |
| `test_zpack_format.py` | Serializes and deserializes a Z-PACK workspace without data loss |

### Integration tests (`packages/api/tests/`)
- `test_api_ingest.py` — POST /workspace/ingest returns populated graph
- `test_api_blast_radius.py` — POST /analysis/blast-radius returns expected artifact list
- `test_api_full_workflow.py` — End-to-end: ingest → blast_radius → propose → validate → snapshot

### MCP smoke tests (`packages/mcp/tests/`)
- `test_mcp_tools.py` — Each MCP tool returns correct schema, no errors on synthetic workspace

### Run commands
```bash
# From packages/engine/:
uv run pytest tests/ -v

# Single test:
uv run pytest tests/test_blast_radius.py::test_customer_id_blast_radius -v

# From packages/api/:
uv run pytest tests/ -v

# Lint (all packages):
uv run ruff check .
uv run mypy .
```

---

## 16. Measurable Impact Metrics

These are shown in the evidence report at the end of the demo.

| Metric | Before Z-FORGE | After Z-FORGE |
|---|---|---|
| Artifacts manually inspected | 9 (manual) | 0 (automated) |
| Time to identify blast radius | ~45 min (manual grep) | < 5 seconds |
| Downstream dependencies discovered | 0 (unknown without tool) | 6 artifacts, 3 data lineage edges |
| Tests generated | 0 | 11 (targeted regression tests) |
| Dangerous changes caught before runtime | 0 | 1 (ACCTPROG truncation) |
| Time from change request to verified change | Hours/days | < 3 minutes (demo) |
| Artifacts affected by final verified change | Unknown | 6 (with evidence per artifact) |

These numbers are exact and reproducible because the synthetic dataset is fixed.

---

## 17. Exact MVP Scope

### IN SCOPE (must demo)
- Z-PACK workspace import and format
- COBOL, copybook, HLASM (DSECT), JCL, dataset schema ingestion and parsing
- Dependency graph construction with typed edges
- Data lineage graph (JCL job → dataset → program)
- Blast-radius analysis for a field change
- Per-artifact change proposals with semantic diff
- LocalSyntaxAdapter validation (always available)
- Adversarial critic subagent (actor/critic pattern)
- Planted failure detection and remediation
- Snapshot versioning (create, list, rollback)
- Evidence report JSON + React UI visualization (blast radius graph + semantic diff table)
- Bob custom mode (`zforge`)
- At least two Bob skills (`analyze-workspace`, `propose-change`)
- MCP server with all tools listed in Section 12
- Measurable before/after metrics in the report

### IN SCOPE (if time permits, adds demo value)
- GnuCOBOL compilation via `LocalSyntaxAdapter` (requires `cobc` installed)
- AFP before/after comparison (Section 9)
- `generate-report` and `run-validation` skills
- watsonx Orchestrate adapter (Section 13)
- Z-PACK zip export

### OUT OF SCOPE (explicitly deferred)
- Real z/OS connectivity of any kind
- Hercules/TK5 adapter integration (architecture supports it; wiring deferred)
- Multi-user collaboration, authentication, cloud storage
- CICS, IMS, or MQ artifact awareness
- Full AFP rendering fidelity
- PL/I, REXX, or Easytrieve parsing
- GitHub integration, PR creation, CI/CD pipeline
- Database (DB2/IMS) schema change analysis
- watsonx.ai fine-tuning or model training
- Performance optimization for large workspaces (>100 artifacts)
- UI beyond the evidence report (no workspace browser, no code editor)

---

## Sub-Tasks for Implementation

> Status: all pending. Implement in order — later tasks depend on earlier ones.

### T1: Repository scaffolding [ ] pending
**Intent:** Create the directory structure, package configs, and empty entry points so every subsequent task has a clean place to land.
**Expected Outcomes:** `packages/engine/`, `packages/api/`, `packages/mcp/`, `packages/ui/` exist with valid `pyproject.toml` / `package.json`. `uv run pytest` runs (0 tests) without error. `npm run dev` starts (empty Vite app).
**Todo:**
- Create directory tree per Section 1
- Write `pyproject.toml` for engine, api, mcp (Python 3.11+, uv, pytest, ruff, mypy)
- Write `package.json` + `vite.config.ts` + `tailwind.config.ts` for ui
- Write empty `__init__.py` files for all Python packages
- Write `docker-compose.yml` (api on :8000, mcp on :8001, ui on :5173)
- Update `AGENTS.md` and `.bob/rules-*` with project-specific conventions

### T2: Synthetic banking workspace [ ] pending
**Intent:** Create the synthetic artifacts that all subsequent analysis and demo work is built on.
**Expected Outcomes:** `workspace/synthetic-banking/` contains all artifacts listed in Section 14. The planted failure is in place. Artifacts are syntactically valid COBOL/HLASM/JCL.
**Todo:**
- Write CUSTMAST.CPY with CUSTOMER-ID PIC X(8)
- Write CUSTPROG.CBL (reads/writes CUST.MASTER.FILE, COPIES CUSTMAST)
- Write CUSTRPT.CBL (report generator, COPIES CUSTMAST)
- Write ACCTPROG.CBL (COPIES ACCTMAST, includes planted failure: WS-ACCT-CUST-ID PIC X(8))
- Write ACCTMAST.CPY (includes CUSTMAST)
- Write ERRCODE.CPY
- Write CUSTDSCT.ASM (DSECT with CUSTID DS CL8)
- Write CUSTLOAD.JCL (LRECL=80), CUSTRPT.JCL, NIGHTLY.JCL
- Write CUST.MASTER.FILE.dsd, CUST.REPORT.FILE.dsd
- Write 10-record CUST.MASTER.FILE.dat (fixed 80-byte records)
- Write synthetic CUSTRPT.AFP (minimal binary AFP with CUSTOMER-ID field)
- Write zforge.pack.json manifest

### T3: Ingestion pipeline [ ] pending
**Intent:** Parse all artifact types into structured Python objects.
**Expected Outcomes:** `test_cobol_parser.py`, `test_copybook_parser.py`, `test_hlasm_parser.py`, `test_jcl_parser.py` all pass.
**Todo:**
- Implement `zforge/ingestion/cobol_parser.py`
- Implement `zforge/ingestion/copybook_parser.py` (reuse cobol parser)
- Implement `zforge/ingestion/hlasm_parser.py`
- Implement `zforge/ingestion/jcl_parser.py`
- Implement `zforge/ingestion/dataset_parser.py`
- Implement `zforge/ingestion/orchestrator.py`
- Write all ingestion unit tests

### T4: Dependency / lineage graph [ ] pending
**Intent:** Build the typed graph from parsed artifacts.
**Expected Outcomes:** `test_graph_builder.py` and `test_blast_radius.py` pass. Blast radius of CUSTOMER-ID returns exactly the expected 6 artifacts.
**Todo:**
- Implement `zforge/graph/builder.py` (networkx-based)
- Implement `zforge/graph/blast_radius.py`
- Implement `zforge/graph/lineage.py`
- Implement `zforge/graph/export.py` (blast_radius_graph.json for UI)
- Write graph unit tests

### T5: Change engine + semantic diff [ ] pending
**Intent:** Generate per-artifact proposals with structured semantic diffs.
**Expected Outcomes:** `test_change_proposals.py` and `test_semantic_diff.py` pass. Engine produces correct proposals for all 6 artifacts.
**Todo:**
- Implement `zforge/change/strategies/` (one per artifact type)
- Implement `zforge/change/semantic_diff.py`
- Implement `zforge/change/proposal_generator.py`
- Implement `zforge/change/patch_engine.py` (writes to snapshots/)
- Write change engine unit tests

### T6: Runtime abstraction + adversarial validator [ ] pending
**Intent:** Validate proposals and catch the planted failure.
**Expected Outcomes:** `test_adversarial.py` passes (critic finds WS-ACCT-CUST-ID truncation). `test_versioning.py` passes.
**Todo:**
- Implement `zforge/runtime/adapter_interface.py`
- Implement `zforge/runtime/local_syntax_adapter.py`
- Implement `zforge/adversarial/critic.py`
- Implement `zforge/versioning/snapshot.py`
- Implement `zforge/versioning/zpack.py` (serialize/deserialize Z-PACK)
- Write validation + versioning unit tests

### T7: FastAPI backend [ ] pending
**Intent:** Expose engine as HTTP API.
**Expected Outcomes:** All API integration tests pass. `curl http://localhost:8000/health` returns OK.
**Todo:**
- Implement all routers in `packages/api/app/routers/`
- Implement Pydantic schemas in `packages/api/app/schemas/`
- Implement `zforge/report/generator.py`
- Write API integration tests

### T8: MCP server [ ] pending
**Intent:** Expose all Z-FORGE capabilities as Bob MCP tools.
**Expected Outcomes:** Bob can call all tools listed in Section 12 and receive correct responses.
**Todo:**
- Implement `packages/mcp/server.py` with all tool groups
- Register MCP server in Bob config
- Write MCP smoke tests
- Test each tool from Bob chat

### T9: Bob mode, skills, and subagent design [ ] pending
**Intent:** Create the custom Bob mode and skills that drive the demo workflow.
**Expected Outcomes:** `zforge` mode active in Bob. Skills guide the full Plan→Agent demo scenario without error.
**Todo:**
- Write `.bob/modes/zforge-mode.yaml`
- Write `.bob/skills/analyze-workspace.md`
- Write `.bob/skills/propose-change.md`
- Write `.bob/skills/run-validation.md`
- Write `.bob/skills/generate-report.md`
- Update `.bob/rules-agent/AGENTS.md`, `.bob/rules-ask/AGENTS.md`, `.bob/rules-plan/AGENTS.md`
- End-to-end demo dry-run in Bob

### T10: React UI evidence report [ ] pending
**Intent:** Visualize the evidence report for the demo finale.
**Expected Outcomes:** `npm run dev` shows blast-radius force graph, semantic diff table, and metrics dashboard from the evidence report JSON.
**Todo:**
- Implement `BlastRadiusGraph.tsx` (D3 force-directed, nodes colored by artifact type)
- Implement `SemanticDiff.tsx` (structured change table per artifact)
- Implement `EvidenceReport.tsx` (metrics cards: N artifacts, N changes, N failures caught)
- Wire to FastAPI `/report/latest` endpoint
- Optional: `AfpComparison.tsx` (side-by-side before/after PNG)

### T11: AFP module [ ] pending (if time permits)
**Intent:** Demonstrate print-output impact of CUSTOMER-ID expansion.
**Expected Outcomes:** `POST /afp/compare` returns before/after PNG paths. UI shows side-by-side comparison.
**Todo:**
- Implement `zforge/afp/parser.py` (minimal AFP binary reader)
- Implement `zforge/afp/impact_analyzer.py` (field reference detection)
- Implement `zforge/afp/renderer.py` (Pillow-based page render)
- Add AFP router to FastAPI
- Wire to `AfpComparison.tsx`

---

*End of Z-FORGE Implementation Blueprint*
