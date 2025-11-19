# Feature: Tool Page Crafting Parser

## Feature Description
Implement a specialized HTML parser for the Minecraft Wiki Tool page (https://minecraft.wiki/w/Tool) that extracts crafting recipes from the page's crafting section. The parser will handle animated/cycling recipe graphics that show multiple alternative ingredients (e.g., "any stone" cycling through cobblestone, cobbled deepslate, and blackstone) and create separate transformation records for each valid recipe combination.

## User Story
As a Minegraph user
I want to extract all tool crafting recipes from the Tool wiki page including all alternative ingredient combinations
So that the transformation graph contains complete crafting data for all tool variants (e.g., stone hoe with cobblestone, stone hoe with cobbled deepslate, stone hoe with blackstone)

## Problem Statement
The current system extracts crafting recipes from the main Crafting page, but the Tool page contains additional organized crafting data with clear categorization. The Tool page uses animated crafting UI elements that cycle through alternative ingredients (indicated by words like "any" in the ingredients column), requiring special handling to extract all valid recipe combinations. Without this parser, the graph may be missing tool crafting recipes or may not capture all valid ingredient alternatives.

## Solution Statement
Create a new parser function `parse_tool_crafting()` that:
1. Downloads the Tool wiki page to `ai_doc/downloaded_pages/tool.html` using curl
2. Parses the crafting section's table structure (name, ingredients, crafting recipe GUI, description)
3. Detects animated/cycling recipes in the crafting UI elements
4. Extracts each combination as a separate crafting transformation
5. Uses the existing `TransformationType.CRAFTING` enum and metadata with `category: "crafting"` or a more specific category based on the section heading
6. Follows the same patterns as existing parsers for Java Edition filtering, item extraction, and deduplication

## Relevant Files
Use these files to implement the feature:

### Existing Files

- **src/core/parsers.py** (line 256-453) - Contains the main `parse_crafting()` function which handles animated slots via `find_item_in_slot()` and multi-slot alternatives. The new `parse_tool_crafting()` function will follow similar patterns for extracting items from crafting UI elements and handling alternatives.

- **src/core/parsers.py** (line 192-215) - The `find_item_in_slot()` helper function finds all items in an inventory slot, including animated alternatives. This will be the key function for detecting cycling ingredients in Tool page recipes.

- **src/core/parsers.py** (line 108-167) - The `extract_item_from_link()` helper extracts Item objects from wiki links with proper filtering for Education Edition items and inline edition markers.

- **src/core/parsers.py** (line 14-61) - Contains `is_java_edition()` helper for filtering out Bedrock/Education Edition content, which must be used in the new parser.

- **src/core/parsers.py** (line 218-253) - The `extract_category_from_element()` helper traverses the DOM to find section headings for categorization metadata.

- **src/core/download_data.py** (line 10-21) - The `WIKI_PAGES` dictionary maps page names to URLs. Need to add `"tool": "https://minecraft.wiki/w/Tool"` entry here.

- **src/core/download_data.py** (line 119-171) - The `download_page()` function handles downloading wiki pages with curl and caching. This will be used to download the Tool page.

- **src/extract_transformations.py** (line 60-70) - The `parsers` dictionary maps HTML filenames to parser functions. Need to add `"tool.html": parse_tool_crafting` entry here.

- **src/extract_transformations.py** (line 12-23) - Import statements for parser functions. Need to add `parse_tool_crafting` to the imports from `core.parsers`.

- **src/core/data_models.py** - Contains `Item`, `Transformation`, and `TransformationType` dataclasses. The new parser will use `TransformationType.CRAFTING` and follow the same patterns for creating transformations.

### New Files

- **tests/test_tool_parser.py** - New test file to validate the Tool page parser with sample HTML fixtures and edge cases for animated ingredients.

- **tests/fixtures/tool_crafting_sample.html** - HTML fixture containing sample Tool page structure with animated crafting recipes for testing.

## Implementation Plan

### Phase 1: Foundation
Add infrastructure for downloading and parsing the Tool page:
1. Add Tool page URL to `WIKI_PAGES` dictionary in `src/core/download_data.py`
2. Download the Tool page HTML manually using curl and save to `ai_doc/downloaded_pages/tool.html`
3. Inspect the downloaded HTML to understand the exact structure of the crafting section table

### Phase 2: Core Implementation
Implement the parser function following existing patterns:
1. Create `parse_tool_crafting()` function in `src/core/parsers.py` following the structure of `parse_crafting()`
2. Use BeautifulSoup to find the crafting section (likely an h2/h3 heading with id "Crafting")
3. Parse the table structure to extract name, ingredients, crafting recipe GUI, and description columns
4. Use `find_item_in_slot()` to detect all items in each crafting slot (handles animated alternatives automatically)
5. Create separate `Transformation` objects for each combination when alternatives are present
6. Apply Java Edition filtering using `is_java_edition()`
7. Apply deduplication using signature-based seen tracking (pattern from existing parsers)
8. Extract category metadata using `extract_category_from_element()` or hardcode `"crafting"`

### Phase 3: Integration
Connect the new parser to the extraction pipeline:
1. Add `parse_tool_crafting` import to `src/extract_transformations.py`
2. Add `"tool.html": parse_tool_crafting` to the parsers dictionary in `extract_all_transformations()`
3. Create test fixtures with sample Tool page HTML showing animated crafting recipes
4. Write comprehensive tests covering single recipes, animated alternatives, and edge cases
5. Run the extraction pipeline and validate output contains Tool crafting recipes

## Step by Step Tasks

### Step 1: Download and Inspect Tool Page
- Download the Tool page using curl to `ai_doc/downloaded_pages/tool.html`
- Inspect the HTML structure to understand the crafting section layout
- Identify the table headers and row structure
- Locate example recipes with animated ingredients (e.g., stone hoe with "any stone")
- Document the HTML patterns for the implementation

### Step 2: Add Tool Page to Download Configuration
- Edit `src/core/download_data.py`
- Add `"tool": "https://minecraft.wiki/w/Tool"` to `WIKI_PAGES` dictionary
- Verify the page can be downloaded using the `download_page()` function

### Step 3: Implement parse_tool_crafting() Function
- Edit `src/core/parsers.py`
- Create `parse_tool_crafting(html_content: str) -> List[Transformation]` function
- Use BeautifulSoup to parse HTML and find the crafting section
- Locate the crafting table (likely with class "wikitable")
- Parse table headers to identify column indices for name, ingredients, crafting recipe, description
- Iterate through table rows and extract data from each column
- For each row, find crafting UI elements (class `mcui.*Crafting.*Table`)
- Use `find_item_in_slot()` to extract input items from mcui-input section
- Use `find_item_in_slot()` to extract output item from mcui-output section
- Handle animated slots by creating separate transformations for each alternative
- Apply `is_java_edition()` filtering
- Apply deduplication using `seen_signatures` set
- Extract category using `extract_category_from_element()` or hardcode `"crafting"`
- Return list of Transformation objects

### Step 4: Create Test Fixtures
- Create `tests/fixtures/` directory if it doesn't exist
- Create `tests/fixtures/tool_crafting_sample.html` with sample HTML
- Include examples of:
  - Simple tool recipe (e.g., wooden pickaxe)
  - Animated alternative recipe (e.g., stone hoe with 3 stone variants)
  - Multiple tools in the same section
- Ensure fixture includes proper mcui crafting UI structure

### Step 5: Write Comprehensive Tests
- Create `tests/test_tool_parser.py`
- Import `parse_tool_crafting` from `src.core.parsers`
- Test basic recipe extraction (single non-animated recipe)
- Test animated alternative expansion (stone hoe should create 3 transformations)
- Test Java Edition filtering (exclude Bedrock content if present)
- Test deduplication (duplicate recipes should be filtered)
- Test output item extraction (tool names are correct)
- Test input item extraction (ingredients are correct)
- Test category metadata (category field is populated)
- Run tests with `uv run pytest tests/test_tool_parser.py -v`

### Step 6: Integrate Parser into Extraction Pipeline
- Edit `src/extract_transformations.py`
- Add `parse_tool_crafting` to the import list from `core.parsers`
- Add `"tool.html": parse_tool_crafting` entry to the `parsers` dictionary
- Verify the integration by running `uv run python src/extract_transformations.py`

### Step 7: Run End-to-End Extraction and Validation
- Run the full extraction pipeline: `uv run python src/extract_transformations.py`
- Verify tool.html is processed and transformations are extracted
- Check output/transformations.csv for tool crafting recipes
- Verify stone hoe has 3 separate transformation records (one for each stone type)
- Run validation: `uv run python src/validate_output.py`
- Verify no errors or warnings related to Tool page data
- Spot-check specific tool recipes in the CSV output (e.g., wooden pickaxe, stone hoe, iron axe)

### Step 8: Run Full Test Suite and Document Results
- Run complete test suite: `uv run pytest tests/ -v`
- Ensure all tests pass including the new Tool parser tests
- Verify test coverage for the new parser function
- Document the number of tool transformations extracted
- Compare with existing crafting transformations to check for overlap or new additions

## Testing Strategy

### Unit Tests
- **test_parse_tool_crafting_basic**: Parse a simple tool recipe without alternatives
- **test_parse_tool_crafting_animated_alternatives**: Parse stone hoe with 3 stone variants, verify 3 separate transformations created
- **test_parse_tool_crafting_java_edition_filtering**: Verify Bedrock/Education content is filtered out
- **test_parse_tool_crafting_deduplication**: Verify duplicate recipes are not added multiple times
- **test_parse_tool_crafting_output_extraction**: Verify output item names are extracted correctly
- **test_parse_tool_crafting_input_extraction**: Verify all input ingredients are extracted correctly
- **test_parse_tool_crafting_category_metadata**: Verify category field is populated in metadata
- **test_find_item_in_slot_with_alternatives**: Test the helper function with animated slot HTML

### Integration Tests
- **test_extract_all_transformations_includes_tool**: Verify tool.html is processed in the full pipeline
- **test_tool_transformations_in_csv**: Verify tool recipes appear in output/transformations.csv
- **test_no_duplicate_tool_recipes**: Verify no duplicate tool transformations in final output

### Edge Cases
- **Empty crafting section**: Tool page has no crafting section (should return empty list)
- **Malformed HTML**: Crafting UI elements are missing expected classes (should skip gracefully)
- **No alternatives detected**: Recipe has no animated slots (should create single transformation)
- **Multiple alternative slots**: Multiple ingredients have alternatives (should create combinations)
- **Education Edition exclusive tools**: Should be filtered out by `is_java_edition()` and `extract_item_from_link()`
- **Missing output slot**: Crafting UI has no mcui-output (should skip recipe)
- **Missing input slots**: Crafting UI has no mcui-input (should skip recipe)

## Acceptance Criteria
- [ ] Tool page HTML is downloaded to `ai_doc/downloaded_pages/tool.html`
- [ ] `parse_tool_crafting()` function is implemented in `src/core/parsers.py`
- [ ] Parser correctly identifies the crafting section in the Tool page
- [ ] Parser extracts all tool crafting recipes from the table
- [ ] Animated/cycling ingredients are detected and expanded into separate transformations
- [ ] Stone hoe recipe creates 3 separate transformations (cobblestone, cobbled deepslate, blackstone)
- [ ] All transformations use `TransformationType.CRAFTING`
- [ ] Category metadata is populated (either from section heading or hardcoded "crafting")
- [ ] Java Edition filtering is applied (Bedrock/Education content excluded)
- [ ] Deduplication is applied (no duplicate transformations)
- [ ] Parser is integrated into `src/extract_transformations.py` pipeline
- [ ] Comprehensive tests are written in `tests/test_tool_parser.py`
- [ ] All tests pass with 100% success rate
- [ ] Full extraction pipeline runs without errors
- [ ] Tool crafting transformations appear in `output/transformations.csv`
- [ ] Validation script runs without errors or warnings

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

```bash
# Download the Tool page manually
curl -s -L -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" \
  -H "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8" \
  -H "Accept-Language: en-US,en;q=0.5" \
  "https://minecraft.wiki/w/Tool" \
  -o ai_doc/downloaded_pages/tool.html

# Verify the file was downloaded
ls -lh ai_doc/downloaded_pages/tool.html

# Run unit tests for the Tool parser
uv run pytest tests/test_tool_parser.py -v

# Run full test suite to ensure no regressions
uv run pytest tests/ -v

# Run the extraction pipeline
uv run python src/extract_transformations.py

# Verify tool transformations in output
grep -i "stone hoe" output/transformations.csv

# Count tool crafting transformations (should have multiple for stone hoe)
grep -i "hoe" output/transformations.csv | wc -l

# Run validation to check data quality
uv run python src/validate_output.py

# Verify no duplicate transformations
uv run python -c "
import csv
import json
from collections import Counter

with open('output/transformations.csv', 'r') as f:
    reader = csv.DictReader(f)
    signatures = []
    for row in reader:
        sig = f\"{row['transformation_type']}|{row['input_items']}|{row['output_items']}\"
        signatures.append(sig)

    duplicates = {sig: count for sig, count in Counter(signatures).items() if count > 1}
    if duplicates:
        print(f'Found {len(duplicates)} duplicate transformation signatures:')
        for sig in list(duplicates.keys())[:5]:
            print(f'  {sig}')
    else:
        print('✓ No duplicate transformations found')
"

# Verify stone hoe has exactly 3 variants (cobblestone, cobbled deepslate, blackstone)
uv run python -c "
import csv
import json

with open('output/transformations.csv', 'r') as f:
    reader = csv.DictReader(f)
    stone_hoe_recipes = []
    for row in reader:
        outputs = json.loads(row['output_items'])
        if 'Stone Hoe' in outputs:
            inputs = json.loads(row['input_items'])
            stone_hoe_recipes.append(inputs)

    print(f'Found {len(stone_hoe_recipes)} stone hoe crafting recipes:')
    for recipe in stone_hoe_recipes:
        print(f'  {recipe}')

    # Check for expected stone types
    expected_stones = ['Cobblestone', 'Cobbled Deepslate', 'Blackstone']
    found_stones = []
    for recipe in stone_hoe_recipes:
        for item in recipe:
            if item in expected_stones:
                found_stones.append(item)

    print(f'\\nFound stone types: {found_stones}')
    if len(found_stones) >= 3:
        print('✓ Stone hoe has multiple variants')
    else:
        print('✗ Warning: Expected at least 3 stone hoe variants')
"
```

## Notes

### Alternative Detection Strategy
The user mentioned looking for the word "any" in the ingredients column to detect cycling recipes. However, based on the existing `parse_crafting()` implementation (line 256-453 in parsers.py), the more robust approach is to:

1. Use `find_item_in_slot()` which automatically detects multiple items in animated slots by finding all `span.invslot-item` elements within a slot
2. Check if `len(items_in_slot) > 1` to detect alternatives
3. Create separate transformations for each alternative combination

This approach is more reliable than text parsing because:
- It directly inspects the crafting UI graphics
- It handles cases where "any" might not appear in text
- It reuses existing, tested code from the crafting parser
- It automatically extracts the exact item names from the animation frames

### Category Metadata
The category should be set to `"crafting"` to match the pattern from existing parsers, or extracted from the section heading if the Tool page has subsections (e.g., "Wooden Tools", "Stone Tools"). Use `extract_category_from_element()` to automatically detect the section.

### Deduplication
Follow the pattern from `parse_crafting()` and other parsers:
```python
seen_signatures = set()
# ... in loop:
sig = transformation.get_signature()
if sig not in seen_signatures:
    seen_signatures.add(sig)
    transformations.append(transformation)
```

### Multi-Slot Alternatives Handling
If the Tool page shows recipes where multiple ingredients have alternatives (e.g., different stick types + different stone types), follow the pattern from `parse_crafting()` lines 315-399 which handles:
- Single alternative slot (simple expansion)
- Multiple alternative slots with matching counts (zip pairing)
- Output-guided pairing when output has alternatives matching input alternatives

### Performance Considerations
The Tool page likely has fewer recipes than the main Crafting page, so performance should not be a concern. If needed, the same deduplication strategy using signature-based sets will prevent memory bloat from duplicate transformations.

### Future Enhancements
- Consider parsing other sections of the Tool page (e.g., upgrading tools via smithing)
- Add tool-specific metadata (e.g., durability, mining speed tier)
- Cross-reference with existing crafting recipes to detect overlaps or differences
- Extract tool repair recipes if present on the page
