"""Main script for extracting Minecraft transformations and exporting to CSV."""

import argparse
import csv
import json
import logging
import os
from pathlib import Path
from typing import List, Set

from core.data_models import Item, Transformation, TransformationType
from core.parsers import (
    parse_bartering,
    parse_brewing,
    parse_composting,
    parse_crafting,
    parse_grindstone,
    parse_mob_drops,
    parse_smelting,
    parse_smithing,
    parse_stonecutter,
    parse_tool_crafting,
    parse_trading,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Manual fixes to add missing transformations and items
# Format: (transformation_type, input_items, output_items, metadata)
# where input_items and output_items are lists of (item_name, item_url) tuples
MANUAL_FIXES_ADD: List[tuple] = [
    ("mob_drop", [("Evoker", "https://minecraft.wiki/w/Evoker")], [("Totem Of Undying", "https://minecraft.wiki/w/Totem_of_Undying")], {}),
    ("mob_drop", [("Evoker", "https://minecraft.wiki/w/Evoker")], [("Emerald", "https://minecraft.wiki/w/Emerald")], {}),
    ("mob_drop", [("Vindicator", "https://minecraft.wiki/w/Vindicator")], [("Emerald", "https://minecraft.wiki/w/Emerald")], {}),
    ("mob_drop", [("Vindicator", "https://minecraft.wiki/w/Vindicator")], [("Ominous Bottle", "https://minecraft.wiki/w/Ominous_Bottle")], {}),
    ("mob_drop", [("Witch", "https://minecraft.wiki/w/Witch")], [("Redstone Dust", "https://minecraft.wiki/w/Redstone_Dust")], {}),
    ("mob_drop", [("Witch", "https://minecraft.wiki/w/Witch")], [("Glass Bottle", "https://minecraft.wiki/w/Glass_Bottle")], {}),
    ("mob_drop", [("Witch", "https://minecraft.wiki/w/Witch")], [("Glowstone Dust", "https://minecraft.wiki/w/Glowstone_Dust")], {}),
    ("mob_drop", [("Witch", "https://minecraft.wiki/w/Witch")], [("Gunpowder", "https://minecraft.wiki/w/Gunpowder")], {}),
    ("mob_drop", [("Witch", "https://minecraft.wiki/w/Witch")], [("Spider Eye", "https://minecraft.wiki/w/Spider_Eye")], {}),
    ("mob_drop", [("Witch", "https://minecraft.wiki/w/Witch")], [("Sugar", "https://minecraft.wiki/w/Sugar")], {}),
    ("mob_drop", [("Witch", "https://minecraft.wiki/w/Witch")], [("Stick", "https://minecraft.wiki/w/Stick")], {}),
    ("world_interaction", [("Log", "https://minecraft.wiki/w/Log")], [("Stripped Log", "https://minecraft.wiki/w/Stripped_Log")], {}),
    ("world_interaction", [("Wood", "https://minecraft.wiki/w/Wood")], [("Stripped Wood", "https://minecraft.wiki/w/Stripped_Wood")], {}),
    ("world_interaction", [("Block of Bamboo", "https://minecraft.wiki/w/Block_of_Bamboo")], [("Block of Stripped Bamboo", "https://minecraft.wiki/w/Block_of_Stripped_Bamboo")], {}),
]

# Manual fixes to remove transformations and items
# List of item name patterns to match and remove (e.g., "Potion of Big", "Arrow of Fire")
# Any transformation containing an input or output matching these patterns will be removed
MANUAL_FIXES_REMOVE: List[str] = [
        "Potion of Big", "Potion of Small", "Potion of Sticky", "Potion of Decay"
]


def apply_manual_fixes(transformations: List[Transformation]) -> List[Transformation]:
    """
    Apply manual fixes to add and remove transformations and items.

    Args:
        transformations: List of extracted transformations

    Returns:
        List of transformations with manual fixes applied
    """
    # Apply removals first
    if MANUAL_FIXES_REMOVE:
        logger.info("Applying manual removals...")
        original_count = len(transformations)

        transformations = [
            t for t in transformations
            if not any(
                pattern in item.name
                for pattern in MANUAL_FIXES_REMOVE
                for item in t.inputs + t.outputs
            )
        ]

        removed_count = original_count - len(transformations)
        if removed_count > 0:
            logger.info(f"  Removed {removed_count} transformations matching removal patterns")

    # Apply additions
    if MANUAL_FIXES_ADD:
        logger.info("Applying manual additions...")

        for fix in MANUAL_FIXES_ADD:
            transformation_type_str, input_items, output_items, metadata = fix

            # Convert string type to enum
            try:
                transformation_type = TransformationType(transformation_type_str)
            except ValueError:
                logger.error(f"  Invalid transformation type: {transformation_type_str}")
                continue

            # Convert tuples to Item objects
            inputs = [Item(name=name, url=url) for name, url in input_items]
            outputs = [Item(name=name, url=url) for name, url in output_items]

            # Create transformation
            try:
                transformation = Transformation(
                    transformation_type=transformation_type,
                    inputs=inputs,
                    outputs=outputs,
                    metadata=metadata
                )
                transformations.append(transformation)
                logger.info(f"  Added: {transformation_type_str} ({inputs[0].name} -> {outputs[0].name})")
            except ValueError as e:
                logger.error(f"  Failed to create transformation: {e}")

        logger.info(f"Applied {len(MANUAL_FIXES_ADD)} manual additions")

    return transformations


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
        "bartering.html": parse_bartering,
        "brewing.html": parse_brewing,
        "composting.html": parse_composting,
        "crafting.html": parse_crafting,
        "grindstone.html": parse_grindstone,
        "smelting.html": parse_smelting,
        "smithing.html": parse_smithing,
        "stonecutter.html": parse_stonecutter,
        "tool.html": parse_tool_crafting,
        "trading.html": parse_trading,
    }

    for filename, parser_func in parsers.items():
        filepath = os.path.join(data_dir, filename)
        if os.path.exists(filepath):
            logger.info(f"Parsing {filename}...")
            try:
                html_content = load_html_file(filepath)

                # Check if crafting.html might have lazy-loaded content
                if filename == "crafting.html" and "load-page" in html_content:
                    logger.warning("  ⚠️  WARNING: crafting.html contains lazy-loaded sections!")
                    logger.warning("  To get complete data, please:")
                    logger.warning("    1. Open https://minecraft.wiki/w/Crafting in your browser")
                    logger.warning("    2. Scroll through the entire page to load all sections")
                    logger.warning("    3. Open browser inspector (F12)")
                    logger.warning("    4. Copy the full HTML from the <html> element")
                    logger.warning("    5. Paste it into ai_doc/downloaded_pages/crafting.html")
                    logger.warning("  Then re-run this extraction script.")
                    logger.warning("")

                # Parse the page
                results = parser_func(html_content)
                transformations.extend(results)
                logger.info(f"  Found {len(results)} transformations")
            except Exception as e:
                logger.error(f"  Error parsing {filename}: {e}")
        else:
            logger.warning(f"  File not found: {filepath}")

            # Special message for crafting.html
            if filename == "crafting.html":
                logger.warning("  To download crafting.html manually:")
                logger.warning("    1. Open https://minecraft.wiki/w/Crafting in your browser")
                logger.warning("    2. Scroll through the entire page to load all sections")
                logger.warning("    3. Open browser inspector (F12)")
                logger.warning("    4. Copy the full HTML from the <html> element")
                logger.warning("    5. Save it to ai_doc/downloaded_pages/crafting.html")
                logger.warning("")

    # Parse wandering trader trades from the wandering trader mob page
    wandering_trader_path = os.path.join(data_dir, "mobs", "wandering_trader.html")
    if os.path.exists(wandering_trader_path):
        logger.info("Parsing wandering trader trades...")
        try:
            html_content = load_html_file(wandering_trader_path)
            results = parse_trading(html_content)
            transformations.extend(results)
            logger.info(f"  Found {len(results)} wandering trader trades")
        except Exception as e:
            logger.error(f"  Error parsing wandering trader trades: {e}")

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

    # Apply manual fixes
    transformations = apply_manual_fixes(transformations)

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
