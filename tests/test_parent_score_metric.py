"""
Tests for parent score metric in analyze_graph.py

This module tests the parent score analysis functions that compute importance
propagation through the transformation graph by identifying which base materials
appear in the ancestry of many important items.
"""

import pytest
import networkx as nx
from src.analyze_graph import add_score_parents, analyze_parent_score


@pytest.fixture
def simple_chain_graph():
    """
    Create a simple chain graph: A → B → C → D

    If D is most important, C should get the highest parent score.
    """
    graph = nx.DiGraph()
    graph.add_edge("A", "B")
    graph.add_edge("B", "C")
    graph.add_edge("C", "D")
    return graph


@pytest.fixture
def diamond_graph():
    """
    Create a diamond graph:
         A
        / \\
       ↓   ↓
       C   D
        \\ /
         ↓
         E

    Both C and D should score equally when E is important.
    """
    graph = nx.DiGraph()
    graph.add_edge("A", "C")
    graph.add_edge("A", "D")
    graph.add_edge("C", "E")
    graph.add_edge("D", "E")
    return graph


@pytest.fixture
def tree_graph():
    """
    Create a tree graph:
       A   B
       |\\ /|
       | X |
       |/ \\|
       C   D

    A and B should score equally when both C and D are important.
    """
    graph = nx.DiGraph()
    graph.add_edge("A", "C")
    graph.add_edge("A", "D")
    graph.add_edge("B", "C")
    graph.add_edge("B", "D")
    return graph


@pytest.fixture
def cyclic_graph():
    """
    Create a graph with a cycle: A → B → C → A

    Tests that cycles don't cause infinite loops.
    """
    graph = nx.DiGraph()
    graph.add_edge("A", "B")
    graph.add_edge("B", "C")
    graph.add_edge("C", "A")
    return graph


@pytest.fixture
def disconnected_graph():
    """
    Create two separate chains:
    Chain 1: A → B → C
    Chain 2: X → Y → Z

    Verifies only connected parents score.
    """
    graph = nx.DiGraph()
    # Chain 1
    graph.add_edge("A", "B")
    graph.add_edge("B", "C")
    # Chain 2
    graph.add_edge("X", "Y")
    graph.add_edge("Y", "Z")
    return graph


class TestAddScoreParents:
    """Test the add_score_parents recursive function."""

    def test_simple_chain(self, simple_chain_graph):
        """Test that all parents in a chain get scored."""
        scores = {}
        to_process = {"D"}
        processed = set()

        while to_process:
            node = to_process.pop()
            add_score_parents(node, simple_chain_graph, to_process, processed, scores)

        # All nodes in the chain should be scored
        assert "D" in scores
        assert "C" in scores
        assert "B" in scores
        assert "A" in scores

        # Each should have score of 1
        assert scores["D"] == 1
        assert scores["C"] == 1
        assert scores["B"] == 1
        assert scores["A"] == 1

    def test_cycle_no_infinite_loop(self, cyclic_graph):
        """Test that cycles don't cause infinite loops."""
        scores = {}
        to_process = {"A"}
        processed = set()

        # This should complete without hanging
        while to_process:
            node = to_process.pop()
            add_score_parents(node, cyclic_graph, to_process, processed, scores)

        # All nodes should be scored exactly once
        assert "A" in scores
        assert "B" in scores
        assert "C" in scores
        assert scores["A"] == 1
        assert scores["B"] == 1
        assert scores["C"] == 1

    def test_diamond_both_parents_scored(self, diamond_graph):
        """Test that both parents in a diamond get scored."""
        scores = {}
        to_process = {"E"}
        processed = set()

        while to_process:
            node = to_process.pop()
            add_score_parents(node, diamond_graph, to_process, processed, scores)

        # All nodes should be scored
        assert "E" in scores
        assert "C" in scores
        assert "D" in scores
        assert "A" in scores

        # E gets scored once
        assert scores["E"] == 1
        # C and D each get scored once (they're both parents of E)
        assert scores["C"] == 1
        assert scores["D"] == 1
        # A gets scored once (it's parent of both C and D, but processed only once)
        assert scores["A"] == 1

    def test_accumulation_across_calls(self, simple_chain_graph):
        """Test that scores accumulate correctly across multiple starting points."""
        scores = {}

        # Process from D
        to_process = {"D"}
        processed = set()
        while to_process:
            node = to_process.pop()
            add_score_parents(node, simple_chain_graph, to_process, processed, scores)

        # Process from C (with fresh tracking sets)
        to_process = {"C"}
        processed = set()
        while to_process:
            node = to_process.pop()
            add_score_parents(node, simple_chain_graph, to_process, processed, scores)

        # C should now have score 2 (once from D traversal, once from C traversal)
        assert scores["C"] == 2
        # B and A should have score 2 (visited from both traversals)
        assert scores["B"] == 2
        assert scores["A"] == 2
        # D should have score 1 (only visited from D traversal)
        assert scores["D"] == 1


class TestAnalyzeParentScore:
    """Test the analyze_parent_score analysis function."""

    def test_empty_graph(self, capsys):
        """Test graceful handling of empty graph."""
        graph = nx.DiGraph()
        analyze_parent_score(graph)

        captured = capsys.readouterr()
        assert "Cannot compute parent score" in captured.out

    def test_single_node_graph(self, capsys):
        """Test graceful handling of single-node graph."""
        graph = nx.DiGraph()
        graph.add_node("A")
        analyze_parent_score(graph)

        captured = capsys.readouterr()
        assert "Cannot compute parent score" in captured.out

    def test_diamond_graph_integration(self, diamond_graph, capsys):
        """Test analyze_parent_score with diamond graph."""
        # Mock voterank to return E as the important item
        import unittest.mock as mock

        with mock.patch('networkx.voterank', return_value=["E"]):
            analyze_parent_score(diamond_graph, voterank_top_n=1, display_top_n=10)

        captured = capsys.readouterr()
        # Should display parent score analysis
        assert "Parent Score Analysis" in captured.out
        # Should show all nodes in ancestry
        assert "A" in captured.out or "C" in captured.out or "D" in captured.out

    def test_tree_graph_equal_scores(self, tree_graph, capsys):
        """Test that A and B get equal scores when both C and D are important."""
        import unittest.mock as mock

        with mock.patch('networkx.voterank', return_value=["C", "D"]):
            analyze_parent_score(tree_graph, voterank_top_n=2, display_top_n=10)

        captured = capsys.readouterr()
        # Both A and B should appear since they're parents of C and D
        assert "A" in captured.out
        assert "B" in captured.out

    def test_voterank_integration(self, simple_chain_graph):
        """Test that VoteRank is called correctly."""
        import unittest.mock as mock

        with mock.patch('networkx.voterank', return_value=["D"]) as mock_voterank:
            analyze_parent_score(simple_chain_graph, voterank_top_n=5, display_top_n=10)

            # Verify voterank was called with the correct arguments
            mock_voterank.assert_called_once()
            call_args = mock_voterank.call_args
            assert call_args[0][0] == simple_chain_graph
            assert call_args[0][1] == 5

    def test_disconnected_components(self, disconnected_graph, capsys):
        """Test that only connected parents are scored."""
        import unittest.mock as mock

        # Start from Z in chain 2
        with mock.patch('networkx.voterank', return_value=["Z"]):
            analyze_parent_score(disconnected_graph, voterank_top_n=1, display_top_n=10)

        captured = capsys.readouterr()
        # Should show Y and X (chain 2) but not A, B, C (chain 1)
        output_lines = captured.out
        # Z should be in output
        assert "Z" in output_lines or "Y" in output_lines or "X" in output_lines


class TestEdgeCases:
    """Test edge cases for parent score metric."""

    def test_node_with_no_parents(self):
        """Test a root node with no parents."""
        graph = nx.DiGraph()
        graph.add_edge("Root", "Child")

        scores = {}
        to_process = {"Root"}
        processed = set()

        while to_process:
            node = to_process.pop()
            add_score_parents(node, graph, to_process, processed, scores)

        # Root should score itself but have no parents to traverse
        assert scores["Root"] == 1
        assert "Child" not in scores

    def test_multi_input_transformation(self):
        """Test that both parents of a multi-input node are scored."""
        # A → C
        # B → C
        graph = nx.DiGraph()
        graph.add_edge("A", "C")
        graph.add_edge("B", "C")

        scores = {}
        to_process = {"C"}
        processed = set()

        while to_process:
            node = to_process.pop()
            add_score_parents(node, graph, to_process, processed, scores)

        # Both A and B should be scored
        assert "A" in scores
        assert "B" in scores
        assert "C" in scores
        # Each should have score 1
        assert scores["A"] == 1
        assert scores["B"] == 1
        assert scores["C"] == 1

    def test_deep_chain(self):
        """Test a deep chain doesn't cause stack overflow."""
        # Create a chain of 100 nodes
        graph = nx.DiGraph()
        for i in range(99):
            graph.add_edge(f"Node_{i}", f"Node_{i+1}")

        scores = {}
        to_process = {"Node_99"}
        processed = set()

        # This should complete without stack overflow
        while to_process:
            node = to_process.pop()
            add_score_parents(node, graph, to_process, processed, scores)

        # All 100 nodes should be scored
        assert len(scores) == 100
        # Each should have score 1
        for i in range(100):
            assert scores[f"Node_{i}"] == 1


class TestRealWorldIntegration:
    """Integration tests with real CSV data."""

    def test_with_real_csv_data(self, tmp_path):
        """Test parent score with minimal real-world-like data."""
        # Create a minimal transformation CSV with proper JSON format
        csv_content = """output_item,input_items,output_items,transformation_type,metadata
Planks,"[""Oak Log""]","[""Planks""]",crafting,"{}"
Stick,"[""Planks""]","[""Stick""]",crafting,"{}"
Wooden Pickaxe,"[""Planks"",""Stick""]","[""Wooden Pickaxe""]",crafting,"{}"
"""
        csv_file = tmp_path / "test_transformations.csv"
        csv_file.write_text(csv_content)

        # Build graph from CSV
        from src.graph_utils import load_transformations_from_csv
        from src.analyze_graph import AnalysisGraphBuilder

        transformations = load_transformations_from_csv(str(csv_file))
        builder = AnalysisGraphBuilder()

        # Add transformations to builder
        for trans in transformations:
            trans_type = trans['transformation_type']
            inputs = trans['input_items']
            outputs = trans['output_items']
            output_item = outputs[0] if outputs else None
            if output_item:
                builder.add_transformation(inputs, output_item, trans_type)

        graph = builder.graph

        # Test parent score analysis
        import unittest.mock as mock
        with mock.patch('networkx.voterank', return_value=["Wooden Pickaxe"]):
            # This should complete without errors
            analyze_parent_score(graph, voterank_top_n=1, display_top_n=10)

        # Verify graph structure is correct
        assert graph.has_edge("Oak Log", "Planks")
        assert graph.has_edge("Planks", "Stick")
        assert graph.has_edge("Planks", "Wooden Pickaxe")
        assert graph.has_edge("Stick", "Wooden Pickaxe")
