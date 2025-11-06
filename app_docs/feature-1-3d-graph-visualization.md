# Interactive 3D Graph Visualization

**ADW ID:** 1
**Date:** 2025-11-06
**Specification:** specs/feature-3d-graph-visualization.md

## Overview

This feature adds interactive 3D visualization of Minecraft transformation networks using NetworkX and Matplotlib. Unlike the existing 2D Graphviz visualization, the 3D view allows users to rotate, zoom, and pan around the graph in 3D space, providing better spatial separation for large, interconnected graphs with 1961+ transformations.

## What Was Built

The implementation includes:
- **New 3D Visualization Script** (`src/visualize_graph_3d.py`) - Main script that reads CSV data, builds NetworkX graph, and generates interactive 3D visualization
- **Comprehensive Test Suite** (`tests/test_visualize_graph_3d.py`) - Full unit and integration tests for all 3D visualization components
- **NetworkX Dependency** - Added networkx[default]>=3.5 to pyproject.toml for graph construction and layout algorithms
- **Enhanced Documentation** - Updated README.md with detailed comparison between 2D and 3D visualization options
- **File Rename** - Renamed `src/visualize_graph.py` to `src/visualize_graph_with_graphviz.py` for clarity

## Technical Implementation

### Files Modified

- `src/visualize_graph_3d.py` (new): Complete 3D visualization implementation with NetworkX graph construction, spectral layout positioning, and Matplotlib 3D rendering
- `tests/test_visualize_graph_3d.py` (new): Comprehensive test coverage for CSV loading, graph building, layout computation, node sizing, edge coloring, and end-to-end integration
- `pyproject.toml`: Added networkx[default]>=3.5 dependency
- `README.md`: Added extensive 3D visualization documentation including usage examples, command-line options, feature descriptions, and comparison table between 2D and 3D approaches
- `src/visualize_graph_with_graphviz.py` (renamed from `src/visualize_graph.py`): Made naming more explicit
- `tests/test_visualize_graph.py`: Updated import path after rename

### Key Changes

**Graph Construction:**
- Uses NetworkX DiGraph to model transformation network
- Single-input transformations create direct edges between items
- Multi-input transformations use intermediate nodes (consistent with Graphviz approach)
- Reuses existing `config/graph_colors.txt` for edge coloring by transformation type

**3D Layout Algorithm:**
- Primary: Spectral layout (`nx.spectral_layout` with dim=3) for optimal spatial positioning
- Fallback: Spring layout for small graphs (<3 nodes) where spectral layout may fail
- Layout computation separates densely connected clusters and minimizes edge crossings

**Node Sizing Strategy:**
- Item nodes: Size based on degree centrality (50-500 units) - more connections = larger node
- Intermediate nodes: Fixed small size (15 units) to reduce visual clutter
- Helps users quickly identify important/central items in the network

**Interactive Features:**
- Mouse drag to rotate camera view
- Scroll wheel to zoom in/out
- Right-click drag to pan
- Default behavior: Display interactive window (no save)
- Optional: Save to file with `--output` flag

## How to Use

### Display Interactive 3D Visualization

```bash
# Default: opens interactive viewer with all transformations
uv run python src/visualize_graph_3d.py

# With custom input CSV
uv run python src/visualize_graph_3d.py -i output/transformations.csv

# With custom color configuration
uv run python src/visualize_graph_3d.py -c config/graph_colors.txt

# Enable verbose logging to see detailed progress
uv run python src/visualize_graph_3d.py -v

# Save visualization to file (PNG format)
uv run python src/visualize_graph_3d.py -o output/graphs/graph_3d.png

# View help and all options
uv run python src/visualize_graph_3d.py --help
```

### Interactive Controls

Once the 3D viewer opens:
- **Rotate**: Click and drag with left mouse button
- **Zoom**: Use scroll wheel or trackpad pinch gesture
- **Pan**: Click and drag with right mouse button
- **Reset View**: Close and reopen the viewer

### Run Tests

```bash
# Run all 3D visualization tests
uv run pytest tests/test_visualize_graph_3d.py -v

# Run all tests to ensure no regressions
uv run pytest tests/ -v
```

## Configuration

### Color Customization

Edit `config/graph_colors.txt` to customize edge colors by transformation type (applies to both 2D and 3D visualizations):

```
# Example configuration
crafting=#4A90E2
smelting=#E67E22
blast_furnace=#E67E22
smithing=#95A5A6
brewing=#9B59B6
```

Colors can be hex codes (e.g., `#4A90E2`) or standard color names (e.g., `blue`).

## Testing

The test suite (`tests/test_visualize_graph_3d.py`) includes:

**Unit Tests:**
- Color configuration loading with valid configs, defaults, malformed lines, comments
- CSV transformation loading with various data types, multi-input transformations, error handling
- Graph builder methods: node creation, edge creation, intermediate node generation
- 3D layout computation with different graph sizes and edge cases
- Node size calculation based on degree centrality
- Edge color mapping with valid and missing transformation types

**Integration Tests:**
- End-to-end pipeline from CSV to positioned graph with sizes and colors
- Complex transformation data with mixed single/multi-input transformations
- Verification of graph structure and visualization readiness

All tests pass with 100% success rate.

## Notes

### Performance Considerations

With 1961+ transformations:
- **Graph construction**: Fast (<1 second)
- **Spectral layout computation**: May take 5-30 seconds depending on graph complexity
- **Rendering**: Matplotlib handles large graphs well with hardware acceleration
- **Interactive rotation**: Remains smooth even with many nodes/edges

### Comparison: 2D vs 3D Visualization

| Aspect | 2D (Graphviz) | 3D (NetworkX + Matplotlib) |
|--------|---------------|----------------------------|
| Layout | Hierarchical, static | Spectral, spatial |
| Interactivity | None (static images) | Full rotation, zoom, pan |
| Readability | Can be cluttered with large graphs | Better use of 3D space |
| Output | SVG, PNG, PDF files | Interactive window + optional save |
| Performance | Fast for large graphs | Slower layout computation |
| Filtering | By transformation type | All transformations |
| Dependencies | Requires system Graphviz installation | NetworkX + Matplotlib (Python only) |
| Best for | Detailed static analysis, print | Exploration and understanding |

### No System Dependencies Required

Unlike the 2D Graphviz visualization which requires system-level Graphviz installation, the 3D visualization only needs Python packages (NetworkX and Matplotlib) which are automatically managed by uv. This simplifies setup and deployment.

### Future Enhancements

- Add filtering by transformation type (user requested "all transformations" for initial release)
- Implement node click events to show item details
- Add search functionality to highlight specific items or paths
- Support different layout algorithms (force-directed, hierarchical)
- Export to interactive HTML using plotly for web embedding
- Add legend showing transformation type colors
- Implement animation showing transformation paths over time
