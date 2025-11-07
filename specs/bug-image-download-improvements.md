# Bug: Image Download Script Missing Failure Recap and Skip Logic

## Bug Description
The image download script (`src/download_item_images.py`) has two issues:
1. **No failure recap**: When images fail to download (currently 2 out of 1297 items fail), the script doesn't report which specific items failed at the end. Users only see error logs during execution and a summary count, but cannot easily identify which items need manual attention.
2. **Inefficient skip logic**: The script checks if an image already exists only after processing begins (at line 271), rather than skipping it immediately at the start. This means unnecessary logging and processing happens for already-cached items.

## Problem Statement
Users cannot easily identify which specific items failed to download from the summary report, and the script performs unnecessary work for already-cached images, making subsequent runs slower and more verbose than necessary.

## Solution Statement
1. Maintain a list of failed item names throughout the download process
2. Display the failed item names in the final summary recap (not just the count)
3. Move the "already exists" check to the beginning of the loop to skip cached items immediately, reducing unnecessary processing

## Steps to Reproduce
1. Run the image download script: `uv run python src/download_item_images.py --input output/items.csv --output-dir images/ --verbose`
2. Observe that 2 items fail to download ("Chain" and "Head")
3. Look at the final summary - it shows "Failed: 2" but doesn't list which items failed
4. Run the script again - observe that all 1295 cached items are still logged as "Processing" before being skipped

## Root Cause Analysis
**Issue 1 - No failure recap:**
- The script tracks `failed_items` as a counter (line 257) but doesn't store the actual item names that failed
- The summary (lines 307-314) only prints the count, not the list of failed items
- Users have to scroll through verbose logs to find error messages

**Issue 2 - Inefficient skip logic:**
- The "already exists" check happens after logging "Processing: {item_name}" (line 268)
- The check is at line 271, after the item has already been logged and processed
- This causes unnecessary log output and makes it harder to identify what's actually being downloaded

## Relevant Files
Use these files to fix the bug:

- **src/download_item_images.py** (lines 253-314) - Main script that needs modification to:
  - Change `failed_items` from an integer counter to a list that stores failed item names
  - Add failed item names to the list when downloads fail (lines 287-288, 299-300)
  - Display the failed items list in the summary section (after line 313)
  - Move the "already exists" check earlier (before line 268) to skip cached items immediately

- **tests/test_download_item_images.py** - Test suite that should be updated to verify:
  - Failed items list is properly populated
  - Summary includes failed item names
  - Skip logic works correctly for cached images

## Step by Step Tasks

### 1. Update Failed Items Tracking
- Change `failed_items` from an integer counter to a list: `failed_items = []`
- When image URL extraction fails (around line 287-288), append the item name to the list: `failed_items.append(item_name)`
- When image download fails (around line 299-300), append the item name to the list: `failed_items.append(item_name)`
- Update the successful_downloads, cached_items counters to remain as integers

### 2. Improve Skip Logic for Cached Images
- Move the "already exists" check to immediately after the "Processing" log message
- Check if `output_path.exists() and not args.force_redownload` right at the start (before line 271)
- Skip to next iteration immediately with `continue` to avoid unnecessary processing
- This ensures cached items are identified and skipped with minimal logging

### 3. Update Summary Report
- Modify the summary section (lines 307-314) to include failed item names
- Add a new section after the statistics that lists each failed item name on a separate line
- Only show the failed items section if there are failures (i.e., `if failed_items:`)
- Format the failed items list clearly, e.g., "Failed items: - Chain - Head"
- Update the count display to use `len(failed_items)` instead of the old counter

### 4. Update Tests
- Add a test in `tests/test_download_item_images.py` to verify failed items are tracked in a list
- Add a test to verify the summary includes failed item names
- Add a test to verify cached images are skipped early in the process
- Ensure all existing tests still pass with the changes

### 5. Run Validation Commands
- Run the full test suite to ensure no regressions
- Run the download script with verbose mode to verify the improvements
- Verify that failed items are now listed in the summary
- Verify that cached items are skipped efficiently

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

```bash
# Run all tests to ensure no regressions
uv run pytest tests/ -v

# Run the image download script to see the improved output
uv run python src/download_item_images.py --input output/items.csv --output-dir images/ --verbose

# Run without verbose to see clean output with failed items recap
uv run python src/download_item_images.py --input output/items.csv --output-dir images/

# Test with a small limit to verify behavior
uv run python src/download_item_images.py --input output/items.csv --output-dir images/ --limit 10

# Run tests specifically for download_item_images
uv run pytest tests/test_download_item_images.py -v
```

## Notes

### Current Failures
Based on running the script, the two items that currently fail are:
- **Chain** - No image URL found on wiki page
- **Head** - No image URL found on wiki page

These items likely have wiki pages with non-standard layouts or missing infoboxes.

### Expected Output After Fix
The summary should look like this:
```
============================================================
DOWNLOAD SUMMARY
============================================================
Total items:           1297
Successfully downloaded: 0
Already cached:        1295
Failed:                2

Failed items:
  - Chain
  - Head
============================================================
```

### Performance Impact
Moving the "already exists" check earlier will:
- Reduce log verbosity by ~1295 lines when all images are cached
- Make subsequent runs faster by skipping unnecessary processing
- Make it easier to identify what's actually being downloaded vs. skipped

### Backward Compatibility
These changes are fully backward compatible:
- No changes to command-line arguments
- No changes to function signatures
- No changes to output file formats
- Only improvements to logging and summary reporting
