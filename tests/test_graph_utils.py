"""Tests for graph_utils module."""

import csv
import json
import tempfile
from pathlib import Path

import networkx as nx
import pytest

from src.graph_utils import (
    Graph3DBuilder,
    load_transformations_from_csv,
    build_graph_from_csv,
    get_visual_subgraph,
)


class TestGraph3DBuilder:
    """Test Graph3DBuilder class."""

    def test_add_item_node(self):
        """Test adding item nodes to graph."""
        builder = Graph3DBuilder()
        builder.add_item_node("Oak Log")

        assert builder.graph.has_node("Oak Log")
        assert builder.graph.nodes["Oak Log"]["node_type"] == "item"

    def test_add_item_node_duplicate(self):
        """Test adding duplicate item nodes doesn't create duplicates."""
        builder = Graph3DBuilder()
        builder.add_item_node("Oak Log")
        builder.add_item_node("Oak Log")

        assert builder.graph.number_of_nodes() == 1

    def test_create_intermediate_node(self):
        """Test creating intermediate nodes."""
        builder = Graph3DBuilder()
        node1 = builder.create_intermediate_node()
        node2 = builder.create_intermediate_node()

        assert node1 == "intermediate_0"
        assert node2 == "intermediate_1"
        assert builder.graph.nodes[node1]["node_type"] == "intermediate"
        assert builder.graph.nodes[node2]["node_type"] == "intermediate"

    def test_add_single_input_transformation(self):
        """Test adding single-input transformation."""
        builder = Graph3DBuilder()
        builder.add_single_input_transformation("Oak Log", "Oak Planks", "crafting")

        assert builder.graph.has_node("Oak Log")
        assert builder.graph.has_node("Oak Planks")
        assert builder.graph.has_edge("Oak Log", "Oak Planks")
        assert builder.graph.edges["Oak Log", "Oak Planks"]["transformation_type"] == "crafting"

    def test_add_multi_input_transformation(self):
        """Test adding multi-input transformation with intermediate node."""
        builder = Graph3DBuilder()
        builder.add_multi_input_transformation(
            ["Oak Planks", "Stick"],
            "Wooden Pickaxe",
            "crafting"
        )

        # Check all input and output nodes exist
        assert builder.graph.has_node("Oak Planks")
        assert builder.graph.has_node("Stick")
        assert builder.graph.has_node("Wooden Pickaxe")

        # Check intermediate node was created
        assert builder.intermediate_counter == 1
        intermediate = "intermediate_0"
        assert builder.graph.has_node(intermediate)

        # Check edges
        assert builder.graph.has_edge("Oak Planks", intermediate)
        assert builder.graph.has_edge("Stick", intermediate)
        assert builder.graph.has_edge(intermediate, "Wooden Pickaxe")


class TestLoadTransformationsFromCSV:
    """Test load_transformations_from_csv function."""

    def create_test_csv(self, transformations_data, csv_path):
        """Helper to create a test CSV file."""
        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, quoting=csv.QUOTE_ALL)
            writer.writerow(["transformation_type", "input_items", "output_items", "metadata"])
            for trans_type, inputs, outputs, metadata in transformations_data:
                input_json = json.dumps(inputs)
                output_json = json.dumps([outputs[0]]) if outputs else json.dumps([])
                metadata_json = json.dumps(metadata)
                writer.writerow([trans_type, input_json, output_json, metadata_json])

    def test_load_basic_transformations(self, tmp_path):
        """Test loading basic transformations."""
        csv_path = tmp_path / "transformations.csv"
        self.create_test_csv([
            ("crafting", ["Oak Log"], ["Oak Planks"], {}),
            ("smelting", ["Iron Ore"], ["Iron Ingot"], {}),
        ], csv_path)

        transformations = load_transformations_from_csv(str(csv_path))

        assert len(transformations) == 2
        assert transformations[0]["transformation_type"] == "crafting"
        assert transformations[1]["transformation_type"] == "smelting"

    def test_load_with_filter(self, tmp_path):
        """Test loading with type filtering."""
        csv_path = tmp_path / "transformations.csv"
        self.create_test_csv([
            ("crafting", ["Oak Log"], ["Oak Planks"], {}),
            ("smelting", ["Iron Ore"], ["Iron Ingot"], {}),
            ("crafting", ["Oak Planks", "Stick"], ["Wooden Pickaxe"], {}),
        ], csv_path)

        transformations = load_transformations_from_csv(
            str(csv_path),
            filter_types=["crafting"]
        )

        assert len(transformations) == 2
        assert all(t["transformation_type"] == "crafting" for t in transformations)

    def test_load_nonexistent_file(self):
        """Test loading from non-existent file."""
        with pytest.raises(FileNotFoundError):
            load_transformations_from_csv("nonexistent.csv")


class TestBuildGraphFromCSV:
    """Test build_graph_from_csv function."""

    def create_test_csv(self, transformations_data, csv_path):
        """Helper to create a test CSV file."""
        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, quoting=csv.QUOTE_ALL)
            writer.writerow(["transformation_type", "input_items", "output_items", "metadata"])
            for trans_type, inputs, outputs, metadata in transformations_data:
                input_json = json.dumps(inputs)
                output_json = json.dumps([outputs[0]]) if outputs else json.dumps([])
                metadata_json = json.dumps(metadata)
                writer.writerow([trans_type, input_json, output_json, metadata_json])

    def test_build_simple_graph(self, tmp_path):
        """Test building a simple graph."""
        csv_path = tmp_path / "transformations.csv"
        self.create_test_csv([
            ("crafting", ["Oak Log"], ["Oak Planks"], {}),
        ], csv_path)

        graph = build_graph_from_csv(str(csv_path))

        assert graph.number_of_nodes() == 2
        assert graph.has_node("Oak Log")
        assert graph.has_node("Oak Planks")
        assert graph.has_edge("Oak Log", "Oak Planks")

    def test_build_graph_with_multi_input(self, tmp_path):
        """Test building graph with multi-input transformation."""
        csv_path = tmp_path / "transformations.csv"
        self.create_test_csv([
            ("crafting", ["Oak Planks", "Stick"], ["Wooden Pickaxe"], {}),
        ], csv_path)

        graph = build_graph_from_csv(str(csv_path))

        # 3 item nodes + 1 intermediate node = 4 total
        assert graph.number_of_nodes() == 4
        assert graph.has_node("Oak Planks")
        assert graph.has_node("Stick")
        assert graph.has_node("Wooden Pickaxe")


class TestGetVisualSubgraph:
    """Test get_visual_subgraph function."""

    def create_test_csv(self, transformations_data, csv_path):
        """Helper to create a test CSV file."""
        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, quoting=csv.QUOTE_ALL)
            writer.writerow(["transformation_type", "input_items", "output_items", "metadata"])
            for trans_type, inputs, outputs, metadata in transformations_data:
                input_json = json.dumps(inputs)
                output_json = json.dumps([outputs[0]]) if outputs else json.dumps([])
                metadata_json = json.dumps(metadata)
                writer.writerow([trans_type, input_json, output_json, metadata_json])

    def test_linear_chain(self, tmp_path):
        """Test subgraph extraction with linear chain: A→B→C→D."""
        csv_path = tmp_path / "transformations.csv"
        self.create_test_csv([
            ("crafting", ["A"], ["B"], {}),
            ("crafting", ["B"], ["C"], {}),
            ("crafting", ["C"], ["D"], {}),
        ], csv_path)

        graph = get_visual_subgraph("A", str(csv_path))

        # Should include all nodes in forward path
        assert graph.has_node("A")
        assert graph.has_node("B")
        assert graph.has_node("C")
        assert graph.has_node("D")
        assert graph.number_of_nodes() == 4

    def test_tree_structure(self, tmp_path):
        """Test subgraph extraction with tree: A→B, A→C, B→D."""
        csv_path = tmp_path / "transformations.csv"
        self.create_test_csv([
            ("crafting", ["A"], ["B"], {}),
            ("crafting", ["A"], ["C"], {}),
            ("crafting", ["B"], ["D"], {}),
        ], csv_path)

        graph = get_visual_subgraph("A", str(csv_path))

        # Should include all forward nodes
        assert graph.has_node("A")
        assert graph.has_node("B")
        assert graph.has_node("C")
        assert graph.has_node("D")

    def test_multi_input_transformation(self, tmp_path):
        """Test subgraph with multi-input: [A, B]→C."""
        csv_path = tmp_path / "transformations.csv"
        self.create_test_csv([
            ("crafting", ["A", "B"], ["C"], {}),
        ], csv_path)

        graph = get_visual_subgraph("A", str(csv_path))

        # Should include A, B (contextual input), C, and intermediate node
        assert graph.has_node("A")
        assert graph.has_node("B")
        assert graph.has_node("C")
        # Check for intermediate node
        intermediate_nodes = [n for n in graph.nodes() if graph.nodes[n].get("node_type") == "intermediate"]
        assert len(intermediate_nodes) == 1

    def test_multi_input_contextual(self, tmp_path):
        """Test multi-input contextual: [A, B]→C, C→D. B should be included but not explored."""
        csv_path = tmp_path / "transformations.csv"
        self.create_test_csv([
            ("crafting", ["A", "B"], ["C"], {}),
            ("crafting", ["C"], ["D"], {}),
            ("crafting", ["B"], ["E"], {}),  # This should NOT be included
        ], csv_path)

        graph = get_visual_subgraph("A", str(csv_path))

        # Should include A, B, C, D but NOT E (since B is not explored backward)
        assert graph.has_node("A")
        assert graph.has_node("B")
        assert graph.has_node("C")
        assert graph.has_node("D")
        assert not graph.has_node("E")

    def test_cycle_handling(self, tmp_path):
        """Test cycle handling: A→B→C→A."""
        csv_path = tmp_path / "transformations.csv"
        self.create_test_csv([
            ("crafting", ["A"], ["B"], {}),
            ("crafting", ["B"], ["C"], {}),
            ("crafting", ["C"], ["A"], {}),
        ], csv_path)

        # Should not infinite loop
        graph = get_visual_subgraph("A", str(csv_path))

        # Should include all nodes in cycle
        assert graph.has_node("A")
        assert graph.has_node("B")
        assert graph.has_node("C")

    def test_leaf_node(self, tmp_path):
        """Test starting from leaf node (no outputs)."""
        csv_path = tmp_path / "transformations.csv"
        self.create_test_csv([
            ("crafting", ["A"], ["B"], {}),
        ], csv_path)

        graph = get_visual_subgraph("B", str(csv_path))

        # Should only contain the starting node
        assert graph.number_of_nodes() == 1
        assert graph.has_node("B")

    def test_disconnected_component(self, tmp_path):
        """Test with disconnected components."""
        csv_path = tmp_path / "transformations.csv"
        self.create_test_csv([
            ("crafting", ["A"], ["B"], {}),
            ("crafting", ["C"], ["D"], {}),  # Disconnected from A
        ], csv_path)

        graph = get_visual_subgraph("A", str(csv_path))

        # Should only include A's component
        assert graph.has_node("A")
        assert graph.has_node("B")
        assert not graph.has_node("C")
        assert not graph.has_node("D")

    def test_with_filter_types(self, tmp_path):
        """Test subgraph extraction with transformation type filtering."""
        csv_path = tmp_path / "transformations.csv"
        self.create_test_csv([
            ("crafting", ["A"], ["B"], {}),
            ("smelting", ["B"], ["C"], {}),
            ("crafting", ["C"], ["D"], {}),
        ], csv_path)

        graph = get_visual_subgraph("A", str(csv_path), filter_types=["crafting"])

        # Should include A→B but not B→C (smelting) so C and D not reachable
        assert graph.has_node("A")
        assert graph.has_node("B")
        assert not graph.has_node("C")
        assert not graph.has_node("D")

    def test_empty_csv(self, tmp_path):
        """Test with empty CSV (only header)."""
        csv_path = tmp_path / "transformations.csv"
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write("transformation_type,input_items,output_items,metadata\n")

        graph = get_visual_subgraph("A", str(csv_path))

        # Should only contain starting node
        assert graph.number_of_nodes() == 1
        assert graph.has_node("A")

    def test_node_and_edge_counts(self, tmp_path):
        """Test correct node and edge counts for complex graph."""
        csv_path = tmp_path / "transformations.csv"
        self.create_test_csv([
            ("crafting", ["Oak Log"], ["Oak Planks"], {}),
            ("crafting", ["Oak Planks"], ["Stick"], {}),
            ("crafting", ["Oak Planks", "Stick"], ["Wooden Pickaxe"], {}),
        ], csv_path)

        graph = get_visual_subgraph("Oak Log", str(csv_path))

        # Oak Log, Oak Planks, Stick, Wooden Pickaxe + 2 intermediates
        # (one from Oak Planks→Wooden Pickaxe path, one from Stick→Wooden Pickaxe path)
        assert graph.number_of_nodes() == 6

        # Oak Log→Oak Planks, Oak Planks→Stick,
        # Oak Planks→intermediate_0, Stick→intermediate_0, intermediate_0→Wooden Pickaxe
        # Oak Planks→intermediate_1, Stick→intermediate_1, intermediate_1→Wooden Pickaxe
        assert graph.number_of_edges() == 8
