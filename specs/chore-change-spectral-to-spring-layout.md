# Chore: Change Spectral Layout to Spring Layout in 3D Visualization

## Chore Description
Change the primary 3D graph layout algorithm from `spectral_layout` to `spring_layout` in `src/visualize_graph_3d.py` at line 257. This change affects how nodes are positioned in 3D space. After making this code change, update all documentation files that reference spectral layout to reflect the new spring layout algorithm, including technical descriptions, performance characteristics, and coordinate range expectations.

## Relevant Files
Use these files to resolve the chore:

### Existing Files

- **src/visualize_graph_3d.py** (line 257): Contains the primary layout algorithm call that needs to be changed from `nx.spectral_layout` to `nx.spring_layout`. This is the core implementation file where the actual code change occurs.
  - Line 257 currently: `pos = nx.spectral_layout(graph, dim=3)`
  - Line 258: Logging statement that references spectral layout
  - Line 260-261: Fallback to spring layout for small graphs (logic will need adjustment)
  - Line 263: Error handling that mentions spectral layout failing

- **README.md** (line 161): Documents the 3D visualization features, specifically mentions "Uses spectral layout algorithm to position nodes in 3D space" in the feature list. This needs to be updated to reference spring layout.
  - Line 171: Comparison table shows "Spectral, spatial" for 3D layout - needs update

- **app_docs/feature-1-3d-graph-visualization.md** (lines 39-42): Technical implementation documentation that describes the "3D Layout Algorithm" section with detailed information about spectral layout as primary and spring as fallback. This needs to be inverted or rewritten.
  - Describes spectral layout characteristics (optimal spatial positioning, separating clusters, minimizing edge crossings)
  - Mentions performance implications

- **app_docs/feature-2-3d-graph-hover-interactivity.md** (lines 57, 130): References coordinate ranges "approximately -1 to 1 due to spectral layout normalization". Spring layout may have different coordinate characteristics that need to be documented.

- **.claude/commands/conditional_docs.md** (line 50): Conditional documentation mentions "When working with spectral or spring layout algorithms" - this is already generic enough but may benefit from clarification about which is primary.

### New Files
None required - all changes are updates to existing files.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Read and understand the current layout implementation
- Read `src/visualize_graph_3d.py` lines 240-270 to understand the complete layout logic including fallback mechanisms
- Understand the current control flow: spectral (primary) → spring (fallback for <3 nodes or on error)
- Review how the `seed=42` parameter is used in spring layout for reproducibility
- Note the logging statements that reference layout type

### Step 2: Update the code in src/visualize_graph_3d.py
- Change line 257 from `pos = nx.spectral_layout(graph, dim=3)` to `pos = nx.spring_layout(graph, dim=3, seed=42)`
- Update line 258 logging statement from "Using spectral layout for 3D positioning" to "Using spring layout for 3D positioning"
- Simplify or remove the conditional logic at line 256 (`if num_nodes >= 3`) since spring layout works for all graph sizes
- Update line 261 logging statement to reflect that spring layout is now primary (or remove if logic is simplified)
- Update line 263 error message from "Spectral layout failed" to "Spring layout failed" if keeping try/except, or consider if fallback is still needed
- Consider removing the try/except block entirely if spring layout is more robust

### Step 3: Update README.md documentation
- Change line 161: "Uses spectral layout algorithm to position nodes in 3D space" to "Uses spring layout algorithm to position nodes in 3D space"
- Change line 171 in the comparison table: Update "Spectral, spatial" to "Spring (force-directed), spatial" for the 3D layout row
- Review performance note at line 197 about "Layout computation may take 5-30 seconds" - verify if this timing changes with spring layout
- Add a brief note about spring layout characteristics if helpful for users (force-directed, physics-based)

### Step 4: Update app_docs/feature-1-3d-graph-visualization.md
- Rewrite lines 39-42 in the "3D Layout Algorithm" section to reflect spring layout as primary:
  - Change "Primary: Spectral layout (`nx.spectral_layout` with dim=3) for optimal spatial positioning"
  - Update description of layout characteristics for spring layout (force-directed, physics-based simulation, iterative)
  - Update or remove the "Fallback: Spring layout for small graphs" line since spring is now primary
  - Update description: "Layout computation separates densely connected clusters and minimizes edge crossings" - verify this still applies to spring layout
- Review lines 135-145 (Performance Considerations section) to update timing estimates if spring layout has different performance characteristics
- Check if any other sections reference spectral layout characteristics that need updating

### Step 5: Update app_docs/feature-2-3d-graph-hover-interactivity.md
- Update line 57: Change "Typical coordinate ranges are approximately -1 to 1 due to spectral layout normalization" to describe spring layout's coordinate characteristics (may be different)
- Update line 130: Change "Verified scales show appropriate ranges (approximately -1 to 1 from spectral layout)" to reflect spring layout ranges
- Research or note: Spring layout coordinates may have different ranges than spectral layout - document the typical ranges

### Step 6: Review and update .claude/commands/conditional_docs.md if needed
- Review line 50: "When working with spectral or spring layout algorithms"
- Consider updating to emphasize spring layout is now primary, or keep as-is since it's already generic
- No change strictly required, but consider clarifying if it would help future developers

### Step 7: Run validation commands
- Execute all commands listed in "Validation Commands" section below to ensure the chore is complete with zero regressions
- Verify the 3D visualization still works correctly with spring layout
- Confirm no test failures or errors

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

```bash
# Run all tests to ensure no regressions
uv run pytest tests/ -v

# Run specific 3D visualization tests if they exist
uv run pytest tests/test_visualize_graph_3d.py -v

# Test the 3D visualization with spring layout (manual verification)
# Verify that:
# - The graph renders without errors
# - Layout looks reasonable with nodes well-distributed
# - Hover annotations still work correctly
# - Interactive controls still function properly
uv run python src/visualize_graph_3d.py -v

# Test with custom input to verify it works with real data
uv run python src/visualize_graph_3d.py -i output/transformations.csv -v

# Verify all source files have no syntax errors
uv run python -m py_compile src/visualize_graph_3d.py
```

## Notes

### Spring Layout vs Spectral Layout Characteristics

**Spectral Layout:**
- Uses eigenvectors of graph Laplacian matrix for positioning
- Generally produces normalized coordinates (approximately -1 to 1 range)
- Optimal for certain graph properties (minimizes edge crossings mathematically)
- Can fail on very small graphs (<3 nodes)
- Deterministic (same graph always produces same layout)

**Spring Layout:**
- Force-directed algorithm (physics simulation)
- Nodes repel each other, edges act as springs pulling connected nodes together
- Iterative process that converges to equilibrium
- Works reliably for all graph sizes including small graphs
- Uses `seed` parameter for reproducibility (otherwise results vary)
- Coordinate ranges can vary but typically are centered around 0
- May take longer to compute for large graphs but is more robust

### Impact of This Change

1. **Coordinate Ranges**: Spring layout may produce different coordinate ranges than spectral layout. Documentation should reflect typical ranges (likely still centered around 0, but may have different spread).

2. **Visual Appearance**: The graph's spatial arrangement will look different. Spring layout tends to create more "organic" clustering based on connectivity, while spectral layout is more mathematically optimized.

3. **Performance**: Spring layout may have different performance characteristics (potentially slower for large graphs, but more predictable/robust).

4. **Robustness**: Spring layout is more robust and doesn't require fallback logic for small graphs, simplifying the code.

5. **Reproducibility**: The `seed=42` parameter ensures reproducible layouts with spring layout, which is important for testing and consistent user experience.

### Why This Change Might Be Requested

- Spring layout may provide better visual separation for this specific graph type
- More robust behavior (no fallback logic needed)
- User preference for force-directed layout aesthetics
- Better performance for this graph's characteristics
- More intuitive "physics-based" positioning

### Documentation Update Strategy

When updating documentation:
- Be accurate about algorithm characteristics
- Update performance expectations if they change
- Update coordinate range descriptions
- Keep user-facing documentation focused on benefits/behavior, not implementation details
- Keep technical documentation precise about algorithm choice and characteristics
