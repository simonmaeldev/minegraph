# Bug: Invalid Items in Transformation Data

## Bug Description
The transformation data extraction system is incorrectly including items that should not be in the dataset:
1. **"Bedrock Edition"** - appears as a composting ingredient (it's actually a caption/metadata text, not an item)
2. **"Wind Charge"** - appears in transformations but has no corresponding image file
3. **"Cerium Chloride"** - appears in crafting recipes (this is a Minecraft Education Edition chemistry item that should be filtered out)

These invalid items break data quality, create orphaned nodes in graph visualizations, and include content from non-Java Edition versions of Minecraft.

## Problem Statement
The HTML parsers in `src/core/parsers.py` are extracting item names from wiki page elements without proper context checking:
- They extract links from metadata/caption sections (infoboxes) instead of only from data tables
- They don't filter Education Edition chemistry items (compounds like chlorides, elements)
- The edition filtering logic doesn't catch inline edition markers in table cells

## Solution Statement
Enhance the parsing filters to:
1. Skip items extracted from infobox/metadata sections (class `infobox-imagecaption`)
2. Add Education Edition content detection by checking for inline edition markers
3. Create a blacklist of known Education Edition chemistry items
4. Improve the `is_java_edition()` filter to check table cell descriptions for edition markers

## Steps to Reproduce
1. Run the extraction: `uv run python src/extract_transformations.py`
2. Check items CSV: `grep -E "Bedrock Edition|Cerium Chloride|Wind Charge" output/items.csv`
3. Check transformations: `grep -E "Bedrock Edition|Cerium Chloride|Wind Charge" output/transformations.csv`
4. Observe: All three items appear in the output
5. Verify Wind Charge has no image: `ls images/ | grep -i "wind_charge"`

## Root Cause Analysis

### Issue 1: "Bedrock Edition" as Item
**File:** `ai_doc/downloaded_pages/composting.html`
**Location:** Lines 55-77 (infobox section)
**Root Cause:** The `parse_composting()` function extracts all links with `/w/` href pattern without checking if they're in metadata sections. The text "Bedrock Edition" appears in an `<div class="infobox-imagecaption">` element as an image caption showing different game versions, not as a composting ingredient.

### Issue 2: "Cerium Chloride" (Education Edition)
**File:** `ai_doc/downloaded_pages/crafting.html`
**Location:** Lines 2692-2700
**Root Cause:** Education Edition items are marked with inline edition markers in the **description column** (4th column) of recipe tables. The marker is: `<sup class="nowrap Inline-Template">...[Bedrock Edition and Minecraft Education only]</sup>`. The current `is_java_edition()` function only checks the recipe element itself and parent sections, but doesn't check sibling table cells for inline markers.

### Issue 3: "Wind Charge" Without Image
**File:** `ai_doc/downloaded_pages/crafting.html`
**Location:** Lines 4652-4660
**Root Cause:** Wind Charge actually DOES have an image in the wiki HTML (`/images/Invicon_Wind_Charge.png`), but the image may have failed to download or the item image URL has query parameters (`?711b5`) that cause issues. This needs investigation in the image download script.

## Relevant Files
Use these files to fix the bug:

- **src/core/parsers.py** (lines 1-1001)
  - Contains all parser functions that need enhancement
  - `extract_item_from_link()` (lines 99-128): Needs to check parent element classes
  - `is_java_edition()` (lines 13-52): Needs enhancement to check table cell siblings for inline markers
  - `parse_composting()` (lines 881-953): Needs to skip infobox sections
  - `parse_crafting()` (lines 217-414): Needs to check description column for edition markers

- **src/download_item_images.py**
  - May need fixes for handling image URLs with query parameters
  - Investigate why Wind Charge image isn't downloading

- **tests/test_parsers.py**
  - Add tests for filtering infobox links
  - Add tests for Education Edition inline markers
  - Add tests for chemistry item blacklist

### New Files
- **src/core/education_edition_blacklist.py**
  - Contains list of known Education Edition chemistry items to filter out

## Step by Step Tasks

### Step 1: Add infobox filtering to extract_item_from_link()
- Modify `extract_item_from_link()` function in `src/core/parsers.py`
- Add logic to check if the link's parent elements contain class `infobox-imagecaption` or `infobox`
- Return `None` if the link is within an infobox section
- This prevents metadata/caption text from being extracted as items

### Step 2: Enhance is_java_edition() to check inline edition markers
- Modify `is_java_edition()` function in `src/core/parsers.py`
- When checking table rows, iterate through all `<td>` cells in the row
- Look for `<sup class="nowrap Inline-Template">` elements
- Check if the sup element contains text like "Bedrock Edition and Minecraft Education only" or "Minecraft Education"
- Return `False` if found
- This catches inline edition markers that appear in description columns

### Step 3: Create Education Edition chemistry item blacklist
- Create new file `src/core/education_edition_blacklist.py`
- Add comprehensive list of Education Edition chemistry items:
  - All chlorides (Cerium Chloride, Mercuric Chloride, Potassium Chloride, Tungsten Chloride, etc.)
  - All elements (Carbon, Cerium, Magnesium, etc.)
  - All compounds (Salt, Sodium Hypochlorite, etc.)
  - All colored torches (Blue Torch, Red Torch, Purple Torch, Green Torch)
  - Sparklers, Glowsticks, Balloons, etc.
- Export as a set constant: `EDUCATION_EDITION_ITEMS`

### Step 4: Apply blacklist filter in extract_item_from_link()
- Import `EDUCATION_EDITION_ITEMS` in `src/core/parsers.py`
- In `extract_item_from_link()`, after extracting the item name
- Check if the name is in the blacklist
- Return `None` if found in blacklist
- This provides a safety net for known Education Edition items

### Step 5: Investigate Wind Charge image download issue
- Run `uv run python src/download_item_images.py --verbose` and check Wind Charge specifically
- Check if the image URL with query parameters (`?711b5`) causes issues
- Verify the image is being saved with correct filename
- May need to strip query parameters before saving files

### Step 6: Add comprehensive tests
- Add test case for filtering infobox links in `tests/test_parsers.py`
- Add test case for inline Education Edition markers in table cells
- Add test case for chemistry item blacklist filtering
- Add test case to ensure valid items like "Iron Chain" are NOT filtered
- Mock HTML snippets based on actual wiki structure

### Step 7: Run extraction and validate results
- Run `uv run python src/extract_transformations.py`
- Verify "Bedrock Edition" is NOT in items.csv or transformations.csv
- Verify "Cerium Chloride" and other chemistry items are NOT in output
- Verify "Wind Charge" either has an image or is excluded
- Check that all legitimate items are still present (Iron Chain, Copper Chain, etc.)

### Step 8: Run validation commands
- Execute all validation commands listed below
- Ensure zero regressions in test suite
- Verify data quality improvements

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `uv run pytest tests/ -v` - Run all tests to ensure zero regressions
- `uv run python src/extract_transformations.py` - Re-extract transformation data with fixes
- `grep -i "bedrock edition" output/items.csv` - Should return no results (filtered out)
- `grep -i "cerium chloride" output/items.csv` - Should return no results (Education Edition filtered)
- `grep -i "mercuric chloride" output/items.csv` - Should return no results (Education Edition filtered)
- `grep -i "wind charge" output/items.csv` - Check if present and valid
- `grep -i "iron chain" output/items.csv` - Should be present (verify no regression)
- `grep -i "copper chain" output/items.csv` - Should be present (verify no regression)
- `uv run python src/validate_output.py` - Run data quality validation
- `wc -l output/items.csv output/transformations.csv` - Count total items/transformations (should decrease slightly)

## Notes

### Education Edition Chemistry Items Pattern
Education Edition chemistry content follows these patterns:
- **Elements**: Single words often matching periodic table (Carbon, Helium, Nitrogen, etc.)
- **Compounds**: Chemical formulas as names (Sodium Hypochlorite, Hydrogen Peroxide, etc.)
- **Chlorides**: Pattern `<Element> Chloride` (Cerium Chloride, Mercuric Chloride, etc.)
- **Special items**: Colored torches, sparklers, glowsticks, balloons, heat blocks

### Inline Edition Markers
Look for these HTML patterns to detect Education Edition content:
```html
<sup class="nowrap Inline-Template">
  [<i><span title="This statement only applies to...">
    Bedrock Edition and Minecraft Education only
  </span></i>]
</sup>
```

### Infobox Structure
Infoboxes have this HTML structure:
```html
<div class="infobox-imagecaption">
  <p><i><a href="/w/Bedrock_Edition">Bedrock Edition</a></i></p>
</div>
```

### Testing Strategy
- Use actual HTML snippets from downloaded wiki pages for test cases
- Test both positive cases (should extract) and negative cases (should filter)
- Ensure blacklist doesn't accidentally filter valid items with similar names
- Validate that multi-slot alternatives still work correctly after changes
