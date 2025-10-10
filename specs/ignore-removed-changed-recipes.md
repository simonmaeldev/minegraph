# Bug: Parser Includes Removed and Changed Recipe Sections

## Bug Description
The crafting parser (`parse_crafting()`) currently processes ALL content on the crafting.html page, including historical sections like "Removed recipes" and "Changed recipes". These sections contain recipes that are no longer valid in current Minecraft Java Edition and should not be included in the transformation data.

**Symptoms:**
- The parser extracts crafting UI elements from sections that document historical/obsolete recipes
- These invalid recipes pollute the transformation dataset with items and transformations that don't exist in current gameplay
- Users of the data may attempt to use recipes that were removed from the game

**Expected Behavior:**
- Only extract recipes that are currently valid in Minecraft Java Edition
- Skip sections with IDs: `Removed_recipes`, `Changed_recipes`
- Ensure all extracted transformations represent current, usable game mechanics

**Actual Behavior:**
- Parser processes the entire HTML page indiscriminately
- Historical and obsolete recipes are included in output CSV files

## Problem Statement
The `parse_crafting()` function in `src/core/parsers.py` needs to filter out HTML sections that contain removed or changed recipes to ensure only current, valid recipes are extracted into the transformation dataset.

## Solution Statement
Modify the `parse_crafting()` function to skip processing crafting UI elements that are descendants of sections with IDs `Removed_recipes` or `Changed_recipes`. This will be accomplished by:
1. Detecting when a crafting UI element is within one of these excluded sections
2. Skipping that element during the parsing loop
3. Maintaining all existing parsing logic for valid recipes

## Steps to Reproduce
1. Run: `uv run python src/extract_transformations.py`
2. Examine: `output/transformations.csv`
3. Check if the CSV contains any recipes from the "Removed recipes" or "Changed recipes" sections
4. Compare transformation count before and after the fix

Note: To verify the bug exists, you would need to manually inspect the HTML at lines 6157-7293 (Changed recipes) and 7294+ (Removed recipes) to see if any crafting UI elements exist there, then check if those recipes appear in the CSV output.

## Root Cause Analysis
**Location**: `src/core/parsers.py`, function `parse_crafting()`, lines 130-304

**Analysis**:
1. Lines 144-146: The function finds ALL crafting table UI elements in the entire HTML:
   ```python
   crafting_uis = soup.find_all("span", class_=re.compile(r"mcui.*Crafting.*Table"))
   ```
   This search is global and doesn't exclude any sections.

2. Lines 147-302: Each UI element is processed if it passes the `is_java_edition()` filter
   - The `is_java_edition()` filter only checks for Bedrock/Education markers
   - It does NOT check if the element is in a "Removed recipes" or "Changed recipes" section

3. The HTML structure shows these sections have identifiable heading IDs:
   - Line 6157: `<h3><span class="mw-headline" id="Changed_recipes">`
   - Line 7294: `<h3><span class="mw-headline" id="Removed_recipes">`

4. Any crafting UI elements within these sections are currently being processed and included in the output, even though they represent obsolete recipes.

**Root Cause**: No logic exists to exclude elements based on their parent section's ID or semantic meaning. The parser treats all crafting UIs equally regardless of context.

## Relevant Files
Use these files to fix the bug:

- **src/core/parsers.py** (lines 130-304)
  - Contains `parse_crafting()` function that needs modification
  - Line 144-146: Where crafting UI elements are found
  - Line 147: Where filtering logic should be added
  - Function `is_java_edition()` provides a model for section-based filtering

- **tests/test_parsers.py**
  - Existing test suite for parsers
  - Validates that current tests still pass after fix
  - Contains examples of how to structure parser tests

- **ai_doc/downloaded_pages/crafting.html** (lines 6157-7294+)
  - Contains the "Changed recipes" section (starts line 6157)
  - Contains the "Removed recipes" section (starts line 7294)
  - Used to understand HTML structure and validate fix

### New Files

- **tests/test_exclude_historical_recipes.py**
  - New test file to validate that removed/changed recipes are excluded
  - Will test that UI elements within these sections are properly skipped

## Step by Step Tasks

### Step 1: Create helper function to detect excluded sections
- Add new function `is_in_excluded_section(element: Tag) -> bool` in `src/core/parsers.py`
- Function should check if element is a descendant of sections with IDs: `Removed_recipes`, `Changed_recipes`
- Use BeautifulSoup's `find_parent()` or similar method to traverse up the DOM tree
- Look for parent elements with `id` attribute matching excluded section names
- Return `True` if element is in excluded section, `False` otherwise

### Step 2: Integrate exclusion logic into parse_crafting
- Modify `src/core/parsers.py` in the `parse_crafting()` function (line 147)
- Add check after `is_java_edition()` filter:
  ```python
  if not is_java_edition(ui):
      continue
  if is_in_excluded_section(ui):  # NEW CHECK
      continue
  ```
- This ensures historical recipes are skipped before any processing occurs

### Step 3: Create comprehensive tests for exclusion logic
- Create `tests/test_exclude_historical_recipes.py`
- Test 1: `test_excludes_removed_recipes_section()`
  - Create HTML with a crafting UI inside `<section id="Removed_recipes">` or similar structure
  - Verify `parse_crafting()` returns empty list or doesn't include that recipe
- Test 2: `test_excludes_changed_recipes_section()`
  - Create HTML with a crafting UI inside a section with `id="Changed_recipes"`
  - Verify recipe is not extracted
- Test 3: `test_accepts_valid_current_recipes()`
  - Create HTML with a crafting UI NOT in any excluded section
  - Verify recipe IS extracted normally
- Test 4: `test_helper_function_detects_excluded_sections()`
  - Unit test for `is_in_excluded_section()` helper function
  - Test with various HTML structures

### Step 4: Validate fix with existing tests
- Run `uv run pytest tests/test_parsers.py -v`
- Ensure all existing tests pass (no regressions)
- Verify Bedrock/Education filtering still works
- Verify multi-slot alternative parsing still works

### Step 5: Execute validation commands and verify outputs
- Run full validation command suite (see Validation Commands section)
- Compare transformation counts before and after fix
- Manually inspect a sample of the HTML sections to confirm excluded recipes exist
- Verify the CSV no longer contains those recipes

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `uv run pytest tests/test_exclude_historical_recipes.py -v` - Validate new exclusion tests pass
- `uv run pytest tests/test_parsers.py -v` - Ensure existing parser tests still pass
- `uv run pytest tests/ -v` - Run complete test suite for zero regressions
- `uv run python src/extract_transformations.py` - Re-extract transformations with fixed parser
- `wc -l output/transformations.csv` - Count transformations (should be fewer than before fix)
- `grep -i "removed\|changed" output/transformations.csv || echo "No historical recipes found (expected)"` - Verify no removed/changed recipes in output

## Notes
- The exclusion check should happen AFTER the `is_java_edition()` check for efficiency
- This fix is specific to crafting.html; other parser functions (smelting, brewing, etc.) may not have similar sections, but the pattern could be reused if needed
- The helper function `is_in_excluded_section()` should be generic enough to handle additional section IDs if needed in the future (e.g., `Experimental_recipes`)
- Consider making the list of excluded section IDs a constant at the module level for easy maintenance:
  ```python
  EXCLUDED_CRAFTING_SECTIONS = {"Removed_recipes", "Changed_recipes"}
  ```
- This fix improves data quality by ensuring only current, valid game mechanics are represented in the transformation graph
