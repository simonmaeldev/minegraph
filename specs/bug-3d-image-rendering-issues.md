# Bug: 3D Image Node Rendering Issues

## Bug Description
When using `--use-images` flag with the 3D visualization, images are not displayed correctly. Instead of showing the actual Minecraft item images, users see:
1. A single-color square (not the actual image texture)
2. Squares that do not face the camera (lack billboard effect)
3. Images that are too large relative to the graph size, causing overlap even without zooming

The current implementation uses `Poly3DCollection` with only the center pixel color extracted from the image, rather than properly rendering the full image as a billboard-style texture that faces the camera.

## Problem Statement
The `create_image_plane()` function in `src/visualize_graph_3d.py` (lines 135-192) incorrectly renders images by:
1. Only extracting the center pixel color (`center_color = image[h // 2, w // 2, :]`) instead of displaying the full image
2. Creating a static 3D polygon that doesn't rotate to face the camera (no billboard effect)
3. Using `Poly3DCollection` which doesn't support proper texture mapping in matplotlib 3D

Additionally, the scaling logic (line 156: `scale = np.sqrt(size) / 20`) makes images too large, causing them to overlap.

## Solution Statement
Replace the `Poly3DCollection` approach with matplotlib's `AnnotationBbox` and `OffsetImage` to create camera-facing 2D image overlays at 3D positions. This approach:
1. Displays the full image texture instead of a single color
2. Automatically faces the camera (billboard effect) since it's a 2D annotation in screen space
3. Uses `proj3d.proj_transform` to project 3D coordinates to 2D screen space
4. Provides better size control with a proper zoom parameter
5. Implements a draw event handler to update image positions during camera rotation

## Steps to Reproduce
1. Download item images: `uv run python src/download_item_images.py --input output/items.csv --output-dir images/ --limit 10`
2. Run 3D visualization with images: `uv run python src/visualize_graph_3d.py --use-images --images-dir images/`
3. Observe that:
   - Images appear as single-color squares instead of showing the full item texture
   - Squares don't rotate to face the camera when you rotate the view
   - Squares are too large and overlap each other

## Root Cause Analysis
The root cause is in the `create_image_plane()` function (lines 135-192 of `src/visualize_graph_3d.py`):

1. **Line 179-185**: Only the center pixel color is extracted from the image:
   ```python
   center_color = image[h // 2, w // 2, :]
   ```
   This results in a single-color polygon instead of the full image texture.

2. **Lines 163-168**: Creates a static 3D polygon that doesn't rotate with the camera:
   ```python
   verts = [
       [x - half_size, y - half_size, z],
       [x + half_size, y - half_size, z],
       ...
   ]
   ```
   This creates a fixed plane in 3D space that doesn't face the camera (no billboard effect).

3. **Line 156**: Incorrect scaling calculation:
   ```python
   scale = np.sqrt(size) / 20
   ```
   This makes images too large, causing overlaps without significant zoom.

4. **Fundamental approach issue**: Matplotlib's `Poly3DCollection` doesn't support texture mapping with images. The proper approach is to use 2D annotations (`AnnotationBbox` + `OffsetImage`) projected to 3D positions, which automatically face the camera.

## Relevant Files
Use these files to fix the bug:

- **src/visualize_graph_3d.py** (lines 135-192) - Contains the broken `create_image_plane()` function that needs to be rewritten. Also need to modify `render_3d_graph()` (lines 440-654) to use the new image rendering approach with `AnnotationBbox` instead of calling `create_image_plane()`.

- **tests/test_visualize_graph_3d.py** (lines 875-892) - Contains test for `create_image_plane()` that will need updates to reflect the new implementation approach.

- **output/transformations.csv** - Used for testing the visualization with real data.

- **output/items.csv** - Contains item names for downloading test images.

- **images/** - Directory containing downloaded Minecraft item images for testing.

- **config/graph_colors.txt** - Color configuration used for fallback spheres and edge colors.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Import Required Modules
- Add imports to the top of `src/visualize_graph_3d.py`:
  - `from matplotlib.offsetbox import OffsetImage, AnnotationBbox`
  - `from mpl_toolkits.mplot3d import proj3d`
- These modules are needed for the new image rendering approach

### 2. Replace create_image_plane() Function
- Delete the current `create_image_plane()` function (lines 135-192)
- Implement a new approach that doesn't use `create_image_plane()` at all
- Instead, modify `render_3d_graph()` to use `AnnotationBbox` with `OffsetImage` directly
- Images will be added as 2D annotations that are projected from 3D coordinates

### 3. Modify render_3d_graph() to Use AnnotationBbox Approach
- In `render_3d_graph()`, after line 482 where image cache is initialized, create a list to store annotation boxes:
  - `annotation_boxes = []`
- Replace the image rendering loop (lines 498-508) to use the new approach:
  - For each item with an image, create an `OffsetImage` from the image array
  - Calculate appropriate zoom factor based on node size: `zoom = np.sqrt(node_sizes[node]) / 1000.0`
  - Project 3D coordinates to 2D using `proj3d.proj_transform()`
  - Create `AnnotationBbox` with the `OffsetImage`, positioned at the projected 2D coordinates
  - Set `xycoords='data'`, `frameon=False`, `pad=0`, `box_alignment=(0.5, 0.5)`
  - Use `ax.add_artist()` to add the annotation box to the axes
  - Store the annotation box, node name, and 3D position in `annotation_boxes` list for later updates

### 4. Implement Draw Event Handler for Camera-Facing Updates
- After rendering all images, implement a draw event handler function:
  - Define `update_image_positions(event)` that iterates through `annotation_boxes`
  - For each annotation box, re-project the 3D position to current 2D screen coordinates
  - Update the annotation box position with `ab.xybox = (x2, y2)` and `ab.set_position((x2, y2))`
- Connect the handler with `fig.canvas.mpl_connect('draw_event', update_image_positions)`
- This ensures images remain facing the camera and positioned correctly during rotation

### 5. Update Scaling Logic for Appropriate Image Sizes
- Use a smaller zoom factor to prevent image overlap:
  - Change from `scale = np.sqrt(size) / 20` to `zoom = np.sqrt(size) / 1000.0`
  - This provides better scaling where images are visible but don't overlap without zooming
- Consider the relationship between node_sizes (range 50-500) and the desired image size
- The zoom parameter in `OffsetImage` controls the final rendered size

### 6. Ensure Fallback Spheres Still Render Correctly
- Verify that the fallback sphere rendering (lines 510-526) remains unchanged
- Ensure items without images still render as blue spheres
- Test that the invisible scatter plot for hover detection (lines 528-543) still works with the new image rendering

### 7. Update Tests for New Implementation
- Modify `test_create_image_plane_basic()` in `tests/test_visualize_graph_3d.py` (lines 875-892)
- Since `create_image_plane()` no longer exists, either:
  - Remove this test entirely (if no longer applicable)
  - Replace it with a test for the new annotation-based rendering approach
- Update the test name to `test_render_with_annotationbox_images()`
- Test that `AnnotationBbox` objects are created and added to the axes when images are available

### 8. Test Image Rendering with Small Dataset
- Download a small set of item images (10-20 items): `uv run python src/download_item_images.py --input output/items.csv --output-dir images/ --limit 10 --verbose`
- Run visualization with images: `uv run python src/visualize_graph_3d.py --use-images --images-dir images/ --verbose`
- Verify that:
  - Full images are displayed (not single-color squares)
  - Images face the camera when rotating the view
  - Images have appropriate size (visible but not overlapping)
  - Hover functionality still works

### 9. Test with Larger Dataset
- Download more images (50-100 items): `uv run python src/download_item_images.py --input output/items.csv --output-dir images/ --limit 50`
- Run visualization with the larger dataset
- Verify performance is acceptable and images render correctly
- Test rotation, zoom, and pan interactions

### 10. Verify Fallback Behavior
- Test with items that have no images to ensure fallback spheres render
- Verify mixed rendering (some nodes with images, some without)
- Ensure intermediate nodes still render as small gray spheres

### 11. Run All Tests
- Execute the full test suite: `uv run pytest tests/test_visualize_graph_3d.py -v`
- Verify all tests pass
- Fix any failing tests related to the implementation changes

### 12. Run Full Test Suite
- Execute all tests to ensure no regressions: `uv run pytest tests/ -v`
- Verify all tests pass with zero failures

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `uv sync` - Ensure all dependencies are installed
- `uv run pytest tests/ -v` - Run all tests before changes to establish baseline
- `uv run python src/download_item_images.py --input output/items.csv --output-dir images/ --limit 10 --verbose` - Download test images
- `ls -lh images/ | head -20` - Verify images were downloaded
- `uv run python src/visualize_graph_3d.py --use-images --images-dir images/ --verbose` - Test visualization with images after fix
- `uv run python src/visualize_graph_3d.py --verbose` - Test visualization without images (fallback mode)
- `uv run pytest tests/test_visualize_graph_3d.py -v` - Run visualization tests
- `uv run pytest tests/ -v` - Run all tests to validate zero regressions

## Notes

### Why AnnotationBbox Approach Works
The recommended solution uses `AnnotationBbox` with `OffsetImage` because:
1. **Proper image display**: `OffsetImage` displays the full image array, not just a color sample
2. **Automatic billboard effect**: Annotations exist in 2D screen space, so they automatically face the camera
3. **Native matplotlib support**: This is the standard approach for adding images to matplotlib plots
4. **Projection from 3D to 2D**: Using `proj3d.proj_transform()` correctly maps 3D positions to 2D screen coordinates
5. **Dynamic updates**: The draw event handler updates positions when the camera rotates

### Implementation References
The bug report included example code showing the correct approach:
```python
from mpl_toolkits.mplot3d import proj3d
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

# For each node:
img = Image.open(image_path)
img_array = np.array(img)

# Create OffsetImage that faces camera
imagebox = OffsetImage(img_array, zoom=your_zoom)
imagebox.image.axes = ax

# Create annotation with 3D coordinates
ab = AnnotationBbox(imagebox, (x, y, z),
                    xybox=(0, 0),
                    xycoords='data',
                    boxcoords="offset points",
                    frameon=False,
                    pad=0)

# Add with 2D projection
ax.add_artist(ab)

# Force update of positions after rotation
def update_image_positions(event):
    for ab in annotation_boxes:
        # Project 3D coordinates to 2D
        x2, y2, _ = proj3d.proj_transform(x, y, z, ax.get_proj())
        ab.xybox = (x2, y2)
        ab.set_position((x2, y2))

fig.canvas.mpl_connect('draw_event', update_image_positions)
```

### Why Current Implementation Fails
The current `Poly3DCollection` approach fundamentally cannot work because:
1. Matplotlib 3D doesn't support texture mapping on 3D polygons
2. `Poly3DCollection.set_facecolor()` only accepts a single color, not an image
3. 3D polygons don't automatically rotate to face the camera
4. The manual billboard calculation would require complex rotation matrices and camera position tracking

### Zoom Factor Tuning
The zoom factor needs experimentation to find the right balance:
- Too small: Images are tiny and hard to see
- Too large: Images overlap and clutter the visualization
- Recommended starting point: `zoom = np.sqrt(node_sizes[node]) / 1000.0`
- This maps node_sizes (50-500) to zoom values (0.007-0.022)
- Fine-tune based on visual testing with real data

### Performance Considerations
- `AnnotationBbox` is more efficient than trying to manually render textures
- The draw event handler runs on every redraw, but only updates positions (fast operation)
- With 850+ items, rendering may take a few seconds initially, but interaction remains smooth
- Images are cached in memory by the existing `image_cache` dictionary

### Edge Cases to Consider
- Empty images directory (should fall back to spheres)
- Corrupted image files (should log warning and fall back)
- Very large or very small node sizes (zoom should scale appropriately)
- Rotation and zoom interactions (draw handler should maintain correct positioning)
- Mixed rendering (images + spheres) should work seamlessly
