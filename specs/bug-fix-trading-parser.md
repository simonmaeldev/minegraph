# Bug: Trading Transformations Not Being Extracted

## Bug Description
The trading parser (`parse_trading` function in `src/core/parsers.py`) is failing to extract any trading transformations from the Minecraft Trading wiki page. The output CSV file (`output/transformations.csv`) contains 0 trading transformations despite the trading.html file containing extensive trading data for all villager professions (Armorer, Butcher, Cartographer, Cleric, Farmer, Fisherman, Fletcher, Leatherworker, Librarian, Mason, Shepherd, Toolsmith, Weaponsmith) and wandering traders.

Expected behavior: The CSV should contain hundreds of trading transformations representing:
- Trades where players sell items to villagers for emeralds (e.g., "15 Coal → 1 Emerald")
- Trades where players buy items from villagers with emeralds (e.g., "5 Emeralds → 1 Iron Helmet")
- Trades with 1 or 2 input items and 1 output item

Actual behavior: Zero trading transformations are extracted and written to the CSV file.

## Problem Statement
The `parse_trading()` function in `src/core/parsers.py:679-777` is unable to extract trading data from the Minecraft Trading wiki page because it searches for item links using an incorrect HTML pattern. The parser looks for "invslot" span elements to find items, but trading tables use a completely different HTML structure based on nested span elements with class "nowrap" and "sprite-text".

## Solution Statement
Fix the `parse_trading()` function to correctly parse the HTML structure used in trading tables by:
1. Finding all `<a href="/w/[Item_Name]">` links within table cells instead of searching for "invslot" elements
2. Correctly identifying "Item wanted" and "Item given" columns
3. Parsing quantity multipliers (e.g., "15 ×", "5 ×") that appear before item names
4. Extracting both emerald-to-item trades (buying) and item-to-emerald trades (selling)
5. Handling trades with single items or multiple items in the input

## Steps to Reproduce
1. Run the extraction script: `uv run python src/extract_transformations.py`
2. Check the output file: `grep -c "^trading" output/transformations.csv`
3. Observe that the count is 0 (no trading transformations extracted)
4. Verify that trading.html exists and contains data: `ls -lh ai_doc/downloaded_pages/trading.html`
5. Confirm the file is not empty: `wc -l ai_doc/downloaded_pages/trading.html` (should show 1546 lines)

## Root Cause Analysis
The root cause is in the `parse_trading()` function (lines 679-777 in `src/core/parsers.py`). The function has multiple issues:

1. **Incorrect item extraction pattern** (lines 738-747): The parser looks for `<a href="/w/">` links directly in table cells, but doesn't properly handle the nested span structure used in trading tables where items are wrapped in `<span class="nowrap">` containers.

2. **Missing quantity parsing integration**: While the function has a `parse_quantity()` helper (lines 169-189), it's not being used effectively to extract quantity multipliers from the text before item names in trading tables.

3. **Invslot assumption**: The trading parser may be incorrectly assuming items will have "invslot" styling like crafting tables do, but trading tables use a simpler link-based structure.

4. **Edge case handling**: The parser needs to handle cases where:
   - Items can appear with or without quantity multipliers (e.g., "15 × Coal" vs "Emerald")
   - Multiple items can appear in a single cell (for trades requiring 2 input items)
   - The sprite-text span contains the display name while the href contains the URL

The specific HTML pattern in trading tables is:
```html
<span class="nowrap">
  <span class="sprite-file" style="">
    <span class="pixel-image" typeof="mw:File">
      <a href="/w/[Item_Name]" title="[Item Name]">
        <img alt="" src="/images/Invicon_[Item_Name].png" />
      </a>
    </span>
  </span>
  <a href="/w/[Item_Name]" title="[Item Name]">
    <span class="sprite-text">[Item Name]</span>
  </a>
</span>
```

The parser needs to find these `<a>` tags and extract items from them, not look for "invslot" elements.

## Relevant Files
Use these files to fix the bug:

- **src/core/parsers.py:679-777** - The `parse_trading()` function that needs to be fixed. This is where the HTML parsing logic for trading tables is located.

- **ai_doc/downloaded_pages/trading.html** - The source HTML file containing trading data. This file has 1546 lines of HTML with all villager trading tables.

- **tests/test_parsers.py** - Test file where we need to add or update tests for the trading parser to verify the fix works correctly.

- **output/transformations.csv** - The output file that should contain trading transformations after the fix.

- **src/core/data_models.py:1-96** - Contains the `Item` and `Transformation` data models used by the parser. Needed to understand the expected structure.

- **app_docs/feature-minecraft-transformation-extraction.md** - Documentation about the extraction system architecture and how parsers work.

## Step by Step Tasks

### Step 1: Analyze Trading HTML Structure
- Read a sample section of `ai_doc/downloaded_pages/trading.html` to understand the exact HTML pattern used for trading tables
- Document the specific nested span structure: `span.nowrap > span.sprite-file > a[href^="/w/"]`
- Identify how quantities are represented (text before the span structure, e.g., "15 × ")
- Note the difference between "Item wanted" and "Item given" columns

### Step 2: Fix the parse_trading() Function
- Modify `src/core/parsers.py` function `parse_trading()` (lines 679-777)
- Update the item extraction logic to:
  - Find all `<a href="/w/...">` tags within table cells (not just "invslot" elements)
  - Parse the full cell text to extract quantity multipliers using the existing `parse_quantity()` helper
  - Handle multiple items in a single cell (for multi-item trades)
  - Correctly extract item names from the link href or title attribute
- Ensure the function filters Java Edition content using the existing `is_java_edition()` helper
- Preserve the metadata structure (villager_type, level) that's already in the function

### Step 3: Add Test Cases for Trading Parser
- Add test cases to `tests/test_parsers.py` that verify:
  - Parsing a simple emerald-to-item trade (e.g., "5 Emeralds → Iron Helmet")
  - Parsing an item-to-emerald trade (e.g., "15 Coal → 1 Emerald")
  - Parsing trades with quantity multipliers
  - Parsing trades with multiple input items (if any exist)
  - Verifying that the parser extracts the correct villager_type and level metadata
- Use sample HTML snippets that match the actual trading.html structure

### Step 4: Run and Validate the Extraction
- Run the extraction script: `uv run python src/extract_transformations.py`
- Verify trading transformations are now extracted: `grep -c "^trading" output/transformations.csv`
- Spot check specific trades in the output:
  - `grep "Coal" output/transformations.csv | grep "trading"` (should find coal-to-emerald trades)
  - `grep "Iron Helmet" output/transformations.csv | grep "trading"` (should find emerald-to-helmet trades)
- Verify that both directions of trades are captured (buying with emeralds and selling for emeralds)

### Step 5: Run Full Test Suite
- Run the complete test suite to ensure no regressions: `uv run pytest tests/ -v`
- Verify all existing tests still pass
- Verify the new trading parser tests pass
- Check that trading transformations are properly integrated into the CSV export

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `uv run python src/extract_transformations.py` - Run extraction to generate transformations.csv with trading data
- `grep -c "^trading" output/transformations.csv` - Verify trading transformations are extracted (should be > 0, ideally 100+)
- `grep "Emerald" output/transformations.csv | grep "trading" | head -5` - Spot check emerald trades exist in output
- `uv run pytest tests/test_parsers.py -v -k trading` - Run trading-specific parser tests
- `uv run pytest tests/ -v` - Run full test suite to ensure zero regressions
- `uv run python src/validate_output.py` - Run validation script to check data quality

## Notes
- The trading parser should extract both directions of trades:
  - **Selling to villagers**: Item(s) → Emerald(s) - where items are input and emeralds are output
  - **Buying from villagers**: Emerald(s) → Item - where emeralds are input and items are output
- Trading tables in the wiki use a different HTML structure than crafting tables (no "invslot" divs)
- The quantity multiplier format is "N ×" (e.g., "15 ×", "5 ×") and appears before the item span structure
- Some trades may have 2 input items (e.g., "Emerald + Book → Enchanted Book") - the parser should handle this
- The parser should preserve villager profession and level information in the metadata field
- The fix should be surgical - only modify the `parse_trading()` function and add tests, don't refactor other parsers
