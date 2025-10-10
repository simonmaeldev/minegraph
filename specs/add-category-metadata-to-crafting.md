# Feature: Add Category Metadata to Crafting Transformations

## Feature Description
Extend the crafting parser to capture the section/category context from wiki pages and include it in transformation metadata. This will allow users to understand which category each crafting recipe belongs to (e.g., "Redstone", "Transportation", "Building blocks", "Combat"), providing better organization and filtering capabilities for the transformation data.

## User Story
As a data consumer
I want to know which category each crafting recipe belongs to (e.g., redstone, transportation)
So that I can filter and organize recipes by their functional category in the game

## Problem Statement
Currently, the crafting parser extracts recipes from wiki pages but does not capture the contextual information about which section/category the recipe appears in. When a user looks at a transformation for a "Repeater" or "Minecart", there's no indication that one belongs to the "Redstone" category and the other to "Transportation". This contextual information is valuable for:
- Filtering recipes by functional category
- Understanding the intended use of items
- Building category-aware crafting tools
- Analyzing recipe distribution across game mechanics

## Solution Statement
Modify the `parse_crafting()` function in `src/core/parsers.py` to:
1. Track the current section heading context as it traverses the DOM
2. Extract the section title (category) from `<span class="mw-headline" id="...">` elements
3. Add the category to the transformation metadata as a `category` field
4. Normalize category names to lowercase with underscores for consistency

The category will be extracted from heading elements (h2/h3) with `mw-headline` class that appear before each crafting UI element in the HTML structure.

## Relevant Files
Use these files to implement the feature:

- **src/core/parsers.py** (lines 179-357)
  - Contains the `parse_crafting()` function that needs modification
  - Already has helper functions like `is_java_edition()` and `is_in_excluded_section()`
  - Uses BeautifulSoup for HTML parsing
  - Returns `List[Transformation]` with metadata dict

- **src/core/data_models.py** (lines 40-75)
  - Contains the `Transformation` dataclass with `metadata: Dict[str, Any]` field
  - Already supports arbitrary metadata (e.g., `{"has_alternatives": true}`)
  - The `category` field will be added to this metadata dict

- **tests/test_parsers.py** (lines 225-415)
  - Contains existing tests for the crafting parser
  - New tests need to be added to verify category extraction

- **src/extract_transformations.py** (lines 72-112)
  - Calls `parse_crafting()` for the main crafting page
  - No changes required, but good to understand the context

### New Files
- **tests/test_category_extraction.py**
  - New test file specifically for testing category metadata extraction
  - Will contain tests for various section types and edge cases

## Implementation Plan

### Phase 1: Foundation
Add a helper function to extract the current category context from a BeautifulSoup element by traversing up the DOM to find the most recent section heading. This function will be used by the crafting parser to determine which category each recipe belongs to.

### Phase 2: Core Implementation
Modify the `parse_crafting()` function to:
1. For each crafting UI element, call the helper function to determine its category
2. Add the category to the transformation metadata
3. Handle edge cases (no category found, excluded sections, etc.)
4. Normalize category names for consistency

### Phase 3: Integration
1. Create comprehensive tests to verify category extraction works correctly
2. Run the extraction on actual wiki data to validate results
3. Verify the CSV output includes the category metadata
4. Update documentation if needed

## Step by Step Tasks

### 1. Create helper function to extract category from DOM element
- Add `extract_category_from_element()` function in `src/core/parsers.py`
- Function should traverse up the DOM tree to find the nearest h2/h3 heading with `mw-headline` class
- Extract the text content from the heading span
- Normalize the category name (lowercase, replace spaces with underscores, remove special characters)
- Return the normalized category name or None if not found
- Handle excluded sections (should not return "removed_recipes" or "changed_recipes")

### 2. Modify parse_crafting to add category metadata
- In the `parse_crafting()` function, after validating each crafting UI element
- Call `extract_category_from_element()` to get the category
- Add the category to the metadata dict when creating Transformation objects
- Ensure category is added for both simple recipes and alternative recipes
- Update all places where Transformation objects are created in the function

### 3. Create comprehensive test file for category extraction
- Create `tests/test_category_extraction.py`
- Test the `extract_category_from_element()` helper function with various HTML structures
- Test cases: recipe under h2 heading, recipe under h3 heading, nested sections, no heading found
- Test edge cases: excluded sections, multiple headings, special characters in category names

### 4. Add integration tests to existing test file
- Add tests to `tests/test_parsers.py` that verify `parse_crafting()` includes categories
- Test with realistic wiki HTML structure
- Verify category is present in metadata for simple recipes
- Verify category is present in metadata for recipes with alternatives

### 5. Run tests and fix any issues
- Run `uv run pytest tests/ -v` to execute all tests
- Fix any failing tests or bugs discovered
- Ensure all existing tests still pass (no regressions)

### 6. Test with real data
- Run `uv run python src/extract_transformations.py` to extract transformations
- Check `output/transformations.csv` to verify category metadata is present
- Manually verify a few known examples (e.g., repeater should have "redstone" or similar category)
- Verify the category values make sense and are properly normalized

### 7. Validate no regressions
- Run `uv run python src/validate_output.py` to check data quality
- Verify transformation count hasn't changed unexpectedly
- Ensure no errors or warnings in the validation output
- Confirm all tests pass with `uv run pytest tests/ -v`

## Testing Strategy

### Unit Tests
- **test_extract_category_from_element()**
  - Test with various HTML structures (h2, h3, nested divs)
  - Test normalization (spaces, underscores, lowercase)
  - Test edge cases (no heading, multiple headings, excluded sections)

- **test_parse_crafting_includes_category()**
  - Test that simple recipes include category metadata
  - Test that recipes with alternatives include category metadata
  - Test that category is correctly extracted from different section types

### Integration Tests
- **test_parse_crafting_with_realistic_html()**
  - Use realistic wiki HTML structure with multiple sections
  - Verify multiple recipes in different sections get correct categories
  - Verify excluded sections don't get category metadata (or get None)

### Edge Cases
- Recipe outside any section heading (category should be None or "uncategorized")
- Recipe in excluded section (should be filtered out entirely by existing logic)
- Section heading with special characters or unusual formatting
- Multiple nested headings (should use the most specific/closest heading)

## Acceptance Criteria
1. All crafting transformations in `transformations.csv` include a `category` field in metadata
2. Category names are normalized (lowercase, underscores instead of spaces)
3. Category matches the wiki section heading where the recipe appears
4. Examples work correctly:
   - Repeater has category "redstone" (or similar)
   - Minecart has category "transportation" (or similar)
   - Iron Block has category "building_blocks" (or similar)
5. All existing tests continue to pass (no regressions)
6. New tests for category extraction pass with 100% success rate
7. CSV output is valid and parseable
8. Total transformation count remains consistent with previous version

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

```bash
# Run all tests including new category tests
uv run pytest tests/ -v

# Run extraction to generate updated CSV with categories
uv run python src/extract_transformations.py

# Validate output data quality
uv run python src/validate_output.py

# Check that transformations.csv includes category metadata
head -20 output/transformations.csv

# Search for specific examples to verify categories
grep -i "repeater" output/transformations.csv
grep -i "minecart" output/transformations.csv
grep -i "iron block" output/transformations.csv

# Count transformations to ensure no data loss
wc -l output/transformations.csv
```

## Notes
- The wiki structure uses `<h2>` and `<h3>` tags with `<span class="mw-headline" id="...">` for section headings
- Main categories visible in crafting.html include: "Building blocks", "Decoration blocks", "Utilities", "Combat", "Materials", "Miscellaneous"
- Some recipes may not have a clear category (e.g., recipes at the top of the page before any section heading) - these should have category set to None or "uncategorized"
- The metadata field is already used for other purposes (e.g., `{"has_alternatives": true}`), so the category should be added alongside existing metadata, not replace it
- Category names from wiki may have inconsistent formatting - normalization is important for downstream consumers
- Consider adding category support to other transformation types in the future (smelting, smithing, etc.) but this feature focuses only on crafting
