# Bug: Image Zoom Factor Too Small - Images Display as Invisible Dots

## Bug Description
When using `--use-images` flag with 3D visualization, the item images appear as extremely tiny dots (essentially invisible pixels) that don't scale appropriately when zooming in. The images are so small they're practically invisible, making the feature unusable.

**Symptoms:**
- Images appear as barely visible tiny dots in the 3D visualization
- Zooming in doesn't make the images larger (they remain fixed size dots)
- Images don't scale proportionally to their node importance
- The visualization is essentially unusable with images - users can't see what items they're looking at

**Expected Behavior:**
- Images should be clearly visible at default zoom level
- Images should be large enough to recognize the Minecraft items they represent
- Larger/more important nodes should have proportionally larger images
- Images should remain visible and recognizable throughout normal interaction

**Actual Behavior:**
- Images are microscopic dots, appearing as single pixels
- Completely impossible to identify what item each image represents
- The `--use-images` feature is non-functional due to invisibility

## Problem Statement
The zoom factor calculation in `src/visualize_graph_3d.py` (line 447) produces extremely small values that make images essentially invisible. The current formula is:

```python
zoom = np.sqrt(node_sizes[node]) / 1000.0
```

Given that node sizes range from 50-500:
- Minimum: `sqrt(50) / 1000 = 0.00707` (7x too small by factor of 1000!)
- Maximum: `sqrt(500) / 1000 = 0.02236` (22x too small by factor of 1000!)

These zoom values are 1-2 orders of magnitude too small for matplotlib's `OffsetImage`, resulting in images that are practically invisible.

## Solution Statement
Increase the zoom factor by removing or significantly reducing the division factor. The original implementation before the bug fix divided by 20, which was too large (causing overlap). The current division by 1000 is far too aggressive.

**Recommended approach:**
1. Change the formula to use a more reasonable divisor (e.g., 50-100 instead of 1000)
2. This will produce zoom values in the range of 0.07-0.45, which should be visible
3. Start conservatively with division by 100, which gives zoom range of 0.071-0.224
4. Fine-tune if needed based on visual testing

**Alternative formula options:**
- `zoom = np.sqrt(node_sizes[node]) / 100.0` → range 0.071-0.224 (reasonable starting point)
- `zoom = np.sqrt(node_sizes[node]) / 50.0` → range 0.141-0.447 (larger, may overlap)
- `zoom = np.sqrt(node_sizes[node]) / 75.0` → range 0.094-0.298 (middle ground)

## Steps to Reproduce
1. Ensure images are downloaded: `uv run python src/download_item_images.py --input output/items.csv --output-dir images/ --limit 10`
2. Run 3D visualization with images: `uv run python src/visualize_graph_3d.py --use-images --images-dir images/`
3. Observe the visualization
4. Notice that images appear as microscopic dots, barely visible
5. Try zooming in (scroll wheel)
6. Observe that images remain as tiny dots regardless of zoom level
7. Images are completely unusable - cannot identify any items

## Root Cause Analysis
The root cause is in line 447 of `src/visualize_graph_3d.py`:

```python
# Calculate zoom factor based on node size
zoom = np.sqrt(node_sizes[node]) / 1000.0
```

**Why This Calculation is Wrong:**

1. **Node sizes range from 50-500** (for item nodes):
   - Intermediate nodes: 15 (small gray spheres)
   - Item nodes: 50-500 (based on degree centrality)

2. **Current zoom calculation produces values that are too small by 10-50x**:
   - For node_size = 50: `zoom = sqrt(50) / 1000 = 7.07 / 1000 = 0.00707`
   - For node_size = 500: `zoom = sqrt(500) / 1000 = 22.36 / 1000 = 0.02236`

3. **Matplotlib's OffsetImage zoom parameter interpretation**:
   - `zoom=1.0` displays image at its original pixel dimensions
   - `zoom=0.5` displays image at half size
   - `zoom=0.01` displays image at 1% of original size (microscopic!)
   - `zoom=0.007` displays image at 0.7% of original size (essentially invisible!)

4. **Historical context**:
   - The original broken implementation used `scale = np.sqrt(size) / 20`
   - This was changed to `/1000` to prevent overlap, but overcorrected by 50x
   - The correct value should be somewhere between /20 and /1000
   - A divisor of 75-100 is likely optimal

5. **Why images don't grow when zooming**:
   - The `zoom` parameter is set once during creation and never updated
   - It defines the image size relative to its pixel dimensions
   - It's not related to the 3D axis zoom/scale
   - To make images respond to zoom, we'd need to update the zoom dynamically (complex)
   - Instead, we should just make them visible at a reasonable default size

## Relevant Files
Use these files to fix the bug:

- **src/visualize_graph_3d.py** (line 447) - Contains the zoom factor calculation that produces values too small by ~50x. The formula `zoom = np.sqrt(node_sizes[node]) / 1000.0` needs the divisor changed from 1000 to approximately 75-100 to make images visible and appropriately sized.

- **tests/test_visualize_graph_3d.py** - Contains tests for the visualization functionality. No changes needed, but we should verify tests still pass after the fix.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Fix the Zoom Factor Calculation
- Open `src/visualize_graph_3d.py` and navigate to line 447
- Change the zoom calculation from: `zoom = np.sqrt(node_sizes[node]) / 1000.0`
- To: `zoom = np.sqrt(node_sizes[node]) / 100.0`
- This increases the zoom factor by 10x, making images visible
- With this change, zoom values will range from:
  - Minimum (size=50): `sqrt(50)/100 = 0.071` (7% of original image size)
  - Maximum (size=500): `sqrt(500)/100 = 0.224` (22% of original image size)

### 2. Test with Small Dataset
- Download test images (if not already present): `uv run python src/download_item_images.py --input output/items.csv --output-dir images/ --limit 10 --verbose`
- Run visualization with images: `uv run python src/visualize_graph_3d.py --use-images --images-dir images/`
- Visually verify:
  - Images are now clearly visible (not microscopic dots)
  - Can identify what item each image represents
  - Images have reasonable size differentiation based on node importance
  - Images don't overlap excessively
- If images are still too small, try dividing by 75 instead of 100
- If images overlap too much, try dividing by 125 or 150

### 3. Test Without Images (Fallback Mode)
- Run visualization without images: `uv run python src/visualize_graph_3d.py`
- Verify that the visualization still works correctly with colored spheres
- Ensure no errors occur and spheres are properly sized

### 4. Run Existing Tests
- Run visualization test suite: `uv run pytest tests/test_visualize_graph_3d.py -v`
- Verify all 43 tests pass
- Ensure no regressions were introduced

### 5. Run Full Test Suite
- Run all tests: `uv run pytest tests/ -v --tb=no -q`
- Verify that the existing pass/fail status is maintained (154 passing, 4 pre-existing failures)
- Ensure the fix doesn't introduce new test failures

### 6. Fine-Tune if Needed (Optional)
- If after step 2, images are still too small, adjust the divisor:
  - Try 75: `zoom = np.sqrt(node_sizes[node]) / 75.0` (larger images)
  - Try 85: `zoom = np.sqrt(node_sizes[node]) / 85.0` (medium)
- If images overlap too much, increase the divisor:
  - Try 125: `zoom = np.sqrt(node_sizes[node]) / 125.0` (smaller images)
  - Try 150: `zoom = np.sqrt(node_sizes[node]) / 150.0` (much smaller)
- Goal: Find the sweet spot where images are clearly visible but don't overlap excessively

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `uv run python src/download_item_images.py --input output/items.csv --output-dir images/ --limit 10 --verbose` - Ensure test images are available
- `uv run python src/visualize_graph_3d.py --use-images --images-dir images/` - Run visualization with images and visually verify images are clearly visible (not microscopic dots)
- `uv run python src/visualize_graph_3d.py` - Run visualization without images to verify fallback mode works correctly
- `uv run pytest tests/test_visualize_graph_3d.py -v` - Run visualization tests to verify zero regressions (all 43 should pass)
- `uv run pytest tests/ -v --tb=no -q` - Run full test suite to verify zero regressions (154 passed, 4 pre-existing failures)

## Notes

### Zoom Factor Science

The `zoom` parameter in matplotlib's `OffsetImage` controls the scaling of the image relative to its pixel dimensions:
- `zoom=1.0`: Full original size
- `zoom=0.5`: Half size (50%)
- `zoom=0.1`: 10% of original size (small but visible)
- `zoom=0.01`: 1% of original size (microscopic dot)
- `zoom=0.007`: 0.7% of original size (essentially invisible!)

### Historical Context

1. **Original implementation** (Poly3DCollection approach):
   - Used `scale = np.sqrt(size) / 20`
   - This was too large, causing overlap

2. **First fix attempt** (AnnotationBbox with /1000):
   - Changed to `zoom = np.sqrt(node_sizes[node]) / 1000.0`
   - Overcorrected by 50x, making images invisible

3. **This fix** (AnnotationBbox with /100):
   - Changes to `zoom = np.sqrt(node_sizes[node]) / 100.0`
   - Balances visibility with preventing excessive overlap

### Recommended Divisor: 100

With divisor of 100:
- Node size 50 → zoom 0.071 → 7.1% of original image size
- Node size 250 → zoom 0.158 → 15.8% of original image size
- Node size 500 → zoom 0.224 → 22.4% of original image size

This provides:
- Clearly visible images (7-22% of original size)
- Reasonable size differentiation (3x range from smallest to largest)
- Minimal overlap (images are small enough to coexist)

### Image Sizes Reference

Typical Minecraft item images from the wiki are:
- Standard: 150x150 pixels
- With zoom=0.071: displayed as ~11x11 pixels (small but visible)
- With zoom=0.224: displayed as ~34x34 pixels (clearly visible)

### Alternative: Dynamic Zoom Based on View

For future enhancement (not part of this fix), images could scale with the 3D view zoom by:
1. Detecting axis zoom level in the draw event handler
2. Adjusting the `zoom` parameter of each OffsetImage dynamically
3. This is complex and out of scope for this bug fix

### Testing Considerations

- Manual visual testing is critical for this fix
- Automated tests don't validate visual appearance
- The "right" size is subjective but should prioritize visibility
- Balance between "clearly visible" and "not overlapping"
- May need iteration based on user feedback
