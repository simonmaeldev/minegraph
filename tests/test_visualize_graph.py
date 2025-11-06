"""Unit tests for graph visualization module."""

import json
import tempfile
from pathlib import Path

import pytest

from src.visualize_graph_with_graphviz import (
    TransformationGraphBuilder,
    generate_graph,
    load_color_config,
    load_transformations_from_csv,
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

    def test_empty_csv(self):
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

    def test_missing_csv_raises_error(self):
        """Test that missing CSV file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_transformations_from_csv('/nonexistent/path/data.csv')

    def test_malformed_json_rows_are_skipped(self):
        """Test that rows with malformed JSON are skipped gracefully."""
        csv_content = """transformation_type,input_items,output_items,metadata
crafting,"[""Oak Planks""]","[""Crafting Table""]","{""source"":""test""}"
invalid,"invalid json","[""Item""]","{}"
smelting,"[""Iron Ore""]","[""Iron Ingot""]","{}"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            transformations = load_transformations_from_csv(temp_path)
            # Should load 2 valid rows, skip 1 invalid
            assert len(transformations) == 2
        finally:
            Path(temp_path).unlink()


class TestTransformationGraphBuilder:
    """Test cases for the TransformationGraphBuilder class."""

    def test_create_item_node(self):
        """Test creating item nodes."""
        builder = TransformationGraphBuilder()
        builder.add_item_node("Diamond")
        assert "Diamond" in builder.item_nodes

    def test_duplicate_nodes_not_created(self):
        """Test that duplicate item nodes are not created."""
        builder = TransformationGraphBuilder()
        builder.add_item_node("Diamond")
        builder.add_item_node("Diamond")
        # Should only have one node
        assert len(builder.item_nodes) == 1

    def test_create_intermediate_nodes_with_unique_ids(self):
        """Test that intermediate nodes have unique IDs."""
        builder = TransformationGraphBuilder()
        id1 = builder.create_intermediate_node()
        id2 = builder.create_intermediate_node()
        id3 = builder.create_intermediate_node()

        assert id1 != id2
        assert id2 != id3
        assert id1 != id3
        assert builder.intermediate_counter == 3

    def test_single_input_transformation(self):
        """Test adding a single-input transformation."""
        builder = TransformationGraphBuilder()
        builder.add_single_input_transformation("Iron Ore", "Iron Ingot", "#E67E22")

        assert "Iron Ore" in builder.item_nodes
        assert "Iron Ingot" in builder.item_nodes
        assert len(builder.item_nodes) == 2

    def test_multi_input_transformation(self):
        """Test adding a multi-input transformation."""
        builder = TransformationGraphBuilder()
        builder.add_multi_input_transformation(
            ["Iron Ingot", "Stick"],
            "Iron Pickaxe",
            "#4A90E2"
        )

        assert "Iron Ingot" in builder.item_nodes
        assert "Stick" in builder.item_nodes
        assert "Iron Pickaxe" in builder.item_nodes
        assert builder.intermediate_counter == 1  # One intermediate node created

    def test_render_creates_files(self):
        """Test that render creates output files."""
        builder = TransformationGraphBuilder()
        builder.add_single_input_transformation("Iron Ore", "Iron Ingot", "#E67E22")

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = str(Path(temp_dir) / "test_graph")
            created_files = builder.render(output_path, ['svg'])

            assert len(created_files) == 1
            assert Path(created_files[0]).exists()
            assert created_files[0].endswith('.svg')


class TestGenerateGraph:
    """Test cases for the main generate_graph function."""

    def test_generate_graph_integration(self):
        """Integration test for generating a complete graph."""
        # Create test CSV
        csv_content = """transformation_type,input_items,output_items,metadata
crafting,"[""Oak Planks""]","[""Crafting Table""]","{}"
crafting,"[""Iron Ingot"",""Stick""]","[""Iron Pickaxe""]","{}"
smelting,"[""Iron Ore""]","[""Iron Ingot""]","{}"
"""
        # Create test config
        config_content = """crafting=#4A90E2
smelting=#E67E22
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            # Write CSV
            csv_path = Path(temp_dir) / "test_transformations.csv"
            csv_path.write_text(csv_content)

            # Write config
            config_path = Path(temp_dir) / "test_config.txt"
            config_path.write_text(config_content)

            # Generate graph
            output_path = str(Path(temp_dir) / "test_graph")
            created_files = generate_graph(
                csv_path=str(csv_path),
                config_path=str(config_path),
                output_path=output_path,
                formats=['svg']
            )

            assert len(created_files) == 1
            assert Path(created_files[0]).exists()
            assert created_files[0].endswith('.svg')

    def test_generate_graph_with_filter(self):
        """Test generating graph with transformation type filter."""
        csv_content = """transformation_type,input_items,output_items,metadata
crafting,"[""Oak Planks""]","[""Crafting Table""]","{}"
smelting,"[""Iron Ore""]","[""Iron Ingot""]","{}"
crafting,"[""Iron Ingot""]","[""Iron Block""]","{}"
"""
        config_content = """crafting=#4A90E2
smelting=#E67E22
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "test_transformations.csv"
            csv_path.write_text(csv_content)

            config_path = Path(temp_dir) / "test_config.txt"
            config_path.write_text(config_content)

            output_path = str(Path(temp_dir) / "test_graph")
            created_files = generate_graph(
                csv_path=str(csv_path),
                config_path=str(config_path),
                output_path=output_path,
                formats=['svg'],
                filter_type='crafting'
            )

            assert len(created_files) == 1
            assert Path(created_files[0]).exists()

    def test_generate_graph_multiple_formats(self):
        """Test generating graph in multiple formats."""
        csv_content = """transformation_type,input_items,output_items,metadata
crafting,"[""Oak Planks""]","[""Crafting Table""]","{}"
"""
        config_content = """crafting=#4A90E2
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "test_transformations.csv"
            csv_path.write_text(csv_content)

            config_path = Path(temp_dir) / "test_config.txt"
            config_path.write_text(config_content)

            output_path = str(Path(temp_dir) / "test_graph")
            created_files = generate_graph(
                csv_path=str(csv_path),
                config_path=str(config_path),
                output_path=output_path,
                formats=['svg', 'png']
            )

            assert len(created_files) == 2
            svg_files = [f for f in created_files if f.endswith('.svg')]
            png_files = [f for f in created_files if f.endswith('.png')]
            assert len(svg_files) == 1
            assert len(png_files) == 1
