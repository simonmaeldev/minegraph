# Bug Fix: Remove Intermediate Nodes from Analysis Graph

**ADW ID:** remove-intermediate-nodes
**Date:** 2025-11-24
**Specification:** specs/bug-remove-intermediate-nodes.md

## Overview

Fixed a critical bug where the graph analysis script (`analyze_graph.py`) was creating intermediate nodes for multi-input transformations, which artificially inflated node counts and skewed graph metrics. The fix introduces a new `AnalysisGraphBuilder` that creates direct edges from inputs to outputs (A→D, B→D, C→D) without intermediate nodes, while preserving the existing visualization behavior that uses intermediate nodes for visual clarity.

## What Was Built

- **AnalysisGraphBuilder class**: New graph builder specifically for analysis that creates direct edges without intermediate nodes
- **build_analysis_graph_from_csv()**: Analysis-specific graph loading function that uses the new builder
- **Edge deduplication**: Ensures maximum one oriented edge between any two nodes in a given direction
- **Comprehensive test suite**: 521 lines of tests covering all edge cases and metric computations

## Technical Implementation

### Files Created

- `src/analyze_graph.py` (526 lines): Complete graph analysis module with the new AnalysisGraphBuilder
  - Lines 39-118: `AnalysisGraphBuilder` class with methods for direct edge construction
  - Lines 120-163: `build_analysis_graph_from_csv()` function for analysis-specific graph loading
  - Lines 165-526: Metric computation functions (average degree, max degree, connected components, density, etc.)

- `tests/test_analyze_graph.py` (521 lines): Comprehensive test suite
  - Lines 32-167: Test fixtures for various graph topologies
  - Lines 170-521: Tests for all metric functions and edge cases

### Key Changes

- **Direct edge construction**: For multi-input transformations (A, B, C → D), creates three direct edges: A→D, B→D, C→D instead of using intermediate nodes
- **Edge deduplication**: Uses an `edge_set` dictionary to track existing edges and prevent duplicates when multiple transformations share the same input-output relationship
- **Separation of concerns**: Analysis graphs now use `AnalysisGraphBuilder` while visualization graphs continue using `Graph3DBuilder` with intermediate nodes
- **Accurate metrics**: Graph metrics (degree, density, centrality) now reflect true item-to-item relationships without artificial inflation from intermediate nodes

`★ Insight ─────────────────────────────────────`
**1. Design Pattern - Separation of Concerns**: This implementation demonstrates a clean separation between visualization and analysis concerns. The `Graph3DBuilder` optimizes for human visual comprehension with grouping nodes, while `AnalysisGraphBuilder` optimizes for mathematical accuracy by representing the true transformation network.

**2. Edge Deduplication Strategy**: The `edge_set` dictionary using `(from, to)` tuples as keys provides O(1) lookup for duplicate detection. This is critical when multiple different recipes produce the same item from the same ingredient (e.g., different crafting recipes that all use wood to create planks).

**3. Graph Theory Application**: By removing intermediate nodes, the analysis reveals the true bipartite nature of the transformation network - items that are only inputs vs. items that are only outputs vs. items that serve both roles (intermediate goods in the production chain).
`─────────────────────────────────────────────────`

## How to Use

### Running Graph Analysis

1. **Analyze all transformations**:
   ```bash
   uv run python src/analyze_graph.py
   ```

2. **Verbose output with detailed logging**:
   ```bash
   uv run python src/analyze_graph.py -v
   ```

3. **Filter by transformation type**:
   ```bash
   uv run python src/analyze_graph.py --filter-type=crafting
   uv run python src/analyze_graph.py --filter-type=crafting,smelting
   ```

4. **Use custom CSV file**:
   ```bash
   uv run python src/analyze_graph.py -i custom.csv
   ```

### Available Metrics

The analysis script computes the following metrics:
- **Average Degree**: Mean in-degree and out-degree across all nodes
- **Maximum Degree**: Nodes with highest connectivity (hub identification)
- **Connected Components**: Weakly and strongly connected components
- **Edge Count**: Total edges and node breakdown (item nodes only)
- **Graph Density**: Ratio of actual edges to possible edges

### Verifying the Fix

Check that intermediate nodes are removed:
```bash
uv run python src/analyze_graph.py -v
```

Look for the output line showing "Item nodes: X" matching "Total nodes: X" (no intermediate nodes).

## Configuration

No configuration changes required. The analysis automatically uses the new `AnalysisGraphBuilder`, while visualization tools (`visualize_graph_3d.py`, `visualize_graph_2d.py`, `visualize_cosmograph.py`) continue using `Graph3DBuilder`.

## Testing

Run the comprehensive test suite:

```bash
# Run only analysis tests
uv run pytest tests/test_analyze_graph.py -v

# Run all tests to check for regressions
uv run pytest tests/ -v
```

Test coverage includes:
- Empty graphs, single-node graphs, and chain graphs
- Multi-input transformations with direct edges
- Disconnected components
- Cyclic graphs
- Hub nodes with high degree
- Complete graphs (maximum density)
- Edge cases (division by zero, no edges, etc.)

## Notes

### Why This Approach?

**For Analysis**: Intermediate nodes were problematic because:
- They artificially inflated node counts
- They created indirect edges instead of showing direct item-to-item relationships
- They skewed graph metrics (degree, density, centrality)
- They didn't represent actual Minecraft items

**For Visualization**: Intermediate nodes are still useful because:
- They provide visual grouping for multi-input transformations
- They make the graph easier to understand visually
- They show the "recipe" as a distinct entity

### Graph Structure Changes

After this fix, analysis graphs have:
- **Higher in-degree nodes**: Multiple inputs can now point directly to the same output
- **More direct edges**: Each input creates its own edge to the output
- **Accurate metrics**: Metrics now reflect true item-to-item transformation relationships
- **Single node type**: All nodes have `node_type='item'` (no intermediate nodes)

### Backward Compatibility

- **Visualization unchanged**: All visualization tools (3D, 2D Graphviz, Cosmograph) continue working as before
- **CSV parsing reused**: The `load_transformations_from_csv()` function is shared between both builders
- **No breaking changes**: Existing visualization scripts and their outputs remain unchanged

### Edge Deduplication Details

If multiple transformations produce the same output from the same input:
- Example: Recipe A: [Wood] → Planks (crafting), Recipe B: [Wood] → Planks (stonecutting)
- Only **one edge** is created: Wood → Planks
- The `transformation_type` of the first encountered transformation is preserved
- This prevents duplicate edges while maintaining graph integrity
