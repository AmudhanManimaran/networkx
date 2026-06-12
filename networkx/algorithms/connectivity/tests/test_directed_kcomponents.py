"""
Tests for directed k-components algorithms:
weak_k_components and strong_k_components.

Follows TDD and Clean Code principles (Robert C. Martin, 2008)
for modular test data management and explicit expected outputs.

References
----------
Grannis, R. (2009). Paths and Semipaths: Reconceptualizing
Structural Cohesion in Terms of Directed Relations.
Sociological Methodology, 39, 117-150.
https://www.jstor.org/stable/40376146
"""
import pytest
import networkx as nx

from networkx.algorithms.connectivity.kcomponents import (
    strong_k_components,
    weak_k_components,
)


# ============================================================
# GRAPH FACTORIES
# Each factory has a single responsibility — build one graph.
# ============================================================


def build_simple_directed_cycle():
    """
    Returns a simple directed cycle: 0->1->2->3->0.

    Removing any single node destroys the cycle path,
    making this graph 1-connected under strong rules,
    but 2-connected under weak rules (semipaths exist).
    """
    G = nx.DiGraph()
    G.add_edges_from([(0, 1), (1, 2), (2, 3), (3, 0)])
    return G


def build_directed_two_components_with_bridge():
    """
    Returns two directed cycles connected by a one-way bridge.

    Component 1: 0->1->2->0
    Component 2: 3->4->5->3
    Bridge:      2->3 (one-way only)

    The bridge is one-directional, so strong connectivity
    cannot cross it. Weak connectivity ignores this.
    """
    G = nx.DiGraph()
    G.add_edges_from([(0, 1), (1, 2), (2, 0)])
    G.add_edges_from([(3, 4), (4, 5), (5, 3)])
    G.add_edge(2, 3)
    return G


def build_directed_complete_graph():
    """
    Returns a directed complete graph K4.

    Every node connects to every other node in both directions.
    A 4-node complete directed graph is 3-connected because
    you must remove 3 nodes to disconnect any pair.
    """
    G = nx.DiGraph()
    nodes = [0, 1, 2, 3]
    for u in nodes:
        for v in nodes:
            if u != v:
                G.add_edge(u, v)
    return G


def build_single_node_graph():
    """
    Returns a directed graph with one node and no edges.

    A single node cannot form a k-component because
    k-connectivity requires at least two nodes.
    """
    G = nx.DiGraph()
    G.add_node(0)
    return G


def build_disconnected_directed_graph():
    """
    Returns two disconnected directed edges: 0->1 and 2->3.

    Neither edge forms a strongly connected component since
    you cannot return from node 1 to node 0, or 3 to 2.
    Weakly, each pair forms a separate 1-component.
    """
    G = nx.DiGraph()
    G.add_edges_from([(0, 1), (2, 3)])
    return G


def build_grannis_figure2_graph():
    """
    Returns the directed graph from Grannis (2009) Figure 2.

    7 nodes, 11 directed arcs. Used to validate weak
    k-connectivity against Table 1(a) known values.

    From Table 1(a):
    - Nodes 1,2,3,4,5,6 are weakly 2-connected
    - Node 7 has weak connectivity of only 1

    Reference:
    Grannis, R. (2009). Paths and Semipaths.
    Sociological Methodology, 39, 117-150. Figure 2, p.122.
    https://www.jstor.org/stable/40376146
    """
    G = nx.DiGraph()
    G.add_edges_from([
        (1, 2), (2, 3), (3, 1),
        (3, 4), (4, 1),
        (1, 5), (3, 5),
        (1, 6), (3, 6),
        (2, 4),
        (7, 1),
    ])
    return G


# ============================================================
# TESTS: WEAK K-COMPONENTS
# ============================================================


def test_weak_k_components_simple_cycle():
    """
    A 4-node directed cycle is 2-connected when direction
    is ignored because two independent semipaths connect
    any pair of nodes.
    """
    G = build_simple_directed_cycle()
    result = weak_k_components(G)
    expected = {1: [{0, 1, 2, 3}], 2: [{0, 1, 2, 3}]}
    assert result == expected


def test_weak_k_components_single_node():
    """
    A single isolated node cannot form any k-component.
    NetworkX requires at least 2 nodes for k=1.
    """
    G = build_single_node_graph()
    result = weak_k_components(G)
    assert result == {}


def test_weak_k_components_disconnected():
    """
    Two disconnected directed edges form two separate
    weak 1-components — one per connected pair.
    """
    G = build_disconnected_directed_graph()
    result = weak_k_components(G)
    expected = {1: [{0, 1}, {2, 3}]}
    assert result == expected


def test_weak_k_components_empty_graph():
    """
    An empty directed graph with no nodes or edges
    returns an empty dictionary — nothing to compute.
    """
    G = nx.DiGraph()
    result = weak_k_components(G)
    assert result == {}


def test_weak_k_components_rejects_undirected():
    """
    weak_k_components is designed only for directed graphs.
    For undirected graphs, use nx.k_components instead.
    """
    G = nx.petersen_graph()
    with pytest.raises(nx.NetworkXNotImplemented):
        weak_k_components(G)


def test_weak_k_components_complete_graph():
    """
    A complete directed graph K4 is 3-connected because
    you need to remove 3 nodes to disconnect any pair.
    All 4 nodes appear at k=1, k=2, and k=3.
    """
    G = build_directed_complete_graph()
    result = weak_k_components(G)
    expected = {
        1: [{0, 1, 2, 3}],
        2: [{0, 1, 2, 3}],
        3: [{0, 1, 2, 3}],
    }
    assert result == expected


def test_weak_k_components_grannis_figure2():
    """
    Validates against Grannis (2009) Table 1(a).

    Nodes 1-6 are weakly 2-connected to each other.
    Node 7 connects into the graph via one arc only,
    making it weakly 1-connected but not 2-connected.

    Reference: Grannis (2009), Table 1(a), p.123.
    """
    G = build_grannis_figure2_graph()
    result = weak_k_components(G)

    assert 1 in result
    assert {1, 2, 3, 4, 5, 6, 7} in result[1]

    assert 2 in result
    assert {1, 2, 3, 4, 5, 6} in result[2]

    for comp in result.get(2, []):
        assert 7 not in comp


# ============================================================
# TESTS: STRONG K-COMPONENTS
# ============================================================


def test_strong_k_components_simple_cycle():
    """
    A directed cycle is only 1-connected under strong rules.
    Removing any single node breaks the directional loop —
    no return path exists. It cannot be 2-connected.
    """
    G = build_simple_directed_cycle()
    result = strong_k_components(G)
    expected = {1: [{0, 1, 2, 3}]}
    assert result == expected


def test_strong_k_components_with_bridge():
    """
    A one-way bridge between two cycles creates two separate
    strong 1-components. Strong connectivity cannot cross
    a one-directional bridge because no return path exists.
    """
    G = build_directed_two_components_with_bridge()
    result = strong_k_components(G)

    assert list(result.keys()) == [1]
    assert len(result[1]) == 2
    assert {0, 1, 2} in result[1]
    assert {3, 4, 5} in result[1]


def test_strong_k_components_complete_graph():
    """
    A complete directed K4 graph has bidirectional edges
    between all pairs. It is 3-connected because three
    independent directed paths exist between every pair.
    """
    G = build_directed_complete_graph()
    result = strong_k_components(G)
    expected = {
        1: [{0, 1, 2, 3}],
        2: [{0, 1, 2, 3}],
        3: [{0, 1, 2, 3}],
    }
    assert result == expected


def test_strong_k_components_empty_graph():
    """
    An empty directed graph returns an empty dictionary.
    No strongly connected components exist with 2+ nodes.
    """
    G = nx.DiGraph()
    result = strong_k_components(G)
    assert result == {}


def test_strong_k_components_rejects_undirected():
    """
    strong_k_components is designed only for directed graphs.
    Passing an undirected graph raises NetworkXNotImplemented.
    """
    G = nx.petersen_graph()
    with pytest.raises(nx.NetworkXNotImplemented):
        strong_k_components(G)


def test_strong_k_components_disconnected():
    """
    Two disconnected one-way edges form no strongly connected
    components. Nodes 0,1 and 2,3 cannot return to their
    source, so strong connectivity is zero for all pairs.
    """
    G = build_disconnected_directed_graph()
    result = strong_k_components(G)
    assert result == {}


if __name__ == "__main__":
    pytest.main(["-v", __file__])