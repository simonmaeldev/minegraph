# Crafting Recipe Category Metadata

**Date:** 2025-10-10
**Specification:** specs/add-category-metadata-to-crafting.md

## Overview

The crafting parser now extracts and includes category/section metadata for each crafting recipe based on the wiki page structure. This enables users to filter and organize recipes by their functional category (e.g., "redstone", "transportation", "building_blocks") making it easier to understand the intended use of items and build category-aware crafting tools.

## What was built

- Category extraction helper function that traverses the DOM to find section headings
- Integration of category metadata into the crafting parser workflow
- Category normalization (lowercase with underscores)
- Handling of excluded sections (Removed/Changed recipes)
- Comprehensive test suite for category extraction logic
- Updated CSV output with category metadata for all crafting recipes

## Technical Implementation

### Files Modified

- `src/core/parsers.py` (lines 179-357): Added `extract_category_from_element()` helper function and integrated category extraction into `parse_crafting()` function
- `src/core/data_models.py` (lines 40-75): Existing `Transformation` dataclass with `metadata: Dict[str, Any]` field supports the new category metadata
- `tests/test_category_extraction.py` (new file): 212 lines of comprehensive tests for the category extraction helper function
- `tests/test_parsers.py` (lines 225-415+): Added integration tests verifying category metadata is included in parsed transformations
- `output/transformations.csv`: Updated with category metadata for all crafting recipes

### Key Changes

1. **Category Extraction Helper** (`extract_category_from_element()`):
   - Traverses up the DOM tree to find the nearest h2/h3 heading with `mw-headline` class
   - Extracts text content from the heading span
   - Normalizes category names: lowercase, underscores for spaces, special characters removed
   - Returns None for excluded sections (Removed/Changed recipes) or when no heading found

2. **Parser Integration**:
   - `parse_crafting()` calls `extract_category_from_element()` for each crafting UI element
   - Category added to transformation metadata dict alongside existing metadata like `has_alternatives`
   - Both simple recipes and alternative recipes include category metadata

3. **Normalization Logic**:
   - Special characters removed using regex: `re.sub(r'[^\w\s]', '', text)`
   - Spaces replaced with underscores
   - Converted to lowercase for consistency

4. **Test Coverage**:
   - Unit tests for helper function with various HTML structures (h2, h3, nested elements)
   - Tests for normalization (spaces, special chars, mixed case)
   - Tests for edge cases (no heading, excluded sections, multiple headings)
   - Integration tests verifying full parser workflow includes categories

## How to Use

### Accessing Category Data

After running the extraction pipeline, category metadata is available in the CSV output:

```bash
# Run extraction to generate transformations.csv with categories
uv run python src/extract_transformations.py

# View sample output with categories
head -20 output/transformations.csv
```

### CSV Format

The `transformations.csv` file includes a `metadata` column with JSON containing the category:

```csv
transformation_type,input_items,output_items,metadata
crafting,"[""Redstone Torch"", ""Redstone Dust"", ""Stone""]","[""Redstone Repeater""]","{""category"": ""redstone""}"
crafting,"[""Gold Ingot""]","[""Block of Gold""]","{""category"": ""building_blocks""}"
```

### Querying by Category

```bash
# Find all redstone recipes
grep '"category": "redstone"' output/transformations.csv

# Find all building block recipes
grep '"category": "building_blocks"' output/transformations.csv

# Count recipes by category
grep -o '"category": "[^"]*"' output/transformations.csv | sort | uniq -c
```

### Programmatic Access

When loading transformations in Python, access the category via the metadata dict:

```python
from src.core.data_models import Transformation

transformation = Transformation(...)
category = transformation.metadata.get("category")  # e.g., "redstone", "building_blocks"
```

## Configuration

No additional configuration required. Category extraction is automatically enabled for all crafting recipes.

### Available Categories

Categories are extracted from wiki section headings and include (but are not limited to):
- `building_blocks`
- `decoration_blocks`
- `redstone`
- `transportation`
- `utilities`
- `combat`
- `materials`
- `miscellaneous`

## Testing

### Run Test Suite

```bash
# Run all tests including category extraction tests
uv run pytest tests/ -v

# Run only category extraction tests
uv run pytest tests/test_category_extraction.py -v
```

### Validate Output

```bash
# Run extraction and validation pipeline
uv run python src/extract_transformations.py
uv run python src/validate_output.py

# Verify specific examples have correct categories
grep -i "repeater" output/transformations.csv  # Should show "redstone"
grep -i "minecart" output/transformations.csv  # Should show "transportation"
grep -i "iron block" output/transformations.csv  # Should show "building_blocks"
```

## Notes

- Some recipes at the top of wiki pages before any section heading will have `category: null` in the metadata
- Excluded sections (Removed recipes, Changed recipes) are filtered out entirely by existing parser logic, so they never receive category metadata
- Category names are normalized for consistency - wiki headings like "Building blocks" become "building_blocks"
- The metadata field can contain multiple entries (e.g., `{"has_alternatives": true, "category": "redstone"}`)
- This feature currently applies only to crafting transformations; smelting, smithing, and other transformation types do not yet include category metadata
