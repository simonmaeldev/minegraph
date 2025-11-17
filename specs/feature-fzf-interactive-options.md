# Feature: Interactive Option Selection with FZF

## Feature Description
Replace command-line option selection in the 3D visualization script with an interactive fzf-based menu. This feature allows users to interactively select visualization options (--use-images, --verbose, and transformation type filters) using a fuzzy-finding interface instead of remembering command-line flags. Users can still provide flags directly on the command line to bypass the interactive menu.

## User Story
As a user running the 3D visualization script
I want to select options interactively using fzf checkboxes
So that I don't have to remember command-line flags and can easily toggle multiple options

## Problem Statement
The current 3D visualization script requires users to remember and type command-line flags like `--use-images`, `--verbose`, and transformation type filters. This creates friction, especially when users want to experiment with different combinations of options. Users must either remember the exact flag names or constantly refer to `--help` documentation.

## Solution Statement
Implement an interactive fzf-based menu that presents visualization options as selectable checkboxes. The menu will appear when specific flags are not provided on the command line, allowing users to:
- Toggle boolean flags (--use-images, --verbose) with checkboxes
- Select transformation types to filter by (with multi-select support)
- Bypass the menu entirely by providing flags directly on the command line
- Disable the interactive menu with a new `--no-interactive` flag for scripting/automation

The solution uses the pyfzf library (already in the venv) to provide a consistent, terminal-native interface.

## Relevant Files
Use these files to implement the feature:

- `src/visualize_graph_3d.py` - Main 3D visualization script that currently uses argparse for command-line options. This file needs modification to:
  - Add fzf-based interactive option selection
  - Detect when flags are missing and trigger fzf prompts
  - Preserve existing argparse for direct command-line usage
  - Add `--no-interactive` flag to disable fzf prompts
  - Support filtering by transformation type (new feature)

- `output/transformations.csv` - Contains transformation data with types: brewing, composting, crafting, mob_drop, smelting, smithing, stonecutter, trading. Used to determine available filter options.

- `README.md` - Documentation that describes how to run the 3D visualization script. Needs updating to document:
  - New interactive mode behavior
  - How to bypass interactive mode with flags
  - `--no-interactive` flag for scripting
  - New transformation type filtering capability

- `tests/test_visualize_graph_3d.py` - Existing test suite for 3D visualization. Needs updates to:
  - Test fzf integration and option parsing
  - Test behavior with and without command-line flags
  - Mock fzf user interactions
  - Test filtering by transformation type

### New Files
- None - all changes are modifications to existing files

## Implementation Plan

### Phase 1: Foundation
Add the core infrastructure for interactive option selection:
- Add helper functions to present fzf menus with checkbox support
- Create option collection logic that merges command-line args with fzf selections
- Implement `--no-interactive` flag to preserve scriptability

### Phase 2: Core Implementation
Integrate fzf prompts into the visualization workflow:
- Add fzf prompt for boolean flags (--use-images, --verbose) when not specified
- Add transformation type filtering capability with multi-select fzf menu
- Ensure command-line flags take precedence over interactive selection
- Handle user cancellation gracefully (exit without error)

### Phase 3: Integration
Complete the feature with filtering logic and documentation:
- Implement CSV filtering by selected transformation types
- Update README.md with new usage patterns and examples
- Add comprehensive tests for all interactive scenarios
- Validate end-to-end workflow with various flag combinations

## Step by Step Tasks

### 1. Add FZF Helper Functions
- Import pyfzf library at the top of `src/visualize_graph_3d.py`
- Create `prompt_boolean_options()` function to present checkbox menu for boolean flags
- Create `prompt_transformation_types()` function to present multi-select menu for transformation types
- Add error handling for when fzf is not available or user cancels selection
- Test helper functions work correctly with pyfzf API

### 2. Add Transformation Type Filtering
- Add `--filter-type` argument to argparse (accepts comma-separated transformation types)
- Create `load_transformation_types()` function to extract unique types from CSV
- Modify `load_transformations_from_csv()` to accept optional filter parameter
- Filter transformations based on selected types before building graph
- Log how many transformations were filtered out

### 3. Implement Interactive Option Collection
- Add `--no-interactive` flag to argparse
- Create `collect_options()` function that orchestrates option collection
- Check if boolean flags (--use-images, --verbose) are already specified
- If not specified and interactive mode enabled, prompt with fzf
- Check if `--filter-type` is specified, otherwise prompt with fzf for transformation types
- Return complete options dictionary merging CLI args and fzf selections

### 4. Integrate Interactive Logic into Main Flow
- Call `collect_options()` early in `main()` function
- Use collected options to override argparse defaults
- Pass filter_type to CSV loading function
- Ensure `--no-interactive` completely bypasses all fzf prompts
- Test with various combinations: no flags, some flags, all flags, --no-interactive

### 5. Update Tests for Interactive Features
- Add mock/patch for fzf calls in test suite
- Test `prompt_boolean_options()` with various user selections
- Test `prompt_transformation_types()` with single and multiple selections
- Test `collect_options()` with CLI args present (should skip fzf)
- Test `collect_options()` with no args and `--no-interactive=False` (should prompt)
- Test filtering logic removes correct transformations
- Test user cancellation exits gracefully

### 6. Update Documentation
- Add new section in README.md explaining interactive mode
- Document `--filter-type` flag for filtering by transformation type
- Document `--no-interactive` flag for scripting/automation use cases
- Add examples showing interactive usage vs direct flag usage
- Update comparison table to mention filtering capability
- Add notes about pyfzf dependency being pre-installed

### 7. Validation and End-to-End Testing
- Run full test suite to ensure no regressions
- Manually test interactive mode with various selections
- Test with `--no-interactive` flag to ensure scripting compatibility
- Test filtering by single and multiple transformation types
- Test that command-line flags bypass interactive prompts
- Verify README documentation matches actual behavior

## Testing Strategy

### Unit Tests
- `test_prompt_boolean_options()` - Verify checkbox menu presents correct options and returns selections
- `test_prompt_transformation_types()` - Verify multi-select menu for transformation types
- `test_collect_options_with_cli_args()` - Verify CLI args bypass fzf prompts
- `test_collect_options_interactive()` - Verify fzf prompts appear when args missing
- `test_filter_transformations()` - Verify filtering logic correctly filters by type
- `test_load_transformation_types()` - Verify unique types extracted from CSV
- `test_no_interactive_flag()` - Verify `--no-interactive` bypasses all prompts

### Integration Tests
- `test_end_to_end_with_interactive_selection()` - Full pipeline with mocked fzf selections
- `test_end_to_end_with_cli_flags()` - Full pipeline bypassing interactive mode
- `test_filtering_with_selected_types()` - Verify graph only contains selected transformation types
- `test_user_cancellation_handling()` - Verify graceful exit when user cancels fzf prompt

### Edge Cases
- User cancels fzf prompt (should exit gracefully without error)
- pyfzf library not available (should show error message with installation instructions)
- Invalid transformation type specified via `--filter-type` (should warn and continue)
- Empty selection in fzf (should use defaults)
- CSV contains no transformations of selected type (should show warning)
- `--no-interactive` flag with missing required options (should use defaults)

## Acceptance Criteria
1. When running `uv run python src/visualize_graph_3d.py` without flags, fzf presents a checkbox menu for boolean options (use-images, verbose)
2. After selecting boolean options, fzf presents a multi-select menu for transformation types
3. User selections from fzf are applied to the visualization as if they were command-line flags
4. When running with explicit flags like `uv run python src/visualize_graph_3d.py --use-images --verbose --filter-type=crafting,smelting`, no fzf prompts appear
5. The `--no-interactive` flag completely disables all fzf prompts and uses default values
6. Filtering by transformation type correctly excludes unselected types from the graph
7. All existing tests pass without modification
8. New tests achieve 100% coverage of interactive option collection logic
9. README.md clearly documents the new interactive mode and all new flags
10. The feature is backward compatible - old command-line usage patterns still work

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

```bash
# Run all tests including new interactive feature tests
uv run pytest tests/test_visualize_graph_3d.py -v

# Run full test suite to ensure no regressions
uv run pytest tests/ -v

# Test interactive mode manually (requires manual fzf interaction)
uv run python src/visualize_graph_3d.py

# Test bypass with CLI flags (should not show fzf prompts)
uv run python src/visualize_graph_3d.py --use-images --verbose --filter-type=crafting

# Test --no-interactive flag (should not show fzf prompts, use defaults)
uv run python src/visualize_graph_3d.py --no-interactive

# Test filtering by single transformation type
uv run python src/visualize_graph_3d.py --filter-type=crafting -v

# Test filtering by multiple transformation types
uv run python src/visualize_graph_3d.py --filter-type=crafting,smelting,brewing -v

# Test help documentation includes new flags
uv run python src/visualize_graph_3d.py --help

# Verify all commands in README.md still work
uv run python src/visualize_graph_3d.py -i output/transformations.csv -v
```

## Notes

### FZF Integration Considerations
- pyfzf is already installed in the venv per user confirmation
- pyfzf provides Python bindings to fzf for terminal-based fuzzy finding
- Checkboxes are created using fzf's multi-select mode with `--multi` flag
- User selections are returned as a list of strings that need parsing

### Backward Compatibility
- All existing command-line flags continue to work exactly as before
- Users who prefer CLI-only usage are not affected
- The `--no-interactive` flag ensures scripting and automation use cases work seamlessly
- Default behavior changes to interactive, but can be disabled

### Transformation Type Filtering
- This is a new feature requested by the user alongside fzf integration
- Filtering happens at CSV load time before graph construction
- Reduces graph complexity when user wants to focus on specific transformation types
- Mirrors the `--filter-type` functionality from `visualize_graph_with_graphviz.py`

### Future Enhancements
- Remember user's last selections in a config file for quicker re-runs
- Add fzf preview pane showing what each option does
- Support custom fzf themes/styling via configuration
- Add "profiles" that save common option combinations
- Integrate fzf selection for input file, output path, and color config
