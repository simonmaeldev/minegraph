# Feature: Dynamic Image Size Slider

## Feature Description
Add an interactive slider widget to the 3D graph visualization that allows users to dynamically control the size of item images in real-time. Currently, images have a good initial size when loading the graph, but become too large when zooming in. This feature will give users fine-grained control over image scaling, independent of the view zoom level, with a slider that ranges from the initial (small) size to the current zoomed-in (large) size.

## User Story
As a user exploring the 3D Minecraft transformation graph
I want to control the size of item images with a slider
So that I can adjust image sizes to my preference while zooming and navigating the graph, preventing images from becoming too large or too small

## Problem Statement
Based on user feedback with screenshots:
- **Image #1 (zoomed in)**: Images are too large and dominate the view, making it hard to see the graph structure
- **Image #2 (initial view)**: Images are appropriately sized and provide good balance between visibility and graph structure

The current implementation automatically scales images based on view zoom level (implemented in bug-image-zoom-not-responsive.md). While this provides responsive scaling, users need additional control because:
1. The automatic zoom multiplier can make images too large when zoomed in
2. Different users have different preferences for image size
3. Use cases vary - sometimes users want to focus on graph structure (smaller images), other times on item details (larger images)
4. The relationship between view zoom and image size may not always feel right for all zoom levels

## Solution Statement
Implement a matplotlib slider widget that provides a user-controlled scale factor for image sizes:

1. **Add slider widget** - Use `matplotlib.widgets.Slider` to create an interactive slider
2. **Define scale range** - Slider range from 0.5x (50% of base size, matching initial view) to 2.0x (200% of base size, matching zoomed view)
3. **Default value** - Start at 1.0x (100%, current behavior)
4. **Real-time updates** - Update all image sizes when slider value changes
5. **Combine with zoom** - Multiply slider scale with existing zoom multiplier: `final_zoom = base_zoom * zoom_multiplier * slider_scale`
6. **Persistent across interactions** - Slider value persists during rotation, pan, and zoom operations

This approach gives users full control while preserving the existing zoom-responsive behavior.

## Relevant Files
Use these files to implement the feature:

### Existing Files to Modify

- **src/visualize_graph_3d.py** (lines 1-803) - Main visualization script
  - Modify imports to include `matplotlib.widgets.Slider` (line 16)
  - Modify `render_3d_graph()` function (lines 382-674) to:
    - Create axes for slider widget (around line 404, after fig creation)
    - Initialize slider with appropriate range and default value
    - Store slider scale factor in a variable accessible to draw handler
    - Create slider event handler to update image sizes
  - Modify `update_image_positions()` function (lines 635-660) to:
    - Multiply zoom multiplier by slider scale factor when calculating new_zoom
    - Access slider scale from a closure or figure/axes attribute
  - Add slider update callback function to handle slider value changes

- **tests/test_visualize_graph_3d.py** - Test suite for visualization
  - Add tests for slider widget creation (verify slider exists, has correct range)
  - Add tests for slider callback functionality (verify images update on slider change)
  - Test edge cases (min value, max value, mid value)

### New Files

None - all changes are modifications to existing files

## Implementation Plan

### Phase 1: Foundation
1. Research matplotlib slider widget API and best practices for 3D figure integration
2. Determine optimal slider positioning (bottom of figure, doesn't overlap with 3D axes)
3. Define slider range based on user feedback (0.5x to 2.0x with 1.0x default)
4. Plan how slider scale factor will be stored and accessed by draw event handler

### Phase 2: Core Implementation
1. Add slider widget to the figure layout
2. Implement slider callback to update image sizes
3. Integrate slider scale with existing zoom multiplier logic
4. Test slider responsiveness and visual feedback

### Phase 3: Integration
1. Ensure slider works correctly with rotation, zoom, and pan operations
2. Verify slider state persists across all interactions
3. Add logging for slider value changes (verbose mode)
4. Update command-line help text to mention slider control

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Add Slider Widget Import
- Open `src/visualize_graph_3d.py`
- Add `from matplotlib.widgets import Slider` to the imports section (after line 16)
- This provides the Slider class for creating interactive slider widgets

### 2. Create Slider Axes and Widget
- In `render_3d_graph()` function (around line 404, after `fig = plt.figure(figsize=(16, 12))`)
- Adjust the 3D axes to make room for slider:
  - Change `ax = fig.add_subplot(111, projection='3d')` to use specific position
  - Use `ax = fig.add_subplot(111, projection='3d', position=[0.05, 0.15, 0.9, 0.8])`
  - This creates space at bottom (0.15 from bottom edge, 0.8 height leaves room)
- Create slider axes below the 3D plot:
  - `slider_ax = fig.add_axes([0.2, 0.05, 0.6, 0.03])` (left=0.2, bottom=0.05, width=0.6, height=0.03)
- Create the slider widget:
  - `image_size_slider = Slider(slider_ax, 'Image Size', 0.5, 2.0, valinit=1.0, valstep=0.1)`
  - Range: 0.5x (min) to 2.0x (max), default: 1.0x, step: 0.1x increments
- Add slider styling:
  - Customize color: `slider_ax.set_facecolor('#f0f0f0')`

### 3. Store Slider Scale Factor
- Create a mutable container to store slider value that can be accessed from callbacks
- Use a list with single element (mutable) or dict: `slider_scale = [1.0]` (after slider creation)
- This allows the value to be modified inside nested functions

### 4. Modify update_image_positions() to Use Slider Scale
- Locate the `update_image_positions()` function (lines 635-660)
- Find the line that calculates `new_zoom`: `new_zoom = base_zoom * zoom_multiplier` (around line 653)
- Change to: `new_zoom = base_zoom * zoom_multiplier * slider_scale[0]`
- This applies both the automatic zoom multiplier AND the user's slider scale

### 5. Create Slider Callback Function
- After the `update_image_positions()` function definition (around line 661)
- Define slider callback:
  ```python
  def on_slider_change(val):
      """Handle slider value changes to update image sizes."""
      slider_scale[0] = val
      if annotation_boxes:
          # Manually trigger update_image_positions
          update_image_positions(None)
          fig.canvas.draw_idle()
      logging.debug(f"Image size slider changed to {val:.1f}x")
  ```
- Connect callback to slider: `image_size_slider.on_changed(on_slider_change)`
- Place this right after the slider is created

### 6. Test Slider with Small Dataset - Basic Functionality
- Run visualization with images: `uv run python src/visualize_graph_3d.py --use-images --images-dir images/ --verbose`
- Verify slider appears at bottom of figure
- Test slider interaction:
  - Move slider to 0.5x - verify images become smaller
  - Move slider to 2.0x - verify images become larger
  - Move slider back to 1.0x - verify images return to default size
- Check verbose logs for slider change messages

### 7. Test Slider with Zoom Integration
- Run visualization: `uv run python src/visualize_graph_3d.py --use-images --images-dir images/ --verbose`
- Set slider to 0.5x
- Zoom in significantly with scroll wheel
- Verify images scale but remain smaller than without slider adjustment
- Set slider to 2.0x
- Zoom out significantly
- Verify images scale but remain larger than without slider adjustment
- Confirm slider and zoom work together multiplicatively

### 8. Test Slider with Rotation and Pan
- Run visualization: `uv run python src/visualize_graph_3d.py --use-images --images-dir images/ --verbose`
- Adjust slider to 1.5x
- Rotate the 3D view by dragging
- Verify images maintain their slider-adjusted size and reposition correctly
- Pan the view by right-click dragging
- Verify slider setting persists
- Zoom, rotate, and adjust slider in various combinations
- Confirm no visual glitches or reset of slider value

### 9. Test Edge Cases
- Test slider at minimum value (0.5x):
  - Images should be clearly visible but small
  - Should not become invisible or distorted
- Test slider at maximum value (2.0x):
  - Images should be large but not absurdly oversized
  - Should not cause performance issues or overlap excessively
- Test rapid slider adjustments:
  - Move slider quickly back and forth
  - Verify smooth updates without lag or crashes
- Test with partial image set (some nodes without images):
  - Verify fallback spheres are unaffected by slider
  - Only images should respond to slider changes

### 10. Test Without Images (Regression Check)
- Run visualization without images: `uv run python src/visualize_graph_3d.py --verbose`
- Verify slider still appears (even though it has no effect)
- Alternative: Only show slider when `use_images=True`
  - Add conditional: `if use_images and annotation_boxes:` before creating slider
  - This keeps UI cleaner when not needed

### 11. Add Unit Tests for Slider Functionality
- Open `tests/test_visualize_graph_3d.py`
- Add test for slider widget creation:
  ```python
  def test_slider_widget_with_images(sample_graph_with_images):
      """Test that slider widget is created when using images."""
      # Test that slider is created with correct range and default value
      # Test that slider axes exist in the figure
  ```
- Add test for slider callback (may be difficult to test directly, focus on state changes)
- Run tests: `uv run pytest tests/test_visualize_graph_3d.py::test_slider_widget_with_images -v`

### 12. Update Help Text and Logging
- In `main()` function (around line 732), update the help text for `--use-images`:
  - From: "Use item images instead of colored spheres for nodes"
  - To: "Use item images instead of colored spheres for nodes (includes interactive size slider)"
- Add INFO level log message when slider is created:
  - `logging.info("Created interactive image size slider (0.5x - 2.0x, default: 1.0x)")`

### 13. Run Full Visualization Test Suite
- Execute visualization test suite: `uv run pytest tests/test_visualize_graph_3d.py -v`
- Verify all tests pass (should be 43+ tests now)
- Ensure no regressions from the slider addition

### 14. Run Complete Test Suite
- Execute all tests: `uv run pytest tests/ -v`
- Verify zero new test failures
- Confirm all existing passing tests still pass

### 15. Manual End-to-End Validation
- Run full visualization with all features:
  - `uv run python src/visualize_graph_3d.py --use-images --images-dir images/ --verbose`
- Perform comprehensive manual test:
  - Verify initial image sizes match expected default (1.0x)
  - Adjust slider to simulate user's preferred "small" size (0.5x-0.7x)
  - Zoom in and verify images remain at reasonable size (not too large like Image #1)
  - Adjust slider to simulate user's preferred "large" size (1.5x-2.0x)
  - Zoom out and verify images remain visible
  - Test all interactive features in combination:
    - Rotation + slider adjustment
    - Zoom + slider adjustment
    - Pan + slider adjustment
    - Hover tooltips with various slider values
  - Verify performance remains acceptable (no significant lag from slider updates)

## Testing Strategy

### Unit Tests
- Test slider widget creation with correct parameters (range, default, step)
- Test slider axes positioning doesn't overlap with 3D axes
- Test slider scale factor storage and retrieval
- Test that slider callback modifies the scale factor correctly
- Test edge values (min: 0.5x, max: 2.0x)

### Integration Tests
- Test slider interaction with zoom multiplier (combined scaling)
- Test slider persistence across rotation, zoom, and pan operations
- Test slider with mixed rendering (images + fallback spheres)
- Test slider with no images loaded (graceful handling)
- Test slider updates trigger correct draw events

### Edge Cases
- Slider at minimum (0.5x) with extreme zoom out - images shouldn't disappear
- Slider at maximum (2.0x) with extreme zoom in - images shouldn't cause performance issues
- Rapid slider adjustments - should update smoothly without crashes
- Slider interaction during active rotation/zoom - should handle concurrent events
- Empty graph or single node - slider should still function correctly
- Very large graphs (850+ nodes) - slider updates should remain responsive

## Acceptance Criteria
- [ ] Slider widget appears at the bottom of the 3D visualization figure
- [ ] Slider has clear label "Image Size" and visible scale markers (0.5x to 2.0x)
- [ ] Slider default value is 1.0x (current behavior)
- [ ] Moving slider to 0.5x makes images 50% of base size (matching initial view from Image #2)
- [ ] Moving slider to 2.0x makes images 200% of base size (matching zoomed view from Image #1, but user-controlled)
- [ ] Slider adjustments update image sizes in real-time (< 100ms latency)
- [ ] Slider setting persists during rotation, pan, and zoom operations
- [ ] Slider scale multiplies with automatic zoom multiplier (combined effect)
- [ ] Slider only affects images, not fallback spheres or intermediate nodes
- [ ] Slider works correctly with partial image sets (mixed rendering)
- [ ] Slider control is intuitive and responsive (no lag or glitches)
- [ ] All existing tests pass with zero regressions
- [ ] Manual testing confirms user can prevent "too large" images by adjusting slider while zoomed in
- [ ] Documentation updated to describe slider control

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

```bash
# Ensure test images are available
uv run python src/download_item_images.py --input output/items.csv --output-dir images/ --limit 50 --verbose

# Test visualization with slider (MANUAL: verify slider appears and controls image size)
uv run python src/visualize_graph_3d.py --use-images --images-dir images/ --verbose

# Test visualization without images (verify no regression)
uv run python src/visualize_graph_3d.py --verbose

# Run visualization tests
uv run pytest tests/test_visualize_graph_3d.py -v

# Run full test suite
uv run pytest tests/ -v
```

## Notes

### Implementation Approach

The slider approach was chosen over alternatives because:

1. **User Control** - Gives users direct, fine-grained control over image sizes
2. **Visual Feedback** - Slider provides clear indication of current scale setting
3. **Matplotlib Native** - Uses built-in `matplotlib.widgets.Slider`, no external dependencies
4. **Persistent** - Slider value persists across all view manipulations (rotate, zoom, pan)
5. **Non-Destructive** - Works multiplicatively with existing zoom behavior, doesn't replace it
6. **Intuitive** - Slider is familiar UI pattern for continuous value adjustment

### Slider Range Selection

The range of 0.5x to 2.0x was chosen based on:

- **0.5x (minimum)**: Approximately matches the initial view size from Image #2 (good balance, small images)
- **1.0x (default)**: Current automatic behavior, neutral starting point
- **2.0x (maximum)**: Approximately matches the "too large" zoomed-in size from Image #1, but user-controlled
- **0.1x step size**: Provides smooth adjustment without overwhelming number of discrete values

This range gives users enough control to go from "nice and small" to "larger than I'd want" without being extreme.

### Interaction with Zoom Multiplier

The slider scale multiplies with the automatic zoom multiplier:

```
final_zoom = base_zoom * zoom_multiplier * slider_scale
```

**Example scenarios:**

1. **Initial view, slider at 1.0x**:
   - zoom_multiplier ≈ 1.0 (no zoom)
   - slider_scale = 1.0 (default)
   - final_zoom = base_zoom * 1.0 * 1.0 = base_zoom (current behavior)

2. **Zoomed in 3x, slider at 0.5x** (user wants smaller images when zoomed):
   - zoom_multiplier = 3.0 (zoomed in)
   - slider_scale = 0.5 (user set to half)
   - final_zoom = base_zoom * 3.0 * 0.5 = base_zoom * 1.5 (only 1.5x growth instead of 3x)

3. **Zoomed out 2x, slider at 1.5x** (user wants larger images when zoomed out):
   - zoom_multiplier = 0.5 (zoomed out)
   - slider_scale = 1.5 (user set to 150%)
   - final_zoom = base_zoom * 0.5 * 1.5 = base_zoom * 0.75 (only 0.75x shrink instead of 0.5x)

This provides the best of both worlds: automatic zoom responsiveness PLUS user control.

### Alternative Approaches Considered

**Approach 1: Replace automatic zoom with slider** (slider is only control)
- Pros: Simpler logic, one source of truth
- Cons: Loses automatic zoom responsiveness, requires constant manual adjustment

**Approach 2: Two sliders** (one for base size, one for zoom sensitivity)
- Pros: Maximum control, can tune both base size and zoom behavior
- Cons: Complex UI, confusion about which slider does what, takes up more space

**Approach 3: Preset buttons** (Small / Medium / Large buttons instead of slider)
- Pros: Simpler UI, clear discrete options
- Cons: Less fine-grained control, harder to find "just right" size

**Approach 4: Keyboard shortcuts** (+/- keys to adjust size)
- Pros: No screen space used, keyboard-friendly
- Cons: Less discoverable, no visual feedback of current scale

**Chosen approach (multiplicative slider)** is best because:
- Preserves existing automatic zoom behavior users may like
- Provides continuous fine-grained control
- Clear visual feedback via slider position
- Familiar UI pattern
- Relatively simple implementation

### Performance Considerations

- Slider callback triggers `update_image_positions()` which updates all images
- With 850+ images, this could be expensive if called too frequently
- Current implementation uses `fig.canvas.draw_idle()` which throttles redraws
- Slider step size of 0.1 means at most 16 discrete positions (not continuous drag)
- If performance issues arise, could add additional throttling:
  - Only update on slider release (not during drag)
  - Debounce slider changes (wait for N milliseconds of inactivity)
  - Update subset of visible images first, then batch update rest

### UI/UX Considerations

**Slider positioning:**
- Bottom of figure (below 3D axes) - doesn't overlap with visualization
- Centered horizontally - easy to access, visually balanced
- Width 60% of figure - long enough to be easy to use, not too dominant

**Slider styling:**
- Clear label "Image Size" - immediately obvious what it controls
- Value display shows current multiplier (0.5x, 1.0x, 2.0x, etc.)
- Light gray background distinguishes it from visualization area
- Standard matplotlib slider styling for familiarity

**Accessibility:**
- Slider can be controlled with keyboard (Tab to focus, arrow keys to adjust)
- Large enough to easily grab and drag (height: 0.03 of figure)
- Step size (0.1) provides reasonable granularity without being too sensitive

### Conditional Slider Display

Consider only showing slider when `use_images=True`:

```python
if use_images and annotation_boxes:
    # Create slider
    slider_ax = fig.add_axes([0.2, 0.05, 0.6, 0.03])
    image_size_slider = Slider(...)
    # ... slider setup
else:
    # Adjust 3D axes to use full vertical space
    ax = fig.add_subplot(111, projection='3d')
```

This keeps the UI clean when images aren't being used.

### Future Enhancements

1. **Save slider preference** - Remember user's preferred slider value across sessions (config file)
2. **Additional slider for zoom sensitivity** - Control how aggressively automatic zoom affects images
3. **Preset buttons** - Add "Small", "Medium", "Large" buttons for quick common values
4. **Keyboard shortcuts** - Bind '+' and '-' keys to increment/decrement slider
5. **Slider for node spacing** - Allow users to adjust graph layout density
6. **Animation** - Smooth transition when slider value changes (instead of instant jump)
7. **Slider for edge transparency** - Control how visible edges are
8. **Reset button** - Quickly return slider to 1.0x default value

### Relationship to Existing Bug Fixes

This feature builds on previous bug fixes:
- **bug-image-zoom-not-responsive.md**: Implemented automatic zoom-responsive scaling
  - This feature adds user control on top of that automatic behavior
- **bug-zoom-image-position-update.md**: Fixed position updates during zoom
  - Slider leverages the same draw event handler for updates
- **bug-annotationbox-position-update.md**: Fixed AnnotationBbox positioning
  - Slider modifies the same AnnotationBbox zoom property

The slider is the natural next step: automatic responsiveness + manual control = optimal UX.

### Testing Strategy Notes

**Automated testing limitations:**
- Slider is primarily a visual/interactive widget
- Difficult to automatically verify "image is the right size"
- Can test that slider exists, has correct properties, callback fires
- Cannot easily test subjective aspects like "feels responsive" or "looks good"

**Manual testing focus areas:**
1. Visual correctness - do images scale as expected?
2. Responsiveness - is there lag when adjusting slider?
3. Integration - does slider work with zoom/rotate/pan?
4. Edge cases - does slider handle extreme values gracefully?
5. User experience - is slider intuitive and helpful?

**Acceptance testing:**
- Primary validation is user trying to reproduce original issue (Image #1 too large)
- User should be able to zoom in and use slider to prevent images from being too large
- User should feel they have sufficient control over image sizes
