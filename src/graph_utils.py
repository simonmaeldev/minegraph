"""Reusable graph building utilities for Minecraft transformation networks.

This module provides utilities for building and manipulating NetworkX graphs
from Minecraft transformation data, supporting both full graph construction
and focused subgraph extraction for analysis and visualization.
"""

import csv
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set

import networkx as nx


class Graph3DBuilder:
    """Manages construction of NetworkX graphs for 3D visualization.

    This builder creates intermediate nodes for multi-input transformations,
    which makes the graph structure clearer in visualizations. Each multi-input
    transformation is represented as: inputs → intermediate_node → output.
    """

    def __init__(self):
        """Initialize the graph builder."""
        self.graph = nx.DiGraph()
        self.intermediate_counter = 0

    def add_item_node(self, item_name: str) -> None:
        """
        Add an item node to the graph.

        Args:
            item_name: Name of the item
        """
        if not self.graph.has_node(item_name):
            self.graph.add_node(item_name, node_type='item')

    def create_intermediate_node(self, input_items: List[str] = None, output_item: str = None) -> str:
        """
        Create a unique intermediate node for multi-input transformations.

        Args:
            input_items: Optional list of input item names
            output_item: Optional output item name

        Returns:
            Unique identifier for the intermediate node
        """
        node_id = f"intermediate_{self.intermediate_counter}"

        # Create a descriptive label if input/output information is provided
        if input_items and output_item:
            inputs_str = "+".join(input_items)
            label = f"intermediate_node|{inputs_str}={output_item}"
        else:
            label = ""

        self.intermediate_counter += 1
        self.graph.add_node(node_id, node_type='intermediate', label=label)
        return node_id

    def add_edge(self, from_node: str, to_node: str, transformation_type: str) -> None:
        """
        Add an edge with transformation type metadata.

        Args:
            from_node: Source node name
            to_node: Target node name
            transformation_type: Type of transformation
        """
        self.graph.add_edge(from_node, to_node, transformation_type=transformation_type)

    def add_single_input_transformation(
        self,
        input_item: str,
        output_item: str,
        transformation_type: str
    ) -> None:
        """
        Add a single-input transformation edge.

        Args:
            input_item: Name of the input item
            output_item: Name of the output item
            transformation_type: Type of transformation
        """
        self.add_item_node(input_item)
        self.add_item_node(output_item)
        self.add_edge(input_item, output_item, transformation_type)

    def add_multi_input_transformation(
        self,
        input_items: List[str],
        output_item: str,
        transformation_type: str
    ) -> None:
        """
        Add a multi-input transformation with intermediate node.

        Args:
            input_items: List of input item names
            output_item: Name of the output item
            transformation_type: Type of transformation
        """
        # Create intermediate node with input/output information
        intermediate = self.create_intermediate_node(input_items, output_item)

        # Add edges from all inputs to intermediate
        for input_item in input_items:
            self.add_item_node(input_item)
            self.add_edge(input_item, intermediate, transformation_type)

        # Add edge from intermediate to output
        self.add_item_node(output_item)
        self.add_edge(intermediate, output_item, transformation_type)


def load_transformations_from_csv(
    csv_path: str,
    filter_types: Optional[List[str]] = None
) -> List[Dict]:
    """
    Load transformations from CSV file with optional type filtering.

    Args:
        csv_path: Path to the transformations CSV file
        filter_types: Optional list of transformation types to include (None = all types)

    Returns:
        List of transformation dictionaries with parsed data
    """
    transformations = []
    total_count = 0
    filtered_count = 0

    csv_file = Path(csv_path)
    if not csv_file.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    # Convert filter_types to set for faster lookup
    filter_set = set(filter_types) if filter_types else None

    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parse JSON arrays in input_items and output_items
            try:
                total_count += 1
                trans_type = row['transformation_type']

                # Apply type filtering if specified
                if filter_set is not None and trans_type not in filter_set:
                    filtered_count += 1
                    continue

                inputs = json.loads(row['input_items'])
                outputs = json.loads(row['output_items'])
                metadata = json.loads(row['metadata'])

                transformation = {
                    'transformation_type': trans_type,
                    'input_items': inputs,
                    'output_items': outputs,
                    'metadata': metadata
                }
                transformations.append(transformation)
            except (json.JSONDecodeError, KeyError) as e:
                logging.warning(f"Skipping malformed row: {e}")
                continue

    if filter_types:
        logging.info(
            f"Loaded {len(transformations)} transformations from {csv_path} "
            f"(filtered out {filtered_count} of {total_count} total)"
        )
    else:
        logging.info(f"Loaded {len(transformations)} transformations from {csv_path}")

    return transformations


def build_graph_from_csv(
    csv_path: str,
    color_config: Optional[Dict[str, str]] = None,
    filter_types: Optional[List[str]] = None
) -> nx.DiGraph:
    """
    Build NetworkX graph from CSV data with optional type filtering.

    Args:
        csv_path: Path to transformations CSV file
        color_config: Optional color configuration dictionary (unused, kept for backward compatibility)
        filter_types: Optional list of transformation types to include

    Returns:
        NetworkX DiGraph with all transformations
    """
    transformations = load_transformations_from_csv(csv_path, filter_types)
    builder = Graph3DBuilder()

    for trans in transformations:
        trans_type = trans['transformation_type']
        inputs = trans['input_items']
        outputs = trans['output_items']

        # Assume single output (as per data model validation)
        output_item = outputs[0] if outputs else None
        if not output_item:
            logging.warning(f"Skipping transformation with no output: {trans}")
            continue

        # Add transformation based on number of inputs
        if len(inputs) == 1:
            builder.add_single_input_transformation(inputs[0], output_item, trans_type)
        else:
            builder.add_multi_input_transformation(inputs, output_item, trans_type)

    # Log statistics
    item_nodes = [n for n in builder.graph.nodes() if builder.graph.nodes[n].get('node_type') == 'item']
    logging.info(f"Graph contains {len(item_nodes)} unique items")
    logging.info(f"Graph contains {builder.intermediate_counter} multi-input transformations")
    logging.info(f"Graph contains {builder.graph.number_of_nodes()} total nodes")
    logging.info(f"Graph contains {builder.graph.number_of_edges()} edges")

    return builder.graph


def get_visual_subgraph_rec(
    node_name: str,
    transformations: List[Dict],
    processed: Set[str],
    to_process: Set[str],
    graph: nx.DiGraph,
    str_to_node: Dict[str, str],
    builder: Graph3DBuilder
) -> None:
    """
    Recursively extract forward-directed subgraph from a starting node.

    This helper function traverses transformations where node_name appears as an input,
    following only forward edges (outputs). For multi-input transformations, other
    required inputs are included for context but not explored backward.

    Args:
        node_name: Current node being processed
        transformations: List of all transformation dictionaries
        processed: Set of nodes already processed (prevents cycles)
        to_process: Set of nodes to process in next recursion
        graph: NetworkX graph being built
        str_to_node: Mapping from item names to node IDs
        builder: Graph3DBuilder instance for adding nodes/edges
    """
    # Base case: already processed this node
    if node_name in processed:
        return

    # Mark as processed
    processed.add(node_name)

    # Find all transformations where this node is an input
    for trans in transformations:
        trans_type = trans['transformation_type']
        input_items = trans['input_items']
        output_items = trans['output_items']

        # Extract input and output item names
        # Handle both string arrays and dict arrays (with 'name' field)
        if input_items and isinstance(input_items[0], dict):
            input_names = [item['name'] for item in input_items]
        else:
            input_names = input_items

        # Only process if this node is one of the inputs
        if node_name not in input_names:
            continue

        # Get output item name (single output per transformation)
        if output_items:
            if isinstance(output_items[0], dict):
                output_item = output_items[0]['name']
            else:
                output_item = output_items[0]
        else:
            output_item = None

        if not output_item:
            logging.warning(f"Skipping transformation with no output: {trans}")
            continue

        # Get or create output node
        if output_item in str_to_node:
            # Already exists, use existing node
            output_node = str_to_node[output_item]
        else:
            # Create new node and mark for processing
            output_node = output_item
            str_to_node[output_item] = output_node
            to_process.add(output_item)

        # Add transformation to graph
        if len(input_names) == 1:
            # Single input transformation
            builder.add_single_input_transformation(
                input_names[0],
                output_item,
                trans_type
            )
        else:
            # Multi-input transformation
            # Add all input nodes (for context) but only explore forward from current node
            for input_name in input_names:
                if input_name not in str_to_node:
                    str_to_node[input_name] = input_name
                    # Don't add to to_process - we only explore forward from starting node

            builder.add_multi_input_transformation(
                input_names,
                output_item,
                trans_type
            )


def get_visual_subgraph(
    node_name: str,
    csv_path: str = "output/transformations.csv",
    filter_types: Optional[List[str]] = None
) -> nx.DiGraph:
    """
    Extract forward-directed subgraph starting from a specific node.

    This function creates a subgraph containing all items that can be produced
    (directly or indirectly) from the starting node. It follows only outgoing
    edges (transformations where the node is an INPUT), showing "what can be
    made from this item" rather than "what can make this item".

    For multi-input transformations, all required input items are included in
    the graph for context, but only the starting node's forward path is explored.
    This prevents backward exploration while maintaining full context for each
    transformation.

    Example:
        If you have: [Oak Planks, Stick] → Wooden Pickaxe → Mining
        Starting from "Oak Planks" will include:
        - Oak Planks (starting node)
        - Stick (contextual input, not explored backward)
        - Wooden Pickaxe (forward output, explored recursively)
        - Any items craftable from Wooden Pickaxe

    Args:
        node_name: Name of the starting item node
        csv_path: Path to transformations CSV file
        filter_types: Optional list of transformation types to include

    Returns:
        NetworkX DiGraph containing the forward subgraph

    Raises:
        FileNotFoundError: If CSV file doesn't exist
    """
    # Load transformations from CSV
    transformations = load_transformations_from_csv(csv_path, filter_types)

    # Initialize data structures
    processed: Set[str] = set()
    to_process: Set[str] = {node_name}
    str_to_node: Dict[str, str] = {}
    builder = Graph3DBuilder()

    # Add starting node to graph
    builder.add_item_node(node_name)
    str_to_node[node_name] = node_name

    # Process nodes iteratively
    while to_process:
        # Get next node to process
        current_node = to_process.pop()

        # Recursively process this node
        get_visual_subgraph_rec(
            current_node,
            transformations,
            processed,
            to_process,
            builder.graph,
            str_to_node,
            builder
        )

    # Log statistics
    item_nodes = [n for n in builder.graph.nodes() if builder.graph.nodes[n].get('node_type') == 'item']
    logging.info(f"Subgraph from '{node_name}' contains {len(item_nodes)} unique items")
    logging.info(f"Subgraph contains {builder.intermediate_counter} multi-input transformations")
    logging.info(f"Subgraph contains {builder.graph.number_of_nodes()} total nodes")
    logging.info(f"Subgraph contains {builder.graph.number_of_edges()} edges")

    return builder.graph
