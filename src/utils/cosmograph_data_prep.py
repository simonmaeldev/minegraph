"""Utility functions for preparing Minecraft transformation data for Cosmograph visualization.

This module provides functions to transform CSV transformation data into the DataFrame format
required by Cosmograph, a GPU-accelerated graph visualization widget for Jupyter notebooks.

The main challenges addressed:
1. Parsing JSON arrays from CSV columns (input_items, output_items)
2. Creating intermediate nodes for multi-input transformations
3. Mapping transformation types to colors from configuration
4. Computing node sizes based on connectivity (degree)
5. Ensuring data integrity and unique identifiers

Typical usage:
    ```python
    from src.utils.cosmograph_data_prep import prepare_cosmograph_data

    points, links, config = prepare_cosmograph_data(
        'output/transformations.csv',
        'config/graph_colors.txt'
    )
    ```
"""

import csv
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set, Literal
import pandas as pd
import networkx as nx


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


# Default color mappings if config file is missing or incomplete
DEFAULT_COLORS = {
    "crafting": "#4A90E2",
    "smelting": "#E67E22",
    "blast_furnace": "#E67E22",
    "smoker": "#E67E22",
    "smithing": "#95A5A6",
    "stonecutter": "#7F8C8D",
    "trading": "#F39C12",
    "mob_drop": "#E74C3C",
    "brewing": "#9B59B6",
    "composting": "#27AE60",
    "grindstone": "#34495E",
    "bartering": "#D4AF37",  # Metallic gold
}

# Visual configuration
INTERMEDIATE_NODE_COLOR = "#808080"  # Gray
INTERMEDIATE_NODE_SIZE = 4
DEFAULT_ITEM_COLOR = "#FFFFFF"  # White for items without specific color
MIN_NODE_SIZE = 10
MAX_NODE_SIZE = 30


def load_color_config(config_path: str) -> Dict[str, str]:
    """Load transformation type color mappings from configuration file.

    Args:
        config_path: Path to the color configuration file (e.g., 'config/graph_colors.txt')

    Returns:
        Dictionary mapping transformation types to hex color strings

    Example:
        >>> colors = load_color_config('config/graph_colors.txt')
        >>> colors['crafting']
        '#4A90E2'
    """
    color_config = DEFAULT_COLORS.copy()

    config_file = Path(config_path)
    if not config_file.exists():
        logger.warning(f"Color config file not found: {config_path}. Using defaults.")
        return color_config

    try:
        with open(config_file, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue

                # Parse "transformation_type=color" format
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    color_config[key] = value
                    logger.debug(f"Loaded color mapping: {key} -> {value}")

        logger.info(f"Loaded {len(color_config)} color mappings from {config_path}")

    except Exception as e:
        logger.error(f"Error loading color config: {e}. Using defaults.")

    return color_config


def load_transformations_from_csv(csv_path: str) -> List[Dict]:
    """Load and parse transformation data from CSV file.

    Args:
        csv_path: Path to the transformations CSV file

    Returns:
        List of transformation dictionaries with parsed JSON fields

    Raises:
        FileNotFoundError: If CSV file doesn't exist
        ValueError: If CSV is malformed
    """
    csv_file = Path(csv_path)
    if not csv_file.exists():
        raise FileNotFoundError(f"Transformations CSV not found: {csv_path}")

    transformations = []

    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                try:
                    # Parse JSON arrays
                    transformation = {
                        'transformation_type': row['transformation_type'],
                        'input_items': json.loads(row['input_items']),
                        'output_items': json.loads(row['output_items']),
                        'metadata': json.loads(row.get('metadata', '{}'))
                    }
                    transformations.append(transformation)

                except json.JSONDecodeError as e:
                    logger.error(f"JSON parsing error in row: {row}. Error: {e}")
                    continue

        logger.info(f"Loaded {len(transformations)} transformations from {csv_path}")

    except Exception as e:
        raise ValueError(f"Error reading CSV file: {e}")

    return transformations


class CosmographDataBuilder:
    """Builder class for constructing Cosmograph-compatible DataFrames from transformation data.

    This class handles the complexity of:
    - Tracking all unique items
    - Creating intermediate nodes for multi-input transformations
    - Building points (nodes) and links (edges) DataFrames
    - Computing node sizes based on connectivity
    """

    def __init__(self, transformations: List[Dict], color_config: Dict[str, str], include_intermediate_nodes: bool = True):
        """Initialize the data builder.

        Args:
            transformations: List of transformation dictionaries
            color_config: Mapping of transformation types to colors
            include_intermediate_nodes: If True, create intermediate nodes for multi-input transformations
        """
        self.transformations = transformations
        self.color_config = color_config
        self.include_intermediate_nodes = include_intermediate_nodes
        self.intermediate_counter = 0
        self.intermediate_labels = {}  # Map intermediate_id -> label

    def build_points_dataframe(self) -> pd.DataFrame:
        """Build the points (nodes) DataFrame for Cosmograph.

        Creates nodes for:
        1. All unique items from transformations
        2. Intermediate nodes for multi-input transformations (if enabled)

        Returns:
            DataFrame with columns: id, label, node_type, size, color
        """
        points_data = []
        items_seen = set()

        # Collect all unique items first
        for trans in self.transformations:
            for item in trans['input_items']:
                items_seen.add(item)
            for item in trans['output_items']:
                items_seen.add(item)

        # Add item nodes
        for item in sorted(items_seen):
            points_data.append({
                'id': item,
                'label': item,
                'node_type': 'item',
                'size': float(MIN_NODE_SIZE),  # Will be updated based on degree
                'color': DEFAULT_ITEM_COLOR
            })

        # Add intermediate nodes for multi-input transformations (if enabled)
        if self.include_intermediate_nodes:
            for trans in self.transformations:
                if len(trans['input_items']) > 1:
                    # Create intermediate node for this multi-input transformation
                    intermediate_id = f"intermediate_{self.intermediate_counter}"
                    self.intermediate_counter += 1

                    # Create a descriptive label with input/output information
                    inputs_str = "+".join(trans['input_items'])
                    output_str = trans['output_items'][0] if trans['output_items'] else ""
                    label = f"intermediate_node|{inputs_str}={output_str}"
                    self.intermediate_labels[intermediate_id] = label

                    points_data.append({
                        'id': intermediate_id,
                        'label': label,
                        'node_type': 'intermediate',
                        'size': float(INTERMEDIATE_NODE_SIZE),
                        'color': INTERMEDIATE_NODE_COLOR
                    })

                    # Store the intermediate ID for link building
                    trans['_intermediate_id'] = intermediate_id

        df = pd.DataFrame(points_data)
        logger.info(f"Built points DataFrame: {len(items_seen)} items + {self.intermediate_counter} intermediate nodes")

        return df

    def build_links_dataframe(self) -> pd.DataFrame:
        """Build the links (edges) DataFrame for Cosmograph.

        Creates edges for:
        1. Single-input transformations: direct input -> output
        2. Multi-input transformations:
           - If intermediate nodes enabled: inputs -> intermediate -> output
           - If intermediate nodes disabled: direct inputs -> output

        Returns:
            DataFrame with columns: source, target, transformation_type, color, arrows
        """
        links_data = []

        for trans in self.transformations:
            trans_type = trans['transformation_type']
            color = self.color_config.get(trans_type, DEFAULT_ITEM_COLOR)

            if len(trans['input_items']) == 1:
                # Single input: direct edge from input to output
                input_item = trans['input_items'][0]
                for output_item in trans['output_items']:
                    links_data.append({
                        'source': input_item,
                        'target': output_item,
                        'transformation_type': trans_type,
                        'color': color,
                        'arrows': True
                    })
            else:
                # Multi-input transformations
                if self.include_intermediate_nodes:
                    # With intermediate nodes: inputs -> intermediate -> output
                    intermediate_id = trans.get('_intermediate_id')

                    if intermediate_id:
                        # Create edges from inputs to intermediate node
                        for input_item in trans['input_items']:
                            links_data.append({
                                'source': input_item,
                                'target': intermediate_id,
                                'transformation_type': trans_type,
                                'color': color,
                                'arrows': True
                            })

                        # Create edge from intermediate to output
                        for output_item in trans['output_items']:
                            links_data.append({
                                'source': intermediate_id,
                                'target': output_item,
                                'transformation_type': trans_type,
                                'color': color,
                                'arrows': True
                            })
                else:
                    # Without intermediate nodes: direct edges from each input to output
                    for input_item in trans['input_items']:
                        for output_item in trans['output_items']:
                            links_data.append({
                                'source': input_item,
                                'target': output_item,
                                'transformation_type': trans_type,
                                'color': color,
                                'arrows': True
                            })

        df = pd.DataFrame(links_data)
        logger.info(f"Built links DataFrame: {len(df)} edges")

        return df

    def calculate_node_sizes(self, points: pd.DataFrame, links: pd.DataFrame) -> pd.DataFrame:
        """Calculate node sizes based on degree (number of connections).

        Args:
            points: Points DataFrame
            links: Links DataFrame

        Returns:
            Updated points DataFrame with computed sizes
        """
        # Count degree for each node
        degree_count = {}

        for _, link in links.iterrows():
            source = link['source']
            target = link['target']
            degree_count[source] = degree_count.get(source, 0) + 1
            degree_count[target] = degree_count.get(target, 0) + 1

        # Update sizes based on degree
        for idx, row in points.iterrows():
            node_id = row['id']

            if row['node_type'] == 'intermediate':
                # Intermediate nodes always stay small
                points.at[idx, 'size'] = float(INTERMEDIATE_NODE_SIZE)
            else:
                # Item nodes scale with degree
                degree = degree_count.get(node_id, 0)
                # Scale size: higher degree = larger node
                # Use log scale to prevent extremely large nodes
                import math
                if degree > 0:
                    size = MIN_NODE_SIZE + (MAX_NODE_SIZE - MIN_NODE_SIZE) * (math.log(degree + 1) / math.log(100))
                else:
                    size = MIN_NODE_SIZE
                points.at[idx, 'size'] = float(min(size, MAX_NODE_SIZE))

        logger.info("Calculated node sizes based on connectivity")
        return points


def get_parent_nodes_recursive(
    seed_nodes: Set[str],
    graph: nx.DiGraph
) -> Set[str]:
    """Recursively find all parent nodes (predecessors) of seed nodes.

    Args:
        seed_nodes: Starting nodes
        graph: NetworkX directed graph

    Returns:
        Set of all nodes reachable by following predecessor edges
    """
    visited = set()
    to_visit = set(seed_nodes)

    while to_visit:
        current = to_visit.pop()
        if current in visited:
            continue
        visited.add(current)

        # Add all predecessors of this node
        for predecessor in graph.predecessors(current):
            if predecessor not in visited:
                to_visit.add(predecessor)

    return visited


def get_child_nodes_recursive(
    seed_nodes: Set[str],
    graph: nx.DiGraph
) -> Set[str]:
    """Recursively find all child nodes (successors) of seed nodes.

    Args:
        seed_nodes: Starting nodes
        graph: NetworkX directed graph

    Returns:
        Set of all nodes reachable by following successor edges
    """
    visited = set()
    to_visit = set(seed_nodes)

    while to_visit:
        current = to_visit.pop()
        if current in visited:
            continue
        visited.add(current)

        # Add all successors of this node
        for successor in graph.successors(current):
            if successor not in visited:
                to_visit.add(successor)

    return visited


def get_main_component_nodes(
    points: pd.DataFrame,
    links: pd.DataFrame
) -> Set[str]:
    """Extract nodes in the main (largest) weakly connected component.

    Builds a temporary NetworkX graph to identify connected components,
    then returns the set of node IDs in the largest component.

    Args:
        points: Points DataFrame with 'id' column
        links: Links DataFrame with 'source' and 'target' columns

    Returns:
        Set of node IDs in the main connected component
    """
    # Build temporary graph
    graph = nx.DiGraph()

    # Add all nodes
    for _, row in points.iterrows():
        graph.add_node(row['id'])

    # Add all edges
    for _, row in links.iterrows():
        graph.add_edge(row['source'], row['target'])

    # Find weakly connected components
    components = list(nx.weakly_connected_components(graph))

    if not components:
        # Empty graph case
        return set()

    # Return the largest component
    main_component = max(components, key=len)
    logger.info(f"Main component has {len(main_component)} nodes out of {len(graph.nodes())}")

    return main_component


def prepare_cosmograph_data(
    csv_path: str,
    config_path: str,
    only_main_component: bool = False,
    filter_link: List[str] = None,
    include_intermediate_nodes: bool = True,
    starting_nodes: Optional[List[str]] = None,
    exploration: Literal['parent', 'child', 'both'] = 'both'
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, str]]:
    """Prepare all data needed for Cosmograph visualization.

    This is the main entry point for data preparation. It orchestrates:
    1. Loading color configuration
    2. Loading transformation data
    3. Building points and links DataFrames
    4. Computing node sizes
    5. Optionally filtering to only the main connected component
    6. Optionally excluding intermediate nodes
    7. Optionally filtering by seed nodes and exploration direction

    Args:
        csv_path: Path to transformations CSV file
        config_path: Path to color configuration file
        only_main_component: If True, filter to only nodes in the largest connected component
        filter_link: Optional list of transformation types to include
        include_intermediate_nodes: If True, include intermediate nodes for multi-input transformations
        starting_nodes: Optional list of seed node names. If None or empty, all nodes are kept.
                       If provided, only nodes reachable from seeds (based on exploration direction) are retained.
        exploration: Direction of recursive exploration from seeds - 'parent' (predecessors),
                    'child' (successors), or 'both' (both directions).

    Returns:
        Tuple of (points_df, links_df, color_config)

    Example:
        >>> points, links, config = prepare_cosmograph_data(
        ...     'output/transformations.csv',
        ...     'config/graph_colors.txt'
        ... )
        >>> print(f"Nodes: {len(points)}, Edges: {len(links)}")

        >>> # Explore all ingredients (parents) needed to craft a Diamond Sword
        >>> points, links, config = prepare_cosmograph_data(
        ...     'output/technical_transformations.csv',
        ...     'config/graph_colors.txt',
        ...     only_main_component=True,
        ...     include_intermediate_nodes=False,
        ...     starting_nodes=['Diamond Sword'],
        ...     exploration='parent'
        ... )

        >>> # Explore all items that can be crafted from Iron Ingot (children)
        >>> points, links, config = prepare_cosmograph_data(
        ...     'output/technical_transformations.csv',
        ...     'config/graph_colors.txt',
        ...     only_main_component=True,
        ...     include_intermediate_nodes=False,
        ...     starting_nodes=['Iron Ingot'],
        ...     exploration='child'
        ... )

        >>> # To get only the main component without intermediate nodes:
        >>> points, links, config = prepare_cosmograph_data(
        ...     'output/transformations.csv',
        ...     'config/graph_colors.txt',
        ...     only_main_component=True,
        ...     include_intermediate_nodes=False
        ... )
    """
    logger.info("Starting Cosmograph data preparation...")

    # Load configuration and data
    color_config = load_color_config(config_path)
    transformations = load_transformations_from_csv(csv_path)

    # Build DataFrames
    builder = CosmographDataBuilder(transformations, color_config, include_intermediate_nodes)
    points = builder.build_points_dataframe()
    links = builder.build_links_dataframe()

    # Filter to only get the transformations types
    if filter_link:
        filtered_links = links[links['transformation_type'].isin(filter_link)]
        filtered_node_ids = set(filtered_links['source']).union(set(filtered_links['target']))
        filtered_points = points[points['id'].isin(filtered_node_ids)]
        points = filtered_points
        links = filtered_links

    # Filter to main component if requested
    if only_main_component:
        logger.info("Filtering to main connected component...")
        main_component_nodes = get_main_component_nodes(points, links)

        # Filter points to only those in the main component
        points = points[points['id'].isin(main_component_nodes)].copy()

        # Filter links to only those where both source and target are in the main component
        links = links[
            (links['source'].isin(main_component_nodes)) &
            (links['target'].isin(main_component_nodes))
        ].copy()

        logger.info(f"Filtered to main component: {len(points)} nodes, {len(links)} edges")


    # Apply seed-based filtering if seeds are provided
    seed_nodes_set = set()
    if starting_nodes:
        starting_nodes = [s for s in starting_nodes if s]  # Filter out empty strings
        if starting_nodes:
            logger.info(f"Applying seed-based filtering with {len(starting_nodes)} seeds, exploration: {exploration}")

            # Build temporary NetworkX graph
            temp_graph = nx.DiGraph()
            for _, row in points.iterrows():
                temp_graph.add_node(row['id'])
            for _, row in links.iterrows():
                temp_graph.add_edge(row['source'], row['target'])

            # Validate seeds exist in the graph
            seed_nodes_set = set(starting_nodes)
            graph_nodes = set(temp_graph.nodes())
            invalid_seeds = seed_nodes_set - graph_nodes
            if invalid_seeds:
                logger.warning(f"Seeds not found in graph: {invalid_seeds}")
                seed_nodes_set = seed_nodes_set & graph_nodes

            if seed_nodes_set:
                # Perform recursive exploration based on direction
                if exploration == 'parent':
                    filtered_nodes = get_parent_nodes_recursive(seed_nodes_set, temp_graph)
                elif exploration == 'child':
                    filtered_nodes = get_child_nodes_recursive(seed_nodes_set, temp_graph)
                else:  # 'both'
                    parent_nodes = get_parent_nodes_recursive(seed_nodes_set, temp_graph)
                    child_nodes = get_child_nodes_recursive(seed_nodes_set, temp_graph)
                    filtered_nodes = parent_nodes | child_nodes

                # Filter points to only nodes in filtered_nodes
                before_node_count = len(points)
                points = points[points['id'].isin(filtered_nodes)].copy()
                logger.info(f"Filtered nodes: {before_node_count} -> {len(points)}")

                # Filter links to only edges where both source and target are in filtered_nodes
                before_edge_count = len(links)
                links = links[
                    (links['source'].isin(filtered_nodes)) &
                    (links['target'].isin(filtered_nodes))
                ].copy()
                logger.info(f"Filtered edges: {before_edge_count} -> {len(links)}")

                # Color seed nodes red and store for later sizing
                for idx, row in points.iterrows():
                    if row['id'] in seed_nodes_set:
                        points.at[idx, 'color'] = '#FF0000'

    # Calculate node sizes
    # points = builder.calculate_node_sizes(points, links)

    # Apply 2x size multiplier to seed nodes
    if seed_nodes_set:
        for idx, row in points.iterrows():
            if row['id'] in seed_nodes_set and row['node_type'] != 'intermediate':
                current_size = row['size']
                new_size = min(current_size * 2.0, MAX_NODE_SIZE)
                points.at[idx, 'size'] = float(new_size)
        logger.info(f"Applied 2x size multiplier to {len(seed_nodes_set)} seed nodes")

    logger.info("Data preparation complete!")
    logger.info(f"  Total nodes: {len(points)} ({sum(points['node_type'] == 'item')} items + {sum(points['node_type'] == 'intermediate')} intermediate)")
    logger.info(f"  Total edges: {len(links)}")

    return points, links, color_config
