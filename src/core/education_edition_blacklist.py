"""Blacklist of Minecraft Education Edition items to filter out."""

# Education Edition chemistry items and special content
# These items should not appear in Java Edition transformation data
EDUCATION_EDITION_ITEMS = {
    # Chlorides
    "Cerium Chloride",
    "Mercuric Chloride",
    "Potassium Chloride",
    "Tungsten Chloride",

    # Elements
    "Aluminum",
    "Argon",
    "Barium",
    "Beryllium",
    "Bismuth",
    "Boron",
    "Bromine",
    "Cadmium",
    "Calcium",
    "Carbon",
    "Cerium",
    "Cesium",
    "Chlorine",
    "Chromium",
    "Cobalt",
    "Copper",  # Note: Be careful - there is Java Edition copper
    "Fluorine",
    "Gadolinium",
    "Gallium",
    "Germanium",
    "Helium",
    "Hydrogen",
    "Iodine",
    "Krypton",
    "Lanthanum",
    "Lithium",
    "Magnesium",
    "Mercury",
    "Neon",
    "Nickel",
    "Nitrogen",
    "Oxygen",
    "Phosphorus",
    "Polonium",
    "Potassium",
    "Radon",
    "Rubidium",
    "Scandium",
    "Selenium",
    "Silicon",
    "Silver",
    "Sodium",
    "Strontium",
    "Sulfur",
    "Tantalum",
    "Tellurium",
    "Tin",
    "Titanium",
    "Tungsten",
    "Uranium",
    "Xenon",
    "Yttrium",
    "Zinc",

    # Compounds
    "Ammonia",
    "Barium Sulfate",
    "Benzene",
    "Boron Trioxide",
    "Calcium Bromide",
    "Calcium Chloride",
    "Crude Oil",
    "Glue",
    "Hydrogen Peroxide",
    "Ice Bomb",
    # "Ink Sac" removed - Java Edition has this as a mob drop from squids
    "Iron Sulfide",
    "Latex",
    "Lithium Hydride",
    "Magnesium Nitrate",
    "Magnesium Oxide",
    "Polyethylene",
    "Potassium Iodide",
    "Salt",
    "Soap",
    "Sodium Acetate",
    "Sodium Fluoride",
    "Sodium Hydride",
    "Sodium Hypochlorite",
    "Sodium Oxide",
    "Sugar",  # Note: Java Edition has sugar, but Education has chemistry version
    "Sulfate",
    "Water",  # Note: Education Edition has chemistry water item

    # Colored torches (Education Edition only)
    "Blue Torch",
    "Red Torch",
    "Purple Torch",
    "Green Torch",

    # Sparklers
    "Blue Sparkler",
    "Red Sparkler",
    "Purple Sparkler",
    "Green Sparkler",
    "Orange Sparkler",
    "White Sparkler",

    # Glowsticks
    "Blue Glow Stick",
    "Red Glow Stick",
    "Purple Glow Stick",
    "Green Glow Stick",
    "Orange Glow Stick",
    "White Glow Stick",
    "Yellow Glow Stick",

    # Balloons
    "White Balloon",
    "Orange Balloon",
    "Magenta Balloon",
    "Light Blue Balloon",
    "Yellow Balloon",
    "Lime Balloon",
    "Pink Balloon",
    "Gray Balloon",
    "Light Gray Balloon",
    "Cyan Balloon",
    "Purple Balloon",
    "Blue Balloon",
    "Brown Balloon",
    "Green Balloon",
    "Red Balloon",
    "Black Balloon",

    # Other Education Edition items
    "Bleach",
    "Heat Block",
    "Super Fertilizer",
    "Hardened Glass",
    "Hardened Glass Pane",
    "Hardened Stained Glass",
    "Hardened Stained Glass Pane",
    "Colored Torch",
    "Underwater Torch",
    "Underwater TNT",
    "Element Constructor",
    "Compound Creator",
    "Material Reducer",
    "Lab Table",
    "Portfolio",
    "Chalkboard",
    "Poster",
    "Slate",
    "Allow",
    "Deny",
    "Border",
    "Camera",
    "NPC",
}

# Items that should NOT be blacklisted (Java Edition items with similar names)
# This is a safety list to prevent false positives
JAVA_EDITION_ITEMS_TO_KEEP = {
    "Copper Ingot",
    "Copper Block",
    "Copper Ore",
    "Raw Copper",
    "Sugar Cane",
    "Sugar",  # Actually, Java has sugar from sugar cane
    "Ice",
    "Packed Ice",
    "Blue Ice",
}


def is_education_edition_item(item_name: str) -> bool:
    """
    Check if an item is from Minecraft Education Edition.

    Args:
        item_name: Name of the item to check

    Returns:
        True if the item is Education Edition only, False otherwise
    """
    # First check if it's explicitly a Java Edition item
    if item_name in JAVA_EDITION_ITEMS_TO_KEEP:
        return False

    # Then check against blacklist
    return item_name in EDUCATION_EDITION_ITEMS
