# Bug: Remove Intermediate Nodes from Analysis Graph

## Bug Description
The current graph construction creates intermediate nodes for multi-input transformations. For example, a crafting recipe with inputs [A, B, C] and output D creates the following structure:
- A -> intermediate_0 -> D
- B -> intermediate_0
- C -> intermediate_0

**For visualization purposes**, these intermediate nodes are useful as they clearly show multi-input transformations with a visual grouping node.

**For graph analysis and metrics**, these intermediate nodes are problematic because:
1. They artificially inflate node counts
2. They create indirect edges instead of showing direct item-to-item relationships
3. They skew graph metrics (degree, density, centrality, etc.)
4. They don't represent actual Minecraft items

The expected behavior is:
- **Visualization (3D/2D/Cosmograph)**: Keep intermediate nodes for visual clarity
- **Analysis (analyze_graph.py)**: Use direct edges without intermediate nodes, with maximum one oriented edge between any two nodes

## Problem Statement
The `analyze_graph.py` script currently imports and uses `build_graph_from_csv()` from `visualize_graph_3d.py`, which always creates intermediate nodes. For accurate graph metrics, we need a separate graph construction function that creates direct edges from inputs to outputs without intermediate nodes.

Additionally, the analysis graph must enforce that there is at most one oriented edge between any two nodes in a given direction (though bidirectional edges A->B and B->A are both allowed).

## Solution Statement
Create a new analysis-specific graph builder that:
1. Creates direct edges from each input item to output items (A->D, B->D, C->D)
2. Skips creating intermediate nodes entirely
3. Implements edge deduplication (no duplicate A->B edges)
4. Is used by `analyze_graph.py` instead of the visualization builder
5. Keeps the existing `Graph3DBuilder` unchanged for visualization purposes

## Steps to Reproduce
1. Run the graph analysis script: `uv run python src/analyze_graph.py`
2. Observe that the output shows "Intermediate nodes: X nodes" where X > 0
3. Metrics like average degree, density, and node count include intermediate nodes
4. These metrics don't accurately reflect item-to-item transformation relationships

## Root Cause Analysis
The root cause is in `src/analyze_graph.py:89-130`:
- **Line 33**: Imports `build_graph_from_csv` from `visualize_graph_3d.py`
- **Line 125**: Calls `build_graph_from_csv()` which always creates intermediate nodes
- **No alternative**: There's no analysis-specific graph builder without intermediate nodes

The `build_graph_from_csv()` function in `visualize_graph_3d.py:422-465`:
- **Lines 395-419**: `Graph3DBuilder.add_multi_input_transformation()` creates intermediate nodes
- **Lines 452-456**: Calls this method for all transformations with multiple inputs
- **Design intent**: Intermediate nodes were designed for visual clarity in graphs, which is appropriate for visualization but not for analysis

## Relevant Files
Use these files to fix the bug:

- **src/analyze_graph.py**
  - Currently imports `build_graph_from_csv` from visualize_graph_3d.py (line 33)
  - Calls it in `load_graph()` function (line 125)
  - Contains `analyze_edge_count()` which reports intermediate node count (lines 278-300)
  - Need to add new analysis-specific graph builder here

- **src/visualize_graph_3d.py** (DO NOT MODIFY - keep for visualization)
  - Contains `Graph3DBuilder` class (lines 336-420)
  - Contains `build_graph_from_csv()` function (lines 422-465)
  - Keep unchanged - used by 3D visualization, 2D Graphviz, and Cosmograph
  - Intermediate nodes are intentionally kept for visual clarity

- **tests/test_analyze_graph.py**
  - Contains fixtures that create graphs with intermediate nodes
  - Tests specifically validate intermediate node behavior
  - Need to update fixtures to use direct edges for analysis tests

### New Files
- None - all changes are modifications to existing files

## Step by Step Tasks

### Step 1: Create analysis-specific graph builder in analyze_graph.py
- Add a new `AnalysisGraphBuilder` class to `src/analyze_graph.py`
- Implement methods similar to `Graph3DBuilder` but without intermediate nodes:
  - `add_item_node(item_name)`: Add item nodes only
  - `add_edge_with_dedup(from_node, to_node, transformation_type)`: Add edges with deduplication
  - `add_transformation(inputs, outputs, transformation_type)`: Handle both single and multi-input transformations
- For multi-input transformations, create direct edges: A->D, B->D, C->D
- Implement edge deduplication to ensure maximum one oriented edge between nodes

### Step 2: Create analysis-specific graph loading function
- Add a new `build_analysis_graph_from_csv()` function to `src/analyze_graph.py`
- Use `load_transformations_from_csv()` from visualize_graph_3d.py (reuse CSV parsing)
- Use the new `AnalysisGraphBuilder` instead of `Graph3DBuilder`
- Return a graph with only item nodes and direct edges

### Step 3: Update load_graph() to use analysis builder
- Modify `load_graph()` function in `src/analyze_graph.py` (lines 89-130)
- Replace call to `build_graph_from_csv()` with `build_analysis_graph_from_csv()`
- Remove import of `build_graph_from_csv` from visualize_graph_3d.py
- Keep import of `load_color_config` (still needed for compatibility)

### Step 4: Update analyze_edge_count() reporting
- Modify `analyze_edge_count()` in `src/analyze_graph.py` (lines 278-300)
- Update messaging to clarify this is an analysis graph without intermediate nodes
- Remove intermediate node counting logic (should always be 0)
- Add note that visualization graphs may have intermediate nodes

### Step 5: Update test fixtures for analysis
- Modify `multi_input_graph` fixture in `tests/test_analyze_graph.py` (lines 62-81)
  - Remove intermediate node creation
  - Create direct edges: A->D, B->D, C->D
- Update test expectations:
  - `test_average_degree_multi_input` (lines 206-221): Update expected averages for direct edges
  - `test_edge_count_multi_input` (lines 329-337): Expect 0 intermediate nodes
  - `test_max_degree_multi_input` (lines 251-257): Update to reflect direct edges

### Step 6: Run validation commands
- Execute all validation commands below to ensure the fix works correctly
- Verify that analysis shows "Intermediate nodes: 0"
- Verify that 3D visualization still shows intermediate nodes correctly
- Check that metrics accurately reflect item-to-item relationships

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `uv run pytest tests/test_analyze_graph.py -v` - Run analysis tests to verify graph construction without intermediate nodes
- `uv run python src/analyze_graph.py -v` - Run analysis and verify "Item nodes: X" matches total nodes (no intermediate nodes)
- `uv run python src/analyze_graph.py --filter-type=crafting -v` - Test with filtering to ensure direct edges work correctly
- `uv run python src/visualize_graph_3d.py --no-interactive` - Verify visualization STILL shows intermediate nodes correctly
- `uv run pytest tests/ -v` - Run all tests to catch any regressions

## Notes
- **Separation of Concerns**: This fix creates two separate graph construction paths:
  - **Visualization path**: `visualize_graph_3d.py` → `Graph3DBuilder` → keeps intermediate nodes for visual clarity
  - **Analysis path**: `analyze_graph.py` → `AnalysisGraphBuilder` → direct edges only for accurate metrics
- **Why keep intermediate nodes in visualization?** They provide visual grouping for multi-input transformations and make the graph easier to understand visually
- **Why remove them from analysis?** They artificially inflate metrics and don't represent actual Minecraft items
- After this fix, analysis graphs will have:
  - Nodes with higher in-degree (multiple inputs pointing to same output)
  - More direct edges (each input creates its own edge to output)
  - Accurate graph metrics reflecting true item-to-item relationships
- Edge deduplication is critical for analysis: if two different transformations have the same input->output pair, only create one edge
- The `node_type` attribute in analysis graphs will only have one value: 'item'
- All visualization features (3D, 2D Graphviz, Cosmograph) continue to use `Graph3DBuilder` and are unchanged
- The CSV parsing logic (`load_transformations_from_csv`) can be reused by both builders
