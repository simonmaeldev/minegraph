# Bug: Transformation CSV Contains JSON Objects Instead of Item Names

## Bug Description
The transformations.csv file currently stores input_items and output_items as JSON arrays containing objects with both "name" and "url" fields (e.g., `[{"name": "Iron Ingot", "url": "https://minecraft.wiki/w/Iron_Ingot"}]`). However, the expected format should only contain the item names as a simple JSON array (e.g., `["Iron Ingot"]`). The URL information is redundant in the transformations CSV since it's already stored in the items.csv file.

**Current Format:**
```csv
crafting,"[{""name"": ""Iron Ingot"", ""url"": ""https://minecraft.wiki/w/Iron_Ingot""}]","[{""name"": ""Block of Iron"", ""url"": ""https://minecraft.wiki/w/Block_of_Iron""}]","{}"
```

**Expected Format:**
```csv
crafting,"[""Iron Ingot""]","[""Block of Iron""]","{}"
```

## Problem Statement
The `export_transformations_csv` function in `src/extract_transformations.py` (lines 168-177) serializes Item objects to JSON as dictionaries containing both name and url fields, when only the name field is needed. This creates unnecessarily verbose CSV output and couples the transformation data to the item URL information.

## Solution Statement
Modify the `export_transformations_csv` function to serialize only the item names (as strings) instead of the full Item objects (as dictionaries with name and url). This will simplify the CSV format and make it more maintainable, as the relationship between item names and URLs is already captured in items.csv.

## Steps to Reproduce
1. Run the extraction script: `python -m src.extract_transformations`
2. Open the generated file: `output/transformations.csv`
3. Observe that input_items and output_items columns contain JSON arrays with objects like `[{"name": "...", "url": "..."}]`
4. Expected: JSON arrays with just strings like `["..."]`

## Root Cause Analysis
In `src/extract_transformations.py`, the `export_transformations_csv` function (lines 146-189) explicitly creates dictionaries with both "name" and "url" fields when converting Item objects to JSON:

```python
# Lines 168-171
inputs_json = json.dumps([
    {"name": item.name, "url": item.url}
    for item in transformation.inputs
])

# Lines 173-177
outputs_json = json.dumps([
    {"name": item.name, "url": item.url}
    for item in transformation.outputs
])
```

This format was likely chosen to preserve all information, but it creates redundancy since:
1. The items.csv file already maintains the name-to-url mapping
2. Transformations should reference items by name only
3. The verbose JSON objects make the CSV harder to read and parse

## Relevant Files
Use these files to fix the bug:

- **src/extract_transformations.py** (lines 146-189)
  - Contains the `export_transformations_csv` function that needs to be modified
  - Lines 168-177 need to be changed to export only item names instead of full dictionaries

- **output/transformations.csv**
  - The generated output file that will have the corrected format after the fix
  - Will need to be regenerated after the code fix

### New Files
No new files are needed for this bug fix.

## Step by Step Tasks

### 1. Update the export_transformations_csv function
- Modify lines 168-171 in `src/extract_transformations.py` to serialize only item names:
  - Change from: `{"name": item.name, "url": item.url}` dictionary format
  - Change to: `item.name` string format
- Modify lines 173-177 similarly for outputs

### 2. Regenerate the transformations.csv file
- Run the extraction script to regenerate the CSV with the corrected format
- Command: `python -m src.extract_transformations`
- This will overwrite the existing transformations.csv with the correct format

### 3. Validate the fix
- Verify the transformations.csv format is correct by inspecting the first few lines
- Ensure input_items and output_items columns contain simple JSON string arrays
- Confirm no functionality is broken

### 4. Run the validation commands
- Execute all validation commands to ensure zero regressions
- Verify tests pass with the new format

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `python -m src.extract_transformations` - Regenerate transformations.csv with the corrected format
- `head -5 output/transformations.csv` - Verify the first few lines show item names only (not JSON objects)
- `python -m pytest tests/ -v` - Run all tests to ensure zero regressions
- `python -m src.validate_output` - Run output validation if such a script exists

## Notes
- This is a minimal, surgical fix that changes only the CSV export format
- The Item data model itself (src/core/data_models.py) does not need to be changed
- The items.csv file already contains the name-to-url mapping, so no information is lost
- The change makes transformations.csv more readable and aligns with the principle of normalization (item names reference the items table)
- After this fix, transformations can be joined with items using the item names as keys
