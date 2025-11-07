# Bug: Missing Smelting Transformations in Output

## Bug Description
No smelting transformations appear in `output/transformations.csv` despite the smelting parser existing and being called during extraction. The output shows 0 smelting, 0 blast_furnace, and 0 smoker transformations when there should be hundreds of smelting recipes (e.g., Raw Iron → Iron Ingot, Raw Copper → Copper Ingot, etc.).

Expected behavior: Smelting recipes should be extracted from `ai_doc/downloaded_pages/smelting.html` and appear in the output CSV.

Actual behavior: Zero smelting transformations are extracted, resulting in an incomplete transformation graph.

## Problem Statement
The `parse_smelting()` function in `src/core/parsers.py` (lines 417-473) searches for mcui-based UI elements (e.g., `class="mcui.*Furnace"`), but the actual smelting.html page uses a **table-based structure** with `class="sortable wikitable"` instead. The HTML contains zero mcui elements, causing the parser to find no matches and return an empty list.

## Solution Statement
Rewrite the `parse_smelting()` function to parse the table-based HTML structure found in smelting.html. The new parser will:

1. Find all tables with class `"sortable wikitable"`
2. Identify the header row to locate "Product" (output) and "Ingredient" (input) columns
3. Parse each data row to extract output item from the first `<th>` cell and input item(s) from the first `<td>` cell
4. Handle multiple ingredient options separated by " or " by creating separate transformations for each option
5. Determine the furnace type (SMELTING, BLAST_FURNACE, or SMOKER) based on table context or section headings
6. Extract experience values from the experience column (optional metadata)
7. Filter out Java Edition content using the existing `is_java_edition()` helper

## Steps to Reproduce
1. Run extraction: `uv run python src/extract_transformations.py`
2. Check transformation types: `cut -d',' -f1 output/transformations.csv | sort | uniq -c`
3. Observe: No "smelting", "blast_furnace", or "smoker" entries appear in the output
4. Verify smelting.html exists: `ls -lah ai_doc/downloaded_pages/smelting.html` (file exists, 473KB)
5. Search for smelting in output: `grep -i "smelting" output/transformations.csv` (returns empty)

## Root Cause Analysis
The smelting wiki page structure differs fundamentally from crafting/smithing pages:

**Current Parser Assumption (WRONG):**
- Expects mcui UI elements: `<span class="mcui.*Furnace">...</span>`
- Looks for `mcui-input` and `mcui-output` sections
- Pattern: `soup.find_all("span", class_=re.compile(f"mcui.*{furnace_name}"))`

**Actual HTML Structure (CORRECT):**
- Uses standard wiki tables: `<table class="sortable wikitable">`
- Header row: `<tr><th>Product</th><th>Ingredient</th><th>Exp</th><th>Usage</th></tr>`
- Data rows: `<tr><th>[OUTPUT]</th><td>[INPUT]</td><td>[EXP]</td><td>[USAGE]</td></tr>`
- Items wrapped in `<span class="invslot">` with nested `<a href="/w/ItemName">` links
- Multiple ingredient options separated by `<br /> or <br />` in the same cell

**Evidence:**
- `grep -c "mcui" ai_doc/downloaded_pages/smelting.html` returns **0**
- File contains multiple tables with recipes like:
  - Iron Ingot ← Raw Iron (lines 228-236)
  - Copper Ingot ← Raw Copper (lines 237-245)
  - Gold Ingot ← Raw Gold OR Nether Gold Ore (lines 246-254)

## Relevant Files
Use these files to fix the bug:

### Existing Files to Modify
- **src/core/parsers.py** (lines 417-473)
  - Contains the broken `parse_smelting()` function
  - Needs complete rewrite to parse table structure instead of mcui elements
  - Should reuse existing helper functions: `extract_item_from_link()`, `is_java_edition()`

### Files to Reference
- **ai_doc/downloaded_pages/smelting.html**
  - Source data file containing smelting recipes in table format
  - Contains tables for: Food, Ore/Materials, Wasted Ores, Other Items, Furnace-only recipes
  - Lines 119-634 contain the main recipe tables

### Test Files
- **tests/test_parsers.py**
  - Contains existing tests for all parsers
  - Need to verify existing smelting tests or add new ones to validate table parsing

## Step by Step Tasks

### 1. Backup and analyze current implementation
- Read the current `parse_smelting()` function to understand its mcui-based approach
- Document what furnace types it attempts to detect (Furnace, Blast_Furnace, Smoker)
- Check if there are existing tests in `tests/test_parsers.py` for smelting

### 2. Implement table-based smelting parser
- Rewrite `parse_smelting()` to find tables with `class="sortable wikitable"`
- Parse table header to identify column indices for "Product" and "Ingredient"
- Extract output item from first `<th>` cell using `extract_item_from_link()`
- Extract input item(s) from first `<td>` cell, handling multiple invslot elements
- Handle " or " separators by creating separate transformations for each ingredient option
- Extract experience value from experience column (optional, store in metadata)
- Apply `is_java_edition()` filtering to tables

### 3. Determine furnace type classification
- Analyze section headings in smelting.html to determine which recipes go to which furnace type
- Implement logic to assign TransformationType.SMELTING, BLAST_FURNACE, or SMOKER
- For MVP: Default all to TransformationType.SMELTING (can refine later with section parsing)
- Add deduplication using `seen_signatures` set (pattern from other parsers)

### 4. Test the updated parser
- Run extraction: `uv run python src/extract_transformations.py`
- Verify smelting recipes appear: `grep -i "smelting" output/transformations.csv | head -5`
- Check specific recipes exist: `grep "Iron Ingot" output/transformations.csv`
- Validate count: `cut -d',' -f1 output/transformations.csv | sort | uniq -c`

### 5. Run validation commands
- Execute all validation commands listed below to ensure the fix works with zero regressions
- Verify no existing transformations were broken (crafting, smithing, etc. counts remain the same)
- Confirm smelting transformations are now present in output

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `uv run python src/extract_transformations.py` - Re-run extraction to generate new output with smelting recipes
- `grep "smelting\|blast_furnace\|smoker" output/transformations.csv | wc -l` - Count smelting-related transformations (should be > 0)
- `grep "Iron Ingot" output/transformations.csv` - Verify Iron Ingot smelting recipe exists
- `grep "Copper Ingot" output/transformations.csv` - Verify Copper Ingot smelting recipe exists
- `cut -d',' -f1 output/transformations.csv | sort | uniq -c` - Show breakdown of all transformation types
- `uv run pytest tests/test_parsers.py -v -k smelting` - Run smelting-specific tests (if they exist)
- `uv run pytest tests/ -v` - Run full test suite to ensure no regressions

## Notes

### Furnace Type Classification Strategy
The smelting.html page contains recipes for three furnace types, but they may not be clearly separated in the HTML structure. For this bug fix:

1. **MVP Approach**: Classify all smelting recipes as `TransformationType.SMELTING` initially
2. **Future Enhancement**: Parse section headings to differentiate:
   - Regular Furnace: Most recipes
   - Blast Furnace: Ore smelting (faster for ores)
   - Smoker: Food recipes (faster for food)

### Multiple Ingredient Handling
Per user confirmation, when a recipe has multiple ingredient options (e.g., "Raw Gold OR Nether Gold Ore"):
- Create **separate transformations** for each option
- Example: Gold Ingot ← Raw Gold (one edge) AND Gold Ingot ← Nether Gold Ore (another edge)
- This matches the existing crafting parser's alternative handling approach

### Deduplication Strategy
Use the same pattern as other parsers (crafting, smithing, etc.):
```python
seen_signatures = set()
# ... for each recipe:
sig = transformation.get_signature()
if sig not in seen_signatures:
    seen_signatures.add(sig)
    transformations.append(transformation)
```

### HTML Structure Pattern
All smelting recipes follow this structure:
```html
<tr>
  <th><!-- OUTPUT: first <a href="/w/OutputItem"> link --></th>
  <td><!-- INPUT: one or more <a href="/w/InputItem"> links, separated by " or " --></td>
  <td><!-- EXPERIENCE VALUE --></td>
  <td><!-- USAGE DESCRIPTION --></td>
</tr>
```

### Edge Cases to Handle
- Recipes with multiple ingredient options (e.g., gold ore variants)
- Empty rows or header rows in tables
- Bedrock Edition filtering (use existing `is_java_edition()` helper)
- Tables that aren't recipe tables (e.g., fuel/combustible tables - ignore these)
