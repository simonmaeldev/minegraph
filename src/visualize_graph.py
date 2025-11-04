"""Generate Graphviz visualization of Minecraft transformation graphs."""

import argparse
import csv
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set

import graphviz


# Default color mappings if config file is missing or incomplete
DEFAULT_COLORS = {
    "crafting": "#4A90E2",
    "smelting": "#E67E22",
    "blast_furnace": "#E67E22",  # Same as smelting
    "smoker": "#E67E22",  # Same as smelting
    "smithing": "#95A5A6",
    "stonecutter": "#7F8C8D",
    "trading": "#F39C12",
    "mob_drop": "#E74C3C",
    "brewing": "#9B59B6",
    "composting": "#27AE60",
    "grindstone": "#34495E",
}


def load_color_config(config_path: str) -> Dict[str, str]:
    """
    Load color configuration from file.

    Args:
        config_path: Path to the color configuration file

    Returns:
        Dictionary mapping transformation types to color codes
    """
    colors = DEFAULT_COLORS.copy()

    config_file = Path(config_path)
    if not config_file.exists():
        logging.warning(f"Config file not found at {config_path}, using default colors")
        return colors

    try:
        with open(config_file, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue

                # Parse key=value format
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    if key and value:
                        colors[key] = value

        logging.info(f"Loaded {len(colors)} color mappings from {config_path}")
    except Exception as e:
        logging.error(f"Error loading config file: {e}, using default colors")

    return colors


def load_transformations_from_csv(csv_path: str) -> List[Dict]:
    """
    Load transformations from CSV file.

    Args:
        csv_path: Path to the transformations CSV file

    Returns:
        List of transformation dictionaries with parsed data
    """
    transformations = []

    csv_file = Path(csv_path)
    if not csv_file.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parse JSON arrays in input_items and output_items
            try:
                inputs = json.loads(row['input_items'])
                outputs = json.loads(row['output_items'])
                metadata = json.loads(row['metadata'])

                transformation = {
                    'transformation_type': row['transformation_type'],
                    'input_items': inputs,
                    'output_items': outputs,
                    'metadata': metadata
                }
                transformations.append(transformation)
            except (json.JSONDecodeError, KeyError) as e:
                logging.warning(f"Skipping malformed row: {e}")
                continue

    logging.info(f"Loaded {len(transformations)} transformations from {csv_path}")
    return transformations


class TransformationGraphBuilder:
    """Manages construction of transformation graphs using Graphviz."""

    def __init__(self):
        """Initialize the graph builder."""
        self.graph = graphviz.Digraph(
            comment='Minecraft Transformations',
            engine='dot',
            format='svg'
        )

        # Set graph attributes for left-to-right layout
        self.graph.attr(rankdir='LR')
        self.graph.attr('node', shape='circle')
        self.graph.attr('edge', arrowhead='normal')

        # Track created nodes to avoid duplicates
        self.item_nodes: Set[str] = set()
        self.intermediate_counter = 0

    def add_item_node(self, item_name: str) -> None:
        """
        Add an item node to the graph.

        Args:
            item_name: Name of the item
        """
        if item_name not in self.item_nodes:
            self.graph.node(item_name, label=item_name, shape='circle')
            self.item_nodes.add(item_name)

    def create_intermediate_node(self) -> str:
        """
        Create a unique intermediate node for multi-input transformations.

        Returns:
            Unique identifier for the intermediate node
        """
        node_id = f"intermediate_{self.intermediate_counter}"
        self.intermediate_counter += 1

        # Style as small dot
        self.graph.node(node_id, label='', shape='point', width='0.1')
        return node_id

    def add_single_input_transformation(
        self,
        input_item: str,
        output_item: str,
        color: str
    ) -> None:
        """
        Add a single-input transformation edge.

        Args:
            input_item: Name of the input item
            output_item: Name of the output item
            color: Color for the edge
        """
        self.add_item_node(input_item)
        self.add_item_node(output_item)
        self.graph.edge(input_item, output_item, color=color)

    def add_multi_input_transformation(
        self,
        input_items: List[str],
        output_item: str,
        color: str
    ) -> None:
        """
        Add a multi-input transformation with intermediate node.

        Args:
            input_items: List of input item names
            output_item: Name of the output item
            color: Color for the edges
        """
        # Create intermediate node
        intermediate = self.create_intermediate_node()

        # Add edges from all inputs to intermediate
        for input_item in input_items:
            self.add_item_node(input_item)
            self.graph.edge(input_item, intermediate, color=color)

        # Add edge from intermediate to output
        self.add_item_node(output_item)
        self.graph.edge(intermediate, output_item, color=color)

    def render(self, output_path: str, formats: List[str]) -> List[str]:
        """
        Render the graph to files.

        Args:
            output_path: Output file path without extension
            formats: List of output formats (svg, png, pdf, dot)

        Returns:
            List of created file paths
        """
        created_files = []

        for fmt in formats:
            self.graph.format = fmt
            output_file = self.graph.render(
                filename=output_path,
                cleanup=True  # Remove the intermediate .dot file
            )
            created_files.append(output_file)
            logging.info(f"Generated graph: {output_file}")

        return created_files


def generate_graph(
    csv_path: str,
    config_path: str,
    output_path: str,
    formats: List[str],
    filter_type: Optional[str] = None
) -> List[str]:
    """
    Generate transformation graph from CSV data.

    Args:
        csv_path: Path to transformations CSV file
        config_path: Path to color configuration file
        output_path: Output file path without extension
        formats: List of output formats
        filter_type: Optional transformation type to filter by

    Returns:
        List of created file paths
    """
    # Load configuration and data
    colors = load_color_config(config_path)
    transformations = load_transformations_from_csv(csv_path)

    # Filter by transformation type if specified
    if filter_type:
        transformations = [
            t for t in transformations
            if t['transformation_type'] == filter_type
        ]
        logging.info(f"Filtered to {len(transformations)} {filter_type} transformations")

    # Build graph
    builder = TransformationGraphBuilder()

    for trans in transformations:
        trans_type = trans['transformation_type']
        inputs = trans['input_items']
        outputs = trans['output_items']

        # Get color for this transformation type
        color = colors.get(trans_type, "#000000")  # Default to black

        # Assume single output (as per data model validation)
        output_item = outputs[0] if outputs else None
        if not output_item:
            logging.warning(f"Skipping transformation with no output: {trans}")
            continue

        # Add transformation based on number of inputs
        if len(inputs) == 1:
            builder.add_single_input_transformation(inputs[0], output_item, color)
        else:
            builder.add_multi_input_transformation(inputs, output_item, color)

    # Create output directory if it doesn't exist
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Render graph
    created_files = builder.render(output_path, formats)

    # Log statistics
    logging.info(f"Graph contains {len(builder.item_nodes)} unique items")
    logging.info(f"Graph contains {builder.intermediate_counter} multi-input transformations")

    return created_files


def main():
    """Main entry point for the visualization script."""
    parser = argparse.ArgumentParser(
        description="Generate Graphviz visualization of Minecraft transformation graphs"
    )

    parser.add_argument(
        '-i', '--input',
        default='output/transformations.csv',
        help='Path to transformations CSV file (default: output/transformations.csv)'
    )

    parser.add_argument(
        '-c', '--config',
        default='config/graph_colors.txt',
        help='Path to color configuration file (default: config/graph_colors.txt)'
    )

    parser.add_argument(
        '-o', '--output',
        default='output/graphs/transformation_graph',
        help='Output file path without extension (default: output/graphs/transformation_graph)'
    )

    parser.add_argument(
        '-f', '--format',
        default='svg',
        help='Output format(s) - comma-separated: svg, png, pdf, dot (default: svg)'
    )

    parser.add_argument(
        '-t', '--filter-type',
        help='Filter to only include specific transformation type'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(levelname)s: %(message)s'
    )

    # Parse formats
    formats = [fmt.strip() for fmt in args.format.split(',')]

    try:
        created_files = generate_graph(
            csv_path=args.input,
            config_path=args.config,
            output_path=args.output,
            formats=formats,
            filter_type=args.filter_type
        )

        print(f"Successfully generated {len(created_files)} graph file(s):")
        for file in created_files:
            print(f"  - {file}")

    except Exception as e:
        logging.error(f"Failed to generate graph: {e}")
        raise


if __name__ == '__main__':
    main()
