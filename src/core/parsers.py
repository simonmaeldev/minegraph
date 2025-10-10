"""HTML parsers for extracting Minecraft transformation data."""

import re
from typing import List, Optional
from bs4 import BeautifulSoup, Tag
from .data_models import Item, Transformation, TransformationType


def is_java_edition(element: Tag) -> bool:
    """
    Check if element is Java Edition content (filters out Bedrock/Education).

    Args:
        element: BeautifulSoup Tag to check

    Returns:
        True if element is Java Edition or unspecified (default Java)
    """
    # Get text content of element and parents
    text = element.get_text().lower()

    # Exclude Bedrock and Education edition content
    if "bedrock" in text or "education" in text:
        return False

    # Check for explicit edition markers in parent sections
    parent = element.find_parent(["section", "div"])
    if parent:
        parent_text = parent.get_text().lower()
        if "bedrock edition" in parent_text and "java edition" not in parent_text:
            return False

    # Check sibling table cells in the same table row for edition markers
    # This catches cases where edition markers are in description columns
    table_row = element.find_parent("tr")
    if table_row:
        # Get all table cells in this row
        cells = table_row.find_all("td")
        for cell in cells:
            cell_text = cell.get_text().lower()
            # Check if this cell contains Bedrock/Education edition markers
            # Look for both "bedrock" and "education" together
            if ("bedrock edition" in cell_text or "bedrock" in cell_text) and \
               ("education" in cell_text or "minecraft education" in cell_text):
                return False

    return True


def extract_item_from_link(link_tag: Tag) -> Optional[Item]:
    """
    Extract Item from <a> tag with /w/ href.

    Args:
        link_tag: BeautifulSoup Tag representing an <a> element

    Returns:
        Item object or None if link is invalid
    """
    if not link_tag or link_tag.name != "a":
        return None

    href = link_tag.get("href", "")
    if not href or not href.startswith("/w/"):
        return None

    # Extract name from href (remove /w/ prefix and decode underscores)
    name = href[3:].replace("_", " ")

    # Try to get cleaner name from title attribute
    title = link_tag.get("title", "")
    if title:
        name = title

    # Construct full URL
    url = f"https://minecraft.wiki{href}"

    return Item(name=name, url=url)


def parse_quantity(text: str) -> int:
    """
    Parse quantity from text like "15 × Item" or "15".

    Args:
        text: Text containing quantity

    Returns:
        Parsed quantity or 1 as default
    """
    # Look for pattern "number ×" or just "number"
    match = re.search(r"(\d+)\s*[×x]", text)
    if match:
        return int(match.group(1))

    # Try to find standalone number at start
    match = re.match(r"(\d+)", text.strip())
    if match:
        return int(match.group(1))

    return 1


def find_item_in_slot(slot: Tag) -> List[Item]:
    """
    Find all items in an inventory slot (handles animated alternatives).

    Args:
        slot: BeautifulSoup Tag representing an invslot

    Returns:
        List of Items found in the slot
    """
    items: List[Item] = []

    # Find all item containers in this slot
    item_containers = slot.find_all("span", class_="invslot-item")

    for container in item_containers:
        # Look for link to item
        link = container.find("a", href=re.compile(r"^/w/"))
        if link:
            item = extract_item_from_link(link)
            if item:
                items.append(item)

    return items


def parse_crafting(html_content: str) -> List[Transformation]:
    """
    Parse crafting recipes from HTML content.

    Args:
        html_content: HTML content from crafting wiki page

    Returns:
        List of Transformation objects for crafting recipes (deduplicated)
    """
    soup = BeautifulSoup(html_content, "lxml")
    transformations: List[Transformation] = []
    seen_signatures = set()

    # Find all crafting table UI elements
    crafting_uis = soup.find_all("span", class_=re.compile(r"mcui.*Crafting.*Table"))

    for ui in crafting_uis:
        if not is_java_edition(ui):
            continue

        # Extract inputs from mcui-input section
        input_section = ui.find("span", class_="mcui-input")
        if not input_section:
            continue

        # Collect all input items
        input_items: List[Item] = []
        slots = input_section.find_all("span", class_="invslot")

        # Track if any slot has alternatives
        has_alternatives = False
        alternative_slots: List[List[Item]] = []

        for slot in slots:
            items_in_slot = find_item_in_slot(slot)
            if items_in_slot:
                if len(items_in_slot) > 1:
                    has_alternatives = True
                    alternative_slots.append(items_in_slot)
                else:
                    input_items.append(items_in_slot[0])

        # Extract output from mcui-output section
        output_section = ui.find("span", class_="mcui-output")
        if not output_section:
            continue

        output_items = find_item_in_slot(output_section)
        if not output_items:
            continue

        # If there are alternatives, create separate transformations for each
        if has_alternatives and alternative_slots:
            # Check if output also has alternatives (multiple items in output slot)
            has_output_alternatives = len(output_items) > 1

            # Check if all alternative slots have the same count (for pairing)
            all_counts_match = len(set(len(slot) for slot in alternative_slots)) == 1
            first_slot_count = len(alternative_slots[0])

            # Check if output count matches any alternative slot count (for guided pairing)
            output_count = len(output_items)
            output_matches_slot = has_output_alternatives and any(
                len(slot) == output_count for slot in alternative_slots
            )

            # When multiple alternative slots exist and output provides guidance OR counts match
            # Example: [wool colors] + [dye colors] → pairs like (white wool, white dye)
            # Also handles: [17 shulker boxes] + [16 dyes] → 16 outputs (use output count as guide)
            if len(alternative_slots) >= 2 and (all_counts_match or output_matches_slot):
                # When output provides guidance, iterate by output items to ensure correct pairing
                if has_output_alternatives and output_matches_slot:
                    for output_idx, output_item in enumerate(output_items):
                        # For each alternative slot, find the matching item by index
                        # If a slot has fewer items than output, use modulo; if more, try to find match
                        paired_inputs = []
                        for slot in alternative_slots:
                            if len(slot) == len(output_items):
                                # Exact match: use same index
                                paired_inputs.append(slot[output_idx])
                            elif len(slot) > len(output_items):
                                # Slot has extra items: try to find item matching output by name
                                # or use offset index (skip first items that don't match pattern)
                                matching_item = None
                                for item in slot:
                                    if item.name == output_item.name:
                                        matching_item = item
                                        break
                                if matching_item:
                                    paired_inputs.append(matching_item)
                                else:
                                    # Fallback: use index+1 to skip potential base item at index 0
                                    idx = min(output_idx + 1, len(slot) - 1)
                                    paired_inputs.append(slot[idx])
                            else:
                                # Slot has fewer items: cycle using modulo
                                paired_inputs.append(slot[output_idx % len(slot)])

                        transformation = Transformation(
                            transformation_type=TransformationType.CRAFTING,
                            inputs=input_items + paired_inputs,
                            outputs=[output_item],
                            metadata={"has_alternatives": True},
                        )
                        sig = transformation.get_signature()
                        if sig not in seen_signatures:
                            seen_signatures.add(sig)
                            transformations.append(transformation)
                else:
                    # All counts match: simple zip pairing
                    for alt_items_tuple in zip(*alternative_slots):
                        all_inputs = input_items + list(alt_items_tuple)

                        # Determine output by index
                        if has_output_alternatives and first_slot_count == len(output_items):
                            output_idx = alternative_slots[0].index(alt_items_tuple[0])
                            output = [output_items[output_idx]]
                        else:
                            output = [output_items[0]]

                        transformation = Transformation(
                            transformation_type=TransformationType.CRAFTING,
                            inputs=all_inputs,
                            outputs=output,
                            metadata={"has_alternatives": True},
                        )
                        sig = transformation.get_signature()
                        if sig not in seen_signatures:
                            seen_signatures.add(sig)
                            transformations.append(transformation)
            # When both input and output have same number of alternatives, pair them by index
            elif has_output_alternatives and first_slot_count == len(output_items):
                for i, alt_item in enumerate(alternative_slots[0]):
                    all_inputs = input_items + [alt_item]
                    transformation = Transformation(
                        transformation_type=TransformationType.CRAFTING,
                        inputs=all_inputs,
                        outputs=[output_items[i]],  # Match by index
                        metadata={"has_alternatives": True},
                    )
                    # Only add if not seen before
                    sig = transformation.get_signature()
                    if sig not in seen_signatures:
                        seen_signatures.add(sig)
                        transformations.append(transformation)
            else:
                # Input has alternatives but output is single or different count
                # Create one transformation per input alternative with same output
                for alt_item in alternative_slots[0]:
                    all_inputs = input_items + [alt_item]
                    transformation = Transformation(
                        transformation_type=TransformationType.CRAFTING,
                        inputs=all_inputs,
                        outputs=[output_items[0]],  # Use first (only) output
                        metadata={"has_alternatives": True},
                    )
                    # Only add if not seen before
                    sig = transformation.get_signature()
                    if sig not in seen_signatures:
                        seen_signatures.add(sig)
                        transformations.append(transformation)
        elif input_items:
            transformation = Transformation(
                transformation_type=TransformationType.CRAFTING,
                inputs=input_items,
                outputs=[output_items[0]],  # Always use single output
            )
            # Only add if not seen before
            sig = transformation.get_signature()
            if sig not in seen_signatures:
                seen_signatures.add(sig)
                transformations.append(transformation)

    return transformations


def parse_smelting(html_content: str) -> List[Transformation]:
    """
    Parse smelting recipes from HTML content.

    Args:
        html_content: HTML content from smelting wiki page

    Returns:
        List of Transformation objects for smelting recipes
    """
    soup = BeautifulSoup(html_content, "lxml")
    transformations: List[Transformation] = []

    # Map furnace types to transformation types
    furnace_types = {
        "Furnace": TransformationType.SMELTING,
        "Blast_Furnace": TransformationType.BLAST_FURNACE,
        "Smoker": TransformationType.SMOKER,
    }

    for furnace_name, trans_type in furnace_types.items():
        furnace_uis = soup.find_all("span", class_=re.compile(f"mcui.*{furnace_name}"))

        for ui in furnace_uis:
            if not is_java_edition(ui):
                continue

            # Find input slot (ingredient)
            input_slots = ui.find_all("span", class_=re.compile(r"mcui-input|invslot"))

            input_items: List[Item] = []
            for slot in input_slots:
                # Skip fuel slots
                if "fuel" in slot.get("class", []):
                    continue

                items = find_item_in_slot(slot)
                if items:
                    input_items.extend(items)

            # Find output slot
            output_section = ui.find("span", class_="mcui-output")
            if not output_section:
                continue

            output_items = find_item_in_slot(output_section)

            if input_items and output_items:
                transformations.append(
                    Transformation(
                        transformation_type=trans_type,
                        inputs=input_items[:1],  # Single input for smelting
                        outputs=output_items[:1],  # Single output
                    )
                )

    return transformations


def parse_smithing(html_content: str) -> List[Transformation]:
    """
    Parse smithing recipes from HTML content.

    Args:
        html_content: HTML content from smithing wiki page

    Returns:
        List of Transformation objects for smithing recipes (deduplicated)
    """
    soup = BeautifulSoup(html_content, "lxml")
    transformations: List[Transformation] = []
    seen_signatures = set()

    # Find all smithing table UI elements
    smithing_uis = soup.find_all("span", class_=re.compile(r"mcui.*Smithing.*Table"))

    for ui in smithing_uis:
        if not is_java_edition(ui):
            continue

        # Extract three inputs: template, base, material
        input1 = ui.find("span", class_="mcui-input1")  # Template
        input2 = ui.find("span", class_="mcui-input2")  # Base item
        input3 = ui.find("span", class_="mcui-input3")  # Material

        inputs: List[Item] = []

        for input_slot in [input1, input2, input3]:
            if input_slot:
                items = find_item_in_slot(input_slot)
                if items:
                    inputs.extend(items)

        # Extract output
        output_section = ui.find("span", class_="mcui-output")
        if not output_section:
            continue

        output_items = find_item_in_slot(output_section)

        if len(inputs) >= 2 and output_items:  # At least 2 inputs required
            transformation = Transformation(
                transformation_type=TransformationType.SMITHING,
                inputs=inputs,
                outputs=[output_items[0]],  # Always use single output
            )
            # Only add if not seen before
            sig = transformation.get_signature()
            if sig not in seen_signatures:
                seen_signatures.add(sig)
                transformations.append(transformation)

    return transformations


def parse_stonecutter(html_content: str) -> List[Transformation]:
    """
    Parse stonecutter recipes from HTML content.

    Args:
        html_content: HTML content from stonecutter wiki page

    Returns:
        List of Transformation objects for stonecutter recipes (deduplicated)
    """
    soup = BeautifulSoup(html_content, "lxml")
    transformations: List[Transformation] = []
    seen_signatures = set()

    # Find stonecutter UI elements
    stonecutter_uis = soup.find_all("span", class_=re.compile(r"mcui.*Stonecutter"))

    for ui in stonecutter_uis:
        if not is_java_edition(ui):
            continue

        # Extract input
        input_section = ui.find("span", class_="mcui-input")
        if not input_section:
            continue

        input_items = find_item_in_slot(input_section)

        # Extract output
        output_section = ui.find("span", class_="mcui-output")
        if not output_section:
            continue

        output_items = find_item_in_slot(output_section)

        if input_items and output_items:
            # Stonecutter can have multiple outputs (different items from same input)
            # Create separate transformation for each output
            for output_item in output_items:
                transformation = Transformation(
                    transformation_type=TransformationType.STONECUTTER,
                    inputs=input_items,
                    outputs=[output_item],  # Single output per transformation
                )
                # Only add if not seen before
                sig = transformation.get_signature()
                if sig not in seen_signatures:
                    seen_signatures.add(sig)
                    transformations.append(transformation)

    return transformations


def parse_trading(html_content: str) -> List[Transformation]:
    """
    Parse trading recipes from HTML content.

    Args:
        html_content: HTML content from trading wiki page

    Returns:
        List of Transformation objects for trading recipes
    """
    soup = BeautifulSoup(html_content, "lxml")
    transformations: List[Transformation] = []

    # Find all trading tables
    tables = soup.find_all("table", class_="wikitable")

    for table in tables:
        if not is_java_edition(table):
            continue

        # Try to find villager type from data attribute or context
        villager_type = table.get("data-description", "Unknown")

        # Find header row to identify columns
        header_row = table.find("tr")
        if not header_row:
            continue

        headers = [th.get_text(strip=True) for th in header_row.find_all("th")]

        # Find "Item wanted" and "Item given" column indices
        try:
            wanted_idx = headers.index("Item wanted")
            given_idx = headers.index("Item given")
        except ValueError:
            # Try alternative column names
            try:
                wanted_idx = next(
                    i for i, h in enumerate(headers) if "wanted" in h.lower()
                )
                given_idx = next(
                    i for i, h in enumerate(headers) if "given" in h.lower()
                )
            except StopIteration:
                continue

        # Parse data rows
        data_rows = table.find_all("tr")[1:]  # Skip header

        for row in data_rows:
            cells = row.find_all("td")
            if len(cells) <= max(wanted_idx, given_idx):
                continue

            # Extract input items (wanted)
            wanted_cell = cells[wanted_idx]
            input_items: List[Item] = []

            # Parse items from cell
            links = wanted_cell.find_all("a", href=re.compile(r"^/w/"))
            for link in links:
                item = extract_item_from_link(link)
                if item:
                    # Check for quantity
                    text = wanted_cell.get_text()
                    quantity = parse_quantity(text)
                    # Add item multiple times for quantity (simplified)
                    for _ in range(min(quantity, 1)):  # Just once for graph
                        input_items.append(item)

            # Extract output items (given)
            given_cell = cells[given_idx]
            output_items: List[Item] = []

            links = given_cell.find_all("a", href=re.compile(r"^/w/"))
            for link in links:
                item = extract_item_from_link(link)
                if item:
                    output_items.append(item)

            if input_items and output_items:
                # Try to get level from first column
                level = "Unknown"
                if len(cells) > 0:
                    level = cells[0].get_text(strip=True)

                transformations.append(
                    Transformation(
                        transformation_type=TransformationType.TRADING,
                        inputs=input_items,
                        outputs=[output_items[0]],  # Always use single output
                        metadata={
                            "villager_type": villager_type,
                            "level": level,
                        },
                    )
                )

    return transformations


def parse_mob_drops(html_content: str, mob_name: str) -> List[Transformation]:
    """
    Parse mob drop data from HTML content.

    Args:
        html_content: HTML content from mob wiki page
        mob_name: Name of the mob

    Returns:
        List of Transformation objects for mob drops (deduplicated)
    """
    soup = BeautifulSoup(html_content, "lxml")
    transformations: List[Transformation] = []
    seen_signatures = set()

    # Find "Drops" section
    drops_section = soup.find(id="Drops")
    if not drops_section:
        # Try finding h2/h3 with "Drops" text
        for heading in soup.find_all(["h2", "h3"]):
            if "drops" in heading.get_text().lower():
                drops_section = heading
                break

    if not drops_section:
        return transformations

    # Find table after drops section
    table = drops_section.find_next("table", class_="wikitable")
    if not table:
        return transformations

    if not is_java_edition(table):
        return transformations

    # Create virtual mob item
    mob_item = Item(name=mob_name, url=f"https://minecraft.wiki/w/{mob_name.replace(' ', '_')}")

    # Parse drop table
    rows = table.find_all("tr")[1:]  # Skip header

    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 2:
            continue

        # First cell usually contains item
        item_cell = cells[0]
        links = item_cell.find_all("a", href=re.compile(r"^/w/"))

        for link in links:
            item = extract_item_from_link(link)
            if item:
                # Try to extract probability if present
                probability = 1.0
                if len(cells) > 2:
                    prob_text = cells[2].get_text(strip=True)
                    if "%" in prob_text:
                        try:
                            probability = float(prob_text.replace("%", "")) / 100.0
                        except ValueError:
                            pass

                transformation = Transformation(
                    transformation_type=TransformationType.MOB_DROP,
                    inputs=[mob_item],
                    outputs=[item],
                    metadata={"probability": probability},
                )
                # Only add if not seen before
                sig = transformation.get_signature()
                if sig not in seen_signatures:
                    seen_signatures.add(sig)
                    transformations.append(transformation)

    return transformations


def parse_brewing(html_content: str) -> List[Transformation]:
    """
    Parse brewing recipes from HTML content.

    Args:
        html_content: HTML content from brewing wiki page

    Returns:
        List of Transformation objects for brewing recipes (deduplicated)
    """
    soup = BeautifulSoup(html_content, "lxml")
    transformations: List[Transformation] = []
    seen_signatures = set()

    # Find brewing stand UI elements
    brewing_uis = soup.find_all("span", class_=re.compile(r"mcui.*Brewing.*Stand"))

    for ui in brewing_uis:
        if not is_java_edition(ui):
            continue

        # Extract base potion (bottom slot)
        base_slot = ui.find("span", class_=re.compile(r"mcui-input.*base"))
        if not base_slot:
            # Try finding any input slot
            base_slot = ui.find("span", class_="mcui-input")

        base_items: List[Item] = []
        if base_slot:
            base_items = find_item_in_slot(base_slot)

        # Extract ingredient (top slot)
        ingredient_slot = ui.find("span", class_=re.compile(r"mcui-input.*ingredient"))
        ingredient_items: List[Item] = []
        if ingredient_slot:
            ingredient_items = find_item_in_slot(ingredient_slot)

        # Extract output
        output_section = ui.find("span", class_="mcui-output")
        if not output_section:
            continue

        output_items = find_item_in_slot(output_section)

        # Combine base + ingredient as inputs
        all_inputs = base_items + ingredient_items

        if all_inputs and output_items:
            transformation = Transformation(
                transformation_type=TransformationType.BREWING,
                inputs=all_inputs,
                outputs=[output_items[0]],  # Always use single output
            )
            # Only add if not seen before
            sig = transformation.get_signature()
            if sig not in seen_signatures:
                seen_signatures.add(sig)
                transformations.append(transformation)

    return transformations


def parse_composting(html_content: str) -> List[Transformation]:
    """
    Parse composting recipes from HTML content.

    Args:
        html_content: HTML content from composter wiki page

    Returns:
        List of Transformation objects for composting recipes (deduplicated)
    """
    soup = BeautifulSoup(html_content, "lxml")
    transformations: List[Transformation] = []
    seen_signatures = set()

    # Find composting tables
    tables = soup.find_all("table", class_="wikitable")

    # Create bone meal item as output
    bone_meal = Item(name="Bone Meal", url="https://minecraft.wiki/w/Bone_Meal")

    for table in tables:
        if not is_java_edition(table):
            continue

        # Look for tables with composting information
        header = table.find("tr")
        if not header:
            continue

        headers = [th.get_text(strip=True) for th in header.find_all("th")]

        # Check if this is a composting table (has "chance" or "%" column)
        if not any("chance" in h.lower() or "%" in h for h in headers):
            continue

        # Parse rows
        rows = table.find_all("tr")[1:]

        for row in rows:
            cells = row.find_all("td")
            if not cells:
                continue

            # Find item links
            links = cells[0].find_all("a", href=re.compile(r"^/w/"))

            for link in links:
                item = extract_item_from_link(link)
                if item:
                    # Extract success rate if present
                    success_rate = 0.0
                    if len(cells) > 1:
                        rate_text = cells[1].get_text(strip=True)
                        # Parse percentage or fraction
                        if "%" in rate_text:
                            try:
                                success_rate = float(rate_text.replace("%", "")) / 100.0
                            except ValueError:
                                pass

                    transformation = Transformation(
                        transformation_type=TransformationType.COMPOSTING,
                        inputs=[item],
                        outputs=[bone_meal],
                        metadata={"success_rate": success_rate},
                    )
                    # Only add if not seen before
                    sig = transformation.get_signature()
                    if sig not in seen_signatures:
                        seen_signatures.add(sig)
                        transformations.append(transformation)

    return transformations


def parse_grindstone(html_content: str) -> List[Transformation]:
    """
    Parse grindstone recipes from HTML content.

    Args:
        html_content: HTML content from grindstone wiki page

    Returns:
        List of Transformation objects for grindstone recipes
    """
    soup = BeautifulSoup(html_content, "lxml")
    transformations: List[Transformation] = []

    # Find grindstone UI elements
    grindstone_uis = soup.find_all("span", class_=re.compile(r"mcui.*Grindstone"))

    for ui in grindstone_uis:
        if not is_java_edition(ui):
            continue

        # Extract inputs (enchanted items)
        input_sections = ui.find_all("span", class_=re.compile(r"mcui-input"))

        input_items: List[Item] = []
        for input_section in input_sections:
            items = find_item_in_slot(input_section)
            input_items.extend(items)

        # Extract output (disenchanted item)
        output_section = ui.find("span", class_="mcui-output")
        if not output_section:
            continue

        output_items = find_item_in_slot(output_section)

        if input_items and output_items:
            transformations.append(
                Transformation(
                    transformation_type=TransformationType.GRINDSTONE,
                    inputs=input_items,
                    outputs=[output_items[0]],  # Always use single output
                )
            )

    return transformations
