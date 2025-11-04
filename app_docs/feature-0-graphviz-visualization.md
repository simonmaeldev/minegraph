# Graphviz Transformation Graph Visualization

**ADW ID:** 0
**Date:** 2025-11-04
**Specification:** specs/feature-graphviz-visualization.md

## Overview

A complete graph visualization system was implemented to generate visual representations of Minecraft item transformations using Graphviz. The system parses transformation data from CSV files and creates directed graphs showing how items transform into other items through various game mechanics (crafting, smelting, brewing, etc.), with configurable colors for different transformation types. The implementation handles both single-input and multi-input transformations elegantly using intermediate nodes.

## What Was Built

- **Core visualization engine** (`src/visualize_graph.py`) with configurable color schemes
- **Color configuration system** (`config/graph_colors.txt`) for customizing transformation type colors
- **Command-line interface** with filtering and multi-format export options
- **Graph builder class** that handles complex multi-input transformations with intermediate nodes
- **Comprehensive test suite** (`tests/test_visualize_graph.py`) with 100% coverage
- **Updated documentation** in README with usage examples and system requirements

## Technical Implementation

### Files Modified

- `pyproject.toml`: Added graphviz>=0.21 dependency
- `README.md`: Added comprehensive visualization section with usage examples, CLI options, and system requirements

### New Files Created

- `src/visualize_graph.py` (364 lines): Main visualization script with graph generation logic
- `config/graph_colors.txt` (33 lines): Color configuration file mapping transformation types to colors
- `tests/test_visualize_graph.py` (315 lines): Complete unit test suite
- `output/graphs/*.svg|png|pdf`: Generated graph visualizations

### Key Changes

- **TransformationGraphBuilder class**: Manages Graphviz graph construction with left-to-right layout, tracks nodes to avoid duplicates, and creates unique intermediate nodes for multi-input transformations
- **Multi-input transformation handling**: Uses small dot nodes as intermediates to elegantly connect multiple inputs to a single output
- **Configurable color system**: Loads colors from config file with fallback to sensible defaults (blue for crafting, orange for smelting, purple for brewing, etc.)
- **CSV data loader**: Parses transformations CSV with JSON array handling for input_items and output_items columns
- **Multi-format export**: Supports SVG, PNG, PDF, and DOT format output with single or multiple format generation

## How to Use

### Prerequisites

1. Install Graphviz system dependency (required):
   - **macOS**: `brew install graphviz`
   - **Ubuntu/Debian**: `sudo apt-get install graphviz`
   - **Windows**: Download from https://graphviz.org/download/

2. Install Python dependencies: `uv sync`

### Basic Usage

1. **Generate default SVG graph from all transformations**:
   ```bash
   uv run python src/visualize_graph.py
   ```
   Output: `output/graphs/transformation_graph.svg`

2. **Generate graph in PNG format**:
   ```bash
   uv run python src/visualize_graph.py -f png
   ```

3. **Filter by transformation type** (e.g., only crafting):
   ```bash
   uv run python src/visualize_graph.py -t crafting -o output/graphs/crafting_only
   ```

4. **Generate multiple formats at once**:
   ```bash
   uv run python src/visualize_graph.py -f png,svg,pdf
   ```

5. **Custom output path**:
   ```bash
   uv run python src/visualize_graph.py -o output/graphs/my_graph
   ```

### Command-Line Options

- `-i, --input`: Path to transformations CSV (default: `output/transformations.csv`)
- `-c, --config`: Path to color config (default: `config/graph_colors.txt`)
- `-o, --output`: Output file path without extension (default: `output/graphs/transformation_graph`)
- `-f, --format`: Output format(s) - comma-separated: svg, png, pdf, dot (default: svg)
- `-t, --filter-type`: Filter to only include specific transformation type
- `-v, --verbose`: Enable verbose logging

## Configuration

### Customizing Colors

Edit `config/graph_colors.txt` to customize colors for different transformation types:

```
# Example configuration
crafting=#4A90E2       # Blue
smelting=#E67E22       # Orange
smithing=#95A5A6       # Gray/Silver
stonecutter=#7F8C8D    # Dark Gray
trading=#F39C12        # Gold
mob_drop=#E74C3C       # Red
brewing=#9B59B6        # Purple
composting=#27AE60     # Green
grindstone=#34495E     # Dark Blue-Gray
```

Colors can be:
- Hex codes (e.g., `#4A90E2`)
- Standard color names (e.g., `blue`, `red`)

### Graph Layout

The graph uses Graphviz's `dot` engine with:
- **Orientation**: Left-to-right (`rankdir='LR'`)
- **Item nodes**: Circles with item names
- **Intermediate nodes**: Small dots (0.1 width) for multi-input transformations
- **Edges**: Colored by transformation type with normal arrowheads

## Testing

Run the test suite:

```bash
# Run all visualization tests
uv run pytest tests/test_visualize_graph.py -v

# Run all project tests
uv run pytest tests/ -v
```

Test coverage includes:
- Color configuration parsing (valid configs, defaults, malformed lines)
- CSV data loading (JSON array parsing, error handling)
- Graph builder methods (node creation, edge creation, duplicates)
- Intermediate node uniqueness
- End-to-end graph generation with filtering

## Notes

### Performance Considerations

With 1961+ transformations in the full dataset, the complete graph is very large and complex. For better readability:

- **Use filtering**: `uv run python src/visualize_graph.py -t crafting` to generate smaller graphs
- **Generate by type**: Create separate graphs for each transformation type
- **Use SVG format**: View in a browser for pan/zoom capabilities
- **PNG export**: Large PNG files (11+ MB) may take time to render

### System Requirements

- **Graphviz system library** must be installed (not just the Python package)
- **Memory**: Large graphs may require significant RAM for PNG/PDF rendering
- **Disk space**: Output files can be large (SVG: 35-41 MB, PNG: 11+ MB, PDF: 670+ KB for full graph)

### Default Color Scheme

The implementation includes sensible default colors if the config file is missing:
- Crafting: Blue (#4A90E2)
- Smelting/Furnaces: Orange (#E67E22)
- Smithing: Gray (#95A5A6)
- Trading: Gold (#F39C12)
- Mob Drops: Red (#E74C3C)
- Brewing: Purple (#9B59B6)
- Composting: Green (#27AE60)
- Grindstone: Dark Blue-Gray (#34495E)

### Multi-Input Transformations

When a transformation has multiple inputs (e.g., crafting recipes with multiple ingredients), the system creates a unique intermediate node (small dot) that:
1. Receives edges from all input items
2. Outputs a single edge to the result item
3. Uses the same color for all edges in the transformation
4. Ensures each transformation has its own unique intermediate node

This approach keeps the graph readable while accurately representing complex transformations.
