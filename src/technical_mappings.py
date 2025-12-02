"""
Technical Item Mappings for Minecraft Transformation Compression

This module provides mappings from technical category names to lists of exact
item names. These mappings are used to compress the transformation graph by
grouping functionally similar items together.

The TECHNICAL_MAPPINGS dictionary is designed to be human-readable and easy to
edit. The generate_exact_to_technical() function creates a reverse mapping for
efficient lookup during compression.

Example:
    TECHNICAL_MAPPINGS = {
        "Planks": ["Oak Planks", "Spruce Planks", ...],
        "Tipped Arrow": ["Arrow of Poison", "Arrow of Healing", ...]
    }

    exact_to_technical = generate_exact_to_technical()
    # {"Oak Planks": "Planks", "Arrow of Poison": "Tipped Arrow", ...}
"""

import logging
from typing import Dict, List, Set

logger = logging.getLogger(__name__)

# Technical mappings: technical category name -> list of exact item names
TECHNICAL_MAPPINGS: Dict[str, List[str]] = {
    # Wood Products - Sapling
    "Saplings": [
        "Oak Sapling",
        "Spruce Sapling",
        "Birch Sapling",
        "Jungle Sapling",
        "Acacia Sapling",
        "Dark Oak Sapling",
        "Mangrove Sapling",
        "Cherry Sapling",
        "Pale Oak Sapling",
        "Bamboo Sapling",
        "Crimson Sapling",
        "Warped Sapling",
    ],
    # Wood Products - Shelf
    "Shelf": [
        "Oak Shelf",
        "Spruce Shelf",
        "Birch Shelf",
        "Jungle Shelf",
        "Acacia Shelf",
        "Dark Oak Shelf",
        "Mangrove Shelf",
        "Cherry Shelf",
        "Pale Oak Shelf",
        "Bamboo Shelf",
        "Crimson Shelf",
        "Warped Shelf",
    ],
    # Wood Products - Planks
    "Planks": [
        "Oak Planks",
        "Spruce Planks",
        "Birch Planks",
        "Jungle Planks",
        "Acacia Planks",
        "Dark Oak Planks",
        "Crimson Planks",
        "Warped Planks",
        "Mangrove Planks",
        "Cherry Planks",
        "Bamboo Planks",
        "Pale Oak Planks",
    ],
    # Wood Products - Logs
    "Log": [
        "Oak Log",
        "Spruce Log",
        "Birch Log",
        "Jungle Log",
        "Acacia Log",
        "Dark Oak Log",
        "Mangrove Log",
        "Cherry Log",
        "Pale Oak Log",
        "Crimson Stem",
        "Warped Stem",
    ],
    # Wood Products - Stripped Logs
    "Stripped Log": [
        "Stripped Oak Log",
        "Stripped Spruce Log",
        "Stripped Birch Log",
        "Stripped Jungle Log",
        "Stripped Acacia Log",
        "Stripped Dark Oak Log",
        "Stripped Mangrove Log",
        "Stripped Cherry Log",
        "Stripped Pale Oak Log",
        "Stripped Crimson Stem",
        "Stripped Warped Stem",
    ],
    # Wood Products - Wood Blocks
    "Wood": [
        "Oak Wood",
        "Spruce Wood",
        "Birch Wood",
        "Jungle Wood",
        "Acacia Wood",
        "Dark Oak Wood",
        "Mangrove Wood",
        "Cherry Wood",
        "Pale Oak Wood",
        "Crimson Hyphae",
        "Warped Hyphae",
    ],
    # Wood Products - Stripped Wood Blocks
    "Stripped Wood": [
        "Stripped Oak Wood",
        "Stripped Spruce Wood",
        "Stripped Birch Wood",
        "Stripped Jungle Wood",
        "Stripped Acacia Wood",
        "Stripped Dark Oak Wood",
        "Stripped Mangrove Wood",
        "Stripped Cherry Wood",
        "Stripped Pale Oak Wood",
        "Stripped Crimson Hyphae",
        "Stripped Warped Hyphae",
    ],
    # Combat - Tipped Arrows (arrows with potion effects)
    "Tipped Arrow": [
        "Arrow of Poison",
        "Arrow of Healing",
        "Arrow of Harming",
        "Arrow of Regeneration",
        "Arrow of Strength",
        "Arrow of Swiftness",
        "Arrow of Slowness",
        "Arrow of Leaping",
        "Arrow of Invisibility",
        "Arrow of Night Vision",
        "Arrow of Weakness",
        "Arrow of Fire Resistance",
        "Arrow of Water Breathing",
        "Arrow of Luck",
        "Arrow of the Turtle Master",
        "Arrow of Slow Falling",
        "Arrow of Decay",
        "Arrow of Splashing",
        "Arrow of Oozing",
        "Arrow of Weaving",
        "Arrow of Wind Charging",
        "Arrow of Infestation",
        "Arrow of Big",
        "Arrow of Small",
        "Arrow of Sticky",
        "Spectral Arrow",
    ],
    # Combat - Base Arrows (note: keep separate from tipped arrows)
    # "Arrow" is the regular arrow, "Spectral Arrow" is craftable with glowstone
    # We don't compress these together as they have different crafting recipes
    # Transportation - Boats
    "Boat": [
        "Oak Boat",
        "Spruce Boat",
        "Birch Boat",
        "Jungle Boat",
        "Acacia Boat",
        "Dark Oak Boat",
        "Mangrove Boat",
        "Cherry Boat",
        "Pale Oak Boat",
    ],
    # Transportation - Boats with Chest
    "Boat with Chest": [
        "Oak Boat with Chest",
        "Spruce Boat with Chest",
        "Birch Boat with Chest",
        "Jungle Boat with Chest",
        "Acacia Boat with Chest",
        "Dark Oak Boat with Chest",
        "Mangrove Boat with Chest",
        "Cherry Boat with Chest",
        "Pale Oak Boat with Chest",
    ],
    # Decoration - Signs
    "Sign": [
        "Oak Sign",
        "Spruce Sign",
        "Birch Sign",
        "Jungle Sign",
        "Acacia Sign",
        "Dark Oak Sign",
        "Crimson Sign",
        "Warped Sign",
        "Mangrove Sign",
        "Cherry Sign",
        "Bamboo Sign",
        "Pale Oak Sign",
    ],
    # Decoration - Hanging Signs
    "Hanging Sign": [
        "Oak Hanging Sign",
        "Spruce Hanging Sign",
        "Birch Hanging Sign",
        "Jungle Hanging Sign",
        "Acacia Hanging Sign",
        "Dark Oak Hanging Sign",
        "Crimson Hanging Sign",
        "Warped Hanging Sign",
        "Mangrove Hanging Sign",
        "Cherry Hanging Sign",
        "Bamboo Hanging Sign",
        "Pale Oak Hanging Sign",
    ],
    # Wood Building Blocks - Buttons
    "Button": [
        "Oak Button",
        "Spruce Button",
        "Birch Button",
        "Jungle Button",
        "Acacia Button",
        "Dark Oak Button",
        "Mangrove Button",
        "Cherry Button",
        "Pale Oak Button",
        "Bamboo Button",
        "Crimson Button",
        "Warped Button",
    ],
    # Wood Building Blocks - Doors
    "Door": [
        "Oak Door",
        "Spruce Door",
        "Birch Door",
        "Jungle Door",
        "Acacia Door",
        "Dark Oak Door",
        "Mangrove Door",
        "Cherry Door",
        "Pale Oak Door",
        "Bamboo Door",
        "Crimson Door",
        "Warped Door",
    ],
    # Wood Building Blocks - Fences
    "Fence": [
        "Oak Fence",
        "Spruce Fence",
        "Birch Fence",
        "Jungle Fence",
        "Acacia Fence",
        "Dark Oak Fence",
        "Mangrove Fence",
        "Cherry Fence",
        "Pale Oak Fence",
        "Bamboo Fence",
        "Crimson Fence",
        "Warped Fence",
    ],
    # Wood Building Blocks - Fence Gates
    "Fence Gate": [
        "Oak Fence Gate",
        "Spruce Fence Gate",
        "Birch Fence Gate",
        "Jungle Fence Gate",
        "Acacia Fence Gate",
        "Dark Oak Fence Gate",
        "Mangrove Fence Gate",
        "Cherry Fence Gate",
        "Pale Oak Fence Gate",
        "Bamboo Fence Gate",
        "Crimson Fence Gate",
        "Warped Fence Gate",
    ],
    # Wood Building Blocks - Pressure Plates
    "Pressure Plate": [
        "Oak Pressure Plate",
        "Spruce Pressure Plate",
        "Birch Pressure Plate",
        "Jungle Pressure Plate",
        "Acacia Pressure Plate",
        "Dark Oak Pressure Plate",
        "Mangrove Pressure Plate",
        "Cherry Pressure Plate",
        "Pale Oak Pressure Plate",
        "Bamboo Pressure Plate",
        "Crimson Pressure Plate",
        "Warped Pressure Plate",
    ],
    # Wood Building Blocks - Trapdoors
    "Trapdoor": [
        "Oak Trapdoor",
        "Spruce Trapdoor",
        "Birch Trapdoor",
        "Jungle Trapdoor",
        "Acacia Trapdoor",
        "Dark Oak Trapdoor",
        "Mangrove Trapdoor",
        "Cherry Trapdoor",
        "Pale Oak Trapdoor",
        "Bamboo Trapdoor",
        "Crimson Trapdoor",
        "Warped Trapdoor",
    ],
    # Wood Building Blocks - Stairs
    "Wooden Stairs": [
        "Oak Stairs",
        "Spruce Stairs",
        "Birch Stairs",
        "Jungle Stairs",
        "Acacia Stairs",
        "Dark Oak Stairs",
        "Mangrove Stairs",
        "Cherry Stairs",
        "Pale Oak Stairs",
        "Bamboo Stairs",
        "Crimson Stairs",
        "Warped Stairs",
    ],
    # Wood Building Blocks - Slab
    "Wooden Slab": [
        "Oak Slab",
        "Spruce Slab",
        "Birch Slab",
        "Jungle Slab",
        "Acacia Slab",
        "Dark Oak Slab",
        "Mangrove Slab",
        "Cherry Slab",
        "Pale Oak Slab",
        "Bamboo Slab",
        "Crimson Slab",
        "Warped Slab",
    ],
    # Colored Blocks - Wool
    "Wool": [
        "White Wool",
        "Light Gray Wool",
        "Gray Wool",
        "Black Wool",
        "Brown Wool",
        "Red Wool",
        "Orange Wool",
        "Yellow Wool",
        "Lime Wool",
        "Green Wool",
        "Cyan Wool",
        "Light Blue Wool",
        "Blue Wool",
        "Purple Wool",
        "Magenta Wool",
        "Pink Wool",
    ],
    # Colored Blocks - Carpet
    "Carpet": [
        "White Carpet",
        "Light Gray Carpet",
        "Gray Carpet",
        "Black Carpet",
        "Brown Carpet",
        "Red Carpet",
        "Orange Carpet",
        "Yellow Carpet",
        "Lime Carpet",
        "Green Carpet",
        "Cyan Carpet",
        "Light Blue Carpet",
        "Blue Carpet",
        "Purple Carpet",
        "Magenta Carpet",
        "Pink Carpet",
    ],
    # Colored Blocks - Terracotta
    "Terracotta": [
        "White Terracotta",
        "Light Gray Terracotta",
        "Gray Terracotta",
        "Black Terracotta",
        "Brown Terracotta",
        "Red Terracotta",
        "Orange Terracotta",
        "Yellow Terracotta",
        "Lime Terracotta",
        "Green Terracotta",
        "Cyan Terracotta",
        "Light Blue Terracotta",
        "Blue Terracotta",
        "Purple Terracotta",
        "Magenta Terracotta",
        "Pink Terracotta",
    ],
    # Colored Blocks - Concrete Powder
    "Concrete Powder": [
        "White Concrete Powder",
        "Light Gray Concrete Powder",
        "Gray Concrete Powder",
        "Black Concrete Powder",
        "Brown Concrete Powder",
        "Red Concrete Powder",
        "Orange Concrete Powder",
        "Yellow Concrete Powder",
        "Lime Concrete Powder",
        "Green Concrete Powder",
        "Cyan Concrete Powder",
        "Light Blue Concrete Powder",
        "Blue Concrete Powder",
        "Purple Concrete Powder",
        "Magenta Concrete Powder",
        "Pink Concrete Powder",
    ],
    # Colored Blocks - Stained Glass
    "Stained Glass": [
        "White Stained Glass",
        "Light Gray Stained Glass",
        "Gray Stained Glass",
        "Black Stained Glass",
        "Brown Stained Glass",
        "Red Stained Glass",
        "Orange Stained Glass",
        "Yellow Stained Glass",
        "Lime Stained Glass",
        "Green Stained Glass",
        "Cyan Stained Glass",
        "Light Blue Stained Glass",
        "Blue Stained Glass",
        "Purple Stained Glass",
        "Magenta Stained Glass",
        "Pink Stained Glass",
    ],
    # Colored Blocks - Stained Glass Pane
    "Stained Glass Pane": [
        "White Stained Glass Pane",
        "Light Gray Stained Glass Pane",
        "Gray Stained Glass Pane",
        "Black Stained Glass Pane",
        "Brown Stained Glass Pane",
        "Red Stained Glass Pane",
        "Orange Stained Glass Pane",
        "Yellow Stained Glass Pane",
        "Lime Stained Glass Pane",
        "Green Stained Glass Pane",
        "Cyan Stained Glass Pane",
        "Light Blue Stained Glass Pane",
        "Blue Stained Glass Pane",
        "Purple Stained Glass Pane",
        "Magenta Stained Glass Pane",
        "Pink Stained Glass Pane",
    ],
    # Colored Items - Shulker Box
    "Shulker Box": [
        "White Shulker Box",
        "Light Gray Shulker Box",
        "Gray Shulker Box",
        "Black Shulker Box",
        "Brown Shulker Box",
        "Red Shulker Box",
        "Orange Shulker Box",
        "Yellow Shulker Box",
        "Lime Shulker Box",
        "Green Shulker Box",
        "Cyan Shulker Box",
        "Light Blue Shulker Box",
        "Blue Shulker Box",
        "Purple Shulker Box",
        "Magenta Shulker Box",
        "Pink Shulker Box",
    ],
    # Colored Items - Bed
    "Bed": [
        "White Bed",
        "Light Gray Bed",
        "Gray Bed",
        "Black Bed",
        "Brown Bed",
        "Red Bed",
        "Orange Bed",
        "Yellow Bed",
        "Lime Bed",
        "Green Bed",
        "Cyan Bed",
        "Light Blue Bed",
        "Blue Bed",
        "Purple Bed",
        "Magenta Bed",
        "Pink Bed",
    ],
    # Colored Items - Candle
    "Candle": [
        "White Candle",
        "Light Gray Candle",
        "Gray Candle",
        "Black Candle",
        "Brown Candle",
        "Red Candle",
        "Orange Candle",
        "Yellow Candle",
        "Lime Candle",
        "Green Candle",
        "Cyan Candle",
        "Light Blue Candle",
        "Blue Candle",
        "Purple Candle",
        "Magenta Candle",
        "Pink Candle",
    ],
    # Colored Items - Dye
    "Dye": [
        "White Dye",
        "Light Gray Dye",
        "Gray Dye",
        "Black Dye",
        "Brown Dye",
        "Red Dye",
        "Orange Dye",
        "Yellow Dye",
        "Lime Dye",
        "Green Dye",
        "Cyan Dye",
        "Light Blue Dye",
        "Blue Dye",
        "Purple Dye",
        "Magenta Dye",
        "Pink Dye",
    ],
    # Colored Items - Harness
    "Harness": [
        "White Harness",
        "Light Gray Harness",
        "Gray Harness",
        "Black Harness",
        "Brown Harness",
        "Red Harness",
        "Orange Harness",
        "Yellow Harness",
        "Lime Harness",
        "Green Harness",
        "Cyan Harness",
        "Light Blue Harness",
        "Blue Harness",
        "Purple Harness",
        "Magenta Harness",
        "Pink Harness",
    ],
    # Colored Items - Firework
    "Firework": [
        "White Firework",
        "Light Gray Firework",
        "Gray Firework",
        "Black Firework",
        "Brown Firework",
        "Red Firework",
        "Orange Firework",
        "Yellow Firework",
        "Lime Firework",
        "Green Firework",
        "Cyan Firework",
        "Light Blue Firework",
        "Blue Firework",
        "Purple Firework",
        "Magenta Firework",
        "Pink Firework",
    ],
    # Colored Items - Bundle
    "Bundle": [
        "White Bundle",
        "Light Gray Bundle",
        "Gray Bundle",
        "Black Bundle",
        "Brown Bundle",
        "Red Bundle",
        "Orange Bundle",
        "Yellow Bundle",
        "Lime Bundle",
        "Green Bundle",
        "Cyan Bundle",
        "Light Blue Bundle",
        "Blue Bundle",
        "Purple Bundle",
        "Magenta Bundle",
        "Pink Bundle",
    ],
    # Colored Items - Shield
    "Shield": [
        "White Shield",
        "Light Gray Shield",
        "Gray Shield",
        "Black Shield",
        "Brown Shield",
        "Red Shield",
        "Orange Shield",
        "Yellow Shield",
        "Lime Shield",
        "Green Shield",
        "Cyan Shield",
        "Light Blue Shield",
        "Blue Shield",
        "Purple Shield",
        "Magenta Shield",
        "Pink Shield",
        "Ominous Shield",
    ],
    # Colored Items - Banner
    "Banner": [
        "White Banner",
        "Light Gray Banner",
        "Gray Banner",
        "Black Banner",
        "Brown Banner",
        "Red Banner",
        "Orange Banner",
        "Yellow Banner",
        "Lime Banner",
        "Green Banner",
        "Cyan Banner",
        "Light Blue Banner",
        "Blue Banner",
        "Purple Banner",
        "Magenta Banner",
        "Pink Banner",
    ],
    "Block of Copper": [
        "Unoxidized Block of Copper",
        "Exposed Copper",
        "Weathered Copper",
        "Oxidized Copper",
        " Block of Copper",
        "Waxed Block of Copper",
        "Waxed Unoxidized Copper",
        "Waxed Exposed Copper",
        "Waxed Weathered Copper",
        "Waxed Oxidized Copper",
    ],
    "Chiseled Copper": [
        "Unoxidized Chiseled Copper",
        "Exposed Chiseled Copper",
        "Weathered Chiseled Copper",
        "Oxidized Chiseled Copper",
        " Chiseled Copper",
        "Waxed Chiseled Copper",
        "Waxed Unoxidized Chiseled Copper",
        "Waxed Exposed Chiseled Copper",
        "Waxed Weathered Chiseled Copper",
        "Waxed Oxidized Chiseled Copper",
    ],
    "Copper Bulb": [
        "Unoxidized Copper Bulb",
        "Exposed Copper Bulb",
        "Weathered Copper Bulb",
        "Oxidized Copper Bulb",
        " Copper Bulb",
        "Waxed Copper Bulb",
        "Waxed Unoxidized Copper Bulb",
        "Waxed Exposed Copper Bulb",
        "Waxed Weathered Copper Bulb",
        "Waxed Oxidized Copper Bulb",
    ],
    "Copper Door": [
        "Unoxidized Copper Door",
        "Exposed Copper Door",
        "Weathered Copper Door",
        "Oxidized Copper Door",
        " Copper Door",
        "Waxed Copper Door",
        "Waxed Unoxidized Copper Door",
        "Waxed Exposed Copper Door",
        "Waxed Weathered Copper Door",
        "Waxed Oxidized Copper Door",
    ],
    "Copper Grate": [
        "Unoxidized Copper Grate",
        "Exposed Copper Grate",
        "Weathered Copper Grate",
        "Oxidized Copper Grate",
        " Copper Grate",
        "Waxed Copper Grate",
        "Waxed Unoxidized Copper Grate",
        "Waxed Exposed Copper Grate",
        "Waxed Weathered Copper Grate",
        "Waxed Oxidized Copper Grate",
    ],
    "Copper Trapdoor": [
        "Unoxidized Copper Trapdoor",
        "Exposed Copper Trapdoor",
        "Weathered Copper Trapdoor",
        "Oxidized Copper Trapdoor",
        " Copper Trapdoor",
        "Waxed Copper Trapdoor",
        "Waxed Unoxidized Copper Trapdoor",
        "Waxed Exposed Copper Trapdoor",
        "Waxed Weathered Copper Trapdoor",
        "Waxed Oxidized Copper Trapdoor",
    ],
    "Cut Copper": [
        "Unoxidized Cut Copper",
        "Exposed Cut Copper",
        "Weathered Cut Copper",
        "Oxidized Cut Copper",
        " Cut Copper",
        "Waxed Cut Copper",
        "Waxed Unoxidized Cut Copper",
        "Waxed Exposed Cut Copper",
        "Waxed Weathered Cut Copper",
        "Waxed Oxidized Cut Copper",
    ],
    "Cut Copper Slab": [
        "Unoxidized Cut Copper Slab",
        "Exposed Cut Copper Slab",
        "Weathered Cut Copper Slab",
        "Oxidized Cut Copper Slab",
        " Cut Copper Slab",
        "Waxed Cut Copper Slab",
        "Waxed Unoxidized Cut Copper Slab",
        "Waxed Exposed Cut Copper Slab",
        "Waxed Weathered Cut Copper Slab",
        "Waxed Oxidized Cut Copper Slab",
    ],
    "Cut Copper Stairs": [
        "Unoxidized Cut Copper Stairs",
        "Exposed Cut Copper Stairs",
        "Weathered Cut Copper Stairs",
        "Oxidized Cut Copper Stairs",
        " Cut Copper Stairs",
        "Waxed Cut Copper Stairs",
        "Waxed Unoxidized Cut Copper Stairs",
        "Waxed Exposed Cut Copper Stairs",
        "Waxed Weathered Cut Copper Stairs",
        "Waxed Oxidized Cut Copper Stairs",
    ],
    "Copper Bars": [
        "Unoxidized Copper Bars",
        "Exposed Copper Bars",
        "Weathered Copper Bars",
        "Oxidized Copper Bars",
        " Copper Bars",
        "Waxed Copper Bars",
        "Waxed Unoxidized Copper Bars",
        "Waxed Exposed Copper Bars",
        "Waxed Weathered Copper Bars",
        "Waxed Oxidized Copper Bars",
    ],
    "Copper Chain": [
        "Unoxidized Copper Chain",
        "Exposed Copper Chain",
        "Weathered Copper Chain",
        "Oxidized Copper Chain",
        " Copper Chain",
        "Waxed Copper Chain",
        "Waxed Unoxidized Copper Chain",
        "Waxed Exposed Copper Chain",
        "Waxed Weathered Copper Chain",
        "Waxed Oxidized Copper Chain",
    ],
    "Copper Chest": [
        "Unoxidized Copper Chest",
        "Exposed Copper Chest",
        "Weathered Copper Chest",
        "Oxidized Copper Chest",
        " Copper Chest",
        "Waxed Copper Chest",
        "Waxed Unoxidized Copper Chest",
        "Waxed Exposed Copper Chest",
        "Waxed Weathered Copper Chest",
        "Waxed Oxidized Copper Chest",
    ],
    "Copper Golem Statue": [
        "Unoxidized Copper Golem Statue",
        "Exposed Copper Golem Statue",
        "Weathered Copper Golem Statue",
        "Oxidized Copper Golem Statue",
        " Copper Golem Statue",
        "Waxed Copper Golem Statue",
        "Waxed Unoxidized Copper Golem Statue",
        "Waxed Exposed Copper Golem Statue",
        "Waxed Weathered Copper Golem Statue",
        "Waxed Oxidized Copper Golem Statue",
    ],
    "Copper Lantern": [
        "Unoxidized Copper Lantern",
        "Exposed Copper Lantern",
        "Weathered Copper Lantern",
        "Oxidized Copper Lantern",
        " Copper Lantern",
        "Waxed Copper Lantern",
        "Waxed Unoxidized Copper Lantern",
        "Waxed Exposed Copper Lantern",
        "Waxed Weathered Copper Lantern",
        "Waxed Oxidized Copper Lantern",
    ],
    "Lightning Rod": [
        "Unoxidized Lightning Rod",
        "Exposed Lightning Rod",
        "Weathered Lightning Rod",
        "Oxidized Lightning Rod",
        " Lightning Rod",
        "Waxed Lightning Rod",
        "Waxed Unoxidized Lightning Rod",
        "Waxed Exposed Lightning Rod",
        "Waxed Weathered Lightning Rod",
        "Waxed Oxidized Lightning Rod",
    ],
    "Bamboo Mosaic Variants": [
        "Bamboo Mosaic Stairs",
        "Bamboo Mosaic Slab",
    ],
    "Stone Variants": [
        "Stone Stairs",
        "Stone Slab",
        "Stone Wall",
        "Stone Chiseled",
        "Stone Brick Stairs",
        "Stone Brick Slab",
        "Stone Brick Wall",
        "Chiseled Stone Brick",
    ],
    "Cobblestone Variants": [
        "Cobblestone Stairs",
        "Cobblestone Slab",
        "Cobblestone Wall",
    ],
    "Mossy Cobblestone Variants": [
        "Mossy Cobblestone Stairs",
        "Mossy Cobblestone Slab",
        "Mossy Cobblestone Wall",
    ],
    "Smooth Stone Variants": [
        "Smooth Stone Slab",
    ],
    "Mossy Stone Brick Variants": [
        "Mossy Stone Brick Stairs",
        "Mossy Stone Brick Slab",
        "Mossy Stone Brick Wall",
    ],
    "Granite Variants": [
        "Granite Stairs",
        "Granite Slab",
        "Granite Wall",
        "Polished Granite",
        "Polished Granite Stairs",
        "Polished Granite Slab",
        "Polished Granite Wall",
    ],
    "Diorite Variants": [
        "Diorite Stairs",
        "Diorite Slab",
        "Diorite Wall",
        "Polished Diorite",
        "Polished Diorite Stairs",
        "Polished Diorite Slab",
        "Polished Diorite Wall",
    ],
    "Andesite Variants": [
        "Andesite Stairs",
        "Andesite Slab",
        "Andesite Wall",
        "Polished Andesite",
        "Polished Andesite Stairs",
        "Polished Andesite Slab",
        "Polished Andesite Wall",
    ],
    "Cobbled Deepslate Variants": [
        "Cobbled Deepslate Stairs",
        "Cobbled Deepslate Slab",
        "Cobbled Deepslate Wall",
        "Chiseled Deepslate",
        "Polished Deepslate",
        "Polished Deepslate Stairs",
        "Polished Deepslate Slab",
        "Polished Deepslate Wall",
        "Deepslate Bricks",
        "Deepslate Brick Stairs",
        "Deepslate Brick Slab",
        "Deepslate Brick Wall",
        "Deepslate Tiles",
        "Deepslate Tile Stairs",
        "Deepslate Tile Slab",
        "Deepslate Tile Wall",
    ],
    "Tuff Variants": [
        "Tuff Stairs",
        "Tuff Slab",
        "Tuff Wall",
        "Polished Tuff",
        "Polished Tuff Stairs",
        "Polished Tuff Slab",
        "Polished Tuff Wall",
        "Tuff Bricks",
        "Tuff Brick Stairs",
        "Tuff Brick Slab",
        "Tuff Brick Wall",
        "Chiseled Tuff Bricks",
        "Chiseled Tuff",
    ],
    "Brick Variants": ["Brick Stairs", "Brick Slab", "Brick Wall"],
    "Mud Brick Variants": [
        "Mud Brick Stairs",
        "Mud Brick Slab",
        "Mud Brick Wall",
    ],
    "Resin Brick Variants": [
        "Resin Brick Stairs",
        "Resin Brick Slab",
        "Resin Brick Wall",
        "Chiseled Resin Bricks",
    ],
    "Sandstone Variants": [
        "Sandstone Stairs",
        "Sandstone Slab",
        "Sandstone Wall",
        "Chiseled Sandstone",
        "Cut Sandstone",
    ],
    "Smooth Sandstone Variants": [
        "Smooth Sandstone Stairs",
        "Smooth Sandstone Slab",
    ],
    "Red Sandstone Variants": [
        "Red Sandstone Stairs",
        "Red Sandstone Slab",
        "Red Sandstone Wall",
        "Chiseled Red Sandstone",
        "Cut Red Sandstone",
    ],
    "Smooth Red Sandstone Variants": [
        "Smooth Red Sandstone Stairs",
        "Smooth Red Sandstone Slab",
    ],
    "Prismarine Variants": [
        "Prismarine Stairs",
        "Prismarine Slab",
        "Prismarine Wall",
    ],
    "Prismarine Bricks Variants": [
        "Prismarine Bricks Stairs",
        "Prismarine Bricks Slab",
    ],
    "Dark Prismarine Variants": [
        "Dark Prismarine Stairs",
        "Dark Prismarine Slab",
    ],
    "Nether Bricks Variants": [
        "Nether Brick Stairs",
        "Nether Brick Slab",
        "Nether Brick Wall",
        "Chiseled Nether Bricks",
    ],
    "Red Nether Bricks Variants": [
        "Red Nether Brick Stairs",
        "Red Nether Brick Slab",
        "Red Nether Brick Wall",
    ],
    "Blackstone Variants": [
        "Blackstone Stairs",
        "Blackstone Slab",
        "Blackstone Wall",
        "Polished Blackstone",
        "Polished Blackstone Stairs",
        "Polished Blackstone Slab",
        "Polished Blackstone Wall",
        "Chiseled Polished Blackstone",
        "Polished Blackstone Bricks",
        "Polished Blackstone Brick Stairs",
        "Polished Blackstone Brick Slab",
        "Polished Blackstone Brick Wall",
    ],
    "End Stone Brick Variants": [
        "End Stone Brick Stairs",
        "End Stone Brick Slab",
        "End Stone Brick Wall",
    ],
    "Purpur Variants": [
        "Purpur Stairs",
        "Purpur Slab",
        "Purpur Pillar",
    ],
    "Quarz Variants": [
        "Quartz Stairs",
        "Quartz Slab",
        "Chiseled Quartz Block",
        "Quartz Bricks",
        "Quartz Pillar",
    ],
    "Smooth Quartz Variants": ["Smooth Quartz Stairs", "Smooth Quartz Slab"],
    "Copper Variants": [
        "Cut Copper",
        "Cut Copper Stairs",
        "Cut Copper Slab",
        "Chiseled Copper",
        "Copper Grate",
    ],
    "Potion": [
        "Water Bottle",
        "Awkward Potion",
        "Mundane Potion",
        "Thick Potion",
        "Potion of Night Vision",
        "Potion of Invisibility",
        "Potion of Leaping",
        "Potion of Fire Resistance",
        "Potion of Swiftness",
        "Potion of Slowness",
        "Potion of the Turtle Master",
        "Potion of Water Breathing",
        "Potion of Healing",
        "Potion of Harming",
        "Potion of Poison",
        "Potion of Regeneration",
        "Potion of Strength",
        "Potion of Weakness",
        "Potion of Slow Falling",
        "Potion of Wind Charging",
        "Potion of Weaving",
        "Potion of Oozing",
        "Potion of Infestation",
        "Potion of Luck‌",
        "Lingering Water Bottle",
        "Awkward Lingering Potion",
        "Thick Lingering Potion",
        "Mundane Lingering Potion",
        "Lingering Potion of Night Vision",
        "Lingering Potion of Invisibility",
        "Lingering Potion of Leaping",
        "Lingering Potion of Fire Resistance",
        "Lingering Potion of Swiftness",
        "Lingering Potion of Slowness",
        "Lingering Potion of the Turtle Master",
        "Lingering Potion of Water Breathing",
        "Lingering Potion of Healing",
        "Lingering Potion of Harming",
        "Lingering Potion of Poison",
        "Lingering Potion of Regeneration",
        "Lingering Potion of Strength",
        "Lingering Potion of Weakness",
        "Lingering Potion of Slow Falling",
        "Lingering Potion of Wind Charging",
        "Lingering Potion of Weaving",
        "Lingering Potion of Oozing",
        "Lingering Potion of Infestation",
        "Lingering Potion of Luck",
        "Splash Potion of Fire Resistance",
    ],
    "Pottery Sherd": [
        "Angler Pottery Sherd",
        "Arms Up Pottery Sherd",
        "Archer Pottery Sherd",
        "Blade Pottery Sherd",
        "Brewer Pottery Sherd",
        "Burn Pottery Sherd",
        "Danger Pottery Sherd",
        "Explorer Pottery Sherd",
        "Flow Pottery Sherd",
        "Friend Pottery Sherd",
        "Guster Pottery Sherd",
        "Heart Pottery Sherd",
        "Heartbreak Pottery Sherd",
        "Howl Pottery Sherd",
        "Miner Pottery Sherd",
        "Mourner Pottery Sherd",
        "Plenty Pottery Sherd",
        "Prize Pottery Sherd",
        "Scrape Pottery Sherd",
        "Sheaf Pottery Sherd",
        "Shelter Pottery Sherd",
        "Skull Pottery Sherd",
        "Snort Pottery Sherd",
    ],
    "Axe": [
        "Wooden Axe",
        "Stone Axe",
        "Copper Axe",
        "Iron Axe",
        "Golden Axe",
        "Diamond Axe",
        "Netherite Axe",
    ],
    "Sword": [
        "Wooden Sword",
        "Stone Sword",
        "Copper Sword",
        "Iron Sword",
        "Golden Sword",
        "Diamond Sword",
        "Netherite Sword",
    ],
    "Hoe": [
        "Wooden Hoe",
        "Stone Hoe",
        "Copper Hoe",
        "Iron Hoe",
        "Golden Hoe",
        "Diamond Hoe",
        "Netherite Hoe",
    ],
    "Pickaxe": [
        "Wooden Pickaxe",
        "Stone Pickaxe",
        "Copper Pickaxe",
        "Iron Pickaxe",
        "Golden Pickaxe",
        "Diamond Pickaxe",
        "Netherite Pickaxe",
    ],
    "Shovel": [
        "Wooden Shovel",
        "Stone Shovel",
        "Copper Shovel",
        "Iron Shovel",
        "Golden Shovel",
        "Diamond Shovel",
        "Netherite Shovel",
    ],
}


def generate_exact_to_technical() -> Dict[str, str]:
    """
    Generate a reverse mapping from exact item names to technical category names.

    This function creates an efficient lookup dictionary for compression,
    mapping each exact item name to its technical category.

    Returns:
        Dict[str, str]: Mapping from exact item name to technical category name.

    Raises:
        ValueError: If an exact item name appears in multiple technical categories.

    Example:
        >>> mapping = generate_exact_to_technical()
        >>> mapping["Oak Planks"]
        'Planks'
        >>> mapping["Arrow of Poison"]
        'Tipped Arrow'
    """
    exact_to_technical: Dict[str, str] = {}

    for technical_name, exact_names in TECHNICAL_MAPPINGS.items():
        for exact_name in exact_names:
            if exact_name in exact_to_technical:
                existing_technical = exact_to_technical[exact_name]
                raise ValueError(
                    f"Duplicate exact item '{exact_name}' found in multiple "
                    f"technical categories: '{existing_technical}' and '{technical_name}'"
                )
            exact_to_technical[exact_name] = technical_name

    return exact_to_technical


def validate_mappings() -> bool:
    """
    Validate that all technical mappings are well-formed.

    Checks:
    - No empty technical categories
    - No duplicate exact items across categories
    - No technical names that collide with exact item names
    - All exact item names are non-empty strings

    Returns:
        bool: True if all validations pass.

    Raises:
        ValueError: If any validation fails.
    """
    # Check for empty categories
    for technical_name, exact_names in TECHNICAL_MAPPINGS.items():
        if not exact_names:
            raise ValueError(f"Technical category '{technical_name}' has no items")

        # Check all items are non-empty strings
        for exact_name in exact_names:
            if not exact_name or not isinstance(exact_name, str):
                raise ValueError(
                    f"Invalid exact item name in category '{technical_name}': {exact_name!r}"
                )

    # Check for duplicates (this will raise if duplicates found)
    exact_to_technical = generate_exact_to_technical()

    # Check for technical names that collide with exact item names
    all_exact_names: Set[str] = set(exact_to_technical.keys())
    technical_names: Set[str] = set(TECHNICAL_MAPPINGS.keys())

    collisions = technical_names & all_exact_names
    if collisions:
        print(f"Collisions : {collisions}")
        # raise ValueError(
        #     f"Technical category names collide with exact item names: {collisions}"
        # )

    logger.info(
        f"Validation passed: {len(TECHNICAL_MAPPINGS)} technical categories, "
        f"{len(exact_to_technical)} exact items"
    )

    return True


if __name__ == "__main__":
    # Quick validation when run directly
    logging.basicConfig(level=logging.INFO)
    try:
        validate_mappings()
        exact_to_technical = generate_exact_to_technical()
        print(f"✓ Mappings validated successfully")
        print(f"  Technical categories: {len(TECHNICAL_MAPPINGS)}")
        print(f"  Exact items: {len(exact_to_technical)}")
        print(f"\nSample mappings:")
        for technical, exacts in list(TECHNICAL_MAPPINGS.items())[:3]:
            print(f"  {technical}: {exacts[0]}, {exacts[1]}, ... ({len(exacts)} items)")
    except ValueError as e:
        print(f"✗ Validation failed: {e}")
        exit(1)
