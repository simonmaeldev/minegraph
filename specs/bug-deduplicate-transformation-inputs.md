# Bug: Transformation Input Items Should Be Deduplicated as Sets

## Bug Description
Currently, transformation input items are stored as lists, which means duplicate items (e.g., multiple sticks in a crafting recipe) are stored multiple times. This results in input_items containing redundant data like `["Stick", "Stick", "Stick", "Stick", ...]` instead of just unique items `["Stick"]`.

**Expected Behavior**: Input items should be stored as unique sets (deduplicated) to represent the types of items needed, not the quantity.

**Actual Behavior**: Input items are stored as lists with duplicates. For example, a recipe requiring 8 sticks stores 8 separate "Stick" items in the list.

## Problem Statement
The `Transformation` data model stores `inputs` and `outputs` as `List[Item]` in data_models.py:44-45, which allows duplicate items. When parsers extract items from recipes (e.g., crafting recipes with multiple identical items like sticks), they append all instances to the list, resulting in duplicate entries. This creates unnecessary data redundancy and doesn't align with the expected graph representation where we only care about item types, not quantities.

## Solution Statement
Convert the `inputs` and `outputs` fields in the `Transformation` data model from `List[Item]` to use lists initialized from sets to ensure deduplication. The Item class already has proper `__hash__` and `__eq__` methods based on name, making it suitable for set operations. We'll update the `__post_init__` method to automatically deduplicate inputs and outputs while maintaining the list type for JSON serialization compatibility.

## Steps to Reproduce
1. Run the extraction script: `cd /home/apprentyr/projects/minegraph && python -m src.extract_transformations`
2. Open the output file: `output/transformations.csv`
3. Look at rows 9-20 (crafting recipes for paintings)
4. Observe that `input_items` contains duplicate "Stick" entries (8 identical sticks)
5. Expected: `input_items` should contain only 1 unique "Stick" item and 1 unique "Wool" item variant

## Root Cause Analysis
The root cause is in the `Transformation` data model (src/core/data_models.py:40-54):

1. **Data Model Definition**: The `inputs` and `outputs` fields are defined as `List[Item]` which allows duplicates
2. **Parser Behavior**: All parser functions (parse_crafting, parse_smelting, etc.) in src/core/parsers.py extract items and append them to lists without deduplication
3. **Example**: In parse_crafting (parsers.py:116-190), when processing crafting table slots, each slot's items are appended to `input_items` list, resulting in duplicates for recipes requiring multiple of the same item

The Item class already implements proper hashing and equality (data_models.py:29-37), making items suitable for set operations, but this isn't being utilized.

## Relevant Files
Use these files to fix the bug:

### Existing Files
- **src/core/data_models.py** (lines 40-54) - Contains the `Transformation` class definition that needs modification. The `__post_init__` method should be updated to deduplicate inputs and outputs.

- **src/extract_transformations.py** (lines 103-119, 166-177) - The `extract_unique_items` function already demonstrates set usage for Items. The export function serializes inputs/outputs to JSON, which requires lists, so we need to maintain list type after deduplication.

- **tests/test_data_models.py** (lines 85-156) - Contains tests for the Transformation class. Tests currently expect lists with duplicates (e.g., lines 95, 111 use `[iron] * 9` and `[coal] * 15`). These tests need to be updated to expect deduplicated inputs.

- **src/core/parsers.py** (entire file) - Contains all parser functions. While parsers don't need modification (they can continue building lists), we should verify the deduplication works correctly across all parser types.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Update Transformation Data Model to Deduplicate Inputs/Outputs
- Modify `src/core/data_models.py` in the `Transformation` class `__post_init__` method
- Add logic to deduplicate `self.inputs` by converting to set and back to list: `self.inputs = list(set(self.inputs))`
- Add logic to deduplicate `self.outputs` by converting to set and back to list: `self.outputs = list(set(self.outputs))`
- Maintain list type for JSON serialization compatibility
- Keep existing validation checks for empty inputs/outputs

### Step 2: Update Test Cases to Expect Deduplicated Data
- Update `tests/test_data_models.py::TestTransformation::test_transformation_creation`
  - Change assertion from `assert len(transformation.inputs) == 9` to `assert len(transformation.inputs) == 1`
  - Update test to verify deduplication: create transformation with `[iron] * 9`, verify only 1 unique item in inputs
- Update `tests/test_data_models.py::TestTransformation::test_transformation_with_metadata`
  - Change assertion for inputs from 15 to 1
  - Verify deduplication works with metadata
- Add new test case `test_transformation_deduplicates_inputs` to explicitly test deduplication behavior
  - Create transformation with duplicate items in inputs
  - Verify only unique items are stored
- Add new test case `test_transformation_deduplicates_outputs` to test output deduplication
  - Create transformation with duplicate items in outputs
  - Verify only unique items are stored

### Step 3: Run All Tests to Validate Changes
- Run pytest on data_models tests: `cd /home/apprentyr/projects/minegraph && python -m pytest tests/test_data_models.py -v`
- Run pytest on parser tests: `cd /home/apprentyr/projects/minegraph && python -m pytest tests/test_parsers.py -v`
- Verify all tests pass with zero failures

### Step 4: Re-extract Transformations and Validate Output
- Run the extraction script: `cd /home/apprentyr/projects/minegraph && python -m src.extract_transformations`
- Read the output CSV file `output/transformations.csv`
- Verify that transformation inputs are now deduplicated (e.g., stick recipes should have 1 stick entry, not 8)
- Spot-check several rows to ensure deduplication is working correctly

### Step 5: Run Validation Commands
- Execute all validation commands listed below to ensure zero regressions

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `cd /home/apprentyr/projects/minegraph && python -m pytest tests/ -v` - Run all tests to validate the bug is fixed with zero regressions
- `cd /home/apprentyr/projects/minegraph && python -m src.extract_transformations` - Re-extract transformations with deduplicated inputs
- `cd /home/apprentyr/projects/minegraph && python -m src.validate_output` - Validate the output data is correct (if validation script exists)

## Notes
- The Item class already has proper `__hash__` and `__eq__` implementations based on item name (data_models.py:29-37), which makes it safe to use in sets
- Deduplication happens in the `Transformation.__post_init__` method, so all parser functions continue to work without modification
- The change maintains list type for backward compatibility with JSON serialization in extract_transformations.py
- Set conversion order is non-deterministic in Python, but since Items are deduplicated by name and we don't care about quantity, order doesn't matter for the graph representation
- This change aligns with the project's goal of extracting transformation relationships between items, where we care about "which items" not "how many items"
