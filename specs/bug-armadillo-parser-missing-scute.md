# Bug: Armadillo Parser Missing 'Armadillo Scute' Drop

## Bug Description
The armadillo mob parser is not extracting the "Armadillo Scute" item from the armadillo's HTML page. The armadillo page has a unique structure where the scute drop is documented in a "Brushing" subsection under "Drops", but this section doesn't use a wikitable format. Instead, it uses a simple `<ul><li>` structure with sprite links.

**Expected behavior**: Armadillo → Armadillo Scute transformation should be extracted
**Actual behavior**: No transformations are extracted for armadillo

## Problem Statement
The `parse_mob_drops` function in `src/core/parsers.py` only parses items from wikitable tables within the "Drops" section. The armadillo's "Brushing" subsection contains the scute drop in a simple list format that the current parser doesn't handle.

## Solution Statement
Add special handling for the armadillo's "Brushing" subsection to extract items from list (`<ul><li>`) elements in addition to existing wikitable parsing. This will be implemented as an armadillo-specific expert rule that checks for the "Brushing" subsection ID and extracts items from list elements.

## Steps to Reproduce
1. Run `uv run python src/extract_transformations.py`
2. Check `output/transformations.csv` for armadillo transformations
3. Search for "Armadillo" in the transformations - no "Armadillo Scute" found
4. Only crafting transformation exists: `Armadillo Scute → Wolf Armor`

## Root Cause Analysis
The `parse_mob_drops` function at line 882 in `src/core/parsers.py` has the following logic:
1. Find the "Drops" section heading
2. Look for subsections under "Drops"
3. For each subsection, find wikitable tables and parse them

The armadillo's HTML structure for the scute drop is:
```html
<h3><span class="mw-headline" id="Brushing">Brushing</span></h3>
<p>If a player or dispenser uses a brush on an armadillo, it drops:</p>
<ul>
  <li>1 <a href="/w/Armadillo_Scute" title="Armadillo Scute">Armadillo Scute</a></li>
</ul>
```

This doesn't match the wikitable pattern, so the parser skips it. The function only calls `_parse_drops_table()` which looks for `<table class="wikitable">` elements.

## Relevant Files
Use these files to fix the bug:

- **src/core/parsers.py** (lines 882-1015)
  - Contains the `parse_mob_drops` function that needs to be updated
  - Currently only parses wikitable tables
  - Needs to add logic to parse list elements (`<ul><li>`) in the "Brushing" subsection

- **ai_doc/downloaded_pages/mobs/armadillo.html**
  - The HTML source file that contains the armadillo page structure
  - Used to understand the exact HTML pattern to match

- **tests/test_parsers.py**
  - Contains tests for parser functions
  - Need to add a test case for armadillo to verify "Armadillo Scute" is extracted

## Step by Step Tasks

### 1. Add armadillo-specific parsing logic to parse_mob_drops
- In `src/core/parsers.py`, modify the `parse_mob_drops` function (around line 979-1000)
- After the existing subsection table parsing loop, add special handling for "Brushing" subsection
- Create a helper function or inline logic to extract items from `<ul><li>` elements
- Only apply this logic for subsections with id="Brushing" to avoid affecting other parsers
- Use `extract_item_from_link` to extract items from `<a href="/w/...">` links within the list items

### 2. Test the fix manually
- Run `uv run python src/extract_transformations.py` to regenerate transformations
- Verify that "Armadillo → Armadillo Scute" appears in `output/transformations.csv`
- Check that no other mob drops are affected by inspecting the transformation count

### 3. Write a unit test for armadillo parser
- In `tests/test_parsers.py`, add a test function `test_parse_mob_drops_armadillo`
- Load the armadillo HTML from `ai_doc/downloaded_pages/mobs/armadillo.html`
- Call `parse_mob_drops(html, "Armadillo")`
- Assert that exactly 1 transformation exists: Armadillo → Armadillo Scute
- Verify the transformation type is MOB_DROP

### 4. Run validation commands
- Execute all validation commands listed below to ensure zero regressions

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `uv run python src/extract_transformations.py` - Regenerate transformations with the fix
- `uv run python -c "from src.core.parsers import parse_mob_drops; from pathlib import Path; html = Path('ai_doc/downloaded_pages/mobs/armadillo.html').read_text(); t = parse_mob_drops(html, 'Armadillo'); print(f'Found {len(t)} transformations'); [print(f'{x.inputs[0].name} -> {x.outputs[0].name}') for x in t]"` - Verify armadillo parser extracts scute
- `grep -i "armadillo scute" output/transformations.csv` - Confirm "Armadillo Scute" appears in transformations
- `uv run pytest tests/test_parsers.py -v -k armadillo` - Run armadillo-specific test
- `uv run pytest tests/ -v` - Run all tests to ensure no regressions

## Notes
- This is an armadillo-specific expert rule, as requested by the user
- The fix should be surgical: only add logic to handle the "Brushing" subsection pattern
- Do not modify the existing wikitable parsing logic - it works correctly for other mobs
- The "Brushing" subsection is unique to armadillo; other mobs use standard wikitable formats
- Ensure the fix doesn't break other mob parsers (sheep, chicken, cow, etc.)
