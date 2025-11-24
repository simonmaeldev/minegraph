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
    - Connected components (weakly and strongly connected)
    - Edge count (total edges and nodes)
    - Graph density (ratio of actual edges to possible edges)
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

import networkx as nx

# Import graph building functions from existing visualization script
from visualize_graph_3d import (
    load_transformations_from_csv,
    load_color_config
)


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

        # Load the graph
        graph = load_graph(args.input, args.config, filter_types)

        print("\n" + "=" * 60)
        print("  MINECRAFT TRANSFORMATION GRAPH ANALYSIS")
        print("=" * 60)
        print(f"\nData source: {args.input}")
        if filter_types:
            print(f"Filtered by: {', '.join(filter_types)}")

        # ============================================================
        # METRIC SELECTION: Comment/uncomment metrics to run
        # ============================================================
        # Uncomment the metrics you want to compute:

        analyze_average_degree(graph)
        analyze_max_degree(graph)
        analyze_connected_components(graph)
        analyze_edge_count(graph)
        analyze_density(graph)

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
