# Feature: Add Bartering Parser

## Feature Description
Add support for extracting Piglin bartering data from the Minecraft Wiki. Bartering is a game mechanic where players give gold ingots to Piglins, who return random items in exchange. This feature will download the bartering wiki page, parse the bartering items table, and extract all bartering transformations (gold ingot → various items) into the transformation graph.

## User Story
As a Minecraft data analyst
I want to include bartering transformations in the graph
So that I can see all methods for obtaining items, including Piglin bartering

## Problem Statement
The current transformation extraction system supports crafting, smelting, trading, smithing, stonecutting, mob drops, brewing, composting, and grindstone. However, it does not extract bartering data, which is a significant transformation mechanic in Minecraft Java Edition. Piglins accept gold ingots and return various items with different probabilities, providing an alternative method for obtaining many valuable items like ender pearls, fire charges, and enchanted books.

## Solution Statement
Add a new `parse_bartering()` function to `src/core/parsers.py` that parses the bartering items table from the Minecraft Wiki bartering page. The table contains items that Piglins give in exchange for gold ingots, along with quantities and probabilities. The parser will:
1. Parse the bartering items table structure (similar to trading parser)
2. Extract item names from the "Item given" column
3. Filter out Bedrock Edition exclusive items (Arrow vs Spectral Arrow)
4. Create transformations with gold ingot as input and bartered items as output
5. Include probability metadata from the "Chance" column

Register this parser in the extraction pipeline to run automatically alongside other parsers.

## Relevant Files
Use these files to implement the feature:

- **`src/core/parsers.py`** (lines 1-1215)
  - Contains all existing parser functions (crafting, smelting, trading, etc.)
  - Use `parse_trading()` (lines 679-818) as the primary reference pattern
  - Use `parse_mob_drops()` (lines 882-1005) for table parsing patterns
  - Add `parse_bartering()` function after `parse_grindstone()` (around line 1215)
  - The bartering table has a simpler structure than trading tables
  - Need to extract items from "Item given" column
  - Need to parse probability from "Chance" column (e.g., "5⁄469 (~1.07%)")
  - Filter Bedrock Edition items using `is_java_edition()` helper

- **`src/core/data_models.py`**
  - Contains `TransformationType` enum and data models
  - Need to add `BARTERING = "bartering"` to the `TransformationType` enum
  - Contains `Item` and `Transformation` classes used by parsers

- **`src/core/download_data.py`** (lines 10-20: WIKI_PAGES dict)
  - Contains `WIKI_PAGES` dictionary mapping page names to URLs
  - Add `"bartering": "https://minecraft.wiki/w/Bartering"` entry
  - This enables automatic downloading of the bartering page

- **`src/extract_transformations.py`** (lines 59-68: parsers dict)
  - Contains the `parsers` dictionary that registers parser functions
  - Add `"bartering.html": parse_bartering` entry
  - This integrates bartering parser into the extraction pipeline

- **`tests/test_parsers.py`**
  - Contains unit tests for all parser functions
  - Use trading parser tests as reference (search for "test_parse_trading")
  - Add comprehensive tests for `parse_bartering()` function

- **`README.md`** (lines 8-17: transformation types list)
  - Documents all supported transformation types
  - Add "Bartering (piglin bartering)" to the list

### New Files
None - all changes are modifications to existing files.

## Implementation Plan

### Phase 1: Foundation
1. Add `BARTERING` transformation type to the enum in `src/core/data_models.py`
2. Download the bartering page using curl command to understand the HTML structure
3. Analyze the bartering items table structure in the downloaded HTML

### Phase 2: Core Implementation
1. Implement `parse_bartering()` function in `src/core/parsers.py`
2. Handle table parsing with proper column detection
3. Extract items from "Item given" column using existing helper functions
4. Parse probability values from "Chance" column
5. Filter out Bedrock Edition exclusive items (Arrow)
6. Create transformations with gold ingot as input
7. Add probability metadata to transformations

### Phase 3: Integration
1. Register bartering page in `WIKI_PAGES` dict in `src/core/download_data.py`
2. Register `parse_bartering` in parsers dict in `src/extract_transformations.py`
3. Update README.md to document bartering transformation type
4. Run full extraction pipeline to verify integration
5. Download images for any new items discovered

## Step by Step Tasks

### Step 1: Download and analyze bartering page
- Use curl to download the bartering page: `curl -s https://minecraft.wiki/w/Bartering > bartering_analysis.html`
- Open the HTML file and identify the bartering items table structure
- Locate the "Item given" column (contains items Piglins return)
- Locate the "Chance" column (contains probability data)
- Identify how Bedrock Edition items are marked (e.g., Arrow vs Spectral Arrow)
- Note the table headers and cell structure for parsing

### Step 2: Add BARTERING transformation type
- Open `src/core/data_models.py`
- Find the `TransformationType` enum class
- Add `BARTERING = "bartering"` after the existing transformation types
- Ensure alphabetical ordering if that pattern is followed
- Save the file

### Step 3: Implement parse_bartering() function
- Open `src/core/parsers.py`
- Add `parse_bartering()` function after `parse_grindstone()` (around line 1215)
- Follow the pattern from `parse_trading()` for table-based parsing
- Function signature: `def parse_bartering(html_content: str) -> List[Transformation]`
- Parse BeautifulSoup HTML content with lxml parser
- Find the bartering items table (class="wikitable" or similar)
- Extract table headers to identify column indices for "Item given" and "Chance"
- Iterate through table rows (skip header row)
- For each row:
  - Apply `is_java_edition()` filter to exclude Bedrock-only items
  - Extract item from "Item given" column using `extract_item_from_link()`
  - Parse quantity if present (e.g., "2-4" means create multiple output items)
  - Parse probability from "Chance" column (extract percentage like "~1.07%")
  - Create gold ingot input item: `Item(name="Gold Ingot", url="https://minecraft.wiki/w/Gold_Ingot")`
  - Create `Transformation` with `TransformationType.BARTERING`
  - Add metadata: `{"probability": probability_value}` if probability was parsed
- Use deduplication with `seen_signatures` set like other parsers
- Return list of transformations

### Step 4: Handle quantity ranges in output
- Some items have quantity ranges (e.g., "2-4" Ender Pearls)
- For simplicity, represent quantity by adding the item multiple times to outputs list
- Use the minimum quantity from ranges (e.g., "2-4" → 2 items)
- This matches the pattern used in `parse_trading()` for consistency
- Example: If "2-4 Ender Pearl", add Ender Pearl twice to outputs list

### Step 5: Handle probability parsing
- Probabilities appear as fractions and percentages: "5⁄469 (~1.07%)"
- Extract the percentage value from the text using regex
- Pattern: `(\d+\.?\d*)\s*%` to capture decimal percentage
- Convert to decimal probability: `float(percentage_match) / 100.0`
- If parsing fails, default to probability of 1.0 (certain drop)
- Store in metadata: `{"probability": 0.0107}` for 1.07%

### Step 6: Filter Bedrock Edition items
- The table includes items marked as Bedrock Edition or Java Edition only
- Use the existing `is_java_edition()` helper function on table rows
- Specifically, Arrow is Bedrock Edition only (should be excluded)
- Spectral Arrow is Java Edition (should be included)
- Apply edition filter at the row or cell level before creating transformations
- This ensures only Java Edition bartering items are extracted

### Step 7: Write comprehensive tests
- Open `tests/test_parsers.py`
- Add `TestParseBartering` test class after existing parser tests
- Create test cases:
  - `test_parse_bartering_basic()` - Test parsing a simple bartering table with 2-3 items
  - `test_parse_bartering_extracts_items()` - Verify correct items are extracted
  - `test_parse_bartering_gold_ingot_input()` - Verify gold ingot is the input for all transformations
  - `test_parse_bartering_quantity_ranges()` - Test items with quantity ranges (2-4)
  - `test_parse_bartering_probability_metadata()` - Verify probability is parsed and stored
  - `test_parse_bartering_filters_bedrock_items()` - Verify Arrow is excluded, Spectral Arrow included
  - `test_parse_bartering_deduplication()` - Verify no duplicate transformations
  - `test_parse_bartering_empty_table()` - Test handling of empty or missing table
- Use mock HTML structures similar to other parser tests
- Run tests: `uv run pytest tests/test_parsers.py::TestParseBartering -v`

### Step 8: Register bartering page for download
- Open `src/core/download_data.py`
- Locate the `WIKI_PAGES` dictionary (around line 10)
- Add new entry: `"bartering": "https://minecraft.wiki/w/Bartering"`
- Maintain alphabetical ordering if that pattern exists
- Save the file
- This enables the download script to fetch the bartering page automatically

### Step 9: Register parser in extraction pipeline
- Open `src/extract_transformations.py`
- Locate the `parsers` dictionary in `extract_all_transformations()` function (around line 59)
- Import `parse_bartering` at the top of the file with other parser imports
- Add new entry: `"bartering.html": parse_bartering`
- Maintain alphabetical ordering if that pattern exists
- Save the file
- This integrates bartering parser into the main extraction workflow

### Step 10: Update README documentation
- Open `README.md`
- Locate the "Purpose" section listing transformation types (around line 8)
- Add new bullet: `- **Bartering** (piglin bartering)`
- Insert in logical order (alphabetically or by game mechanic grouping)
- Ensure consistent formatting with other entries
- Save the file

### Step 11: Run validation commands
Execute all validation commands to confirm the feature works correctly with zero regressions.

## Testing Strategy

### Unit Tests
- **Basic table parsing**: Parse simple bartering table HTML with 2-3 items
- **Item extraction**: Verify items are correctly extracted from "Item given" column
- **Gold ingot input**: Verify all transformations have Gold Ingot as input
- **Quantity handling**: Test items with quantity ranges (e.g., "2-4")
- **Probability parsing**: Verify probability metadata is correctly parsed from percentages
- **Edition filtering**: Verify Bedrock Edition items (Arrow) are excluded
- **Java Edition items**: Verify Java Edition items (Spectral Arrow) are included
- **Deduplication**: Verify no duplicate transformations are created
- **Empty/missing table**: Test graceful handling of malformed HTML

### Integration Tests
- **Full pipeline**: Run complete extraction with bartering parser enabled
- **CSV output**: Verify bartering transformations appear in `output/transformations.csv`
- **Item discovery**: Verify new bartering items appear in `output/items.csv`
- **Image download**: Verify images can be downloaded for bartering items
- **No regressions**: Verify all existing parser tests still pass

### Edge Cases
- **Multiple items per cell**: Some cells may list multiple items separated by line breaks
- **Missing probability**: Some rows might not have probability data
- **Missing quantity**: Items without explicit quantity should default to 1
- **Malformed table**: Missing columns or headers should be handled gracefully
- **Alternative names**: Items with alternative names or titles should use canonical names
- **Nested elements**: Complex HTML with nested spans and links

## Acceptance Criteria
- [ ] `BARTERING` transformation type is added to `TransformationType` enum
- [ ] `parse_bartering()` function is implemented in `src/core/parsers.py`
- [ ] Bartering page URL is registered in `WIKI_PAGES` dict
- [ ] Parser is registered in `extract_transformations.py` parsers dict
- [ ] All bartering transformations have Gold Ingot as the single input item
- [ ] All bartering items from Java Edition are extracted as outputs
- [ ] Bedrock Edition exclusive items (Arrow) are filtered out
- [ ] Java Edition items (Spectral Arrow) are included
- [ ] Probability metadata is stored in transformations
- [ ] Quantity ranges are handled appropriately
- [ ] Comprehensive unit tests are added and passing
- [ ] All existing tests still pass (no regressions)
- [ ] README.md is updated with bartering documentation
- [ ] Full extraction pipeline runs successfully with bartering data
- [ ] Bartering transformations appear in `output/transformations.csv`
- [ ] All bartering items appear in `output/items.csv`
- [ ] Images can be downloaded for bartering items
- [ ] Expected bartering items are present (at minimum: Ender Pearl, Spectral Arrow, Fire Charge, Obsidian, Iron Nugget, Enchanted Book, String, Nether Quartz, Gravel, Leather, Soul Sand, Nether Brick, Blackstone, Crying Obsidian, Iron Boots)

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

```bash
# Run unit tests for bartering parser
uv run pytest tests/test_parsers.py::TestParseBartering -v

# Run all parser tests to ensure no regressions
uv run pytest tests/test_parsers.py -v

# Run full test suite
uv run pytest tests/ -v

# Download all wiki pages including bartering
uv run python -m src.core.download_data

# Verify bartering page was downloaded
ls -lh ai_doc/downloaded_pages/bartering.html

# Run full extraction pipeline
uv run python src/extract_transformations.py

# Count bartering transformations in output
grep "^bartering," output/transformations.csv | wc -l

# Expected: 15-20 bartering transformations (depending on item variations)

# Verify Gold Ingot is input for all bartering transformations
grep "^bartering," output/transformations.csv | grep -v "Gold Ingot" | wc -l

# Expected: 0 (all bartering transformations should have Gold Ingot as input)

# Check for specific expected bartering items
grep "^bartering," output/transformations.csv | grep "Ender Pearl"
grep "^bartering," output/transformations.csv | grep "Spectral Arrow"
grep "^bartering," output/transformations.csv | grep "Fire Charge"
grep "^bartering," output/transformations.csv | grep "Obsidian"

# Verify Bedrock Edition Arrow is NOT present (should be filtered)
grep "^bartering," output/transformations.csv | grep '"Arrow"' | grep -v "Spectral"

# Expected: 0 results (Arrow should be filtered as Bedrock Edition only)

# Verify Spectral Arrow IS present (Java Edition)
grep "^bartering," output/transformations.csv | grep "Spectral Arrow"

# Expected: 1 result (Spectral Arrow should be included)

# Validate output quality (no duplicates, no orphaned items)
uv run python src/validate_output.py

# Download images for all items including new bartering items
uv run python src/download_item_images.py --input output/items.csv --output-dir images/ --verbose

# Verify bartering items have images downloaded
ls images/ | grep -i "ender_pearl\|spectral_arrow\|fire_charge\|obsidian"

# Test 3D visualization with bartering transformations included
uv run python src/visualize_graph_3d.py --filter-type=bartering --no-interactive

# Test filtering in visualization
uv run python src/visualize_graph_3d.py --filter-type=bartering,trading --no-interactive
```

## Notes
- **Bartering probabilities**: The wiki lists probabilities as fractions (e.g., 5⁄469) and percentages (e.g., ~1.07%). Parse the percentage for metadata.
- **Quantity ranges**: Some items have ranges like "2-4" or "10-36". Use the minimum value for consistency with other parsers.
- **Gold Ingot**: All bartering transformations have exactly one input: Gold Ingot. This is a constant for all bartering trades.
- **Bedrock vs Java**: The table includes edition markers. Arrow is Bedrock Edition only and should be filtered. Spectral Arrow is Java Edition and should be included.
- **Alternative items**: Some rows list multiple items (e.g., "Splash Potion of Fire Resistance, Potion of Fire Resistance, Water Bottle"). These should be treated as alternatives - create separate transformations for each.
- **Enchanted items**: Some outputs are enchanted (e.g., "Enchanted Book with Soul Speed", "Iron Boots with Soul Speed"). Extract the item name properly.
- **Metadata**: Consider storing probability, quantity ranges, or other metadata in the transformation metadata dict.
- **Parser ordering**: Add the bartering parser in alphabetical order within the parsers dict for consistency.
- **Image download**: After extraction, run the image download script to fetch images for any new items discovered through bartering.
- **Testing approach**: Create focused unit tests with mock HTML first, then validate against real downloaded HTML.
- **Edition filtering**: The existing `is_java_edition()` helper should handle the edition filtering, similar to how trading parser uses it.
- **Future enhancements**: Could add "piglin" entity metadata similar to how trading adds "villager_type" metadata, but this is optional for the initial implementation.
