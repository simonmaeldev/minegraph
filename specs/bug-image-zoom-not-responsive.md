# Bug: Image Zoom Not Responsive to 3D View Zoom

## Bug Description
When using `--use-images` flag with the 3D visualization, item images do not scale proportionally when zooming in/out using the scroll wheel. The images maintain a fixed pixel size regardless of the 3D view zoom level, making them appear static while the rest of the visualization scales. This creates a poor user experience where:

1. At default zoom level, images may be reasonably sized
2. When zooming in (to see specific areas), images remain the same tiny size instead of getting larger
3. When zooming out, images remain the same size and may appear too large relative to the view
4. Images don't feel integrated with the 3D space - they appear as static overlays

**Expected Behavior:**
- Images should scale proportionally with the 3D view zoom level
- When zooming in, images should appear larger (more detail visible)
- When zooming out, images should appear smaller (maintaining spatial relationships)
- Images should feel integrated with the 3D space, not like static overlays

**Actual Behavior:**
- Images maintain a constant pixel size regardless of zoom level
- Only the 3D axes and spatial layout scale during zoom
- Images appear disconnected from the 3D space
- Cannot zoom in to see image details more clearly

## Problem Statement
The `zoom` parameter of each `OffsetImage` is set once during creation (line 447 of `src/visualize_graph_3d.py`) and never updated during interaction. The current draw event handler (lines 624-634) only updates the 2D position (`xy` and `xybox`) of annotation boxes when the camera rotates, but does not update the zoom/scale of the images themselves.

```python
# Line 447 - zoom is set once during creation
zoom = np.sqrt(node_sizes[node]) / 100.0

# Lines 624-634 - draw handler only updates position, not zoom
def update_image_positions(event):
    """Update annotation box positions when the view changes."""
    for item in annotation_boxes:
        ab = item['ab']
        x, y, z = item['pos_3d']
        # Re-project 3D coordinates to current 2D screen coordinates
        x2, y2, _ = proj3d.proj_transform(x, y, z, ax.get_proj())
        ab.xybox = (x2, y2)
        ab.xy = (x2, y2)
        # Missing: No zoom/scale update!
```

The matplotlib 3D axis zoom is controlled by axis limits (xlim, ylim, zlim). When the user scrolls to zoom, these limits change, but the `OffsetImage` zoom parameter remains constant.

## Solution Statement
Enhance the draw event handler to detect axis scale changes and dynamically update the zoom factor of each `OffsetImage` accordingly. The solution involves:

1. **Calculate base zoom factor** - Determine appropriate default zoom based on node size (current implementation at line 447)
2. **Track axis scale** - Store initial axis limits to detect zoom level changes
3. **Calculate zoom multiplier** - Compare current axis limits to initial limits to determine zoom factor
4. **Update image zoom** - Multiply base zoom by the calculated zoom multiplier and update each `OffsetImage`
5. **Store base zoom** - Keep the base zoom factor for each image in the `annotation_boxes` list

**Implementation approach:**
- Store initial axis limits after first render
- In the draw event handler, calculate the current zoom level by comparing axis ranges
- Update each `OffsetImage.zoom` property based on current zoom level
- Use the distance between axis limits as a proxy for zoom level

## Steps to Reproduce
1. Ensure images are downloaded: `uv run python src/download_item_images.py --input output/items.csv --output-dir images/ --limit 20 --verbose`
2. Run 3D visualization with images: `uv run python src/visualize_graph_3d.py --use-images --images-dir images/`
3. Observe the initial image sizes at default zoom
4. Use scroll wheel to zoom in significantly (zoom in until you're focusing on a small cluster of nodes)
5. Observe that images remain the exact same pixel size - they don't get larger
6. Use scroll wheel to zoom out significantly (zoom out to see entire graph)
7. Observe that images remain the exact same pixel size - they don't get smaller
8. Compare with how the spheres (intermediate nodes or fallback nodes) scale with zoom - they grow/shrink appropriately

## Root Cause Analysis
The root cause is in the `update_image_positions()` function (lines 624-634 of `src/visualize_graph_3d.py`):

**Current implementation only updates position:**
```python
def update_image_positions(event):
    """Update annotation box positions when the view changes."""
    for item in annotation_boxes:
        ab = item['ab']
        x, y, z = item['pos_3d']
        # Re-project 3D coordinates to current 2D screen coordinates
        x2, y2, _ = proj3d.proj_transform(x, y, z, ax.get_proj())
        ab.xybox = (x2, y2)
        ab.xy = (x2, y2)
        # MISSING: zoom/scale update
```

**Why this causes the bug:**

1. **Initial zoom calculation (line 447)** - The zoom is calculated once:
   ```python
   zoom = np.sqrt(node_sizes[node]) / 100.0
   ```
   This produces values like 0.071-0.224 based on node importance.

2. **OffsetImage zoom is static** - The `OffsetImage` object is created with a fixed zoom value:
   ```python
   imagebox = OffsetImage(img, zoom=zoom)
   ```
   The `zoom` parameter controls the image scale relative to its pixel dimensions.

3. **3D axis zoom changes limits** - When the user scrolls to zoom:
   - Matplotlib adjusts the axis limits (xlim, ylim, zlim)
   - The 3D scatter plots automatically scale with these limits
   - But `OffsetImage` objects exist in 2D screen space - they don't automatically scale with 3D axis changes

4. **Draw handler is incomplete** - The current handler updates positions but not zoom:
   - It correctly recalculates 2D screen positions from 3D coordinates
   - But it never recalculates or updates the `zoom` property of the `OffsetImage`
   - Result: Images stay at their initial pixel size regardless of view zoom

**Technical details:**
- `OffsetImage.zoom` is a mutable property that can be updated
- Axis zoom level can be inferred from the range of axis limits
- Initial axis range: `max_coord - min_coord` for each axis
- Current axis range: `ax.get_xlim()[1] - ax.get_xlim()[0]` (and y, z)
- Zoom factor: `initial_range / current_range` (smaller range = zoomed in)
- Updated zoom: `base_zoom * zoom_factor`

## Relevant Files
Use these files to fix the bug:

- **src/visualize_graph_3d.py** (lines 440-475, 622-636) - Contains the image rendering code and draw event handler that needs enhancement. Need to:
  - Store base zoom factor for each image in `annotation_boxes` (around line 470)
  - Calculate and store initial axis limits after rendering (around line 476)
  - Enhance `update_image_positions()` function (lines 624-634) to calculate current zoom multiplier and update each `OffsetImage.zoom` property

- **tests/test_visualize_graph_3d.py** - Contains tests for the visualization functionality. May need to add or update tests for zoom responsiveness, though this is primarily a visual/interactive feature that's hard to test automatically.

- **app_docs/feature-image-based-3d-nodes.md** - Documentation for the image-based 3D nodes feature. Should be updated to note the zoom responsiveness capability.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Store Base Zoom Factor in annotation_boxes
- In `src/visualize_graph_3d.py`, modify the image rendering loop (around line 470)
- Add `'base_zoom': zoom` to the dictionary stored in `annotation_boxes`
- This preserves the original node-size-based zoom calculation for each image
- Also store a reference to the imagebox itself: `'imagebox': imagebox`
- The annotation_boxes items should now have: `ab`, `node`, `pos_3d`, `base_zoom`, and `imagebox`

### 2. Calculate and Store Initial Axis Limits
- After the image rendering section (around line 476), calculate initial axis limits
- Store the initial range (max - min) for each axis:
  - `initial_x_range = ax.get_xlim()[1] - ax.get_xlim()[0]`
  - `initial_y_range = ax.get_ylim()[1] - ax.get_ylim()[0]`
  - `initial_z_range = ax.get_zlim()[1] - ax.get_zlim()[0]`
- Calculate average initial range: `initial_range = (initial_x_range + initial_y_range + initial_z_range) / 3`
- This will be used to determine relative zoom level

### 3. Enhance update_image_positions() to Update Zoom
- Modify the `update_image_positions()` function (lines 624-634)
- At the start of the function, calculate current axis ranges:
  - `current_x_range = ax.get_xlim()[1] - ax.get_xlim()[0]`
  - `current_y_range = ax.get_ylim()[1] - ax.get_ylim()[0]`
  - `current_z_range = ax.get_zlim()[1] - ax.get_zlim()[0]`
  - `current_range = (current_x_range + current_y_range + current_z_range) / 3`
- Calculate zoom multiplier: `zoom_multiplier = initial_range / current_range`
  - When zoomed in (smaller range), zoom_multiplier > 1 (larger images)
  - When zoomed out (larger range), zoom_multiplier < 1 (smaller images)
- For each item in annotation_boxes:
  - Get base_zoom and imagebox from the item dictionary
  - Calculate new zoom: `new_zoom = base_zoom * zoom_multiplier`
  - Update the OffsetImage zoom: `item['imagebox'].set_zoom(new_zoom)`
  - Then update position as before (xy and xybox)

### 4. Test with Small Dataset - Verify Zoom Responsiveness
- Ensure test images exist: `uv run python src/download_item_images.py --input output/items.csv --output-dir images/ --limit 20 --verbose`
- Run visualization: `uv run python src/visualize_graph_3d.py --use-images --images-dir images/`
- Manually test zoom behavior:
  - Observe initial image sizes (should be clearly visible)
  - Scroll to zoom in significantly (focus on a cluster)
  - Verify images get proportionally larger
  - Scroll to zoom out significantly (see entire graph)
  - Verify images get proportionally smaller
  - Rotate view and verify images still scale correctly with zoom
  - Test edge cases: extreme zoom in, extreme zoom out

### 5. Verify Fallback Sphere Behavior Unchanged
- Run visualization without images: `uv run python src/visualize_graph_3d.py`
- Verify spheres render correctly and scale with zoom as before
- Ensure no errors or warnings appear

### 6. Test Mixed Rendering (Images + Spheres)
- Test with partial image set (some nodes have images, others don't)
- Verify both images and fallback spheres scale appropriately with zoom
- Ensure hover functionality works for both types of nodes

### 7. Update Feature Documentation
- Edit `app_docs/feature-image-based-3d-nodes.md`
- In the "Interactive Features" section, update the Zoom bullet point:
  - From: "Scroll to zoom in/out - image positions update dynamically"
  - To: "Scroll to zoom in/out - images scale proportionally with zoom level and positions update dynamically"
- Add a note in the "Technical Implementation" section about the zoom scaling behavior

### 8. Run Visualization Tests
- Execute visualization test suite: `uv run pytest tests/test_visualize_graph_3d.py -v`
- Verify all tests pass (should be 43 tests)
- Ensure no regressions from the changes

### 9. Run Full Test Suite
- Execute all tests: `uv run pytest tests/ -v`
- Verify zero new test failures
- Confirm all existing passing tests still pass

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `uv run python src/download_item_images.py --input output/items.csv --output-dir images/ --limit 20 --verbose` - Ensure test images are available
- `uv run python src/visualize_graph_3d.py --use-images --images-dir images/` - Test visualization with zoom-responsive images (MANUAL: verify images scale when zooming in/out)
- `uv run python src/visualize_graph_3d.py` - Test visualization without images to verify no regressions
- `uv run pytest tests/test_visualize_graph_3d.py -v` - Run visualization tests to verify zero regressions
- `uv run pytest tests/ -v` - Run all tests to validate zero regressions across entire codebase

## Notes

### Why This Approach Works

The solution leverages the fact that:
1. **Axis limits reflect zoom** - When users scroll to zoom, matplotlib adjusts axis limits
2. **Range ratio = zoom factor** - Comparing initial to current axis range gives relative zoom
3. **OffsetImage.zoom is mutable** - Can be updated dynamically via `set_zoom()`
4. **Draw events capture all changes** - The draw event fires on zoom, rotation, and pan
5. **Base zoom preserves importance** - Node importance is baked into base_zoom, then scaled by view zoom

### Zoom Calculation Details

**Initial state:**
- Base zoom for node: `base_zoom = sqrt(node_size) / 100.0` (e.g., 0.071 to 0.224)
- Axis range: `initial_range = (xlim_max - xlim_min + ylim_max - ylim_min + zlim_max - zlim_min) / 3`

**During zoom in (axis limits get smaller):**
- Current range: `current_range < initial_range`
- Zoom multiplier: `initial_range / current_range > 1.0` (e.g., 2.0 when zoomed in 2x)
- New zoom: `base_zoom * 2.0` → images appear 2x larger

**During zoom out (axis limits get larger):**
- Current range: `current_range > initial_range`
- Zoom multiplier: `initial_range / current_range < 1.0` (e.g., 0.5 when zoomed out 2x)
- New zoom: `base_zoom * 0.5` → images appear 2x smaller

### Performance Considerations

- The draw event handler runs frequently during interaction
- Calculating zoom multiplier adds minimal overhead (just 6 axis limit lookups and 3 divisions)
- Calling `set_zoom()` on each OffsetImage is efficient (matplotlib operation)
- With 850+ images, the overhead per frame is negligible on modern hardware
- If performance becomes an issue, could add throttling (only update zoom every N frames)

### Alternative Approaches Considered

**Approach 1: Fixed zoom tiers** - Only update zoom at specific zoom levels (1x, 2x, 4x, etc.)
- Pros: Less computation, simpler logic
- Cons: Jumpy/stepwise scaling, not smooth

**Approach 2: Distance-based zoom** - Scale images based on camera distance from each node
- Pros: More realistic 3D depth perception
- Cons: Complex calculations, inconsistent sizing, harder to implement

**Approach 3: Screen space size maintenance** - Try to keep images at constant screen pixels
- Pros: Always visible at same apparent size
- Cons: Defeats the purpose of zoom, images wouldn't grow when zooming in

**Chosen approach (axis range ratio)** is best because:
- Simple and efficient calculation
- Smooth and continuous scaling
- Intuitive behavior matching user expectations
- Consistent with how 3D scatter plots scale

### Edge Cases to Consider

1. **Extreme zoom in** - Very small axis range could produce huge zoom multipliers
   - Consider capping zoom_multiplier at max value (e.g., 10.0)
   - Prevents images from becoming absurdly large

2. **Extreme zoom out** - Very large axis range could make images tiny
   - Consider capping zoom_multiplier at min value (e.g., 0.1)
   - Ensures images remain somewhat visible

3. **Asymmetric axis scaling** - User manually adjusts one axis more than others
   - Using average of all three axes handles this gracefully
   - Could alternatively use max or min axis range depending on desired behavior

4. **Initial view may not be "neutral"** - If initial axis limits are already zoomed
   - This is fine - we measure zoom relative to initial state
   - Users perceive zoom relative to what they first see

5. **Figure resize** - If the figure window is resized, aspect ratios change
   - Axis ranges stay the same, so zoom calculation unaffected
   - Images may appear stretched if figure aspect ratio changes dramatically

### Testing Strategy

Since zoom responsiveness is primarily a visual/interactive feature:

1. **Manual testing is critical** - Need human to scroll and observe behavior
2. **Automated tests are limited** - Can verify code doesn't error, but not visual correctness
3. **Test checklist**:
   - [ ] Images visible at default zoom
   - [ ] Images grow when zooming in
   - [ ] Images shrink when zooming out
   - [ ] Size changes are smooth and proportional
   - [ ] Images remain correctly positioned during zoom
   - [ ] Rotation + zoom combination works correctly
   - [ ] Hover tooltips still work during/after zoom
   - [ ] Extreme zoom in doesn't make images absurdly large
   - [ ] Extreme zoom out doesn't make images invisible
   - [ ] Mixed rendering (images + spheres) both scale appropriately

### Future Enhancements

1. **Configurable zoom sensitivity** - Add parameter to control how aggressively images scale
2. **Depth-based scaling** - Make images farther from camera smaller (perspective)
3. **LOD (Level of Detail)** - Use higher resolution images when zoomed in close
4. **Zoom-dependent detail** - Show different information at different zoom levels
5. **Smart min/max zoom limits** - Automatically cap zoom multiplier based on image sizes
