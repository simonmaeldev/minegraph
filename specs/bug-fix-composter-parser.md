# Bug: Composter Parser Missing Items

## Bug Description
The composter parser (`parse_composting` function in `src/core/parsers.py`) is incorrectly parsing the composting wiki page. Currently, it only outputs "Bone Meal -> Bone Meal" (1 transformation), which is wrong. The actual composting table contains dozens of organic items (beetroot seeds, kelp, sugar cane, tall grass, apple, carrot, pitcher plant, pumpkin pie, etc.) that can be composted INTO bone meal. The parser is completely missing these input items.

Expected behavior: Parse all compostable items from the "Items" section of the composting table and create transformations like "Beetroot Seeds -> Bone Meal", "Kelp -> Bone Meal", "Apple -> Bone Meal", etc.

Actual behavior: Only creates one transformation "Bone Meal -> Bone Meal" (which makes no sense).

## Problem Statement
The current `parse_composting` function looks for tables with "chance" or "%" column headers. However, the composting wiki page has a different structure where items are organized in a table with a row containing `<th colspan="6">Items</th>`, followed by rows with `<td>` cells containing `<ul>` lists of item links. The parser is not detecting or parsing this table structure, resulting in it only finding the bone meal item itself and creating an incorrect self-transformation.

## Solution Statement
Rewrite the `parse_composting` function to:
1. Find the composting items table by looking for the row with `<th colspan="6">Items</th>` header
2. Parse all `<td>` cells in the rows following the "Items" header row
3. Extract all item links from `<ul>` lists within these cells
4. Create transformations from each compostable item to bone meal
5. Preserve success rate metadata where available (the table has percentage columns before the "Items" section)
6. Apply Java Edition filtering to exclude Bedrock-only items

## Steps to Reproduce
1. Run: `uv run python src/extract_transformations.py`
2. Check output: `grep "COMPOSTING" output/transformations.csv`
3. Observe: Only "Bone Meal" -> "Bone Meal" transformation appears
4. Expected: Dozens of transformations like "Beetroot Seeds" -> "Bone Meal", "Kelp" -> "Bone Meal", etc.

Alternatively:
```bash
uv run python -c "
from src.core.parsers import parse_composting
with open('ai_doc/downloaded_pages/composting.html', 'r') as f:
    html = f.read()
transformations = parse_composting(html)
print(f'Found {len(transformations)} composting transformations')
for t in transformations[:10]:
    print(f'{t.inputs[0].name} -> {t.outputs[0].name}')
"
```
Output: Only "Bone Meal -> Bone Meal"

## Root Cause Analysis
The root cause is in `src/core/parsers.py` lines 961-1033. The current implementation:

1. Line 976: Finds all tables with class "wikitable"
2. Lines 990-994: Checks if headers contain "chance" or "%"
3. Lines 997-1002: Parses rows looking for item links in first cell

The problem is that the composting table structure on the wiki has:
- A row with `<th colspan="6">Items</th>` that marks the start of the items section
- Multiple `<td>` cells (columns) containing `<ul>` lists with multiple item links per cell
- Items are not in a traditional table row with one item per row

The parser's current logic expects:
- Table headers with "chance" or "%"
- One item link per row in the first cell
- A percentage in the second cell

This mismatch causes the parser to skip the actual items table and only find a self-referential bone meal transformation.

## Relevant Files
Use these files to fix the bug:

- **src/core/parsers.py** (lines 961-1033): Contains the buggy `parse_composting` function that needs to be rewritten to correctly parse the composting items table structure

- **ai_doc/downloaded_pages/composting.html**: The downloaded wiki page that contains the composting data. The table structure shows items organized under a `<th colspan="6">Items</th>` header row, with items listed in `<ul>` elements across multiple `<td>` columns

- **tests/test_parsers.py**: Contains existing parser tests. We need to add comprehensive tests for the fixed `parse_composting` function to ensure it correctly parses multiple items and creates proper transformations

- **app_docs/feature-minecraft-transformation-extraction.md**: Documentation for the transformation extraction system that may need updating if the composting parser behavior changes significantly

### New Files
None - this is a bug fix to existing functionality, no new files are needed.

## Step by Step Tasks

### 1. Analyze the composting table structure
- Read the composting.html file to understand the exact DOM structure
- Identify the table with the "Items" header row
- Map out where item links are located (in `<ul>` lists within `<td>` cells)
- Identify any percentage/success rate columns that precede the items section
- Document the structure in code comments for future reference

### 2. Rewrite the `parse_composting` function
- Replace the current logic in `src/core/parsers.py` lines 961-1033
- Find tables by looking for rows with `<th colspan="6">Items</th>` header
- Parse all `<td>` cells following the "Items" header row
- Extract all `<a href="/w/...">` links from `<ul>` lists in these cells
- For each extracted item, call `extract_item_from_link()` to create an Item
- Apply `is_java_edition()` filtering to exclude Bedrock-only items (e.g., Grass Block has [BE only] marker)
- Create a Transformation from each item to Bone Meal
- Handle success rate metadata if available (may need to correlate items with percentage rows)
- Use the existing deduplication pattern with `seen_signatures` set

### 3. Add comprehensive tests for composting parser
- Add tests to `tests/test_parsers.py` for the `parse_composting` function
- Test that it correctly parses multiple items from the "Items" section
- Test that it creates transformations with bone meal as output
- Test that it filters out Bedrock-only items (like Grass Block with [BE only] marker)
- Test that success rate metadata is preserved where applicable
- Test that empty HTML returns empty list
- Test deduplication (same item shouldn't create duplicate transformations)

### 4. Run tests and validate
- Run the full test suite: `uv run pytest tests/test_parsers.py -v -k composting`
- Run all tests: `uv run pytest tests/ -v`
- Ensure all existing tests still pass (no regressions)
- Ensure new composting tests pass

### 5. Validate with actual extraction
- Run the full extraction: `uv run python src/extract_transformations.py`
- Check composting transformations: `grep "COMPOSTING" output/transformations.csv | head -20`
- Verify we see dozens of transformations like "Beetroot Seeds" -> "Bone Meal"
- Verify no "Bone Meal" -> "Bone Meal" transformation exists
- Count total composting transformations: `grep -c "COMPOSTING" output/transformations.csv`
- Manually spot-check a few well-known compostable items (kelp, apple, carrot, pumpkin)

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `uv run pytest tests/test_parsers.py -v -k composting` - Run composting-specific tests
- `uv run pytest tests/ -v` - Run full test suite to ensure no regressions
- `uv run python src/extract_transformations.py` - Run full extraction
- `grep "COMPOSTING" output/transformations.csv | head -20` - View first 20 composting transformations
- `grep -c "COMPOSTING" output/transformations.csv` - Count total composting transformations (should be 50+)
- `grep "Bone Meal.*Bone Meal" output/transformations.csv` - Verify no self-transformation exists (should return nothing)
- `grep "Beetroot Seeds" output/transformations.csv` - Verify beetroot seeds transformation exists
- `grep "Kelp" output/transformations.csv` - Verify kelp transformation exists
- `grep "Apple" output/transformations.csv` - Verify apple transformation exists

## Notes
- The composting table on the wiki organizes items by their success rate (30%, 50%, 65%, 85%, 100%)
- Items are grouped in columns under the "Items" header, not in individual rows
- Some items have Bedrock Edition markers like `<sup class="nowrap Inline-Template">[BE only]</sup>` that should be filtered
- Success rate metadata should be preserved in the transformation metadata if possible
- The bone meal output is consistent across all compostable items
- This is purely a parser bug - the data model and CSV export logic are correct
- No changes needed to the transformation type enum or data structures
