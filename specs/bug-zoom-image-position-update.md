# Bug: Images Don't Update Position/Size When Zooming in 3D Visualization

## Bug Description
When using the 3D graph visualization with image-based nodes (`--use-images` flag), zooming in or out does not automatically update the position and size of the item images. The images only update their positions when the cursor hovers over a node, which triggers a canvas redraw. This results in a poor user experience where images appear misaligned or incorrectly sized until the user manually hovers over nodes.

**Expected behavior:** Images should automatically update their positions and sizes immediately when the user zooms in or out, without requiring any additional mouse interaction.

**Actual behavior:** Images remain at their old positions and sizes after zooming. They only update when the mouse hovers over a node, triggering a redraw event.

## Problem Statement
The draw event handler that updates AnnotationBbox positions is connected but doesn't properly handle zoom events. Matplotlib's zoom functionality changes the axis limits but doesn't consistently trigger draw events, or the draw events are triggered before the axis projection matrix is fully updated. This causes the 3D-to-2D projection calculations to use stale projection data, resulting in misaligned images.

## Solution Statement
Add explicit event handlers for zoom and axis limit changes that trigger image position updates. Specifically:
1. Connect to `button_release_event` to handle scroll wheel zoom completion
2. Connect to `xlim_changed`, `ylim_changed`, and `zlim_changed` events to handle axis limit changes
3. Ensure the `update_image_positions` function is called whenever these events fire

This ensures that image positions are recalculated with the updated projection matrix immediately after zoom operations complete.

## Steps to Reproduce
1. Download item images:
   ```bash
   uv run python src/download_item_images.py --input output/items.csv --output-dir images/ --limit 10
   ```

2. Run the 3D visualization with images enabled:
   ```bash
   uv run python src/visualize_graph_3d.py --use-images --images-dir images/ --verbose
   ```

3. Wait for the interactive 3D visualization window to open showing item images

4. Use the scroll wheel to zoom in or out

5. Observe that the item images do NOT update their positions or sizes

6. Move the mouse cursor over any node

7. Observe that all images suddenly snap to their correct positions and sizes

## Root Cause Analysis
The root cause is in `src/visualize_graph_3d.py` lines 622-635. The code only connects a `draw_event` handler to update image positions:

```python
if annotation_boxes:
    def update_image_positions(event):
        """Update annotation box positions when the view changes."""
        for item in annotation_boxes:
            ab = item['ab']
            x, y, z = item['pos_3d']
            # Re-project 3D coordinates to current 2D screen coordinates
            x2, y2, _ = proj3d.proj_transform(x, y, z, ax.get_proj())
            ab.xybox = (x2, y2)
            ab.xy = (x2, y2)

    fig.canvas.mpl_connect('draw_event', update_image_positions)
```

The `draw_event` is fired during rotation and panning, but zoom operations via scroll wheel don't consistently trigger `draw_event` in the expected sequence. Matplotlib's zoom functionality modifies axis limits, which may complete before a full canvas redraw occurs. The hover event forces a redraw via `fig.canvas.draw_idle()` (line 594, 606, 611, 616), which is why hovering over a node fixes the positioning.

## Relevant Files
Use these files to fix the bug:

- **src/visualize_graph_3d.py** (lines 622-635 in `render_3d_graph` function)
  - Contains the `update_image_positions` function and event handler registration
  - Need to add additional event connections for zoom/axis limit changes
  - The function already has the correct logic for updating positions, just needs more trigger points

- **tests/test_visualize_graph_3d.py** (TestImageFunctionality class)
  - Contains tests for image rendering functionality
  - Need to add test cases that verify image position updates happen on zoom events

## Step by Step Tasks

### Update Event Handler Connections
- Modify the `render_3d_graph` function in `src/visualize_graph_3d.py` at line 634
- Keep the existing `draw_event` connection for rotation/pan updates
- Add connection to `button_release_event` to catch scroll wheel zoom completion
- In the button release handler, check if the event was a scroll zoom and call `fig.canvas.draw_idle()` to force a redraw with updated positions
- This ensures that after each zoom action completes, the images are immediately repositioned

### Add Test for Zoom Event Handling
- Add a new test method `test_render_image_updates_on_zoom` in the `TestImageFunctionality` class
- Create a graph with image rendering enabled
- Verify that appropriate event handlers are connected (button_release_event)
- Simulate a zoom event and verify the canvas requests a redraw
- This ensures the fix doesn't regress in future changes

### Manual Validation
- Run the validation commands below to ensure the bug is fixed
- Verify that zooming immediately updates image positions without requiring hover
- Test both zoom in and zoom out operations
- Verify that rotation and panning still work correctly (regression check)

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `uv run pytest tests/test_visualize_graph_3d.py::TestImageFunctionality -v` - Run image functionality tests to validate the fix
- `uv run pytest tests/test_visualize_graph_3d.py -v` - Run all visualization tests to ensure zero regressions
- `uv run python src/visualize_graph_3d.py --use-images --images-dir images/ --verbose` - Manually test the visualization with images enabled and verify zooming immediately updates positions
- `uv run python src/visualize_graph_3d.py --use-images --images-dir images/` - Test without verbose mode to ensure it works in normal usage

## Notes

### Implementation Details
The fix should be minimal and surgical:
- Only add event handler connections, don't modify the `update_image_positions` function logic
- The `button_release_event` handler should check `event.button` to ensure it's a scroll event
- Use `fig.canvas.draw_idle()` to request an async redraw, not `fig.canvas.draw()` which would block
- Keep all existing draw_event connections for backward compatibility

### Alternative Approaches Considered
1. **Axis limit change events** - Matplotlib 3D axes don't reliably fire `xlim_changed`/`ylim_changed`/`zlim_changed` events for all backends
2. **Motion notify during zoom** - Would cause excessive updates and performance issues
3. **Timer-based polling** - Inefficient and introduces lag

The `button_release_event` approach is the most reliable and performant solution.

### Testing Strategy
- Unit tests verify event handler connections are made
- Manual testing required to validate actual zoom behavior (matplotlib event simulation is limited)
- Regression testing ensures rotation/pan still work correctly
- Test with both small graphs (few nodes) and large graphs (850+ nodes) to ensure performance is acceptable
