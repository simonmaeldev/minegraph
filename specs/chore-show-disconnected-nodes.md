# Chore: Show Disconnected Nodes in Graph Analysis

## Chore Description
Add functionality to the graph analysis script (`src/analyze_graph.py`) to identify and display all nodes that are not connected to the main (largest) weakly connected component. This will help identify isolated items, small disconnected crafting chains, and orphaned transformation networks that exist separately from the primary Minecraft transformation graph.

The output should clearly list the names of all nodes in disconnected components, grouped by component, making it easy to understand which items form isolated subgraphs.

## Relevant Files
Use these files to resolve the chore:

- **src/analyze_graph.py** - Main graph analysis script
  - Contains the `AnalysisGraphBuilder` class for constructing analysis graphs
  - Contains modular metric analysis functions that we'll extend
  - Lines 376-405: `analyze_connected_components()` function that we'll enhance
  - Lines 462-526: `main()` function where we'll add the new metric call
  - Already has the infrastructure for computing weakly connected components using NetworkX

- **tests/test_analyze_graph.py** - Test suite for graph analysis
  - Lines 266-302: Existing tests for `analyze_connected_components()` that we'll extend
  - Lines 98-117: `disconnected_graph` fixture showing a graph with 2 components (A→B and C→D)
  - We'll add new tests for the enhanced disconnected node analysis

### Documentation Files to Reference
Per `conditional_docs.md`, the following documentation is relevant for this chore:

- **app_docs/feature-graph-analysis-metrics.md** - Understanding the metric system
  - How to add new metric computation functions following the established pattern
  - Understanding the comment/uncomment pattern for metric selection
  - How metrics use `print_section_header()` and `print_metric()` utilities

- **app_docs/bug-remove-intermediate-nodes.md** - Understanding the graph structure
  - Explains why `AnalysisGraphBuilder` creates direct edges without intermediate nodes
  - Confirms that analysis graphs contain only item nodes (`node_type='item'`)
  - All nodes in the analysis graph represent actual Minecraft items

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Enhance the `analyze_connected_components()` function
- Modify the existing `analyze_connected_components()` function in `src/analyze_graph.py` (lines 376-405)
- After computing the number of weakly connected components, add logic to:
  - Use `nx.weakly_connected_components(graph)` to get all component node sets
  - Identify the largest component (main graph)
  - Identify all smaller components (disconnected from main graph)
  - For each disconnected component, collect and display the node names
- Format the output to show:
  - Number of nodes in the main (largest) component
  - Number of disconnected components (excluding the main one)
  - For each disconnected component: list of node names, sorted alphabetically
  - Total count of disconnected nodes
- Use existing formatting utilities: `print_metric()` for counts, plain print statements for node lists
- Handle edge cases:
  - Empty graphs (no components)
  - Single-component graphs (all nodes connected - this is the expected case)
  - Graphs with only disconnected components (no dominant component)

### Step 2: Update tests for enhanced component analysis
- Modify existing tests in `tests/test_analyze_graph.py`
- Update `test_connected_components_disconnected()` (lines 287-293) to verify:
  - The new output includes "Main component nodes" count
  - The new output includes "Disconnected components" count
  - The new output lists the specific node names in disconnected components
- Add a new test `test_connected_components_lists_disconnected_nodes()`:
  - Use the `disconnected_graph` fixture (A→B and C→D components)
  - Verify that disconnected node names are printed
  - Verify that nodes are grouped by component
  - Verify that node names are sorted alphabetically within each component
- Add a new test `test_connected_components_all_connected()`:
  - Use the `simple_chain_graph` fixture (A→B→C, all in one component)
  - Verify that the output indicates "All nodes are in the main component"
  - Verify no disconnected nodes are listed

### Step 3: Add example to module docstring
- Update the module docstring in `src/analyze_graph.py` (lines 1-22)
- Add "Disconnected nodes" to the list of available metrics (around line 21)
- Update the description to mention that connected components analysis now includes detailed node listings

### Step 4: Manual verification with real data
- Run the enhanced analysis script on the actual Minecraft transformation graph:
  - `uv run python src/analyze_graph.py -v`
- Review the output to confirm:
  - The main component size matches expectations (~800+ nodes for full Minecraft data)
  - Any disconnected components are correctly identified with their node names
  - Output is readable and well-formatted
- If disconnected nodes are found, verify they make sense in the Minecraft context:
  - Could be Education Edition items that aren't connected to main Java Edition recipes
  - Could be deprecated/removed items with orphaned transformations
  - Could be data extraction bugs that need fixing (note for future investigation)

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `uv run pytest tests/test_analyze_graph.py::test_connected_components_disconnected -v` - Verify enhanced disconnected graph test passes
- `uv run pytest tests/test_analyze_graph.py::test_connected_components_all_connected -v` - Verify all-connected graph test passes
- `uv run pytest tests/test_analyze_graph.py -v` - Run all analysis graph tests to ensure no regressions
- `uv run pytest tests/ -v` - Run full test suite to ensure no project-wide regressions
- `uv run python src/analyze_graph.py -v` - Run analysis on real data and verify disconnected nodes are displayed
- `uv run python src/analyze_graph.py --filter-type=crafting -v` - Test with filtered data to verify it works with subsets

## Notes

### NetworkX API Usage
- Use `nx.weakly_connected_components(graph)` which returns an iterator of sets, where each set contains the node names in a component
- Components are returned in descending order by size (largest first), so the first component is the main one
- Example:
  ```python
  components = list(nx.weakly_connected_components(graph))
  main_component = components[0] if components else set()
  disconnected_components = components[1:] if len(components) > 1 else []
  ```

### Output Format Example
The enhanced output should look like this for a graph with disconnected components:

```
============================================================
  Connected Components Analysis
============================================================
  Weakly connected components: 3
    (Components connected ignoring edge direction)
  Strongly connected components: 8
    (Components with directed paths between all nodes)

  Main component nodes: 847 nodes
  Disconnected components: 2

  Component 1 (3 nodes):
    - Board
    - Chalkboard
    - Slate

  Component 2 (2 nodes):
    - Glow Stick
    - Polyethylene

  Total disconnected nodes: 5 nodes
```

For a fully connected graph:
```
============================================================
  Connected Components Analysis
============================================================
  Weakly connected components: 1
    (Components connected ignoring edge direction)
  Strongly connected components: 245
    (Components with directed paths between all nodes)

  Main component nodes: 850 nodes
  All nodes are in the main component (no disconnected nodes).
```

### Why This Is Useful
- **Data Quality**: Identifies items that may have parsing errors or missing transformation data
- **Game Understanding**: Reveals isolated crafting systems (e.g., Education Edition items)
- **Debugging**: Helps diagnose why certain items don't appear in the main transformation network
- **Documentation**: Provides a clear list of "orphaned" items for further investigation
