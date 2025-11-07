"""
Download item images from Minecraft Wiki pages.

This script downloads item images from the Minecraft Wiki, parsing HTML to find
the correct infobox image (not inventory images), and saves them with standardized
filenames for use in the 3D visualization.
"""

import argparse
import csv
import logging
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from PIL import Image

# Configure logging
logger = logging.getLogger(__name__)


def standardize_filename(item_name: str) -> str:
    """
    Convert item name to standardized filename format.

    Args:
        item_name: Original item name (e.g., "Iron Ingot")

    Returns:
        Standardized filename (e.g., "iron_ingot.png")
    """
    import re
    # Convert to lowercase and replace spaces with underscores
    filename = item_name.lower().replace(" ", "_")
    # Remove special characters that might cause issues
    filename = "".join(c for c in filename if c.isalnum() or c == "_")
    # Collapse multiple underscores into one
    filename = re.sub(r"_+", "_", filename)
    return f"{filename}.png"


def load_items_from_csv(csv_path: str) -> List[Dict[str, str]]:
    """
    Load items from CSV file.

    Args:
        csv_path: Path to items.csv file

    Returns:
        List of dictionaries with 'item_name' and 'item_url' keys
    """
    items = []
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if "item_name" in row and "item_url" in row:
                    items.append({
                        "item_name": row["item_name"],
                        "item_url": row["item_url"]
                    })
        logger.info(f"Loaded {len(items)} items from {csv_path}")
        return items
    except Exception as e:
        logger.error(f"Failed to load items from {csv_path}: {e}")
        raise


def extract_image_url_from_page(page_url: str) -> Optional[str]:
    """
    Extract the item image URL from a Minecraft Wiki page.

    Looks for the main infobox image, excluding inventory images.

    Args:
        page_url: URL of the wiki page

    Returns:
        Image URL if found, None otherwise
    """
    try:
        # Add a user agent to avoid being blocked
        headers = {
            "User-Agent": "MinecraftGraphBot/1.0 (Educational Project)"
        }

        response = requests.get(page_url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

        # First, try to find the main infobox (not inventory images)
        # Look for divs with class containing 'infobox' but not 'invimages'
        infoboxes = soup.find_all("div", class_=lambda x: x and "infobox" in x.lower())

        for infobox in infoboxes:
            # Skip inventory image infoboxes
            class_str = " ".join(infobox.get("class", []))
            if "invimages" in class_str.lower():
                continue

            # Find the first img tag within this infobox
            img = infobox.find("img")
            if img and img.get("src"):
                img_url = img["src"]
                # Handle relative URLs
                if img_url.startswith("//"):
                    img_url = "https:" + img_url
                elif img_url.startswith("/"):
                    img_url = urljoin(page_url, img_url)

                logger.debug(f"Found image URL: {img_url}")
                return img_url

        logger.warning(f"No suitable infobox image found on {page_url}")
        return None

    except requests.RequestException as e:
        logger.error(f"Failed to fetch page {page_url}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error parsing page {page_url}: {e}")
        return None


def detect_image_format(file_path: str) -> str:
    """
    Detect the actual image format of a file.

    Uses Pillow to detect the true file format,
    regardless of the file extension.

    Args:
        file_path: Path to the image file

    Returns:
        Format string (e.g., "gif", "png", "jpeg") or "unknown" if detection fails
    """
    try:
        with Image.open(file_path) as img:
            format_type = img.format
            if format_type:
                format_lower = format_type.lower()
                logger.debug(f"Detected format '{format_lower}' for {file_path}")
                return format_lower
            else:
                logger.warning(f"Could not detect format for {file_path}")
                return "unknown"
    except Exception as e:
        logger.error(f"Error detecting format for {file_path}: {e}")
        return "unknown"


def convert_gif_to_png(gif_path: str, png_path: str) -> bool:
    """
    Convert a GIF image to PNG format using ffmpeg.

    Extracts only the first frame for animated GIFs.

    Args:
        gif_path: Path to the input GIF file
        png_path: Path to the output PNG file

    Returns:
        True if conversion successful, False otherwise
    """
    try:
        # Use ffmpeg to convert GIF to PNG
        # -vframes 1: Extract only the first frame (important for animated GIFs)
        # -y: Overwrite output file without prompting
        cmd = ["ffmpeg", "-i", gif_path, "-vframes", "1", "-y", png_path]

        logger.debug(f"Running ffmpeg conversion: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            logger.info(f"Successfully converted GIF to PNG: {gif_path} -> {png_path}")
            return True
        else:
            logger.error(f"ffmpeg conversion failed (exit code {result.returncode}): {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        logger.error(f"ffmpeg conversion timed out for {gif_path}")
        return False
    except FileNotFoundError:
        logger.error("ffmpeg not found. Please install ffmpeg to enable GIF conversion.")
        return False
    except Exception as e:
        logger.error(f"Error converting GIF to PNG for {gif_path}: {e}")
        return False


def download_image(
    image_url: str,
    output_path: str,
    min_size: int = 100,
    max_size: int = 10 * 1024 * 1024,  # 10MB
    convert_gifs: bool = True
) -> Tuple[bool, bool]:
    """
    Download an image from a URL and save it to a file.

    Args:
        image_url: URL of the image to download
        output_path: Path where the image should be saved
        min_size: Minimum file size in bytes (warns if smaller)
        max_size: Maximum file size in bytes (warns if larger)
        convert_gifs: If True, automatically convert GIF files to PNG format

    Returns:
        Tuple of (success, converted) where:
        - success: True if download successful, False otherwise
        - converted: True if a GIF was converted to PNG, False otherwise
    """
    try:
        headers = {
            "User-Agent": "MinecraftGraphBot/1.0 (Educational Project)"
        }

        response = requests.get(image_url, headers=headers, timeout=15)
        response.raise_for_status()

        # Check file size
        content_length = len(response.content)
        if content_length < min_size:
            logger.warning(
                f"Downloaded image is suspiciously small ({content_length} bytes): {image_url}"
            )
        elif content_length > max_size:
            logger.warning(
                f"Downloaded image is suspiciously large ({content_length} bytes): {image_url}"
            )

        # Save the image
        with open(output_path, "wb") as f:
            f.write(response.content)

        logger.debug(f"Successfully downloaded image to {output_path}")

        # Detect format and convert GIFs to PNG if needed
        converted = False
        if convert_gifs:
            detected_format = detect_image_format(output_path)
            if detected_format == "gif":
                logger.info(f"Detected GIF file, converting to PNG: {output_path}")
                # Create a temporary path for the conversion
                temp_path = output_path + ".tmp.png"
                if convert_gif_to_png(output_path, temp_path):
                    # Replace the original GIF with the converted PNG
                    shutil.move(temp_path, output_path)
                    logger.info(f"Successfully replaced GIF with PNG: {output_path}")
                    converted = True
                else:
                    logger.warning(f"Failed to convert GIF, keeping original: {output_path}")
                    # Clean up temp file if it exists
                    if os.path.exists(temp_path):
                        os.remove(temp_path)

        return True, converted

    except requests.RequestException as e:
        logger.error(f"Failed to download image from {image_url}: {e}")
        return False, False
    except Exception as e:
        logger.error(f"Error saving image to {output_path}: {e}")
        return False, False


def main():
    """Main entry point for the image downloader script."""
    parser = argparse.ArgumentParser(
        description="Download item images from Minecraft Wiki"
    )
    parser.add_argument(
        "--input",
        type=str,
        default="output/items.csv",
        help="Path to items CSV file (default: output/items.csv)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="images",
        help="Directory to save images (default: images/)"
    )
    parser.add_argument(
        "--force-redownload",
        action="store_true",
        help="Force re-download of existing images"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate downloads without actually downloading"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Delay between downloads in seconds (default: 0.5)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of items to process (for testing)"
    )
    parser.add_argument(
        "--convert-gifs",
        action="store_true",
        default=True,
        help="Automatically convert GIF files to PNG format (default: True)"
    )
    parser.add_argument(
        "--no-convert-gifs",
        dest="convert_gifs",
        action="store_false",
        help="Disable automatic GIF to PNG conversion"
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    # Create output directory
    output_dir = Path(args.output_dir)
    if not args.dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Output directory: {output_dir.absolute()}")

    # Load items from CSV
    try:
        items = load_items_from_csv(args.input)
    except Exception as e:
        logger.error(f"Failed to load items: {e}")
        return 1

    # Apply limit if specified
    if args.limit:
        items = items[:args.limit]
        logger.info(f"Limited to first {args.limit} items")

    # Statistics
    total_items = len(items)
    successful_downloads = 0
    cached_items = 0
    converted_gifs = 0
    failed_items = []

    # Process each item
    for idx, item in enumerate(items, 1):
        item_name = item["item_name"]
        item_url = item["item_url"]

        # Generate standardized filename
        filename = standardize_filename(item_name)
        output_path = output_dir / filename

        # Check if image already exists (skip early to avoid unnecessary processing)
        if output_path.exists() and not args.force_redownload:
            logger.debug(f"[{idx}/{total_items}] Skipping (already cached): {item_name}")
            cached_items += 1
            continue

        logger.info(f"[{idx}/{total_items}] Processing: {item_name}")

        if args.dry_run:
            logger.info(f"  → Would download from: {item_url}")
            logger.info(f"  → Would save to: {filename}")
            successful_downloads += 1
            continue

        # Extract image URL from wiki page
        logger.debug(f"  → Fetching page: {item_url}")
        image_url = extract_image_url_from_page(item_url)

        if not image_url:
            logger.error(f"  → Failed to find image URL for {item_name}")
            failed_items.append(item_name)
            continue

        # Download the image
        logger.debug(f"  → Downloading image: {image_url}")
        success, converted = download_image(
            image_url,
            str(output_path),
            convert_gifs=args.convert_gifs
        )

        if success:
            logger.info(f"  → ✓ Downloaded: {filename}")
            successful_downloads += 1
            if converted:
                converted_gifs += 1
        else:
            logger.error(f"  → ✗ Failed to download: {filename}")
            failed_items.append(item_name)

        # Rate limiting
        if idx < total_items and args.delay > 0:
            time.sleep(args.delay)

    # Print summary
    print("\n" + "=" * 60)
    print("DOWNLOAD SUMMARY")
    print("=" * 60)
    print(f"Total items:           {total_items}")
    print(f"Successfully downloaded: {successful_downloads}")
    print(f"Already cached:        {cached_items}")
    print(f"Converted GIFs:        {converted_gifs}")
    print(f"Failed:                {len(failed_items)}")

    if failed_items:
        print("\nFailed items:")
        for item in failed_items:
            print(f"  - {item}")

    print("=" * 60)

    if args.dry_run:
        print("\n(DRY RUN - No files were actually downloaded)")

    return 0 if len(failed_items) == 0 else 1


if __name__ == "__main__":
    exit(main())
