"""Graph builder.

Builds a directed graph from a DependencyGraph model, preserving
DependencyKind edge attributes and SourceLocation information.

Uses the internal _digraph module (Python-3.14-safe) instead of networkx
directly, since networkx 3.x crashes on Python 3.14 due to a dataclass
slots+kw_only issue.
"""

from __future__ import annotations

from zforge.graph._digraph import (
    DiGraph,
    NetworkXUnfeasible,
    ancestors,
    descendants,
    topological_sort,
)
from zforge.models import (
    Artifact,
    DependencyGraph,
    DependencyKind,
)


def build_nx_graph(dep_graph: DependencyGraph) -> DiGraph:
    """Build a DiGraph from a DependencyGraph model.

    Nodes carry the full Artifact as an ``artifact`` attribute.
    Edges carry ``kind`` (DependencyKind value string) and ``line`` attrs.
    """
    g: DiGraph = DiGraph()

    for art_id, artifact in dep_graph.artifacts.items():
        g.add_node(
            art_id,
            artifact=artifact,
            label=_node_label(artifact),
            type=artifact.type.value,
        )

    for edge in dep_graph.edges:
        if edge.source_id not in g or edge.target_id not in g:
            continue
        g.add_edge(
            edge.source_id,
            edge.target_id,
            kind=edge.kind.value,
            line=edge.location.line,
        )

    return g


def _node_label(artifact: Artifact) -> str:
    return artifact.path.rsplit("/", 1)[-1]


def topological_sort_artifacts(
    dep_graph: DependencyGraph,
    artifact_ids: list[str],
) -> list[str]:
    """Return *artifact_ids* sorted in dependency order (dependencies first)."""
    g = build_nx_graph(dep_graph)

    # Include ancestors to give topo sort enough context
    nodes_to_include: set[str] = set(artifact_ids)
    for art_id in artifact_ids:
        if art_id in g:
            nodes_to_include.update(ancestors(g, art_id))

    sub = g.subgraph(nodes_to_include).copy()

    try:
        topo = topological_sort(sub)
    except (ValueError, NetworkXUnfeasible):
        topo = list(nodes_to_include)

    # topo gives sources first (nodes with no incoming edges first).
    # In our graph A → B means "A depends on B" (A COPIES B).
    # We want dependencies first: CUSTMAST before ACCTMAST before ACCTPROG.
    # CUSTMAST has no incoming edges in the sub (nobody COPIES it in our set)
    # but it DOES have outgoing edges. Standard topo puts it last in reverse.
    # We want the REVERSE of standard topo: dependencies (targets of edges) first.
    topo_reversed = list(reversed(topo))

    requested = set(artifact_ids)
    ordered = [n for n in topo_reversed if n in requested]
    seen = set(ordered)
    ordered.extend(n for n in artifact_ids if n not in seen)
    return ordered


def ancestors_of(g: DiGraph, node_id: str) -> set[str]:
    return ancestors(g, node_id)


def descendants_of(g: DiGraph, node_id: str) -> set[str]:
    return descendants(g, node_id)


def edges_of_kind(g: DiGraph, kind: DependencyKind) -> list[tuple[str, str]]:
    return [(u, v) for u, v, data in g.edges(data=True) if data.get("kind") == kind.value]
