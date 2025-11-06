# Feature: Interactive 3D Graph Hover Annotations and Enhanced Navigation

## Feature Description
Enhance the 3D graph visualization with hover-based node annotations that display item names when the user hovers over nodes. Additionally, add visible axis labels with numeric scales to help users understand zoom levels and spatial positioning, and enable the interactive navigation toolbar for better user control of the 3D view.

This feature adapts the 2D matplotlib hover annotation pattern (from StackOverflow) to work with 3D scatter plots in matplotlib, providing a more informative and user-friendly interactive visualization experience.

## User Story
As a user exploring the 3D transformation graph
I want to see item names when I hover over nodes and have numeric axis scales
So that I can quickly identify items, understand my zoom level, and navigate the graph more effectively

## Problem Statement
The current 3D visualization lacks critical interactive feedback and navigation features:
1. **No node identification on hover**: Users cannot identify which item a node represents without external reference, making exploration difficult when viewing 1961+ transformations
2. **Missing axis scales**: Users cannot determine their zoom level or spatial position, making it hard to navigate and understand the graph's extent
3. **Hidden navigation toolbar**: The matplotlib toolbar with zoom, pan, and home buttons is not visible, forcing users to rely solely on mouse gestures which may not be intuitive for all users

These limitations reduce the usability and effectiveness of the 3D visualization, especially for large graphs where visual exploration is the primary use case.

## Solution Statement
Implement three enhancements to the 3D visualization:

1. **Hover Annotations**: Add motion_notify_event handlers to detect when the mouse hovers over nodes, display an annotation box with the item name (or "craft_node" identifier for intermediate nodes), and update the annotation position as the user moves between nodes
2. **Numeric Axis Scales**: Replace the current empty axis ticks (ax.set_xticks([])) with actual numeric scales to show coordinate ranges and help users understand zoom levels
3. **Interactive Toolbar**: Enable matplotlib's interactive navigation toolbar by ensuring the figure manager displays the standard navigation controls (zoom, pan, home, save)

This solution adapts proven 2D matplotlib patterns to 3D scatter plots while maintaining the existing NetworkX graph structure and visualization pipeline.

## Relevant Files
Use these files to implement the feature:

### Existing Files
- **src/visualize_graph_3d.py** (lines 325-417): Contains the `render_3d_graph()` function that creates the matplotlib 3D visualization. This is where hover event handlers will be added, axis tick removal will be changed to numeric scales, and toolbar visibility will be ensured.
  - Currently removes axis ticks with `ax.set_xticks([])`, `ax.set_yticks([])`, `ax.set_zticks([])` (lines 407-409)
  - Creates 3D scatter plots for item nodes (lines 363-377) and intermediate nodes (lines 380-393)
  - Needs event handler setup similar to the StackOverflow 2D example

- **tests/test_visualize_graph_3d.py**: Contains unit and integration tests for the 3D visualization module. Will need new tests to verify hover annotation functionality and axis scale presence.

### New Files
None required - all enhancements will be additions to existing files.

## Implementation Plan

### Phase 1: Foundation
1. Research matplotlib 3D scatter plot event handling and annotation positioning in 3D space
2. Study the provided StackOverflow 2D hover example and understand how to adapt `motion_notify_event`, `contains()` method, and annotation positioning for 3D
3. Understand the existing graph data structure: `graph.nodes()` contains node names with `node_type` attribute ('item' or 'intermediate')

### Phase 2: Core Implementation
1. **Add hover annotation support to render_3d_graph()**:
   - Create annotation object using `ax.annotate()` with appropriate 3D positioning parameters
   - Implement `update_annot()` function to update annotation text and position based on the hovered node
   - Implement `hover()` event handler function to detect mouse motion, check if hovering over a node using scatter plot's `contains()` method, and show/hide annotation
   - Connect event handler to figure using `fig.canvas.mpl_connect("motion_notify_event", hover)`
   - Handle both item nodes (display item name) and intermediate nodes (display "intermediate_X" identifier)

2. **Replace axis tick removal with numeric scales**:
   - Remove the `ax.set_xticks([])`, `ax.set_yticks([])`, `ax.set_zticks([])` calls (lines 407-409)
   - Let matplotlib automatically generate numeric ticks, or explicitly set reasonable tick ranges based on the node position data

3. **Ensure toolbar visibility**:
   - Verify that `plt.show()` displays the standard matplotlib toolbar with navigation controls
   - If toolbar is not visible, investigate matplotlib backend configuration or add explicit toolbar enabling code

### Phase 3: Integration
1. Test with small graphs (3-10 nodes) to verify hover detection works correctly
2. Test with the full transformation graph (1961+ transformations) to ensure performance remains acceptable
3. Verify annotation updates smoothly as user moves mouse between nodes
4. Verify axis scales are visible and informative
5. Verify toolbar appears and all controls (zoom, pan, home) function correctly

## Step by Step Tasks

### Step 1: Implement hover annotation infrastructure
- Read the current `render_3d_graph()` function to understand the scatter plot structure
- Add an `ax.annotate()` call to create a hidden annotation object with appropriate styling (white background box, arrow pointer)
- Store references to the scatter plot objects (item nodes and intermediate nodes) for hit testing

### Step 2: Implement update_annot() function
- Create function that takes node index or identifier
- Look up node name from the graph structure
- Update annotation text with item name (or "intermediate_X" for intermediate nodes)
- Update annotation 3D position to point at the hovered node's (x, y, z) coordinates
- Handle edge cases like multiple nodes at similar positions

### Step 3: Implement hover() event handler
- Create function that receives matplotlib motion_notify_event
- Check if event is within the 3D axes
- Use scatter plot's `contains(event)` method to detect if hovering over a node
- If hovering, call `update_annot()` and set annotation visible
- If not hovering but annotation was visible, hide it
- Call `fig.canvas.draw_idle()` to trigger redraw

### Step 4: Connect event handler and enable numeric axes
- Connect hover handler using `fig.canvas.mpl_connect("motion_notify_event", hover)` before `plt.show()`
- Remove or comment out the three `set_xticks([])` calls to allow automatic numeric tick generation
- Test that both changes work correctly together

### Step 5: Verify toolbar visibility
- Run the visualization and verify matplotlib toolbar appears
- If toolbar is missing, research matplotlib backend configuration and implement fix
- Document any required environment configuration for toolbar visibility

### Step 6: Create comprehensive tests
- Add unit test for annotation object creation and configuration
- Add test to verify event handler is properly connected
- Add test to verify axis ticks are no longer empty lists
- Add integration test that simulates mouse hover events (if feasible with matplotlib testing utilities)
- Consider manual testing plan for interactive features that are difficult to unit test

### Step 7: Update documentation
- Update README.md to document the new hover annotation feature in the "3D Visualization Features" section
- Add note about axis scales helping users understand zoom levels
- Document the toolbar controls if not already covered
- Update the feature documentation file (app_docs/feature-1-3d-graph-visualization.md) with implementation details

### Step 8: Run validation commands
- Execute all commands listed in "Validation Commands" section to ensure feature works correctly with zero regressions
- Fix any issues discovered during validation
- Re-run tests until all pass

## Testing Strategy

### Unit Tests
- Test annotation object creation with correct styling parameters (bbox, arrow, text)
- Test that node name lookup correctly retrieves item names from graph structure
- Test that intermediate nodes display their identifier (e.g., "intermediate_0")
- Test axis tick configuration - verify ticks are not empty after changes
- Test event handler connection - verify motion_notify_event handler is registered

### Integration Tests
- Test hover annotation with small test graph (3-5 nodes) to verify end-to-end functionality
- Test with multi-input transformation graph to verify intermediate node annotation works
- Test with large graph to ensure hover detection performance is acceptable (no lag when moving mouse)
- Test that axis scales display appropriate numeric ranges based on node positions
- Manual test: verify toolbar appears and all controls work (zoom, pan, home, save)

### Edge Cases
- Hovering over dense node clusters where multiple nodes are very close together
- Hovering when no nodes are present (empty graph)
- Hovering on intermediate nodes vs item nodes (different label formats)
- Rapid mouse movement across many nodes (annotation should update smoothly)
- Very long item names that might overflow annotation box
- Graph with single node (minimal test case)

## Acceptance Criteria
1. When hovering over any item node in the 3D graph, an annotation box appears showing the item's name
2. When hovering over intermediate nodes, the annotation shows the node identifier (e.g., "intermediate_0")
3. The annotation follows the mouse as the user moves between nodes
4. The annotation disappears when the mouse moves away from all nodes
5. The X, Y, and Z axes display numeric scales/ticks showing coordinate values
6. The matplotlib navigation toolbar is visible with zoom, pan, home, and save controls all functional
7. All existing 3D visualization tests continue to pass (no regressions)
8. New tests verify annotation, axis, and event handler functionality
9. Performance remains acceptable with the full transformation graph (1961+ transformations) - no noticeable lag when moving mouse

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

```bash
# Run all tests to ensure no regressions
uv run pytest tests/ -v

# Run specific 3D visualization tests
uv run pytest tests/test_visualize_graph_3d.py -v

# Test with small sample graph (manual verification required)
# User should hover over nodes and verify:
# - Annotation appears with item names
# - Axis scales show numeric values
# - Toolbar is visible with working controls
uv run python src/visualize_graph_3d.py -i output/transformations.csv -v

# Test with verbose logging to see graph statistics
uv run python src/visualize_graph_3d.py -v

# Verify the feature works with custom color config
uv run python src/visualize_graph_3d.py -c config/graph_colors.txt

# Test saving to file (should preserve toolbar functionality)
uv run python src/visualize_graph_3d.py -o output/graphs/test_hover_3d.png
```

## Notes

### Technical Considerations
1. **3D Annotation Positioning**: Unlike 2D scatter plots, 3D annotations require careful handling of the projection matrix. The annotation's `xy` parameter must account for the current 3D view angle. Consider using `proj3d.proj_transform()` to convert 3D coordinates to 2D screen coordinates.

2. **Hit Testing in 3D**: The `contains()` method works differently in 3D scatter plots due to depth perception. Multiple nodes may appear at the same screen position from different view angles. Consider detecting the closest node to the mouse cursor or implementing a tolerance threshold.

3. **Performance**: With 1961+ nodes, hover detection must be efficient. The matplotlib `contains()` method is generally optimized, but consider throttling mouse events or using spatial indexing if performance issues arise.

4. **Annotation Styling**: The StackOverflow example uses `bbox=dict(boxstyle="round", fc="w")` which works well. Consider adjusting `alpha` value for semi-transparency and ensuring good contrast with the graph background.

5. **Axis Scale Ranges**: After removing `set_xticks([])` calls, matplotlib will auto-generate ticks based on node positions. The spectral layout algorithm produces normalized coordinates, so expect ranges roughly from -1 to 1 or similar. Consider setting explicit limits with `ax.set_xlim()` if auto-scaling is problematic.

6. **Toolbar Visibility**: The toolbar should appear by default with `plt.show()` when using interactive backends (Qt5Agg, TkAgg, etc.). If the toolbar is missing, it may indicate a non-interactive backend (Agg, SVG) or a configuration issue. Document the expected backend in the README.

### Future Enhancements
- Add configurable annotation styling (colors, fonts, box style) via command-line arguments or config file
- Implement click events to show detailed item information in a separate window
- Add option to display multiple node properties in annotation (e.g., degree centrality, transformation counts)
- Support pinning annotations so they remain visible without hovering
- Add keyboard shortcuts to toggle annotation visibility
- Implement search functionality that highlights matching nodes and shows their annotations

### Dependencies
- No new dependencies required - feature uses existing matplotlib and NetworkX libraries
- Requires matplotlib with interactive backend (Qt5Agg, TkAgg, etc.) for full functionality
- May need to document required matplotlib backend configuration for users

### Reference Implementation
The provided StackOverflow code demonstrates the core pattern:
```python
# Create annotation (initially hidden)
annot = ax.annotate("", xy=(0,0), xytext=(20,20), textcoords="offset points",
                    bbox=dict(boxstyle="round", fc="w"),
                    arrowprops=dict(arrowstyle="->"))
annot.set_visible(False)

# Update annotation for hovered node
def update_annot(ind):
    pos = sc.get_offsets()[ind["ind"][0]]
    annot.xy = pos
    text = "Node Name"  # Lookup from graph data
    annot.set_text(text)

# Handle mouse motion events
def hover(event):
    vis = annot.get_visible()
    if event.inaxes == ax:
        cont, ind = sc.contains(event)
        if cont:
            update_annot(ind)
            annot.set_visible(True)
            fig.canvas.draw_idle()
        else:
            if vis:
                annot.set_visible(False)
                fig.canvas.draw_idle()

# Connect event handler
fig.canvas.mpl_connect("motion_notify_event", hover)
```

Adapt this pattern to work with 3D axes and the NetworkX graph structure used in the project.
