"""
Tests for technical item compression script.

These tests verify that the compression logic correctly replaces item names,
performs deduplication, and handles edge cases.
"""

import csv
import json
import pytest
from pathlib import Path
from typing import Dict, List

from src.compress_technical import (
    replace_item_name,
    compress_transformation_row,
    get_transformation_signature,
    compress_csv,
    CompressionStatistics,
    validate_compression,
)


class TestReplaceItemName:
    """Tests for replace_item_name() function."""

    def test_replace_mapped_item(self):
        """Test that mapped items are replaced with technical names."""
        mapping = {"Oak Planks": "Planks", "Spruce Planks": "Planks"}

        assert replace_item_name("Oak Planks", mapping) == "Planks"
        assert replace_item_name("Spruce Planks", mapping) == "Planks"

    def test_unmapped_item_unchanged(self):
        """Test that unmapped items pass through unchanged."""
        mapping = {"Oak Planks": "Planks"}

        assert replace_item_name("Diamond", mapping) == "Diamond"
        assert replace_item_name("Stick", mapping) == "Stick"

    def test_empty_string(self):
        """Test that empty strings are handled correctly."""
        mapping = {"Oak Planks": "Planks"}

        assert replace_item_name("", mapping) == ""

    def test_none_value(self):
        """Test that None values are handled correctly."""
        mapping = {"Oak Planks": "Planks"}

        # Empty string should be returned for None (or None itself)
        result = replace_item_name(None, mapping)
        assert result is None or result == ""


class TestCompressTransformationRow:
    """Tests for compress_transformation_row() function."""

    def test_compress_single_input(self):
        """Test compression with a single input item."""
        row = {
            "transformation_type": "crafting",
            "input_items": '["Oak Planks"]',
            "output_items": '["Stick"]',
            "metadata": "{}",
        }
        mapping = {"Oak Planks": "Planks"}

        result = compress_transformation_row(row, mapping)

        assert json.loads(result["input_items"]) == ["Planks"]
        assert json.loads(result["output_items"]) == ["Stick"]
        assert result["transformation_type"] == "crafting"

    def test_compress_multiple_inputs(self):
        """Test compression with multiple input items."""
        row = {
            "transformation_type": "crafting",
            "input_items": '["Oak Planks", "Spruce Planks", "Stick"]',
            "output_items": '["Wooden Pickaxe"]',
            "metadata": "{}",
        }
        mapping = {"Oak Planks": "Planks", "Spruce Planks": "Planks"}

        result = compress_transformation_row(row, mapping)

        inputs = json.loads(result["input_items"])
        assert "Planks" in inputs
        assert "Stick" in inputs

    def test_unmapped_items_unchanged(self):
        """Test that unmapped items pass through unchanged."""
        row = {
            "transformation_type": "crafting",
            "input_items": '["Diamond", "Stick"]',
            "output_items": '["Diamond Pickaxe"]',
            "metadata": "{}",
        }
        mapping = {"Oak Planks": "Planks"}

        result = compress_transformation_row(row, mapping)

        assert json.loads(result["input_items"]) == ["Diamond", "Stick"]
        assert json.loads(result["output_items"]) == ["Diamond Pickaxe"]

    def test_metadata_unchanged(self):
        """Test that metadata field is not modified."""
        row = {
            "transformation_type": "crafting",
            "input_items": '["Oak Planks"]',
            "output_items": '["Stick"]',
            "metadata": '{"count": 4}',
        }
        mapping = {"Oak Planks": "Planks"}

        result = compress_transformation_row(row, mapping)

        assert result["metadata"] == '{"count": 4}'

    def test_malformed_json_handled(self):
        """Test that malformed JSON is handled gracefully."""
        row = {
            "transformation_type": "crafting",
            "input_items": "not valid json",
            "output_items": '["Stick"]',
            "metadata": "{}",
        }
        mapping = {"Oak Planks": "Planks"}

        # Should not raise an exception
        result = compress_transformation_row(row, mapping)

        # Malformed field should remain unchanged
        assert result["input_items"] == "not valid json"

    def test_duplicate_items_removed_in_inputs(self):
        """Test that duplicate items in input_items are removed after compression."""
        row = {
            "transformation_type": "stonecutter",
            "input_items": '["Cut Copper", "Cut Copper", "Cut Copper", "Cut Copper", "Cut Copper", "Cut Copper", "Cut Copper", "Cut Copper"]',
            "output_items": '["Cut Copper Stairs"]',
            "metadata": "{}",
        }
        mapping = {}  # No mapping, so items stay the same

        result = compress_transformation_row(row, mapping)

        inputs = json.loads(result["input_items"])
        assert inputs == ["Cut Copper"], f"Expected ['Cut Copper'], got {inputs}"
        assert len(inputs) == 1

    def test_duplicate_items_removed_in_outputs(self):
        """Test that duplicate items in output_items are removed after compression."""
        row = {
            "transformation_type": "crafting",
            "input_items": '["A", "B"]',
            "output_items": '["Result", "Result", "Result"]',
            "metadata": "{}",
        }
        mapping = {}

        result = compress_transformation_row(row, mapping)

        outputs = json.loads(result["output_items"])
        assert outputs == ["Result"]
        assert len(outputs) == 1

    def test_duplicates_removed_after_mapping(self):
        """Test that duplicates created by mapping compression are removed."""
        row = {
            "transformation_type": "crafting",
            "input_items": '["Oak Planks", "Spruce Planks", "Birch Planks"]',
            "output_items": '["Stick"]',
            "metadata": "{}",
        }
        # All different wood types map to the same technical name
        mapping = {
            "Oak Planks": "Planks",
            "Spruce Planks": "Planks",
            "Birch Planks": "Planks",
        }

        result = compress_transformation_row(row, mapping)

        inputs = json.loads(result["input_items"])
        assert inputs == ["Planks"], f"Expected ['Planks'], got {inputs}"
        assert len(inputs) == 1

    def test_first_occurrence_preserved(self):
        """Test that the first occurrence of a duplicate is preserved."""
        row = {
            "transformation_type": "crafting",
            "input_items": '["A", "B", "A", "C"]',
            "output_items": '["X"]',
            "metadata": "{}",
        }
        mapping = {}

        result = compress_transformation_row(row, mapping)

        inputs = json.loads(result["input_items"])
        assert inputs == ["A", "B", "C"]
        # Verify A appears in position 0 (first occurrence preserved)
        assert inputs.index("A") == 0

    def test_no_duplicates_unchanged(self):
        """Test that rows with no duplicates remain unchanged."""
        row = {
            "transformation_type": "crafting",
            "input_items": '["A", "B", "C"]',
            "output_items": '["X", "Y"]',
            "metadata": "{}",
        }
        mapping = {}

        result = compress_transformation_row(row, mapping)

        assert json.loads(result["input_items"]) == ["A", "B", "C"]
        assert json.loads(result["output_items"]) == ["X", "Y"]


class TestGetTransformationSignature:
    """Tests for get_transformation_signature() function."""

    def test_identical_rows_same_signature(self):
        """Test that identical rows produce the same signature."""
        row1 = {
            "transformation_type": "crafting",
            "input_items": '["A", "B"]',
            "output_items": '["C"]',
            "metadata": "{}",
        }
        row2 = {
            "transformation_type": "crafting",
            "input_items": '["A", "B"]',
            "output_items": '["C"]',
            "metadata": "{}",
        }

        sig1 = get_transformation_signature(row1)
        sig2 = get_transformation_signature(row2)

        assert sig1 == sig2

    def test_different_order_same_signature(self):
        """Test that different input order produces the same signature."""
        row1 = {
            "transformation_type": "crafting",
            "input_items": '["A", "B"]',
            "output_items": '["C"]',
            "metadata": "{}",
        }
        row2 = {
            "transformation_type": "crafting",
            "input_items": '["B", "A"]',
            "output_items": '["C"]',
            "metadata": "{}",
        }

        sig1 = get_transformation_signature(row1)
        sig2 = get_transformation_signature(row2)

        assert sig1 == sig2, "Input order should not affect signature"

    def test_different_type_different_signature(self):
        """Test that different transformation types produce different signatures."""
        row1 = {
            "transformation_type": "crafting",
            "input_items": '["A"]',
            "output_items": '["C"]',
            "metadata": "{}",
        }
        row2 = {
            "transformation_type": "smelting",
            "input_items": '["A"]',
            "output_items": '["C"]',
            "metadata": "{}",
        }

        sig1 = get_transformation_signature(row1)
        sig2 = get_transformation_signature(row2)

        assert sig1 != sig2

    def test_different_outputs_different_signature(self):
        """Test that different outputs produce different signatures."""
        row1 = {
            "transformation_type": "crafting",
            "input_items": '["A"]',
            "output_items": '["C"]',
            "metadata": "{}",
        }
        row2 = {
            "transformation_type": "crafting",
            "input_items": '["A"]',
            "output_items": '["D"]',
            "metadata": "{}",
        }

        sig1 = get_transformation_signature(row1)
        sig2 = get_transformation_signature(row2)

        assert sig1 != sig2

    def test_different_metadata_different_signature(self):
        """Test that different metadata produces different signatures."""
        row1 = {
            "transformation_type": "crafting",
            "input_items": '["A"]',
            "output_items": '["C"]',
            "metadata": '{"count": 1}',
        }
        row2 = {
            "transformation_type": "crafting",
            "input_items": '["A"]',
            "output_items": '["C"]',
            "metadata": '{"count": 4}',
        }

        sig1 = get_transformation_signature(row1)
        sig2 = get_transformation_signature(row2)

        assert sig1 != sig2


class TestCompressionStatistics:
    """Tests for CompressionStatistics class."""

    def test_statistics_initialization(self):
        """Test that statistics object initializes correctly."""
        stats = CompressionStatistics()

        assert stats.transformations_processed == 0
        assert stats.transformations_written == 0
        assert stats.duplicates_removed == 0
        assert len(stats.exact_items) == 0
        assert len(stats.technical_items) == 0
        assert len(stats.unmapped_items) == 0

    def test_add_transformation_tracking(self):
        """Test that add_transformation correctly tracks items."""
        stats = CompressionStatistics()
        mapping = {"Oak Planks": "Planks"}

        row = {
            "transformation_type": "crafting",
            "input_items": '["Oak Planks", "Diamond"]',
            "output_items": '["Item"]',
            "metadata": "{}",
        }

        stats.add_transformation(row, mapping)

        assert stats.transformations_processed == 1
        assert "Oak Planks" in stats.exact_items
        assert "Diamond" in stats.exact_items
        assert "Planks" in stats.technical_items
        assert "Diamond" in stats.technical_items
        assert "Diamond" in stats.unmapped_items

    def test_duplicate_calculation(self):
        """Test that duplicate count is calculated correctly."""
        stats = CompressionStatistics()
        stats.transformations_processed = 100
        stats.transformations_written = 75

        stats.calculate_duplicates()

        assert stats.duplicates_removed == 25


class TestCompressCsv:
    """Tests for compress_csv() function."""

    def create_test_csv(self, tmp_path: Path, rows: List[Dict[str, str]]) -> Path:
        """Helper to create a test CSV file."""
        csv_path = tmp_path / "test_input.csv"

        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            fieldnames = ["transformation_type", "input_items", "output_items", "metadata"]
            writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
            writer.writeheader()
            writer.writerows(rows)

        return csv_path

    def test_compress_simple_csv(self, tmp_path):
        """Test basic CSV compression."""
        rows = [
            {
                "transformation_type": "crafting",
                "input_items": '["Oak Planks"]',
                "output_items": '["Stick"]',
                "metadata": "{}",
            },
            {
                "transformation_type": "crafting",
                "input_items": '["Diamond"]',
                "output_items": '["Diamond Block"]',
                "metadata": "{}",
            },
        ]

        input_path = self.create_test_csv(tmp_path, rows)
        output_path = tmp_path / "output.csv"
        mapping = {"Oak Planks": "Planks"}

        stats = compress_csv(input_path, output_path, mapping)

        # Verify file was created
        assert output_path.exists()

        # Verify statistics
        assert stats.transformations_processed == 2
        assert stats.transformations_written == 2

        # Verify content
        with open(output_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            result_rows = list(reader)

        assert len(result_rows) == 2
        assert json.loads(result_rows[0]["input_items"]) == ["Planks"]

    def test_deduplication(self, tmp_path):
        """Test that duplicate transformations are removed."""
        rows = [
            {
                "transformation_type": "crafting",
                "input_items": '["Oak Planks", "Stick"]',
                "output_items": '["Wooden Pickaxe"]',
                "metadata": "{}",
            },
            {
                "transformation_type": "crafting",
                "input_items": '["Spruce Planks", "Stick"]',
                "output_items": '["Wooden Pickaxe"]',
                "metadata": "{}",
            },
        ]

        input_path = self.create_test_csv(tmp_path, rows)
        output_path = tmp_path / "output.csv"
        mapping = {"Oak Planks": "Planks", "Spruce Planks": "Planks"}

        stats = compress_csv(input_path, output_path, mapping)

        # Both should compress to the same transformation
        assert stats.transformations_processed == 2
        assert stats.transformations_written == 1
        assert stats.duplicates_removed == 1

    def test_order_independent_deduplication(self, tmp_path):
        """Test that input order doesn't affect deduplication."""
        rows = [
            {
                "transformation_type": "crafting",
                "input_items": '["A", "B"]',
                "output_items": '["C"]',
                "metadata": "{}",
            },
            {
                "transformation_type": "crafting",
                "input_items": '["B", "A"]',
                "output_items": '["C"]',
                "metadata": "{}",
            },
        ]

        input_path = self.create_test_csv(tmp_path, rows)
        output_path = tmp_path / "output.csv"
        mapping = {}

        stats = compress_csv(input_path, output_path, mapping)

        # Should be deduplicated despite different order
        assert stats.transformations_processed == 2
        assert stats.transformations_written == 1

    def test_empty_csv(self, tmp_path):
        """Test compression of an empty CSV (header only)."""
        rows = []

        input_path = self.create_test_csv(tmp_path, rows)
        output_path = tmp_path / "output.csv"
        mapping = {"Oak Planks": "Planks"}

        stats = compress_csv(input_path, output_path, mapping)

        assert stats.transformations_processed == 0
        assert stats.transformations_written == 0

        # Verify output file exists with header
        assert output_path.exists()
        with open(output_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            result_rows = list(reader)
        assert len(result_rows) == 0

    def test_no_duplicates(self, tmp_path):
        """Test CSV with no duplicates keeps all transformations."""
        rows = [
            {
                "transformation_type": "crafting",
                "input_items": '["A"]',
                "output_items": '["X"]',
                "metadata": "{}",
            },
            {
                "transformation_type": "crafting",
                "input_items": '["B"]',
                "output_items": '["Y"]',
                "metadata": "{}",
            },
        ]

        input_path = self.create_test_csv(tmp_path, rows)
        output_path = tmp_path / "output.csv"
        mapping = {}

        stats = compress_csv(input_path, output_path, mapping)

        assert stats.transformations_processed == 2
        assert stats.transformations_written == 2
        assert stats.duplicates_removed == 0

    def test_all_duplicates(self, tmp_path):
        """Test CSV where all rows become duplicates after compression."""
        rows = [
            {
                "transformation_type": "crafting",
                "input_items": '["Oak Planks"]',
                "output_items": '["X"]',
                "metadata": "{}",
            },
            {
                "transformation_type": "crafting",
                "input_items": '["Spruce Planks"]',
                "output_items": '["X"]',
                "metadata": "{}",
            },
            {
                "transformation_type": "crafting",
                "input_items": '["Birch Planks"]',
                "output_items": '["X"]',
                "metadata": "{}",
            },
        ]

        input_path = self.create_test_csv(tmp_path, rows)
        output_path = tmp_path / "output.csv"
        mapping = {
            "Oak Planks": "Planks",
            "Spruce Planks": "Planks",
            "Birch Planks": "Planks",
        }

        stats = compress_csv(input_path, output_path, mapping)

        # Should keep only the first one
        assert stats.transformations_processed == 3
        assert stats.transformations_written == 1
        assert stats.duplicates_removed == 2


class TestValidateCompression:
    """Tests for validate_compression() function."""

    def create_test_csv(self, path: Path, rows: List[Dict[str, str]]):
        """Helper to create a test CSV file."""
        with open(path, "w", encoding="utf-8", newline="") as f:
            fieldnames = ["transformation_type", "input_items", "output_items", "metadata"]
            writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
            writer.writeheader()
            writer.writerows(rows)

    def test_validate_successful(self, tmp_path):
        """Test validation with valid compression output."""
        input_rows = [
            {
                "transformation_type": "crafting",
                "input_items": '["A"]',
                "output_items": '["X"]',
                "metadata": "{}",
            },
            {
                "transformation_type": "crafting",
                "input_items": '["B"]',
                "output_items": '["Y"]',
                "metadata": "{}",
            },
        ]

        output_rows = [
            {
                "transformation_type": "crafting",
                "input_items": '["A"]',
                "output_items": '["X"]',
                "metadata": "{}",
            },
        ]

        input_path = tmp_path / "input.csv"
        output_path = tmp_path / "output.csv"

        self.create_test_csv(input_path, input_rows)
        self.create_test_csv(output_path, output_rows)

        # Should not raise
        result = validate_compression(input_path, output_path)
        assert result is True

    def test_validate_missing_output(self, tmp_path):
        """Test validation fails if output file doesn't exist."""
        input_path = tmp_path / "input.csv"
        output_path = tmp_path / "nonexistent.csv"

        self.create_test_csv(input_path, [])

        with pytest.raises(ValueError, match="Output file does not exist"):
            validate_compression(input_path, output_path)

    def test_validate_duplicate_in_output(self, tmp_path):
        """Test validation fails if output contains duplicates."""
        input_rows = [
            {
                "transformation_type": "crafting",
                "input_items": '["A"]',
                "output_items": '["X"]',
                "metadata": "{}",
            },
            {
                "transformation_type": "crafting",
                "input_items": '["B"]',
                "output_items": '["Y"]',
                "metadata": "{}",
            },
        ]

        output_rows = [
            {
                "transformation_type": "crafting",
                "input_items": '["A"]',
                "output_items": '["X"]',
                "metadata": "{}",
            },
            {
                "transformation_type": "crafting",
                "input_items": '["A"]',
                "output_items": '["X"]',
                "metadata": "{}",
            },
        ]

        input_path = tmp_path / "input.csv"
        output_path = tmp_path / "output.csv"

        self.create_test_csv(input_path, input_rows)
        self.create_test_csv(output_path, output_rows)

        with pytest.raises(ValueError, match="duplicate signatures"):
            validate_compression(input_path, output_path)

    def test_validate_invalid_json(self, tmp_path):
        """Test validation fails if output contains invalid JSON."""
        input_rows = [
            {
                "transformation_type": "crafting",
                "input_items": '["A"]',
                "output_items": '["X"]',
                "metadata": "{}",
            },
        ]

        output_rows = [
            {
                "transformation_type": "crafting",
                "input_items": "not valid json",
                "output_items": '["X"]',
                "metadata": "{}",
            },
        ]

        input_path = tmp_path / "input.csv"
        output_path = tmp_path / "output.csv"

        self.create_test_csv(input_path, input_rows)
        self.create_test_csv(output_path, output_rows)

        with pytest.raises(ValueError, match="Invalid JSON"):
            validate_compression(input_path, output_path)


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_special_characters_in_names(self):
        """Test that items with special characters are handled correctly."""
        mapping = {"Item's Name": "Technical"}

        result = replace_item_name("Item's Name", mapping)
        assert result == "Technical"

    def test_unicode_characters(self):
        """Test that unicode characters in item names are handled correctly."""
        mapping = {"Café Mocha": "Coffee"}

        result = replace_item_name("Café Mocha", mapping)
        assert result == "Coffee"

    def test_very_long_item_names(self):
        """Test that very long item names are handled correctly."""
        long_name = "A" * 1000
        mapping = {long_name: "Short"}

        result = replace_item_name(long_name, mapping)
        assert result == "Short"
