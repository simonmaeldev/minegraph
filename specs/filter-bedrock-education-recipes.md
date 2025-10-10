# Bug: Bedrock Edition and Minecraft Education recipes incorrectly included in output

## Bug Description
The current parser is extracting crafting recipes from Bedrock Edition and Minecraft Education, which should be excluded since this project focuses on Java Edition only. Items like "Bleach" appear in the `output/transformations.csv` file, but Bleach is only available in Bedrock Edition and Minecraft Education.

In the HTML, these recipes are marked with a `<sup>` tag containing text like "Bedrock Edition and Minecraft Education only" within the table row's description column (`<td>`), but the recipe UI elements (`<span class="mcui mcui-Crafting_Table">`) themselves don't contain this marker directly in their parent structure - it appears in sibling table cells.

**Expected behavior**: Only Java Edition recipes should be included in the output.
**Actual behavior**: Bedrock Edition and Minecraft Education recipes are being extracted and saved to CSV.

## Problem Statement
The existing `is_java_edition()` function in `src/core/parsers.py:9-33` checks for edition markers within the element's text and parent sections, but it doesn't detect cases where the edition marker appears in a sibling table cell (`<td>`) rather than within the crafting UI element's parent hierarchy. This causes Bedrock/Education-only recipes (like Bleach-based crafting) to bypass the filter.

## Solution Statement
Enhance the `is_java_edition()` function to also check sibling table cells (`<td>` elements) in the same table row (`<tr>`) for Bedrock/Education edition markers. When a crafting UI element is within a table row, we should check all table cells in that row for the edition marker text before accepting the recipe.

## Steps to Reproduce
1. Run the extraction script: `uv run python src/extract_transformations.py`
2. Open `output/transformations.csv`
3. Search for "Bleach" in the file
4. Observe that Bleach-related crafting recipes are present (lines 41-55 in current output)
5. Verify in `ai_doc/downloaded_pages/crafting.html` that Bleach recipes have `<sup>` tags with "Bedrock Edition and Minecraft Education only" text in the description column

## Root Cause Analysis
The `is_java_edition()` function in `src/core/parsers.py:9-33` currently:
1. Checks the element's own text for "bedrock" or "education" keywords
2. Checks parent sections for "bedrock edition" text
3. Does NOT check sibling table cells in the same table row

The Minecraft Wiki's HTML structure for crafting recipes uses a table where:
- Each recipe is in a `<tr>` (table row)
- The crafting UI (`<span class="mcui mcui-Crafting_Table">`) is in one `<td>` cell
- The description/edition marker is in a different `<td>` cell in the same row
- The edition marker is in a `<sup>` tag like: `[Bedrock Edition and Minecraft Education only]`

Since the edition marker is in a sibling cell, not a parent element of the crafting UI, the current parent-based check misses it.

## Relevant Files
Use these files to fix the bug:

- **src/core/parsers.py** (Lines 9-33, `is_java_edition()` function)
  - This is the main filter function that needs enhancement
  - Currently checks element text and parent sections
  - Needs to also check sibling table cells for edition markers

- **src/core/parsers.py** (Lines 116-216, `parse_crafting()` function)
  - Uses `is_java_edition()` to filter crafting UIs
  - No changes needed here, but important to understand the context

- **tests/test_parsers.py**
  - Needs a new test case to verify Bedrock/Education recipes are filtered out
  - Should test the enhanced `is_java_edition()` function with HTML containing table row markers

### New Files
None required - all changes are in existing files.

## Step by Step Tasks

### Step 1: Enhance the `is_java_edition()` function
- Modify `src/core/parsers.py:9-33` to check sibling table cells in the same table row
- When the element is within a `<tr>` (table row), find all `<td>` cells in that row
- Check if any of those cells contain text with "Bedrock Edition" and "Minecraft Education" together
- Also check for variations like "Bedrock" + "Education" in the same cell
- Maintain backward compatibility with existing checks (element text and parent sections)

### Step 2: Create test case for Bedrock/Education filtering
- Add a test function in `tests/test_parsers.py` called `test_filter_bedrock_education_recipes()`
- Create sample HTML that mimics the wiki structure with:
  - A table row containing a crafting UI with Bleach
  - A description cell with `<sup>` tag containing "Bedrock Edition and Minecraft Education only"
- Verify that `parse_crafting()` returns an empty list for this HTML
- Also test that Java Edition recipes (without the marker) are still parsed correctly

### Step 3: Verify the fix with actual data
- Delete the existing `output/transformations.csv` and `output/items.csv` files
- Run the extraction script: `uv run python src/extract_transformations.py`
- Verify that Bleach no longer appears in the output files
- Check that legitimate Java Edition recipes are still present

### Step 4: Run validation commands
- Execute all validation commands listed below to ensure zero regressions
- Fix any issues that arise from the tests

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `uv run pytest tests/test_parsers.py -v` - Run parser tests to validate filtering works correctly
- `uv run pytest tests/ -v` - Run all tests to ensure no regressions
- `uv run python src/extract_transformations.py` - Run extraction to regenerate CSV files
- `grep -i "bleach" output/transformations.csv` - Verify Bleach is NOT in the output (should return empty)
- `grep -i "bleach" output/items.csv` - Verify Bleach item is NOT in the output (should return empty)
- `wc -l output/transformations.csv` - Check total transformation count (should be less than before)
- `grep "crafting" output/transformations.csv | wc -l` - Verify we still have many crafting recipes (sanity check)

## Notes
- The fix should be surgical and focused only on improving the `is_java_edition()` filter
- Do not modify the core parsing logic in `parse_crafting()` or other parser functions
- The edition marker pattern to detect is: text containing both "Bedrock Edition" AND ("Minecraft Education" OR "Education") in the same table row
- Be careful with case-insensitive matching since the HTML uses proper capitalization
- The `<sup>` tags with edition markers can appear anywhere in the table row, not just in the first or last cell
