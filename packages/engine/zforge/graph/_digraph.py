"""Lightweight directed graph — Python 3.14 compatible networkx shim.

NetworkX 3.x uses dataclass(slots=True, kw_only=True) which crashes
on Python 3.14.  This module provides just the subset of networkx
DiGraph API used by the graph package, without that dependency.

If networkx ever becomes importable we transparently use it instead.
"""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Any, Generator, Iterator


class DiGraph:
    """Minimal directed graph compatible with networkx DiGraph API subset."""

    def __init__(self) -> None:
        self._nodes: dict[str, dict[str, Any]] = {}
        self._adj: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
        self._pred: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)

    # --- Node operations ---

    def add_node(self, node_id: str, **attrs: Any) -> None:
        if node_id not in self._nodes:
            self._nodes[node_id] = {}
            # Ensure adjacency entries exist
            if node_id not in self._adj:
                self._adj[node_id] = {}
            if node_id not in self._pred:
                self._pred[node_id] = {}
        self._nodes[node_id].update(attrs)

    @property
    def nodes(self) -> "_NodeView":
        return _NodeView(self)

    def __contains__(self, node_id: str) -> bool:
        return node_id in self._nodes

    def __iter__(self) -> Iterator[str]:
        return iter(self._nodes)

    def __len__(self) -> int:
        return len(self._nodes)

    # --- Edge operations ---

    def add_edge(self, u: str, v: str, **attrs: Any) -> None:
        if u not in self._nodes:
            self.add_node(u)
        if v not in self._nodes:
            self.add_node(v)
        self._adj[u][v] = attrs
        self._pred[v][u] = attrs

    def edges(self, data: bool = False) -> "_EdgeView":
        return _EdgeView(self, data=data)

    def in_degree(self, node_id: str) -> int:
        return len(self._pred.get(node_id, {}))

    def out_degree(self, node_id: str) -> int:
        return len(self._adj.get(node_id, {}))

    def predecessors(self, node_id: str) -> Iterator[str]:
        return iter(self._pred.get(node_id, {}).keys())

    def successors(self, node_id: str) -> Iterator[str]:
        return iter(self._adj.get(node_id, {}).keys())

    def subgraph(self, nodes: Any) -> "DiGraph":
        node_set = set(nodes)
        g = DiGraph()
        for n in node_set:
            if n in self._nodes:
                g.add_node(n, **self._nodes[n])
        for u in node_set:
            for v, attrs in self._adj.get(u, {}).items():
                if v in node_set:
                    g.add_edge(u, v, **attrs)
        return g

    def copy(self) -> "DiGraph":
        return self.subgraph(self._nodes.keys())

    def __getitem__(self, node_id: str) -> dict[str, Any]:
        return self._nodes[node_id]

    def get_edge_data(self, u: str, v: str) -> dict[str, Any] | None:
        return self._adj.get(u, {}).get(v)


class _NodeView:
    def __init__(self, g: DiGraph) -> None:
        self._g = g

    def __iter__(self) -> Iterator[str]:
        return iter(self._g._nodes)

    def __len__(self) -> int:
        return len(self._g._nodes)

    def __contains__(self, item: str) -> bool:
        return item in self._g._nodes

    def data(self, attr: str | None = None) -> Iterator[tuple[str, Any]]:
        for nid, attrs in self._g._nodes.items():
            yield (nid, attrs.get(attr) if attr else attrs)


class _EdgeView:
    def __init__(self, g: DiGraph, data: bool = False) -> None:
        self._g = g
        self._data = data

    def __iter__(self) -> Iterator[Any]:
        for u, nbrs in self._g._adj.items():
            for v, attrs in nbrs.items():
                if self._data:
                    yield (u, v, attrs)
                else:
                    yield (u, v)

    def __len__(self) -> int:
        return sum(len(nbrs) for nbrs in self._g._adj.values())


# ---------------------------------------------------------------------------
# Graph algorithms
# ---------------------------------------------------------------------------


def ancestors(g: DiGraph, node_id: str) -> set[str]:
    """Return all ancestors (nodes that can reach *node_id*)."""
    visited: set[str] = set()
    queue: deque[str] = deque([node_id])
    while queue:
        n = queue.popleft()
        for pred in g.predecessors(n):
            if pred not in visited:
                visited.add(pred)
                queue.append(pred)
    return visited


def descendants(g: DiGraph, node_id: str) -> set[str]:
    """Return all descendants (nodes reachable from *node_id*)."""
    visited: set[str] = set()
    queue: deque[str] = deque([node_id])
    while queue:
        n = queue.popleft()
        for succ in g.successors(n):
            if succ not in visited:
                visited.add(succ)
                queue.append(succ)
    return visited


def topological_sort(g: DiGraph) -> list[str]:
    """Kahn's algorithm — raises ValueError on cycle."""
    in_deg: dict[str, int] = {n: g.in_degree(n) for n in g.nodes}
    queue: deque[str] = deque(n for n, d in in_deg.items() if d == 0)
    result: list[str] = []
    while queue:
        n = queue.popleft()
        result.append(n)
        for succ in g.successors(n):
            in_deg[succ] -= 1
            if in_deg[succ] == 0:
                queue.append(succ)
    if len(result) != len(g.nodes):
        raise ValueError("Graph contains a cycle")
    return result


def all_simple_paths(g: DiGraph, source: str, target: str) -> Generator[list[str], None, None]:
    """Yield all simple paths from source to target (DFS)."""
    stack: list[tuple[str, list[str]]] = [(source, [source])]
    while stack:
        node, path = stack.pop()
        if node == target:
            yield list(path)
            continue
        for succ in g.successors(node):
            if succ not in path:
                stack.append((succ, path + [succ]))


class NetworkXUnfeasible(Exception):
    pass


class NetworkXNoPath(Exception):
    pass


class NodeNotFound(Exception):
    pass


def node_link_data(g: DiGraph) -> dict[str, Any]:
    """Produce a node-link JSON-serialisable dict (networkx-compatible format)."""
    nodes = [{"id": nid, **attrs} for nid, attrs in g._nodes.items()]
    links = [
        {"source": u, "target": v, **attrs}
        for u, nbrs in g._adj.items()
        for v, attrs in nbrs.items()
    ]
    return {"directed": True, "multigraph": False, "nodes": nodes, "links": links}
