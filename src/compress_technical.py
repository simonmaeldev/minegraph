"""
Technical Item Compressor for Minecraft Transformations

This script compresses transformations.csv by replacing exact item names with
technical category names. This reduces graph complexity by grouping functionally
similar items (e.g., all wood planks, all tipped arrows) together.

The compression also performs deduplication to remove transformations that become
identical after compression. Input order is ignored during deduplication since
transformation inputs are conceptually sets, not ordered lists.

Example:
    # Compress with statistics
    python src/compress_technical.py --stats --verbose

    # Compress with custom paths
    python src/compress_technical.py --input my_trans.csv --output my_technical.csv

    # Validate compression output
    python src/compress_technical.py --validate
"""

import csv
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Set, Tuple, List, Optional
from collections import defaultdict

from src.technical_mappings import (
    TECHNICAL_MAPPINGS,
    generate_exact_to_technical,
    validate_mappings,
)

logger = logging.getLogger(__name__)


def replace_item_name(item_name: str, exact_to_technical: Dict[str, str]) -> str:
    """
    Replace an exact item name with its technical category name if mapped.

    Performs iterative replacement to handle transitive mappings. If the replacement
    target is itself a key in the mapping, it will be replaced as well, continuing
    until no more replacements occur or the safety limit is reached.

    Args:
        item_name: The exact item name to replace.
        exact_to_technical: Mapping from exact names to technical names.

    Returns:
        Technical name if mapped, otherwise the original exact name.

    Example:
        >>> mapping = {"Oak Planks": "Planks", "Planks": "Wood"}
        >>> replace_item_name("Oak Planks", mapping)
        'Wood'
        >>> replace_item_name("Diamond", mapping)
        'Diamond'
    """
    if not item_name:
        return item_name

    # Iteratively replace until no more replacements occur
    max_iterations = 10
    current_name = item_name

    for _ in range(max_iterations):
        replacement = exact_to_technical.get(current_name, current_name)
        # If no replacement occurred, we're done
        if replacement == current_name:
            return current_name
        current_name = replacement

    # Return the current name after max iterations (shouldn't happen with valid mappings)
    return current_name


def compress_transformation_row(
    row: Dict[str, str], exact_to_technical: Dict[str, str]
) -> Dict[str, str]:
    """
    Compress a transformation row by replacing exact item names with technical names.

    The transformation type and metadata remain unchanged. Only item names in the
    input_items and output_items JSON arrays are replaced.

    Args:
        row: A CSV row as a dictionary with keys: transformation_type, input_items,
             output_items, metadata.
        exact_to_technical: Mapping from exact names to technical names.

    Returns:
        The row with item names replaced by technical names.

    Example:
        >>> row = {
        ...     "transformation_type": "crafting",
        ...     "input_items": '["Oak Planks", "Stick"]',
        ...     "output_items": '["Wooden Pickaxe"]',
        ...     "metadata": "{}"
        ... }
        >>> mapping = {"Oak Planks": "Planks"}
        >>> result = compress_transformation_row(row, mapping)
        >>> result["input_items"]
        '["Planks", "Stick"]'
    """
    compressed_row = row.copy()

    # Process input_items
    try:
        input_items = json.loads(row["input_items"])
        compressed_input = [
            replace_item_name(item, exact_to_technical) for item in input_items
        ]
        # Remove duplicates while preserving order (keep first occurrence)
        deduped_input = list(dict.fromkeys(compressed_input))
        compressed_row["input_items"] = json.dumps(deduped_input)
    except (json.JSONDecodeError, KeyError) as e:
        logger.warning(f"Failed to parse input_items: {e}")

    # Process output_items
    try:
        output_items = json.loads(row["output_items"])
        compressed_output = [
            replace_item_name(item, exact_to_technical) for item in output_items
        ]
        # Remove duplicates while preserving order (keep first occurrence)
        deduped_output = list(dict.fromkeys(compressed_output))
        compressed_row["output_items"] = json.dumps(deduped_output)
    except (json.JSONDecodeError, KeyError) as e:
        logger.warning(f"Failed to parse output_items: {e}")

    return compressed_row


def get_transformation_signature(row: Dict[str, str]) -> Tuple:
    """
    Generate a unique signature for a transformation row for deduplication.

    The signature is order-independent for inputs and outputs. This means that
    [A, B] and [B, A] produce the same signature, which is correct because
    transformation inputs are conceptually sets, not ordered lists.

    Args:
        row: A CSV row dictionary with transformation_type, input_items,
             output_items, metadata.

    Returns:
        A hashable tuple representing the transformation signature.

    Example:
        >>> row1 = {
        ...     "transformation_type": "crafting",
        ...     "input_items": '["A", "B"]',
        ...     "output_items": '["C"]',
        ...     "metadata": "{}"
        ... }
        >>> row2 = {
        ...     "transformation_type": "crafting",
        ...     "input_items": '["B", "A"]',
        ...     "output_items": '["C"]',
        ...     "metadata": "{}"
        ... }
        >>> get_transformation_signature(row1) == get_transformation_signature(row2)
        True
    """
    transformation_type = row.get("transformation_type", "")

    # Parse and sort input items
    try:
        input_items = json.loads(row["input_items"])
        sorted_inputs = tuple(sorted(input_items))
    except (json.JSONDecodeError, KeyError):
        sorted_inputs = ()

    # Parse and sort output items
    try:
        output_items = json.loads(row["output_items"])
        sorted_outputs = tuple(sorted(output_items))
    except (json.JSONDecodeError, KeyError):
        sorted_outputs = ()

    # Parse and sort metadata items (if metadata is a dict)
    try:
        metadata = json.loads(row["metadata"])
        if isinstance(metadata, dict):
            sorted_metadata = tuple(sorted(metadata.items()))
        else:
            sorted_metadata = (str(metadata),)
    except (json.JSONDecodeError, KeyError):
        sorted_metadata = ()

    return (transformation_type, sorted_inputs, sorted_outputs, sorted_metadata)


class CompressionStatistics:
    """Statistics tracker for compression operations."""

    def __init__(self):
        self.transformations_processed = 0
        self.transformations_written = 0
        self.duplicates_removed = 0
        self.exact_items: Set[str] = set()
        self.technical_items: Set[str] = set()
        self.unmapped_items: Set[str] = set()

    def add_transformation(self, row: Dict[str, str], exact_to_technical: Dict[str, str]):
        """Track items from a transformation row."""
        self.transformations_processed += 1

        # Track items from input_items
        try:
            input_items = json.loads(row["input_items"])
            for item in input_items:
                self.exact_items.add(item)
                technical_name = replace_item_name(item, exact_to_technical)
                self.technical_items.add(technical_name)
                if technical_name == item and item not in exact_to_technical:
                    self.unmapped_items.add(item)
        except (json.JSONDecodeError, KeyError):
            pass

        # Track items from output_items
        try:
            output_items = json.loads(row["output_items"])
            for item in output_items:
                self.exact_items.add(item)
                technical_name = replace_item_name(item, exact_to_technical)
                self.technical_items.add(technical_name)
                if technical_name == item and item not in exact_to_technical:
                    self.unmapped_items.add(item)
        except (json.JSONDecodeError, KeyError):
            pass

    def add_written(self):
        """Increment count of transformations written."""
        self.transformations_written += 1

    def calculate_duplicates(self):
        """Calculate number of duplicates removed."""
        self.duplicates_removed = self.transformations_processed - self.transformations_written

    def print_statistics(self):
        """Print compression statistics."""
        self.calculate_duplicates()

        print("\n=== Compression Statistics ===")
        print(f"Transformations processed: {self.transformations_processed}")
        print(f"Transformations written: {self.transformations_written}")
        print(f"Duplicates removed: {self.duplicates_removed}")

        if self.transformations_processed > 0:
            dedup_ratio = (
                self.transformations_written / self.transformations_processed * 100
            )
            print(f"Deduplication ratio: {dedup_ratio:.1f}%")

        print(f"\nUnique exact items: {len(self.exact_items)}")
        print(f"Unique technical items: {len(self.technical_items)}")

        if len(self.exact_items) > 0:
            compression_ratio = len(self.technical_items) / len(self.exact_items) * 100
            print(f"Item compression ratio: {compression_ratio:.1f}%")

        if self.unmapped_items:
            print(f"\nUnmapped items ({len(self.unmapped_items)}):")
            for item in sorted(self.unmapped_items)[:20]:
                print(f"  - {item}")
            if len(self.unmapped_items) > 20:
                print(f"  ... and {len(self.unmapped_items) - 20} more")


def compress_csv(
    input_path: Path,
    output_path: Path,
    exact_to_technical: Dict[str, str],
    stats: Optional[CompressionStatistics] = None,
) -> CompressionStatistics:
    """
    Compress a transformations CSV file by replacing exact names with technical names.

    Performs deduplication to remove transformations that become identical after
    compression. Input order is ignored during deduplication.

    Args:
        input_path: Path to input transformations.csv file.
        output_path: Path to output technical_transformations.csv file.
        exact_to_technical: Mapping from exact names to technical names.
        stats: Optional statistics tracker. If None, a new one is created.

    Returns:
        CompressionStatistics object with compression metrics.

    Raises:
        FileNotFoundError: If input file doesn't exist.
        IOError: If there's an error reading or writing files.
    """
    if stats is None:
        stats = CompressionStatistics()

    seen_signatures: Set[Tuple] = set()

    logger.info(f"Reading transformations from {input_path}")

    with open(input_path, "r", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames

        if not fieldnames:
            raise ValueError("Input CSV has no header")

        # Open output file
        with open(output_path, "w", encoding="utf-8", newline="") as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
            writer.writeheader()

            for row in reader:
                # Track statistics
                if stats:
                    stats.add_transformation(row, exact_to_technical)

                # Compress item names
                compressed_row = compress_transformation_row(row, exact_to_technical)

                # Get signature for deduplication
                signature = get_transformation_signature(compressed_row)

                # Only write if not a duplicate
                if signature not in seen_signatures:
                    writer.writerow(compressed_row)
                    seen_signatures.add(signature)
                    if stats:
                        stats.add_written()

    logger.info(f"Wrote compressed transformations to {output_path}")

    # Calculate duplicates before returning
    if stats:
        stats.calculate_duplicates()

    logger.info(
        f"Processed {stats.transformations_processed} transformations, "
        f"wrote {stats.transformations_written} (removed {stats.duplicates_removed} duplicates)"
    )

    return stats


def validate_compression(input_path: Path, output_path: Path) -> bool:
    """
    Validate that compression was performed correctly.

    Checks:
    - Output file exists
    - Output has fewer or equal rows than input (due to deduplication)
    - All rows have valid JSON
    - No duplicate signatures exist in output

    Args:
        input_path: Path to original transformations.csv.
        output_path: Path to compressed technical_transformations.csv.

    Returns:
        True if validation passes.

    Raises:
        ValueError: If validation fails.
    """
    if not output_path.exists():
        raise ValueError(f"Output file does not exist: {output_path}")

    # Count rows in input and output
    with open(input_path, "r", encoding="utf-8") as f:
        input_rows = sum(1 for _ in csv.DictReader(f))

    with open(output_path, "r", encoding="utf-8") as f:
        output_rows = sum(1 for _ in csv.DictReader(f))

    if output_rows > input_rows:
        raise ValueError(
            f"Output has more rows ({output_rows}) than input ({input_rows})"
        )

    logger.info(f"Row count: {input_rows} → {output_rows} ({input_rows - output_rows} removed)")

    # Validate JSON and check for duplicates
    seen_signatures: Set[Tuple] = set()
    duplicate_count = 0

    with open(output_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=1):
            # Validate JSON
            try:
                json.loads(row["input_items"])
                json.loads(row["output_items"])
                json.loads(row["metadata"])
            except (json.JSONDecodeError, KeyError) as e:
                raise ValueError(f"Invalid JSON in row {i}: {e}")

            # Check for duplicates
            signature = get_transformation_signature(row)
            if signature in seen_signatures:
                duplicate_count += 1
                logger.warning(f"Duplicate signature found in output at row {i}")
            seen_signatures.add(signature)

    if duplicate_count > 0:
        raise ValueError(f"Found {duplicate_count} duplicate signatures in output")

    logger.info("✓ Validation passed: no duplicates, all JSON valid")
    return True


def main():
    """Main entry point for the compression script."""
    parser = argparse.ArgumentParser(
        description="Compress transformations by replacing exact item names with technical categories"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("output/transformations.csv"),
        help="Input transformations CSV file (default: output/transformations.csv)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output/technical_transformations.csv"),
        help="Output compressed CSV file (default: output/technical_transformations.csv)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )
    parser.add_argument(
        "--stats", "-s", action="store_true", help="Print compression statistics"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate compression output (requires existing output file)",
    )

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    try:
        # Validate technical mappings
        logger.info("Validating technical mappings...")
        validate_mappings()
        logger.info("✓ Technical mappings validated")

        # Generate exact to technical mapping
        exact_to_technical = generate_exact_to_technical()
        logger.info(
            f"Generated reverse mapping: {len(exact_to_technical)} exact items → "
            f"{len(TECHNICAL_MAPPINGS)} technical categories"
        )

        if args.validate:
            # Validate existing compression
            logger.info("Validating compression output...")
            validate_compression(args.input, args.output)
            print("✓ Validation successful")
        else:
            # Perform compression
            logger.info("Starting compression...")
            stats = CompressionStatistics()
            compress_csv(args.input, args.output, exact_to_technical, stats)

            # Print statistics if requested
            if args.stats:
                stats.print_statistics()

            print(f"\n✓ Compression complete: {args.output}")
            print(
                f"  Processed: {stats.transformations_processed}, "
                f"Written: {stats.transformations_written}, "
                f"Removed: {stats.duplicates_removed} duplicates"
            )

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=args.verbose)
        exit(1)


if __name__ == "__main__":
    main()
