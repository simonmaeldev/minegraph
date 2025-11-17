"""Module for downloading Minecraft Wiki pages."""

import os
import subprocess
import time
from pathlib import Path
from typing import Dict


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

# Complete mob list for drops extraction (from https://minecraft.wiki/w/Mob)
MOB_PAGES: Dict[str, str] = {
    # Passive mobs (allay to zombie horse)
    "allay": "https://minecraft.wiki/w/Allay",
    "armadillo": "https://minecraft.wiki/w/Armadillo",
    "axolotl": "https://minecraft.wiki/w/Axolotl",
    "bat": "https://minecraft.wiki/w/Bat",
    "camel": "https://minecraft.wiki/w/Camel",
    "cat": "https://minecraft.wiki/w/Cat",
    "chicken": "https://minecraft.wiki/w/Chicken",
    "cod": "https://minecraft.wiki/w/Cod",
    "copper_golem": "https://minecraft.wiki/w/Copper_Golem",
    "cow": "https://minecraft.wiki/w/Cow",
    "donkey": "https://minecraft.wiki/w/Donkey",
    "frog": "https://minecraft.wiki/w/Frog",
    "glow_squid": "https://minecraft.wiki/w/Glow_Squid",
    "happy_ghast": "https://minecraft.wiki/w/Happy_Ghast",
    "horse": "https://minecraft.wiki/w/Horse",
    "mooshroom": "https://minecraft.wiki/w/Mooshroom",
    "mule": "https://minecraft.wiki/w/Mule",
    "ocelot": "https://minecraft.wiki/w/Ocelot",
    "parrot": "https://minecraft.wiki/w/Parrot",
    "pig": "https://minecraft.wiki/w/Pig",
    "rabbit": "https://minecraft.wiki/w/Rabbit",
    "salmon": "https://minecraft.wiki/w/Salmon",
    "sheep": "https://minecraft.wiki/w/Sheep",
    "sniffer": "https://minecraft.wiki/w/Sniffer",
    "snow_golem": "https://minecraft.wiki/w/Snow_Golem",
    "squid": "https://minecraft.wiki/w/Squid",
    "strider": "https://minecraft.wiki/w/Strider",
    "tadpole": "https://minecraft.wiki/w/Tadpole",
    "tropical_fish": "https://minecraft.wiki/w/Tropical_Fish",
    "turtle": "https://minecraft.wiki/w/Turtle",
    "villager": "https://minecraft.wiki/w/Villager",
    "wandering_trader": "https://minecraft.wiki/w/Wandering_Trader",
    "camel_husk": "https://minecraft.wiki/w/Camel_Husk",
    "skeleton_horse": "https://minecraft.wiki/w/Skeleton_Horse",
    "zombie_horse": "https://minecraft.wiki/w/Zombie_Horse",
    # Neutral mobs (bee to zombified piglin)
    "bee": "https://minecraft.wiki/w/Bee",
    "dolphin": "https://minecraft.wiki/w/Dolphin",
    "fox": "https://minecraft.wiki/w/Fox",
    "goat": "https://minecraft.wiki/w/Goat",
    "iron_golem": "https://minecraft.wiki/w/Iron_Golem",
    "llama": "https://minecraft.wiki/w/Llama",
    "nautilus": "https://minecraft.wiki/w/Nautilus",
    "panda": "https://minecraft.wiki/w/Panda",
    "polar_bear": "https://minecraft.wiki/w/Polar_Bear",
    "pufferfish": "https://minecraft.wiki/w/Pufferfish",
    "trader_llama": "https://minecraft.wiki/w/Trader_Llama",
    "wolf": "https://minecraft.wiki/w/Wolf",
    "cave_spider": "https://minecraft.wiki/w/Cave_Spider",
    "drowned": "https://minecraft.wiki/w/Drowned",
    "enderman": "https://minecraft.wiki/w/Enderman",
    "piglin": "https://minecraft.wiki/w/Piglin",
    "spider": "https://minecraft.wiki/w/Spider",
    "zombie_nautilus": "https://minecraft.wiki/w/Zombie_Nautilus",
    "zombified_piglin": "https://minecraft.wiki/w/Zombified_Piglin",
    # Hostile mobs (blaze to wither)
    "blaze": "https://minecraft.wiki/w/Blaze",
    "bogged": "https://minecraft.wiki/w/Bogged",
    "breeze": "https://minecraft.wiki/w/Breeze",
    "creaking": "https://minecraft.wiki/w/Creaking",
    "creeper": "https://minecraft.wiki/w/Creeper",
    "elder_guardian": "https://minecraft.wiki/w/Elder_Guardian",
    "endermite": "https://minecraft.wiki/w/Endermite",
    "evoker": "https://minecraft.wiki/w/Evoker",
    "ghast": "https://minecraft.wiki/w/Ghast",
    "guardian": "https://minecraft.wiki/w/Guardian",
    "hoglin": "https://minecraft.wiki/w/Hoglin",
    "husk": "https://minecraft.wiki/w/Husk",
    "magma_cube": "https://minecraft.wiki/w/Magma_Cube",
    "parched": "https://minecraft.wiki/w/Parched",
    "phantom": "https://minecraft.wiki/w/Phantom",
    "piglin_brute": "https://minecraft.wiki/w/Piglin_Brute",
    "pillager": "https://minecraft.wiki/w/Pillager",
    "ravager": "https://minecraft.wiki/w/Ravager",
    "shulker": "https://minecraft.wiki/w/Shulker",
    "silverfish": "https://minecraft.wiki/w/Silverfish",
    "skeleton": "https://minecraft.wiki/w/Skeleton",
    "slime": "https://minecraft.wiki/w/Slime",
    "stray": "https://minecraft.wiki/w/Stray",
    "vex": "https://minecraft.wiki/w/Vex",
    "vindicator": "https://minecraft.wiki/w/Vindicator",
    "warden": "https://minecraft.wiki/w/Warden",
    "witch": "https://minecraft.wiki/w/Witch",
    "wither_skeleton": "https://minecraft.wiki/w/Wither_Skeleton",
    "zoglin": "https://minecraft.wiki/w/Zoglin",
    "zombie": "https://minecraft.wiki/w/Zombie",
    "zombie_villager": "https://minecraft.wiki/w/Zombie_Villager",
    "ender_dragon": "https://minecraft.wiki/w/Ender_Dragon",
    "wither": "https://minecraft.wiki/w/Wither",
    # Boss mob (warden already listed in hostile section above)
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

    # Add delay to respect rate limits (5 seconds between requests)
    time.sleep(5)

    # Use curl to download (bypasses some wiki blocking)
    curl_command = [
        "curl",
        "-s",  # silent
        "-L",  # follow redirects
        "-A",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "-H",
        "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "-H",
        "Accept-Language: en-US,en;q=0.5",
        url,
        "-o",
        str(output_path),
    ]

    result = subprocess.run(curl_command, capture_output=True, text=True, timeout=60)

    if result.returncode != 0:
        raise Exception(f"curl failed with return code {result.returncode}: {result.stderr}")

    print(f"Saved to: {output_path}")

    return str(output_path)


def download_all_pages(output_dir: str = "ai_doc/downloaded_pages") -> None:
    """
    Download all wiki pages needed for transformation extraction.

    Args:
        output_dir: Base directory for downloaded pages
    """
    failed_downloads = []

    print("Downloading main wiki pages...")
    for page_name, url in WIKI_PAGES.items():
        try:
            download_page(page_name, url, output_dir)
        except Exception as e:
            print(f"Failed to download {page_name}: {e}")
            failed_downloads.append((page_name, url, str(e)))

    print("\nDownloading mob pages...")
    mob_dir = os.path.join(output_dir, "mobs")
    for mob_name, url in MOB_PAGES.items():
        try:
            download_page(mob_name, url, mob_dir)
        except Exception as e:
            print(f"Failed to download {mob_name}: {e}")
            failed_downloads.append((mob_name, url, str(e)))

    print("\nAll downloads complete!")

    if failed_downloads:
        print(f"\n{len(failed_downloads)} downloads failed:")
        for name, url, error in failed_downloads:
            print(f"  - {name}: {error}")


if __name__ == "__main__":
    download_all_pages()
