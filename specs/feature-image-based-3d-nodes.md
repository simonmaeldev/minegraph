# Feature: Image-Based 3D Node Visualization

## Feature Description
Enhance the 3D graph visualization to display actual Minecraft item images as textured planes instead of simple colored spheres for nodes. This feature will download item images from the Minecraft Wiki, cache them locally with standardized filenames, and render them as 3D textured surfaces in the interactive visualization, making the graph more visually intuitive and recognizable.

## User Story
As a user exploring the Minecraft transformation network
I want to see actual item images instead of abstract nodes
So that I can immediately recognize items without reading labels and better understand the transformation relationships visually

## Problem Statement
The current 3D visualization uses simple colored spheres to represent items, which requires users to hover over nodes to identify items. For a game-centric graph where visual recognition is important, displaying the actual item images from the wiki would significantly improve usability and make the visualization more engaging and intuitive.

## Solution Statement
Implement a three-part solution:
1. Create an image downloader that fetches item images from Minecraft Wiki pages (from the 'infobox' div, excluding inventory images), saves them with standardized lowercase underscore-separated filenames in a dedicated images directory
2. Modify the 3D visualization to load these images and display them as textured flat planes in 3D space instead of sphere markers
3. Implement proper error handling and fallback to colored spheres when images are unavailable

## Relevant Files
Use these files to implement the feature:

- **src/visualize_graph_3d.py** - Main 3D visualization script that needs modification to load and render images as textures instead of sphere nodes. Contains the `render_3d_graph()` function and graph layout logic.

- **output/items.csv** - Contains item names and their wiki URLs. This will be the data source for downloading images, mapping item names to their wiki pages.

- **config/graph_colors.txt** - Color configuration that will be used as fallback when images cannot be loaded or for edge coloring.

- **tests/test_visualize_graph_3d.py** - Test suite that needs updates to test image loading, texture rendering, and fallback behavior.

- **src/core/data_models.py** - Data models for items and transformations (for reference, may need to verify item name standardization).

- **README.md** - Documentation that needs updates to describe the new image-based visualization feature and image download process.

### New Files

- **src/download_item_images.py** - New standalone script to download item images from wiki pages, parse HTML to find the correct infobox image (not inventory images), and save with standardized filenames.

- **images/** - New directory to store downloaded item images with names formatted as `{item_name_lowercase_with_underscores}.png`

- **tests/test_download_item_images.py** - Test suite for image downloading functionality including HTML parsing, URL extraction, filename standardization, and error handling.

## Implementation Plan

### Phase 1: Foundation
Create the image downloading infrastructure that can fetch, parse, and save item images from Minecraft Wiki pages with proper caching, error handling, and filename standardization.

### Phase 2: Core Implementation
Implement the image texture rendering in the 3D visualization using matplotlib's image loading capabilities and 3D plane surfaces, replacing the current sphere-based node rendering.

### Phase 3: Integration
Integrate the image loader into the visualization pipeline with fallback mechanisms, update tests to cover the new functionality, and update documentation to guide users through the new image-based visualization.

## Step by Step Tasks

### 1. Set Up Image Storage Infrastructure
- Create `images/` directory in the project root
- Add `images/` to .gitignore with a comment explaining it contains cached wiki images
- Verify write permissions and directory accessibility

### 2. Implement Image Downloader Core
- Create `src/download_item_images.py` with argument parsing for input CSV and output directory
- Implement `load_items_from_csv()` function to read items.csv and extract item names and URLs
- Implement `standardize_filename()` function to convert item names to lowercase with underscores (e.g., "Iron Ingot" -> "iron_ingot.png")
- Add logging configuration with verbose mode support

### 3. Implement Wiki Image Extraction
- Implement `extract_image_url_from_page()` function using BeautifulSoup to parse wiki HTML
- Find the div with class 'infobox' (not 'infobox-invimages')
- Extract the image URL from the first img tag within the infobox
- Handle edge cases: missing infobox, missing image, multiple infoboxes
- Add comprehensive error handling and logging for failed extractions

### 4. Implement Image Download and Caching
- Implement `download_image()` function to fetch images from extracted URLs using requests library
- Save images to the standardized filename in the images directory
- Implement caching logic: skip download if file already exists
- Add file size validation (warn if image is suspiciously small/large)
- Handle HTTP errors, timeouts, and network failures gracefully

### 5. Create Image Download Script Entry Point
- Implement `main()` function with argparse for CLI interface
- Add options: `--input` (items CSV path), `--output-dir` (images directory), `--force-redownload` (skip cache), `--verbose`
- Add progress tracking with item counter (e.g., "Processing 150/850 items...")
- Generate summary report: successful downloads, cached items, failures
- Add dry-run mode for testing without actually downloading

### 6. Test Image Download Functionality
- Create `tests/test_download_item_images.py`
- Test filename standardization with various item names (spaces, special characters, unicode)
- Test HTML parsing with mock wiki pages (valid infobox, missing infobox, inventory images only)
- Test image downloading with mocked requests (success, 404, timeout, network error)
- Test caching behavior (skip existing files, force redownload flag)
- Test end-to-end with a small subset of real items

### 7. Implement Image Loading in 3D Visualization
- Add `load_item_image()` helper function in `visualize_graph_3d.py` to load PNG images using matplotlib.image.imread()
- Implement fallback logic: if image file doesn't exist, return None
- Add image cache dictionary to avoid reloading the same image multiple times during rendering
- Handle PIL/image loading errors gracefully with logging

### 8. Implement 3D Image Texture Rendering
- Research matplotlib's approach to displaying images in 3D space (likely using `plot_surface` or custom artists)
- Implement `create_image_plane()` function to create a textured 3D plane from an image array
- Calculate appropriate plane size based on node size (scale with degree centrality)
- Position planes at node coordinates with camera-facing orientation (billboard effect)
- Handle alpha transparency for PNG images

### 9. Modify Graph Rendering Pipeline
- Update `render_3d_graph()` to attempt loading images for all item nodes
- Replace sphere scatter plots with image planes for nodes with available images
- Keep sphere rendering as fallback for nodes without images (intermediate nodes, missing images)
- Maintain consistent sizing logic (images scaled based on node_sizes dictionary)
- Preserve hover annotation functionality for both image and sphere nodes

### 10. Update Color and Edge Rendering
- Ensure edge rendering remains unchanged (edges should still be colored by transformation type)
- Keep intermediate nodes as small gray spheres (no images for intermediate nodes)
- Maintain existing color configuration system for fallback sphere nodes
- Test that edge transparency and colors work correctly with mixed image/sphere nodes

### 11. Test Image Visualization Functionality
- Update `tests/test_visualize_graph_3d.py` to include image loading tests
- Test image loading with valid and invalid file paths
- Test fallback behavior when images are missing
- Test image plane creation and sizing
- Test mixed rendering (some nodes with images, some without)
- Verify hover annotations still work with image-based nodes
- Test performance with large number of image textures

### 12. Add Command-Line Options
- Add `--use-images` flag to `visualize_graph_3d.py` to enable/disable image rendering
- Add `--images-dir` option to specify custom image directory (default: `images/`)
- Update argument parser with new options and help text
- Ensure backward compatibility (images optional, spheres as default)

### 13. Update Documentation
- Update README.md with new "Download Item Images" section before "Visualize Transformation Graph"
- Document the image download process and command-line options
- Add instructions for the two-step workflow: 1) download images, 2) visualize with images
- Update 3D visualization section with `--use-images` flag documentation
- Add troubleshooting section for image download and rendering issues
- Include notes about image caching and storage requirements

### 14. Performance Testing and Optimization
- Test 3D visualization performance with full dataset (1961+ transformations, 850+ items)
- Profile image loading time and memory usage
- Optimize image cache to prevent memory bloat
- Consider image resolution limits (downscale large images if needed)
- Add performance notes to README with recommendations for large graphs

### 15. Validation and Final Testing
- Run image downloader on full items.csv dataset
- Verify all images are downloaded and correctly named
- Run 3D visualization with `--use-images` flag
- Verify visual quality and performance
- Test all interactive features (rotate, zoom, pan, hover) with images
- Run full test suite to ensure zero regressions
- Validate with multiple sample subsets of items

## Testing Strategy

### Unit Tests

**Image Download Module:**
- `test_standardize_filename()` - Various item names with spaces, capitals, special characters
- `test_load_items_from_csv()` - CSV parsing with valid/malformed data
- `test_extract_image_url_from_page()` - HTML parsing with various page structures
- `test_download_image()` - Mocked HTTP requests with success/failure scenarios
- `test_caching_behavior()` - Verify existing files are skipped unless force flag used

**3D Visualization Module:**
- `test_load_item_image()` - Image loading with valid/invalid paths, various formats
- `test_image_plane_creation()` - Plane geometry and texture mapping
- `test_fallback_rendering()` - Verify spheres used when images unavailable
- `test_image_cache()` - Verify images loaded once and reused

### Integration Tests

**End-to-End Image Download:**
- Test downloading images for a small subset of items (5-10 items)
- Verify files created with correct names in correct directory
- Verify caching works across multiple runs
- Test summary report generation

**End-to-End Visualization:**
- Build graph from test CSV with known items
- Download images for test items
- Render 3D visualization with images enabled
- Verify no errors and proper rendering
- Test with mixed scenarios (some images present, some missing)

### Edge Cases

- Item names with special characters, unicode, or punctuation
- Wiki pages with missing infoboxes or images
- Network failures during image download
- Corrupted or invalid image files
- Very large or very small images
- Items with multiple infoboxes on wiki page
- Concurrent access to image cache
- Extremely large graphs with memory constraints
- Image rendering with different matplotlib backends

## Acceptance Criteria

1. Image downloader successfully fetches images from Minecraft Wiki for all items in items.csv
2. Images are saved with standardized lowercase underscore-separated filenames in the `images/` directory
3. Image downloader implements caching and skips already-downloaded images
4. 3D visualization successfully loads and displays item images as textured planes in 3D space
5. Nodes without available images fall back to the original colored sphere rendering
6. Interactive features (rotate, zoom, pan, hover annotations) continue to work with image-based nodes
7. Performance remains acceptable with full dataset (1961+ transformations)
8. All existing tests pass with zero regressions
9. New tests provide comprehensive coverage of image download and rendering functionality
10. Documentation clearly explains the two-step process (download images, then visualize)
11. Command-line interface is intuitive with helpful error messages
12. The `--use-images` flag allows users to toggle between image and sphere rendering

## Validation Commands

Execute every command to validate the feature works correctly with zero regressions.

```bash
# Install any new dependencies (if added)
uv sync

# Run all existing tests to ensure no regressions
uv run pytest tests/ -v

# Test image downloader with a small subset (first 10 items for quick validation)
uv run python src/download_item_images.py --input output/items.csv --output-dir images/ --verbose

# Download all item images
uv run python src/download_item_images.py --input output/items.csv --output-dir images/

# Verify images directory contains PNG files
ls -lh images/ | head -20

# Test 3D visualization with images enabled
uv run python src/visualize_graph_3d.py --use-images --images-dir images/ --verbose

# Test 3D visualization without images (backward compatibility)
uv run python src/visualize_graph_3d.py --verbose

# Test with custom output save
uv run python src/visualize_graph_3d.py --use-images --images-dir images/ --output output/graphs/graph_3d_with_images.png

# Run specific image download tests
uv run pytest tests/test_download_item_images.py -v

# Run specific 3D visualization tests
uv run pytest tests/test_visualize_graph_3d.py -v

# Run all tests again to confirm everything works
uv run pytest tests/ -v
```

## Notes

### Image URL Extraction Strategy
The Minecraft Wiki uses consistent HTML structure with infoboxes containing item images. The key challenge is distinguishing between the full-size item image (in the main infobox) and the smaller inventory icon (in 'infobox-invimages'). The parser should target the main infobox first and extract the largest available image.

### Matplotlib 3D Image Rendering Considerations
Matplotlib's 3D capabilities are primarily designed for scientific visualization, not game-like graphics. Rendering images in 3D space may require creative approaches:
- **Option A**: Use `imshow` with transformed coordinates to create billboard-style image planes that face the camera
- **Option B**: Use `plot_surface` with the image as a texture on a flat surface mesh
- **Option C**: Use custom artists to draw images at projected 3D positions

Research during implementation will determine the best approach based on performance and visual quality.

### Memory and Performance Considerations
With 850+ unique items, loading all images into memory could be significant:
- Each PNG might be 50-500KB, totaling 40-400MB for all images
- Consider lazy loading images only when nodes are visible
- Implement image resolution limits (e.g., downscale to max 128x128 pixels)
- Use image compression if memory becomes an issue
- Profile memory usage during testing phase

### Future Enhancements
- **Smart image scaling**: Vary image size more dramatically based on node importance
- **Image quality tiers**: Use higher resolution images when zoomed in
- **Animated textures**: Rotate or pulse important nodes to draw attention
- **Custom image overlays**: Add borders or effects to distinguish transformation types
- **Web export**: Generate interactive HTML with three.js for web browser viewing with full image support
- **Image preprocessing**: Pre-generate optimized image sets with alpha channels and consistent sizes
- **Legend with images**: Show sample item images in a legend with transformation type colors

### Dependency Management
This feature should not require additional Python dependencies beyond what's already in pyproject.toml:
- `requests` - Already included for HTTP requests (image download)
- `beautifulsoup4` - Already included for HTML parsing (image URL extraction)
- `matplotlib` - Already included for visualization (image rendering in 3D)
- `Pillow` - Typically included with matplotlib for image handling

If Pillow is not available, add it with: `uv add Pillow`

### Backward Compatibility
The feature should be fully backward compatible:
- Default behavior remains unchanged (sphere nodes)
- Images only rendered when `--use-images` flag is used
- Existing visualization code paths remain functional
- No breaking changes to command-line interface
- All existing tests continue to pass
