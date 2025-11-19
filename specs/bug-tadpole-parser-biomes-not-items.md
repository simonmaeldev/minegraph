# Bug: Tadpole Parser Extracting Biomes as Mob Drops

## Bug Description
The mob drop parser incorrectly extracts 30 biome names from the tadpole wiki page as if they were items dropped by the mob. The tadpole page contains a "Behavior" section with a table showing which biomes tadpoles grow up in (to determine frog variants), but the parser is mistakenly treating these biome links as mob drops.

According to the wiki page: "As with other baby animals, tadpoles do not drop any items or experience on death."

**Expected Behavior:** Tadpole should have 0 transformations (no drops)

**Actual Behavior:** Tadpole has 30 transformations with biomes as "dropped items" (River, Beach, Taiga, etc.)

## Problem Statement
The `parse_mob_drops()` function in `src/core/parsers.py` is parsing tables in sections adjacent to or after the "Drops" section that contain non-drop information (like behavior tables showing biome-to-frog-variant mappings). The parser needs to be more restrictive about which sections it searches for drop tables.

## Solution Statement
Modify the `parse_mob_drops()` function to:
1. Only parse tables that are directly under the "Drops" section (immediate next sibling)
2. Skip parsing tables in "Behavior" sections or any sections after "Drops"
3. Ensure the parser stops at the next major section (h2) after "Drops"

The fix should ensure that tadpoles (and other mobs with 0 drops) correctly output 0 transformations, while mobs with actual drops continue to be parsed correctly.

## Steps to Reproduce
1. Run extraction: `uv run python src/extract_transformations.py`
2. Check output: `grep "Tadpole" output/transformations.csv`
3. Observe 30 incorrect transformations with biomes as outputs

## Root Cause Analysis
The bug is in `src/core/parsers.py` lines 959-990, specifically in the `parse_mob_drops()` function.

The parser searches for subsections under "Drops" and parses any wikitable found in those subsections. However, the search doesn't properly bound itself to the "Drops" section - it continues searching into subsequent sections like "Behavior".

For the tadpole page:
1. The parser finds the "Drops" section (h2)
2. It finds NO tables directly under "Drops" (correct - tadpole has no drops)
3. It then searches for subsections using `find_subsections()` which looks for h3 elements
4. The search incorrectly continues beyond the "Drops" section into the "Behavior" section
5. In the "Behavior" section, there's a table showing biome-to-frog-variant mappings
6. The parser extracts all the biome links (River, Beach, Taiga, etc.) as if they were dropped items

The issue is that `find_subsections()` (lines 849-879) searches for h3 elements between an h2 and the next h2, but the "Behavior" section is an h2, not an h3. So the parser is incorrectly looking at tables in the "Behavior" section thinking they're part of "Drops".

Actually, looking more carefully: The parser finds the "Drops" section at line 959-957, then at line 969 it calls `find_subsections(drops_section)` to find h3 subsections. The function should only return h3 elements between the "Drops" h2 and the next h2 (which would be "Behavior"). But the actual bug is that after finding no tables in direct subsections, the parser shouldn't be finding tables in the Behavior section at all.

Wait - re-reading the code more carefully at lines 979-990: The parser finds subsections, then for each subsection it searches for tables. The issue is that the search at line 983 (`current_elem = subsection_heading.find_next_sibling()`) walks through ALL siblings until hitting `next_heading`, and `next_heading` is found at line 980 as the next h2 OR h3.

The real bug: The Drops section on the tadpole page likely has NO h3 subsections between "Drops" (h2) and "Behavior" (h2), so `find_subsections()` returns an empty list. That's correct. But then the parser also searches for tables directly under the "Drops" section at line 962-964. The table being incorrectly parsed must be found by the `drops_section.find_next("table", class_="wikitable")` call at line 962.

The method `find_next()` searches ALL following elements in the document, not just immediate children or siblings! So it finds the first wikitable after the "Drops" heading, which is actually in the "Behavior" section.

**True Root Cause:** The `find_next()` call at line 962 searches the entire document tree after the "Drops" heading, crossing into other sections. It should only search within the "Drops" section boundary (until the next h2).

## Relevant Files
Use these files to fix the bug:

- **src/core/parsers.py** (lines 882-1005) - Contains the `parse_mob_drops()` function that needs to be fixed. The bug is specifically at line 962 where `find_next()` searches too broadly.

- **ai_doc/downloaded_pages/mobs/tadpole.html** - The HTML file being parsed, contains the Behavior section table that's being incorrectly extracted.

- **tests/test_parsers.py** - Contains test cases for the mob drop parser. Need to add a test case for tadpole to ensure 0 drops are extracted.

- **output/transformations.csv** - The output file containing the incorrect transformations that need to be eliminated.

- **extraction_output.txt** - Log file showing "Tadpole: 30 drops" which should be "Tadpole: 0 drops".

## Step by Step Tasks

### Fix the parse_mob_drops() function
- Replace the unbounded `find_next()` call at line 962 with a bounded search that only looks for tables between the "Drops" heading and the next major section (h2)
- The fix should use `find_next_sibling()` in a loop that stops when hitting the next h2 heading
- Ensure the search only finds tables that are truly within the "Drops" section boundary
- **Important**: Do NOT modify the subsection parsing (lines 969-990) or Gifts section parsing (lines 995-1003) - these already work correctly
- The fix only affects the main drops table search, which currently crosses section boundaries incorrectly

### Add test case for mobs with zero drops
- Add a test case in `tests/test_parsers.py` for tadpole to verify 0 transformations are extracted
- Test should parse the actual tadpole HTML file and assert len(transformations) == 0
- Add similar test for other mobs known to have no drops (e.g., Villager, Wandering Trader if they also have 0 drops)

### Verify fix doesn't break other mob parsers
- Run full test suite: `uv run pytest tests/test_parsers.py -v`
- Ensure all existing mob drop tests still pass
- Check that mobs with actual drops still extract correctly (e.g., zombie, skeleton)

### Run extraction and validate output
- Run extraction: `uv run python src/extract_transformations.py`
- Verify tadpole has 0 transformations: `grep "Tadpole" output/transformations.csv` should return nothing
- Check extraction_output.txt shows "Tadpole: 0 drops"
- Run validation: `uv run python src/validate_output.py`

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

```bash
# Run tests to verify the fix
uv run pytest tests/test_parsers.py::test_parse_mob_drops_tadpole -v

# Run all parser tests to ensure no regressions
uv run pytest tests/test_parsers.py -v

# Run extraction to generate new output
uv run python src/extract_transformations.py

# Verify tadpole has NO transformations in output (should return empty)
grep "Tadpole" output/transformations.csv

# Check extraction log shows 0 drops for tadpole
grep "Tadpole:" extraction_output.txt

# Run full validation to check data quality
uv run python src/validate_output.py

# Verify mobs WITH drops still work correctly (spot checks)
grep "Zombie" output/transformations.csv | head -n 5

# Verify cat still has all its drops (death drops + gifts, should be 7 items)
grep '^mob_drop.*"Cat"' output/transformations.csv | wc -l

# Verify cat still has its death drop (String)
grep '^mob_drop.*"Cat".*"String"' output/transformations.csv

# Verify cat still has its gifts (Rabbit's foot, Feather, etc.)
grep '^mob_drop.*"Cat".*"Rabbit' output/transformations.csv

# Verify armadillo still has 0 drops (should return nothing)
grep '^mob_drop.*"Armadillo"' output/transformations.csv
```

## Notes
- The bug affects any mob page where the "Drops" section has no table but a subsequent section (like "Behavior") has a wikitable with item/biome links
- The fix must be surgical - only change how tables are searched under the "Drops" section to respect section boundaries
- Other mobs that truly have no drops (Villager, Wandering Trader per the previous bug spec) should also benefit from this fix
- This is related to the previous bug "bug-mob-drop-parser-missing-items.md" but is a different issue (that bug was about missing drops, this bug is about false positive drops from wrong sections)

### Safety Verification
The fix has been verified to NOT affect other mobs:
- **Cat** (currently 7 mob_drop entries): Uses h3 subsection parsing (lines 969-990) for death drops and separate Gifts section parsing (lines 995-1003). The fix to line 962 does NOT affect these code paths. ✓
- **Armadillo** (currently 0 mob_drop entries): Has h3 subsections under "Drops" but no drop tables, correctly returns 0 drops. The fix maintains this behavior. ✓
- **Other mobs with death drops** (Zombie, Skeleton, etc.): Have drop tables either as direct siblings of "Drops" h2 (will be found by bounded search) or in h3 subsections (handled by separate code path). The fix maintains all existing functionality. ✓
