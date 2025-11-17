# Bug: Missing Trading Transformations

## Bug Description
The trading parser is extracting only a small fraction of the trades present in the Minecraft wiki trading page. For the Armorer villager alone, only 4 trades are being parsed when there should be approximately 15+ trades. Missing trades include:
- **Item-to-Emerald trades (selling)**: Coal, Iron Ingot, Lava Bucket, Diamond
- **Emerald-to-Item trades (buying)**: All iron armor pieces, Chainmail Leggings, Chainmail Boots, Chainmail Chestplate, Shield, and enchanted diamond armor pieces

Similar patterns of missing trades occur across other villager types (Butcher, Fisherman, Fletcher, etc.), resulting in incomplete trading graph data.

## Problem Statement
The `parse_trading()` function in `src/core/parsers.py` is not correctly handling the complex table structure used by the Minecraft wiki for trading data. The wiki tables use a "Slot" column system where multiple rows share the same slot number, representing different possible trades at the same villager level with different probabilities. The current parser iterates through rows sequentially but fails to recognize that many consecutive rows belong to different trade options within the same slot.

## Solution Statement
Simplify and fix the trading parser to parse ALL trades from ALL villager profession tables:
1. **Remove Java Edition filtering** for trading tables since both editions offer the same trades (only probabilities differ, which we ignore)
2. **Find "Item wanted" and "Item given" columns dynamically** per row by searching for cells containing item links, instead of using fixed header-based indices
3. **Parse every data row** as a potential trade - if a row has both wanted and given items, create a transformation
4. **Remove level extraction** - level metadata is not needed for the transformation graph (just villager_type is sufficient)
5. Ensure ALL villager profession tables are processed (Armorer, Butcher, Cartographer, Cleric, Farmer, Fisherman, Fletcher, Leatherworker, Librarian, Mason, Shepherd, Toolsmith, Weaponsmith)

## Steps to Reproduce
1. Run `uv run python -c "from src.core.parsers import parse_trading; import sys; html = open('ai_doc/downloaded_pages/trading.html').read(); trades = parse_trading(html); armorer = [t for t in trades if t.metadata.get('villager_type') == 'Armorer']; print(f'Armorer trades: {len(armorer)}'); [print(f\"  {', '.join(i.name for i in t.inputs)} -> {', '.join(o.name for o in t.outputs)}\") for t in armorer]"`
2. Observe that only 4 Armorer trades are returned
3. Expected: Should return 15+ Armorer trades including Coal->Emerald, Iron Ingot->Emerald, Lava Bucket->Emerald, Diamond->Emerald, Emerald->Iron Helmet/Chestplate/Leggings/Boots, Emerald->Chainmail pieces, Emerald->Shield, and enchanted diamond armor trades

## Root Cause Analysis
Examining the trading HTML structure and current parser logic:

**HTML Table Structure:**
```html
<tr>
  <th rowspan="5">Novice</th>           <!-- Level spans multiple rows -->
  <th rowspan="1">1</th>                 <!-- Slot 1 -->
  <td>100%</td>                          <!-- Bedrock probability -->
  <td>40%</td>                           <!-- Java probability -->
  <td>15 × Coal</td>                     <!-- Item wanted -->
  <td>Emerald</td>                       <!-- Item given -->
  ...
</tr>
<tr>
  <th rowspan="4">2</th>                 <!-- Slot 2 - new trade slot -->
  <td>25%</td>
  <td>40%</td>
  <td>5 × Emerald</td>
  <td>Iron Helmet</td>
  ...
</tr>
<tr>                                     <!-- Still Slot 2 - different option -->
  <td>25%</td>
  <td>40%</td>
  <td>9 × Emerald</td>
  <td>Iron Chestplate</td>
  ...
</tr>
```

**Current Parser Logic Issues:**
1. **CRITICAL BUG #1 - Over-filtering by Edition**: The parser tries to filter for Java Edition only by checking `java_col_idx`, but **both Bedrock and Java editions offer the same trades** (only probabilities differ). Since we ignore probabilities, we should parse ALL rows regardless of edition markers. The current Java Edition filtering is causing many valid trades to be skipped.

2. **CRITICAL BUG #2 - Column Index Mismatch**: The indices `wanted_idx` and `given_idx` are calculated from the **header row**, but subsequent data rows have **different column counts** because:
   - The "Level" cell uses `rowspan` to span multiple rows, so it's missing from most data rows
   - The "Slot" cell also uses `rowspan`, missing from some data rows
   - This causes column indices to shift, making `cells[wanted_idx]` and `cells[given_idx]` point to the wrong columns

3. **CRITICAL BUG #3 - Multiple Rows per Slot**: The parser doesn't recognize that multiple consecutive rows can represent different trade options within the same slot (e.g., 4 different armor pieces all sharing the same level/slot due to rowspan).

**Example of Index Mismatch:**
- Header row: `[Level, Slot, BE Prob, JE Prob, Item wanted, Item given, ...]` → indices 0,1,2,3,4,5
- First data row (with Level + Slot cells): `[Novice, 1, 100%, 40%, Coal, Emerald, ...]` → indices match
- Second data row (Slot cell only, no Level): `[2, 25%, 40%, Emerald, Iron Helmet, ...]` → indices DON'T match!
  - Using index 4 (for "Item wanted") actually gets "Iron Helmet" instead of "Emerald"
  - The parser is looking in the wrong columns

**Key Insight from User**: Since Bedrock and Java editions offer the same trades (only probabilities differ), and we're ignoring probabilities, we should **parse ALL rows from ALL villager profession tables** without filtering by edition. This dramatically simplifies the fix.

## Relevant Files
Focus on the following files:

- **src/core/parsers.py** (lines 679-861)
  - Contains the `parse_trading()` function that needs to be fixed
  - The function currently tries to use fixed column indices but doesn't account for rowspan-induced column shifts
  - Need to make column detection dynamic per-row instead of using header-based fixed indices

- **tests/test_parsers.py** (lines 257-467)
  - Contains existing tests for `parse_trading()` including item-to-emerald and emerald-to-item tests
  - Tests pass for simple single-row cases but don't cover multi-slot scenarios
  - Need to add comprehensive test cases for multi-slot trades (multiple trades at same level)

- **ai_doc/downloaded_pages/trading.html**
  - Source HTML data that the parser needs to process
  - Contains complex table structures with rowspan attributes
  - Used for validation and testing of parser fixes

### New Files
None required - this is a bug fix to existing functionality.

## Step by Step Tasks

### 1. Understand Current Parser and Identify All Issues
- Read `src/core/parsers.py` lines 679-861 to understand current `parse_trading()` logic
- Identify where Java Edition filtering is causing trades to be skipped
- Identify where fixed column indices cause misalignment with actual data rows
- Document all the issues found in code comments
- List all 13 villager professions that should be parsed: Armorer, Butcher, Cartographer, Cleric, Farmer, Fisherman, Fletcher, Leatherworker, Librarian, Mason, Shepherd, Toolsmith, Weaponsmith

### 2. Remove Java Edition Filtering and Level Extraction
- **Remove or disable** the Java Edition filtering logic in `parse_trading()` (lines checking `java_col_idx`, `is_java_edition()`)
- **Remove level extraction logic** - we don't need level metadata for the transformation graph
- Since both editions offer the same trades, parse ALL rows from ALL tables
- Keep only the villager_type extraction logic (from `data-description` attribute)
- This simplification will allow us to capture all trades without worrying about edition columns or rowspan issues

### 3. Implement Dynamic Column Detection Per Row
- **Replace fixed header-based indices** (`wanted_idx`, `given_idx`) with dynamic per-row detection
- For each data row, iterate through ALL cells and identify:
  - **Input cell**: Contains item links (`<a href="/w/Item">`) representing items the player gives to villager
  - **Output cell**: Contains item links representing items the villager gives to player
- Use heuristic: look for cells with `<a href="/w/">` links - typically there are 2 such cells per row (wanted and given)
- The logic should find cells with item links (can identify them by checking for `<a>` tags with `/w/` in href)
- Handle quantity parsing (e.g., "15 × Coal") using existing `parse_quantity()` helper
- Handle multiple items in same cell (e.g., "Emerald + Book") using existing logic

### 4. Ensure All Rows Are Parsed
- Remove any early `continue` statements that skip rows unnecessarily
- Parse EVERY row in the table that comes after the header row
- For each row:
  - Find cells with item links (wanted and given)
  - If both are found, create a transformation with metadata containing only `villager_type`
  - Extract villager_type from table header (existing logic with `data-description`)
- This ensures multi-slot trades (multiple rows with same slot) are all captured
- Ignore rows that don't have both wanted and given items (header rows, separator rows, etc.)

### 5. Add Comprehensive Tests
- Add test case for multi-slot trades: Armorer with 4 iron armor pieces
- Add test case for ALL missing items: Coal, Iron Ingot, Lava Bucket, Diamond, Chainmail pieces
- Add test case to verify total Armorer trade count is 15+
- Add test case for Butcher trades including Raw Chicken, Raw Rabbit, Raw Porkchop
- Update existing tests to remove level assertions if they check for level metadata
- Ensure existing tests still pass (no regression)

### 6. Validate Against Full Dataset
- Run `uv run python src/extract_transformations.py` to regenerate CSV files
- Verify Armorer trades increased from 4 to 15+
- Check ALL 13 villager professions have complete trade lists
- Verify item-to-emerald trades (selling) are present: Coal, Iron Ingot, Lava Bucket, etc.
- Verify emerald-to-item trades (buying) are complete: all armor, weapons, tools, etc.
- Ensure no regression: existing parsed trades remain correct
- Total trade count should increase from ~53 to 150-200+

### 7. Run All Tests and Validation Commands
- Execute `uv run pytest tests/test_parsers.py -v -k trading` to run trading-specific tests
- Execute `uv run pytest tests/ -v` to run full test suite
- Execute `uv run python src/validate_output.py` to check output quality
- Confirm total trade count is significantly higher (from ~53 to 150-200+)
- Verify all expected items appear in the trades (see validation commands below)

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

### Quick Parser Tests (Before Running Full Extraction)
- `uv run python -c "from src.core.parsers import parse_trading; html = open('ai_doc/downloaded_pages/trading.html').read(); trades = parse_trading(html); print(f'Total trades: {len(trades)} (should be 150-200+)')"`  - Verify total trade count is significantly increased
- `uv run python -c "from src.core.parsers import parse_trading; html = open('ai_doc/downloaded_pages/trading.html').read(); trades = parse_trading(html); armorer = [t for t in trades if t.metadata.get('villager_type') == 'Armorer']; print(f'Armorer trades: {len(armorer)} (should be 15+)'); print('\\nArmorer item check:'); items_to_check = ['Coal', 'Iron Ingot', 'Lava Bucket', 'Iron Helmet', 'Iron Chestplate', 'Iron Leggings', 'Iron Boots', 'Chainmail Leggings', 'Chainmail Boots', 'Chainmail Chestplate', 'Chainmail Helmet', 'Bell', 'Shield', 'Diamond']; [print(f'  {item}: {\"✓ FOUND\" if any(item in i.name or item in o.name for t in armorer for i in t.inputs for o in t.outputs) else \"✗ MISSING\"}') for item in items_to_check]"` - Verify all expected Armorer items are parsed
- `uv run python -c "from src.core.parsers import parse_trading; html = open('ai_doc/downloaded_pages/trading.html').read(); trades = parse_trading(html); butcher = [t for t in trades if t.metadata.get('villager_type') == 'Butcher']; print(f'Butcher trades: {len(butcher)} (should be 8+)'); print('\\nButcher item check:'); items = ['Raw Chicken', 'Raw Rabbit', 'Raw Porkchop']; [print(f'  {item}: {\"✓ FOUND\" if any(item in i.name for t in butcher for i in t.inputs) else \"✗ MISSING\"}') for item in items]"` - Verify Butcher trades include Raw Chicken, Raw Rabbit, Raw Porkchop
- `uv run python -c "from src.core.parsers import parse_trading; html = open('ai_doc/downloaded_pages/trading.html').read(); trades = parse_trading(html); fisherman = [t for t in trades if t.metadata.get('villager_type') == 'Fisherman']; print(f'Fisherman trades: {len(fisherman)} (should be 8+)'); items = ['Pufferfish']; [print(f'  {item}: {\"✓ FOUND\" if any(item in i.name for t in fisherman for i in t.inputs) else \"✗ MISSING\"}') for item in items]"` - Verify Fisherman trades include Pufferfish
- `uv run python -c "from src.core.parsers import parse_trading; html = open('ai_doc/downloaded_pages/trading.html').read(); trades = parse_trading(html); fletcher = [t for t in trades if t.metadata.get('villager_type') == 'Fletcher']; print(f'Fletcher trades: {len(fletcher)} (should be 10+)'); items = ['Flint', 'Tripwire Hook']; [print(f'  {item}: {\"✓ FOUND\" if any(item in i.name for t in fletcher for i in t.inputs) else \"✗ MISSING\"}') for item in items]"` - Verify Fletcher trades include Flint, Tripwire Hook
- `uv run python -c "from src.core.parsers import parse_trading; html = open('ai_doc/downloaded_pages/trading.html').read(); trades = parse_trading(html); farmer = [t for t in trades if t.metadata.get('villager_type') == 'Farmer']; print(f'Farmer trades: {len(farmer)} (should be 15+)'); items = ['Melon']; [print(f'  {item}: {\"✓ FOUND\" if any(item in i.name for t in farmer for i in t.inputs) else \"✗ MISSING\"}') for item in items]"` - Verify Farmer trades include Melon
- `uv run python -c "from src.core.parsers import parse_trading; html = open('ai_doc/downloaded_pages/trading.html').read(); trades = parse_trading(html); cartographer = [t for t in trades if t.metadata.get('villager_type') == 'Cartographer']; print(f'Cartographer trades: {len(cartographer)} (should be 8+)'); items = ['Glass Pane', 'Paper']; [print(f'  {item}: {\"✓ FOUND\" if any(item in i.name for t in cartographer for i in t.inputs) else \"✗ MISSING\"}') for item in items]"` - Verify Cartographer trades include Glass Pane, Paper
- `uv run python -c "from src.core.parsers import parse_trading; html = open('ai_doc/downloaded_pages/trading.html').read(); trades = parse_trading(html); cleric = [t for t in trades if t.metadata.get('villager_type') == 'Cleric']; print(f'Cleric trades: {len(cleric)} (should be 8+)'); items = ['Nether Wart']; [print(f'  {item}: {\"✓ FOUND\" if any(item in i.name for t in cleric for i in t.inputs) else \"✗ MISSING\"}') for item in items]"` - Verify Cleric trades include Nether Wart
- `uv run python -c "from src.core.parsers import parse_trading; html = open('ai_doc/downloaded_pages/trading.html').read(); trades = parse_trading(html); leatherworker = [t for t in trades if t.metadata.get('villager_type') == 'Leatherworker']; print(f'Leatherworker trades: {len(leatherworker)} (should be 10+)'); items = ['Leather']; [print(f'  {item}: {\"✓ FOUND\" if any(item in i.name for t in leatherworker for i in t.inputs) else \"✗ MISSING\"}') for item in items]"` - Verify Leatherworker trades include Leather
- `uv run python -c "from src.core.parsers import parse_trading; html = open('ai_doc/downloaded_pages/trading.html').read(); trades = parse_trading(html); shepherd = [t for t in trades if t.metadata.get('villager_type') == 'Shepherd']; print(f'Shepherd trades: {len(shepherd)} (should be 15+)'); items = ['Magenta Dye']; [print(f'  {item}: {\"✓ FOUND\" if any(item in i.name or item in o.name for t in shepherd for i in t.inputs for o in t.outputs) else \"✗ MISSING\"}') for item in items]"` - Verify Shepherd trades include Magenta Dye
- `uv run python -c "from src.core.parsers import parse_trading; html = open('ai_doc/downloaded_pages/trading.html').read(); trades = parse_trading(html); toolsmith = [t for t in trades if t.metadata.get('villager_type') == 'Toolsmith']; print(f'Toolsmith trades: {len(toolsmith)} (should be 12+)')"` - Verify Toolsmith trade count
- `uv run python -c "from src.core.parsers import parse_trading; html = open('ai_doc/downloaded_pages/trading.html').read(); trades = parse_trading(html); mason = [t for t in trades if t.metadata.get('villager_type') == 'Mason']; print(f'Mason trades: {len(mason)} (should be 10+)'); items = ['Nether Quartz']; [print(f'  {item}: {\"✓ FOUND\" if any(item in i.name for t in mason for i in t.inputs) else \"✗ MISSING\"}') for item in items]"` - Verify Mason trades include Nether Quartz
- `uv run python -c "from src.core.parsers import parse_trading; html = open('ai_doc/downloaded_pages/trading.html').read(); trades = parse_trading(html); cleric = [t for t in trades if t.metadata.get('villager_type') == 'Cleric']; items = ['Fermented Spider Eye']; [print(f'  {item}: {\"✓ FOUND\" if any(item in i.name for t in cleric for i in t.inputs) else \"✗ MISSING\"}') for item in items]"` - Verify Cleric trades include Fermented Spider Eye

### Unit Tests
- `uv run pytest tests/test_parsers.py::TestParsers::test_parse_trading_item_to_emerald -v` - Verify item-to-emerald trades test passes
- `uv run pytest tests/test_parsers.py::TestParsers::test_parse_trading_emerald_to_item -v` - Verify emerald-to-item trades test passes
- `uv run pytest tests/test_parsers.py -v -k trading` - Run all trading-related tests
- `uv run pytest tests/ -v` - Run full test suite to ensure no regressions

### Full Extraction and CSV Validation
- `uv run python src/extract_transformations.py` - Regenerate CSV files with complete trading data
- `uv run python src/validate_output.py` - Validate output quality and check for any issues
- `grep -c "TRADING" output/transformations.csv` - Count total trading transformations (should be 150-200+)
- `grep -i "chainmail" output/transformations.csv | wc -l` - Verify chainmail armor pieces appear in output (should be 4+ lines)
- `grep "Coal.*Emerald" output/transformations.csv | head -3` - Verify Coal to Emerald trade exists
- `grep "Iron Ingot.*Emerald" output/transformations.csv | head -3` - Verify Iron Ingot to Emerald trade exists
- `grep "Lava Bucket.*Emerald" output/transformations.csv | head -3` - Verify Lava Bucket to Emerald trade exists
- `grep -i "raw chicken.*emerald" output/transformations.csv | head -3` - Verify Raw Chicken to Emerald trade exists
- `grep -i "glass pane.*emerald" output/transformations.csv | head -3` - Verify Glass Pane to Emerald trade exists
- `grep -i "leather.*emerald" output/transformations.csv | head -3` - Verify Leather to Emerald trade exists
- `grep -i "paper.*emerald" output/transformations.csv | head -3` - Verify Paper to Emerald trade exists

## Notes

### Key Insights
- **Both Bedrock and Java editions offer the same trades** - only the probability distributions differ
- Since we're building a transformation graph and **ignoring probabilities**, we can safely parse ALL rows regardless of edition markers
- This dramatically simplifies the fix: remove edition filtering for trading tables and parse everything

### Implementation Details
- The wiki table structure uses `rowspan` attributes to reduce visual redundancy, but this creates complex parsing requirements
- This bug was likely introduced because the initial implementation worked for simple tables but didn't account for:
  1. Multi-slot structure (multiple rows per slot)
  2. Rowspan causing column index misalignment
  3. Over-aggressive Java Edition filtering
- The fix uses dynamic column detection by searching for item links in cells, avoiding the rowspan index mismatch issue
- By removing edition filtering and level extraction, we dramatically simplify the parser and ensure all trades are captured

### Validation Checklist
- All 13 villager professions should have complete trade lists: Armorer, Butcher, Cartographer, Cleric, Farmer, Fisherman, Fletcher, Leatherworker, Librarian, Mason, Shepherd, Toolsmith, Weaponsmith
- Item-to-emerald trades (selling) should be present: Coal, Iron Ingot, Lava Bucket, Diamond, Raw Chicken, Raw Rabbit, Glass Pane, Nether Wart, Melon, Pufferfish, Tripwire Hook, Leather, Paper, Nether Quartz, Magenta Dye, Flint, Fermented Spider Eye, etc.
- Emerald-to-item trades (buying) should be complete: all armor pieces (including chainmail), weapons, tools, enchanted items, etc.
- The metadata extraction for villager type should be validated after the fix (level is no longer extracted)
- Similar table structures may exist in other wiki pages - this pattern could be generalized if needed
