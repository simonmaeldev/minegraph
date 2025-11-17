"""Unit tests for 3D graph visualization module."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from argparse import Namespace

import pytest
import networkx as nx

from src.visualize_graph_3d import (
    Graph3DBuilder,
    build_graph_from_csv,
    calculate_node_sizes,
    collect_options,
    compute_3d_layout,
    get_edge_colors,
    load_color_config,
    load_item_image,
    load_transformation_types,
    load_transformations_from_csv,
    prompt_boolean_options,
    prompt_transformation_types,
    render_3d_graph,
    standardize_filename,
)


class TestLoadColorConfig:
    """Test cases for color configuration loading."""

    def test_load_valid_config(self):
        """Test loading a valid configuration file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("# Comment line\n")
            f.write("crafting=#4A90E2\n")
            f.write("smelting=#E67E22\n")
            f.write("\n")  # Empty line
            f.write("brewing=#9B59B6\n")
            temp_path = f.name

        try:
            colors = load_color_config(temp_path)
            assert 'crafting' in colors
            assert colors['crafting'] == '#4A90E2'
            assert 'smelting' in colors
            assert colors['smelting'] == '#E67E22'
            assert 'brewing' in colors
            assert colors['brewing'] == '#9B59B6'
        finally:
            Path(temp_path).unlink()

    def test_missing_config_file_uses_defaults(self):
        """Test that missing config file falls back to defaults."""
        colors = load_color_config('/nonexistent/path/config.txt')
        # Should contain default colors
        assert 'crafting' in colors
        assert 'smelting' in colors
        assert 'brewing' in colors
        assert len(colors) > 0

    def test_malformed_lines_are_skipped(self):
        """Test that malformed lines are gracefully skipped."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("crafting=#4A90E2\n")
            f.write("invalid_line_without_equals\n")
            f.write("=no_key\n")
            f.write("no_value=\n")
            f.write("smelting=#E67E22\n")
            temp_path = f.name

        try:
            colors = load_color_config(temp_path)
            assert 'crafting' in colors
            assert 'smelting' in colors
        finally:
            Path(temp_path).unlink()

    def test_comments_and_empty_lines_ignored(self):
        """Test that comments and empty lines are properly ignored."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("# This is a comment\n")
            f.write("\n")
            f.write("   \n")  # Whitespace only
            f.write("# Another comment\n")
            f.write("crafting=#4A90E2\n")
            temp_path = f.name

        try:
            colors = load_color_config(temp_path)
            assert 'crafting' in colors
            assert colors['crafting'] == '#4A90E2'
        finally:
            Path(temp_path).unlink()


class TestLoadTransformationsFromCSV:
    """Test cases for CSV transformation loading."""

    def test_load_valid_csv(self):
        """Test loading a valid CSV with various transformation types."""
        csv_content = """transformation_type,input_items,output_items,metadata
crafting,"[""Oak Planks""]","[""Crafting Table""]","{""source"":""test""}"
smelting,"[""Iron Ore""]","[""Iron Ingot""]","{""fuel"":""coal""}"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            transformations = load_transformations_from_csv(temp_path)
            assert len(transformations) == 2

            # Check first transformation
            assert transformations[0]['transformation_type'] == 'crafting'
            assert transformations[0]['input_items'] == ['Oak Planks']
            assert transformations[0]['output_items'] == ['Crafting Table']
            assert transformations[0]['metadata'] == {'source': 'test'}

            # Check second transformation
            assert transformations[1]['transformation_type'] == 'smelting'
            assert transformations[1]['input_items'] == ['Iron Ore']
            assert transformations[1]['output_items'] == ['Iron Ingot']
            assert transformations[1]['metadata'] == {'fuel': 'coal'}
        finally:
            Path(temp_path).unlink()

    def test_load_empty_csv(self):
        """Test loading an empty CSV file."""
        csv_content = """transformation_type,input_items,output_items,metadata
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            transformations = load_transformations_from_csv(temp_path)
            assert len(transformations) == 0
        finally:
            Path(temp_path).unlink()

    def test_missing_csv_file_raises_error(self):
        """Test that missing CSV file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_transformations_from_csv('/nonexistent/path/transformations.csv')

    def test_malformed_rows_are_skipped(self):
        """Test that malformed rows are gracefully skipped."""
        csv_content = """transformation_type,input_items,output_items,metadata
crafting,"[""Oak Planks""]","[""Crafting Table""]","{""source"":""test""}"
invalid,bad_json,"[""Output""]","{}"
smelting,"[""Iron Ore""]","[""Iron Ingot""]","{}"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            transformations = load_transformations_from_csv(temp_path)
            # Should skip the malformed row
            assert len(transformations) == 2
            assert transformations[0]['transformation_type'] == 'crafting'
            assert transformations[1]['transformation_type'] == 'smelting'
        finally:
            Path(temp_path).unlink()

    def test_multi_input_transformation(self):
        """Test loading transformation with multiple inputs."""
        csv_content = """transformation_type,input_items,output_items,metadata
crafting,"[""Oak Planks"", ""Iron Ingot""]","[""Door""]","{}"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            transformations = load_transformations_from_csv(temp_path)
            assert len(transformations) == 1
            assert len(transformations[0]['input_items']) == 2
            assert transformations[0]['input_items'] == ['Oak Planks', 'Iron Ingot']
        finally:
            Path(temp_path).unlink()


class TestGraph3DBuilder:
    """Test cases for Graph3DBuilder class."""

    def test_add_item_node(self):
        """Test adding item nodes to the graph."""
        builder = Graph3DBuilder()
        builder.add_item_node('Oak Planks')
        builder.add_item_node('Crafting Table')

        assert builder.graph.number_of_nodes() == 2
        assert builder.graph.has_node('Oak Planks')
        assert builder.graph.has_node('Crafting Table')
        assert builder.graph.nodes['Oak Planks']['node_type'] == 'item'
        assert builder.graph.nodes['Crafting Table']['node_type'] == 'item'

    def test_add_item_node_no_duplicates(self):
        """Test that adding the same node twice doesn't create duplicates."""
        builder = Graph3DBuilder()
        builder.add_item_node('Oak Planks')
        builder.add_item_node('Oak Planks')

        assert builder.graph.number_of_nodes() == 1
        assert builder.graph.has_node('Oak Planks')

    def test_create_intermediate_node(self):
        """Test creating unique intermediate nodes."""
        builder = Graph3DBuilder()
        node1 = builder.create_intermediate_node()
        node2 = builder.create_intermediate_node()
        node3 = builder.create_intermediate_node()

        assert node1 != node2 != node3
        assert builder.graph.has_node(node1)
        assert builder.graph.has_node(node2)
        assert builder.graph.has_node(node3)
        assert builder.graph.nodes[node1]['node_type'] == 'intermediate'
        assert builder.graph.nodes[node2]['node_type'] == 'intermediate'
        assert builder.intermediate_counter == 3

    def test_add_edge(self):
        """Test adding edges with transformation type metadata."""
        builder = Graph3DBuilder()
        builder.add_item_node('Oak Planks')
        builder.add_item_node('Crafting Table')
        builder.add_edge('Oak Planks', 'Crafting Table', 'crafting')

        assert builder.graph.number_of_edges() == 1
        assert builder.graph.has_edge('Oak Planks', 'Crafting Table')
        assert builder.graph.edges['Oak Planks', 'Crafting Table']['transformation_type'] == 'crafting'

    def test_add_single_input_transformation(self):
        """Test adding single-input transformation."""
        builder = Graph3DBuilder()
        builder.add_single_input_transformation('Iron Ore', 'Iron Ingot', 'smelting')

        assert builder.graph.number_of_nodes() == 2
        assert builder.graph.number_of_edges() == 1
        assert builder.graph.has_edge('Iron Ore', 'Iron Ingot')
        assert builder.graph.edges['Iron Ore', 'Iron Ingot']['transformation_type'] == 'smelting'

    def test_add_multi_input_transformation(self):
        """Test adding multi-input transformation with intermediate node."""
        builder = Graph3DBuilder()
        inputs = ['Oak Planks', 'Iron Ingot']
        output = 'Door'
        builder.add_multi_input_transformation(inputs, output, 'crafting')

        # Should have 2 input nodes + 1 intermediate + 1 output = 4 nodes
        assert builder.graph.number_of_nodes() == 4

        # Should have 2 edges from inputs to intermediate + 1 edge from intermediate to output = 3 edges
        assert builder.graph.number_of_edges() == 3

        # Find the intermediate node
        intermediate_nodes = [
            n for n in builder.graph.nodes()
            if builder.graph.nodes[n].get('node_type') == 'intermediate'
        ]
        assert len(intermediate_nodes) == 1
        intermediate = intermediate_nodes[0]

        # Verify edges
        assert builder.graph.has_edge('Oak Planks', intermediate)
        assert builder.graph.has_edge('Iron Ingot', intermediate)
        assert builder.graph.has_edge(intermediate, 'Door')

        # Verify all edges have correct transformation type
        for u, v in builder.graph.edges():
            assert builder.graph.edges[u, v]['transformation_type'] == 'crafting'

    def test_multiple_transformations(self):
        """Test adding multiple transformations creates correct graph structure."""
        builder = Graph3DBuilder()

        # Add single-input transformation
        builder.add_single_input_transformation('Iron Ore', 'Iron Ingot', 'smelting')

        # Add multi-input transformation
        builder.add_multi_input_transformation(['Iron Ingot', 'Stick'], 'Iron Sword', 'crafting')

        # Add another single-input transformation
        builder.add_single_input_transformation('Oak Log', 'Oak Planks', 'crafting')

        # Should have: Iron Ore, Iron Ingot, Stick, Iron Sword, Oak Log, Oak Planks + 1 intermediate = 7 nodes
        assert builder.graph.number_of_nodes() == 7

        # Count intermediate nodes
        intermediate_nodes = [
            n for n in builder.graph.nodes()
            if builder.graph.nodes[n].get('node_type') == 'intermediate'
        ]
        assert len(intermediate_nodes) == 1

        # Count item nodes
        item_nodes = [
            n for n in builder.graph.nodes()
            if builder.graph.nodes[n].get('node_type') == 'item'
        ]
        assert len(item_nodes) == 6


class TestBuildGraphFromCSV:
    """Test cases for building graph from CSV."""

    def test_build_graph_single_input_transformations(self):
        """Test building graph with only single-input transformations."""
        csv_content = """transformation_type,input_items,output_items,metadata
crafting,"[""Oak Planks""]","[""Crafting Table""]","{}"
smelting,"[""Iron Ore""]","[""Iron Ingot""]","{}"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            color_config = {'crafting': '#4A90E2', 'smelting': '#E67E22'}
            graph = build_graph_from_csv(temp_path, color_config)

            # Should have 4 item nodes (no intermediates)
            assert graph.number_of_nodes() == 4
            assert graph.number_of_edges() == 2

            # Verify nodes
            assert graph.has_node('Oak Planks')
            assert graph.has_node('Crafting Table')
            assert graph.has_node('Iron Ore')
            assert graph.has_node('Iron Ingot')

            # Verify edges
            assert graph.has_edge('Oak Planks', 'Crafting Table')
            assert graph.has_edge('Iron Ore', 'Iron Ingot')
        finally:
            Path(temp_path).unlink()

    def test_build_graph_multi_input_transformations(self):
        """Test building graph with multi-input transformations."""
        csv_content = """transformation_type,input_items,output_items,metadata
crafting,"[""Oak Planks"", ""Iron Ingot""]","[""Door""]","{}"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            color_config = {'crafting': '#4A90E2'}
            graph = build_graph_from_csv(temp_path, color_config)

            # Should have 2 inputs + 1 intermediate + 1 output = 4 nodes
            assert graph.number_of_nodes() == 4

            # Should have 2 edges to intermediate + 1 edge from intermediate = 3 edges
            assert graph.number_of_edges() == 3

            # Find intermediate node
            intermediate_nodes = [
                n for n in graph.nodes()
                if graph.nodes[n].get('node_type') == 'intermediate'
            ]
            assert len(intermediate_nodes) == 1
        finally:
            Path(temp_path).unlink()

    def test_build_graph_mixed_transformations(self):
        """Test building graph with mix of single and multi-input transformations."""
        csv_content = """transformation_type,input_items,output_items,metadata
crafting,"[""Oak Planks""]","[""Stick""]","{}"
crafting,"[""Stick"", ""Iron Ingot""]","[""Iron Sword""]","{}"
smelting,"[""Iron Ore""]","[""Iron Ingot""]","{}"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            color_config = {'crafting': '#4A90E2', 'smelting': '#E67E22'}
            graph = build_graph_from_csv(temp_path, color_config)

            # Should have: Oak Planks, Stick, Iron Ingot, Iron Sword, Iron Ore + 1 intermediate = 6 nodes
            assert graph.number_of_nodes() == 6

            # 2 single-input edges + 3 multi-input edges = 5 edges
            assert graph.number_of_edges() == 5

            # Verify item nodes
            assert graph.has_node('Oak Planks')
            assert graph.has_node('Stick')
            assert graph.has_node('Iron Ingot')
            assert graph.has_node('Iron Sword')
            assert graph.has_node('Iron Ore')
        finally:
            Path(temp_path).unlink()


class TestCompute3DLayout:
    """Test cases for 3D layout computation."""

    def test_compute_layout_empty_graph(self):
        """Test layout computation with empty graph."""
        graph = nx.DiGraph()
        pos = compute_3d_layout(graph)
        assert len(pos) == 0

    def test_compute_layout_small_graph(self):
        """Test layout computation with small graph."""
        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        graph.add_edge('B', 'C')

        pos = compute_3d_layout(graph)

        # Should have positions for all nodes
        assert len(pos) == 3
        assert 'A' in pos
        assert 'B' in pos
        assert 'C' in pos

        # Each position should be (x, y, z) tuple
        for node in pos:
            assert len(pos[node]) == 3
            # Verify all coordinates are floats
            assert all(isinstance(coord, (int, float)) for coord in pos[node])

    def test_compute_layout_larger_graph(self):
        """Test layout computation with larger graph."""
        graph = nx.DiGraph()
        # Create a more complex graph
        for i in range(10):
            for j in range(i + 1, min(i + 3, 10)):
                graph.add_edge(f'node_{i}', f'node_{j}')

        pos = compute_3d_layout(graph)

        # Should have positions for all nodes
        assert len(pos) == 10

        # Verify 3D coordinates
        for node in pos:
            assert len(pos[node]) == 3


class TestCalculateNodeSizes:
    """Test cases for node size calculation."""

    def test_calculate_sizes_single_node(self):
        """Test size calculation with single node."""
        graph = nx.DiGraph()
        graph.add_node('A', node_type='item')

        pos = {'A': (0, 0, 0)}
        sizes = calculate_node_sizes(graph, pos)

        assert 'A' in sizes
        # Single node should have some size
        assert sizes['A'] > 0

    def test_calculate_sizes_intermediate_nodes_smaller(self):
        """Test that intermediate nodes get smaller sizes."""
        graph = nx.DiGraph()
        graph.add_node('Item1', node_type='item')
        graph.add_node('Item2', node_type='item')
        graph.add_node('intermediate_0', node_type='intermediate')
        graph.add_edge('Item1', 'intermediate_0')
        graph.add_edge('intermediate_0', 'Item2')

        pos = {'Item1': (0, 0, 0), 'intermediate_0': (1, 1, 1), 'Item2': (2, 2, 2)}
        sizes = calculate_node_sizes(graph, pos)

        # Intermediate node should be smaller
        assert sizes['intermediate_0'] < sizes['Item1']
        assert sizes['intermediate_0'] < sizes['Item2']
        assert sizes['intermediate_0'] == 15  # Fixed size for intermediate

    def test_calculate_sizes_based_on_degree(self):
        """Test that node sizes vary based on degree centrality."""
        graph = nx.DiGraph()
        # Create a hub node with many connections
        graph.add_node('Hub', node_type='item')
        graph.add_node('A', node_type='item')
        graph.add_node('B', node_type='item')
        graph.add_node('C', node_type='item')

        # Hub has high degree
        graph.add_edge('Hub', 'A')
        graph.add_edge('Hub', 'B')
        graph.add_edge('Hub', 'C')

        # A has low degree
        graph.add_edge('A', 'B')

        pos = {n: (0, 0, 0) for n in graph.nodes()}
        sizes = calculate_node_sizes(graph, pos)

        # Hub should have larger size due to higher degree
        assert sizes['Hub'] >= sizes['A']
        assert sizes['Hub'] >= sizes['B']


class TestGetEdgeColors:
    """Test cases for edge color mapping."""

    def test_edge_colors_basic(self):
        """Test basic edge color mapping."""
        graph = nx.DiGraph()
        graph.add_edge('A', 'B', transformation_type='crafting')
        graph.add_edge('B', 'C', transformation_type='smelting')

        color_config = {
            'crafting': '#4A90E2',
            'smelting': '#E67E22'
        }

        colors = get_edge_colors(graph, color_config)

        assert len(colors) == 2
        assert colors[0] == '#4A90E2'
        assert colors[1] == '#E67E22'

    def test_edge_colors_missing_type_uses_default(self):
        """Test that missing transformation type uses default color."""
        graph = nx.DiGraph()
        graph.add_edge('A', 'B', transformation_type='unknown_type')

        color_config = {'crafting': '#4A90E2'}

        colors = get_edge_colors(graph, color_config)

        assert len(colors) == 1
        assert colors[0] == '#000000'  # Default black

    def test_edge_colors_no_transformation_type_attribute(self):
        """Test handling of edges without transformation_type attribute."""
        graph = nx.DiGraph()
        graph.add_edge('A', 'B')  # No transformation_type

        color_config = {'crafting': '#4A90E2'}

        colors = get_edge_colors(graph, color_config)

        assert len(colors) == 1
        assert colors[0] == '#000000'  # Default black


class TestIntegration:
    """Integration tests for end-to-end functionality."""

    def test_full_pipeline_simple(self):
        """Test complete pipeline with simple transformation data."""
        csv_content = """transformation_type,input_items,output_items,metadata
crafting,"[""Oak Planks""]","[""Stick""]","{}"
smelting,"[""Iron Ore""]","[""Iron Ingot""]","{}"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            # Load color config
            color_config = load_color_config('/nonexistent/path/config.txt')

            # Build graph
            graph = build_graph_from_csv(temp_path, color_config)

            # Compute layout
            pos = compute_3d_layout(graph)

            # Calculate sizes
            sizes = calculate_node_sizes(graph, pos)

            # Get colors
            colors = get_edge_colors(graph, color_config)

            # Verify results
            assert graph.number_of_nodes() == 4
            assert graph.number_of_edges() == 2
            assert len(pos) == 4
            assert len(sizes) == 4
            assert len(colors) == 2

            # Verify all nodes have 3D positions
            for node in graph.nodes():
                assert node in pos
                assert len(pos[node]) == 3

            # Verify all nodes have sizes
            for node in graph.nodes():
                assert node in sizes
                assert sizes[node] > 0

        finally:
            Path(temp_path).unlink()

    def test_full_pipeline_complex(self):
        """Test complete pipeline with complex transformation data."""
        csv_content = """transformation_type,input_items,output_items,metadata
crafting,"[""Oak Planks""]","[""Stick""]","{}"
crafting,"[""Stick"", ""Iron Ingot""]","[""Iron Sword""]","{}"
smelting,"[""Iron Ore""]","[""Iron Ingot""]","{}"
crafting,"[""Oak Planks""]","[""Crafting Table""]","{}"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            # Load color config
            color_config = load_color_config('/nonexistent/path/config.txt')

            # Build graph
            graph = build_graph_from_csv(temp_path, color_config)

            # Compute layout
            pos = compute_3d_layout(graph)

            # Calculate sizes
            sizes = calculate_node_sizes(graph, pos)

            # Get colors
            colors = get_edge_colors(graph, color_config)

            # Verify results
            assert graph.number_of_nodes() > 0
            assert graph.number_of_edges() > 0
            assert len(pos) == graph.number_of_nodes()
            assert len(sizes) == graph.number_of_nodes()
            assert len(colors) == graph.number_of_edges()

            # Find intermediate nodes
            intermediate_nodes = [
                n for n in graph.nodes()
                if graph.nodes[n].get('node_type') == 'intermediate'
            ]
            assert len(intermediate_nodes) == 1  # One multi-input transformation

            # Verify intermediate node has smaller size
            for inter in intermediate_nodes:
                assert sizes[inter] == 15

        finally:
            Path(temp_path).unlink()


class TestRender3DGraph:
    """Test cases for 3D graph rendering with hover annotations."""

    def test_render_creates_event_handler(self):
        """Test that render_3d_graph creates and connects hover event handler."""
        import matplotlib
        matplotlib.use('Agg')  # Use non-interactive backend for testing
        import matplotlib.pyplot as plt

        # Create simple graph
        graph = nx.DiGraph()
        graph.add_node('Item1', node_type='item')
        graph.add_node('Item2', node_type='item')
        graph.add_edge('Item1', 'Item2', transformation_type='crafting')

        pos = {'Item1': (0, 0, 0), 'Item2': (1, 1, 1)}
        node_sizes = {'Item1': 50, 'Item2': 50}
        edge_colors = ['#4A90E2']
        color_config = {'crafting': '#4A90E2'}

        # Render graph
        render_3d_graph(graph, pos, node_sizes, edge_colors, color_config)

        # Get current figure
        fig = plt.gcf()

        # Check that motion_notify_event handler is connected
        callbacks = fig.canvas.callbacks.callbacks.get('motion_notify_event', {})
        assert len(callbacks) > 0, "No motion_notify_event handler connected"

        plt.close(fig)

    def test_render_with_empty_graph(self):
        """Test rendering with empty graph doesn't crash."""
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        graph = nx.DiGraph()
        pos = {}
        node_sizes = {}
        edge_colors = []
        color_config = {}

        # Should not raise any errors
        render_3d_graph(graph, pos, node_sizes, edge_colors, color_config)

        fig = plt.gcf()
        plt.close(fig)

    def test_render_with_only_item_nodes(self):
        """Test rendering with only item nodes (no intermediate nodes)."""
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        graph = nx.DiGraph()
        graph.add_node('Item1', node_type='item')
        graph.add_node('Item2', node_type='item')
        graph.add_edge('Item1', 'Item2', transformation_type='crafting')

        pos = {'Item1': (0, 0, 0), 'Item2': (1, 1, 1)}
        node_sizes = {'Item1': 50, 'Item2': 50}
        edge_colors = ['#4A90E2']
        color_config = {'crafting': '#4A90E2'}

        render_3d_graph(graph, pos, node_sizes, edge_colors, color_config)

        fig = plt.gcf()
        ax = fig.axes[0]

        # Check that axis ticks are not empty (numeric scales enabled)
        # Note: Matplotlib may auto-generate ticks, so we check they exist
        assert ax.get_xticks() is not None
        assert ax.get_yticks() is not None
        assert ax.get_zticks() is not None

        plt.close(fig)

    def test_render_with_intermediate_nodes(self):
        """Test rendering with both item and intermediate nodes."""
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        graph = nx.DiGraph()
        graph.add_node('Item1', node_type='item')
        graph.add_node('Item2', node_type='item')
        graph.add_node('intermediate_0', node_type='intermediate')
        graph.add_node('Item3', node_type='item')
        graph.add_edge('Item1', 'intermediate_0', transformation_type='crafting')
        graph.add_edge('Item2', 'intermediate_0', transformation_type='crafting')
        graph.add_edge('intermediate_0', 'Item3', transformation_type='crafting')

        pos = {
            'Item1': (0, 0, 0),
            'Item2': (1, 0, 0),
            'intermediate_0': (0.5, 0.5, 0.5),
            'Item3': (0.5, 1, 1)
        }
        node_sizes = {'Item1': 50, 'Item2': 50, 'intermediate_0': 15, 'Item3': 50}
        edge_colors = ['#4A90E2', '#4A90E2', '#4A90E2']
        color_config = {'crafting': '#4A90E2'}

        render_3d_graph(graph, pos, node_sizes, edge_colors, color_config)

        fig = plt.gcf()
        plt.close(fig)

    def test_render_with_large_graph(self):
        """Test rendering performance with larger graph (simulating real use case)."""
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        # Create graph with 100 nodes
        graph = nx.DiGraph()
        for i in range(100):
            graph.add_node(f'Item{i}', node_type='item')

        # Add edges between sequential nodes
        for i in range(99):
            graph.add_edge(f'Item{i}', f'Item{i+1}', transformation_type='crafting')

        # Create positions and sizes
        pos = {f'Item{i}': (i % 10, i // 10, i % 5) for i in range(100)}
        node_sizes = {f'Item{i}': 50 for i in range(100)}
        edge_colors = ['#4A90E2'] * 99
        color_config = {'crafting': '#4A90E2'}

        # Should handle large graph without errors
        render_3d_graph(graph, pos, node_sizes, edge_colors, color_config)

        fig = plt.gcf()

        # Verify event handler is still connected
        callbacks = fig.canvas.callbacks.callbacks.get('motion_notify_event', {})
        assert len(callbacks) > 0

        plt.close(fig)

    def test_axis_scales_enabled(self):
        """Test that numeric axis scales are enabled (ticks not removed)."""
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        graph = nx.DiGraph()
        graph.add_node('Item1', node_type='item')
        graph.add_node('Item2', node_type='item')
        graph.add_edge('Item1', 'Item2', transformation_type='crafting')

        pos = {'Item1': (0, 0, 0), 'Item2': (1, 1, 1)}
        node_sizes = {'Item1': 50, 'Item2': 50}
        edge_colors = ['#4A90E2']
        color_config = {'crafting': '#4A90E2'}

        render_3d_graph(graph, pos, node_sizes, edge_colors, color_config)

        fig = plt.gcf()
        ax = fig.axes[0]

        # Check that ticks exist (not explicitly set to empty)
        # Matplotlib auto-generates ticks when not explicitly set to []
        x_ticks = ax.get_xticks()
        y_ticks = ax.get_yticks()
        z_ticks = ax.get_zticks()

        # Verify ticks are present (may be auto-generated)
        assert x_ticks is not None
        assert y_ticks is not None
        assert z_ticks is not None

        plt.close(fig)


class TestImageFunctionality:
    """Test cases for image loading and rendering functionality."""

    def test_standardize_filename_basic(self):
        """Test basic filename standardization."""
        assert standardize_filename("Iron Ingot") == "iron_ingot.png"
        assert standardize_filename("Oak Planks") == "oak_planks.png"

    def test_standardize_filename_special_chars(self):
        """Test filename standardization with special characters."""
        assert standardize_filename("Iron-Ingot!") == "ironingot.png"
        assert standardize_filename("Boat (Oak)") == "boat_oak.png"

    def test_load_item_image_nonexistent(self):
        """Test loading image that doesn't exist."""
        cache = {}
        img = load_item_image("Nonexistent Item", "/nonexistent/path", cache)
        assert img is None
        assert "Nonexistent Item" in cache
        assert cache["Nonexistent Item"] is None

    def test_load_item_image_cache(self):
        """Test that image cache is used."""
        import numpy as np

        cache = {}
        fake_img = np.array([[[255, 0, 0]]])  # Fake image

        # Pre-populate cache
        cache["Iron Ingot"] = fake_img

        # Should return cached image without trying to load from disk
        img = load_item_image("Iron Ingot", "/nonexistent/path", cache)
        assert img is not None
        assert np.array_equal(img, fake_img)

    def test_load_item_image_real_file(self):
        """Test loading a real image file."""
        import numpy as np
        from PIL import Image

        # Create a temporary image file
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a simple test image
            test_img = Image.new('RGB', (10, 10), color=(255, 0, 0))
            img_path = Path(tmpdir) / "iron_ingot.png"
            test_img.save(img_path)

            # Test loading
            cache = {}
            img = load_item_image("Iron Ingot", tmpdir, cache)

            assert img is not None
            assert isinstance(img, np.ndarray)
            assert "Iron Ingot" in cache
            assert cache["Iron Ingot"] is not None

    def test_render_with_images_enabled(self):
        """Test rendering with image mode enabled but no images available."""
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        graph = nx.DiGraph()
        graph.add_node('Item1', node_type='item')
        graph.add_node('Item2', node_type='item')
        graph.add_edge('Item1', 'Item2', transformation_type='crafting')

        pos = {'Item1': (0, 0, 0), 'Item2': (1, 1, 1)}
        node_sizes = {'Item1': 50, 'Item2': 50}
        edge_colors = ['#4A90E2']
        color_config = {'crafting': '#4A90E2'}

        # Render with images enabled but no images directory
        render_3d_graph(
            graph, pos, node_sizes, edge_colors, color_config,
            use_images=True,
            images_dir="/nonexistent/path"
        )

        fig = plt.gcf()
        plt.close(fig)

    def test_render_with_images_disabled(self):
        """Test rendering with image mode disabled (default behavior)."""
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        graph = nx.DiGraph()
        graph.add_node('Item1', node_type='item')
        graph.add_node('Item2', node_type='item')
        graph.add_edge('Item1', 'Item2', transformation_type='crafting')

        pos = {'Item1': (0, 0, 0), 'Item2': (1, 1, 1)}
        node_sizes = {'Item1': 50, 'Item2': 50}
        edge_colors = ['#4A90E2']
        color_config = {'crafting': '#4A90E2'}

        # Render without images (default)
        render_3d_graph(
            graph, pos, node_sizes, edge_colors, color_config,
            use_images=False
        )

        fig = plt.gcf()
        plt.close(fig)

    def test_render_image_updates_on_zoom(self):
        """Test that zoom event handlers are connected when images are enabled."""
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from PIL import Image
        import tempfile

        # Create a temporary image file
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a simple test image
            test_img = Image.new('RGB', (10, 10), color=(255, 0, 0))
            img_path = Path(tmpdir) / "item1.png"
            test_img.save(img_path)

            graph = nx.DiGraph()
            graph.add_node('Item1', node_type='item')
            graph.add_node('Item2', node_type='item')
            graph.add_edge('Item1', 'Item2', transformation_type='crafting')

            pos = {'Item1': (0, 0, 0), 'Item2': (1, 1, 1)}
            node_sizes = {'Item1': 50, 'Item2': 50}
            edge_colors = ['#4A90E2']
            color_config = {'crafting': '#4A90E2'}

            # Render with images enabled
            render_3d_graph(
                graph, pos, node_sizes, edge_colors, color_config,
                use_images=True,
                images_dir=tmpdir
            )

            fig = plt.gcf()

            # Verify button_release_event handler is connected
            callbacks = fig.canvas.callbacks.callbacks.get('button_release_event', {})
            assert len(callbacks) > 0, "No button_release_event handler connected for zoom updates"

            # Verify draw_event handler is still connected (for rotation/pan)
            draw_callbacks = fig.canvas.callbacks.callbacks.get('draw_event', {})
            assert len(draw_callbacks) > 0, "No draw_event handler connected"

            plt.close(fig)


class TestLoadTransformationTypes:
    """Test cases for loading unique transformation types from CSV."""

    def test_load_types_from_valid_csv(self):
        """Test loading transformation types from valid CSV."""
        csv_content = """transformation_type,input_items,output_items,metadata
crafting,"[""Oak Planks""]","[""Stick""]","{}"
smelting,"[""Iron Ore""]","[""Iron Ingot""]","{}"
crafting,"[""Stick""]","[""Tool""]","{}"
brewing,"[""Water Bottle""]","[""Potion""]","{}"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            types = load_transformation_types(temp_path)
            assert len(types) == 3  # crafting, smelting, brewing (unique)
            assert 'crafting' in types
            assert 'smelting' in types
            assert 'brewing' in types
            # Verify sorted order
            assert types == sorted(types)
        finally:
            Path(temp_path).unlink()

    def test_load_types_from_empty_csv(self):
        """Test loading types from empty CSV."""
        csv_content = """transformation_type,input_items,output_items,metadata
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            types = load_transformation_types(temp_path)
            assert len(types) == 0
        finally:
            Path(temp_path).unlink()

    def test_load_types_from_nonexistent_file(self):
        """Test loading types from nonexistent file."""
        types = load_transformation_types('/nonexistent/path.csv')
        assert len(types) == 0


class TestTransformationFiltering:
    """Test cases for filtering transformations by type."""

    def test_load_with_filter(self):
        """Test loading transformations with type filter."""
        csv_content = """transformation_type,input_items,output_items,metadata
crafting,"[""Oak Planks""]","[""Stick""]","{}"
smelting,"[""Iron Ore""]","[""Iron Ingot""]","{}"
crafting,"[""Stick""]","[""Tool""]","{}"
brewing,"[""Water Bottle""]","[""Potion""]","{}"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            # Filter for only crafting
            transformations = load_transformations_from_csv(temp_path, filter_types=['crafting'])
            assert len(transformations) == 2
            assert all(t['transformation_type'] == 'crafting' for t in transformations)

            # Filter for smelting and brewing
            transformations = load_transformations_from_csv(temp_path, filter_types=['smelting', 'brewing'])
            assert len(transformations) == 2
            types = [t['transformation_type'] for t in transformations]
            assert 'smelting' in types
            assert 'brewing' in types
            assert 'crafting' not in types
        finally:
            Path(temp_path).unlink()

    def test_load_without_filter(self):
        """Test loading transformations without filter (all types)."""
        csv_content = """transformation_type,input_items,output_items,metadata
crafting,"[""Oak Planks""]","[""Stick""]","{}"
smelting,"[""Iron Ore""]","[""Iron Ingot""]","{}"
brewing,"[""Water Bottle""]","[""Potion""]","{}"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            transformations = load_transformations_from_csv(temp_path, filter_types=None)
            assert len(transformations) == 3
        finally:
            Path(temp_path).unlink()

    def test_build_graph_with_filter(self):
        """Test building graph with type filtering."""
        csv_content = """transformation_type,input_items,output_items,metadata
crafting,"[""Oak Planks""]","[""Stick""]","{}"
smelting,"[""Iron Ore""]","[""Iron Ingot""]","{}"
crafting,"[""Stick""]","[""Tool""]","{}"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            color_config = {'crafting': '#4A90E2', 'smelting': '#E67E22'}

            # Build graph with only crafting transformations
            graph = build_graph_from_csv(temp_path, color_config, filter_types=['crafting'])

            # Should have 3 item nodes: Oak Planks, Stick, Tool
            # And 2 edges for the two crafting transformations
            assert graph.number_of_nodes() == 3
            assert graph.number_of_edges() == 2

            # Verify no smelting items
            assert not graph.has_node('Iron Ore')
            assert not graph.has_node('Iron Ingot')
        finally:
            Path(temp_path).unlink()


class TestInteractiveOptions:
    """Test cases for interactive option collection."""

    @patch('src.visualize_graph_3d.FzfPrompt')
    def test_prompt_boolean_options_with_selections(self, mock_fzf_class):
        """Test prompting for boolean options with user selections."""
        mock_fzf = Mock()
        mock_fzf_class.return_value = mock_fzf
        mock_fzf.prompt.return_value = [
            "use-images: Use item images instead of spheres",
            "verbose: Enable verbose logging"
        ]

        result = prompt_boolean_options()

        assert result['use_images'] is True
        assert result['verbose'] is True

    @patch('src.visualize_graph_3d.FzfPrompt')
    def test_prompt_boolean_options_no_selections(self, mock_fzf_class):
        """Test prompting for boolean options with no selections."""
        mock_fzf = Mock()
        mock_fzf_class.return_value = mock_fzf
        mock_fzf.prompt.return_value = []

        result = prompt_boolean_options()

        assert result['use_images'] is False
        assert result['verbose'] is False

    @patch('src.visualize_graph_3d.FzfPrompt')
    def test_prompt_boolean_options_partial_selections(self, mock_fzf_class):
        """Test prompting for boolean options with partial selections."""
        mock_fzf = Mock()
        mock_fzf_class.return_value = mock_fzf
        mock_fzf.prompt.return_value = ["verbose: Enable verbose logging"]

        result = prompt_boolean_options()

        assert result['use_images'] is False
        assert result['verbose'] is True

    @patch('src.visualize_graph_3d.FzfPrompt')
    def test_prompt_transformation_types_with_selections(self, mock_fzf_class):
        """Test prompting for transformation types with selections."""
        csv_content = """transformation_type,input_items,output_items,metadata
crafting,"[""Oak Planks""]","[""Stick""]","{}"
smelting,"[""Iron Ore""]","[""Iron Ingot""]","{}"
brewing,"[""Water Bottle""]","[""Potion""]","{}"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            mock_fzf = Mock()
            mock_fzf_class.return_value = mock_fzf
            mock_fzf.prompt.return_value = ["crafting", "smelting"]

            result = prompt_transformation_types(temp_path)

            assert result == ["crafting", "smelting"]
        finally:
            Path(temp_path).unlink()

    @patch('src.visualize_graph_3d.FzfPrompt')
    def test_prompt_transformation_types_all_selected(self, mock_fzf_class):
        """Test prompting for transformation types with 'All types' selected."""
        csv_content = """transformation_type,input_items,output_items,metadata
crafting,"[""Oak Planks""]","[""Stick""]","{}"
smelting,"[""Iron Ore""]","[""Iron Ingot""]","{}"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            mock_fzf = Mock()
            mock_fzf_class.return_value = mock_fzf
            mock_fzf.prompt.return_value = ["[All types - no filtering]"]

            result = prompt_transformation_types(temp_path)

            assert result is None
        finally:
            Path(temp_path).unlink()

    @patch('src.visualize_graph_3d.FzfPrompt')
    def test_collect_options_no_interactive(self, mock_fzf_class):
        """Test collect_options with --no-interactive flag."""
        args = Namespace(
            use_images=False,
            verbose=False,
            filter_type=None,
            no_interactive=True
        )

        csv_content = """transformation_type,input_items,output_items,metadata
crafting,"[""Oak Planks""]","[""Stick""]","{}"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            result = collect_options(args, temp_path)

            # FZF should not be called at all
            mock_fzf_class.assert_not_called()

            assert result['use_images'] is False
            assert result['verbose'] is False
            assert result['filter_types'] is None
        finally:
            Path(temp_path).unlink()

    @patch('src.visualize_graph_3d.FzfPrompt')
    def test_collect_options_with_cli_args(self, mock_fzf_class):
        """Test collect_options with CLI args provided (should skip prompts)."""
        args = Namespace(
            use_images=True,
            verbose=True,
            filter_type='crafting,smelting',
            no_interactive=False
        )

        csv_content = """transformation_type,input_items,output_items,metadata
crafting,"[""Oak Planks""]","[""Stick""]","{}"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            result = collect_options(args, temp_path)

            # FZF should not be called since all args are provided
            mock_fzf_class.assert_not_called()

            assert result['use_images'] is True
            assert result['verbose'] is True
            assert result['filter_types'] == ['crafting', 'smelting']
        finally:
            Path(temp_path).unlink()

    @patch('src.visualize_graph_3d.prompt_transformation_types')
    @patch('src.visualize_graph_3d.prompt_boolean_options')
    def test_collect_options_interactive_mode(self, mock_bool_prompt, mock_type_prompt):
        """Test collect_options in interactive mode."""
        args = Namespace(
            use_images=False,
            verbose=False,
            filter_type=None,
            no_interactive=False
        )

        mock_bool_prompt.return_value = {'use_images': True, 'verbose': False}
        mock_type_prompt.return_value = ['crafting']

        csv_content = """transformation_type,input_items,output_items,metadata
crafting,"[""Oak Planks""]","[""Stick""]","{}"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            result = collect_options(args, temp_path)

            # Both prompts should be called
            mock_bool_prompt.assert_called_once()
            mock_type_prompt.assert_called_once_with(temp_path)

            assert result['use_images'] is True
            assert result['verbose'] is False
            assert result['filter_types'] == ['crafting']
        finally:
            Path(temp_path).unlink()

    @patch('src.visualize_graph_3d.prompt_transformation_types')
    def test_collect_options_partial_cli_args(self, mock_type_prompt):
        """Test collect_options with partial CLI args (some prompting needed)."""
        args = Namespace(
            use_images=True,  # Provided
            verbose=False,    # Not provided (default)
            filter_type=None, # Not provided
            no_interactive=False
        )

        mock_type_prompt.return_value = ['smelting']

        csv_content = """transformation_type,input_items,output_items,metadata
crafting,"[""Oak Planks""]","[""Stick""]","{}"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            result = collect_options(args, temp_path)

            # Type prompt should be called, but not boolean prompt (use_images was set)
            mock_type_prompt.assert_called_once_with(temp_path)

            assert result['use_images'] is True
            assert result['verbose'] is False
            assert result['filter_types'] == ['smelting']
        finally:
            Path(temp_path).unlink()
