"""Unit tests for cosmograph_data_prep module."""

import pytest
import pandas as pd
from pathlib import Path
from src.utils.cosmograph_data_prep import (
    load_color_config,
    load_transformations_from_csv,
    CosmographDataBuilder,
    prepare_cosmograph_data,
    DEFAULT_COLORS,
    INTERMEDIATE_NODE_COLOR,
    INTERMEDIATE_NODE_SIZE,
)


class TestLoadColorConfig:
    """Tests for load_color_config function."""

    def test_load_valid_config(self):
        """Test loading a valid configuration file."""
        config_path = "tests/fixtures/test_colors.txt"
        colors = load_color_config(config_path)

        assert "crafting" in colors
        assert colors["crafting"] == "#4A90E2"
        assert colors["smelting"] == "#E67E22"
        assert colors["custom_type"] == "#ABCDEF"

    def test_missing_config_returns_defaults(self):
        """Test that missing config file returns default colors."""
        colors = load_color_config("nonexistent_file.txt")

        # Should return defaults
        assert colors == DEFAULT_COLORS
        assert "crafting" in colors
        assert "smelting" in colors

    def test_config_with_comments_and_empty_lines(self):
        """Test that comments and empty lines are handled correctly."""
        config_path = "tests/fixtures/test_colors.txt"
        colors = load_color_config(config_path)

        # Should skip comments and parse only valid lines
        assert isinstance(colors, dict)
        assert len(colors) > 0


class TestLoadTransformationsFromCSV:
    """Tests for load_transformations_from_csv function."""

    def test_load_valid_csv(self):
        """Test loading a valid CSV file."""
        csv_path = "tests/fixtures/test_transformations.csv"
        transformations = load_transformations_from_csv(csv_path)

        assert len(transformations) == 4
        assert transformations[0]['transformation_type'] == 'crafting'
        assert transformations[0]['input_items'] == ['Oak Planks']
        assert transformations[0]['output_items'] == ['Stick']

    def test_parse_json_arrays(self):
        """Test that JSON arrays are correctly parsed."""
        csv_path = "tests/fixtures/test_transformations.csv"
        transformations = load_transformations_from_csv(csv_path)

        # Check single input
        assert isinstance(transformations[0]['input_items'], list)
        assert len(transformations[0]['input_items']) == 1

        # Check multi-input
        multi_input_trans = transformations[2]
        assert len(multi_input_trans['input_items']) == 2
        assert 'Iron Ingot' in multi_input_trans['input_items']
        assert 'Stick' in multi_input_trans['input_items']

    def test_missing_csv_raises_error(self):
        """Test that missing CSV file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_transformations_from_csv("nonexistent.csv")


class TestCosmographDataBuilder:
    """Tests for CosmographDataBuilder class."""

    @pytest.fixture
    def sample_transformations(self):
        """Sample transformation data for testing."""
        return [
            {
                'transformation_type': 'crafting',
                'input_items': ['Oak Planks'],
                'output_items': ['Stick'],
                'metadata': {}
            },
            {
                'transformation_type': 'crafting',
                'input_items': ['Iron Ingot', 'Stick'],
                'output_items': ['Iron Sword'],
                'metadata': {}
            },
            {
                'transformation_type': 'smelting',
                'input_items': ['Iron Ore'],
                'output_items': ['Iron Ingot'],
                'metadata': {}
            }
        ]

    @pytest.fixture
    def sample_colors(self):
        """Sample color configuration."""
        return {
            'crafting': '#4A90E2',
            'smelting': '#E67E22'
        }

    def test_build_points_dataframe_creates_all_items(self, sample_transformations, sample_colors):
        """Test that all unique items are added as points."""
        builder = CosmographDataBuilder(sample_transformations, sample_colors)
        points = builder.build_points_dataframe()

        # Should have 4 unique items + 1 intermediate node
        unique_items = {'Oak Planks', 'Stick', 'Iron Ingot', 'Iron Sword', 'Iron Ore'}
        item_nodes = points[points['node_type'] == 'item']

        assert len(item_nodes) == len(unique_items)
        assert set(item_nodes['id']) == unique_items

    def test_build_points_creates_intermediate_nodes(self, sample_transformations, sample_colors):
        """Test that intermediate nodes are created for multi-input transformations."""
        builder = CosmographDataBuilder(sample_transformations, sample_colors)
        points = builder.build_points_dataframe()

        intermediate_nodes = points[points['node_type'] == 'intermediate']

        # Should have 1 intermediate node (for Iron Sword recipe)
        assert len(intermediate_nodes) == 1
        assert intermediate_nodes.iloc[0]['id'].startswith('intermediate_')
        assert intermediate_nodes.iloc[0]['color'] == INTERMEDIATE_NODE_COLOR
        assert intermediate_nodes.iloc[0]['size'] == INTERMEDIATE_NODE_SIZE

    def test_build_points_dataframe_has_required_columns(self, sample_transformations, sample_colors):
        """Test that points DataFrame has all required columns."""
        builder = CosmographDataBuilder(sample_transformations, sample_colors)
        points = builder.build_points_dataframe()

        required_columns = {'id', 'label', 'node_type', 'size', 'color'}
        assert set(points.columns) == required_columns

    def test_build_links_dataframe_single_input(self, sample_transformations, sample_colors):
        """Test that single-input transformations create direct links."""
        builder = CosmographDataBuilder(sample_transformations, sample_colors)
        builder.build_points_dataframe()  # Need to build points first
        links = builder.build_links_dataframe()

        # Find the Oak Planks -> Stick link
        direct_link = links[(links['source'] == 'Oak Planks') & (links['target'] == 'Stick')]

        assert len(direct_link) == 1
        assert direct_link.iloc[0]['transformation_type'] == 'crafting'
        assert direct_link.iloc[0]['color'] == '#4A90E2'
        assert direct_link.iloc[0]['arrows'] == True

    def test_build_links_dataframe_multi_input(self, sample_transformations, sample_colors):
        """Test that multi-input transformations create intermediate links."""
        builder = CosmographDataBuilder(sample_transformations, sample_colors)
        builder.build_points_dataframe()
        links = builder.build_links_dataframe()

        # Check that intermediate nodes are involved in some links
        intermediate_involved = links[
            links['source'].str.startswith('intermediate_') |
            links['target'].str.startswith('intermediate_')
        ]

        # Should have at least 3 links involving intermediate nodes
        # (2 multi-input transformations, each creates 3 links: 2 inputs->intermediate + intermediate->output)
        assert len(intermediate_involved) >= 3

    def test_build_links_dataframe_has_required_columns(self, sample_transformations, sample_colors):
        """Test that links DataFrame has all required columns."""
        builder = CosmographDataBuilder(sample_transformations, sample_colors)
        builder.build_points_dataframe()
        links = builder.build_links_dataframe()

        required_columns = {'source', 'target', 'transformation_type', 'color', 'arrows'}
        assert set(links.columns) == required_columns

    def test_all_links_have_arrows(self, sample_transformations, sample_colors):
        """Test that all links have arrows enabled."""
        builder = CosmographDataBuilder(sample_transformations, sample_colors)
        builder.build_points_dataframe()
        links = builder.build_links_dataframe()

        assert all(links['arrows'] == True)

    def test_calculate_node_sizes(self, sample_transformations, sample_colors):
        """Test that node sizes are calculated based on degree."""
        builder = CosmographDataBuilder(sample_transformations, sample_colors)
        points = builder.build_points_dataframe()
        links = builder.build_links_dataframe()
        points = builder.calculate_node_sizes(points, links)

        # Intermediate nodes should always be small
        intermediate = points[points['node_type'] == 'intermediate']
        assert all(intermediate['size'] == INTERMEDIATE_NODE_SIZE)

        # Item nodes should have varying sizes based on degree
        items = points[points['node_type'] == 'item']
        # Stick appears in multiple transformations, should have larger size
        stick_size = items[items['id'] == 'Stick']['size'].values[0]
        # Oak Planks appears less, should have smaller size
        oak_size = items[items['id'] == 'Oak Planks']['size'].values[0]

        # Both should be within valid range
        assert 10 <= stick_size <= 30
        assert 10 <= oak_size <= 30


class TestPrepareCosmographData:
    """Tests for the main prepare_cosmograph_data function."""

    def test_prepare_data_end_to_end(self):
        """Test the complete data preparation pipeline."""
        csv_path = "tests/fixtures/test_transformations.csv"
        config_path = "tests/fixtures/test_colors.txt"

        points, links, config = prepare_cosmograph_data(csv_path, config_path)

        # Verify output types
        assert isinstance(points, pd.DataFrame)
        assert isinstance(links, pd.DataFrame)
        assert isinstance(config, dict)

        # Verify data integrity
        assert len(points) > 0
        assert len(links) > 0
        assert len(config) > 0

        # Verify columns
        assert 'id' in points.columns
        assert 'source' in links.columns
        assert 'target' in links.columns

    def test_prepare_data_returns_correct_counts(self):
        """Test that data preparation returns correct node and edge counts."""
        csv_path = "tests/fixtures/test_transformations.csv"
        config_path = "tests/fixtures/test_colors.txt"

        points, links, config = prepare_cosmograph_data(csv_path, config_path)

        # 6 unique items + 2 intermediate nodes (for multi-input transformations)
        # Items: Oak Planks, Stick, Iron Ingot, Iron Sword, Iron Ore, Wooden Pickaxe
        assert len(points) == 8

        # Should have more links than original transformations due to intermediate nodes
        # 2 single-input transformations = 2 links
        # 2 multi-input transformations = 6 links (2 inputs->intermediate + intermediate->output each)
        assert len(links) >= 8


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
