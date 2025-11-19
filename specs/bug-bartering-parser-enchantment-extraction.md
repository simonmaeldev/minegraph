# Bug: Bartering Parser Incorrectly Extracts Enchantments as Items

## Bug Description
The bartering parser is extracting 20 items when it should only extract 19. The issue is that "Soul Speed" is being extracted as a separate bartering item, when it's actually an enchantment that applies to "Enchanted Book" and "Iron Boots", not a standalone item that piglins give.

**Symptoms:**
- Running `grep -c "^bartering," output/transformations.csv` returns 20 instead of expected 19
- "Soul Speed" appears as a separate transformation: `bartering,"[""Gold Ingot""]","[""Soul Speed""]",{}`
- Both "Enchanted Book" and "Soul Speed" are extracted from the same table cell

**Expected behavior:**
- Only extract 19 items from bartering table
- "Soul Speed" should NOT be extracted as a standalone item
- Only "Enchanted Book" should be extracted (the enchantment is metadata, not an output item)
- Only "Iron Boots" should be extracted (the Soul Speed enchantment on it is metadata)

**Actual behavior:**
- 20 items are extracted
- "Soul Speed" is incorrectly extracted as a bartering output item

## Problem Statement
The bartering parser currently extracts all links (`<a>` tags) within the "Item given" cell, but some cells contain both the item link and enchantment links. In the bartering table, the structure is:

```html
<td>
  <span class="nowrap">
    <a href="/w/Enchanted_Book">Enchanted Book</a>
  </span>
  <br />with <a href="/w/Soul_Speed">Soul Speed</a> (random level)
</td>
```

The parser extracts both "Enchanted Book" (correct) and "Soul Speed" (incorrect). "Soul Speed" is an enchantment applied to the book, not an item that piglins give directly.

## Solution Statement
Modify the `parse_bartering()` function in `src/core/parsers.py` to only extract the primary item link and skip enchantment links that appear after "with" text. The fix should:

1. Only extract links that are within the primary `<span class="nowrap">` wrapper (the first item link in each cell)
2. Skip any links that appear after `<br />with` text pattern
3. Ensure enchantment links (Soul Speed, etc.) are not extracted as standalone items

This preserves the correct behavior of extracting 19 items while excluding the Soul Speed enchantment.

## Steps to Reproduce
1. Run the extraction pipeline: `uv run python src/extract_transformations.py`
2. Count bartering transformations: `grep -c "^bartering," output/transformations.csv`
3. Observe: Returns 20 (incorrect)
4. Check for Soul Speed: `grep "^bartering," output/transformations.csv | grep "Soul Speed"`
5. Observe: Soul Speed appears as a separate transformation (incorrect)

## Root Cause Analysis
The root cause is in `src/core/parsers.py` lines 1268-1342, specifically the section that extracts items from links:

```python
item_links = item_given_cell.find_all("a", href=re.compile(r"^/w/"))

for link in item_links:
    # ... processes ALL links in the cell
```

The current code finds ALL `<a>` tags in the cell and processes them. However, in cells with enchanted items, there are multiple links:
1. The primary item link (e.g., "Enchanted Book")
2. The enchantment link after "with" text (e.g., "Soul Speed")

The parser doesn't distinguish between these two types of links, treating both as separate bartering outputs.

The HTML structure shows:
- Primary item is within first `<span class="nowrap">` element
- Enchantment appears after `<br />with` and before `(random level)` text
- Multiple cells have this pattern: Enchanted Book with Soul Speed, Iron Boots with Soul Speed

## Relevant Files
Use these files to fix the bug:

- **`src/core/parsers.py`** (lines 1217-1343: `parse_bartering()` function)
  - Contains the bartering parser logic that extracts items from the "Item given" column
  - Lines 1268-1342 contain the link extraction loop that needs modification
  - Need to add logic to skip enchantment links that appear after "with" text
  - Should only extract the first/primary item link in each cell

- **`tests/test_parsers.py`** (lines 1489-1700: `TestParseBartering` class)
  - Contains unit tests for bartering parser
  - Need to add test case for enchanted items with "with" pattern
  - Should verify Soul Speed is NOT extracted as separate item
  - Should verify Enchanted Book and Iron Boots ARE extracted correctly

- **`ai_doc/downloaded_pages/bartering.html`**
  - The actual HTML file containing the bartering table
  - Used to verify the fix works with real wiki data
  - Contains the problematic cells with "with Soul Speed" pattern

- **`output/transformations.csv`**
  - Output file to verify fix
  - Should contain exactly 19 bartering transformations after fix
  - Should NOT contain Soul Speed as output item

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Reproduce the bug
- Run extraction: `uv run python src/extract_transformations.py`
- Count bartering items: `grep -c "^bartering," output/transformations.csv`
- Verify it returns 20 (incorrect count)
- Check for Soul Speed: `grep "^bartering," output/transformations.csv | grep "Soul Speed"`
- Verify Soul Speed appears as separate item (the bug)

### Step 2: Analyze the HTML structure
- Examine the bartering.html file to understand the enchantment pattern
- Identify cells with "with <a>enchantment</a>" pattern
- Confirm that Enchanted Book and Iron Boots both have "with Soul Speed" text
- Note that primary items are in first `<span class="nowrap">` wrapper
- Note that enchantment links appear after `<br />with` text

### Step 3: Fix the parser logic
- Open `src/core/parsers.py`
- Locate the `parse_bartering()` function (line 1217)
- Find the link extraction loop (around line 1268)
- Modify the logic to skip enchantment links:
  - Option A: Only extract links within the first `<span class="nowrap">` element
  - Option B: Skip links that have "with" text before them in the cell
  - Option C: Check if the link's previous sibling text contains "with"
- Implement the chosen approach to filter out enchantment links
- Ensure the fix is minimal and surgical (don't break other functionality)

### Step 4: Write test case for enchanted items
- Open `tests/test_parsers.py`
- Add new test method: `test_parse_bartering_excludes_enchantments()`
- Create mock HTML with structure matching real bartering page:
  ```html
  <td>
    <span class="nowrap">
      <a href="/w/Enchanted_Book">Enchanted Book</a>
    </span>
    <br />with <a href="/w/Soul_Speed">Soul Speed</a> (random level)
  </td>
  ```
- Assert that only "Enchanted Book" is extracted
- Assert that "Soul Speed" is NOT extracted
- Assert total count is 1, not 2

### Step 5: Run unit tests
- Run the new test: `uv run pytest tests/test_parsers.py::TestParseBartering::test_parse_bartering_excludes_enchantments -v`
- Verify it passes with the fix
- Run all bartering tests: `uv run pytest tests/test_parsers.py::TestParseBartering -v`
- Verify all existing tests still pass (no regressions)

### Step 6: Run full test suite
- Run all parser tests: `uv run pytest tests/test_parsers.py -v`
- Verify no regressions in other parsers
- Run full test suite: `uv run pytest tests/ -v`
- Ensure all tests pass

### Step 7: Run validation commands
- Execute all validation commands listed below
- Verify bartering count is now 19 (not 20)
- Verify Soul Speed is NOT in output
- Verify Enchanted Book and Iron Boots ARE in output
- Verify all other expected items are present

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

```bash
# Run new test for enchantment filtering
uv run pytest tests/test_parsers.py::TestParseBartering::test_parse_bartering_excludes_enchantments -v

# Run all bartering tests
uv run pytest tests/test_parsers.py::TestParseBartering -v

# Run all parser tests to ensure no regressions
uv run pytest tests/test_parsers.py -v

# Run full test suite
uv run pytest tests/ -v

# Re-run extraction pipeline with fixed parser
uv run python src/extract_transformations.py

# Count bartering transformations (should be 19, not 20)
grep -c "^bartering," output/transformations.csv

# Expected output: 19

# Verify Soul Speed is NOT in bartering output (should return nothing)
grep "^bartering," output/transformations.csv | grep '"Soul Speed"'

# Expected output: (empty - no results)

# Verify Enchanted Book IS in bartering output (should find it)
grep "^bartering," output/transformations.csv | grep '"Enchanted Book"'

# Expected output: bartering,"[""Gold Ingot""]","[""Enchanted Book""]",{}

# Verify Iron Boots IS in bartering output (should find it)
grep "^bartering," output/transformations.csv | grep '"Iron Boots"'

# Expected output: bartering,"[""Gold Ingot""]","[""Iron Boots""]",{}

# List all 19 bartering items to verify they're correct
grep "^bartering," output/transformations.csv | sed 's/.*\["\([^"]*\)"\]$/\1/' | sort

# Expected items (19 total):
# - Enchanted Book (with Soul Speed enchantment, but Soul Speed itself not listed)
# - Iron Boots (with Soul Speed enchantment, but Soul Speed itself not listed)
# - Splash Potion of Fire Resistance
# - Potion of Fire Resistance
# - Water Bottle
# - Iron Nugget
# - Ender Pearl
# - String
# - Nether Quartz
# - Obsidian
# - Fire Charge
# - Crying Obsidian
# - Leather
# - Soul Sand
# - Nether Brick
# - Spectral Arrow (JE only)
# - Gravel
# - Blackstone
# - (one more item to verify in actual output)

# Validate overall output quality
uv run python src/validate_output.py

# Run spot checks for other transformation types (ensure no regressions)
grep "^crafting," output/transformations.csv | wc -l
grep "^trading," output/transformations.csv | wc -l
grep "^mob_drop," output/transformations.csv | wc -l
```

## Notes
- **Expert rule**: Enchantments like "Soul Speed" that appear after "with" text are modifiers/metadata, not standalone items
- **Pattern to detect**: Look for `<br />with <a>enchantment</a>` structure in HTML
- **Other affected parsers**: Check if trading, mob_drops, or other parsers have similar issues with enchanted items
- **Minimal fix**: Only modify the link extraction logic in `parse_bartering()` - don't refactor or change other parts
- **Surgical approach**: This is a targeted bug fix, not a feature enhancement
- **Test thoroughly**: Ensure the fix handles both Enchanted Book and Iron Boots cases
- **No false positives**: Make sure legitimate items with "with" in their name aren't filtered
- **Edge case**: Verify that items appearing on same line but without "with" (like Arrow/Spectral Arrow with edition markers) still work correctly
