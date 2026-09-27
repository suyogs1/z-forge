"""Ingestion orchestrator.

Scans a workspace directory, dispatches the correct parser by file
extension, resolves COPY/copybook references, constructs typed Artifact
objects, and produces:
  - DependencyGraph (with Dependency edges)
  - list[DataLineageEdge]
  - Persisted graph/dependency.json and graph/lineage.json
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from zforge.ingestion.cobol_parser import parse_cobol_file
from zforge.ingestion.copybook_parser import parse_copybook_file
from zforge.ingestion.dataset_parser import parse_dat_file, parse_dsd_file
from zforge.ingestion.hlasm_parser import parse_hlasm_file
from zforge.ingestion.jcl_parser import parse_jcl_file
from zforge.models import (
    Artifact,
    ArtifactType,
    DataLineageEdge,
    Dependency,
    DependencyGraph,
    DependencyKind,
    SourceLocation,
)

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Extension → ArtifactType mapping
# ---------------------------------------------------------------------------

_EXT_MAP: dict[str, ArtifactType] = {
    ".cbl": ArtifactType.COBOL,
    ".cob": ArtifactType.COBOL,
    ".cobol": ArtifactType.COBOL,
    ".cpy": ArtifactType.COPYBOOK,
    ".copy": ArtifactType.COPYBOOK,
    ".asm": ArtifactType.HLASM,
    ".hlasm": ArtifactType.HLASM,
    ".jcl": ArtifactType.JCL,
    ".dsd": ArtifactType.DATASET,
    ".dat": ArtifactType.DATASET,
    ".afp": ArtifactType.AFP,
}

# Files to skip entirely
_SKIP_PATTERNS = {".gitignore", ".gitkeep", "zforge.pack.json"}


# ---------------------------------------------------------------------------
# Index helpers
# ---------------------------------------------------------------------------


def _make_artifact(path: Path, workspace_root: Path, artifact_type: ArtifactType) -> Artifact:
    rel = path.relative_to(workspace_root).as_posix()
    art_id = Artifact.make_id(rel, artifact_type)
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except (OSError, UnicodeDecodeError):
        raw = ""
    return Artifact(id=art_id, path=rel, type=artifact_type, raw_content=raw)


def _normalise_copybook_name(name: str) -> str:
    """Strip .CPY suffix and uppercase for lookup."""
    return name.upper().removesuffix(".CPY")


def _normalise_dataset_name(dsn: str) -> str:
    """Strip ZENITH. qualifier for short matching."""
    return dsn.upper().removeprefix("ZENITH.")


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


class IngestionOrchestrator:
    """Scan a workspace and build a DependencyGraph."""

    def __init__(self, workspace_root: str | Path) -> None:
        self.workspace_root = Path(workspace_root).resolve()
        self.graph = DependencyGraph()
        self._lineage: list[DataLineageEdge] = []

        # Lookup indexes built during scan
        # name (uppercase stem) → artifact id
        self._cobol_by_name: dict[str, str] = {}
        self._copybook_by_name: dict[str, str] = {}
        self._dataset_by_name: dict[str, str] = {}  # normalised DSN → artifact id
        self._artifact_by_stem: dict[str, str] = {}  # uppercase stem → artifact id

        # Parsed results (kept for edge derivation)
        self._cobol_results: dict[str, object] = {}  # artifact_id → CobolParseResult
        self._copybook_results: dict[str, object] = {}
        self._jcl_results: dict[str, object] = {}
        self._hlasm_results: dict[str, object] = {}
        self._dataset_results: dict[str, object] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def ingest(self) -> DependencyGraph:
        """Run the full ingestion pipeline and return the DependencyGraph."""
        self._scan_files()
        self._derive_copy_edges()
        self._derive_call_edges()
        self._derive_jcl_edges()
        self._derive_hlasm_copy_edges()
        self.graph.lineage = self._lineage
        return self.graph

    def persist(self, graph_dir: Optional[str | Path] = None) -> None:
        """Write graph/dependency.json and graph/lineage.json."""
        out_dir = Path(graph_dir) if graph_dir else self.workspace_root / "graph"
        out_dir.mkdir(parents=True, exist_ok=True)

        dep_path = out_dir / "dependency.json"
        lin_path = out_dir / "lineage.json"

        dep_path.write_text(self.graph.model_dump_json(indent=2), encoding="utf-8")
        lin_edges = [e.model_dump() for e in self._lineage]
        lin_path.write_text(json.dumps(lin_edges, indent=2), encoding="utf-8")

        log.info("Persisted dependency graph to %s", dep_path)
        log.info("Persisted lineage graph to %s", lin_path)

    # ------------------------------------------------------------------
    # Scan phase
    # ------------------------------------------------------------------

    def _scan_files(self) -> None:
        for path in sorted(self.workspace_root.rglob("*")):
            if not path.is_file():
                continue
            if path.name in _SKIP_PATTERNS:
                continue
            # Skip hidden dirs and non-source subtrees
            parts = path.relative_to(self.workspace_root).parts
            if any(p.startswith(".") for p in parts):
                continue
            # Skip output dirs
            if parts and parts[0] in ("snapshots", "graph", "reports"):
                continue

            ext = path.suffix.lower()
            if ext not in _EXT_MAP:
                continue

            artifact_type = _EXT_MAP[ext]
            artifact = _make_artifact(path, self.workspace_root, artifact_type)
            self.graph.artifacts[artifact.id] = artifact
            stem_upper = path.stem.upper()
            self._artifact_by_stem[stem_upper] = artifact.id

            # Dispatch to parser
            try:
                self._parse_artifact(path, artifact, artifact_type)
            except Exception as exc:
                log.warning("Parse error for %s: %s", path, exc)

    def _parse_artifact(  # noqa: PLR0912
        self, path: Path, artifact: Artifact, artifact_type: ArtifactType
    ) -> None:
        if artifact_type == ArtifactType.COBOL:
            cbl = parse_cobol_file(path)
            self._cobol_results[artifact.id] = cbl
            stem = artifact.path.split("/")[-1].upper().removesuffix(".CBL")
            self._cobol_by_name[stem] = artifact.id
            artifact.metadata["program_id"] = cbl.program_id
            artifact.metadata["copy_statements"] = [c for c, _ in cbl.copy_statements]
            artifact.metadata["call_statements"] = [c for c, _ in cbl.call_statements]
            artifact.metadata["local_declarations"] = [
                {"name": f.name, "pic": f.pic, "byte_size": f.byte_size, "line": f.line}
                for f in cbl.local_declarations
            ]
            artifact.metadata["file_selects"] = [
                {"logical": s.logical_name, "assign_to": s.assign_to} for s in cbl.file_selects
            ]

        elif artifact_type == ArtifactType.COPYBOOK:
            cpy = parse_copybook_file(path)
            self._copybook_results[artifact.id] = cpy
            cpy_name = _normalise_copybook_name(path.name)
            self._copybook_by_name[cpy_name] = artifact.id
            artifact.metadata["fields"] = [
                {"name": f.name, "pic": f.pic, "byte_size": f.byte_size, "level": f.level}
                for f in cpy.fields
                if f.pic
            ]
            artifact.metadata["copy_statements"] = [c for c, _ in cpy.copy_statements]

        elif artifact_type == ArtifactType.HLASM:
            asm = parse_hlasm_file(path)
            self._hlasm_results[artifact.id] = asm
            artifact.metadata["sections"] = [
                {
                    "name": s.name,
                    "kind": s.kind,
                    "fields": [
                        {
                            "label": f.label,
                            "opcode": f.opcode,
                            "operand": f.operand,
                            "byte_size": f.byte_size,
                            "offset": f.offset,
                        }
                        for f in s.fields
                        if f.label
                    ],
                }
                for s in asm.sections
            ]
            artifact.metadata["copy_references"] = [c for c, _ in asm.copy_references]
            artifact.metadata["equ_symbols"] = asm.equ_symbols

        elif artifact_type == ArtifactType.JCL:
            jcl = parse_jcl_file(path)
            self._jcl_results[artifact.id] = jcl
            artifact.metadata["job_name"] = jcl.job_name
            artifact.metadata["steps"] = [
                {
                    "name": step.name,
                    "pgm": step.pgm,
                    "dds": [
                        {"ddname": dd.ddname, "dsn": dd.dsn, "disp": dd.disp, "lrecl": dd.lrecl}
                        for dd in step.dds
                        if dd.dsn
                    ],
                }
                for step in jcl.steps
            ]

        elif artifact_type == ArtifactType.DATASET:
            ext = path.suffix.lower()
            if ext == ".dsd":
                dsd = parse_dsd_file(path)
                self._dataset_results[artifact.id] = dsd
                dsn = dsd.dataset_name
                self._dataset_by_name[dsn.upper()] = artifact.id
                self._dataset_by_name[_normalise_dataset_name(dsn)] = artifact.id
                artifact.metadata["dataset_name"] = dsn
                artifact.metadata["lrecl"] = dsd.dcb.lrecl
                artifact.metadata["copybook"] = dsd.copybook
                artifact.metadata["program"] = dsd.program
                artifact.metadata["fields"] = [
                    {"name": f.name, "offset": f.offset, "length": f.length, "pic": f.pic}
                    for f in dsd.fields
                ]
            elif ext == ".dat":
                dat = parse_dat_file(path)
                self._dataset_results[artifact.id] = dat
                artifact.metadata["sample_record_count"] = len(dat.sample_records)
                artifact.metadata["inferred_lrecl"] = dat.dcb.lrecl

        elif artifact_type == ArtifactType.AFP:
            artifact.metadata["afp"] = True

    # ------------------------------------------------------------------
    # Edge derivation
    # ------------------------------------------------------------------

    def _resolve_artifact_id(self, name: str) -> Optional[str]:
        """Try to find an artifact id by name (stem, copybook name, etc.)."""
        upper = name.upper()
        # Direct stem lookup
        if upper in self._artifact_by_stem:
            return self._artifact_by_stem[upper]
        # Copybook name (without extension)
        key = _normalise_copybook_name(upper)
        if key in self._copybook_by_name:
            return self._copybook_by_name[key]
        # COBOL program name
        if upper in self._cobol_by_name:
            return self._cobol_by_name[upper]
        return None

    def _add_edge(
        self,
        source_id: str,
        target_id: str,
        kind: DependencyKind,
        line: int = 0,
    ) -> None:
        self.graph.edges.append(
            Dependency(
                source_id=source_id,
                target_id=target_id,
                kind=kind,
                location=SourceLocation(line=line),
            )
        )

    def _derive_copy_edges(self) -> None:
        """COBOL and copybook COPY statements → COPIES edges."""
        # COBOL programs
        for art_id, result in self._cobol_results.items():
            from zforge.ingestion.cobol_parser import CobolParseResult  # type: ignore[attr-defined]

            if not isinstance(result, CobolParseResult):
                continue
            for cpy_name, lineno in result.copy_statements:
                target_id = self._resolve_artifact_id(cpy_name)
                if target_id:
                    self._add_edge(art_id, target_id, DependencyKind.COPIES, lineno)
                else:
                    log.debug("COPY target not found: %s (from %s)", cpy_name, art_id)

        # Copybooks may COPY other copybooks
        for art_id, result in self._copybook_results.items():
            from zforge.ingestion.copybook_parser import (
                CopybookParseResult,  # type: ignore[attr-defined]
            )

            if not isinstance(result, CopybookParseResult):
                continue
            for cpy_name, lineno in result.copy_statements:
                target_id = self._resolve_artifact_id(cpy_name)
                if target_id:
                    self._add_edge(art_id, target_id, DependencyKind.COPIES, lineno)

    def _derive_call_edges(self) -> None:
        """COBOL CALL statements → CALLS edges."""
        for art_id, result in self._cobol_results.items():
            from zforge.ingestion.cobol_parser import CobolParseResult  # type: ignore[attr-defined]

            if not isinstance(result, CobolParseResult):
                continue
            for prog_name, lineno in result.call_statements:
                target_id = self._resolve_artifact_id(prog_name)
                if target_id:
                    self._add_edge(art_id, target_id, DependencyKind.CALLS, lineno)

    def _derive_jcl_edges(self) -> None:
        """JCL DD statements → READS_FROM / WRITES_TO + lineage edges."""
        for art_id, result in self._jcl_results.items():
            from zforge.ingestion.jcl_parser import JclParseResult  # type: ignore[attr-defined]

            if not isinstance(result, JclParseResult):
                continue

            for step in result.steps:
                pgm_id = self._resolve_artifact_id(step.pgm) if step.pgm else None

                for dd in step.dds:
                    if not dd.dsn:
                        continue
                    dsn_upper = dd.dsn.upper()
                    dsn_short = _normalise_dataset_name(dsn_upper)
                    dataset_id = self._dataset_by_name.get(dsn_upper) or self._dataset_by_name.get(
                        dsn_short
                    )

                    # JCL → dataset edge (USES_DD)
                    if dataset_id:
                        self._add_edge(art_id, dataset_id, DependencyKind.USES_DD, dd.line)

                    # Program → dataset read/write edge
                    if pgm_id and dataset_id:
                        if dd.is_output:
                            self._add_edge(pgm_id, dataset_id, DependencyKind.WRITES_TO, dd.line)
                        elif dd.is_input:
                            self._add_edge(pgm_id, dataset_id, DependencyKind.READS_FROM, dd.line)

                    # Data lineage edges
                    if pgm_id and dataset_id:
                        if dd.is_output:
                            self._lineage.append(
                                DataLineageEdge(
                                    producer_id=pgm_id,
                                    consumer_id=dataset_id,
                                    dataset_name=dd.dsn,
                                    dd_name=dd.ddname,
                                )
                            )
                        elif dd.is_input:
                            self._lineage.append(
                                DataLineageEdge(
                                    producer_id=dataset_id,
                                    consumer_id=pgm_id,
                                    dataset_name=dd.dsn,
                                    dd_name=dd.ddname,
                                )
                            )

    def _derive_hlasm_copy_edges(self) -> None:
        """HLASM COPY references → INCLUDES edges."""
        for art_id, result in self._hlasm_results.items():
            from zforge.ingestion.hlasm_parser import HlasmParseResult  # type: ignore[attr-defined]

            if not isinstance(result, HlasmParseResult):
                continue
            for ref_name, lineno in result.copy_references:
                target_id = self._resolve_artifact_id(ref_name)
                if target_id:
                    self._add_edge(art_id, target_id, DependencyKind.INCLUDES, lineno)


# ---------------------------------------------------------------------------
# Convenience entry point
# ---------------------------------------------------------------------------


def ingest_workspace(
    workspace_root: str | Path,
    persist: bool = True,
    graph_dir: Optional[str | Path] = None,
) -> DependencyGraph:
    """Ingest a workspace and return a DependencyGraph.

    If *persist* is True, writes dependency.json and lineage.json to
    *graph_dir* (default: workspace_root/graph/).
    """
    orchestrator = IngestionOrchestrator(workspace_root)
    graph = orchestrator.ingest()
    if persist:
        orchestrator.persist(graph_dir)
    return graph
