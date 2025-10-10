# Bug: Missing Dye Inputs in Wool Dyeing Recipes

## Bug Description
When parsing crafting recipes where multiple input slots contain animated alternatives (like "Any Wool + Matching Dye"), the parser only captures items from the first alternative slot and completely misses items from subsequent alternative slots. This results in incomplete transformation records where essential ingredients are missing.

**Specific Example - Wool Dyeing:**
- Wiki shows: "Any Wool + Matching Dye" → outputs the matching colored wool
- Current CSV shows: `crafting,"[\"Green Wool\"]","[\"Green Wool\"]","{\"has_alternatives\": true}"`
- **Bug**: Green Dye is completely missing from the inputs!
- **Expected**: `crafting,"[\"Green Wool\",\"Green Dye\"]","[\"Green Wool\"]","{\"has_alternatives\": true}"`

## Problem Statement
The crafting parser fails to include all input items when a recipe has multiple slots with animated alternatives. It only processes the first alternative slot and ignores all other alternative slots, resulting in missing ingredients in the transformation data.

## Solution Statement
Modify the `parse_crafting()` function to handle multiple alternative slots by:
1. Detecting when 2+ slots contain alternatives (animated items)
2. When alternative slots have matching counts, pair items by index (e.g., white wool with white dye, green wool with green dye)
3. Include ALL items from ALL alternative slots in each transformation record

## Steps to Reproduce
1. Run: `uv run python src/extract_transformations.py`
2. Check: `grep "Green Wool" output/transformations.csv`
3. Observe: `crafting,"[\"Green Wool\"]","[\"Green Wool\"]","{\"has_alternatives\": true}"`
4. Problem: The Green Dye input is missing - it should be `["Green Wool","Green Dye"]`

## Root Cause Analysis
**Location**: `src/core/parsers.py`, function `parse_crafting()`, lines 163-217

**Analysis**:
1. Lines 163-172 correctly identify ALL slots with alternatives and store them in `alternative_slots` list:
   ```python
   for slot in slots:
       items_in_slot = find_item_in_slot(slot)
       if items_in_slot:
           if len(items_in_slot) > 1:
               has_alternatives = True
               alternative_slots.append(items_in_slot)  # Stores ALL alternative slots
   ```

2. Lines 184-217 process alternatives BUT only use `alternative_slots[0]` (the first slot):
   ```python
   if has_alternatives and alternative_slots:
       # ...
       for i, alt_item in enumerate(alternative_slots[0]):  # BUG: Only first slot!
           all_inputs = input_items + [alt_item]
   ```

3. For wool dyeing: `alternative_slots = [[16 wool colors], [16 dye colors]]`
   - Only wool colors from `alternative_slots[0]` are processed
   - Dye colors in `alternative_slots[1]` are completely ignored

## Relevant Files
Use these files to fix the bug:

- **src/core/parsers.py** (lines 130-230)
  - Contains `parse_crafting()` function with the bug
  - Lines 163-172: Correctly identifies multiple alternative slots
  - Lines 184-217: **BUG LOCATION** - only processes first alternative slot

- **tests/test_parsers.py**
  - Existing test suite for parsers
  - Validates that current tests still pass after fix

### New Files

- **tests/test_multi_slot_alternatives.py**
  - New test file to validate multi-slot alternative parsing
  - Will test wool + dye recipe scenario

## Step by Step Tasks

### Step 1: Create comprehensive test for multi-slot alternatives
- Create `tests/test_multi_slot_alternatives.py`
- Write test `test_wool_dyeing_with_matching_dye()` that:
  - Creates HTML mimicking wiki structure with two animated slots (wool colors + dye colors)
  - Verifies both wool AND dye appear in transformation inputs
  - Validates 16 transformations are created (one per color)
  - Confirms each transformation pairs matching colors (green wool + green dye)

### Step 2: Fix parse_crafting to handle multiple alternative slots
- Modify `src/core/parsers.py` in the `parse_crafting()` function (lines 184-217)
- Replace logic that only processes `alternative_slots[0]`
- Implement pairing logic:
  - When `len(alternative_slots) >= 2` and all have equal counts
  - Zip alternative slots together: `zip(alternative_slots[0], alternative_slots[1], ...)`
  - Create transformations with items from ALL zipped positions
  - Example: (white wool, white dye) → white wool, (green wool, green dye) → green wool, etc.
- Handle edge case: if alternative slot counts differ, fall back to current behavior (use only first)

### Step 3: Validate fix with existing tests
- Run `uv run pytest tests/test_parsers.py -v`
- Ensure all existing tests pass (no regressions)
- Verify filter logic for Bedrock/Education still works

### Step 4: Execute validation commands and verify outputs
- Run full validation command suite (see Validation Commands section)
- Manually inspect CSV output to confirm wool + dye recipes are complete
- Verify recipe counts match expectations

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `uv run pytest tests/test_multi_slot_alternatives.py -v` - Validate new multi-slot test passes
- `uv run pytest tests/test_parsers.py -v` - Ensure existing parser tests still pass
- `uv run pytest tests/ -v` - Run complete test suite for zero regressions
- `uv run python src/extract_transformations.py` - Re-extract transformations with fixed parser
- `grep "Green Wool" output/transformations.csv | head -3` - Verify Green Dye now appears in inputs
- `grep -c "Green Wool" output/transformations.csv` - Confirm recipe count is correct
- `python -c "import csv; rows = list(csv.DictReader(open('output/transformations.csv'))); wool_recipes = [r for r in rows if 'Wool' in r['input_items'] and 'Dye' in r['input_items']]; print(f'Found {len(wool_recipes)} wool+dye recipes'); print(wool_recipes[0] if wool_recipes else 'None')"` - Validate wool+dye recipes exist and are complete

## Notes
- This fix must be generic to handle ANY number of alternative slots (not hardcoded to 2)
- When alternative slots have different counts, preserve current behavior (only first slot varies)
- The `has_alternatives: true` metadata should remain to indicate transformation families
- This bug affects ANY recipe with multiple animated ingredient slots, not just wool dyeing
- Other potential affected recipes: concrete powder (sand/gravel + dye), firework stars (gunpowder + dye + material), etc.
