# Feature: Cosmograph Interactive Graph Visualization

## Feature Description
Add the ability to visualize Minecraft item transformations using Cosmograph, a high-performance interactive graph visualization widget for Jupyter notebooks. The visualization will display the transformation graph as an interactive, force-directed network with nodes representing items and directed edges showing transformations. Users can zoom, pan, hover over nodes for details, and explore the complex web of Minecraft transformations in an intuitive, web-based interface. The visualization will handle multi-input transformations using intermediate nodes, color edges by transformation type, and provide an engaging alternative to the existing 2D Graphviz and 3D Matplotlib visualizations.

## User Story
As a Minecraft data analyst or developer
I want to visualize the transformation graph interactively in a Jupyter notebook using Cosmograph
So that I can explore item relationships with smooth animations, hover tooltips, and modern web-based interactivity without needing to install system dependencies like Graphviz

## Problem Statement
The existing visualization options have limitations:
- **Graphviz (2D)**: Produces static images that can be cluttered with 1961+ transformations, requires system-level installation of Graphviz, no interactivity
- **Matplotlib (3D)**: Interactive but slower for large graphs, limited styling options, desktop-only matplotlib window

A web-based, high-performance interactive visualization would allow users to:
- Explore transformations smoothly with force-directed physics simulation
- Hover over nodes to see item names and details
- Zoom and pan seamlessly with modern web interactions
- View the graph in Jupyter notebooks alongside analysis code
- Share interactive HTML exports with others
- Avoid system dependency installations (pure Python package)

Cosmograph provides GPU-accelerated rendering that can handle thousands of nodes smoothly, making it ideal for the complete Minecraft transformation graph.

## Solution Statement
Implement a Jupyter notebook that uses the Cosmograph widget to visualize the transformation graph. The solution will:
- Load transformation data from output/transformations.csv
- Transform the data into Cosmograph's expected format (points DataFrame and links DataFrame)
- Handle multi-input transformations using intermediate nodes (consistent with existing visualizations)
- Color edges by transformation type using the existing config/graph_colors.txt configuration
- Make intermediate nodes visually distinct (smaller size AND gray color)
- Show directed arrows on all edges to indicate transformation direction
- Enable hover labels and display labels for the most important/connected nodes
- Configure the force simulation for optimal layout (repulsion, link forces, etc.)
- Provide clear documentation and examples for users to customize the visualization

## Relevant Files
Use these files to implement the feature:

- **output/transformations.csv** - Source data containing all transformations with transformation_type, input_items, output_items, and metadata. The notebook will read and parse this CSV file.
- **config/graph_colors.txt** - Existing color configuration file mapping transformation types to hex color codes. Will be reused for consistent edge coloring across all visualization types.
- **ai_doc/cosmograph/get_started.txt** - Cosmograph quick start guide explaining basic usage, data format requirements, and key parameters.
- **ai_doc/cosmograph/configuration.txt** - Comprehensive Cosmograph configuration documentation covering all available parameters for points, links, simulation, appearance, and labels.
- **ai_doc/cosmograph/Cosmograph_Widget_in_Colab_✌️.ipynb** - Example Jupyter notebook demonstrating Cosmograph widget usage with sample data, interactive features, and dynamic property updates.
- **src/visualize_graph.py** or **src/visualize_graph_3d.py** - Existing visualization scripts that provide reference for CSV parsing, color configuration loading, and transformation data handling patterns. Utility functions may be reused.

### New Files

- **notebooks/cosmograph_visualization.ipynb** - Jupyter notebook that loads transformation data, prepares it for Cosmograph, and renders the interactive graph visualization
- **src/utils/cosmograph_data_prep.py** - Python module with utility functions for transforming CSV data into Cosmograph-compatible DataFrames (can be imported by the notebook)
- **tests/test_cosmograph_data_prep.py** - Unit tests for the data preparation utility functions

## Implementation Plan

### Phase 1: Foundation
Set up the Cosmograph dependency and understand the required data format. Create utility functions to transform the CSV data into Cosmograph's expected DataFrames (points and links), handling the complexity of multi-input transformations with intermediate nodes.

### Phase 2: Core Implementation
Implement the main Jupyter notebook that:
- Loads transformation data from CSV
- Prepares points and links DataFrames using utility functions
- Configures Cosmograph widget with appropriate visual and simulation settings
- Applies transformation type colors from graph_colors.txt
- Distinguishes intermediate nodes visually (size and color)
- Enables directional arrows and labels

### Phase 3: Integration
Add test coverage for data preparation utilities, document the notebook with clear markdown cells explaining each step, and ensure the implementation follows existing project patterns. Create example outputs and usage instructions.

## Step by Step Tasks

### 1. Add Cosmograph Dependency
- Run `uv add cosmograph` to add the Cosmograph widget package to the project
- Verify the dependency is added to pyproject.toml
- Verify the dependency is compatible with existing Python version (3.13)

### 2. Create Notebooks Directory
- Create `notebooks/` directory in the project root to hold Jupyter notebooks
- Add `notebooks/` to .gitignore if needed (or keep notebooks tracked - decision point)
- Verify the directory structure is appropriate for the project

### 3. Create Data Preparation Utility Module
- Create `src/utils/` directory if it doesn't exist
- Create `src/utils/__init__.py` to make it a package
- Create `src/utils/cosmograph_data_prep.py` with module docstring explaining its purpose
- Set up logging configuration

### 4. Implement Color Configuration Loader
- In `src/utils/cosmograph_data_prep.py`, create function `load_color_config(config_path: str) -> dict`
- Parse the config/graph_colors.txt file line by line
- Handle comments (lines starting with #) and empty lines
- Extract transformation_type=color mappings into a dictionary
- Provide sensible default colors if config file is missing or incomplete
- Return dictionary mapping transformation types to hex color strings

### 5. Implement CSV Data Loader
- Create function `load_transformations_from_csv(csv_path: str) -> List[dict]`
- Read the CSV file using pandas
- Parse JSON arrays in input_items and output_items columns (use json.loads)
- Parse JSON object in metadata column if needed
- Return list of transformation dictionaries with parsed data
- Add error handling for malformed CSV data

### 6. Implement Points DataFrame Builder
- Create class `CosmographDataBuilder` to manage data preparation
- Add method `build_points_dataframe() -> pd.DataFrame`
- Create DataFrame with columns: id, label, node_type (item or intermediate), size, color
- Add all unique items from transformations as points with node_type='item'
- For multi-input transformations (len(input_items) > 1), create intermediate nodes with unique IDs (e.g., "intermediate_0", "intermediate_1")
- Set size for items based on their degree/importance (can compute later)
- Set color: items get a default color, intermediate nodes get gray (#808080)
- Return points DataFrame ready for Cosmograph

### 7. Implement Links DataFrame Builder
- Add method `build_links_dataframe() -> pd.DataFrame`
- Create DataFrame with columns: source, target, transformation_type, color, arrows
- For single-input transformations: create direct link from input item to output item
- For multi-input transformations:
  - Create links from each input item to the corresponding intermediate node
  - Create link from intermediate node to the output item
- Set transformation_type for each link
- Map transformation_type to color using color_config
- Set arrows=True for all links to show direction
- Return links DataFrame ready for Cosmograph

### 8. Implement Node Size Calculation
- Add method `calculate_node_sizes(points: pd.DataFrame, links: pd.DataFrame) -> pd.DataFrame`
- Count the degree (number of connections) for each node from the links DataFrame
- Compute size based on degree: high-degree nodes get larger sizes (e.g., 10-30)
- Intermediate nodes always get small size (e.g., 3-5)
- Update the size column in points DataFrame
- Return updated points DataFrame with size values

### 9. Implement Main Data Preparation Function
- Create function `prepare_cosmograph_data(csv_path: str, config_path: str) -> Tuple[pd.DataFrame, pd.DataFrame, dict]`
- Load color configuration using load_color_config()
- Load transformations using load_transformations_from_csv()
- Initialize CosmographDataBuilder with transformations and color_config
- Build points DataFrame
- Build links DataFrame
- Calculate node sizes
- Return (points, links, color_config) tuple ready for Cosmograph

### 10. Write Unit Tests for Color Config Loader
- In tests/test_cosmograph_data_prep.py, test loading valid config file
- Test handling missing config file with defaults
- Test handling malformed lines gracefully
- Test comment and empty line handling
- Use pytest fixtures for temporary config files

### 11. Write Unit Tests for CSV Loader
- Test loading valid CSV with various transformation types
- Test parsing JSON arrays in input_items and output_items
- Test handling empty CSV
- Test error handling for malformed CSV
- Create small test CSV files in tests/fixtures/

### 12. Write Unit Tests for Points DataFrame Builder
- Test that all unique items are added as points
- Test that intermediate nodes are created for multi-input transformations
- Test that intermediate nodes have correct node_type='intermediate'
- Test that point IDs are unique
- Test that intermediate nodes get gray color
- Verify DataFrame has all required columns

### 13. Write Unit Tests for Links DataFrame Builder
- Test single-input transformation creates direct link
- Test multi-input transformation creates intermediate links correctly
- Test that transformation_type is correctly assigned
- Test that colors are mapped from color_config
- Test that arrows are enabled for all links
- Verify DataFrame has all required columns

### 14. Write Unit Tests for Node Size Calculation
- Test that node sizes reflect degree (number of connections)
- Test that intermediate nodes always get small size
- Test size ranges are appropriate
- Test handling of isolated nodes (degree 0)

### 15. Create Jupyter Notebook Structure
- Create `notebooks/cosmograph_visualization.ipynb`
- Add title cell with markdown: "# Minecraft Transformation Graph - Cosmograph Visualization"
- Add overview cell explaining what the notebook does
- Add setup cell with imports: pandas, json, cosmograph, and the utility module
- Add cells for each step of the visualization process

### 16. Implement Notebook: Load and Prepare Data
- Add markdown cell explaining data loading
- Add code cell to import utility functions from src.utils.cosmograph_data_prep
- Add code cell to call prepare_cosmograph_data() with default paths
- Add code cell to display basic statistics (number of points, number of links)
- Add code cell to show sample rows from points and links DataFrames

### 17. Implement Notebook: Configure Cosmograph Widget
- Add markdown cell explaining Cosmograph configuration
- Add code cell to create Cosmograph widget with initial configuration:
  - points=points
  - links=links
  - point_id_by='id'
  - point_label_by='label'
  - point_size_by='size'
  - point_color_by='color'
  - link_source_by='source'
  - link_target_by='target'
  - link_color_by='color'
  - link_arrows=True
  - show_hovered_point_label=True
  - show_top_labels=True
  - show_top_labels_limit=50

### 18. Implement Notebook: Simulation Settings
- Add markdown cell explaining force simulation settings
- Add code cell to configure simulation parameters:
  - simulation_repulsion=0.5 (increase repulsion for better spread)
  - simulation_link_spring=0.8 (moderate link spring)
  - simulation_link_distance=20 (increase distance for readability)
  - simulation_friction=0.8 (moderate friction for settling)
  - simulation_decay=1500 (slower decay for smoother animation)

### 19. Implement Notebook: Visual Appearance Settings
- Add markdown cell explaining visual customization
- Add code cell to set appearance parameters:
  - background_color='#1a1a1a' (dark background)
  - point_size_scale=2.0 (scale up node sizes for visibility)
  - link_width=1.5 (slightly thicker edges)
  - curved_links=False (straight links for clarity)
  - scale_points_on_zoom=True (maintain node sizes when zooming)
  - render_links=True

### 20. Implement Notebook: Display Visualization
- Add markdown cell with instructions on how to interact with the graph
- Add code cell to display the Cosmograph widget (just reference the widget variable)
- Add markdown cell explaining that the graph is interactive:
  - Drag to pan
  - Scroll to zoom
  - Hover over nodes to see labels
  - Right-click drag for additional interactions

### 21. Implement Notebook: Optional Filtering Examples
- Add markdown cell explaining how to filter the graph
- Add code cell example: filter by transformation type (e.g., only show crafting)
- Add code cell example: filter by specific items (e.g., only show diamond-related items)
- Add code cell example: create a new Cosmograph instance with filtered data

### 22. Implement Notebook: Optional Export/Save
- Add markdown cell explaining export options
- Add code cell comment showing how to save the notebook (File > Save)
- Add note that the Cosmograph visualization is embedded and interactive in the saved notebook
- Add note about exporting to HTML for sharing

### 23. Add Documentation to Notebook
- Add markdown cell at the beginning explaining prerequisites (uv run jupyter notebook)
- Add markdown cell with a table of contents linking to sections
- Add markdown cells throughout explaining each step and why it's necessary
- Add markdown cell at the end with:
  - Summary of what was accomplished
  - Next steps for customization
  - Links to Cosmograph documentation

### 24. Test Notebook Execution
- Run `uv add jupyter` to ensure Jupyter is installed
- Start Jupyter notebook: `uv run jupyter notebook notebooks/cosmograph_visualization.ipynb`
- Execute all cells in order (Kernel > Restart & Run All)
- Verify that the visualization appears and is interactive
- Test hovering over nodes, zooming, panning
- Verify that colors match the configuration
- Verify that intermediate nodes are smaller and gray

### 25. Create README Section for Cosmograph Visualization
- Add new section to README.md titled "### Option 3: Interactive Web-Based Visualization (Cosmograph)"
- Include installation instructions (`uv add cosmograph jupyter`)
- Include command to run the notebook (`uv run jupyter notebook notebooks/cosmograph_visualization.ipynb`)
- Describe key features: interactive, GPU-accelerated, hover tooltips, force-directed layout
- Add comparison table row for Cosmograph vs Graphviz vs Matplotlib
- Note that Cosmograph works in Jupyter notebooks and can export to HTML

### 26. Run Validation Commands
- Execute all validation commands listed below to ensure zero regressions
- Fix any issues that arise during validation
- Verify both existing tests and new tests pass

## Testing Strategy

### Unit Tests
- **Color Configuration Loader**: Test parsing valid configs, handling defaults, error cases
- **CSV Loader**: Test parsing transformations CSV with various data types
- **Points DataFrame Builder**: Test node creation, intermediate node handling, unique IDs
- **Links DataFrame Builder**: Test single-input and multi-input transformations, color mapping
- **Node Size Calculation**: Test degree-based sizing, intermediate node sizing

### Integration Tests
- **End-to-End Data Preparation**: Test the full prepare_cosmograph_data() function with sample CSV
- **DataFrame Validation**: Verify that output DataFrames have correct columns and dtypes
- **Multi-Input Transformation Handling**: Test that intermediate nodes are created correctly
- **Color Mapping**: Test that all transformation types get proper colors

### Manual Testing (Notebook Execution)
- **Full Dataset Visualization**: Run notebook with complete transformations.csv (1961+ transformations)
- **Interactivity**: Test zoom, pan, hover, drag interactions in the widget
- **Performance**: Verify that the visualization renders smoothly (GPU acceleration)
- **Visual Appearance**: Verify colors, sizes, arrows, labels match specifications
- **Filtering Examples**: Test the optional filtering code cells

### Edge Cases
- Empty CSV file
- CSV with only single-input transformations
- CSV with only multi-input transformations
- Transformation with same item as input and output (self-loop)
- Missing color configuration file
- Invalid transformation type in CSV
- Very large graphs (performance considerations)
- Special characters in item names

## Acceptance Criteria
- [ ] Cosmograph dependency is successfully added to the project
- [ ] Jupyter notebook dependency is added to the project
- [ ] notebooks/ directory is created to hold Jupyter notebooks
- [ ] src/utils/cosmograph_data_prep.py module is created with utility functions
- [ ] Color configuration loader successfully reads graph_colors.txt
- [ ] CSV loader successfully parses transformations.csv with JSON fields
- [ ] Points DataFrame contains all items and intermediate nodes with correct structure
- [ ] Intermediate nodes have node_type='intermediate', gray color, and small size
- [ ] Links DataFrame contains all edges with correct source, target, and colors
- [ ] Single-input transformations create direct edges
- [ ] Multi-input transformations create unique intermediate nodes with connecting edges
- [ ] Node sizes reflect importance (degree/connections)
- [ ] All edges have arrows showing transformation direction (link_arrows=True)
- [ ] Edge colors match transformation types from graph_colors.txt
- [ ] Hover labels show item names when hovering over nodes
- [ ] Top labels display for the most important/connected nodes
- [ ] Force simulation is configured for optimal layout and readability
- [ ] Jupyter notebook executes without errors from top to bottom
- [ ] Cosmograph widget displays and is fully interactive (zoom, pan, hover)
- [ ] All unit tests pass with 100% success rate
- [ ] README documentation includes Cosmograph visualization usage instructions
- [ ] Comparison table in README includes Cosmograph alongside Graphviz and Matplotlib
- [ ] No regressions in existing functionality (all existing tests still pass)

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

```bash
# Run all existing tests to ensure no regressions
uv run pytest tests/ -v

# Install/verify cosmograph dependency
uv add cosmograph

# Install/verify jupyter dependency
uv add jupyter

# Verify packages are installed
uv pip list | grep -E "(cosmograph|jupyter)"

# Run new data preparation utility tests
uv run pytest tests/test_cosmograph_data_prep.py -v

# Start Jupyter notebook server
uv run jupyter notebook notebooks/cosmograph_visualization.ipynb

# (In Jupyter): Execute all cells and verify visualization appears
# (In Jupyter): Test interactivity - zoom, pan, hover
# (In Jupyter): Verify colors match configuration
# (In Jupyter): Verify intermediate nodes are small and gray

# Run full test suite one final time
uv run pytest tests/ -v

# Verify color configuration file can be read
cat config/graph_colors.txt

# Test the data preparation utility directly (optional)
uv run python -c "from src.utils.cosmograph_data_prep import prepare_cosmograph_data; points, links, config = prepare_cosmograph_data('output/transformations.csv', 'config/graph_colors.txt'); print(f'Points: {len(points)}, Links: {len(links)}')"
```

## Notes

### Cosmograph Performance
Cosmograph is GPU-accelerated and can handle thousands of nodes smoothly:
- Uses WebGL for rendering
- Optimized force-directed layout algorithm
- Smooth 60 FPS animations even with large graphs
- Interactive zoom/pan without lag
- Suitable for the full 1961+ transformation dataset without filtering

### Jupyter Notebook vs Script
Unlike the Graphviz and Matplotlib visualizations (standalone scripts), Cosmograph works best in Jupyter notebooks because:
- It's a Jupyter widget (anywidget-based)
- Interactive controls require the Jupyter environment
- Notebooks allow for exploratory analysis alongside visualization
- Easy to share notebooks with embedded interactive visualizations
- Can export to HTML with full interactivity preserved

### Data Format Requirements
Cosmograph requires specific DataFrame structures:
- **Points**: Must have an 'id' column with unique identifiers
- **Links**: Must have 'source' and 'target' columns referencing point IDs
- All other columns are optional but can be used for styling (color, size, label, etc.)

### Intermediate Nodes Specification
Based on user requirements:
- **Color**: Gray (#808080) for visual distinction from item nodes
- **Size**: Small (3-5 units) compared to item nodes (10-30 units based on degree)
- **Labels**: Intermediate nodes don't need labels (no label column or empty label)
- **Purpose**: Connect multiple input items to a single output for multi-input transformations

### Edge Arrows Specification
Based on user requirements:
- **All edges**: Show arrows to indicate transformation direction
- **Configuration**: link_arrows=True (global setting)
- **Alternative**: Could use link_arrow_by column for conditional arrows, but user wants all edges to have arrows

### Label Strategy
Based on user requirements:
- **Hover labels**: show_hovered_point_label=True (show on hover for any node)
- **Top labels**: show_top_labels=True with show_top_labels_limit=50 (show for most connected items)
- **Not all labels**: Showing all 850+ item labels would be too cluttered

### Color Configuration
Edge colors will use the existing graph_colors.txt configuration for consistency:
- Crafting: #4A90E2 (blue)
- Smelting: #E67E22 (orange)
- Smithing: #95A5A6 (gray)
- Stonecutter: #7F8C8D (dark gray)
- Trading: #F39C12 (gold)
- Mob Drop: #E74C3C (red)
- Brewing: #9B59B6 (purple)
- Composting: #27AE60 (green)
- Grindstone: #34495E (dark blue-gray)
- Bartering: Need to add to config (suggested: #D4AF37 - metallic gold)

### Comparison with Other Visualizations
| Aspect | Graphviz (2D) | Matplotlib (3D) | Cosmograph (Web) |
|--------|---------------|-----------------|------------------|
| Layout | Hierarchical, static | Spring (force-directed), spatial | Force-directed, dynamic |
| Interactivity | None (static images) | Rotation, zoom, pan | Zoom, pan, hover, drag |
| Performance | Fast generation, large files | Slower layout, desktop window | GPU-accelerated, smooth |
| Output | SVG, PNG, PDF files | Interactive window + optional save | Interactive notebook widget + HTML export |
| Environment | Command-line script | Command-line script | Jupyter notebook |
| Dependencies | System graphviz + Python package | NetworkX + Matplotlib | Pure Python (cosmograph) |
| Labels | Always visible | Hover annotations | Hover + top nodes |
| Best for | Static analysis, print | 3D exploration | Web-based exploration, sharing |

### Future Enhancements
- Add filtering UI within the notebook (interactive dropdowns for transformation types)
- Implement node click events to show detailed item information
- Add search functionality to highlight specific items and their connections
- Create multiple notebook examples (filtered by transformation type, item chains, etc.)
- Export static snapshots of the visualization at specific zoom/pan positions
- Integrate with the existing validate_output.py to show orphaned items
- Add animation showing transformation sequences (e.g., ore → ingot → block)
- Create a dashboard with multiple Cosmograph widgets showing different views
- Support clustering visualization to group related items
- Add legend widget showing transformation type colors
