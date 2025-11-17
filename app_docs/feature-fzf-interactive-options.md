# Interactive Option Selection with FZF

**ADW ID:** N/A
**Date:** 2025-11-17
**Specification:** specs/feature-fzf-interactive-options.md

## Overview

Added interactive fzf-based menu system to the 3D visualization script, allowing users to select visualization options (--use-images, --verbose) and filter by transformation types without memorizing command-line flags. Users can still provide flags directly to bypass the interactive menu, and a --no-interactive flag is available for scripting and automation.

## What Was Built

- Interactive checkbox menu for boolean options (use-images, verbose)
- Multi-select menu for transformation type filtering with 8+ types
- Transformation type filtering capability to reduce graph complexity
- Command-line flag precedence over interactive selection
- --no-interactive flag for automation/scripting use cases
- Comprehensive test suite with 13 new test cases
- Updated documentation in README.md

## Technical Implementation

### Files Modified

- `src/visualize_graph_3d.py`: Added 262 lines implementing FZF integration, filtering logic, and option collection
- `tests/test_visualize_graph_3d.py`: Added 340 lines of comprehensive tests for interactive features
- `README.md`: Updated documentation with interactive mode examples and new command-line options
- `pyproject.toml`: Added pyfzf dependency

### Key Changes

- **FZF Helper Functions**: Created `prompt_boolean_options()` and `prompt_transformation_types()` to present interactive menus with multi-select support
- **Filtering Infrastructure**: Modified `load_transformations_from_csv()` to accept optional `filter_types` parameter and filter transformations at load time
- **Option Collection**: Implemented `collect_options()` to orchestrate CLI args and interactive prompts with proper precedence handling
- **Backward Compatibility**: All existing CLI usage patterns remain functional; interactive mode is default but can be bypassed
- **Error Handling**: Graceful handling of missing fzf library, user cancellation (Ctrl+C), and empty selections

## How to Use

### Interactive Mode (Default)

1. Run the visualization script without flags:
   ```bash
   uv run python src/visualize_graph_3d.py
   ```

2. Select visualization options using the checkbox menu:
   - Use TAB to select/deselect options
   - Use arrow keys to navigate
   - Press ENTER to confirm selections

3. Select transformation types to filter (or choose "All types"):
   - Use TAB to select multiple types
   - Press ENTER to confirm

### Direct Command-Line Usage

Bypass interactive mode by providing explicit flags:

```bash
# Use images and verbose logging
uv run python src/visualize_graph_3d.py --use-images --verbose

# Filter by specific transformation types
uv run python src/visualize_graph_3d.py --filter-type=crafting,smelting

# Combine flags
uv run python src/visualize_graph_3d.py --use-images -v --filter-type=crafting,brewing
```

### Automation/Scripting

Disable interactive prompts completely:

```bash
uv run python src/visualize_graph_3d.py --no-interactive
```

## Configuration

### Command-Line Options

- `--filter-type`: Filter by transformation types (comma-separated, e.g., "crafting,smelting,brewing")
- `--no-interactive`: Disable interactive fzf prompts and use defaults/CLI args only
- `--use-images`: Use item images instead of colored spheres (can be selected interactively)
- `-v, --verbose`: Enable verbose logging (can be selected interactively)

### Available Transformation Types

The following transformation types can be filtered:
- brewing
- composting
- crafting
- mob_drop
- smelting
- smithing
- stonecutter
- trading

### Dependencies

The feature requires the `pyfzf` library, which is included in the project dependencies. If not available, the script will:
1. Display a clear error message
2. Suggest installation: `pip install pyfzf`
3. Recommend using command-line flags as an alternative

## Testing

### Run All Tests

```bash
# Run 3D visualization tests
uv run pytest tests/test_visualize_graph_3d.py -v

# Run full test suite
uv run pytest tests/ -v
```

### Test Coverage

The test suite includes:
- Interactive prompt behavior with various selections
- Transformation type filtering (single and multiple types)
- Option collection with different CLI arg combinations
- --no-interactive flag behavior
- Graceful handling of user cancellation

### Manual Testing

```bash
# Test interactive mode (requires manual interaction)
uv run python src/visualize_graph_3d.py

# Test bypass with CLI flags
uv run python src/visualize_graph_3d.py --use-images --verbose --filter-type=crafting

# Test --no-interactive flag
uv run python src/visualize_graph_3d.py --no-interactive

# Test filtering by single type
uv run python src/visualize_graph_3d.py --filter-type=crafting -v

# Test filtering by multiple types
uv run python src/visualize_graph_3d.py --filter-type=crafting,smelting,brewing -v
```

## Performance Impact

Filtering significantly improves performance for large graphs:

- **Full graph** (2038 transformations): ~5-30 seconds layout computation
- **Crafting only** (1586 transformations): ~4-20 seconds layout computation
- **Smelting only** (92 transformations): <1 second layout computation
- **Multiple types** (1702 transformations): ~4-25 seconds layout computation

Interactive prompts add negligible overhead (<100ms) and only appear when flags are not provided.

## Notes

### Design Decisions

- **CLI Precedence**: Command-line flags always take precedence over interactive selection to support automation
- **Boolean Prompt Logic**: Boolean options prompt only appears when BOTH --use-images and --verbose are False (not explicitly set)
- **Type Filtering**: Filters at CSV load time (not during graph construction) for efficiency
- **Graceful Exit**: User cancellation (Ctrl+C) exits cleanly without errors

### Limitations

- Requires `fzf` to be installed on the system (the `pyfzf` Python library wraps the native fzf binary)
- Interactive mode is terminal-only (not suitable for GUI environments)
- Cannot save interactive selections for re-use (future enhancement)

### Future Enhancements

Potential improvements mentioned in the specification:
- Remember user's last selections in a config file
- Add fzf preview pane showing what each option does
- Support custom fzf themes/styling via configuration
- Add "profiles" that save common option combinations
- Integrate fzf selection for input file, output path, and color config

### Backward Compatibility

All existing usage patterns continue to work:
- Existing scripts using CLI flags are unaffected
- Users who prefer CLI-only usage don't need to interact with fzf
- The --no-interactive flag ensures scripting/automation compatibility
