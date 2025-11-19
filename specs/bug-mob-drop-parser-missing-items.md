# Bug: Mob Drop Parser Missing Items from Non-Table Sections

## Bug Description

The mob drop parser (`parse_mob_drops` in `src/core/parsers.py`) only extracts drops from HTML tables in the "Drops" section, missing many legitimate mob drops that are documented in other formats:

**Actual behavior:**
- Only parses items from `<table class="wikitable">` elements after "Drops" heading
- Misses drops from subsections like "Brushing", "Gifts", "Goat horns", "Attacking", "Digging"
- Reports 20 mobs with no drops when they actually have drops documented

**Expected behavior:**
- Extract all item drops from various subsections under "Drops"
- Parse drops from list items (`<ul>/<li>` elements) with item links
- Handle special mob behaviors (brushing, gifts, attacking, digging) that yield items
- Correctly identify mobs with no drops (like Tadpole, Villager) vs mobs with drops in non-table format

**Examples of missing drops:**
- Armadillo: "Armadillo Scute" (from Brushing subsection)
- Cat: "String" + gifts table items (from Gifts subsection)
- Frog: "Froglight" (from Attacking subsection when eating magma cubes)
- Goat: "Goat Horn" (from Goat horns subsection)
- Piglin Brute: "Golden Axe" (from drop text)
- Sniffer: "Pitcher Pod", "Torchflower Seeds" (from Behavior section about digging)
- Squid: "Ink Sac" (from Drops table that exists)

## Problem Statement

The current `parse_mob_drops()` function has a narrow extraction pattern:
1. Finds "Drops" section heading
2. Looks for the first `<table class="wikitable">` after it
3. Only parses rows from that table

This fails because:
- Many drops are in subsections (h3 headings) under the main "Drops" section (h2)
- Some drops are documented in paragraph text with item links
- Some drops are in behavior sections outside "Drops" (e.g., Frog attacking, Sniffer digging)
- The parser doesn't look beyond the first table or into list items

## Solution Statement

Enhance `parse_mob_drops()` to:
1. Parse the main drops table (current behavior - keep this)
2. **NEW:** Parse subsections under "Drops" (h3 headings like "Brushing", "Goat horns")
3. **NEW:** Extract items from list elements (`<ul>/<li>`) containing item links
4. **NEW:** Parse special sections like "Gifts", "Attacking" that contain drop tables/lists
5. **NEW:** Add helper function to extract items from text/paragraphs with item links
6. Deduplicate items across all these sources
7. Maintain existing behavior for experience orbs (ignore them - not items)

## Steps to Reproduce

1. Run extraction: `uv run python src/extract_transformations.py`
2. Check output: `grep "^mob_drop," output/transformations.csv | wc -l` shows 209 drops
3. Examine mobs reported with 0 drops but actually have drops:
   - `grep "Armadillo: " extraction.log` → no drops found
   - `grep "Goat: " extraction.log` → no drops found
   - `grep "Cat: " extraction.log` → only 1 drop (should have String + ~10 gifts)
4. Manually inspect HTML files show drops exist in non-table format:
   - `grep -A 30 "Brushing" ai_doc/downloaded_pages/mobs/armadillo.html` → shows Armadillo Scute
   - `grep -A 30 "Goat horns" ai_doc/downloaded_pages/mobs/goat.html` → shows Goat Horn
   - `grep -A 40 "Gifts" ai_doc/downloaded_pages/mobs/cat.html` → shows gifts table

## Root Cause Analysis

The parser's HTML traversal logic stops at the first table:

```python
# Line 849-851 in src/core/parsers.py
table = drops_section.find_next("table", class_="wikitable")
if not table:
    return transformations
```

This means:
1. If there's no immediate table, it returns empty (missing subsection drops)
2. It never looks at subsections (h3 elements) under the Drops h2
3. It doesn't parse `<ul>/<li>` structures with item links
4. It doesn't handle sections outside "Drops" that contain behavioral drops (Attacking, Gifts, Behavior/Digging)

The mob drop extraction needs to be more comprehensive, looking at:
- All tables under "Drops" section (not just first one)
- All subsections (h3) under "Drops"
- List items with item links
- Special sections like "Gifts", "Attacking", "Goat horns", "Brushing"

## Relevant Files

- **`src/core/parsers.py`** (lines 821-896: `parse_mob_drops` function)
  - Contains the mob drop parser that needs enhancement
  - Need to expand HTML traversal to find subsections and lists
  - Add logic to parse items from non-table formats

- **`tests/test_parsers.py`** (lines 572-580: `test_parse_mob_drops_simple`)
  - Contains minimal test for mob drops
  - Need comprehensive tests for new extraction patterns

- **`ai_doc/downloaded_pages/mobs/*.html`**
  - Source HTML files with various drop formats
  - Reference for understanding HTML structures to parse
  - Specific files: armadillo.html, cat.html, frog.html, goat.html, piglin_brute.html, sniffer.html, squid.html

### New Files

None - all changes are modifications to existing files.

## Step by Step Tasks

### Step 1: Add helper function to extract items from any element with links

- Create `extract_items_from_element(element)` function in `src/core/parsers.py`
- Finds all `<a>` tags with `href` matching `/w/` pattern
- Calls `extract_item_from_link()` on each link
- Returns list of unique Item objects
- Place before `parse_mob_drops()` function (around line 820)

### Step 2: Add helper function to find all subsections under a heading

- Create `find_subsections(heading)` function in `src/core/parsers.py`
- Finds all h3 elements between the given heading and next h2
- Returns list of (subsection_heading, content_until_next_heading) tuples
- Handles sibling traversal to get content between headings
- Place before `parse_mob_drops()` function

### Step 3: Enhance parse_mob_drops to handle main drops table (current behavior)

- Keep existing table parsing logic (lines 849-895)
- Extract into separate internal function `_parse_drops_table(table, mob_item, seen_signatures, transformations)`
- This preserves backward compatibility

### Step 4: Add subsection parsing to parse_mob_drops

- After main table parsing, find all h3 subsections under "Drops" h2
- Common subsection ids: "Brushing", "Goat_horns", "On_death", "Breeding"
- For each subsection:
  - Look for tables first (use `_parse_drops_table` helper)
  - If no table, look for `<ul>/<li>` with item links
  - Extract items using `extract_items_from_element()`
- Skip subsections that only mention experience (not items)

### Step 5: Add special section parsers for behavioral drops

- Check for "Gifts" section (cats): parse table under this h3
- Check for "Attacking" section (frogs): parse paragraphs/lists for items like "froglight"
- Check for "Behavior" section (sniffers): find text about digging/seeds
- Use `extract_items_from_element()` on section content
- Add these as special cases after subsection parsing

### Step 6: Update deduplication logic

- Ensure `seen_signatures` set is used across all extraction methods
- Deduplicate items found from tables, lists, paragraphs, and special sections
- Maintain existing signature-based deduplication

### Step 7: Add comprehensive test cases

Add to `tests/test_parsers.py`:
- `test_parse_mob_drops_from_subsection_brushing()` - Armadillo scute from Brushing
- `test_parse_mob_drops_from_subsection_goat_horns()` - Goat horn from subsection
- `test_parse_mob_drops_from_list_items()` - Items in `<li>` without table
- `test_parse_mob_drops_from_gifts_section()` - Cat gifts table
- `test_parse_mob_drops_from_attacking_section()` - Frog froglight
- `test_parse_mob_drops_ignores_experience()` - Verify XP is not treated as item
- `test_parse_mob_drops_deduplicates()` - Same item from multiple sections

### Step 8: Test against real mob HTML files

- Run extraction on specific problematic mobs
- Verify Armadillo now shows Armadillo Scute
- Verify Goat now shows Goat Horn
- Verify Cat now shows String + gift items
- Verify Frog now shows Froglight
- Verify Squid shows Ink Sac
- Verify mobs truly without drops (Tadpole, Villager, Wandering Trader) still show 0

### Step 9: Run full extraction and validate

- Execute `uv run python src/extract_transformations.py`
- Compare before/after mob drop counts
- Expected: increase from 209 to ~250+ transformations
- Expected: reduction in mobs with 0 drops from 20 to <10
- Verify output quality with `uv run python src/validate_output.py`

### Step 10: Run Validation Commands

Execute validation commands to confirm bug is fixed with zero regressions.

## Validation Commands

Execute every command to validate the bug is fixed with zero regressions:

```bash
# Run all existing tests to ensure no regressions
uv run pytest tests/test_parsers.py -v

# Run full test suite
uv run pytest tests/ -v

# Run extraction and capture output
uv run python src/extract_transformations.py 2>&1 | tee extraction_output.txt

# Verify specific mobs now have drops
grep "Armadillo:" extraction_output.txt  # Should show >0 drops
grep "Goat:" extraction_output.txt  # Should show >0 drops
grep "Cat:" extraction_output.txt  # Should show >1 drops (String + gifts)
grep "Frog:" extraction_output.txt  # Should show >0 drops
grep "Squid:" extraction_output.txt  # Should show >0 drops

# Count total mob drop transformations (should be >209)
grep "^mob_drop," output/transformations.csv | wc -l

# Count mobs with zero drops (should be <10)
grep ": 0 drops" extraction_output.txt | wc -l

# Verify no duplicate transformations
uv run python src/validate_output.py

# Verify Tadpole and Villager still correctly have 0 drops (they shouldn't drop items)
grep "Tadpole:" extraction_output.txt | grep "0 drops"
grep "Villager:" extraction_output.txt | grep "0 drops"
```

## Notes

- **Do not parse experience orbs as items** - XP drops are not items and should be ignored
- **Villager and Wandering Trader** drops come from trading, not mob_drop - should remain 0
- **Tadpole** truly has no drops - should remain 0
- **Ender Dragon** has complex drop mechanics - may require special handling
- **Maintain backward compatibility** - existing table parsing must continue to work
- **BeautifulSoup navigation** - use `.find_next_sibling()`, `.find_all()` for traversal
- **Edition filtering** - apply `is_java_edition()` checks to new sections parsed
- Consider that some mobs may have drops in multiple subsections - dedupe across all
- Gift items from cats are a special loot table - extract all items from the gifts table
- Froglight variants (Ochre, Verdant, Pearlescent) may all be listed - extract all
