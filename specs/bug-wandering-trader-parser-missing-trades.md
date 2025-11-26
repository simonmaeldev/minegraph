# Bug: Wandering Trader Parser Missing Trades

## Bug Description
The trading parser (`parse_trading` function in `src/core/parsers.py`) is missing several wandering trader trades when parsing the Wandering Trader HTML page. Specifically, the parser fails to extract trades for:
- **Emerald -> Packed Ice** (1 × Emerald -> 6 × Packed Ice)
- **Emerald -> Blue Ice** (6 × Emerald -> 6 × Blue Ice)
- **Emerald -> Nautilus Shell** (5 × Emerald -> Nautilus Shell)

These trades ARE present in the wandering trader HTML file (`ai_doc/downloaded_pages/mobs/wandering_trader.html`) but are not being extracted by the parser.

## Problem Statement
The `parse_trading` function currently only parses the main Trading wiki page (`ai_doc/downloaded_pages/trading.html`) which contains villager profession trades. However, wandering trader trades are located on a separate wandering trader mob page (`ai_doc/downloaded_pages/mobs/wandering_trader.html`) which is never processed by the trading parser. The wandering trader table has the SAME format as villager trading tables, but it's located in a different file that isn't being parsed for trading data.

## Solution Statement
Modify the extraction pipeline to parse wandering trader trades from the wandering trader mob page in addition to villager trades from the main trading page. The `parse_trading` function already has the correct logic to parse this table format - it just needs to be called on the wandering trader HTML content as well.

## Steps to Reproduce

1. Run the extraction to see current state:
   ```bash
   uv run python src/extract_transformations.py
   ```

2. Check the transformations CSV for wandering trader trades:
   ```bash
   grep -i "wandering" output/transformations.csv
   ```

3. Verify packed ice, blue ice, and nautilus shell trades are missing:
   ```bash
   grep "Packed Ice" output/transformations.csv
   grep "Blue Ice" output/transformations.csv
   grep "Nautilus Shell" output/transformations.csv
   ```

Expected: These items should appear as outputs in TRADING transformations with Wandering Trader as villager_type
Actual: These items are missing or only appear from other transformation types (not TRADING)

## Root Cause Analysis
The root cause is in `src/extract_transformations.py`. The trading transformations are extracted only from the main trading.html page:

```python
trading_path = os.path.join(download_dir, "trading.html")
with open(trading_path) as f:
    trading_transformations = parse_trading(f.read())
```

The wandering trader HTML file (`mobs/wandering_trader.html`) is downloaded but is only used for mob drops parsing, not for trading:

```python
# Mob drops parsing loops through mob pages
for mob in MOB_PAGES:
    mob_html_path = os.path.join(download_dir, f"mobs/{mob}.html")
    with open(mob_html_path) as f:
        html = f.read()
    # Only parse_mob_drops is called, not parse_trading
    transformations.extend(parse_mob_drops(html, mob.replace("_", " ").title()))
```

The wandering trader page contains a valid trading table with:
- Header: `<th colspan="9" data-description="Wandering Trader">`
- Columns: "Level", "Probability", "Villager wants", "Player receives", "Trades in stock"
- Rows with trades including Packed Ice, Blue Ice, Nautilus Shell

The `parse_trading` function is designed to handle this table structure but is never called on the wandering trader HTML.

## Relevant Files
Use these files to fix the bug:

- **`src/extract_transformations.py`**: Main orchestration script that loads HTML files and calls parsers
  - Contains the logic that reads trading.html and calls parse_trading()
  - Contains the mob drops loop that reads mobs/*.html files
  - NEEDS MODIFICATION: Add call to parse_trading() for wandering_trader.html

- **`src/core/parsers.py`**: Contains the parse_trading() function
  - parse_trading() function already handles the wandering trader table format correctly
  - Uses data-description attribute to extract villager_type
  - NO CHANGES NEEDED: Function logic is already correct

- **`src/core/download_data.py`**: Downloads wiki pages including wandering trader
  - MOB_PAGES list includes "wandering_trader"
  - Already downloads ai_doc/downloaded_pages/mobs/wandering_trader.html
  - NO CHANGES NEEDED: File is already being downloaded

- **`tests/test_parsers.py`**: Test suite for parser functions
  - NEEDS MODIFICATION: Add test case for wandering trader trades parsing
  - Should verify Packed Ice, Blue Ice, and Nautilus Shell trades are extracted
  - Should verify villager_type="Wandering Trader" in metadata

- **`ai_doc/downloaded_pages/mobs/wandering_trader.html`**: Source HTML with wandering trader trades
  - Contains the trading table with missing trades
  - Table structure matches villager trading tables
  - NO CHANGES NEEDED: Source data file

## Step by Step Tasks

### 1. Add wandering trader to trading extraction in extract_transformations.py
- Open `src/extract_transformations.py`
- Locate the section where trading transformations are extracted (~line 40-45)
- After parsing trading.html, add code to also parse wandering_trader.html:
  ```python
  # Parse wandering trader trades from the wandering trader mob page
  wandering_trader_path = os.path.join(download_dir, "mobs", "wandering_trader.html")
  with open(wandering_trader_path) as f:
      trading_transformations.extend(parse_trading(f.read()))
  ```
- This will call the existing parse_trading function on the wandering trader HTML

### 2. Add test case for wandering trader parsing
- Open `tests/test_parsers.py`
- Add a new test function `test_parse_wandering_trader_trades()`
- Create sample HTML representing the wandering trader trading table structure
- Include test rows for Packed Ice, Blue Ice, and Nautilus Shell
- Assert that parse_trading extracts all three trades correctly
- Assert that villager_type metadata is "Wandering Trader"
- Assert input/output items and quantities are correct

### 3. Run tests to verify the fix
- Execute pytest to ensure all tests pass
- Verify new test case passes
- Verify existing trading parser tests still pass

### 4. Run full extraction and validate output
- Run the full extraction pipeline
- Grep for wandering trader trades in output CSV
- Verify all three missing trades now appear
- Check transformation counts increased appropriately

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `uv run pytest tests/test_parsers.py::test_parse_wandering_trader_trades -v` - Verify new test passes
- `uv run pytest tests/test_parsers.py -v` - Run all parser tests
- `uv run python src/extract_transformations.py` - Run full extraction
- `grep -i "wandering.trader" output/transformations.csv | wc -l` - Count wandering trader trades (should be >0)
- `grep "Packed Ice" output/transformations.csv | grep "TRADING"` - Verify Packed Ice trade exists
- `grep "Blue Ice" output/transformations.csv | grep "TRADING"` - Verify Blue Ice trade exists
- `grep "Nautilus Shell" output/transformations.csv | grep "TRADING"` - Verify Nautilus Shell trade exists
- `uv run python src/validate_output.py` - Validate CSV format and check for duplicates

## Notes

### Trade Table Structure
The wandering trader table in `mobs/wandering_trader.html` uses the same structure as villager trading tables:
- Header row with `data-description="Wandering Trader"`
- Columns: Level, Probability (JE), Probability (BE), Slot, "Villager wants", "Player receives", "Trades in stock"
- Multiple trade categories: "Purchase" (player sells to trader), "Special", "Ordinary"

### Example Trades
From the HTML analysis:
- **Packed Ice**: 1 × Emerald -> 6 × Packed Ice (13% probability, Special category)
- **Blue Ice**: 6 × Emerald -> 6 × Blue Ice (13% probability, Special category)
- **Nautilus Shell**: 5 × Emerald -> 1 × Nautilus Shell (7% probability, Ordinary category)

### Parser Compatibility
The `parse_trading()` function already correctly handles:
- Extracting villager_type from data-description attribute
- Dynamic column detection per row (handles rowspan)
- Quantity parsing (e.g., "6 ×" prefix)
- Multiple items per cell (emerald quantities)
- Java Edition filtering

No changes to parse_trading() are needed - it will work correctly once called on the wandering trader HTML.

### Why This Was Missed
The wandering trader is treated as a mob (in MOB_PAGES list) rather than as a trading source. The original implementation assumed all trades would be on the main trading.html page, but wandering traders have their own dedicated mob page with a trading table section. This is a gap in the extraction logic, not a parser bug.

### Impact
This bug means players cannot discover transformation paths that involve wandering trader exclusive items like Packed Ice, Blue Ice (for ice-based builds), and Nautilus Shell (for conduits). These are important trades since wandering traders provide access to biome-specific items without traveling.
