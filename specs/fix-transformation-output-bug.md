# Bug: Incorrect Multiple Outputs in Transformation CSV

## Bug Description
The transformation extraction produces incorrect output data where single recipes with animated alternatives generate transformations with multiple output items in a list instead of creating separate 1-to-1 transformations. For example, "Iron Ingot" is incorrectly shown as producing `["Block of Diamond", "Block of Gold", "Block of Iron"]` when it should only produce "Block of Iron". The same issue affects Gold Ingot and Diamond crafting recipes, as well as other recipes with animated alternatives in both input and output slots.

## Problem Statement
When parsing crafting recipes (and potentially other transformation types) that have animated alternatives in BOTH input and output slots, the parser creates separate transformations for each input alternative but assigns ALL output alternatives to each transformation, resulting in incorrect many-to-many mappings instead of correct one-to-one mappings.

## Solution Statement
Modify the parsing logic to match input alternatives with corresponding output alternatives by index position, creating one transformation per alternative pair. When animated alternatives exist in both input and output slots with the same count, pair them by index (first input alternative → first output alternative, etc.). Each transformation should have exactly one output item, never a list of alternatives.

## Steps to Reproduce
1. Run the extraction script: `uv run python src/extract_transformations.py`
2. Open `output/transformations.csv`
3. Look at the first 10 lines
4. Observe lines 2-7 where "Iron Ingot", "Gold Ingot", and "Diamond" all map to `["Block of Diamond", "Block of Gold", "Block of Iron"]`
5. Expected: Three separate transformations with single outputs:
   - Iron Ingot → Block of Iron
   - Gold Ingot → Block of Gold
   - Diamond → Block of Diamond

## Root Cause Analysis
In `src/core/parsers.py`, the `parse_crafting()` function (lines 116-190):

1. **Lines 142-156**: Collects input items and tracks alternative slots. When a slot has multiple items (animated alternatives), it correctly identifies `has_alternatives = True` and stores them in `alternative_slots`

2. **Lines 158-165**: Extracts output items using `find_item_in_slot(output_section)` which returns a **list** of ALL items in the output slot, including all animated alternatives

3. **Lines 167-180**: When alternatives exist, it iterates through `alternative_slots[0]` (input alternatives) and creates one transformation per input alternative, BUT it passes the entire `output_items` list (containing all output alternatives) to each transformation

4. **Result**: Each transformation gets assigned ALL output alternatives instead of just the matching one

The bug affects all parsers that use `find_item_in_slot()` for outputs without pairing alternatives by index. This primarily impacts:
- `parse_crafting()` - AFFECTED
- `parse_smelting()` - Uses `[:1]` slice, may still have issues
- `parse_smithing()` - May be affected
- `parse_stonecutter()` - May be affected
- Other parsers that don't enforce single outputs

## Relevant Files
Use these files to fix the bug:

- **src/core/parsers.py** (lines 90-190)
  - Contains `find_item_in_slot()` function that extracts items from slots
  - Contains `parse_crafting()` function with the buggy logic for handling alternatives
  - Lines 167-180 specifically create transformations with alternative handling
  - Other parser functions may have similar issues

- **src/core/data_models.py** (lines 40-58)
  - Contains `Transformation` class with `__post_init__` method
  - Currently deduplicates outputs but doesn't enforce single output
  - May need validation to ensure outputs list has exactly one item

- **output/transformations.csv**
  - Used to verify the bug is fixed by checking the first 10 lines

### New Files
No new files needed for this bug fix.

## Step by Step Tasks

### 1. Fix the parse_crafting() function to properly match input/output alternatives
- Modify `parse_crafting()` in `src/core/parsers.py` (lines 167-180)
- When both inputs and outputs have alternatives, pair them by index
- Track output alternatives separately from single outputs
- Create transformations with matched pairs (input_alt[i] → output_alt[i])
- Ensure each transformation has exactly ONE output item

### 2. Apply the same fix to other parser functions
- Review `parse_smithing()` for similar issues with alternatives
- Review `parse_stonecutter()` for similar issues with alternatives
- Review `parse_smelting()` to ensure `[:1]` slicing is working correctly
- Ensure all parsers create transformations with single output items only

### 3. Add validation to prevent multi-output transformations
- Modify `Transformation.__post_init__()` in `src/core/data_models.py`
- Add validation to ensure `len(self.outputs) == 1` after deduplication
- Raise a descriptive error if multiple outputs are detected
- This prevents future bugs from creating invalid transformations

### 4. Run tests to validate changes
- Execute existing test suite: `uv run pytest tests/ -v`
- Ensure all existing tests pass
- Verify tests cover the alternative handling logic

### 5. Validate the bug fix with actual data
- Run the extraction script: `uv run python src/extract_transformations.py`
- Check `output/transformations.csv` first 10 lines
- Verify Iron Ingot → Block of Iron (single output)
- Verify Gold Ingot → Block of Gold (single output)
- Verify Diamond → Block of Diamond (single output)
- Scan for any remaining multi-output entries in the CSV

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `uv run pytest tests/ -v` - Run all tests to ensure no regressions
- `uv run python src/extract_transformations.py` - Re-extract transformations with the fix
- `head -10 output/transformations.csv` - Check first 10 lines for correct single outputs
- `grep -E '"\[.*,.*,.*\]"' output/transformations.csv | wc -l` - Count any remaining multi-output entries (should be 0 for output_items column)
- `uv run python src/validate_output.py` - Run validation script to check data quality

## Notes
- The bug is specifically about OUTPUT items having multiple values when they should be singular
- Input items CAN have multiple alternatives in a single transformation (e.g., "any wool" recipes)
- The issue stems from misunderstanding animated alternatives in HTML - they show alternative recipes, not alternative outcomes of a single recipe
- When alternatives appear in both input AND output with the same count, they represent parallel recipes that should be separate transformations
- The fix should be surgical - only modify the alternative handling logic, not the entire parser structure
- Be careful not to break legitimate cases where inputs truly do have alternatives (e.g., different wool colors for the same output)
