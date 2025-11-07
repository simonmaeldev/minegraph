# Minegraph

A Python-based data extraction system for Minecraft Java Edition transformation recipes. Minegraph downloads and parses wiki pages to build a comprehensive directed graph of all item transformations in the game.

## Purpose

Minegraph extracts transformation data from the Minecraft Wiki to create structured datasets showing how items can be transformed through various game mechanics:

- **Crafting** (shaped and shapeless recipes)
- **Smelting** (furnace, blast furnace, smoker)
- **Smithing** (netherite upgrades, armor trims)
- **Stonecutting**
- **Trading** (villager trades)
- **Mob drops** (with probabilities)
- **Brewing** (potions)
- **Composting** (organic items to bone meal)
- **Grindstone** (disenchanting)

The output consists of two CSV files:
- `output/items.csv` - All unique items with their wiki URLs
- `output/transformations.csv` - All transformations with input/output items and transformation types

This data can be used for graph analysis, recipe calculators, crafting optimization tools, or any application requiring Minecraft transformation data.

## Installation

This project uses [uv](https://github.com/astral-sh/uv) for dependency management.

1. **Install uv** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd minegraph
   ```

3. **Install dependencies**:
   ```bash
   uv sync
   ```

   This will create a virtual environment and install all required dependencies:
   - beautifulsoup4
   - lxml
   - requests
   - pytest
   - graphviz (Python package)
   - networkx (for 3D visualization)
   - matplotlib (for 3D visualization)

4. **Install Graphviz system dependency** (optional, only required for 2D visualization):
   - **macOS**: `brew install graphviz`
   - **Ubuntu/Debian**: `sudo apt-get install graphviz`
   - **Windows**: Download from https://graphviz.org/download/
   - **Note**: The 3D visualization (NetworkX + Matplotlib) does not require Graphviz to be installed

## Usage

### Extract Transformation Data

Run the extraction script to download wiki pages and generate CSV outputs:

```bash
uv run python src/extract_transformations.py
```

This will:
1. Download wiki pages to `ai_doc/downloaded_pages/` (cached, skips if already present)
2. Parse HTML to extract transformation recipes
3. Generate `output/items.csv` and `output/transformations.csv`

### Run Tests

Execute the test suite to verify parsing and data models:

```bash
uv run pytest tests/ -v
```

### Validate Output

After extraction, validate the output data quality:

```bash
uv run python src/validate_output.py
```

This checks for duplicates, orphaned transformations, and reports statistics.

### Visualize Transformation Graph

Minegraph provides two visualization options: **static 2D graphs** (Graphviz) and **interactive 3D graphs** (NetworkX + Matplotlib).

#### Option 1: 2D Graph Visualization (Graphviz)

Generate static 2D visual representations using Graphviz:

```bash
# Generate default SVG graph from all transformations
uv run python src/visualize_graph_with_graphviz.py

# Generate graph in PNG format
uv run python src/visualize_graph_with_graphviz.py -f png

# Generate graph with custom output path
uv run python src/visualize_graph_with_graphviz.py -o output/graphs/my_graph

# Filter by transformation type (e.g., only crafting)
uv run python src/visualize_graph_with_graphviz.py -t crafting -o output/graphs/crafting_only

# Generate multiple formats at once
uv run python src/visualize_graph_with_graphviz.py -f png,svg,pdf

# Show help for all options
uv run python src/visualize_graph_with_graphviz.py --help
```

**Command-line Options:**
- `-i, --input`: Path to transformations CSV (default: `output/transformations.csv`)
- `-c, --config`: Path to color config (default: `config/graph_colors.txt`)
- `-o, --output`: Output file path without extension (default: `output/graphs/transformation_graph`)
- `-f, --format`: Output format(s) - comma-separated: svg, png, pdf, dot (default: svg)
- `-t, --filter-type`: Filter to only include specific transformation type
- `-v, --verbose`: Enable verbose logging

#### Option 2: Interactive 3D Visualization (NetworkX + Matplotlib)

Generate an interactive 3D visualization that you can rotate, zoom, and pan:

```bash
# Display interactive 3D visualization (default behavior)
uv run python src/visualize_graph_3d.py

# Display with custom input path
uv run python src/visualize_graph_3d.py -i output/transformations.csv

# Display with custom color config
uv run python src/visualize_graph_3d.py -c config/graph_colors.txt

# Display with verbose logging
uv run python src/visualize_graph_3d.py -v

# Save visualization to file (optional)
uv run python src/visualize_graph_3d.py -o output/graphs/graph_3d.png

# Show help for all options
uv run python src/visualize_graph_3d.py --help
```

**Command-line Options:**
- `-i, --input`: Path to transformations CSV (default: `output/transformations.csv`)
- `-c, --config`: Path to color config (default: `config/graph_colors.txt`)
- `-o, --output`: Optional output file path to save figure (if not provided, only displays)
- `-v, --verbose`: Enable verbose logging

**3D Visualization Features:**
- **Interactive Controls**: Rotate with mouse drag, zoom with scroll wheel, pan with right-click drag
- **Spatial Layout**: Uses spring layout algorithm to position nodes in 3D space
- **Node Sizing**: Node size reflects importance (based on degree centrality - more connections = larger node)
- **Edge Coloring**: Edges colored by transformation type using the same color configuration as 2D graphs
- **Intermediate Nodes**: Multi-input transformations use small gray intermediate nodes
- **No System Dependencies**: Uses NetworkX and Matplotlib (already included), no need to install Graphviz

**Comparison: 2D vs 3D Visualization**

| Aspect | 2D (Graphviz) | 3D (NetworkX + Matplotlib) |
|--------|---------------|----------------------------|
| Layout | Hierarchical, static | Spring (force-directed), spatial |
| Interactivity | None (static images) | Full rotation, zoom, pan |
| Readability | Can be cluttered with large graphs | Better use of 3D space |
| Output | SVG, PNG, PDF files | Interactive window + optional save |
| Performance | Fast for large graphs | Slower layout computation |
| Filtering | By transformation type | All transformations |
| Best for | Detailed static analysis, print | Exploration and understanding |

**Customizing Colors:**

Edit `config/graph_colors.txt` to customize the colors for different transformation types (applies to both 2D and 3D visualizations):

```
# Example configuration
crafting=#4A90E2
smelting=#E67E22
smithing=#95A5A6
# ... etc
```

Colors can be hex codes (e.g., `#4A90E2`) or standard color names (e.g., `blue`).

**Performance Note:**

With 1961+ transformations, the full graph is very large and complex:
- **2D Graphviz**: Use the `-t` flag to filter by transformation type for better readability
- **3D Visualization**: Layout computation may take 5-30 seconds; interactive rotation remains smooth
- View SVG files in a browser for pan/zoom capabilities
- 3D visualization provides better spatial separation for large, interconnected graphs

## Output Format

### items.csv
```csv
item_name,item_url
Iron Ingot,https://minecraft.wiki/w/Iron_Ingot
Diamond,https://minecraft.wiki/w/Diamond
```

### transformations.csv
```csv
transformation_type,input_items,output_items,metadata
CRAFTING,"[{""name"":""Iron Ingot"",""url"":""...""}]","[{""name"":""Iron Block"",""url"":""...""}]",{}
SMELTING,"[{""name"":""Iron Ore"",""url"":""...""}]","[{""name"":""Iron Ingot"",""url"":""...""}]",{}
```

## Requirements

- Python >= 3.13
- uv package manager

## License

[Add license information]
