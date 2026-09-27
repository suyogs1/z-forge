"""Data lineage traversal.

Given a dataset artifact, identifies:
- Direct producers (programs that write to the dataset)
- Direct consumers (programs that read from the dataset)
- Chained dependencies (dataset → program → dataset chains through JCL workflow)
"""

from __future__ import annotations

from dataclasses import dataclass, field

from zforge.graph._digraph import (
    DiGraph,
    NetworkXNoPath,
    NodeNotFound,
    all_simple_paths,
    ancestors,
    descendants,
)
from zforge.graph.builder import build_nx_graph
from zforge.models import (
    Artifact,
    ArtifactType,
    DependencyGraph,
    DependencyKind,
)


@dataclass
class LineageResult:
    dataset_name: str
    dataset_id: str
    producers: list[Artifact] = field(default_factory=list)
    consumers: list[Artifact] = field(default_factory=list)
    downstream_datasets: list[Artifact] = field(default_factory=list)
    upstream_datasets: list[Artifact] = field(default_factory=list)
    lineage_chain: list[str] = field(default_factory=list)  # ordered path of artifact ids


def dataset_lineage(
    dataset_id: str,
    dep_graph: DependencyGraph,
) -> LineageResult:
    """Return full lineage for a dataset artifact."""
    artifacts = dep_graph.artifacts
    dataset_art = artifacts.get(dataset_id)
    ds_name = dataset_art.metadata.get("dataset_name", "") if dataset_art else ""

    result = LineageResult(dataset_name=ds_name, dataset_id=dataset_id)

    # Build lineage graph from DataLineageEdge list
    lg: DiGraph = DiGraph()
    for art_id in artifacts:
        lg.add_node(art_id)
    for edge in dep_graph.lineage:
        lg.add_edge(edge.producer_id, edge.consumer_id, dataset=edge.dataset_name, dd=edge.dd_name)

    g = build_nx_graph(dep_graph)

    # Direct producers: WRITES_TO edge to this dataset
    for source, target, data in g.edges(data=True):
        if target != dataset_id:
            continue
        if data.get("kind") == DependencyKind.WRITES_TO.value:
            art = artifacts.get(source)
            if art:
                result.producers.append(art)

    # Producers from lineage edges
    for edge in dep_graph.lineage:
        if edge.consumer_id == dataset_id:
            art = artifacts.get(edge.producer_id)
            if art and art not in result.producers:
                result.producers.append(art)

    # Direct consumers: READS_FROM edge from this dataset
    for source, target, data in g.edges(data=True):
        if source != dataset_id:
            continue
        if data.get("kind") == DependencyKind.READS_FROM.value:
            art = artifacts.get(target)
            if art:
                result.consumers.append(art)

    # Consumers from lineage edges
    for edge in dep_graph.lineage:
        if edge.producer_id == dataset_id:
            art = artifacts.get(edge.consumer_id)
            if art and art not in result.consumers:
                result.consumers.append(art)

    # Downstream datasets: follow lineage graph forward
    for node_id in descendants(lg, dataset_id):
        art = artifacts.get(node_id)
        if art and art.type == ArtifactType.DATASET and node_id != dataset_id:
            result.downstream_datasets.append(art)

    # Upstream datasets: follow lineage graph backward
    for node_id in ancestors(lg, dataset_id):
        art = artifacts.get(node_id)
        if art and art.type == ArtifactType.DATASET and node_id != dataset_id:
            result.upstream_datasets.append(art)

    # Lineage chain
    upstream_nodes = list(ancestors(lg, dataset_id))
    downstream_nodes = list(descendants(lg, dataset_id))
    result.lineage_chain = upstream_nodes + [dataset_id] + downstream_nodes

    return result


def all_lineage_paths(dep_graph: DependencyGraph) -> list[list[str]]:
    """Return all simple paths in the lineage graph as lists of artifact ids."""
    lg: DiGraph = DiGraph()
    for art_id in dep_graph.artifacts:
        lg.add_node(art_id)
    for edge in dep_graph.lineage:
        lg.add_edge(edge.producer_id, edge.consumer_id)

    sources = [n for n in lg.nodes if lg.in_degree(n) == 0 and lg.out_degree(n) > 0]
    sinks = [n for n in lg.nodes if lg.out_degree(n) == 0 and lg.in_degree(n) > 0]

    paths: list[list[str]] = []
    for src in sources:
        for sink in sinks:
            try:
                for path in all_simple_paths(lg, src, sink):
                    paths.append(path)
            except (NetworkXNoPath, NodeNotFound):
                pass
    return paths
