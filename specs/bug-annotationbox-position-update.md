# Bug: AnnotationBbox Position Update Error

## Bug Description
When using `--use-images` flag with 3D visualization and interacting with the plot (rotating, zooming, panning), the application crashes with repeated `AttributeError: 'AnnotationBbox' object has no attribute 'set_position'` errors in the console. The images do not update their positions correctly when the camera view changes, remaining static while the 3D axes rotate.

**Symptoms:**
- Multiple `AttributeError` exceptions in console when interacting with 3D plot
- Images appear frozen at initial positions during camera rotation/zoom
- Draw event handler fails to update image positions dynamically
- Error occurs in `update_image_positions()` function at line 632

**Expected Behavior:**
- Images should update their positions smoothly during camera rotation, zoom, and pan
- No errors should appear in console
- Images should maintain their apparent 3D positions while remaining camera-facing (billboard effect)

**Actual Behavior:**
- `AttributeError` thrown repeatedly on every draw event
- Images remain at initial screen positions despite camera movement
- Billboard effect is broken

## Problem Statement
The `update_image_positions()` event handler in `src/visualize_graph_3d.py` attempts to call `ab.set_position((x2, y2))` on an `AnnotationBbox` object, but this method does not exist in matplotlib's `AnnotationBbox` API. This causes the draw event handler to fail, preventing dynamic position updates during camera interaction.

## Solution Statement
Replace the incorrect `ab.set_position((x2, y2))` call with the correct matplotlib API for updating `AnnotationBbox` positions. The proper approach is to directly set the `xy` attribute of the `AnnotationBbox`, which represents the annotated point. Additionally, we should use `ab.xybox = (x2, y2)` and update `ab.xy = (x2, y2)` to ensure both the box position and annotation point are synchronized.

According to matplotlib documentation, `AnnotationBbox` uses:
- `xy`: The point being annotated (x, y) in data coordinates
- `xybox`: The position of the offsetbox in `boxcoords` system

The correct approach is to update both `ab.xy` and `ab.xybox` directly, then call `fig.canvas.draw_idle()` to trigger a redraw if needed.

## Steps to Reproduce
1. Download item images: `uv run python src/download_item_images.py --input output/items.csv --output-dir images/ --limit 10`
2. Run 3D visualization with images: `uv run python src/visualize_graph_3d.py --use-images --images-dir images/ --verbose`
3. Interact with the plot (click and drag to rotate, scroll to zoom)
4. Observe console output showing repeated `AttributeError` exceptions
5. Notice that images remain at fixed screen positions instead of updating with camera movement

## Root Cause Analysis
The root cause is in the `update_image_positions()` function (line 632 of `src/visualize_graph_3d.py`):

```python
def update_image_positions(event):
    """Update annotation box positions when the view changes."""
    for item in annotation_boxes:
        ab = item['ab']
        x, y, z = item['pos_3d']
        # Re-project 3D coordinates to current 2D screen coordinates
        x2, y2, _ = proj3d.proj_transform(x, y, z, ax.get_proj())
        ab.xybox = (x2, y2)
        ab.set_position((x2, y2))  # ← THIS METHOD DOES NOT EXIST
```

**Why This Fails:**
1. `AnnotationBbox` does not have a `set_position()` method in matplotlib's API
2. The documentation and examples show that position updates should be done by setting the `xy` attribute directly
3. Without proper position updates, the annotation boxes remain at their initial screen coordinates
4. The draw event handler fails silently (caught by matplotlib's event system), but logs errors

**Correct API Usage:**
According to matplotlib documentation for `AnnotationBbox`:
- `xy`: Property representing the annotated point (can be set directly)
- `xybox`: Property for the offset box position (already being set correctly)
- No `set_position()` method exists

The correct approach is:
```python
ab.xy = (x2, y2)      # Update annotated point
ab.xybox = (x2, y2)   # Update box position (already present)
```

## Relevant Files
Use these files to fix the bug:

- **src/visualize_graph_3d.py** (lines 622-635) - Contains the broken `update_image_positions()` function that incorrectly calls `ab.set_position()`. This function is connected to the draw event handler to update image positions during camera rotation. The fix requires replacing line 632 with the correct matplotlib API call.

- **tests/test_visualize_graph_3d.py** - Contains tests for the visualization functionality. No changes needed to tests, as the existing tests don't specifically test the draw event handler behavior during interaction. The tests pass because they don't trigger interactive draw events.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Fix the update_image_positions() Function
- Open `src/visualize_graph_3d.py` and navigate to line 632
- Remove the incorrect line: `ab.set_position((x2, y2))`
- Replace it with the correct matplotlib API: `ab.xy = (x2, y2)`
- Keep the existing `ab.xybox = (x2, y2)` line (line 631) - this is correct
- The function should now correctly update both `xy` and `xybox` properties

### 2. Test the Fix Manually
- Run the visualization with images: `uv run python src/visualize_graph_3d.py --use-images --images-dir images/ --verbose`
- Interact with the 3D plot by:
  - Rotating the view (click and drag)
  - Zooming in and out (scroll wheel)
  - Panning (right-click and drag, if supported)
- Verify that:
  - No `AttributeError` exceptions appear in the console
  - Images update their screen positions smoothly during interaction
  - Images maintain their apparent 3D positions (billboard effect works)
  - The visualization remains responsive and smooth

### 3. Test Without Images (Fallback Mode)
- Run visualization without images: `uv run python src/visualize_graph_3d.py --verbose`
- Verify that the visualization still works correctly with colored spheres
- Ensure no errors occur (the draw handler should only be attached when images are present)

### 4. Run Existing Tests
- Run the visualization test suite: `uv run pytest tests/test_visualize_graph_3d.py -v`
- Verify all 43 tests pass
- Confirm no regressions were introduced

### 5. Run Full Test Suite
- Run all tests: `uv run pytest tests/ -v`
- Verify that the existing pass/fail status is maintained (154 passing, 4 pre-existing Graphviz failures)
- Ensure the fix doesn't introduce new test failures

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `uv run python src/download_item_images.py --input output/items.csv --output-dir images/ --limit 10 --verbose` - Ensure test images are available
- `uv run python src/visualize_graph_3d.py --use-images --images-dir images/ --verbose` - Run visualization with images and manually verify no AttributeError in console when interacting
- `uv run python src/visualize_graph_3d.py --verbose` - Run visualization without images to verify fallback mode works
- `uv run pytest tests/test_visualize_graph_3d.py -v` - Run visualization tests to verify zero regressions
- `uv run pytest tests/ -v` - Run full test suite to verify zero regressions

## Notes

### Matplotlib AnnotationBbox API
The `AnnotationBbox` class in matplotlib has the following relevant attributes for position control:
- `xy`: The point (x, y) being annotated. Can be set directly as a property.
- `xybox`: The location (x, y) of the offsetbox, in `boxcoords` coordinates.
- `xycoords`: Coordinate system for `xy` (default: 'data')
- `boxcoords`: Coordinate system for `xybox` (default: 'offset points')

**No `set_position()` method exists.** Position updates are done by directly setting the `xy` attribute.

### Why the Original Implementation Failed
The original implementation attempted to call a non-existent method:
```python
ab.set_position((x2, y2))  # AttributeError!
```

This method doesn't exist in matplotlib's `AnnotationBbox` class. The developer likely assumed it existed based on other matplotlib objects that do have `set_position()` methods (like certain patch objects).

### Correct Implementation
```python
ab.xy = (x2, y2)      # Set the annotated point
ab.xybox = (x2, y2)   # Set the box position
```

Both properties need to be updated to ensure the annotation box follows the 3D point correctly during camera transformations.

### Testing Considerations
- The bug only manifests during interactive use (draw events)
- Automated tests don't trigger this code path (they use non-interactive backends)
- Manual testing is essential to verify the fix
- Look for smooth image movement during rotation/zoom
- Verify no console errors appear during interaction

### Performance Implications
- The draw event handler runs frequently during interaction
- Simple attribute assignments (`ab.xy = ...`) are lightweight operations
- No performance degradation expected from this fix
- The handler already uses efficient 3D-to-2D projection via `proj3d.proj_transform()`
