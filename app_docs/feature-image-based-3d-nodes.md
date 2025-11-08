# Image-Based 3D Node Visualization

**ADW ID:** feature-image-based-3d-nodes
**Date:** 2025-11-07
**Specification:** specs/feature-image-based-3d-nodes.md

## Overview

Enhanced the 3D graph visualization to display actual Minecraft item images as camera-facing textured annotations instead of simple colored spheres. The implementation uses matplotlib's `AnnotationBbox` and `OffsetImage` to render images that automatically update their positions during camera rotation, creating a billboard effect where images always face the viewer. Items without images fall back to colored sphere rendering.

## What Was Built

- **Camera-facing image rendering** - Images are rendered as 2D annotations in 3D space using matplotlib's AnnotationBbox approach
- **Dynamic position updates** - Draw event handler continuously updates image positions to maintain proper positioning during camera rotation
- **Automatic 3D-to-2D projection** - Uses `proj3d.proj_transform` to project 3D node coordinates to 2D screen space
- **Image zoom scaling** - Node size centrality affects image zoom factor for visual hierarchy
- **Hybrid rendering** - Supports mixed rendering with images for available items and spheres for fallback
- **Simplified architecture** - Removed complex `create_image_plane()` function in favor of matplotlib's built-in annotation system

## Technical Implementation

### Files Modified

- `src/visualize_graph_3d.py`: Replaced Poly3DCollection-based image plane rendering with AnnotationBbox approach
  - Removed `create_image_plane()` function (65 lines removed)
  - Added import for `proj3d` and `AnnotationBbox`/`OffsetImage`
  - Modified `render_3d_graph()` to use 2D projected coordinates for image positioning
  - Added draw event handler to update image positions during camera rotation
  - Implemented image scaling based on node size using zoom factor calculation

- `tests/test_visualize_graph_3d.py`: Removed obsolete test for deleted function
  - Removed `test_create_image_plane_basic()` test (20 lines removed)
  - Retained integration tests for image rendering functionality

### Key Changes

1. **Architecture Shift**: Moved from 3D polygon-based rendering to 2D annotation-based rendering with 3D coordinate projection
2. **Billboard Effect**: Images now automatically face the camera through AnnotationBbox positioning in screen space
3. **Dynamic Updates**: Draw event handler ensures images reposition correctly when the 3D view is rotated or zoomed
4. **Size Scaling**: Node size (based on degree centrality) now properly affects image display size through zoom factor
5. **Zoom Responsiveness**: Images scale proportionally with view zoom level - zooming in makes images larger, zooming out makes them smaller
6. **Code Simplification**: Removed 65 lines of complex plane creation code, replaced with ~30 lines using matplotlib's built-in capabilities

## How to Use

### Prerequisites
Ensure you have downloaded item images using the image downloader script (if available):
```bash
uv run python src/download_item_images.py --input output/items.csv --output-dir images/
```

### Running 3D Visualization with Images

1. **Enable image mode with default images directory:**
   ```bash
   uv run python src/visualize_graph_3d.py --use-images --verbose
   ```

2. **Specify custom images directory:**
   ```bash
   uv run python src/visualize_graph_3d.py --use-images --images-dir /path/to/images/ --verbose
   ```

3. **Save visualization to file:**
   ```bash
   uv run python src/visualize_graph_3d.py --use-images --output output/graph_with_images.png
   ```

4. **Fallback to sphere rendering (original behavior):**
   ```bash
   uv run python src/visualize_graph_3d.py
   ```

### Interactive Features
- **Rotate**: Click and drag to rotate the 3D view - images will automatically reposition to face the camera
- **Zoom**: Scroll to zoom in/out - images scale proportionally with zoom level and positions update dynamically
- **Pan**: Right-click and drag to pan the view
- **Hover**: Hover over nodes to see tooltips with item names and connection counts

## Configuration

### Command-Line Options
- `--use-images`: Enable image-based node rendering (default: False, uses spheres)
- `--images-dir PATH`: Directory containing item images (default: "images/")
- `--verbose`: Enable verbose logging to see image loading details
- `--output PATH`: Save the visualization to a file instead of displaying interactively

### Image Requirements
- Images must be PNG format
- Filenames should match item names (lowercase with underscores, e.g., "iron_ingot.png")
- Recommended image size: 128x128 pixels or smaller for optimal performance
- Images should have transparent backgrounds for best visual appearance

## Testing

### Running Tests
```bash
# Run all visualization tests
uv run pytest tests/test_visualize_graph_3d.py -v

# Run specific image functionality tests
uv run pytest tests/test_visualize_graph_3d.py::TestImageFunctionality -v
```

### Test Coverage
- Image loading with valid and missing files
- Image caching behavior
- Rendering with mixed image/sphere nodes
- Fallback behavior when images are unavailable
- Integration with existing graph rendering pipeline

## Notes

### Implementation Approach
The initial specification proposed using `Poly3DCollection` with texture mapping or custom 3D plane creation. After research and implementation, this approach proved overly complex and had limitations with matplotlib's 3D rendering capabilities. The final implementation uses matplotlib's 2D annotation system with 3D coordinate projection, which provides:
- Simpler code (net reduction of ~35 lines)
- Built-in billboard effect (images always face camera)
- Better performance (2D rendering is faster than 3D polygon rendering)
- More predictable behavior across different matplotlib backends

### Performance Considerations
- Image loading is cached to avoid redundant disk reads
- Images are loaded on-demand during graph rendering
- The draw event handler has minimal overhead as it only updates existing annotation positions
- For large graphs (850+ nodes), performance remains acceptable on modern hardware
- Consider reducing image resolution if memory usage becomes a concern

### Known Limitations
- Images are rendered in 2D screen space, not true 3D objects (by design for billboard effect)
- Image z-ordering may not perfectly match 3D depth in all camera angles
- Very large images (>500KB) may slow down initial loading
- The draw event handler is called frequently during rotation, which may cause slight lag on older hardware

### Future Enhancements
- Implement LOD (Level of Detail) system to use higher resolution images when zoomed in
- Add image preprocessing pipeline to standardize sizes and formats
- Implement smart z-ordering based on camera distance
- Add visual effects (borders, highlights, shadows) to images
- Support animated or multi-state images for special nodes
