"""Main script for extracting Minecraft transformations and exporting to CSV."""

import argparse
import csv
import json
import logging
import os
from pathlib import Path
from typing import List, Set

from core.data_models import Item, Transformation
from core.parsers import (
    parse_crafting,
    parse_smelting,
    parse_smithing,
    parse_stonecutter,
    parse_trading,
    parse_mob_drops,
    parse_brewing,
    parse_composting,
    parse_grindstone,
)
from core.lazy_load_detector import find_lazy_load_pages
from core.download_data import download_crafting_subcategory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_html_file(filepath: str) -> str:
    """
    Load HTML content from file.

    Args:
        filepath: Path to HTML file

    Returns:
        HTML content as string
    """
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def extract_all_transformations(data_dir: str = "ai_doc/downloaded_pages") -> List[Transformation]:
    """
    Extract all transformations from downloaded wiki pages.

    Args:
        data_dir: Directory containing downloaded HTML files

    Returns:
        List of all extracted transformations
    """
    transformations: List[Transformation] = []

    # Parse main wiki pages
    parsers = {
        "crafting.html": parse_crafting,
        "smelting.html": parse_smelting,
        "smithing.html": parse_smithing,
        "stonecutter.html": parse_stonecutter,
        "trading.html": parse_trading,
        "brewing.html": parse_brewing,
        "composting.html": parse_composting,
        "grindstone.html": parse_grindstone,
    }

    for filename, parser_func in parsers.items():
        filepath = os.path.join(data_dir, filename)
        if os.path.exists(filepath):
            logger.info(f"Parsing {filename}...")
            try:
                html_content = load_html_file(filepath)

                # Special handling for crafting.html to extract lazy-loaded subcategories
                if filename == "crafting.html":
                    # Parse main crafting page
                    results = parser_func(html_content)
                    transformations.extend(results)
                    logger.info(f"  Found {len(results)} transformations from main page")

                    # Detect lazy-load subcategories
                    subcategory_urls = find_lazy_load_pages(html_content)
                    logger.info(f"  Detected {len(subcategory_urls)} lazy-load subcategories")

                    # Download and parse each subcategory
                    for url in subcategory_urls:
                        try:
                            # Extract category name for logging
                            category_name = url.split("/")[-1].replace("_", " ")

                            # Download subcategory page
                            subcategory_path = download_crafting_subcategory(url, data_dir)

                            # Parse subcategory page
                            subcategory_html = load_html_file(subcategory_path)
                            subcategory_results = parser_func(subcategory_html)
                            transformations.extend(subcategory_results)

                            if subcategory_results:
                                logger.info(f"    {category_name}: {len(subcategory_results)} transformations")
                        except Exception as e:
                            logger.error(f"    Error processing {url}: {e}")
                else:
                    # Standard parsing for other transformation types
                    results = parser_func(html_content)
                    transformations.extend(results)
                    logger.info(f"  Found {len(results)} transformations")
            except Exception as e:
                logger.error(f"  Error parsing {filename}: {e}")
        else:
            logger.warning(f"  File not found: {filepath}")

    # Parse mob drop pages
    mob_dir = os.path.join(data_dir, "mobs")
    if os.path.exists(mob_dir):
        logger.info("Parsing mob drop pages...")
        for mob_file in Path(mob_dir).glob("*.html"):
            mob_name = mob_file.stem.replace("_", " ").title()
            try:
                html_content = load_html_file(str(mob_file))
                results = parse_mob_drops(html_content, mob_name)
                transformations.extend(results)
                if results:
                    logger.info(f"  {mob_name}: {len(results)} drops")
            except Exception as e:
                logger.error(f"  Error parsing {mob_file.name}: {e}")

    logger.info(f"\nTotal transformations extracted: {len(transformations)}")
    return transformations


def extract_unique_items(transformations: List[Transformation]) -> Set[Item]:
    """
    Extract all unique items from transformations.

    Args:
        transformations: List of transformations

    Returns:
        Set of unique items
    """
    items: Set[Item] = set()

    for transformation in transformations:
        items.update(transformation.inputs)
        items.update(transformation.outputs)

    return items


def export_items_csv(items: Set[Item], filepath: str) -> None:
    """
    Export items to CSV file.

    Args:
        items: Set of items to export
        filepath: Output CSV file path
    """
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    # Sort items by name for consistent output
    sorted_items = sorted(items, key=lambda x: x.name)

    with open(filepath, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["item_name", "item_url"])

        for item in sorted_items:
            writer.writerow([item.name, item.url])

    logger.info(f"Exported {len(sorted_items)} items to {filepath}")


def export_transformations_csv(transformations: List[Transformation], filepath: str) -> None:
    """
    Export transformations to CSV file.

    Args:
        transformations: List of transformations to export
        filepath: Output CSV file path
    """
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    with open(filepath, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "transformation_type",
            "input_items",
            "output_items",
            "metadata"
        ])

        for transformation in transformations:
            # Convert inputs to JSON array
            inputs_json = json.dumps([
                item.name
                for item in transformation.inputs
            ])

            # Convert outputs to JSON array
            outputs_json = json.dumps([
                item.name
                for item in transformation.outputs
            ])

            # Convert metadata to JSON
            metadata_json = json.dumps(transformation.metadata)

            writer.writerow([
                transformation.transformation_type.value,
                inputs_json,
                outputs_json,
                metadata_json
            ])

    logger.info(f"Exported {len(transformations)} transformations to {filepath}")


def main() -> None:
    """Main entry point for extraction script."""
    parser = argparse.ArgumentParser(
        description="Extract Minecraft transformations from wiki pages"
    )
    parser.add_argument(
        "--data-dir",
        default="ai_doc/downloaded_pages",
        help="Directory containing downloaded HTML files"
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Directory for output CSV files"
    )

    args = parser.parse_args()

    logger.info("Starting transformation extraction...")

    # Extract all transformations
    transformations = extract_all_transformations(args.data_dir)

    if not transformations:
        logger.warning("No transformations found. Check your data files.")
        return

    # Extract unique items
    items = extract_unique_items(transformations)
    logger.info(f"Found {len(items)} unique items")

    # Export to CSV
    items_csv = os.path.join(args.output_dir, "items.csv")
    transformations_csv = os.path.join(args.output_dir, "transformations.csv")

    export_items_csv(items, items_csv)
    export_transformations_csv(transformations, transformations_csv)

    logger.info("\nExtraction complete!")


if __name__ == "__main__":
    main()
