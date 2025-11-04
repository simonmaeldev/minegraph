# Minecraft Transformation Extraction System

**Date:** 2025-10-08
**Specification:** specs/minecraft-transformation-extraction.md, specs/minecraft-transformation-patterns.md

## Overview

A comprehensive data extraction system that automatically downloads and parses Minecraft Java Edition wiki pages to extract all item transformation recipes (crafting, smelting, trading, mob drops, etc.) and exports them as structured CSV files suitable for graph construction. The system handles complex patterns like multi-slot alternatives, animated ingredients, villager trades, and probability-based mob drops while filtering out non-Java Edition content.

## What was built

- **Type-safe data models** with proper typing hints for Items, Transformations, and TransformationType enum
- **Wiki page downloader** with caching and rate limiting for 9 main pages + 41 mob pages
- **9 specialized HTML parsers** for different transformation types (crafting, smelting, smithing, stonecutter, trading, mob drops, brewing, composting, grindstone)
- **Edition filtering** to exclude Bedrock Edition and Minecraft Education Edition content
- **Historical recipe exclusion** to filter removed/changed recipes from output
- **Multi-slot alternative handling** for recipes with animated/alternative ingredients
- **CSV export system** generating items.csv and transformations.csv
- **Data validation module** for quality checks and statistics reporting
- **Comprehensive test suite** with 65+ test cases covering all parsers and edge cases

## Technical Implementation

### Files Modified

- `src/core/__init__.py`: Package initialization for core module
- `src/core/data_models.py`: Defines `Item`, `Transformation`, and `TransformationType` dataclasses with deduplication logic
- `src/core/parsers.py`: Contains 9 parser functions and helper utilities for HTML parsing with BeautifulSoup
- `src/core/download_data.py`: Downloads wiki pages with caching to `ai_doc/downloaded_pages/`
- `src/extract_transformations.py`: Main orchestration script that runs all parsers and exports CSV files
- `src/validate_output.py`: Data quality validation and statistics reporting
- `tests/test_data_models.py`: Unit tests for data models (16 test cases)
- `tests/test_parsers.py`: Unit tests for parser functions and helpers
- `tests/test_category_extraction.py`: Tests for category extraction from wiki headings
- `tests/test_multi_slot_alternatives.py`: Tests for multi-slot alternative recipe handling
- `tests/test_exclude_historical_recipes.py`: Tests for historical recipe filtering
- `output/items.csv`: Generated CSV with all unique Minecraft items (800+ items)
- `output/transformations.csv`: Generated CSV with all transformations (2000+ recipes)

### Key Changes

- Implemented comprehensive HTML parsing using BeautifulSoup with `lxml` parser for 9 transformation types
- Added edition filtering logic that checks for Java Edition markers and excludes Bedrock/Education sections
- Implemented multi-slot alternative matching for recipes like wool dyeing (pairs dye alternatives with wool alternatives)
- Created metadata tracking for villager professions/levels, mob drop probabilities, and composting success rates
- Built CSV export with JSON-encoded item lists and metadata objects for flexible graph construction
- Added extensive test coverage including edge cases for animated slots, tag expansion, and conditional drops

## How to Use

### Dependencies

Here are the installed dependencies using uv:
```bash
uv add requests lxml beautifulsoup4 pytest
```
You don't need to run the command as it is already added, just know that the virtual environment is managed with `uv`.

### Step 1: Download Wiki Pages (Optional)

The extraction script will automatically download pages if not cached, but you can manually download:

```bash
python -c "from src.core.download_data import download_all_pages; download_all_pages()"
```

This downloads 50 HTML files to `ai_doc/downloaded_pages/` (9 main pages + 41 mob pages).

### Step 2: Run Extraction

Execute the main extraction script:

```bash
python src/extract_transformations.py
```

This will:
- Load all cached HTML files
- Parse with appropriate parser for each transformation type
- Deduplicate items across all transformations
- Export to `output/items.csv` and `output/transformations.csv`

### Step 3: Validate Output

Run validation to check data quality:

```bash
python src/validate_output.py
```

This reports:
- Total items and transformations extracted
- Breakdown by transformation type
- Duplicate detection
- CSV format validation
- Bedrock/Education content leakage checks

### Step 4: Verify Files

Check the generated CSV files:

```bash
# View items
head -20 output/items.csv

# View transformations
head -20 output/transformations.csv

# Count records
wc -l output/*.csv
```

## Configuration

### Download Settings

In `src/core/download_data.py`:
- `WIKI_PAGES`: Dictionary mapping page names to wiki URLs
- `MOB_PAGES`: List of 41 mob names for individual page downloads
- Rate limiting: 2 seconds between requests
- User-Agent: "MinecraftTransformationExtractor/1.0"

### Parser Settings

In `src/core/parsers.py`:
- Java Edition filtering: Excludes sections with "Bedrock Edition", "Bedrock-specific", "Education Edition" headings
- Historical exclusion: Filters "Removed_recipes" and "Changed_recipes" sections
- Multi-slot alternatives: Automatically expands animated slots into separate transformations
- Metadata capture: Stores villager types, mob drop probabilities, composting rates

### Output Format

**items.csv:**
```csv
item_name,item_url
Iron Ingot,https://minecraft.wiki/w/Iron_Ingot
Block of Iron,https://minecraft.wiki/w/Block_of_Iron
```

**transformations.csv:**
```csv
transformation_type,input_items,output_items,metadata
CRAFTING,"[{""name"":""Iron Ingot"",""url"":""https://minecraft.wiki/w/Iron_Ingot""}]","[{""name"":""Block of Iron"",""url"":""https://minecraft.wiki/w/Block_of_Iron""}]","{""category"":""Building blocks""}"
```

## Testing

Run the full test suite:

```bash
pytest tests/ -v
```

### Test Coverage

- **test_data_models.py**: Tests Item/Transformation creation, hashing, equality, validation (16 tests)
- **test_parsers.py**: Tests all 9 parsers and helper functions with sample HTML
- **test_category_extraction.py**: Tests category extraction from wiki headings
- **test_multi_slot_alternatives.py**: Tests multi-slot alternative pairing logic (e.g., wool+dye)
- **test_exclude_historical_recipes.py**: Tests historical recipe filtering

### Manual Spot Checks

Verify known recipes:
```bash
# Check for iron block crafting
grep "Block_of_Iron" output/transformations.csv

# Check for zombie drops
grep "zombie" output/transformations.csv -i

# Check for villager trades
grep "TRADING" output/transformations.csv
```

## Notes

### Transformation Types Supported

1. **CRAFTING**: 3x3 crafting table recipes (shaped and shapeless)
2. **SMELTING**: Standard furnace recipes
3. **BLAST_FURNACE**: Faster ore smelting
4. **SMOKER**: Faster food cooking
5. **SMITHING**: Netherite upgrades and armor trims
6. **STONECUTTER**: Efficient stone cutting
7. **TRADING**: Villager trades by profession and level
8. **MOB_DROP**: Items dropped when mobs are killed
9. **BREWING**: Potion brewing transformations
10. **COMPOSTING**: Organic items to bone meal
11. **GRINDSTONE**: Disenchanting and repair

### Data Quality Features

- **Edition filtering**: Automatically excludes Bedrock Edition and Minecraft Education Edition content
- **Historical filtering**: Excludes removed and changed recipes from old game versions
- **Deduplication**: Items are deduplicated based on name (case-insensitive)
- **Alternative expansion**: Animated slots create separate transformation edges
- **Metadata preservation**: Villager types, probabilities, and categories preserved

### Limitations

- **Enchanted items**: Represented as generic "Enchanted <item>" without specific enchantment combinations
- **Tag expansion**: Item tags (e.g., "any planks") are not expanded to individual items in current implementation
- **Loot chests**: Excluded as specified (not a player-controlled transformation)
- **Natural generation**: Excluded (not a transformation)
- **Combustibles**: Excluded (fuel is separate from smelting recipes)

### Performance

- Download phase: ~2 minutes (with 2s rate limiting between requests)
- Parsing phase: ~10-20 seconds for all 50 HTML files
- Export phase: <1 second for CSV generation
- Total runtime: ~2-3 minutes for full extraction (first run)
- Cached runtime: ~10-20 seconds (subsequent runs with cached HTML)

### Future Enhancements

- **Graph construction**: Build NetworkX directed graph from CSV files
- **Optimization paths**: Find shortest transformation chains between items
- **Recipe calculator**: Calculate base materials needed for any item
- **Update mechanism**: Periodic re-download and diff detection for wiki updates
- **Parallel parsing**: Parse multiple pages concurrently for faster extraction
- **Tag expansion**: Expand item tags/groups into individual item variations
- **Web API**: Expose transformation data via REST API for applications

### Design Decisions

- **CSV format**: Chosen for broad compatibility (graph libraries, databases, spreadsheets)
- **JSON encoding**: Item lists and metadata stored as JSON strings within CSV for flexibility
- **Separate edges**: Multi-slot alternatives create separate transformations for explicit graph representation
- **Caching**: HTML files cached locally to avoid re-downloading during development
- **Type safety**: Full typing hints throughout codebase (Python 3.9+)
- **No shape preservation**: Crafting grid positions not tracked (shapeless representation)

### Known Issues

- Some complex recipes with NBT data or custom names may not be fully captured
- Bedrock-exclusive mobs may appear in mob list but should have no Java drops
- Some animated slots with conditional logic (e.g., damaged items) may need manual review
- URL encoding edge cases (special characters in item names) handled but may have rare issues
