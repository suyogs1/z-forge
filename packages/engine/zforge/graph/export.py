"""Graph export.

Emits blast_radius_graph.json for the future React UI.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from zforge.graph._digraph import node_link_data
from zforge.graph.blast_radius import BlastRadiusResult
from zforge.graph.builder import build_nx_graph
from zforge.models import DependencyGraph


def export_dependency_graph(
    dep_graph: DependencyGraph,
    output_path: str | Path,
) -> None:
    """Export the full dependency graph as a node-link JSON file."""
    g = build_nx_graph(dep_graph)
    data = node_link_data(g)

    # Replace non-serialisable Artifact objects with dicts
    for node in data["nodes"]:
        art = node.pop("artifact", None)
        if art is not None:
            node["artifact"] = art.model_dump(exclude={"raw_content"})

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(json.dumps(data, indent=2), encoding="utf-8")


def export_blast_radius(
    result: BlastRadiusResult,
    dep_graph: DependencyGraph,
    output_path: str | Path,
) -> None:
    """Export a blast-radius result as a graph JSON for the React UI."""
    g = build_nx_graph(dep_graph)

    impacted_ids = {ai.artifact.id for ai in result.impacted}
    inspected_ids = {ai.artifact.id for ai in result.inspected_unchanged}
    impact_map: dict[str, tuple[str, str]] = {}
    for ai in result.impacted:
        impact_map[ai.artifact.id] = (ai.reason.value, ai.details)
    for ai in result.inspected_unchanged:
        impact_map[ai.artifact.id] = (ai.reason.value, ai.details)

    relevant_ids = impacted_ids | inspected_ids

    nodes: list[dict[str, Any]] = []
    for node_id in relevant_ids:
        art = dep_graph.artifacts.get(node_id)
        if art is None:
            continue
        status = "impacted" if node_id in impacted_ids else "inspected"
        reason, details = impact_map.get(node_id, ("", ""))
        nodes.append(
            {
                "id": node_id,
                "label": art.path.rsplit("/", 1)[-1],
                "path": art.path,
                "type": art.type.value,
                "impact_status": status,
                "reason": reason,
                "details": details,
            }
        )

    edges: list[dict[str, Any]] = []
    for u, v, data in g.edges(data=True):
        if u in relevant_ids and v in relevant_ids:
            edges.append(
                {
                    "source": u,
                    "target": v,
                    "kind": data.get("kind", ""),
                }
            )

    output: dict[str, Any] = {
        "field_name": result.field_name,
        "change_description": result.change_description,
        "adversarial_findings": result.adversarial_findings,
        "nodes": nodes,
        "edges": edges,
    }

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(json.dumps(output, indent=2), encoding="utf-8")
