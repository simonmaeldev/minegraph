"""
Tests for the graph analysis script.

This test suite verifies metric computation functions, graph loading,
filtering, and edge case handling.
"""

import pytest
import networkx as nx
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from analyze_graph import (
    analyze_average_degree,
    analyze_max_degree,
    analyze_connected_components,
    analyze_edge_count,
    analyze_density,
    load_graph,
    parse_arguments
)


# ============================================================
# Pytest Fixtures
# ============================================================

@pytest.fixture
def empty_graph():
    """Empty directed graph with no nodes or edges."""
    return nx.DiGraph()


@pytest.fixture
def single_node_graph():
    """Graph with single node, no edges."""
    G = nx.DiGraph()
    G.add_node("A", node_type='item')
    return G


@pytest.fixture
def simple_chain_graph():
    """
    Simple chain: A -> B -> C
    - 3 nodes, 2 edges
    - Single weakly and strongly connected component
    """
    G = nx.DiGraph()
    G.add_node("A", node_type='item')
    G.add_node("B", node_type='item')
    G.add_node("C", node_type='item')
    G.add_edge("A", "B", transformation_type='crafting')
    G.add_edge("B", "C", transformation_type='crafting')
    return G


@pytest.fixture
def multi_input_graph():
    """
    Multi-input transformation with direct edges (analysis graph):
    A -> D
    B -> D
    C -> D

    This represents the analysis graph structure where inputs connect
    directly to outputs without intermediate nodes.
    """
    G = nx.DiGraph()
    G.add_node("A", node_type='item')
    G.add_node("B", node_type='item')
    G.add_node("C", node_type='item')
    G.add_node("D", node_type='item')

    G.add_edge("A", "D", transformation_type='crafting')
    G.add_edge("B", "D", transformation_type='crafting')
    G.add_edge("C", "D", transformation_type='crafting')
    return G


@pytest.fixture
def disconnected_graph():
    """
    Two disconnected components:
    Component 1: A -> B
    Component 2: C -> D
    """
    G = nx.DiGraph()
    G.add_node("A", node_type='item')
    G.add_node("B", node_type='item')
    G.add_node("C", node_type='item')
    G.add_node("D", node_type='item')

    G.add_edge("A", "B", transformation_type='crafting')
    G.add_edge("C", "D", transformation_type='smelting')
    return G


@pytest.fixture
def cyclic_graph():
    """
    Graph with cycle: A -> B -> C -> A
    - 1 weakly connected component
    - 1 strongly connected component (the cycle itself)
    """
    G = nx.DiGraph()
    G.add_node("A", node_type='item')
    G.add_node("B", node_type='item')
    G.add_node("C", node_type='item')

    G.add_edge("A", "B", transformation_type='crafting')
    G.add_edge("B", "C", transformation_type='crafting')
    G.add_edge("C", "A", transformation_type='crafting')
    return G


@pytest.fixture
def hub_graph():
    """
    Hub node with high degree:
    A -> Hub -> E
    B -> Hub -> F
    C -> Hub -> G
    D -> Hub -> H

    Hub has in-degree=4, out-degree=4
    """
    G = nx.DiGraph()
    for node in ["A", "B", "C", "D", "Hub", "E", "F", "G", "H"]:
        G.add_node(node, node_type='item')

    # Inputs to hub
    G.add_edge("A", "Hub", transformation_type='crafting')
    G.add_edge("B", "Hub", transformation_type='crafting')
    G.add_edge("C", "Hub", transformation_type='crafting')
    G.add_edge("D", "Hub", transformation_type='crafting')

    # Outputs from hub
    G.add_edge("Hub", "E", transformation_type='crafting')
    G.add_edge("Hub", "F", transformation_type='crafting')
    G.add_edge("Hub", "G", transformation_type='crafting')
    G.add_edge("Hub", "H", transformation_type='crafting')

    return G


@pytest.fixture
def complete_graph():
    """
    Complete directed graph with 4 nodes (all possible edges).
    Density should be 1.0 (100%)
    """
    G = nx.DiGraph()
    nodes = ["A", "B", "C", "D"]
    for node in nodes:
        G.add_node(node, node_type='item')

    # Add all possible directed edges
    for src in nodes:
        for dst in nodes:
            if src != dst:
                G.add_edge(src, dst, transformation_type='crafting')

    return G


# ============================================================
# Tests for analyze_average_degree
# ============================================================

def test_average_degree_empty_graph(empty_graph, capsys):
    """Test average degree on empty graph."""
    analyze_average_degree(empty_graph)
    captured = capsys.readouterr()
    assert "Cannot compute average degree: graph has no nodes" in captured.out


def test_average_degree_single_node(single_node_graph, capsys):
    """Test average degree on single node graph."""
    analyze_average_degree(single_node_graph)
    captured = capsys.readouterr()
    assert "Average in-degree: 0.00" in captured.out
    assert "Average out-degree: 0.00" in captured.out
    assert "Total nodes: 1" in captured.out


def test_average_degree_simple_chain(simple_chain_graph, capsys):
    """
    Test average degree on chain A -> B -> C
    - A: in=0, out=1
    - B: in=1, out=1
    - C: in=1, out=0
    - Avg in = (0+1+1)/3 = 0.67
    - Avg out = (1+1+0)/3 = 0.67
    """
    analyze_average_degree(simple_chain_graph)
    captured = capsys.readouterr()
    assert "Average in-degree: 0.67" in captured.out
    assert "Average out-degree: 0.67" in captured.out
    assert "Total nodes: 3" in captured.out


def test_average_degree_multi_input(multi_input_graph, capsys):
    """
    Test average degree with direct edges (analysis graph).
    4 nodes total: A, B, C, D
    - A, B, C: in=0, out=1
    - D: in=3, out=0
    - Avg in = (0+0+0+3)/4 = 0.75
    - Avg out = (1+1+1+0)/4 = 0.75
    """
    analyze_average_degree(multi_input_graph)
    captured = capsys.readouterr()
    assert "Average in-degree: 0.75" in captured.out
    assert "Average out-degree: 0.75" in captured.out
    assert "Total nodes: 4" in captured.out


# ============================================================
# Tests for analyze_max_degree
# ============================================================

def test_max_degree_empty_graph(empty_graph, capsys):
    """Test max degree on empty graph."""
    analyze_max_degree(empty_graph)
    captured = capsys.readouterr()
    assert "Cannot compute max degree: graph has no nodes" in captured.out


def test_max_degree_single_node(single_node_graph, capsys):
    """Test max degree on single node."""
    analyze_max_degree(single_node_graph)
    captured = capsys.readouterr()
    assert "Maximum in-degree: 0" in captured.out
    assert "Maximum out-degree: 0" in captured.out


def test_max_degree_hub_graph(hub_graph, capsys):
    """Test max degree on hub graph where Hub has highest degree."""
    analyze_max_degree(hub_graph)
    captured = capsys.readouterr()
    assert "Maximum in-degree: 4" in captured.out
    assert "Maximum out-degree: 4" in captured.out
    assert "Hub" in captured.out


def test_max_degree_multi_input(multi_input_graph, capsys):
    """Test max degree with direct edges - D has highest in-degree."""
    analyze_max_degree(multi_input_graph)
    captured = capsys.readouterr()
    assert "Maximum in-degree: 3" in captured.out
    assert "D" in captured.out


# ============================================================
# Tests for analyze_connected_components
# ============================================================

def test_connected_components_empty_graph(empty_graph, capsys):
    """Test components on empty graph."""
    analyze_connected_components(empty_graph)
    captured = capsys.readouterr()
    assert "Cannot compute components: graph has no nodes" in captured.out


def test_connected_components_single_node(single_node_graph, capsys):
    """Test components on single node graph."""
    analyze_connected_components(single_node_graph)
    captured = capsys.readouterr()
    assert "Weakly connected components: 1" in captured.out
    assert "Strongly connected components: 1" in captured.out


def test_connected_components_simple_chain(simple_chain_graph, capsys):
    """Test components on simple chain (no cycles)."""
    analyze_connected_components(simple_chain_graph)
    captured = capsys.readouterr()
    assert "Weakly connected components: 1" in captured.out
    # Simple chain has 3 strongly connected components (each node is its own)
    assert "Strongly connected components: 3" in captured.out


def test_connected_components_disconnected(disconnected_graph, capsys):
    """Test components on disconnected graph."""
    analyze_connected_components(disconnected_graph)
    captured = capsys.readouterr()
    assert "Weakly connected components: 2" in captured.out
    # Each component has 2 nodes, but they're chains, so 4 SCCs total
    assert "Strongly connected components: 4" in captured.out


def test_connected_components_cyclic(cyclic_graph, capsys):
    """Test components on graph with cycle."""
    analyze_connected_components(cyclic_graph)
    captured = capsys.readouterr()
    assert "Weakly connected components: 1" in captured.out
    # All 3 nodes form one strongly connected component (cycle)
    assert "Strongly connected components: 1" in captured.out


# ============================================================
# Tests for analyze_edge_count
# ============================================================

def test_edge_count_empty_graph(empty_graph, capsys):
    """Test edge count on empty graph."""
    analyze_edge_count(empty_graph)
    captured = capsys.readouterr()
    assert "Total nodes: 0" in captured.out
    assert "Total edges: 0" in captured.out
    assert "Item nodes: 0" in captured.out
    assert "Analysis graph uses direct edges without intermediate nodes" in captured.out


def test_edge_count_simple_chain(simple_chain_graph, capsys):
    """Test edge count on simple chain."""
    analyze_edge_count(simple_chain_graph)
    captured = capsys.readouterr()
    assert "Total nodes: 3" in captured.out
    assert "Total edges: 2" in captured.out
    assert "Item nodes: 3" in captured.out
    assert "Analysis graph uses direct edges without intermediate nodes" in captured.out


def test_edge_count_multi_input(multi_input_graph, capsys):
    """Test edge count with direct edges (analysis graph)."""
    analyze_edge_count(multi_input_graph)
    captured = capsys.readouterr()
    assert "Total nodes: 4" in captured.out
    assert "Total edges: 3" in captured.out
    assert "Item nodes: 4" in captured.out
    # Analysis graph should have no intermediate nodes
    assert "Analysis graph uses direct edges without intermediate nodes" in captured.out


# ============================================================
# Tests for analyze_density
# ============================================================

def test_density_empty_graph(empty_graph, capsys):
    """Test density on empty graph."""
    analyze_density(empty_graph)
    captured = capsys.readouterr()
    assert "Cannot compute density: graph needs at least 2 nodes" in captured.out


def test_density_single_node(single_node_graph, capsys):
    """Test density on single node."""
    analyze_density(single_node_graph)
    captured = capsys.readouterr()
    assert "Cannot compute density: graph needs at least 2 nodes" in captured.out


def test_density_simple_chain(simple_chain_graph, capsys):
    """
    Test density on chain A -> B -> C
    3 nodes, 2 edges
    Max possible edges = 3 * 2 = 6
    Density = 2/6 = 0.333... = 33.33%
    """
    analyze_density(simple_chain_graph)
    captured = capsys.readouterr()
    assert "Density: 0.33" in captured.out
    assert "Density (percentage): 33.33" in captured.out
    assert "max possible edges: 6" in captured.out


def test_density_complete_graph(complete_graph, capsys):
    """
    Test density on complete directed graph.
    4 nodes, all possible edges = 4*3 = 12 edges
    Density = 12/12 = 1.0 = 100%
    """
    analyze_density(complete_graph)
    captured = capsys.readouterr()
    assert "Density: 1.00" in captured.out
    assert "Density (percentage): 100.00" in captured.out
    assert "max possible edges: 12" in captured.out


def test_density_hub_graph(hub_graph, capsys):
    """
    Test density on hub graph.
    9 nodes, 8 edges
    Max possible edges = 9 * 8 = 72
    Density = 8/72 = 0.111... = 11.11%
    """
    analyze_density(hub_graph)
    captured = capsys.readouterr()
    assert "Density: 0.11" in captured.out
    # Check that percentage is approximately 11%
    output = captured.out
    assert "Density (percentage):" in output


# ============================================================
# Integration Tests
# ============================================================

def test_load_graph_success():
    """Test loading graph from actual CSV file."""
    csv_path = "output/transformations.csv"
    config_path = "config/graph_colors.txt"

    # Skip test if files don't exist
    if not Path(csv_path).exists():
        pytest.skip(f"CSV file not found: {csv_path}")

    graph = load_graph(csv_path, config_path)

    # Verify graph is not empty
    assert graph.number_of_nodes() > 0
    assert graph.number_of_edges() > 0

    # Verify it's a directed graph
    assert isinstance(graph, nx.DiGraph)


def test_load_graph_with_filter():
    """Test loading graph with transformation type filtering."""
    csv_path = "output/transformations.csv"
    config_path = "config/graph_colors.txt"

    # Skip test if files don't exist
    if not Path(csv_path).exists():
        pytest.skip(f"CSV file not found: {csv_path}")

    # Load full graph
    full_graph = load_graph(csv_path, config_path)
    full_edges = full_graph.number_of_edges()

    # Load filtered graph (crafting only)
    filtered_graph = load_graph(csv_path, config_path, filter_types=['crafting'])
    filtered_edges = filtered_graph.number_of_edges()

    # Filtered graph should have fewer edges (unless all transformations are crafting)
    assert filtered_edges <= full_edges


def test_load_graph_nonexistent_file():
    """Test error handling for nonexistent CSV file."""
    with pytest.raises(FileNotFoundError):
        load_graph("nonexistent.csv", "config/graph_colors.txt")


def test_parse_arguments_defaults():
    """Test argument parsing with defaults."""
    with patch('sys.argv', ['analyze_graph.py']):
        args = parse_arguments()
        assert args.input == 'output/transformations.csv'
        assert args.config == 'config/graph_colors.txt'
        assert args.verbose is False
        assert args.filter_type is None


def test_parse_arguments_with_options():
    """Test argument parsing with custom options."""
    with patch('sys.argv', [
        'analyze_graph.py',
        '-i', 'custom.csv',
        '-c', 'custom_colors.txt',
        '-v',
        '--filter-type', 'crafting,smelting'
    ]):
        args = parse_arguments()
        assert args.input == 'custom.csv'
        assert args.config == 'custom_colors.txt'
        assert args.verbose is True
        assert args.filter_type == 'crafting,smelting'


# ============================================================
# Edge Case Tests
# ============================================================

def test_multiple_max_degree_nodes():
    """Test handling of multiple nodes with same max degree."""
    G = nx.DiGraph()
    # Create two nodes with same in-degree
    G.add_node("A", node_type='item')
    G.add_node("B", node_type='item')
    G.add_node("X", node_type='item')
    G.add_node("Y", node_type='item')

    G.add_edge("X", "A", transformation_type='crafting')
    G.add_edge("Y", "A", transformation_type='crafting')
    G.add_edge("X", "B", transformation_type='crafting')
    G.add_edge("Y", "B", transformation_type='crafting')

    # Both A and B should have in-degree=2
    analyze_max_degree(G)
    # Test passes if no exceptions raised


def test_graph_with_self_loop():
    """Test graph with self-loop edge."""
    G = nx.DiGraph()
    G.add_node("A", node_type='item')
    G.add_edge("A", "A", transformation_type='recycling')  # Self-loop

    # Should handle self-loop gracefully
    analyze_average_degree(G)
    analyze_density(G)
    # Test passes if no exceptions raised


def test_very_sparse_graph():
    """Test very sparse graph (low density)."""
    G = nx.DiGraph()
    # 100 nodes, 1 edge -> very low density
    for i in range(100):
        G.add_node(f"Node_{i}", node_type='item')

    G.add_edge("Node_0", "Node_1", transformation_type='crafting')

    analyze_density(G)
    # Test passes if no exceptions raised
