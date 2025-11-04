# Feature: Graphviz Transformation Graph Visualization

## Feature Description
Add the ability to generate a visual directed graph representation of Minecraft item transformations using Graphviz. The graph will visualize how items transform into other items through various game mechanics (crafting, smelting, brewing, etc.), with different colors representing different transformation types. The visualization will be oriented left-to-right and handle both single-input and multi-input transformations elegantly.

## User Story
As a Minecraft data analyst or developer
I want to visualize the transformation graph from the extracted CSV data
So that I can better understand item relationships, crafting chains, and identify patterns in the Minecraft item ecosystem

## Problem Statement
Currently, the Minegraph project extracts transformation data into CSV format, but there's no way to visualize the relationships between items. Understanding complex crafting chains, identifying item dependencies, and analyzing the overall transformation network requires visual representation. A graph visualization would make it much easier to:
- Identify crafting chains (e.g., ore → ingot → block → tools)
- Understand which transformation types are most common
- Spot bottleneck items that are inputs to many transformations
- Debug data extraction issues by visual inspection

## Solution Statement
Implement a Python script using the Graphviz library that reads `output/transformations.csv` and generates a directed graph visualization. The solution will:
- Parse the CSV file to extract transformation_type, input_items, and output_items
- Create nodes for each unique item (rendered as circles)
- Create edges colored by transformation type
- Handle multi-input transformations by creating unique intermediate nodes (small dots) that connect all inputs to the output
- Allow configuration of transformation type colors through a separate config file
- Output the graph as SVG by default to the output/graphs directory (supports other formats like PNG, PDF, DOT)

## Relevant Files
Use these files to implement the feature:

- **output/transformations.csv** - Source data containing all transformations with transformation_type, input_items, output_items, and metadata. The script will read and parse this CSV file.
- **src/core/data_models.py** - Contains the `TransformationType` enum and `Item`/`Transformation` dataclasses. Useful for understanding data structure and potentially reusing enum values.
- **src/extract_transformations.py** - Shows how the project loads and processes transformation data. Provides patterns for file I/O and data handling.
- **pyproject.toml** - Project dependencies file where we'll add the `graphviz` library.

### New Files

- **config/graph_colors.txt** - Configuration file mapping transformation types to color codes (hex or color names)
- **src/visualize_graph.py** - Main script that reads CSV data and generates the Graphviz graph
- **tests/test_visualize_graph.py** - Unit tests for graph generation logic

## Implementation Plan

### Phase 1: Foundation
Set up the Graphviz dependency and create the configuration structure for transformation colors. Define the core data structures and helper functions needed to parse the CSV and build the graph.

### Phase 2: Core Implementation
Implement the main graph generation logic including:
- CSV parsing and data loading
- Node creation for items and intermediate nodes
- Edge creation with proper coloring
- Handling of multi-input transformations with unique intermediate nodes
- Graph layout and styling configuration

### Phase 3: Integration
Create the command-line interface, add test coverage, and integrate with the existing project structure. Ensure the visualization script follows existing project patterns and can be easily invoked by users.

## Step by Step Tasks

### 1. Add Graphviz Dependency
- Run `uv add graphviz` to add the Graphviz Python library to the project
- Verify the dependency is added to pyproject.toml

### 2. Create Color Configuration File
- Create `config/graph_colors.txt` with mappings for each transformation type
- Use a simple format: `transformation_type=color` (e.g., `crafting=#4A90E2`)
- Include colors for: crafting, smelting, smithing, stonecutter, trading, mob_drop, brewing, composting, grindstone
- Add comments explaining the format and how to customize colors

### 3. Implement Configuration Parser
- In `src/visualize_graph.py`, create a function `load_color_config(config_path: str) -> dict` that parses the color configuration file
- Handle comments (lines starting with #) and empty lines
- Validate that all transformation types have color mappings
- Provide sensible default colors if config file is missing or incomplete

### 4. Implement CSV Data Loader
- Create function `load_transformations_from_csv(csv_path: str) -> List[dict]` that reads the transformations CSV
- Parse JSON arrays in input_items and output_items columns
- Parse JSON object in metadata column
- Return list of transformation dictionaries with parsed data

### 5. Implement Graph Builder Core Logic
- Create class `TransformationGraphBuilder` that manages graph construction
- Initialize Graphviz `Digraph` with left-to-right orientation (`rankdir='LR'`)
- Set default node attributes: shape='circle' for item nodes
- Set default edge attributes: arrowhead='normal'

### 6. Implement Item Node Creation
- Add method `add_item_node(item_name: str)` that creates a node for an item
- Track created nodes in a set to avoid duplicates
- Style item nodes as circles with item name as label

### 7. Implement Intermediate Node Creation for Multi-Input Transformations
- Add method `create_intermediate_node() -> str` that generates a unique ID for intermediate nodes
- Use a counter to ensure each intermediate node has a unique identifier
- Style intermediate nodes as small dots: shape='point', width='0.1'

### 8. Implement Single-Input Transformation Edges
- Add method `add_single_input_transformation(input_item: str, output_item: str, color: str)`
- Create a direct edge from input item to output item
- Apply the transformation type color to the edge

### 9. Implement Multi-Input Transformation Edges
- Add method `add_multi_input_transformation(input_items: List[str], output_item: str, color: str)`
- Create a unique intermediate node
- Create edges from all input items to the intermediate node with the transformation color
- Create edge from intermediate node to output item with the same transformation color

### 10. Implement Main Graph Generation Function
- Create function `generate_graph(csv_path: str, config_path: str, output_path: str) -> None`
- Load color configuration
- Load transformations from CSV
- Initialize TransformationGraphBuilder
- Iterate through transformations and add nodes/edges appropriately
- Render graph to output file with multiple format options

### 11. Implement Command-Line Interface
- Use argparse to create CLI with options for:
  - `--input` / `-i`: path to transformations CSV (default: output/transformations.csv)
  - `--config` / `-c`: path to color config (default: config/graph_colors.txt)
  - `--output` / `-o`: output file path without extension (default: output/graphs/transformation_graph)
  - `--format` / `-f`: output format(s) - svg, png, pdf, dot (default: svg)
  - `--filter-type` / `-t`: optional filter to include only specific transformation types
- Create output/graphs directory if it doesn't exist
- Add logging to show progress and statistics

### 12. Write Unit Tests for Color Config Parser
- Test loading valid config file
- Test handling missing config file with defaults
- Test handling malformed lines gracefully
- Test comment and empty line handling

### 13. Write Unit Tests for CSV Loader
- Test loading valid CSV with various transformation types
- Test parsing JSON arrays in input_items and output_items
- Test handling empty CSV
- Test error handling for malformed CSV

### 14. Write Unit Tests for Graph Builder
- Test creating item nodes
- Test creating intermediate nodes with unique IDs
- Test single-input transformation edge creation
- Test multi-input transformation edge creation
- Test that duplicate nodes aren't created

### 15. Write Integration Test
- Create a small test CSV with sample transformations
- Generate graph using the test data
- Verify that the output file is created
- Verify that the graph contains expected nodes and edges

### 16. Update README with Visualization Instructions
- Add a new section "Visualization" explaining how to generate graphs
- Include example commands and screenshots/descriptions of output
- Document the color configuration file format
- Explain filtering options for large graphs

### 17. Run Validation Commands
- Execute all validation commands listed below to ensure zero regressions
- Fix any issues that arise during validation

## Testing Strategy

### Unit Tests
- **Color Configuration Parser**: Test parsing valid configs, handling defaults, error cases
- **CSV Loader**: Test parsing transformations CSV with various data types
- **Graph Builder Methods**: Test node creation, edge creation, duplicate handling
- **Intermediate Node Generation**: Test uniqueness of intermediate node IDs

### Integration Tests
- **End-to-End Graph Generation**: Test generating a complete graph from a sample CSV file
- **Multiple Format Output**: Test generating graphs in PNG, SVG, PDF, and DOT formats
- **Filtering**: Test filtering by transformation type
- **Large Dataset**: Test performance with the full transformations.csv (1961 transformations)

### Edge Cases
- Empty CSV file
- CSV with only single-input transformations
- CSV with only multi-input transformations
- Transformation with same item as input and output (e.g., wool dyeing)
- Missing color configuration file
- Invalid transformation type in CSV
- Very large graphs (performance considerations)
- Special characters in item names

## Acceptance Criteria
- [ ] Graphviz dependency is successfully added to the project
- [ ] Color configuration file exists with mappings for all transformation types
- [ ] Script successfully reads and parses output/transformations.csv
- [ ] Generated graph is oriented left-to-right (horizontal layout)
- [ ] Each transformation type uses a consistent, configurable color
- [ ] Item nodes are rendered as circles with item names
- [ ] Single-input transformations create direct edges from input to output
- [ ] Multi-input transformations create unique intermediate nodes (small dots)
- [ ] All input items connect to the intermediate node, which connects to the output
- [ ] Each multi-input transformation has its own unique intermediate node
- [ ] Graph is exported as SVG by default to output/graphs directory
- [ ] Graph can be exported in multiple formats (SVG, PNG, PDF, DOT)
- [ ] Command-line interface provides intuitive options for customization
- [ ] Users can filter graph by transformation type
- [ ] All unit tests pass with 100% success rate
- [ ] README documentation includes clear usage instructions
- [ ] Script follows existing project conventions and code style

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

```bash
# Run all existing tests to ensure no regressions
uv run pytest tests/ -v

# Install/verify graphviz dependency
uv sync

# Generate default graph from full dataset (SVG in output/graphs/)
uv run python src/visualize_graph.py

# Verify output file was created
ls -lh output/graphs/transformation_graph.svg

# Generate graph with custom output path
uv run python src/visualize_graph.py -o output/graphs/custom_graph

# Verify SVG was created
ls -lh output/graphs/custom_graph.svg

# Generate filtered graph (only crafting transformations)
uv run python src/visualize_graph.py -t crafting -o output/graphs/crafting_only

# Verify filtered graph was created
ls -lh output/graphs/crafting_only.svg

# Generate multiple formats at once
uv run python src/visualize_graph.py -f png,svg,pdf -o output/graphs/multi_format

# Verify all formats were created
ls -lh output/graphs/multi_format.*

# Generate PNG format specifically
uv run python src/visualize_graph.py -f png -o output/graphs/transformation_graph_png

# Verify PNG was created
ls -lh output/graphs/transformation_graph_png.png

# Run visualization tests specifically
uv run pytest tests/test_visualize_graph.py -v

# Test help text
uv run python src/visualize_graph.py --help

# Validate configuration file exists
cat config/graph_colors.txt

# Run full test suite one final time
uv run pytest tests/ -v
```

## Notes

### Graphviz Installation
Users need to have Graphviz installed on their system (not just the Python library):
- **macOS**: `brew install graphviz`
- **Ubuntu/Debian**: `apt-get install graphviz`
- **Windows**: Download from https://graphviz.org/download/

The README should include a note about this system dependency.

### Performance Considerations
With 1961 transformations, the full graph will be very large and complex. Consider:
- Adding filtering options by transformation type
- Implementing a limit on number of transformations to visualize
- Providing example commands for generating smaller, more readable graphs
- Potentially creating separate graphs per transformation type by default

### Color Palette Suggestions
Use distinct, accessible colors for different transformation types:
- crafting: #4A90E2 (blue)
- smelting: #E67E22 (orange)
- smithing: #95A5A6 (gray/silver)
- stonecutter: #7F8C8D (dark gray)
- trading: #F39C12 (gold)
- mob_drop: #E74C3C (red)
- brewing: #9B59B6 (purple)
- composting: #27AE60 (green)
- grindstone: #34495E (dark blue-gray)

### Future Enhancements
- Interactive HTML visualization using vis.js or D3.js
- Graph analysis metrics (centrality, clustering)
- Path finding between items (e.g., "how do I get from logs to diamond pickaxe?")
- Subgraph extraction for specific item chains
- Integration with a web interface
