"""
Tests for directed k-components algorithms:
weak_k_components and strong_k_components.

References
----------
Grannis, R. (2009). Paths and Semipaths: Reconceptualizing
Structural Cohesion in Terms of Directed Relations.
"""
import pytest
import networkx as nx

from networkx.algorithms.connectivity.kcomponents import (
    strong_k_components,
    weak_k_components,
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def assert_components_match(actual, expected):
    """
    Normalizes dictionaries containing lists of sets to ensure safe, 
    order-independent comparisons during assertions.
    """
    def normalize(comp_dict):
        return {
            k: sorted([sorted(list(component)) for component in components])
            for k, components in comp_dict.items()
        }
    
    assert normalize(actual) == normalize(expected)


# ============================================================
# GRAPH FACTORIES
# ============================================================

def build_simple_directed_cycle():
    G = nx.DiGraph()
    G.add_edges_from([(0, 1), (1, 2), (2, 3), (3, 0)])
    return G


def build_directed_two_components_with_bridge():
    G = nx.DiGraph()
    G.add_edges_from([(0, 1), (1, 2), (2, 0)])
    G.add_edges_from([(3, 4), (4, 5), (5, 3)])
    G.add_edge(2, 3) # One-way bridge
    return G


def build_directed_nested_components_graph():
    """
    Builds the topological edge-case trap (Grannis, Sec 3.1).
    A dense K4 core embedded inside a fragile 1-way loop.
    """
    G = nx.DiGraph()
    G.add_edges_from((u, v) for u in range(4) for v in range(4) if u != v)
    G.add_edges_from([(3, 4), (4, 5), (5, 0)])
    return G


def build_directed_complete_graph():
    G = nx.DiGraph()
    G.add_edges_from((u, v) for u in range(4) for v in range(4) if u != v)
    return G


def build_single_node_graph():
    G = nx.DiGraph()
    G.add_node(0)
    return G


def build_disconnected_directed_graph():
    G = nx.DiGraph()
    G.add_edges_from([(0, 1), (2, 3)])
    return G


def build_grannis_figure2_graph():
    """
    Recreates the directed graph from Grannis (2009) Figure 2, p.122
    for validation against Table 1(a).
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
    G = build_simple_directed_cycle()
    expected = {1: [{0, 1, 2, 3}], 2: [{0, 1, 2, 3}]}
    assert_components_match(weak_k_components(G), expected)


def test_weak_k_components_single_node():
    G = build_single_node_graph()
    assert weak_k_components(G) == {}


def test_weak_k_components_disconnected():
    G = build_disconnected_directed_graph()
    expected = {1: [{0, 1}, {2, 3}]}
    assert_components_match(weak_k_components(G), expected)


def test_weak_k_components_empty_graph():
    G = nx.DiGraph()
    assert weak_k_components(G) == {}


def test_weak_k_components_rejects_undirected():
    G = nx.petersen_graph()
    with pytest.raises(nx.NetworkXNotImplemented):
        weak_k_components(G)


def test_weak_k_components_complete_graph():
    G = build_directed_complete_graph()
    expected = {
        1: [{0, 1, 2, 3}],
        2: [{0, 1, 2, 3}],
        3: [{0, 1, 2, 3}],
    }
    assert_components_match(weak_k_components(G), expected)


def test_weak_k_components_grannis_figure2():
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
    G = build_simple_directed_cycle()
    expected = {1: [{0, 1, 2, 3}]}
    assert_components_match(strong_k_components(G), expected)


def test_strong_k_components_with_bridge():
    G = build_directed_two_components_with_bridge()
    result = strong_k_components(G)

    assert list(result.keys()) == [1]
    assert len(result[1]) == 2
    assert {0, 1, 2} in result[1]
    assert {3, 4, 5} in result[1]


def test_strong_k_components_complete_graph():
    G = build_directed_complete_graph()
    expected = {
        1: [{0, 1, 2, 3}],
        2: [{0, 1, 2, 3}],
        3: [{0, 1, 2, 3}],
    }
    assert_components_match(strong_k_components(G), expected)


def test_strong_k_components_recursive_extraction():
    """
    Validates Mayank's code review concern: ensures the algorithm
    extracts the inner core instead of mapping the parent SCC.
    """
    G = build_directed_nested_components_graph()
    expected = {
        1: [{0, 1, 2, 3, 4, 5}],
        2: [{0, 1, 2, 3}],
        3: [{0, 1, 2, 3}]
    }
    assert_components_match(strong_k_components(G), expected)


def test_strong_k_components_empty_graph():
    G = nx.DiGraph()
    assert strong_k_components(G) == {}


def test_strong_k_components_rejects_undirected():
    G = nx.petersen_graph()
    with pytest.raises(nx.NetworkXNotImplemented):
        strong_k_components(G)


def test_strong_k_components_disconnected():
    G = build_disconnected_directed_graph()
    assert strong_k_components(G) == {}


if __name__ == "__main__":
    pytest.main(["-v", __file__])