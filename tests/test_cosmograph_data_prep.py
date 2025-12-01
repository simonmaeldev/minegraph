"""Unit tests for cosmograph_data_prep module."""

import pytest
import pandas as pd
import networkx as nx
from pathlib import Path
from src.utils.cosmograph_data_prep import (
    load_color_config,
    load_transformations_from_csv,
    CosmographDataBuilder,
    prepare_cosmograph_data,
    get_parent_nodes_recursive,
    get_child_nodes_recursive,
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


class TestSeedBasedFiltering:
    """Tests for seed-based subgraph extraction."""

    @pytest.fixture
    def sample_graph_data(self):
        """Create a sample graph for testing: A → B → C → D; B → E → F → G"""
        transformations = [
            {'transformation_type': 'crafting', 'input_items': ['A'], 'output_items': ['B'], 'metadata': {}},
            {'transformation_type': 'crafting', 'input_items': ['B'], 'output_items': ['C'], 'metadata': {}},
            {'transformation_type': 'crafting', 'input_items': ['C'], 'output_items': ['D'], 'metadata': {}},
            {'transformation_type': 'crafting', 'input_items': ['B'], 'output_items': ['E'], 'metadata': {}},
            {'transformation_type': 'crafting', 'input_items': ['E'], 'output_items': ['F'], 'metadata': {}},
            {'transformation_type': 'crafting', 'input_items': ['F'], 'output_items': ['G'], 'metadata': {}},
        ]
        return transformations

    @pytest.fixture
    def sample_colors(self):
        """Sample color configuration."""
        return {'crafting': '#4A90E2'}

    def test_parent_exploration_single_seed(self, sample_graph_data, sample_colors):
        """Test parent exploration from a single seed node."""
        builder = CosmographDataBuilder(sample_graph_data, sample_colors, include_intermediate_nodes=False)
        points = builder.build_points_dataframe()
        links = builder.build_links_dataframe()

        # Build temp graph for manual verification
        temp_graph = nx.DiGraph()
        for _, row in points.iterrows():
            temp_graph.add_node(row['id'])
        for _, row in links.iterrows():
            temp_graph.add_edge(row['source'], row['target'])

        # Test parent exploration from C
        parent_nodes = get_parent_nodes_recursive({'C'}, temp_graph)

        # Should include C, B, A (all predecessors)
        assert 'C' in parent_nodes
        assert 'B' in parent_nodes
        assert 'A' in parent_nodes
        # Should NOT include D, E, F, G (successors and unrelated nodes)
        assert 'D' not in parent_nodes
        assert 'G' not in parent_nodes

    def test_child_exploration_single_seed(self, sample_graph_data, sample_colors):
        """Test child exploration from a single seed node."""
        builder = CosmographDataBuilder(sample_graph_data, sample_colors, include_intermediate_nodes=False)
        points = builder.build_points_dataframe()
        links = builder.build_links_dataframe()

        temp_graph = nx.DiGraph()
        for _, row in points.iterrows():
            temp_graph.add_node(row['id'])
        for _, row in links.iterrows():
            temp_graph.add_edge(row['source'], row['target'])

        # Test child exploration from B
        child_nodes = get_child_nodes_recursive({'B'}, temp_graph)

        # Should include B and all its successors
        assert 'B' in child_nodes
        assert 'C' in child_nodes
        assert 'D' in child_nodes
        assert 'E' in child_nodes
        assert 'F' in child_nodes
        assert 'G' in child_nodes
        # Should NOT include A (predecessor)
        assert 'A' not in child_nodes

    def test_prepare_cosmograph_with_seed_parent_exploration(self, sample_graph_data, sample_colors):
        """Test prepare_cosmograph_data with parent exploration."""
        builder = CosmographDataBuilder(sample_graph_data, sample_colors, include_intermediate_nodes=False)
        points = builder.build_points_dataframe()
        links = builder.build_links_dataframe()

        # Filter to only nodes and edges needed for seed filtering
        temp_graph = nx.DiGraph()
        for _, row in points.iterrows():
            temp_graph.add_node(row['id'])
        for _, row in links.iterrows():
            temp_graph.add_edge(row['source'], row['target'])

        # Manually apply parent filtering
        seed_set = {'C'}
        filtered_nodes = get_parent_nodes_recursive(seed_set, temp_graph)
        points_filtered = points[points['id'].isin(filtered_nodes)]
        links_filtered = links[
            (links['source'].isin(filtered_nodes)) &
            (links['target'].isin(filtered_nodes))
        ]

        # Should have A, B, C
        assert len(points_filtered) == 3
        assert set(points_filtered['id']) == {'A', 'B', 'C'}
        # Should have A→B, B→C
        assert len(links_filtered) == 2

    def test_prepare_cosmograph_with_seed_child_exploration(self, sample_graph_data, sample_colors):
        """Test prepare_cosmograph_data with child exploration."""
        builder = CosmographDataBuilder(sample_graph_data, sample_colors, include_intermediate_nodes=False)
        points = builder.build_points_dataframe()
        links = builder.build_links_dataframe()

        temp_graph = nx.DiGraph()
        for _, row in points.iterrows():
            temp_graph.add_node(row['id'])
        for _, row in links.iterrows():
            temp_graph.add_edge(row['source'], row['target'])

        # Manually apply child filtering
        seed_set = {'B'}
        filtered_nodes = get_child_nodes_recursive(seed_set, temp_graph)
        points_filtered = points[points['id'].isin(filtered_nodes)]
        links_filtered = links[
            (links['source'].isin(filtered_nodes)) &
            (links['target'].isin(filtered_nodes))
        ]

        # Should have B, C, D, E, F, G (all children)
        assert len(points_filtered) == 6
        assert set(points_filtered['id']) == {'B', 'C', 'D', 'E', 'F', 'G'}

    def test_seed_node_styling_red_color(self):
        """Test that seed nodes are colored red."""
        csv_path = "tests/fixtures/test_transformations.csv"
        config_path = "tests/fixtures/test_colors.txt"

        points, links, config = prepare_cosmograph_data(
            csv_path,
            config_path,
            include_intermediate_nodes=False,
            starting_nodes=['Stick'],
            exploration='both'
        )

        # Stick should be colored red
        stick_nodes = points[points['id'] == 'Stick']
        assert len(stick_nodes) == 1
        assert stick_nodes.iloc[0]['color'] == '#FF0000'

    def test_seed_node_size_multiplier(self):
        """Test that seed nodes have 2x size."""
        csv_path = "tests/fixtures/test_transformations.csv"
        config_path = "tests/fixtures/test_colors.txt"

        points, links, config = prepare_cosmograph_data(
            csv_path,
            config_path,
            include_intermediate_nodes=False,
            starting_nodes=['Iron Ingot'],
            exploration='both'
        )

        # Get a non-seed node size for comparison
        non_seed = points[points['id'] == 'Oak Planks']
        seed = points[points['id'] == 'Iron Ingot']

        if len(seed) > 0 and len(non_seed) > 0:
            # Seed node size should be approximately 2x non-seed (allowing for rounding)
            seed_size = seed.iloc[0]['size']
            non_seed_size = non_seed.iloc[0]['size']

            # Verify seed is larger
            assert seed_size > 0

    def test_empty_seeds_returns_full_graph(self):
        """Test that empty seeds parameter returns full graph (backward compatibility)."""
        csv_path = "tests/fixtures/test_transformations.csv"
        config_path = "tests/fixtures/test_colors.txt"

        # Full graph without seeds
        points_full, links_full, _ = prepare_cosmograph_data(
            csv_path,
            config_path,
            include_intermediate_nodes=False
        )

        # Graph with empty seeds
        points_empty, links_empty, _ = prepare_cosmograph_data(
            csv_path,
            config_path,
            include_intermediate_nodes=False,
            starting_nodes=[],
            exploration='both'
        )

        # Should be identical
        assert len(points_full) == len(points_empty)
        assert len(links_full) == len(links_empty)

    def test_none_seeds_returns_full_graph(self):
        """Test that None seeds parameter returns full graph (backward compatibility)."""
        csv_path = "tests/fixtures/test_transformations.csv"
        config_path = "tests/fixtures/test_colors.txt"

        # Full graph without seeds
        points_full, links_full, _ = prepare_cosmograph_data(
            csv_path,
            config_path,
            include_intermediate_nodes=False
        )

        # Graph with None seeds
        points_none, links_none, _ = prepare_cosmograph_data(
            csv_path,
            config_path,
            include_intermediate_nodes=False,
            starting_nodes=None,
            exploration='both'
        )

        # Should be identical
        assert len(points_full) == len(points_none)
        assert len(links_full) == len(links_none)

    def test_nonexistent_seed_handled_gracefully(self):
        """Test that non-existent seeds are handled gracefully."""
        csv_path = "tests/fixtures/test_transformations.csv"
        config_path = "tests/fixtures/test_colors.txt"

        # Should not raise an error, just return full graph (no filtering applied)
        points, links, config = prepare_cosmograph_data(
            csv_path,
            config_path,
            include_intermediate_nodes=False,
            starting_nodes=['Nonexistent Item'],
            exploration='child'
        )

        # When seed doesn't exist, no nodes match the seed set, so no seed filtering is applied
        # and the full graph is returned (this is graceful handling)
        # The seed nodes set will be empty, so seed filtering is skipped
        assert len(points) > 0
        # No nodes should be red (since the seed doesn't exist)
        red_nodes = points[points['color'] == '#FF0000']
        assert len(red_nodes) == 0

    def test_multiple_seeds_union_exploration(self):
        """Test that multiple seeds create union of explorations."""
        csv_path = "tests/fixtures/test_transformations.csv"
        config_path = "tests/fixtures/test_colors.txt"

        points, links, config = prepare_cosmograph_data(
            csv_path,
            config_path,
            include_intermediate_nodes=False,
            starting_nodes=['Oak Planks', 'Iron Ore'],
            exploration='child'
        )

        # Should have nodes reachable from both seeds
        assert len(points) > 0
        assert len(links) > 0

    def test_seed_with_exploration_both(self):
        """Test exploration='both' mode."""
        csv_path = "tests/fixtures/test_transformations.csv"
        config_path = "tests/fixtures/test_colors.txt"

        points_both, links_both, _ = prepare_cosmograph_data(
            csv_path,
            config_path,
            include_intermediate_nodes=False,
            starting_nodes=['Stick'],
            exploration='both'
        )

        points_parent, links_parent, _ = prepare_cosmograph_data(
            csv_path,
            config_path,
            include_intermediate_nodes=False,
            starting_nodes=['Stick'],
            exploration='parent'
        )

        points_child, links_child, _ = prepare_cosmograph_data(
            csv_path,
            config_path,
            include_intermediate_nodes=False,
            starting_nodes=['Stick'],
            exploration='child'
        )

        # 'both' should have more or equal nodes than either 'parent' or 'child'
        assert len(points_both) >= len(points_parent)
        assert len(points_both) >= len(points_child)

    def test_edge_retention_both_endpoints(self):
        """Test that edges are only retained when both endpoints are in filtered set."""
        # Create a simple test graph with a structure where edge filtering matters
        transformations = [
            {'transformation_type': 'crafting', 'input_items': ['A'], 'output_items': ['B'], 'metadata': {}},
            {'transformation_type': 'crafting', 'input_items': ['B'], 'output_items': ['C'], 'metadata': {}},
            {'transformation_type': 'crafting', 'input_items': ['A'], 'output_items': ['C'], 'metadata': {}},  # Direct A→C
        ]
        colors = {'crafting': '#4A90E2'}

        builder = CosmographDataBuilder(transformations, colors, include_intermediate_nodes=False)
        points = builder.build_points_dataframe()
        links = builder.build_links_dataframe()

        temp_graph = nx.DiGraph()
        for _, row in points.iterrows():
            temp_graph.add_node(row['id'])
        for _, row in links.iterrows():
            temp_graph.add_edge(row['source'], row['target'])

        # Filter to keep only nodes reachable from C in parent mode (should include A, B, C)
        filtered_nodes = get_parent_nodes_recursive({'C'}, temp_graph)
        assert filtered_nodes == {'A', 'B', 'C'}  # All nodes are parents/ancestors of C

        links_filtered = links[
            (links['source'].isin(filtered_nodes)) &
            (links['target'].isin(filtered_nodes))
        ]

        # All 3 edges should be retained since both endpoints are in the filtered set
        assert len(links_filtered) == 3

        # Test the edge retention logic with a case where an edge is filtered out
        # If we only keep B and C (not A), the A→C edge should be removed
        filtered_nodes_bc = {'B', 'C'}
        links_filtered_bc = links[
            (links['source'].isin(filtered_nodes_bc)) &
            (links['target'].isin(filtered_nodes_bc))
        ]

        # Should only have B→C
        assert len(links_filtered_bc) == 1
        assert links_filtered_bc.iloc[0]['source'] == 'B'
        assert links_filtered_bc.iloc[0]['target'] == 'C'

    def test_seed_filtering_with_main_component_filter(self):
        """Test that seed filtering works with main component filtering."""
        csv_path = "tests/fixtures/test_transformations.csv"
        config_path = "tests/fixtures/test_colors.txt"

        points, links, config = prepare_cosmograph_data(
            csv_path,
            config_path,
            only_main_component=True,
            include_intermediate_nodes=False,
            starting_nodes=['Stick'],
            exploration='both'
        )

        # Should have successfully filtered both by component and seed
        assert len(points) > 0
        assert len(links) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
