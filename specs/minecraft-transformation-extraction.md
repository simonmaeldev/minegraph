# Feature: Minecraft Java Edition Transformation Data Extraction

## Feature Description
Extract all transformation recipes and processes from Minecraft Java Edition to build a comprehensive directed graph of item transformations. The system will download HTML pages from the Minecraft Wiki, parse them using BeautifulSoup, and extract transformation data including crafting, smelting, trading, mob drops, smithing, stonecutting, brewing, composting, and grindstone operations. The output will be two CSV files: one containing all unique items with their wiki URLs, and another containing all transformations with input/output items and transformation types.

## User Story
As a Minecraft data analyst
I want to extract all transformation recipes from Minecraft Java Edition wiki pages
So that I can build a directed graph showing how items can be transformed into other items through various game mechanics

## Problem Statement
Minecraft has hundreds of items and multiple transformation mechanisms (crafting, smelting, trading, etc.). Manually collecting this data is error-prone and time-consuming. We need an automated system to:
- Download relevant wiki pages
- Parse HTML to extract transformation patterns
- Filter out Bedrock Edition and Education Edition content
- Expand tag/group recipes into individual item variations
- Handle complex patterns like animated alternatives, mob drops with probabilities, and multi-input transformations
- Export clean, structured data suitable for graph construction

## Solution Statement
Build a Python-based extraction system with:
1. **Data models** (`src/core/data_models.py`): Type-safe classes representing Items, Transformations, and related entities with full typing hints
2. **Download module** (`src/core/download_data.py`): Downloads wiki pages for crafting, smelting, trading, smithing, stonecutter, drops, brewing, composting, and grindstone if not already cached
3. **Parser module** (`src/core/parsers.py`): BeautifulSoup-based HTML parsers for each transformation type, with explicit filtering of non-Java Edition content
4. **Extraction script** (`src/extract_transformations.py`): Main script that orchestrates parsing and CSV output generation
5. **Output files**: `output/items.csv` (unique items) and `output/transformations.csv` (transformation edges)

## Relevant Files
Use these files to implement the feature:

- **`specs/minecraft-transformation-patterns.md`**: Contains detailed HTML patterns and parsing strategies discovered through analysis of downloaded wiki pages
- **`ai_doc/downloaded_pages/*.html`**: Downloaded wiki pages containing transformation data (crafting, smelting, trading, smithing, stonecutter, drops)
- **`pyproject.toml`**: Project dependencies including beautifulsoup4 and pytest

### New Files

- **`src/core/__init__.py`**: Package initialization
- **`src/core/data_models.py`**: Type-safe data models (Item, Transformation, TransformationType enum)
- **`src/core/download_data.py`**: Wiki page downloader with caching
- **`src/core/parsers.py`**: HTML parsers for each transformation type
- **`src/extract_transformations.py`**: Main extraction script
- **`output/items.csv`**: Output file for unique items (item_name, item_url)
- **`output/transformations.csv`**: Output file for transformations (transformation_type, input_items, output_items)
- **`tests/test_parsers.py`**: Unit tests for parser functions
- **`tests/test_data_models.py`**: Unit tests for data models

## Implementation Plan

### Phase 1: Foundation
Set up the project structure with proper typing, data models, and download functionality:
- Create `src/core/` package with `__init__.py`
- Define data models with typing hints (Item, Transformation, TransformationType enum)
- Implement wiki page downloader with caching to `ai_doc/downloaded_pages/`
- Add missing dependencies (requests, lxml parser for BeautifulSoup)

### Phase 2: Core Implementation
Build HTML parsers for each transformation type:
- Implement crafting parser (handles 3x3 grid, animated alternatives, shapeless recipes)
- Implement smelting parser (furnace, blast furnace, smoker)
- Implement smithing parser (3-input smithing table)
- Implement stonecutter parser
- Implement trading parser (villager professions and levels)
- Implement mob drops parser (with probability handling)
- Implement brewing parser
- Implement composting parser
- Implement grindstone parser
- Ensure all parsers filter out Bedrock Edition and Education Edition content
- Handle tag/group expansion into individual items

### Phase 3: Integration
Connect all components and generate output:
- Build main extraction script that calls all parsers
- Aggregate all Items into unique set
- Aggregate all Transformations
- Export to CSV files (`output/items.csv` and `output/transformations.csv`)
- Validate output data quality

## Step by Step Tasks

### Step 1: Project Setup and Dependencies
- Create `src/core/` directory and `__init__.py`
- Add `requests` and `lxml` dependencies via `uv add requests lxml`
- Create `output/` directory for CSV files
- Create `tests/` directory for test files

### Step 2: Define Data Models
- Create `src/core/data_models.py`
- Define `TransformationType` enum with values: CRAFTING, SMELTING, BLAST_FURNACE, SMOKER, SMITHING, STONECUTTER, TRADING, MOB_DROP, BREWING, COMPOSTING, GRINDSTONE
- Define `Item` dataclass with fields: `name: str`, `url: str`, `__hash__` and `__eq__` methods for set deduplication
- Define `Transformation` dataclass with fields: `transformation_type: TransformationType`, `inputs: List[Item]`, `outputs: List[Item]`, `metadata: Dict[str, Any]`
- Use proper typing hints (e.g., `Dict[str, int]` not `Dict`)
- Write unit tests in `tests/test_data_models.py`

### Step 3: Implement Download Module
- Create `src/core/download_data.py`
- Define `WIKI_PAGES` dictionary mapping page names to URLs:
  - crafting: `https://minecraft.wiki/w/Crafting`
  - smelting: `https://minecraft.wiki/w/Smelting`
  - trading: `https://minecraft.wiki/w/Trading`
  - smithing: `https://minecraft.wiki/w/Smithing`
  - stonecutter: `https://minecraft.wiki/w/Stonecutter`
  - drops: `https://minecraft.wiki/w/Drops`
  - brewing: `https://minecraft.wiki/w/Brewing`
  - composting: `https://minecraft.wiki/w/Composter`
  - grindstone: `https://minecraft.wiki/w/Grindstone`
- Implement `download_page(page_name: str, output_dir: str) -> str` function
- Check if file exists in `ai_doc/downloaded_pages/<page>.html`, skip download if present
- Use `requests` library with user-agent header
- Return path to downloaded file
- Implement `download_all_pages()` function that downloads all pages
- Use proper typing hints (e.g., `Dict[str, int]` not `Dict`)

### Step 4: Implement Base Parser Utilities
- Create `src/core/parsers.py`
- Implement `is_java_edition(element: Tag) -> bool`: checks if element is Java Edition content (filters out Bedrock/Education)
- Implement `extract_item_from_link(link_tag: Tag) -> Optional[Item]`: extracts Item from `<a>` tag with `/w/` href
- Implement `parse_quantity(text: str) -> int`: parses "15 × Item" format, defaults to 1
- Write helper functions for common patterns identified in `specs/minecraft-transformation-patterns.md`

### Step 5: Implement Crafting Parser
- In `src/core/parsers.py`, implement `parse_crafting(html_content: str) -> List[Transformation]`
- Find all `<span class="mcui mcui-Crafting_Table pixel-image">`
- Extract inputs from `mcui-input` section (3x3 grid)
- Handle animated slots (`invslot animated`) by creating separate transformations for each alternative
- Extract output from `mcui-output` section
- Filter out non-Java Edition recipes
- Expand tag/group recipes into individual items
- Return list of Transformation objects with type CRAFTING
- Write unit tests in `tests/test_parsers.py` using sample HTML

### Step 6: Implement Smelting Parsers
- Implement `parse_smelting(html_content: str) -> List[Transformation]`
- Handle furnace (`mcui-Furnace`), blast furnace (`mcui-Blast_Furnace`), and smoker (`mcui-Smoker`)
- Extract single input item
- Extract single output item
- Ignore fuel slot
- Create appropriate TransformationType (SMELTING, BLAST_FURNACE, or SMOKER)
- Filter non-Java Edition content
- Write unit tests

### Step 7: Implement Smithing Parser
- Implement `parse_smithing(html_content: str) -> List[Transformation]`
- Find all `mcui-Smithing_Table` elements
- Extract three inputs: template (`mcui-input1`), base (`mcui-input2`), material (`mcui-input3`)
- Extract output
- Handle animated alternatives in any slot
- Filter non-Java Edition content
- Write unit tests

### Step 8: Implement Stonecutter Parser
- Implement `parse_stonecutter(html_content: str) -> List[Transformation]`
- Find stonecutter UI elements or conversion tables
- Extract input → output mappings
- Handle multiple outputs from same input (create separate transformations)
- Filter non-Java Edition content
- Write unit tests

### Step 9: Implement Trading Parser
- Implement `parse_trading(html_content: str) -> List[Transformation]`
- Find all `<table class="wikitable">` with trading data
- Identify villager profession from `data-description` or headers
- Extract "Item wanted" (inputs) and "Item given" (outputs)
- Parse quantities ("15 × Coal" format)
- Store villager type and level in metadata
- Handle multi-item trades (emerald + item → item)
- Filter non-Java Edition content
- Write unit tests

### Step 10: Implement Mob Drops Parser
- Implement `parse_mob_drops(html_content: str) -> List[Transformation]`
- Find "Drops" sections on mob pages
- Extract mob name from page title or heading
- Parse drop tables with items, quantities, and probabilities
- Create Transformation with mob as virtual "input" item
- Store probability in metadata
- Use base drop rates (no looting)
- Filter conditional drops as specified (ignore loot chests, natural generation)
- Filter non-Java Edition content
- Write unit tests

### Step 11: Download Individual Mob Pages
- Extend `src/core/download_data.py` to download individual mob pages
- Create list of all mobs from Minecraft wiki (passive, neutral, hostile, boss)
- Implement `download_mob_pages()` function
- Download to `ai_doc/downloaded_pages/mobs/<mob_name>.html`
- Update main download function to include mob pages

### Step 12: Implement Brewing Parser
- Implement `parse_brewing(html_content: str) -> List[Transformation]`
- Find brewing stand UI elements or brewing tables
- Extract base potion + ingredient → result potion
- Handle water bottle + nether wart → awkward potion pattern
- Filter non-Java Edition content
- Write unit tests

### Step 13: Implement Composting Parser
- Implement `parse_composting(html_content: str) -> List[Transformation]`
- Find composter tables showing item → bone meal conversions
- Extract items that can be composted
- Create transformations with composting success rates in metadata
- Filter non-Java Edition content
- Write unit tests

### Step 14: Implement Grindstone Parser
- Implement `parse_grindstone(html_content: str) -> List[Transformation]`
- Find grindstone UI or tables
- Extract enchanted item → disenchanted item + experience
- Handle tool/armor repair patterns
- Filter non-Java Edition content
- Write unit tests

### Step 15: Handle Enchanted Items
- Update parsers to handle "enchanted" versions of items as specified
- Create generic "Enchanted <item>" items without specific enchantment combinations
- Don't generate all possible enchantment variations
- Update data models if needed to flag enchanted items

### Step 16: Create Main Extraction Script
- Create `src/extract_transformations.py`
- Import all parser functions
- Implement `main()` function:
  - Load all downloaded HTML files
  - Call appropriate parser for each file
  - Collect all Transformations
  - Extract unique Items from all transformations
  - Deduplicate items using set
- Add command-line interface using argparse
- Add progress logging

### Step 17: Implement CSV Export
- In `src/extract_transformations.py`, implement `export_items_csv(items: Set[Item], filepath: str)`
- Write CSV with columns: `item_name`, `item_url`
- Implement `export_transformations_csv(transformations: List[Transformation], filepath: str)`
- Write CSV with columns: `transformation_type`, `input_items` (JSON array), `output_items` (JSON array), `metadata` (JSON object)
- Create `output/` directory if it doesn't exist
- Handle CSV encoding properly (UTF-8)

### Step 18: Run Full Extraction
- Execute `python src/extract_transformations.py`
- Verify `output/items.csv` is created
- Verify `output/transformations.csv` is created
- Check for parsing errors or warnings
- Validate CSV format and content

### Step 19: Data Quality Validation
- Implement `src/validate_output.py` script
- Check for duplicate items
- Check for orphan transformations (references to non-existent items)
- Validate all URLs are properly formed
- Count transformations by type
- Report statistics (total items, total transformations, breakdown by type)
- Check for any Bedrock/Education content that slipped through

### Step 20: Run Validation Commands
- Run all unit tests: `pytest tests/ -v`
- Run extraction script: `python src/extract_transformations.py`
- Run validation script: `python src/validate_output.py`
- Check output files exist and contain data
- Verify no errors in execution

## Testing Strategy

### Unit Tests

**`tests/test_data_models.py`:**
- Test Item creation with name and URL
- Test Item equality and hashing for set deduplication
- Test Transformation creation with inputs and outputs
- Test TransformationType enum values

**`tests/test_parsers.py`:**
- Test `extract_item_from_link()` with sample HTML
- Test `parse_quantity()` with various formats
- Test `is_java_edition()` filtering
- Test each parser function with small HTML snippets:
  - `parse_crafting()`: simple recipe, shaped recipe, shapeless recipe, animated alternatives
  - `parse_smelting()`: furnace, blast furnace, smoker
  - `parse_smithing()`: netherite upgrade, armor trim
  - `parse_stonecutter()`: stone variants
  - `parse_trading()`: villager trade with quantities
  - `parse_mob_drops()`: simple drop, multiple drops, probability
  - `parse_brewing()`: basic potion transformation
  - `parse_composting()`: item to bone meal
  - `parse_grindstone()`: disenchanting

### Integration Tests

**Manual integration test:**
- Download all pages
- Run full extraction
- Verify output CSV files
- Spot-check known recipes (e.g., iron ingot → block of iron, coal → smelted iron ore)
- Verify mob drops are present (e.g., zombie → rotten flesh)
- Verify trades are present (e.g., emerald trades)

### Edge Cases

- **Animated alternatives**: Recipe accepts multiple item types (create separate edges)
- **Tag expansion**: "Any planks" → create edges for oak, birch, spruce, etc.
- **Multi-input recipes**: Smithing (3 inputs), trading (2 inputs sometimes)
- **Probability drops**: Mob drops with < 100% chance
- **Enchanted items**: Generic enchanted item without specific enchantments
- **Empty slots**: Crafting recipes with gaps in the grid
- **Bedrock filtering**: Ensure no Bedrock/Education content in output
- **URL encoding**: Handle spaces and special characters in item names
- **Duplicate transformations**: Same input → output via different methods (crafting vs stonecutter)

## Acceptance Criteria

1. ✅ All data models use proper typing hints (e.g., `Dict[str, int]` not `Dict`)
2. ✅ All wiki pages (crafting, smelting, trading, smithing, stonecutter, drops, brewing, composting, grindstone) are downloaded to `ai_doc/downloaded_pages/`
3. ✅ Individual mob pages are downloaded for drop extraction
4. ✅ Parsers explicitly filter out Bedrock Edition and Minecraft Education Edition content
5. ✅ Tag/group recipes are expanded into individual item variations
6. ✅ Enchanted items are represented as generic "Enchanted <item>" without all enchantment variations
7. ✅ `output/items.csv` contains unique items with name and URL
8. ✅ `output/transformations.csv` contains transformations with type, inputs, outputs
9. ✅ All transformation types are extracted: crafting, smelting, blast furnace, smoker, smithing, stonecutter, trading, mob drops, brewing, composting, grindstone
10. ✅ Animated alternatives create separate transformation edges
11. ✅ All unit tests pass
12. ✅ No Bedrock/Education content in output (validated)
13. ✅ Output CSVs are well-formed and can be parsed
14. ✅ Data quality validation script reports statistics and finds no errors
15. ✅ Loot chests, natural generation, and enchanting are excluded as specified
16. ✅ Combustibles are not included in output

## Validation Commands

Execute every command to validate the feature works correctly with zero regressions.

```bash
# Install dependencies
uv add requests lxml

# Create output directory
mkdir -p output

# Run unit tests
pytest tests/ -v

# Download all wiki pages (if not already cached)
python -c "from src.core.download_data import download_all_pages; download_all_pages()"

# Run extraction script
python src/extract_transformations.py

# Verify output files exist and have content
test -f output/items.csv && wc -l output/items.csv
test -f output/transformations.csv && wc -l output/transformations.csv

# Run validation script
python src/validate_output.py

# Spot-check CSV format
head -20 output/items.csv
head -20 output/transformations.csv

# Verify no Bedrock content leaked through (should return 0 matches)
grep -i "bedrock\|education" output/*.csv | wc -l

# Run full test suite again to ensure no regressions
pytest tests/ -v
```

## Notes

### Dependencies Added
- `requests`: For downloading wiki pages via HTTP
- `lxml`: Faster HTML parser for BeautifulSoup
- `beautifulsoup4`: Already included
- `pytest`: Already included

### Wiki Page Sources
All pages from `https://minecraft.wiki/`:
- `/w/Crafting`
- `/w/Smelting`
- `/w/Trading`
- `/w/Smithing`
- `/w/Stonecutter`
- `/w/Drops`
- `/w/Brewing`
- `/w/Composter`
- `/w/Grindstone`
- Individual mob pages: `/w/<Mob_Name>`

### HTML Pattern Reference
See `specs/minecraft-transformation-patterns.md` for detailed HTML patterns, CSS classes, and parsing strategies discovered through analysis.

### Future Considerations
- **Graph construction**: After CSV generation, could build NetworkX graph for analysis
- **Visualization**: Could generate graph visualizations
- **Optimization paths**: Find optimal transformation chains
- **Recipe calculator**: Calculate required base materials for any item
- **Update mechanism**: Periodic re-download and diff detection for wiki updates
- **Performance**: For very large datasets, consider streaming CSV writes
- **Parallel parsing**: Could parse different pages concurrently for speed

### Design Decisions
- **CSV format**: Chosen for simplicity and broad tool compatibility (can import into graph libraries, databases, spreadsheets)
- **Separate edges for alternatives**: Creates explicit graph representation of all possible transformations
- **Generic enchanted items**: Avoids combinatorial explosion while preserving the concept of enchantment
- **Metadata storage**: JSON in CSV allows flexible metadata without fixed schema
- **Caching downloads**: Avoids re-downloading large HTML files during development
- **No shape preservation**: As specified, we don't track crafting grid positions (shapeless vs shaped distinction is optional metadata)
