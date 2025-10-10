# Feature: Extract Lazy-Loaded Crafting Recipes from Subcategory Pages

## Feature Description
The Minecraft Wiki crafting page uses lazy-loaded content sections for recipe categories (Building blocks, Decoration blocks, Redstone, Transportation, Foodstuffs, Tools, Utilities, Combat, Brewing, Materials, and Miscellaneous). These sections are initially hidden and only displayed when users click "show". The actual recipe data is stored in separate wiki pages (e.g., `/w/Crafting/Building_blocks`) that need to be downloaded and parsed. This feature implements a system to detect these lazy-load patterns in the main crafting page, download the subcategory pages containing the actual recipes, parse them to extract crafting transformations, and filter out Bedrock Edition and Minecraft Education recipes to only extract Java Edition content.

## User Story
As a data extractor
I want to automatically detect and download lazy-loaded crafting recipe subcategories
So that I can extract all Java Edition crafting recipes from the Minecraft Wiki, excluding Bedrock Edition and Minecraft Education content

## Problem Statement
The current crafting parser only extracts recipes directly embedded in the main crafting page HTML. However, the majority of crafting recipes are organized into category-specific pages (Building blocks, Decoration blocks, etc.) that are lazy-loaded via `<div class="load-page">` elements with `data-page` attributes pointing to subcategory URLs like `Crafting/Building_blocks`. These subcategory pages contain the actual crafting recipes, but they are never downloaded or parsed, resulting in incomplete extraction. Additionally, some recipes are marked for Bedrock Edition or Minecraft Education and must be filtered out to maintain Java Edition purity.

## Solution Statement
Implement a two-phase extraction approach:

**Phase 1: Pattern Detection**
- Parse the main crafting page HTML to detect `<div class="load-page">` elements
- Extract `data-page` attributes (e.g., "Crafting/Building blocks") to identify subcategory URLs
- Construct full URLs by prepending `https://minecraft.wiki/w/` to the page references
- Filter out "Changed recipes" and "Removed recipes" sections as they should be ignored

**Phase 2: Download & Parse**
- Download each subcategory page HTML (with caching to avoid redundant downloads)
- Parse the downloaded HTML to extract crafting recipes using existing `parse_crafting()` logic
- Apply edition filtering to exclude recipes marked "Bedrock Edition" or "Minecraft Education"
- Aggregate all transformations from subcategory pages with the main page transformations

## Relevant Files
Use these files to implement the feature:

- **ai_doc/downloaded_pages/crafting.html** (lines 158-200)
  - Contains the lazy-load `<div class="load-page">` patterns that need to be detected
  - Each div has `data-page="Crafting/{category}"` attribute with the subcategory reference
  - Categories include: Building blocks, Decoration blocks, Redstone, Transportation, Foodstuffs, Tools, Utilities, Combat, Brewing, Materials, Miscellaneous
  - Should ignore sections with "Changed" or "Removed" in the data-page attribute

- **src/core/download_data.py** (entire file)
  - Contains `download_page()` function for downloading wiki pages with caching
  - Contains `WIKI_PAGES` dictionary mapping page names to URLs
  - Will be extended to support dynamic subcategory page downloads
  - Already has proper User-Agent and timeout handling

- **src/core/parsers.py** (lines 116-216)
  - Contains `parse_crafting()` function that extracts recipes from HTML
  - Already has `is_java_edition()` filter (lines 9-33) to exclude Bedrock/Education content
  - Will be used to parse both main page and subcategory pages
  - Already handles recipe deduplication via signature tracking

- **src/extract_transformations.py** (lines 46-100)
  - Contains `extract_all_transformations()` that orchestrates parsing
  - Currently only parses main crafting.html file once
  - Will be modified to detect lazy-load patterns and trigger subcategory downloads/parsing
  - Uses `load_html_file()` helper to read HTML content

### New Files

- **src/core/lazy_load_detector.py**
  - New module for detecting and processing lazy-loaded content
  - Contains function to find `<div class="load-page">` elements
  - Extracts `data-page` attributes and constructs full URLs
  - Filters out unwanted sections (Changed/Removed recipes)
  - Returns list of subcategory URLs to download

## Implementation Plan

### Phase 1: Foundation
Create the lazy-load detection system that identifies subcategory pages requiring download. This involves analyzing the main crafting HTML to find `<div class="load-page">` elements with `data-page` attributes, extracting the subcategory references (e.g., "Crafting/Building blocks"), constructing full URLs, and filtering out sections we want to ignore (Changed recipes, Removed recipes).

### Phase 2: Core Implementation
Implement the download and parse logic for subcategory pages. This includes extending the download_data module to support dynamic subcategory downloads with proper caching, modifying the crafting parser to handle both main and subcategory pages, and ensuring Bedrock Edition and Minecraft Education recipes are filtered out using the existing `is_java_edition()` function.

### Phase 3: Integration
Integrate the lazy-load detection and parsing into the main extraction pipeline. The `extract_all_transformations()` function will be updated to first detect subcategory pages from the main crafting HTML, download each subcategory page, parse recipes from both main and subcategory pages, deduplicate transformations, and aggregate all results.

## Step by Step Tasks

### 1. Create lazy-load detection module
- Create new file `src/core/lazy_load_detector.py`
- Implement `find_lazy_load_pages(html_content: str) -> List[str]` function
- Use BeautifulSoup to find all `<div class="load-page">` elements
- Extract `data-page` attribute values (e.g., "Crafting/Building blocks")
- Filter out pages containing "Changed" or "Removed" in the name
- Construct full URLs by prepending "https://minecraft.wiki/w/" to each page reference
- Return list of URLs to download

### 2. Extend download_data module for dynamic subcategory downloads
- Add `download_crafting_subcategory(page_ref: str, output_dir: str) -> str` function to `src/core/download_data.py`
- Accept page reference like "Crafting/Building_blocks"
- Construct URL as `https://minecraft.wiki/w/{page_ref}`
- Use existing `download_page()` logic with caching
- Save to `{output_dir}/crafting_{category}.html` (e.g., "crafting_building_blocks.html")
- Return path to downloaded file

### 3. Verify edition filtering in parse_crafting()
- Review `is_java_edition()` function in `src/core/parsers.py` (lines 9-33)
- Ensure it correctly filters out elements containing "Bedrock Edition" or "Minecraft Education"
- Add test case with sample Bedrock/Education HTML to verify filtering works
- Confirm filter applies to all crafting UI elements before parsing

### 4. Update extract_transformations to orchestrate lazy-load extraction
- Modify `extract_all_transformations()` in `src/extract_transformations.py`
- After loading main crafting.html, call `find_lazy_load_pages()` to detect subcategories
- For each subcategory URL, call `download_crafting_subcategory()` to fetch HTML
- Parse each subcategory HTML with `parse_crafting()`
- Combine transformations from main page + all subcategory pages
- Ensure deduplication happens across all sources

### 5. Add logging for transparency
- Log the number of lazy-load subcategories detected
- Log each subcategory download (using existing "Downloading..." / "Using cached..." messages)
- Log transformation count per subcategory
- Log total transformations after aggregation

### 6. Create integration test
- Create test file `tests/test_lazy_load_extraction.py`
- Test `find_lazy_load_pages()` with sample HTML containing load-page divs
- Verify correct URLs are extracted
- Verify "Changed" and "Removed" sections are filtered out
- Test end-to-end extraction with mock subcategory HTML

### 7. Run validation commands
- Execute all validation commands to ensure the feature works correctly
- Verify significantly more crafting recipes are extracted after implementation
- Check that no Bedrock/Education recipes appear in output
- Ensure no regressions in other transformation types

## Testing Strategy

### Unit Tests
- **test_find_lazy_load_pages()**: Test lazy-load detection with sample HTML
  - Input: HTML with 3 load-page divs (Building blocks, Decoration blocks, Changed recipes)
  - Expected: Returns 2 URLs (excludes "Changed recipes")
  - Verify URLs are correctly formatted with wiki base URL

- **test_is_java_edition_filters_bedrock()**: Test edition filtering
  - Input: HTML element with "Bedrock Edition" text
  - Expected: `is_java_edition()` returns False

- **test_is_java_edition_filters_education()**: Test education filtering
  - Input: HTML element with "Minecraft Education" text
  - Expected: `is_java_edition()` returns False

- **test_download_crafting_subcategory_caching()**: Test download caching
  - Download same subcategory twice
  - Verify second call uses cached file, not new download

### Integration Tests
- **test_extract_crafting_with_subcategories()**: End-to-end test
  - Mock main crafting HTML with load-page divs
  - Mock subcategory HTML with sample recipes
  - Verify transformations from both sources are extracted
  - Verify deduplication works across main + subcategory pages

### Edge Cases
- Empty subcategory page (no recipes found) - should not crash, return empty list
- Subcategory page with only Bedrock recipes - should return empty list after filtering
- Malformed data-page attribute - should skip gracefully with warning
- Network error during subcategory download - should log error and continue with other subcategories
- Duplicate recipes across main page and subcategory - should deduplicate correctly

## Acceptance Criteria
- [ ] Lazy-load detector successfully finds all `<div class="load-page">` elements from main crafting page
- [ ] All subcategory URLs are correctly constructed (e.g., `https://minecraft.wiki/w/Crafting/Building_blocks`)
- [ ] "Changed recipes" and "Removed recipes" sections are filtered out and not downloaded
- [ ] All subcategory pages are downloaded with proper caching (no redundant downloads)
- [ ] Recipes are extracted from all subcategory pages using `parse_crafting()`
- [ ] Bedrock Edition and Minecraft Education recipes are filtered out from all sources
- [ ] Transformations from main page and subcategory pages are properly aggregated
- [ ] Deduplication works correctly across all sources
- [ ] Extraction count increases significantly (from ~50 to 500+ crafting recipes)
- [ ] All existing tests pass with zero regressions
- [ ] New integration tests verify lazy-load extraction works end-to-end

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

```bash
# Run all tests to ensure no regressions
uv run pytest tests/ -v

# Run extraction with new lazy-load feature
uv run python src/extract_transformations.py

# Count crafting transformations before and after (should increase significantly)
grep '"crafting"' output/transformations.csv | wc -l

# Verify no Bedrock Edition recipes in output
grep -i "bedrock" output/transformations.csv | wc -l  # Should be 0

# Verify no Minecraft Education recipes in output
grep -i "education" output/transformations.csv | wc -l  # Should be 0

# Check for proper deduplication (no exact duplicate rows)
sort output/transformations.csv | uniq -d | wc -l  # Should be 0

# Validate overall output quality
uv run python src/validate_output.py

# List downloaded subcategory files
ls -lh ai_doc/downloaded_pages/crafting_*.html
```

## Notes
- The lazy-load pattern `<div class="load-page" data-page="...">` is a JavaScript-driven content loading mechanism used by the Minecraft Wiki
- When users visit the page with JavaScript enabled, clicking "show" triggers a request to load the subcategory content
- Since we're parsing static HTML, we need to manually detect these references and download the linked pages
- The `data-page` attribute contains a relative wiki path (e.g., "Crafting/Building_blocks"), not a full URL
- Each subcategory page follows the same HTML structure as the main crafting page, so `parse_crafting()` can handle both
- Bedrock Edition uses different mechanics and recipe formats, so filtering is essential for Java Edition accuracy
- Minecraft Education includes special items not available in standard Java Edition
- The existing `is_java_edition()` function should handle filtering, but verify it works correctly with subcategory pages
- Consider rate limiting if downloading many subcategory pages (though caching should minimize requests)
- Future enhancement: This pattern may apply to other transformation types (smelting, smithing, etc.) - consider generalizing the approach
