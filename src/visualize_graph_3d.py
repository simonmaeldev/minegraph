"""Generate interactive 3D visualization of Minecraft transformation graphs using NetworkX and Matplotlib."""

import argparse
import csv
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import networkx as nx
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


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


def standardize_filename(item_name: str) -> str:
    """
    Convert item name to standardized filename format.

    Args:
        item_name: Original item name (e.g., "Iron Ingot")

    Returns:
        Standardized filename (e.g., "iron_ingot.png")
    """
    import re
    # Convert to lowercase and replace spaces with underscores
    filename = item_name.lower().replace(" ", "_")
    # Remove special characters that might cause issues
    filename = "".join(c for c in filename if c.isalnum() or c == "_")
    # Collapse multiple underscores into one
    filename = re.sub(r"_+", "_", filename)
    return f"{filename}.png"


def load_item_image(
    item_name: str,
    images_dir: str,
    image_cache: Dict[str, Optional[np.ndarray]]
) -> Optional[np.ndarray]:
    """
    Load an item image from disk with caching.

    Args:
        item_name: Name of the item
        images_dir: Directory containing images
        image_cache: Dictionary to cache loaded images

    Returns:
        Image array if found, None otherwise
    """
    # Check cache first
    if item_name in image_cache:
        return image_cache[item_name]

    # Generate standardized filename
    filename = standardize_filename(item_name)
    image_path = Path(images_dir) / filename

    # Try to load the image
    try:
        if image_path.exists():
            img = mpimg.imread(str(image_path))
            image_cache[item_name] = img
            logging.debug(f"Loaded image for {item_name}: {image_path}")
            return img
        else:
            logging.debug(f"No image found for {item_name}: {image_path}")
            image_cache[item_name] = None
            return None
    except Exception as e:
        logging.warning(f"Failed to load image for {item_name}: {e}")
        image_cache[item_name] = None
        return None


def create_image_plane(
    ax: Axes3D,
    image: np.ndarray,
    center: Tuple[float, float, float],
    size: float,
    camera_pos: Optional[Tuple[float, float, float]] = None
) -> None:
    """
    Create a billboard-style image plane in 3D space that faces the camera.

    Args:
        ax: Matplotlib 3D axes
        image: Image array to display
        center: (x, y, z) center position
        size: Size of the plane (width/height)
        camera_pos: Optional camera position for billboard effect
    """
    x, y, z = center

    # Scale size to match visual appearance of scatter points
    # Scatter points use area (s), so we need to scale accordingly
    scale = np.sqrt(size) / 20  # Empirical scaling factor

    # Create a simple square plane facing forward
    # We'll create vertices for a square in the XY plane
    half_size = scale / 2

    # Define the four corners of the plane (facing +Z initially)
    verts = [
        [x - half_size, y - half_size, z],
        [x + half_size, y - half_size, z],
        [x + half_size, y + half_size, z],
        [x - half_size, y + half_size, z]
    ]

    # Create the polygon
    poly = Poly3DCollection([verts], alpha=1.0)

    # Set the image as texture
    # For matplotlib 3D, we'll use facecolors instead of texture mapping
    # We'll approximate by sampling the center color of the image
    # For a better effect, we could use the average color or center pixel

    # Extract a representative color from the image center
    h, w = image.shape[:2]
    if len(image.shape) == 3:
        # RGB or RGBA image
        center_color = image[h // 2, w // 2, :]
    else:
        # Grayscale image
        center_color = [image[h // 2, w // 2]] * 3

    poly.set_facecolor(center_color)
    poly.set_edgecolor('black')
    poly.set_linewidth(0.5)

    ax.add_collection3d(poly)


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


class Graph3DBuilder:
    """Manages construction of NetworkX graphs for 3D visualization."""

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

    def create_intermediate_node(self) -> str:
        """
        Create a unique intermediate node for multi-input transformations.

        Returns:
            Unique identifier for the intermediate node
        """
        node_id = f"intermediate_{self.intermediate_counter}"
        self.intermediate_counter += 1
        self.graph.add_node(node_id, node_type='intermediate')
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
        # Create intermediate node
        intermediate = self.create_intermediate_node()

        # Add edges from all inputs to intermediate
        for input_item in input_items:
            self.add_item_node(input_item)
            self.add_edge(input_item, intermediate, transformation_type)

        # Add edge from intermediate to output
        self.add_item_node(output_item)
        self.add_edge(intermediate, output_item, transformation_type)


def build_graph_from_csv(csv_path: str, color_config: Dict[str, str]) -> nx.DiGraph:
    """
    Build NetworkX graph from CSV data.

    Args:
        csv_path: Path to transformations CSV file
        color_config: Color configuration dictionary

    Returns:
        NetworkX DiGraph with all transformations
    """
    transformations = load_transformations_from_csv(csv_path)
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


def compute_3d_layout(graph: nx.DiGraph) -> Dict[str, Tuple[float, float, float]]:
    """
    Compute 3D positions for graph nodes using spring layout.

    Args:
        graph: NetworkX DiGraph

    Returns:
        Dictionary mapping node names to (x, y, z) coordinates
    """
    num_nodes = graph.number_of_nodes()

    if num_nodes == 0:
        return {}

    # Use spring layout for 3D positioning
    # Spring layout is force-directed and works reliably for all graph sizes
    pos = nx.spring_layout(graph, dim=3, seed=42)
    logging.info("Using spring layout for 3D positioning")

    return pos


def calculate_node_sizes(graph: nx.DiGraph, pos: Dict) -> Dict[str, float]:
    """
    Calculate node sizes based on degree centrality.

    Args:
        graph: NetworkX DiGraph
        pos: Node positions dictionary

    Returns:
        Dictionary mapping node names to size values
    """
    node_sizes = {}

    # Calculate degree centrality
    if graph.number_of_nodes() > 1:
        centrality = nx.degree_centrality(graph)
    else:
        centrality = {n: 1.0 for n in graph.nodes()}

    for node in graph.nodes():
        node_type = graph.nodes[node].get('node_type', 'item')

        if node_type == 'intermediate':
            # Small size for intermediate nodes
            node_sizes[node] = 15
        else:
            # Size based on degree centrality for item nodes
            # Map centrality (0.0-1.0) to size range (50-500)
            cent = centrality.get(node, 0.0)
            size = 50 + (cent * 450)
            node_sizes[node] = size

    return node_sizes


def get_edge_colors(graph: nx.DiGraph, color_config: Dict[str, str]) -> List[str]:
    """
    Get edge colors based on transformation types.

    Args:
        graph: NetworkX DiGraph
        color_config: Color configuration dictionary

    Returns:
        List of colors in same order as graph.edges()
    """
    edge_colors = []

    for u, v in graph.edges():
        trans_type = graph.edges[u, v].get('transformation_type', 'unknown')
        color = color_config.get(trans_type, '#000000')  # Default to black
        edge_colors.append(color)

    return edge_colors


def render_3d_graph(
    graph: nx.DiGraph,
    pos: Dict[str, Tuple[float, float, float]],
    node_sizes: Dict[str, float],
    edge_colors: List[str],
    color_config: Dict[str, str],
    use_images: bool = False,
    images_dir: str = "images"
) -> None:
    """
    Render the 3D graph using Matplotlib with hover annotations.

    Args:
        graph: NetworkX DiGraph
        pos: Node positions dictionary
        node_sizes: Node sizes dictionary
        edge_colors: List of edge colors
        color_config: Color configuration dictionary
        use_images: Whether to use item images instead of spheres
        images_dir: Directory containing item images
    """
    fig = plt.figure(figsize=(16, 12))
    ax = fig.add_subplot(111, projection='3d')

    # Extract 3D coordinates
    nodes = list(graph.nodes())
    xs = [pos[node][0] for node in nodes]
    ys = [pos[node][1] for node in nodes]
    zs = [pos[node][2] for node in nodes]

    # Separate item nodes from intermediate nodes for different rendering
    item_nodes = [n for n in nodes if graph.nodes[n].get('node_type') == 'item']
    intermediate_nodes = [n for n in nodes if graph.nodes[n].get('node_type') == 'intermediate']

    # Plot edges
    for idx, (u, v) in enumerate(graph.edges()):
        x_line = [pos[u][0], pos[v][0]]
        y_line = [pos[u][1], pos[v][1]]
        z_line = [pos[u][2], pos[v][2]]
        ax.plot(x_line, y_line, z_line, color=edge_colors[idx], alpha=0.4, linewidth=0.5)

    # Initialize image cache
    image_cache: Dict[str, Optional[np.ndarray]] = {}

    # Plot item nodes (larger, colored or with images)
    item_scatter = None
    items_with_images = []
    items_without_images = []

    if use_images and item_nodes:
        # Try to load images for each item
        for node in item_nodes:
            img = load_item_image(node, images_dir, image_cache)
            if img is not None:
                items_with_images.append(node)
            else:
                items_without_images.append(node)

        # Render items with images as planes
        for node in items_with_images:
            img = image_cache[node]
            create_image_plane(
                ax,
                img,
                pos[node],
                node_sizes[node]
            )

        logging.info(f"Rendered {len(items_with_images)} items with images")

        # Render items without images as spheres (fallback)
        if items_without_images:
            fallback_xs = [pos[node][0] for node in items_without_images]
            fallback_ys = [pos[node][1] for node in items_without_images]
            fallback_zs = [pos[node][2] for node in items_without_images]
            fallback_sizes = [node_sizes[node] for node in items_without_images]

            ax.scatter(
                fallback_xs, fallback_ys, fallback_zs,
                s=fallback_sizes,
                c='#3498db',  # Blue color for fallback nodes
                alpha=0.7,
                edgecolors='black',
                linewidths=0.5,
                depthshade=True
            )
            logging.info(f"Rendered {len(items_without_images)} items as spheres (no image)")

        # For hover functionality, we need a scatter plot with all item positions
        if item_nodes:
            item_xs = [pos[node][0] for node in item_nodes]
            item_ys = [pos[node][1] for node in item_nodes]
            item_zs = [pos[node][2] for node in item_nodes]
            item_sizes_list = [node_sizes[node] for node in item_nodes]

            # Invisible scatter plot for hover detection
            item_scatter = ax.scatter(
                item_xs, item_ys, item_zs,
                s=item_sizes_list,
                c='none',  # Transparent
                alpha=0.0,
                edgecolors='none',
                depthshade=False
            )

    else:
        # Original sphere rendering (no images)
        if item_nodes:
            item_xs = [pos[node][0] for node in item_nodes]
            item_ys = [pos[node][1] for node in item_nodes]
            item_zs = [pos[node][2] for node in item_nodes]
            item_sizes_list = [node_sizes[node] for node in item_nodes]

            item_scatter = ax.scatter(
                item_xs, item_ys, item_zs,
                s=item_sizes_list,
                c='#3498db',  # Blue color for item nodes
                alpha=0.7,
                edgecolors='black',
                linewidths=0.5,
                depthshade=True
            )

    # Plot intermediate nodes (smaller, gray)
    intermediate_scatter = None
    if intermediate_nodes:
        int_xs = [pos[node][0] for node in intermediate_nodes]
        int_ys = [pos[node][1] for node in intermediate_nodes]
        int_zs = [pos[node][2] for node in intermediate_nodes]
        int_sizes_list = [node_sizes[node] for node in intermediate_nodes]

        intermediate_scatter = ax.scatter(
            int_xs, int_ys, int_zs,
            s=int_sizes_list,
            c='#95a5a6',  # Gray color for intermediate nodes
            alpha=0.5,
            edgecolors='none',
            depthshade=True
        )

    # Set labels and title
    ax.set_xlabel('X', fontsize=10)
    ax.set_ylabel('Y', fontsize=10)
    ax.set_zlabel('Z', fontsize=10)
    ax.set_title(
        f'Minecraft Transformation Network (3D)\n'
        f'{len(item_nodes)} items, {graph.number_of_edges()} transformations',
        fontsize=14,
        fontweight='bold'
    )

    # Enable numeric axis scales (removed tick removal for better navigation)
    # Users can now see coordinate ranges and understand zoom levels

    # Set background color
    ax.xaxis.pane.fill = False
    ax.yaxis.pane.fill = False
    ax.zaxis.pane.fill = False

    # Create annotation for hover functionality
    annot = ax.text2D(0.05, 0.95, "", transform=ax.transAxes,
                      bbox=dict(boxstyle="round,pad=0.5", fc="white", alpha=0.9, edgecolor="black"),
                      fontsize=10, verticalalignment='top')
    annot.set_visible(False)

    def update_annot(node_name, node_type):
        """Update annotation text with node information."""
        if node_type == 'item':
            text = f"{node_name}"
        else:
            text = f"{node_name}"
        annot.set_text(text)

    def hover(event):
        """Handle mouse motion events to show/hide annotations."""
        vis = annot.get_visible()
        if event.inaxes == ax:
            # Check item nodes
            if item_scatter is not None:
                cont, ind = item_scatter.contains(event)
                if cont:
                    # Get the index of the hovered node
                    node_idx = ind["ind"][0]
                    node_name = item_nodes[node_idx]
                    update_annot(node_name, 'item')
                    annot.set_visible(True)
                    fig.canvas.draw_idle()
                    return

            # Check intermediate nodes
            if intermediate_scatter is not None:
                cont, ind = intermediate_scatter.contains(event)
                if cont:
                    # Get the index of the hovered node
                    node_idx = ind["ind"][0]
                    node_name = intermediate_nodes[node_idx]
                    update_annot(node_name, 'intermediate')
                    annot.set_visible(True)
                    fig.canvas.draw_idle()
                    return

            # If we get here, mouse is not over any node
            if vis:
                annot.set_visible(False)
                fig.canvas.draw_idle()
        else:
            # Mouse outside axes
            if vis:
                annot.set_visible(False)
                fig.canvas.draw_idle()

    # Connect hover event handler
    fig.canvas.mpl_connect("motion_notify_event", hover)

    logging.info("3D visualization rendered successfully with hover annotations")


def visualize_3d(
    csv_path: str,
    config_path: str,
    output_path: str = None,
    use_images: bool = False,
    images_dir: str = "images"
) -> None:
    """
    Generate interactive 3D visualization of transformation graph.

    Args:
        csv_path: Path to transformations CSV file
        config_path: Path to color configuration file
        output_path: Optional path to save figure (if None, only displays)
        use_images: Whether to use item images instead of spheres
        images_dir: Directory containing item images
    """
    # Load color configuration
    color_config = load_color_config(config_path)

    # Build NetworkX graph from CSV
    logging.info("Building graph from CSV...")
    graph = build_graph_from_csv(csv_path, color_config)

    # Compute 3D layout
    logging.info("Computing 3D layout...")
    pos = compute_3d_layout(graph)

    # Calculate node sizes
    logging.info("Calculating node sizes...")
    node_sizes = calculate_node_sizes(graph, pos)

    # Get edge colors
    logging.info("Mapping edge colors...")
    edge_colors = get_edge_colors(graph, color_config)

    # Render the 3D visualization
    logging.info("Rendering 3D visualization...")
    render_3d_graph(
        graph, pos, node_sizes, edge_colors, color_config,
        use_images=use_images,
        images_dir=images_dir
    )

    # Save to file if output path provided
    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        logging.info(f"Saved visualization to {output_path}")

    # Display interactive viewer
    logging.info("Opening interactive 3D viewer...")
    plt.show()


def main():
    """Main entry point for the 3D visualization script."""
    parser = argparse.ArgumentParser(
        description="Generate interactive 3D visualization of Minecraft transformation graphs"
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
        help='Optional output file path to save figure (if not provided, only displays)'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    parser.add_argument(
        '--use-images',
        action='store_true',
        help='Use item images instead of colored spheres for nodes'
    )

    parser.add_argument(
        '--images-dir',
        default='images',
        help='Directory containing item images (default: images/)'
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(levelname)s: %(message)s'
    )

    try:
        visualize_3d(
            csv_path=args.input,
            config_path=args.config,
            output_path=args.output,
            use_images=args.use_images,
            images_dir=args.images_dir
        )

        if args.output:
            print(f"Successfully generated 3D visualization: {args.output}")
        else:
            print("3D visualization displayed in interactive viewer")

    except Exception as e:
        logging.error(f"Failed to generate 3D visualization: {e}")
        raise


if __name__ == '__main__':
    main()
