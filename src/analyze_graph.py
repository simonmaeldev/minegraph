"""
Graph Analysis Script for Minecraft Transformation Network

This script constructs the Minecraft transformation graph from CSV data and
provides modular metric computation functions. Each metric is encapsulated in
its own function, allowing users to selectively enable/disable metrics by
commenting/uncommenting function calls.

Usage:
    python src/analyze_graph.py                              # All metrics, all transformations
    python src/analyze_graph.py -v                           # Verbose logging
    python src/analyze_graph.py --filter-type=crafting       # Filter by transformation type
    python src/analyze_graph.py --filter-type=crafting,smelting  # Multiple types
    python src/analyze_graph.py -i custom.csv                # Custom CSV file

Available Metrics:
    - Average degree (in-degree and out-degree)
    - Maximum degree (nodes with highest connectivity)
    - Connected components (weakly and strongly connected, with disconnected nodes listed)
    - Edge count (total edges and nodes)
    - Graph density (ratio of actual edges to possible edges)
    - Root nodes (items with no inputs)
    - Leaf nodes (items with no outputs)
    - Betweenness centrality (items that bridge many paths)
    - VoteRank (most important items by voting algorithm)
    - Parent Score (importance propagation to ancestor nodes)
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

import networkx as nx

# Configure NetworkX to use GPU-accelerated cugraph backend (disabled if not available)
# nx.config.backend_priority = ["cugraph"]
# nx.config.warnings_to_ignore.add("cache")

# Import graph building functions from graph utilities
try:
    # Try package-style import first (for pytest and module usage)
    from src.graph_utils import load_transformations_from_csv, build_graph_from_csv
    from src.visualize_graph_3d import load_color_config
except ModuleNotFoundError:
    # Fall back to direct import (for script execution)
    from graph_utils import load_transformations_from_csv, build_graph_from_csv
    from visualize_graph_3d import load_color_config


class AnalysisGraphBuilder:
    """
    Manages construction of NetworkX graphs for analysis purposes.

    Unlike Graph3DBuilder used for visualization, this builder creates direct edges
    from input items to output items without intermediate nodes. This ensures that
    graph metrics accurately reflect item-to-item relationships.

    Key differences from Graph3DBuilder:
    - No intermediate nodes for multi-input transformations
    - Direct edges from each input to each output (A->D, B->D, C->D)
    - Edge deduplication to prevent multiple edges between same nodes
    """

    def __init__(self):
        """Initialize the graph builder."""
        self.graph = nx.DiGraph()
        # Track edges to prevent duplicates: (from, to) -> transformation_type
        self.edge_set = {}

    def add_item_node(self, item_name: str) -> None:
        """
        Add an item node to the graph.

        Args:
            item_name: Name of the item
        """
        if not self.graph.has_node(item_name):
            self.graph.add_node(item_name, node_type='item')

    def add_edge_with_dedup(
        self,
        from_node: str,
        to_node: str,
        transformation_type: str
    ) -> None:
        """
        Add an edge with deduplication to ensure maximum one oriented edge between nodes.

        If an edge already exists between these nodes, keep the existing one.
        This prevents duplicate edges when multiple transformations have the same
        input->output relationship.

        Args:
            from_node: Source node name
            to_node: Target node name
            transformation_type: Type of transformation
        """
        edge_key = (from_node, to_node)

        # Only add edge if it doesn't already exist
        if edge_key not in self.edge_set:
            self.graph.add_edge(from_node, to_node, transformation_type=transformation_type)
            self.edge_set[edge_key] = transformation_type

    def add_transformation(
        self,
        input_items: List[str],
        output_item: str,
        transformation_type: str
    ) -> None:
        """
        Add a transformation creating direct edges from inputs to output.

        For single-input transformations: A -> D
        For multi-input transformations: A -> D, B -> D, C -> D

        No intermediate nodes are created. All edges are deduplicated.

        Args:
            input_items: List of input item names
            output_item: Name of the output item
            transformation_type: Type of transformation
        """
        # Add output node
        self.add_item_node(output_item)

        # Add direct edge from each input to output
        for input_item in input_items:
            self.add_item_node(input_item)
            self.add_edge_with_dedup(input_item, output_item, transformation_type)


def build_analysis_graph_from_csv(
    csv_path: str,
    color_config: Dict[str, str],
    filter_types: Optional[List[str]] = None
) -> nx.DiGraph:
    """
    Build NetworkX graph for analysis from CSV data with optional type filtering.

    This function creates a graph optimized for analysis by creating direct edges
    between items without intermediate nodes. This ensures graph metrics accurately
    reflect item-to-item transformation relationships.

    Args:
        csv_path: Path to transformations CSV file
        color_config: Color configuration dictionary (unused but kept for compatibility)
        filter_types: Optional list of transformation types to include

    Returns:
        NetworkX DiGraph with direct edges and no intermediate nodes
    """
    transformations = load_transformations_from_csv(csv_path, filter_types)
    builder = AnalysisGraphBuilder()

    for trans in transformations:
        trans_type = trans['transformation_type']
        inputs = trans['input_items']
        outputs = trans['output_items']

        # Assume single output (as per data model validation)
        output_item = outputs[0] if outputs else None
        if not output_item:
            logging.warning(f"Skipping transformation with no output: {trans}")
            continue

        # Add transformation with direct edges (works for both single and multi-input)
        builder.add_transformation(inputs, output_item, trans_type)

    # Log statistics
    item_nodes = [n for n in builder.graph.nodes() if builder.graph.nodes[n].get('node_type') == 'item']
    logging.info(f"Analysis graph contains {len(item_nodes)} unique items")
    logging.info(f"Analysis graph contains {builder.graph.number_of_nodes()} total nodes")
    logging.info(f"Analysis graph contains {builder.graph.number_of_edges()} edges")

    return builder.graph


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        Parsed argument namespace
    """
    parser = argparse.ArgumentParser(
        description='Analyze Minecraft transformation graph metrics',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # All metrics, all transformations
  %(prog)s -v                                 # Verbose logging
  %(prog)s --filter-type=crafting             # Filter by transformation type
  %(prog)s --filter-type=crafting,smelting    # Multiple types
  %(prog)s -i custom.csv                      # Custom CSV file
        """
    )

    parser.add_argument(
        '-i', '--input',
        type=str,
        default='output/transformations.csv',
        help='Path to transformations CSV file (default: output/transformations.csv)'
    )

    parser.add_argument(
        '-c', '--config',
        type=str,
        default='config/graph_colors.txt',
        help='Path to color configuration file (default: config/graph_colors.txt)'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    parser.add_argument(
        '--filter-type',
        type=str,
        default=None,
        help='Comma-separated list of transformation types to include (e.g., crafting,smelting)'
    )

    return parser.parse_args()


def load_graph(
    csv_path: str,
    config_path: str,
    filter_types: Optional[List[str]] = None
) -> nx.DiGraph:
    """
    Load and construct the transformation graph from CSV data for analysis.

    This function uses the AnalysisGraphBuilder to create a graph optimized for
    analysis with direct edges and no intermediate nodes. This ensures graph metrics
    accurately reflect item-to-item relationships.

    Args:
        csv_path: Path to the transformations CSV file
        config_path: Path to the color configuration file
        filter_types: Optional list of transformation types to include

    Returns:
        NetworkX directed graph representing transformations

    Raises:
        FileNotFoundError: If CSV file doesn't exist
        ValueError: If CSV file is empty or invalid
    """
    # Check if CSV file exists
    csv_file = Path(csv_path)
    if not csv_file.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    # Load color configuration (kept for compatibility, though not used in analysis)
    color_config = load_color_config(config_path)

    # Build the analysis graph (without intermediate nodes)
    logging.info(f"Loading analysis graph from {csv_path}")
    if filter_types:
        logging.info(f"Filtering by transformation types: {', '.join(filter_types)}")

    graph = build_analysis_graph_from_csv(csv_path, color_config, filter_types)

    if graph.number_of_nodes() == 0:
        raise ValueError("Graph is empty - no nodes loaded from CSV")

    return graph


def print_section_header(title: str) -> None:
    """
    Print a formatted section header for organizing output.

    Args:
        title: Section title to display
    """
    separator = "=" * 60
    print(f"\n{separator}")
    print(f"  {title}")
    print(separator)


def print_metric(label: str, value: Any, unit: str = "") -> None:
    """
    Print a metric in a consistent format.

    Args:
        label: Metric label/name
        value: Metric value (will be formatted based on type)
        unit: Optional unit string (e.g., "nodes", "%")
    """
    if isinstance(value, float):
        value_str = f"{value:.2f}"
    else:
        value_str = str(value)

    if unit:
        print(f"  {label}: {value_str} {unit}")
    else:
        print(f"  {label}: {value_str}")


def analyze_average_degree(graph: nx.DiGraph) -> None:
    """
    Compute and print average in-degree and out-degree.

    For directed graphs, in-degree counts incoming edges and out-degree counts
    outgoing edges. The average is computed as the sum of all degrees divided
    by the number of nodes.

    Args:
        graph: NetworkX directed graph
    """
    print_section_header("Average Degree Analysis")

    num_nodes = graph.number_of_nodes()

    if num_nodes == 0:
        print("  Cannot compute average degree: graph has no nodes")
        return

    # Compute average in-degree
    total_in_degree = sum(degree for _, degree in graph.in_degree())
    avg_in_degree = total_in_degree / num_nodes

    # Compute average out-degree
    total_out_degree = sum(degree for _, degree in graph.out_degree())
    avg_out_degree = total_out_degree / num_nodes

    print_metric("Average in-degree", avg_in_degree)
    print_metric("Average out-degree", avg_out_degree)
    print_metric("Total nodes", num_nodes, "nodes")


def analyze_max_degree(graph: nx.DiGraph) -> None:
    """
    Find and print nodes with maximum in-degree and out-degree.

    This identifies the most connected nodes in the graph, which can represent
    items that are commonly used as inputs (high out-degree) or commonly
    produced as outputs (high in-degree).

    Args:
        graph: NetworkX directed graph
    """
    print_section_header("Maximum Degree Analysis")

    num_nodes = graph.number_of_nodes()

    if num_nodes == 0:
        print("  Cannot compute max degree: graph has no nodes")
        return

    # Find max in-degree
    in_degrees = dict(graph.in_degree())
    max_in_degree = max(in_degrees.values()) if in_degrees else 0
    max_in_nodes = [node for node, deg in in_degrees.items() if deg == max_in_degree]

    # Find max out-degree
    out_degrees = dict(graph.out_degree())
    max_out_degree = max(out_degrees.values()) if out_degrees else 0
    max_out_nodes = [node for node, deg in out_degrees.items() if deg == max_out_degree]

    print_metric("Maximum in-degree", max_in_degree)
    if max_in_nodes:
        # Show up to 5 nodes with max in-degree
        nodes_to_show = max_in_nodes[:5]
        nodes_str = ", ".join(nodes_to_show)
        if len(max_in_nodes) > 5:
            nodes_str += f" ... ({len(max_in_nodes)} total)"
        print(f"  Nodes with max in-degree: {nodes_str}")

    print_metric("Maximum out-degree", max_out_degree)
    if max_out_nodes:
        # Show up to 5 nodes with max out-degree
        nodes_to_show = max_out_nodes[:5]
        nodes_str = ", ".join(nodes_to_show)
        if len(max_out_nodes) > 5:
            nodes_str += f" ... ({len(max_out_nodes)} total)"
        print(f"  Nodes with max out-degree: {nodes_str}")


def analyze_connected_components(graph: nx.DiGraph) -> None:
    """
    Count and print weakly and strongly connected components.

    Weakly connected components are groups of nodes connected when ignoring
    edge direction. Strongly connected components are groups where every node
    can reach every other node following directed edges.

    This function also identifies and displays all nodes that are disconnected
    from the main (largest) component, helping identify isolated items and
    orphaned transformation networks.

    Args:
        graph: NetworkX directed graph
    """
    print_section_header("Connected Components Analysis")

    num_nodes = graph.number_of_nodes()

    if num_nodes == 0:
        print("  Cannot compute components: graph has no nodes")
        return

    # Count weakly connected components
    num_weak = nx.number_weakly_connected_components(graph)

    # Count strongly connected components
    num_strong = nx.number_strongly_connected_components(graph)

    print_metric("Weakly connected components", num_weak)
    print("    (Components connected ignoring edge direction)")

    print_metric("Strongly connected components", num_strong)
    print("    (Components with directed paths between all nodes)")

    # Analyze disconnected components
    # Get all weakly connected components (returned in descending order by size)
    components = list(nx.weakly_connected_components(graph))

    if not components:
        # Empty graph case (already handled above, but being defensive)
        return

    # The first (largest) component is the main component
    main_component = components[0]
    disconnected_components = components[1:] if len(components) > 1 else []

    print()  # Blank line for readability
    print_metric("Main component nodes", len(main_component), "nodes")

    if disconnected_components:
        print_metric("Disconnected components", len(disconnected_components))
        print()  # Blank line before listing components

        total_disconnected = 0
        for i, component in enumerate(disconnected_components, 1):
            component_size = len(component)
            total_disconnected += component_size


            # Sort node names alphabetically for consistent output
            sorted_nodes = sorted(component)

            print(f"  Component {i} ({component_size} nodes):")
            for node in sorted_nodes:
                print(f"    - {node}")
            print()  # Blank line between components


        print_metric("Total disconnected nodes", total_disconnected, "nodes")
    else:
        print("  All nodes are in the main component (no disconnected nodes).")


def analyze_edge_count(graph: nx.DiGraph) -> None:
    """
    Print total node and edge counts for analysis graph.

    Analysis graphs contain only item nodes with direct edges between them.
    No intermediate nodes are used, ensuring metrics reflect true item relationships.

    Args:
        graph: NetworkX directed graph
    """
    print_section_header("Graph Size")

    num_nodes = graph.number_of_nodes()
    num_edges = graph.number_of_edges()

    print_metric("Total nodes", num_nodes, "nodes")
    print_metric("Total edges", num_edges, "edges")

    # Count item nodes (should be all nodes in analysis graph)
    item_nodes = [n for n in graph.nodes() if graph.nodes[n].get('node_type') == 'item']

    print_metric("Item nodes", len(item_nodes), "nodes")
    print("    (Analysis graph uses direct edges without intermediate nodes)")
    print("    (Visualization graphs may include intermediate nodes for clarity)")


def analyze_density(graph: nx.DiGraph) -> None:
    """
    Compute and print graph density.

    Density is the ratio of actual edges to possible edges in the graph.
    For a directed graph with n nodes, the maximum number of edges is n*(n-1).
    Density = m / (n*(n-1)) where m is the number of edges.

    Args:
        graph: NetworkX directed graph
    """
    print_section_header("Graph Density")

    num_nodes = graph.number_of_nodes()

    if num_nodes < 2:
        print("  Cannot compute density: graph needs at least 2 nodes")
        return

    density = nx.density(graph)
    density_percent = density * 100

    print_metric("Density", density)
    print_metric("Density (percentage)", density_percent, "%")
    print(f"    Ratio of actual edges to possible edges in directed graph")
    print(f"    (For {num_nodes} nodes, max possible edges: {num_nodes * (num_nodes - 1)})")


def get_main_component(graph: nx.DiGraph) -> nx.DiGraph:
    """
    Extract the main (largest) weakly connected component from the graph.

    Args:
        graph: NetworkX directed graph

    Returns:
        Subgraph containing only the main connected component
    """
    components = list(nx.weakly_connected_components(graph))
    if not components:
        return nx.DiGraph()

    # The largest component is the main component
    main_component_nodes = max(components, key=len)
    return graph.subgraph(main_component_nodes).copy()


def analyze_root_nodes(graph: nx.DiGraph) -> None:
    """
    Find and print root nodes (nodes with in-degree = 0).

    Root nodes are items that are not produced by any transformation,
    typically representing base materials or resources.

    Args:
        graph: NetworkX directed graph
    """
    print_section_header("Root Nodes Analysis (In-degree = 0)")

    num_nodes = graph.number_of_nodes()

    if num_nodes == 0:
        print("  Cannot compute root nodes: graph has no nodes")
        return

    # Find nodes with in-degree = 0
    root_nodes = [node for node, in_deg in graph.in_degree() if in_deg == 0]

    print_metric("Number of root nodes", len(root_nodes), "nodes")

    if not root_nodes:
        print("  No root nodes found (all nodes have incoming edges)")


def analyze_leaf_nodes(graph: nx.DiGraph) -> None:
    """
    Find and print leaf nodes (nodes with out-degree = 0).

    Leaf nodes are items that are not used as inputs to any transformation,
    typically representing final products or end-game items.

    Args:
        graph: NetworkX directed graph
    """
    print_section_header("Leaf Nodes Analysis (Out-degree = 0)")

    num_nodes = graph.number_of_nodes()

    if num_nodes == 0:
        print("  Cannot compute leaf nodes: graph has no nodes")
        return

    # Find nodes with out-degree = 0
    leaf_nodes = [node for node, out_deg in graph.out_degree() if out_deg == 0]

    print_metric("Number of leaf nodes", len(leaf_nodes), "nodes")

    if not leaf_nodes:
        print("  No leaf nodes found (all nodes have outgoing edges)")


def analyze_betweenness_centrality(graph: nx.DiGraph, top_n: int = 10) -> List[str]:
    """
    Calculate and display betweenness centrality for the graph.

    Betweenness centrality measures how often a node appears on shortest paths
    between other nodes. High betweenness indicates a node is a critical
    bridge in the network.

    Args:
        graph: NetworkX directed graph
        top_n: Number of top nodes to display (default: 10)

    Returns:
        Complete sorted list of item names (highest centrality first)
    """
    print_section_header("Betweenness Centrality Analysis")

    num_nodes = graph.number_of_nodes()

    if num_nodes == 0:
        print("  Cannot compute betweenness centrality: graph has no nodes")
        return []

    if num_nodes < 2:
        print("  Cannot compute betweenness centrality: graph needs at least 2 nodes")
        return []

    print(f"  Computing betweenness centrality for {num_nodes} nodes...")
    print("  (This measures how often a node lies on shortest paths)")

    # Calculate betweenness centrality
    betweenness = nx.betweenness_centrality(graph)

    # Sort nodes by betweenness centrality (descending)
    sorted_nodes = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)

    # Extract just the node names in sorted order
    sorted_node_names = [node for node, _ in sorted_nodes]

    # Display top N nodes
    print(f"\n  Top {min(top_n, len(sorted_nodes))} nodes by betweenness centrality:")
    print()
    for i, (node, centrality) in enumerate(sorted_nodes[:top_n], 1):
        print(f"  {i:2d}. {node:40s} {centrality:.6f}")

    if len(sorted_nodes) > top_n:
        print(f"\n  ... and {len(sorted_nodes) - top_n} more nodes")

    # Return the complete sorted list of node names
    return sorted_node_names


def analyze_eigenvector_centrality(graph: nx.DiGraph, top_n: int = 10) -> None:
    """
    Calculate and display eigenvector centrality for the graph.

    Eigenvector centrality measures a node's influence based on the importance
    of its neighbors. High eigenvector centrality indicates a node is connected
    to other highly connected nodes.

    Args:
        graph: NetworkX directed graph
        top_n: Number of top nodes to display (default: 10)
    """
    print_section_header("Eigenvector Centrality Analysis")

    num_nodes = graph.number_of_nodes()

    if num_nodes == 0:
        print("  Cannot compute eigenvector centrality: graph has no nodes")
        return

    if num_nodes < 2:
        print("  Cannot compute eigenvector centrality: graph needs at least 2 nodes")
        return

    print(f"  Computing eigenvector centrality for {num_nodes} nodes...")
    print("  (This measures influence based on connections to important nodes)")

    try:
        # Calculate eigenvector centrality with increased iterations
        eigenvector = nx.eigenvector_centrality(graph, max_iter=1000)

        # Sort nodes by eigenvector centrality (descending)
        sorted_nodes = sorted(eigenvector.items(), key=lambda x: x[1], reverse=True)

        # Display top N nodes
        print(f"\n  Top {min(top_n, len(sorted_nodes))} nodes by eigenvector centrality:")
        print()
        for i, (node, centrality) in enumerate(sorted_nodes[:top_n], 1):
            print(f"  {i:2d}. {node:40s} {centrality:.6f}")

        if len(sorted_nodes) > top_n:
            print(f"\n  ... and {len(sorted_nodes) - top_n} more nodes")

    except nx.PowerIterationFailedConvergence:
        print("  WARNING: Eigenvector centrality calculation did not converge")
        print("  This can happen with certain graph structures")
    except nx.NetworkXError as e:
        print(f"  ERROR: Could not compute eigenvector centrality: {e}")


def analyze_voterank(graph: nx.DiGraph, top_n: int = 10) -> List[str]:
    """
    Calculate and display voterank for the graph.

    Args:
        graph: NetworkX directed graph
        top_n: Number of top nodes to display (default: 10)

    Returns:
        Complete sorted list of item names (highest ranked first)
    """
    print_section_header("VoteRank Analysis")

    num_nodes = graph.number_of_nodes()

    if num_nodes == 0:
        print("  Cannot compute vote rank: graph has no nodes")
        return []

    if num_nodes < 2:
        print("  Cannot compute vote rank: graph needs at least 2 nodes")
        return []

    print(f"  Computing vote rank for {num_nodes} nodes...")

    try:
        # Calculate vote rank with increased iterations
        voterank = nx.voterank(graph, top_n)

        # Display top N nodes
        print(f"\n  Top {len(voterank)} nodes by voterank:")
        print()
        for i, node in enumerate(voterank[:top_n], 1):
            print(f"  {i:2d}. {node:40s}")

        # Return the complete sorted list
        return voterank

    except nx.NetworkXError as e:
        print(f"  ERROR: Could not compute voterank: {e}")
        return []

def add_score_parents(
    starting_node: str,
    graph: nx.DiGraph,
    to_process: set[str],
    processed: set[str],
    scores: dict[str, float],
    depth: int = 1,
    skip_intermediate: bool = False
) -> None:
    """
    Recursively traverse parent nodes and increment their scores based on depth.

    This function performs a recursive backward traversal through the graph,
    starting from a given node and visiting all ancestor nodes (parents).
    Each visited node gets 1/depth added to its score, where depth starts at 1
    for the starting node. Intermediate nodes (marked with node_type='intermediate')
    are never scored, but can optionally be skipped during traversal.

    The function uses sets to track processed and to-process nodes to prevent
    infinite loops in cyclic graphs.

    Args:
        starting_node: The node to start traversal from
        graph: NetworkX directed graph to traverse
        to_process: Set of nodes that still need to be processed
        processed: Set of nodes that have already been processed
        scores: Dictionary mapping node names to their accumulated scores
        depth: Current depth in traversal (starts at 1)
        skip_intermediate: If True, don't explore through intermediate nodes
                          (default: False, explore through intermediate nodes)

    Returns:
        None (modifies scores, to_process, and processed in-place)
    """
    # Check if this is an intermediate node
    is_intermediate = graph.nodes[starting_node].get('node_type') == 'intermediate'

    # Get all parent nodes (predecessors in directed graph)
    parents = list(graph.predecessors(starting_node))
    non_intermediate_parents = [parent for parent in parents if graph.nodes[parent].get('node_type') != 'intermediate']

    # Only score non-intermediate nodes
    if not is_intermediate and len(non_intermediate_parents)==0:
        if starting_node not in scores:
            scores[starting_node] = 0
        #scores[starting_node] += depth
        #scores[starting_node] += 1 / depth
        scores[starting_node] += 1

    # Add unprocessed parents to the to_process set with incremented depth
    for parent in parents:
        # Skip this parent if:
        # 1. We're skipping intermediate nodes AND this parent is intermediate, OR
        # 2. The parent has already been processed or is in queue
        parent_is_intermediate = graph.nodes[parent].get('node_type') == 'intermediate'
        should_skip = (skip_intermediate and parent_is_intermediate)

        if not should_skip and parent not in processed and parent not in to_process:
            to_process.add((parent, depth + 1))

    # Mark current node as processed
    processed.add(starting_node)

    # Recursively process next node if any remain
    if to_process:
        next_item = to_process.pop()
        # Handle both tuple (node, depth) and string (node) formats
        if isinstance(next_item, tuple):
            next_node, next_depth = next_item
        else:
            next_node = next_item
            next_depth = depth + 1
        add_score_parents(next_node, graph, to_process, processed, scores, next_depth, skip_intermediate)


def analyze_parent_score(
    graph: nx.DiGraph,
    item_list: List[str],
    display_top_n: int = 20,
    skip_intermediate: bool = False
) -> None:
    """
    Analyze parent scores by propagating importance backward through the graph.

    This metric identifies "critical base materials" by computing which items
    appear in the ancestry of many important items. It works by:
    1. Starting with a pre-computed list of important items
    2. For each important item, recursively traversing all parent nodes
    3. Incrementing a score for each parent encountered (non-intermediate nodes only)
    4. Ranking items by their accumulated scores

    High-scoring items are critical base materials that contribute to many
    important end products. This complements other ranking metrics, which identify
    important end products but don't show which base materials are needed.

    Note: Intermediate nodes are never scored, and can optionally be skipped
    during traversal using the skip_intermediate flag.

    Args:
        graph: NetworkX directed graph to analyze
        item_list: List of items to use as importance sources (pre-computed list)
        display_top_n: Number of top parent score items to display
        skip_intermediate: If True, don't traverse through intermediate nodes
                          (default: False, traverse through them)

    Returns:
        None (prints analysis to console)
    """
    print_section_header("Parent Score Analysis (Importance Propagation)")

    num_nodes = graph.number_of_nodes()

    if num_nodes < 2:
        print("  Cannot compute parent score: graph needs at least 2 nodes")
        return

    if not item_list:
        print("  Cannot compute parent score: item_list is empty")
        return

    print(f"  Computing parent scores for {num_nodes} nodes...")
    print(f"  Using {len(item_list)} pre-computed items as importance sources...")
    if skip_intermediate:
        print("  (Skipping traversal through intermediate nodes)")

    try:
        # Initialize scores dictionary (now uses float for depth-based scoring)
        scores: dict[str, float] = {}

        # Process each item from the provided list
        for item in item_list:
            # Initialize processing set with the starting item at depth 1
            to_process: set = {(item, 1)}
            processed: set[str] = set()

            # Process all parents of this item
            while to_process:
                next_item = to_process.pop()
                next_node, next_depth = next_item
                add_score_parents(next_node, graph, to_process, processed, scores, next_depth, skip_intermediate)

        # Sort items by score (descending)
        sorted_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        # Display top N items
        print(f"\n  Top {min(display_top_n, len(sorted_items))} items by parent score:")
        print("  (Items that appear in the ancestry of many important items)")
        print()

        for i, (node, score) in enumerate(sorted_items[:display_top_n], 1):
            print(f"  {i:2d}. {node:40s} (score: {score})")

    except nx.NetworkXError as e:
        print(f"  ERROR: Could not compute parent score: {e}")


def main() -> int:
    """
    Main execution function.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    # Parse arguments
    args = parse_arguments()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    try:
        # Parse filter types if provided
        filter_types = None
        if args.filter_type:
            filter_types = [t.strip() for t in args.filter_type.split(',')]

        # Load color configuration
        color_config = load_color_config(args.config)

        # Create two graphs: one without intermediate nodes and one with intermediate nodes
        graph_without_intermediate = build_analysis_graph_from_csv(args.input, color_config, filter_types)
        graph_with_intermediate = build_graph_from_csv(args.input, color_config, filter_types)

        print("\n" + "=" * 60)
        print("  MINECRAFT TRANSFORMATION GRAPH ANALYSIS")
        print("=" * 60)
        print(f"\nData source: {args.input}")
        if filter_types:
            print(f"Filtered by: {', '.join(filter_types)}")

        # ============================================================
        # GLOBAL ANALYSIS (Full Graph)
        # ============================================================
        print("\n" + "=" * 60)
        print("  GLOBAL ANALYSIS (Full Graph)")
        print("=" * 60)

        analyze_average_degree(graph_without_intermediate)
        analyze_max_degree(graph_without_intermediate)
        analyze_connected_components(graph_without_intermediate)
        analyze_edge_count(graph_without_intermediate)
        analyze_density(graph_without_intermediate)

        # ============================================================
        # MAIN COMPONENT ANALYSIS
        # ============================================================
        print("\n" + "=" * 60)
        print("  MAIN COMPONENT ANALYSIS")
        print("=" * 60)

        # Extract main components for both graph versions
        main_component_without = get_main_component(graph_without_intermediate)
        main_component_with = get_main_component(graph_with_intermediate)

        print(f"\nMain component (without intermediate nodes) contains {main_component_without.number_of_nodes()} nodes "
              f"and {main_component_without.number_of_edges()} edges")
        print(f"Main component (with intermediate nodes) contains {main_component_with.number_of_nodes()} nodes "
              f"and {main_component_with.number_of_edges()} edges")

        # Run focused analysis on main component (using graph without intermediate nodes for most metrics)
        analyze_root_nodes(main_component_without)
        analyze_leaf_nodes(main_component_without)
        betweenness_items = analyze_betweenness_centrality(main_component_without, top_n=10)
        #analyze_eigenvector_centrality(main_component_without, top_n=10)
        voterank_items = analyze_voterank(main_component_without, top_n=20)

        # Use pre-computed list for parent score with graph containing intermediate nodes
        analyze_parent_score(main_component_with, voterank_items[:20], display_top_n=20, skip_intermediate=True)
        #scores = {}
        #add_score_parents("Redstone Dust", graph, set(), set(), scores)
        #print(scores)
        res = sorted(nx.strongly_connected_components(main_component_without), key=len, reverse=True)

        for s in res : 
            if len(s) > 1:
                print(f"{len(s)}: {s}")

        # ============================================================

        print("\n" + "=" * 60)
        print("  Analysis complete!")
        print("=" * 60 + "\n")

        return 0

    except FileNotFoundError as e:
        logging.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logging.error(f"Invalid data: {e}")
        return 1
    except Exception as e:
        logging.error(f"Unexpected error: {e}", exc_info=args.verbose)
        return 1


if __name__ == "__main__":
    sys.exit(main())
