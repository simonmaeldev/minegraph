# Feature: Graph Analysis Metrics Script

## Feature Description
Create a dedicated graph analysis script that constructs the Minecraft transformation graph once and provides modular metric computation functions. The script focuses on analyzing graph properties using NetworkX, including degree metrics, connectivity, and density. Each metric is encapsulated in its own function, allowing users to selectively enable/disable metrics by commenting/uncommenting function calls. This provides a flexible, extensible analysis framework that complements the visualization capabilities in `visualize_graph_3d.py`.

## User Story
As a data analyst or researcher
I want to compute various graph metrics on the Minecraft transformation network
So that I can understand structural properties like connectivity, centrality, and density without needing to visualize the entire graph

## Problem Statement
Currently, the project provides excellent visualization capabilities (`visualize_graph_3d.py`, `visualize_graph_with_graphviz.py`), but lacks a dedicated script for computing and reporting graph metrics. Users interested in quantitative analysis must either:
- Build the graph manually and compute metrics themselves
- Run visualization scripts just to get basic statistics
- Write one-off analysis code that's hard to reuse

There's no easy way to selectively run different metrics without modifying code logic or creating separate scripts.

## Solution Statement
Create a new script `src/analyze_graph.py` that:
1. Constructs the NetworkX graph once from CSV data (reusing existing `build_graph_from_csv()` function)
2. Provides modular metric functions that are self-contained and handle their own output
3. Uses a simple "comment/uncomment" pattern in the main execution block for metric selection
4. Leverages NetworkX's built-in graph analysis algorithms
5. Supports optional transformation type filtering (consistent with visualization scripts)
6. Provides clear, formatted output for each metric with proper labeling

The script will be command-line driven with similar argument patterns to existing scripts, ensuring consistency across the project.

## Relevant Files
Use these files to implement the feature:

- **src/visualize_graph_3d.py** (existing, lines 336-465)
  - Contains `Graph3DBuilder` class for graph construction
  - Implements `build_graph_from_csv()` function that loads transformations and builds NetworkX DiGraph
  - Handles multi-input transformations with intermediate nodes
  - Provides color configuration loading and transformation filtering
  - This will be imported and reused in the new analysis script

- **src/core/data_models.py** (existing)
  - Defines `TransformationType` enum with all transformation types
  - Defines `Item` and `Transformation` dataclasses
  - Provides data validation logic
  - Reference for understanding transformation structure

- **output/transformations.csv** (existing data)
  - Source data file containing all transformations
  - Format: `transformation_type,input_items,output_items,metadata`
  - Items are JSON arrays, will be loaded by existing CSV loading functions

- **config/graph_colors.txt** (existing)
  - Color configuration file (used by graph building function)
  - Not directly used for analysis, but required by `build_graph_from_csv()`

### New Files

- **src/analyze_graph.py**
  - Main analysis script with metric functions
  - Command-line interface with argparse
  - Modular metric functions (each handles its own printing)
  - Main execution block with comment/uncomment pattern for metric selection

- **tests/test_analyze_graph.py**
  - Unit tests for metric computation functions
  - Tests for graph loading and filtering
  - Edge case testing (empty graphs, single node, disconnected components)

## Implementation Plan

### Phase 1: Foundation
- Set up the basic script structure with imports and CLI argument parsing
- Implement graph loading by reusing `build_graph_from_csv()` from `visualize_graph_3d.py`
- Create basic logging and error handling infrastructure
- Ensure the script can successfully load and build the graph from CSV

### Phase 2: Core Implementation
- Implement individual metric functions with the following signature pattern:
  - Each function takes the graph as input
  - Each function is responsible for computing and printing its metric
  - Each function has a clear, descriptive name (e.g., `analyze_average_degree()`)
- Create metric functions for:
  - Average degree (in-degree and out-degree separately for directed graph)
  - Maximum degree (identify nodes with highest connectivity)
  - Number of connected components (weakly and strongly connected)
  - Number of edges (total edge count)
  - Graph density (ratio of actual edges to possible edges)
- Add helper functions for formatting output (consistent spacing, units, etc.)

### Phase 3: Integration
- Create main execution function that loads the graph once
- Implement clean comment/uncomment pattern for metric selection in main block
- Add comprehensive docstrings and inline comments
- Ensure consistency with existing script patterns (argument names, logging format)
- Add filtering support consistent with visualization scripts

## Step by Step Tasks

### Step 1: Create Script Skeleton
- Create `src/analyze_graph.py` with basic structure
- Add imports: `argparse`, `logging`, `sys`, `pathlib`, `networkx`, and imports from `visualize_graph_3d`
- Implement `parse_arguments()` function with CLI flags:
  - `-i/--input`: Path to transformations CSV (default: `output/transformations.csv`)
  - `-c/--config`: Path to color config (default: `config/graph_colors.txt`)
  - `-v/--verbose`: Enable verbose logging
  - `--filter-type`: Optional transformation type filtering (comma-separated)
- Set up logging configuration

### Step 2: Implement Graph Loading
- Import `build_graph_from_csv` and `load_color_config` from `visualize_graph_3d`
- Create `load_graph()` wrapper function that:
  - Loads color configuration
  - Calls `build_graph_from_csv()` with appropriate parameters
  - Handles filtering if specified
  - Returns the constructed NetworkX DiGraph
- Add error handling for missing CSV files or invalid data

### Step 3: Implement Degree Metrics
- Create `analyze_average_degree(graph: nx.DiGraph) -> None` function
  - Compute average in-degree: sum of all in-degrees / number of nodes
  - Compute average out-degree: sum of all out-degrees / number of nodes
  - Print formatted results with 2 decimal precision
  - Handle edge case of empty graph (0 nodes)
- Create `analyze_max_degree(graph: nx.DiGraph) -> None` function
  - Find node(s) with maximum in-degree
  - Find node(s) with maximum out-degree
  - Print node names and their degree values
  - Handle ties (multiple nodes with same max degree)

### Step 4: Implement Connectivity Metrics
- Create `analyze_connected_components(graph: nx.DiGraph) -> None` function
  - Count weakly connected components: `nx.number_weakly_connected_components(graph)`
  - Count strongly connected components: `nx.number_strongly_connected_components(graph)`
  - Print both counts with explanatory labels
  - Explain the difference in output (weakly = undirected connectivity, strongly = directed paths)
- Handle edge case of empty graph (return 0 components)

### Step 5: Implement Basic Graph Metrics
- Create `analyze_edge_count(graph: nx.DiGraph) -> None` function
  - Get total edge count: `graph.number_of_edges()`
  - Get total node count: `graph.number_of_nodes()`
  - Print both values with clear labels
- Create `analyze_density(graph: nx.DiGraph) -> None` function
  - Compute density: `nx.density(graph)`
  - Print as percentage and raw ratio
  - Add explanation: ratio of actual edges to possible edges in directed graph
  - Handle edge case of graphs with fewer than 2 nodes (density undefined)

### Step 6: Create Output Formatting Utilities
- Create `print_section_header(title: str) -> None` helper function
  - Prints formatted section separator with title
  - Uses consistent formatting (e.g., "=== {title} ===")
- Create `print_metric(label: str, value: Any, unit: str = "") -> None` helper
  - Prints metric in consistent format: "  {label}: {value} {unit}"
  - Handles different value types (int, float, str)

### Step 7: Implement Main Execution Logic
- Create `main()` function that:
  - Parses command-line arguments
  - Configures logging based on verbose flag
  - Loads the graph using `load_graph()`
  - Calls metric functions in organized sequence
  - Provides clear execution flow with section headers
- Use comment/uncomment pattern for metric selection:
  ```python
  # Uncomment the metrics you want to compute:
  analyze_average_degree(graph)
  analyze_max_degree(graph)
  analyze_connected_components(graph)
  analyze_edge_count(graph)
  analyze_density(graph)
  ```
- Add error handling and exit codes

### Step 8: Create Test Suite
- Create `tests/test_analyze_graph.py`
- Write unit tests for each metric function:
  - Test with small hand-crafted graphs (known metrics)
  - Test edge cases: empty graph, single node, disconnected graph
  - Test degree calculations with specific graph structures
  - Test component counting with known topologies
  - Test density calculation with complete and sparse graphs
- Write integration tests:
  - Test graph loading from actual CSV file
  - Test filtering by transformation type
  - Test main execution flow (without actual printing)
- Use pytest fixtures for common test graphs

### Step 9: Add Documentation and Polish
- Add comprehensive module-level docstring explaining script purpose and usage
- Add detailed function docstrings with Args, Returns, and Examples sections
- Add inline comments explaining NetworkX function calls and formulas
- Update README.md to document the new analysis script in the "Usage" section
- Add example command-line invocations and expected output format

### Step 10: Validation and Testing
- Run the validation commands (see below) to ensure feature works correctly
- Test with different filtering options
- Test with verbose logging enabled
- Verify output formatting is clear and consistent
- Ensure no regressions in existing functionality

## Testing Strategy

### Unit Tests
- **Metric Accuracy Tests**: Verify each metric function computes correct values for hand-crafted test graphs
  - Create small directed graphs with known properties (e.g., graph with 4 nodes, 6 edges → known density)
  - Test degree calculations: create graph where node A has in-degree=2, out-degree=3
  - Test component counting: create graph with 2 weakly connected components, 3 strongly connected
- **Edge Case Tests**: Test handling of degenerate cases
  - Empty graph (0 nodes, 0 edges)
  - Single node graph (1 node, 0 edges)
  - Complete directed graph (all possible edges present)
  - Disconnected graph (multiple isolated components)
- **Formatting Tests**: Verify output formatting functions produce expected string formats

### Integration Tests
- **CSV Loading Test**: Verify graph can be loaded from actual `output/transformations.csv`
  - Check that graph contains expected number of nodes and edges
  - Verify node types (item vs intermediate nodes) are handled correctly
- **Filtering Test**: Test transformation type filtering
  - Load graph with `--filter-type=crafting` and verify only crafting transformations included
  - Load graph with multiple types and verify correct filtering
- **CLI Argument Parsing**: Test argparse integration
  - Verify default values are applied correctly
  - Test verbose flag enables debug logging
  - Test invalid filter types are handled gracefully

### Edge Cases
- **Empty CSV**: Test behavior when transformations CSV is empty or has no valid rows
- **Invalid JSON**: Test handling of malformed JSON in CSV input_items/output_items columns
- **Missing Files**: Test error handling when CSV file doesn't exist
- **Very Large Graphs**: Test performance with full graph (2200+ transformations, 850+ items)
- **Single Transformation Type**: Test filtering that results in very small graph (e.g., only grindstone transformations)

## Acceptance Criteria
- [ ] Script can load the full graph from `output/transformations.csv` successfully
- [ ] Script can filter by transformation type(s) using `--filter-type` flag
- [ ] All five metric functions produce correct numerical output:
  - Average degree (in and out) computed correctly
  - Maximum degree identifies nodes with highest connectivity
  - Connected components counts match NetworkX algorithms
  - Edge count matches graph.number_of_edges()
  - Density computed correctly as ratio of actual/possible edges
- [ ] Each metric function is self-contained and handles its own printing
- [ ] Output formatting is clear, consistent, and includes appropriate units/labels
- [ ] Users can comment/uncomment metric function calls to control which metrics run
- [ ] Script includes comprehensive docstrings and inline comments
- [ ] Test suite achieves >90% code coverage
- [ ] All tests pass without errors
- [ ] Script follows existing code patterns (argparse, logging, error handling)
- [ ] README.md is updated with usage examples

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

```bash
# Run all tests to ensure no regressions
uv run pytest tests/ -v

# Run specific test file for new feature
uv run pytest tests/test_analyze_graph.py -v

# Run analysis script with default options (all metrics, all transformations)
uv run python src/analyze_graph.py

# Run analysis with verbose logging
uv run python src/analyze_graph.py -v

# Run analysis with transformation type filtering (crafting only)
uv run python src/analyze_graph.py --filter-type=crafting

# Run analysis with multiple transformation types
uv run python src/analyze_graph.py --filter-type=crafting,smelting,smithing

# Run analysis with custom CSV path
uv run python src/analyze_graph.py -i output/transformations.csv

# Test error handling with non-existent file
uv run python src/analyze_graph.py -i nonexistent.csv

# Verify help text is clear and accurate
uv run python src/analyze_graph.py --help
```

## Notes

### NetworkX Metrics Reference
- **Average Degree**: For directed graphs, compute in-degree and out-degree separately
  - In-degree: number of incoming edges to a node
  - Out-degree: number of outgoing edges from a node
  - Use `graph.in_degree()` and `graph.out_degree()` which return DegreeView objects
  - Sum all degrees and divide by number of nodes for average
- **Connected Components**:
  - Weakly connected: components connected if we ignore edge direction
  - Strongly connected: components where every node can reach every other node following directed edges
  - Use `nx.number_weakly_connected_components()` and `nx.number_strongly_connected_components()`
- **Density**: Ratio of actual edges to possible edges
  - For directed graph with n nodes: max possible edges = n*(n-1)
  - Density = m / (n*(n-1)) where m is number of edges
  - Use `nx.density()` which handles the formula

### Future Enhancement Ideas
- Add centrality metrics (betweenness, closeness, eigenvector centrality)
- Add clustering coefficient analysis
- Add path length statistics (average shortest path, diameter)
- Add degree distribution visualization (histogram)
- Add subgraph analysis (analyze specific item neighborhoods)
- Export metrics to CSV or JSON for further analysis
- Add comparison mode (compare metrics across different filtered graphs)
- Add statistical summaries (quartiles, standard deviation of degrees)

### Code Reuse Strategy
The script imports and reuses these functions from `visualize_graph_3d.py`:
- `load_color_config(config_path)`: Load color configuration
- `build_graph_from_csv(csv_path, color_config, filter_types)`: Build NetworkX DiGraph
- `load_transformations_from_csv(csv_path, filter_types)`: Load raw transformation data (if needed)

This ensures consistency and avoids code duplication. The existing graph building logic is well-tested and handles all edge cases (multi-input transformations, intermediate nodes, filtering).

### Design Rationale: Comment/Uncomment Pattern
The decision to use a simple comment/uncomment pattern for metric selection (rather than command-line flags for each metric) was driven by the user requirement: "The goal for me is to be able to comment / uncomment some functions and get the relative metric printed." This approach:
- Provides maximum flexibility with minimal code changes
- Makes it easy to add new metrics without modifying CLI argument parsing
- Keeps the script simple and readable
- Allows users to easily see all available metrics in one place
- Enables easy experimentation (just comment out a line and re-run)

If more complex metric selection is needed in the future, we can add a `--metrics` flag that takes a comma-separated list.
