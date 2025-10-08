"""Validation script for checking output data quality."""

import csv
import json
import logging
from collections import Counter
from typing import Dict, List, Set

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_items_csv(filepath: str) -> List[Dict[str, str]]:
    """Load items from CSV file."""
    items = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            items.append(row)
    return items


def load_transformations_csv(filepath: str) -> List[Dict[str, str]]:
    """Load transformations from CSV file."""
    transformations = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            transformations.append(row)
    return transformations


def validate_items(items: List[Dict[str, str]]) -> None:
    """Validate items data quality."""
    logger.info("\n=== Validating Items ===")

    # Check for duplicates
    item_names = [item["item_name"] for item in items]
    duplicate_counts = Counter(item_names)
    duplicates = {name: count for name, count in duplicate_counts.items() if count > 1}

    if duplicates:
        logger.warning(f"Found {len(duplicates)} duplicate item names:")
        for name, count in list(duplicates.items())[:10]:
            logger.warning(f"  {name}: {count} occurrences")
    else:
        logger.info("✓ No duplicate items found")

    # Check URL format
    invalid_urls = []
    for item in items:
        url = item["item_url"]
        if not url.startswith("https://minecraft.wiki/w/"):
            invalid_urls.append((item["item_name"], url))

    if invalid_urls:
        logger.warning(f"Found {len(invalid_urls)} items with invalid URLs:")
        for name, url in invalid_urls[:5]:
            logger.warning(f"  {name}: {url}")
    else:
        logger.info("✓ All URLs are properly formed")

    # Check for empty names
    empty_names = [item for item in items if not item["item_name"].strip()]
    if empty_names:
        logger.error(f"Found {len(empty_names)} items with empty names")
    else:
        logger.info("✓ No empty item names")

    logger.info(f"\nTotal items: {len(items)}")


def validate_transformations(
    transformations: List[Dict[str, str]],
    items: List[Dict[str, str]]
) -> None:
    """Validate transformations data quality."""
    logger.info("\n=== Validating Transformations ===")

    # Build set of valid item names
    valid_item_names = {item["item_name"] for item in items}

    # Count transformations by type
    type_counts = Counter([t["transformation_type"] for t in transformations])

    logger.info("\nTransformations by type:")
    for trans_type, count in sorted(type_counts.items()):
        logger.info(f"  {trans_type}: {count}")

    # Check for orphan transformations
    orphan_count = 0
    invalid_json_count = 0

    for i, transformation in enumerate(transformations):
        try:
            # Parse JSON fields
            inputs = json.loads(transformation["input_items"])
            outputs = json.loads(transformation["output_items"])

            # Check if all input/output items exist
            for item in inputs + outputs:
                if item["name"] not in valid_item_names:
                    orphan_count += 1
                    if orphan_count <= 5:
                        logger.warning(
                            f"Orphan item '{item['name']}' in transformation {i}"
                        )
                    break

        except json.JSONDecodeError:
            invalid_json_count += 1
            if invalid_json_count <= 5:
                logger.error(f"Invalid JSON in transformation {i}")

    if orphan_count > 0:
        logger.warning(f"\nFound {orphan_count} transformations with orphan items")
    else:
        logger.info("✓ No orphan transformations found")

    if invalid_json_count > 0:
        logger.error(f"\nFound {invalid_json_count} transformations with invalid JSON")
    else:
        logger.info("✓ All transformations have valid JSON")

    logger.info(f"\nTotal transformations: {len(transformations)}")


def check_bedrock_content(items: List[Dict[str, str]], transformations: List[Dict[str, str]]) -> None:
    """Check for any Bedrock/Education content that slipped through."""
    logger.info("\n=== Checking for Bedrock/Education Content ===")

    bedrock_keywords = ["bedrock", "education", "edition"]
    found_issues = []

    # Check items
    for item in items:
        name_lower = item["item_name"].lower()
        if any(keyword in name_lower for keyword in bedrock_keywords):
            # Allow "edition" in certain contexts
            if "bedrock" in name_lower or "education" in name_lower:
                found_issues.append(("item", item["item_name"]))

    # Check transformations metadata
    for i, transformation in enumerate(transformations):
        try:
            metadata = json.loads(transformation.get("metadata", "{}"))
            metadata_str = json.dumps(metadata).lower()
            if "bedrock" in metadata_str or "education" in metadata_str:
                found_issues.append(("transformation", f"Index {i}"))
        except json.JSONDecodeError:
            pass

    if found_issues:
        logger.warning(f"Found {len(found_issues)} potential Bedrock/Education items:")
        for issue_type, name in found_issues[:10]:
            logger.warning(f"  {issue_type}: {name}")
    else:
        logger.info("✓ No Bedrock/Education content detected")


def generate_statistics(items: List[Dict[str, str]], transformations: List[Dict[str, str]]) -> None:
    """Generate overall statistics."""
    logger.info("\n=== Overall Statistics ===")

    logger.info(f"Total unique items: {len(items)}")
    logger.info(f"Total transformations: {len(transformations)}")

    # Transformation types breakdown
    type_counts = Counter([t["transformation_type"] for t in transformations])
    logger.info("\nTransformation breakdown:")
    for trans_type in sorted(type_counts.keys()):
        count = type_counts[trans_type]
        percentage = (count / len(transformations)) * 100
        logger.info(f"  {trans_type}: {count} ({percentage:.1f}%)")


def main() -> None:
    """Main validation entry point."""
    try:
        # Load data
        logger.info("Loading CSV files...")
        items = load_items_csv("output/items.csv")
        transformations = load_transformations_csv("output/transformations.csv")

        # Run validations
        validate_items(items)
        validate_transformations(transformations, items)
        check_bedrock_content(items, transformations)
        generate_statistics(items, transformations)

        logger.info("\n=== Validation Complete ===")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        logger.error("Make sure to run extract_transformations.py first")
    except Exception as e:
        logger.error(f"Error during validation: {e}")
        raise


if __name__ == "__main__":
    main()
