# Minegraph

A Python-based data extraction system for Minecraft Java Edition transformation recipes. Minegraph downloads and parses wiki pages to build a comprehensive directed graph of all item transformations in the game.

## Purpose

Minegraph extracts transformation data from the Minecraft Wiki to create structured datasets showing how items can be transformed through various game mechanics:

- **Bartering** (piglin bartering)
- **Brewing** (potions)
- **Composting** (organic items to bone meal)
- **Crafting** (shaped and shapeless recipes)
- **Grindstone** (disenchanting)
- **Mob drops** (with probabilities)
- **Smelting** (furnace, blast furnace, smoker)
- **Smithing** (netherite upgrades, armor trims)
- **Stonecutting**
- **Trading** (villager trades)

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

### Download Item Images

Before visualizing graphs with images, download item images from Minecraft Wiki:

```bash
# Download all item images (recommended - run once)
uv run python src/download_item_images.py --input output/items.csv --output-dir images/

# Download with verbose logging to see progress
uv run python src/download_item_images.py --input output/items.csv --output-dir images/ --verbose

# Download first 10 items only (for testing)
uv run python src/download_item_images.py --input output/items.csv --output-dir images/ --limit 10

# Force re-download existing images
uv run python src/download_item_images.py --input output/items.csv --output-dir images/ --force-redownload

# Dry run (simulate without downloading)
uv run python src/download_item_images.py --dry-run

# Show help for all options
uv run python src/download_item_images.py --help
```

**Command-line Options:**
- `--input`: Path to items CSV file (default: `output/items.csv`)
- `--output-dir`: Directory to save images (default: `images/`)
- `--force-redownload`: Force re-download of existing images
- `--convert-gifs`: Automatically convert GIF files to PNG format (default: enabled)
- `--no-convert-gifs`: Disable automatic GIF to PNG conversion
- `--verbose`: Enable verbose logging
- `--dry-run`: Simulate downloads without actually downloading
- `--delay`: Delay between downloads in seconds (default: 0.5)
- `--limit`: Limit number of items to process (for testing)

**Notes:**
- Images are cached locally in the `images/` directory (excluded from git)
- Already downloaded images are skipped (unless `--force-redownload` is used)
- Images are saved with standardized filenames (e.g., `iron_ingot.png`)
- The script downloads the main infobox image from each wiki page
- **GIF images are automatically converted to PNG format** for matplotlib compatibility
  - Some items (banners, chests, campfire, clock, compass) are provided as GIF files by the wiki
  - The conversion uses ffmpeg to extract the first frame and convert to PNG
  - This ensures compatibility with the 3D visualization feature
  - Requires `ffmpeg` to be installed on your system
- With 850+ items, full download may take 5-10 minutes
- Failed downloads are logged but don't stop the process

### Visualize Transformation Graph

Minegraph provides three visualization options: **static 2D graphs** (Graphviz), **interactive 3D graphs** (NetworkX + Matplotlib), and **interactive web-based graphs** (Cosmograph).

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
# Interactive mode (default) - displays fzf menu to select options
uv run python src/visualize_graph_3d.py

# Bypass interactive mode with direct flags
uv run python src/visualize_graph_3d.py --use-images --verbose

# Filter by specific transformation types (comma-separated)
uv run python src/visualize_graph_3d.py --filter-type=crafting,smelting

# Disable interactive prompts (for scripting/automation)
uv run python src/visualize_graph_3d.py --no-interactive

# Display with images from custom directory
uv run python src/visualize_graph_3d.py --use-images --images-dir my_images/

# Display with custom input path
uv run python src/visualize_graph_3d.py -i output/transformations.csv

# Display with custom color config
uv run python src/visualize_graph_3d.py -c config/graph_colors.txt

# Save visualization to file (optional)
uv run python src/visualize_graph_3d.py -o output/graphs/graph_3d.png

# Full example: direct flags + filtering + save
uv run python src/visualize_graph_3d.py --use-images -v --filter-type=crafting,smelting -o output/graphs/filtered_3d.png

# Show help for all options
uv run python src/visualize_graph_3d.py --help
```

**Interactive Mode (New!):**

When you run the script without flags, an interactive fzf-based menu appears allowing you to:
- Select visualization options (use-images, verbose) with checkboxes
- Filter by transformation types (multi-select)
- Avoid memorizing command-line flags

To bypass interactive mode, either:
- Provide explicit flags on the command line (e.g., `--use-images --verbose`)
- Use the `--no-interactive` flag for scripting/automation

**Command-line Options:**
- `-i, --input`: Path to transformations CSV (default: `output/transformations.csv`)
- `-c, --config`: Path to color config (default: `config/graph_colors.txt`)
- `-o, --output`: Optional output file path to save figure (if not provided, only displays)
- `-v, --verbose`: Enable verbose logging
- `--use-images`: Use item images instead of colored spheres for nodes
- `--images-dir`: Directory containing item images (default: `images/`)
- `--filter-type`: Filter by transformation types (comma-separated, e.g., `crafting,smelting`)
- `--no-interactive`: Disable interactive fzf prompts and use defaults/CLI args only

**3D Visualization Features:**
- **Interactive Controls**: Rotate with mouse drag, zoom with scroll wheel, pan with right-click drag
- **Spatial Layout**: Uses spring layout algorithm to position nodes in 3D space
- **Node Sizing**: Node size reflects importance (based on degree centrality - more connections = larger node)
- **Image-Based Nodes**: Display actual Minecraft item images instead of abstract spheres (`--use-images` flag)
- **Hover Annotations**: Hover over nodes to see item names
- **Fallback Rendering**: Items without images automatically fall back to colored spheres
- **Edge Coloring**: Edges colored by transformation type using the same color configuration as 2D graphs
- **Intermediate Nodes**: Multi-input transformations use small gray intermediate nodes
- **No System Dependencies**: Uses NetworkX and Matplotlib (already included), no need to install Graphviz

#### Option 3: Interactive Web-Based Visualization (Cosmograph)

Generate GPU-accelerated interactive graph visualizations in Jupyter notebooks:

```bash
# First, ensure dependencies are installed
uv add cosmograph jupyter

# Start Jupyter notebook
uv run jupyter notebook notebooks/cosmograph_visualization.ipynb

# Alternative: Start JupyterLab
uv run jupyter lab
```

**Cosmograph Features:**
- **GPU-Accelerated Rendering**: Smooth 60 FPS animations even with 2000+ nodes
- **Modern Web Interface**: Zoom, pan, and hover in your browser
- **Force-Directed Layout**: Natural clustering of related items
- **Smart Node Sizing**: More connected items appear larger
- **Hover Tooltips**: See item names on hover
- **Directional Arrows**: Shows transformation flow
- **Color-Coded Edges**: Uses same color configuration as other visualizations
- **No System Dependencies**: Pure Python package, no Graphviz installation needed
- **Export to HTML**: Share interactive visualizations with others
- **Notebook Integration**: Combine analysis code with visualization

**Getting Started:**

1. Install dependencies: `uv add cosmograph jupyter`
2. Open the notebook: `uv run jupyter notebook notebooks/cosmograph_visualization.ipynb`
3. Execute all cells (Kernel → Restart & Run All)
4. Interact with the graph: zoom, pan, hover over nodes

The notebook includes examples for:
- Basic visualization with all transformations
- Filtering by transformation type
- Customizing colors and layout
- Exporting to HTML

**Comparison: 2D vs 3D vs Web Visualization**

| Aspect | 2D (Graphviz) | 3D (NetworkX + Matplotlib) | Web (Cosmograph) |
|--------|---------------|----------------------------|------------------|
| Layout | Hierarchical, static | Spring (force-directed), spatial | Force-directed, dynamic |
| Interactivity | None (static images) | Full rotation, zoom, pan | Zoom, pan, hover, drag |
| Performance | Fast for large graphs | Slower layout computation | GPU-accelerated, very smooth |
| Output | SVG, PNG, PDF files | Interactive window + optional save | Interactive notebook widget + HTML export |
| Environment | Command-line script | Command-line script | Jupyter notebook |
| Dependencies | System graphviz + Python package | NetworkX + Matplotlib | Pure Python (cosmograph) |
| Best for | Detailed static analysis, print | 3D exploration | Web-based exploration, sharing |
| Filtering | By transformation type (`-t` flag) | By transformation type (`--filter-type` flag) | Programmatic filtering in notebook |
| Option Selection | Command-line only | Interactive fzf menu or command-line | Jupyter cells |

**Customizing Colors:**

Edit `config/graph_colors.txt` to customize the colors for different transformation types (applies to all visualizations: 2D, 3D, and Cosmograph):

```
# Example configuration
crafting=#4A90E2
smelting=#E67E22
smithing=#95A5A6
# ... etc
```

Colors can be hex codes (e.g., `#4A90E2`) or standard color names (e.g., `blue`).

**Performance Note:**

With 2200+ transformations, the full graph is very large and complex:
- **2D Graphviz**: Use the `-t` flag to filter by transformation type for better readability
- **3D Visualization**: Use the `--filter-type` flag to focus on specific transformation types
- **Cosmograph**: GPU-accelerated, handles the full graph smoothly without filtering
- Layout computation may take 5-30 seconds for full graph in 2D/3D; filtering significantly improves performance
- Interactive rotation remains smooth even with large graphs
- View SVG files in a browser for pan/zoom capabilities
- Cosmograph provides the best performance for exploring the complete graph interactively

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
