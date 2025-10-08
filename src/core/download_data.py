"""Module for downloading Minecraft Wiki pages."""

import os
from pathlib import Path
from typing import Dict
import requests


WIKI_PAGES: Dict[str, str] = {
    "crafting": "https://minecraft.wiki/w/Crafting",
    "smelting": "https://minecraft.wiki/w/Smelting",
    "trading": "https://minecraft.wiki/w/Trading",
    "smithing": "https://minecraft.wiki/w/Smithing",
    "stonecutter": "https://minecraft.wiki/w/Stonecutter",
    "drops": "https://minecraft.wiki/w/Drops",
    "brewing": "https://minecraft.wiki/w/Brewing",
    "composting": "https://minecraft.wiki/w/Composter",
    "grindstone": "https://minecraft.wiki/w/Grindstone",
}

# Common mob list for drops extraction
MOB_PAGES: Dict[str, str] = {
    # Passive mobs
    "chicken": "https://minecraft.wiki/w/Chicken",
    "cow": "https://minecraft.wiki/w/Cow",
    "pig": "https://minecraft.wiki/w/Pig",
    "sheep": "https://minecraft.wiki/w/Sheep",
    "rabbit": "https://minecraft.wiki/w/Rabbit",
    "horse": "https://minecraft.wiki/w/Horse",
    "donkey": "https://minecraft.wiki/w/Donkey",
    "mule": "https://minecraft.wiki/w/Mule",
    "llama": "https://minecraft.wiki/w/Llama",
    "fox": "https://minecraft.wiki/w/Fox",
    "cat": "https://minecraft.wiki/w/Cat",
    "parrot": "https://minecraft.wiki/w/Parrot",
    "bat": "https://minecraft.wiki/w/Bat",
    "cod": "https://minecraft.wiki/w/Cod",
    "salmon": "https://minecraft.wiki/w/Salmon",
    "tropical_fish": "https://minecraft.wiki/w/Tropical_Fish",
    "pufferfish": "https://minecraft.wiki/w/Pufferfish",
    "squid": "https://minecraft.wiki/w/Squid",
    "glow_squid": "https://minecraft.wiki/w/Glow_Squid",
    "turtle": "https://minecraft.wiki/w/Turtle",
    "frog": "https://minecraft.wiki/w/Frog",
    "tadpole": "https://minecraft.wiki/w/Tadpole",
    "axolotl": "https://minecraft.wiki/w/Axolotl",
    "goat": "https://minecraft.wiki/w/Goat",
    "sniffer": "https://minecraft.wiki/w/Sniffer",
    "armadillo": "https://minecraft.wiki/w/Armadillo",
    # Neutral mobs
    "wolf": "https://minecraft.wiki/w/Wolf",
    "spider": "https://minecraft.wiki/w/Spider",
    "cave_spider": "https://minecraft.wiki/w/Cave_Spider",
    "enderman": "https://minecraft.wiki/w/Enderman",
    "bee": "https://minecraft.wiki/w/Bee",
    "iron_golem": "https://minecraft.wiki/w/Iron_Golem",
    "polar_bear": "https://minecraft.wiki/w/Polar_Bear",
    "panda": "https://minecraft.wiki/w/Panda",
    "dolphin": "https://minecraft.wiki/w/Dolphin",
    "zombified_piglin": "https://minecraft.wiki/w/Zombified_Piglin",
    "piglin": "https://minecraft.wiki/w/Piglin",
    "piglin_brute": "https://minecraft.wiki/w/Piglin_Brute",
    # Hostile mobs
    "zombie": "https://minecraft.wiki/w/Zombie",
    "skeleton": "https://minecraft.wiki/w/Skeleton",
    "creeper": "https://minecraft.wiki/w/Creeper",
    "witch": "https://minecraft.wiki/w/Witch",
    "slime": "https://minecraft.wiki/w/Slime",
    "magma_cube": "https://minecraft.wiki/w/Magma_Cube",
    "ghast": "https://minecraft.wiki/w/Ghast",
    "blaze": "https://minecraft.wiki/w/Blaze",
    "phantom": "https://minecraft.wiki/w/Phantom",
    "drowned": "https://minecraft.wiki/w/Drowned",
    "husk": "https://minecraft.wiki/w/Husk",
    "stray": "https://minecraft.wiki/w/Stray",
    "shulker": "https://minecraft.wiki/w/Shulker",
    "guardian": "https://minecraft.wiki/w/Guardian",
    "elder_guardian": "https://minecraft.wiki/w/Elder_Guardian",
    "endermite": "https://minecraft.wiki/w/Endermite",
    "silverfish": "https://minecraft.wiki/w/Silverfish",
    "vindicator": "https://minecraft.wiki/w/Vindicator",
    "evoker": "https://minecraft.wiki/w/Evoker",
    "vex": "https://minecraft.wiki/w/Vex",
    "pillager": "https://minecraft.wiki/w/Pillager",
    "ravager": "https://minecraft.wiki/w/Ravager",
    "hoglin": "https://minecraft.wiki/w/Hoglin",
    "zoglin": "https://minecraft.wiki/w/Zoglin",
    "wither_skeleton": "https://minecraft.wiki/w/Wither_Skeleton",
    "bogged": "https://minecraft.wiki/w/Bogged",
    "breeze": "https://minecraft.wiki/w/Breeze",
    # Boss mobs
    "ender_dragon": "https://minecraft.wiki/w/Ender_Dragon",
    "wither": "https://minecraft.wiki/w/Wither",
    "warden": "https://minecraft.wiki/w/Warden",
}


def download_page(page_name: str, url: str, output_dir: str) -> str:
    """
    Download a wiki page if not already cached.

    Args:
        page_name: Name to use for the output file
        url: URL to download from
        output_dir: Directory to save the file in

    Returns:
        Path to the downloaded or cached file
    """
    output_path = Path(output_dir) / f"{page_name}.html"

    # Check if file already exists
    if output_path.exists():
        print(f"Using cached file: {output_path}")
        return str(output_path)

    # Create output directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Download the page
    print(f"Downloading {page_name} from {url}...")
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; MinecraftDataExtractor/1.0)"
    }
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    # Save to file
    output_path.write_text(response.text, encoding="utf-8")
    print(f"Saved to: {output_path}")

    return str(output_path)


def download_all_pages(output_dir: str = "ai_doc/downloaded_pages") -> None:
    """
    Download all wiki pages needed for transformation extraction.

    Args:
        output_dir: Base directory for downloaded pages
    """
    print("Downloading main wiki pages...")
    for page_name, url in WIKI_PAGES.items():
        download_page(page_name, url, output_dir)

    print("\nDownloading mob pages...")
    mob_dir = os.path.join(output_dir, "mobs")
    for mob_name, url in MOB_PAGES.items():
        download_page(mob_name, url, mob_dir)

    print("\nAll downloads complete!")


if __name__ == "__main__":
    download_all_pages()
