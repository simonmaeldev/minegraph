# Feature: Interactive 3D Graph Visualization

## Feature Description
Add the ability to generate an interactive 3D visualization of Minecraft item transformations using NetworkX for graph structure and Matplotlib for 3D rendering. The visualization will allow users to rotate, zoom, and pan around the graph in 3D space, providing a more intuitive way to explore complex transformation networks compared to the existing 2D Graphviz visualization. The implementation will use NetworkX's spectral_layout algorithm to position nodes in 3D space and display them with configurable colors, sizes, and edges.

## User Story
As a Minecraft data analyst or developer
I want to visualize the transformation graph in interactive 3D
So that I can explore complex item relationships from multiple angles, better understand the spatial structure of the transformation network, and identify patterns that are harder to see in 2D visualizations

## Problem Statement
The existing Graphviz visualization creates large, complex 2D graphs with 1961+ transformations that are difficult to read and navigate. While filtering helps, even filtered graphs can be cluttered and hard to understand because:
- 2D layouts cannot effectively utilize space for large, interconnected graphs
- Static SVG/PNG outputs don't allow for interactive exploration
- Dense node clusters overlap and become unreadable
- Understanding the overall structure and finding specific patterns requires visual exploration from different perspectives

An interactive 3D visualization would allow users to rotate the camera, zoom in on specific areas, and better understand the spatial relationships between items.

## Solution Statement
Implement a Python script using NetworkX to construct the graph from transformations.csv and Matplotlib's 3D plotting capabilities to render an interactive visualization. The solution will:
- Parse the CSV file to extract transformation_type, input_items, and output_items
- Build a NetworkX directed graph with nodes for items and edges for transformations
- Use spectral_layout to position nodes in 3D space (extending to 3 dimensions)
- Handle multi-input transformations with intermediate nodes (consistent with graphviz approach)
- Color edges by transformation type using the existing graph_colors.txt configuration
- Size nodes based on their importance (number of connections/degree)
- Render using Matplotlib's interactive 3D viewer with mouse controls for rotation and zoom
- Display the visualization by default without saving (though optional save functionality can be added)

## Relevant Files
Use these files to implement the feature:

- **output/transformations.csv** - Source data containing all transformations with transformation_type, input_items, output_items, and metadata. The script will read and parse this CSV file.
- **config/graph_colors.txt** - Existing color configuration file mapping transformation types to color codes. Will be reused for consistent coloring between 2D and 3D visualizations.
- **src/visualize_graph.py** - Existing graphviz visualization script. Provides reference for CSV parsing, color configuration loading, and transformation data handling patterns. We'll reuse some utility functions if appropriate.
- **src/core/data_models.py** - Contains the `TransformationType` enum and `Item`/`Transformation` dataclasses. Useful for understanding data structure and potentially reusing enum values.

### New Files

- **src/visualize_graph_3d.py** - Main script that reads CSV data, builds NetworkX graph, and generates interactive 3D visualization using Matplotlib
- **tests/test_visualize_graph_3d.py** - Unit tests for 3D graph generation logic

## Implementation Plan

### Phase 1: Foundation
Set up the 3D visualization infrastructure by understanding the existing color configuration system and CSV parsing patterns. Create the basic script structure with NetworkX graph construction and ensure dependencies are properly configured.

### Phase 2: Core Implementation
Implement the main 3D visualization logic including:
- NetworkX graph construction from CSV data
- Spectral layout positioning in 3D space
- Node rendering with size based on degree centrality
- Edge rendering with proper coloring by transformation type
- Interactive Matplotlib 3D viewer setup
- Handling of multi-input transformations with intermediate nodes

### Phase 3: Integration
Create the command-line interface following existing project patterns, add test coverage, and ensure the visualization script integrates smoothly with the existing codebase. Document usage and add validation commands.

## Step by Step Tasks

### 1. Research Existing Code Patterns
- Read src/visualize_graph.py to understand CSV parsing and color configuration loading
- Identify utility functions that can be reused (load_color_config, load_transformations_from_csv)
- Understand the data structure of transformations and how intermediate nodes are created
- Review the graph_colors.txt configuration format

### 2. Create Basic Script Structure
- Create src/visualize_graph_3d.py with imports for NetworkX, Matplotlib, and standard libraries
- Add module docstring explaining the script's purpose
- Set up basic logging configuration
- Define constants and default values

### 3. Implement or Reuse CSV Data Loader
- Create function `load_transformations_from_csv(csv_path: str) -> List[dict]` or reuse from existing code
- Parse JSON arrays in input_items and output_items columns
- Parse JSON object in metadata column
- Return list of transformation dictionaries with parsed data
- Add error handling for malformed CSV data

### 4. Implement or Reuse Color Configuration Loader
- Create function `load_color_config(config_path: str) -> dict` or reuse from existing code
- Parse the config/graph_colors.txt file
- Handle comments (lines starting with #) and empty lines
- Provide sensible default colors if config file is missing
- Validate color format (hex codes or color names)

### 5. Implement NetworkX Graph Builder
- Create class `Graph3DBuilder` that manages NetworkX DiGraph construction
- Add method `add_item_node(item_name: str)` that adds nodes to the NetworkX graph
- Track added nodes to avoid duplicates
- Store node metadata (e.g., node type: 'item' vs 'intermediate')

### 6. Implement Intermediate Node Creation for Multi-Input Transformations
- Add method `create_intermediate_node() -> str` that generates unique ID for intermediate nodes
- Use a counter to ensure each intermediate node has a unique identifier
- Mark intermediate nodes with metadata (node_type='intermediate')
- Match the approach used in the graphviz visualization for consistency

### 7. Implement Edge Creation with Transformation Type Metadata
- Add method `add_edge(from_node: str, to_node: str, transformation_type: str)`
- Store transformation type as edge attribute for later coloring
- Handle both single-input and multi-input transformations
- For multi-input: create intermediate node, edges from inputs to intermediate, edge from intermediate to output

### 8. Implement Graph Construction from CSV
- Create function `build_graph_from_csv(csv_path: str) -> nx.DiGraph`
- Load transformations from CSV
- Initialize Graph3DBuilder
- Iterate through transformations and add nodes and edges
- Return completed NetworkX DiGraph with all metadata

### 9. Implement 3D Layout Positioning
- Create function `compute_3d_layout(graph: nx.DiGraph) -> dict`
- Use networkx.spectral_layout with dim=3 to get 3D coordinates
- Handle edge case where graph is too small for spectral layout (fallback to spring_layout)
- Return dictionary mapping node names to (x, y, z) coordinates
- Consider normalizing coordinates to reasonable ranges for visualization

### 10. Implement Node Size Calculation Based on Importance
- Create function `calculate_node_sizes(graph: nx.DiGraph, pos: dict) -> dict`
- Calculate degree centrality for each node using nx.degree_centrality
- Compute node sizes: larger for high-degree nodes, smaller for intermediate nodes
- Use different size ranges: regular nodes (50-500), intermediate nodes (10-20)
- Return dictionary mapping node names to size values

### 11. Implement Edge Color Mapping
- Create function `get_edge_colors(graph: nx.DiGraph, color_config: dict) -> list`
- Extract transformation_type attribute from each edge
- Map transformation type to color using color_config
- Handle missing transformation types with a default color
- Return list of colors in same order as graph.edges()

### 12. Implement 3D Visualization Rendering
- Create function `render_3d_graph(graph: nx.DiGraph, pos: dict, node_sizes: dict, edge_colors: list, color_config: dict)`
- Set up Matplotlib 3D figure and axis (fig = plt.figure(figsize=(16, 12)))
- Plot edges as 3D lines connecting node positions
- Plot nodes as 3D scatter points with appropriate sizes and colors
- Differentiate item nodes (colored by node type or uniform) vs intermediate nodes (smaller, gray)
- Add title and labels

### 13. Implement Main Execution Function
- Create function `visualize_3d(csv_path: str, config_path: str)`
- Load color configuration
- Build NetworkX graph from CSV
- Compute 3D layout with spectral_layout
- Calculate node sizes based on importance
- Get edge colors based on transformation types
- Render the 3D visualization
- Call plt.show() to display interactive viewer (no auto-save by default)

### 14. Implement Command-Line Interface
- Use argparse to create CLI with options for:
  - `--input` / `-i`: path to transformations CSV (default: output/transformations.csv)
  - `--config` / `-c`: path to color config (default: config/graph_colors.txt)
  - `--output` / `-o`: optional output file path to save figure (if not provided, only displays)
  - `--verbose` / `-v`: enable verbose logging
- Add main() function that parses arguments and calls visualize_3d()
- Add if __name__ == "__main__": block

### 15. Write Unit Tests for CSV Loader
- Test loading valid CSV with various transformation types
- Test parsing JSON arrays in input_items and output_items
- Test handling empty CSV
- Test error handling for malformed CSV
- Create small test CSV files in tests/fixtures/

### 16. Write Unit Tests for Graph Builder
- Test creating item nodes without duplicates
- Test creating intermediate nodes with unique IDs
- Test adding edges with transformation type metadata
- Test single-input transformation handling
- Test multi-input transformation handling with intermediate nodes
- Verify graph structure is correct (node count, edge count)

### 17. Write Unit Tests for Layout and Sizing
- Test spectral_layout computation with various graph sizes
- Test node size calculation based on degree centrality
- Test that intermediate nodes get smaller sizes
- Test edge color mapping with valid and missing transformation types
- Use small test graphs with known structures

### 18. Write Integration Test
- Create a small test CSV with sample transformations (mix of single and multi-input)
- Build complete graph and verify structure
- Compute layout and verify all nodes have 3D positions
- Calculate sizes and verify they match expected ranges
- Verify the script can execute end-to-end without errors (no need to test rendering itself)

### 19. Manual Testing and Refinement
- Run the script with full transformations.csv dataset
- Verify visualization is readable and interactive
- Check that colors match the configuration
- Verify node sizes appropriately reflect importance
- Adjust layout parameters or sizing formulas if needed

### 20. Update Documentation
- Add new section to README explaining the 3D visualization feature
- Include usage examples and command-line options
- Document system requirements (NetworkX and Matplotlib already installed)
- Explain the differences between 2D Graphviz and 3D interactive visualization
- Mention that by default it displays without saving, but --output flag can save the figure

### 21. Run Validation Commands
- Execute all validation commands listed below to ensure zero regressions
- Fix any issues that arise during validation
- Verify both existing tests and new tests pass

## Testing Strategy

### Unit Tests
- **CSV Loader**: Test parsing transformations CSV with various data types and edge cases
- **Color Configuration Loader**: Test parsing graph_colors.txt with valid configs, handling defaults
- **Graph Builder Methods**: Test node creation, edge creation, intermediate node generation
- **Layout Computation**: Test spectral_layout with different graph sizes
- **Node Sizing**: Test degree-based sizing calculation with known graphs
- **Edge Coloring**: Test transformation type to color mapping

### Integration Tests
- **End-to-End Graph Building**: Test building complete NetworkX graph from sample CSV
- **Full Visualization Pipeline**: Test entire pipeline from CSV to positioned graph with sizes and colors
- **Multi-Input Transformation Handling**: Test that intermediate nodes are created correctly
- **Error Handling**: Test graceful handling of missing files, malformed data

### Edge Cases
- Empty CSV file
- CSV with only single-input transformations
- CSV with only multi-input transformations
- Very small graphs (< 3 nodes) that may not work well with spectral_layout
- Missing color configuration file
- Invalid transformation types in CSV
- Duplicate transformations
- Self-loops (transformation with same item as input and output)

## Acceptance Criteria
- [ ] NetworkX and Matplotlib dependencies are confirmed available (already installed)
- [ ] New script src/visualize_graph_3d.py is created and functional
- [ ] Script successfully reads and parses output/transformations.csv
- [ ] NetworkX DiGraph is constructed with correct nodes and edges
- [ ] Multi-input transformations create unique intermediate nodes (matching graphviz approach)
- [ ] spectral_layout is used to position nodes in 3D space
- [ ] Node sizes vary based on degree/importance (larger = more connections)
- [ ] Intermediate nodes are smaller than regular item nodes
- [ ] Edges are colored according to transformation type using graph_colors.txt
- [ ] Interactive 3D visualization opens in Matplotlib viewer with default interactivity enabled
- [ ] By default, visualization displays without saving an image
- [ ] Optional --output flag allows saving the figure to a file
- [ ] Command-line interface provides clear options and help text
- [ ] All unit tests pass with 100% success rate
- [ ] Integration test validates end-to-end functionality
- [ ] README documentation includes 3D visualization usage instructions
- [ ] Script follows existing project conventions and code style
- [ ] No regressions in existing functionality (all existing tests still pass)

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

```bash
# Run all existing tests to ensure no regressions
uv run pytest tests/ -v

# Verify NetworkX and Matplotlib are installed
uv pip list | grep -E "(networkx|matplotlib)"

# Display interactive 3D visualization (default behavior - just displays)
uv run python src/visualize_graph_3d.py

# Display with custom input path
uv run python src/visualize_graph_3d.py -i output/transformations.csv

# Display with custom color config
uv run python src/visualize_graph_3d.py -c config/graph_colors.txt

# Display with verbose logging
uv run python src/visualize_graph_3d.py -v

# Save visualization to file (optional)
uv run python src/visualize_graph_3d.py -o output/graphs/graph_3d.png

# Test help text
uv run python src/visualize_graph_3d.py --help

# Run 3D visualization tests specifically
uv run pytest tests/test_visualize_graph_3d.py -v

# Run full test suite one final time
uv run pytest tests/ -v

# Verify color configuration file can be read
cat config/graph_colors.txt
```

## Notes

### NetworkX and Matplotlib Already Installed
The dependencies NetworkX (3.5) and Matplotlib (3.10.7) are already installed via uv, so no additional dependency management is needed. This simplifies the setup compared to the graphviz feature which required system-level installation.

### Spectral Layout for 3D
NetworkX's spectral_layout uses the eigenvectors of the graph Laplacian to position nodes. By setting dim=3, we get 3D coordinates. This layout tends to:
- Separate densely connected clusters
- Place related nodes closer together
- Minimize edge crossings
- Work well for moderately sized graphs (< 5000 nodes)

For very large graphs (1961+ transformations), spectral_layout may be slow. If performance is an issue, we can:
- Use spring_layout with dim=3 as an alternative
- Implement progressive loading or filtering
- Add a command-line flag to choose layout algorithm

### Node Sizing Strategy
Node sizes will be calculated based on degree centrality:
- High-degree nodes (many connections): larger spheres (400-500 units)
- Medium-degree nodes: medium spheres (100-300 units)
- Low-degree nodes: smaller spheres (50-100 units)
- Intermediate nodes: very small spheres (10-20 units)

This helps users quickly identify important/central items in the transformation network.

### Edge Coloring
Edges will be colored according to transformation type using the existing graph_colors.txt configuration:
- Crafting: Blue (#4A90E2)
- Smelting: Orange (#E67E22)
- Brewing: Purple (#9B59B6)
- etc.

This maintains consistency with the Graphviz visualization and makes it easy to identify transformation types at a glance.

### Performance Considerations
With 1961 transformations:
- Graph construction should be fast (< 1 second)
- Spectral layout computation may take 5-30 seconds depending on graph size
- Rendering in Matplotlib may be slower with many nodes/edges
- Interactive rotation should still be smooth with hardware acceleration

If performance becomes an issue:
- Consider using spring_layout with fewer iterations
- Implement edge bundling to reduce visual clutter
- Add optional filtering capabilities (though user requested "always display all")
- Use WebGL-based solutions (plotly, vispy) for better performance (future enhancement)

### Comparison with Graphviz Visualization
| Aspect | Graphviz (2D) | NetworkX + Matplotlib (3D) |
|--------|---------------|----------------------------|
| Layout | Hierarchical, static | Spectral, spatial |
| Interactivity | None (static images) | Full rotation, zoom, pan |
| Readability | Can be cluttered | Better use of 3D space |
| Output | SVG, PNG, PDF files | Interactive window + optional save |
| Performance | Fast for large graphs | Slower layout computation |
| Filtering | By transformation type | All transformations (as requested) |
| Best for | Detailed static analysis | Exploration and understanding |

### Future Enhancements
- Add filtering by transformation type despite user's current preference
- Implement node click events to show item details
- Add search functionality to highlight specific items
- Support different layout algorithms (spring, force-directed)
- Export to interactive HTML using plotly or vispy
- Add animation showing transformation paths
- Implement graph clustering and hierarchical views
- Add legend showing transformation type colors
- Support VR/AR visualization for immersive exploration
