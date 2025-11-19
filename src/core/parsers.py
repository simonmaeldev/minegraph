"""HTML parsers for extracting Minecraft transformation data."""

import re
from typing import List, Optional
from bs4 import BeautifulSoup, Tag
from .data_models import Item, Transformation, TransformationType
from .education_edition_blacklist import is_education_edition_item


# Excluded sections for crafting parser (historical/obsolete recipes)
EXCLUDED_CRAFTING_SECTIONS = {"Removed_recipes", "Changed_recipes"}


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

            # Check for inline edition markers (sup with Inline-Template class)
            # Pattern: <sup class="nowrap Inline-Template">...[Bedrock Edition and Minecraft Education only]</sup>
            sup_markers = cell.find_all("sup", class_="Inline-Template")
            for sup in sup_markers:
                sup_text = sup.get_text().lower()
                if ("bedrock" in sup_text or "education" in sup_text or "minecraft education" in sup_text) and "only" in sup_text:
                    return False

    return True


def is_in_excluded_section(element: Tag, excluded_ids: set = EXCLUDED_CRAFTING_SECTIONS) -> bool:
    """
    Check if element is within an excluded section (e.g., Removed_recipes, Changed_recipes).

    Args:
        element: BeautifulSoup Tag to check
        excluded_ids: Set of section IDs to exclude (default: EXCLUDED_CRAFTING_SECTIONS)

    Returns:
        True if element is within an excluded section, False otherwise
    """
    # Traverse up the DOM tree looking for parent elements with excluded IDs
    current = element
    while current:
        # Check if current element has an id attribute
        element_id = current.get('id')
        if element_id and element_id in excluded_ids:
            return True

        # Also check for child spans with mw-headline class (wiki heading structure)
        # Pattern: <h3><span class="mw-headline" id="Removed_recipes">
        if current.name in ['h2', 'h3', 'h4']:
            headline = current.find('span', class_='mw-headline')
            if headline:
                headline_id = headline.get('id')
                if headline_id and headline_id in excluded_ids:
                    return True

        # Check if we're past a heading with excluded ID
        # Find previous siblings that are headings
        for sibling in current.find_previous_siblings(['h2', 'h3']):
            headline = sibling.find('span', class_='mw-headline')
            if headline:
                sibling_id = headline.get('id')
                if sibling_id and sibling_id in excluded_ids:
                    return True
                # If we hit a non-excluded heading, we're in a different section
                elif sibling_id:
                    return False

        current = current.parent

    return False


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

    # Check if link is within an infobox or metadata section
    # These are captions/metadata, not actual game items
    parent = link_tag.parent
    while parent:
        # Check for infobox-related classes
        parent_classes = parent.get("class", [])
        if isinstance(parent_classes, list):
            if any(cls in parent_classes for cls in ["infobox-imagecaption", "infobox", "notaninfobox"]):
                return None
        parent = parent.parent

    # Check for inline edition markers next to this link (e.g., in same <li> or <td>)
    # Pattern: <a href="/w/Item">Item</a>‌<sup class="Inline-Template">[BE only]</sup>
    # Check both <li> (for list-based tables) and <td> (for regular tables)
    for parent_type in ["li", "td"]:
        parent_element = link_tag.find_parent(parent_type)
        if parent_element:
            # Look for sup elements with Inline-Template class in this parent
            sup_markers = parent_element.find_all("sup", class_="Inline-Template")
            for sup in sup_markers:
                sup_text = sup.get_text().lower()
                # Check for Bedrock/Education edition markers
                # BE = Bedrock Edition abbreviation
                if ("bedrock" in sup_text or "education" in sup_text or ("be" in sup_text and "only" in sup_text)):
                    return None

    # Extract name from href (remove /w/ prefix and decode underscores)
    name = href[3:].replace("_", " ")

    # Try to get cleaner name from title attribute
    title = link_tag.get("title", "")
    if title:
        name = title

    # Filter out Education Edition items
    if is_education_edition_item(name):
        return None

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


def extract_category_from_element(element: Tag) -> Optional[str]:
    """
    Extract category/section name from element by traversing DOM to find nearest heading.

    Args:
        element: BeautifulSoup Tag to extract category from

    Returns:
        Normalized category name (lowercase with underscores) or None if not found
    """
    # Traverse up and look for previous headings
    current = element
    while current:
        # Look for previous sibling headings (h2/h3)
        for sibling in current.find_previous_siblings(['h2', 'h3']):
            # Find mw-headline span inside the heading
            headline = sibling.find('span', class_='mw-headline')
            if headline:
                headline_id = headline.get('id')
                # Skip excluded sections
                if headline_id and headline_id in EXCLUDED_CRAFTING_SECTIONS:
                    return None

                # Extract text content
                category_text = headline.get_text(strip=True)
                if category_text:
                    # Normalize: lowercase, replace spaces with underscores, remove special chars
                    normalized = category_text.lower()
                    normalized = re.sub(r'[^\w\s]', '', normalized)  # Remove special chars
                    normalized = normalized.replace(' ', '_')
                    return normalized

        # Move up to parent
        current = current.parent

    return None


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

        # Skip recipes in excluded sections (Removed/Changed recipes)
        if is_in_excluded_section(ui):
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

        # Extract category from DOM context
        category = extract_category_from_element(ui)

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

                        metadata = {"has_alternatives": True}
                        if category:
                            metadata["category"] = category
                        transformation = Transformation(
                            transformation_type=TransformationType.CRAFTING,
                            inputs=input_items + paired_inputs,
                            outputs=[output_item],
                            metadata=metadata,
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

                        metadata = {"has_alternatives": True}
                        if category:
                            metadata["category"] = category
                        transformation = Transformation(
                            transformation_type=TransformationType.CRAFTING,
                            inputs=all_inputs,
                            outputs=output,
                            metadata=metadata,
                        )
                        sig = transformation.get_signature()
                        if sig not in seen_signatures:
                            seen_signatures.add(sig)
                            transformations.append(transformation)
            # When both input and output have same number of alternatives, pair them by index
            elif has_output_alternatives and first_slot_count == len(output_items):
                for i, alt_item in enumerate(alternative_slots[0]):
                    all_inputs = input_items + [alt_item]
                    metadata = {"has_alternatives": True}
                    if category:
                        metadata["category"] = category
                    transformation = Transformation(
                        transformation_type=TransformationType.CRAFTING,
                        inputs=all_inputs,
                        outputs=[output_items[i]],  # Match by index
                        metadata=metadata,
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
                    metadata = {"has_alternatives": True}
                    if category:
                        metadata["category"] = category
                    transformation = Transformation(
                        transformation_type=TransformationType.CRAFTING,
                        inputs=all_inputs,
                        outputs=[output_items[0]],  # Use first (only) output
                        metadata=metadata,
                    )
                    # Only add if not seen before
                    sig = transformation.get_signature()
                    if sig not in seen_signatures:
                        seen_signatures.add(sig)
                        transformations.append(transformation)
        elif input_items:
            metadata = {}
            if category:
                metadata["category"] = category
            transformation = Transformation(
                transformation_type=TransformationType.CRAFTING,
                inputs=input_items,
                outputs=[output_items[0]],  # Always use single output
                metadata=metadata,
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
    seen_signatures = set()

    # Find all wikitable tables with smelting recipes
    tables = soup.find_all("table", class_="sortable wikitable")

    for table in tables:
        # Filter out Java Edition only
        if not is_java_edition(table):
            continue

        # Find table header row to locate column indices
        header_row = table.find("tr")
        if not header_row:
            continue

        # Find column headers
        headers = header_row.find_all("th")
        if not headers or len(headers) < 2:
            continue

        # Identify Product and Ingredient column indices
        product_col = None
        ingredient_col = None
        for idx, header in enumerate(headers):
            header_text = header.get_text().strip().lower()
            if "product" in header_text:
                product_col = idx
            elif "ingredient" in header_text:
                ingredient_col = idx

        # Skip if we can't find both columns
        if product_col is None or ingredient_col is None:
            continue

        # Parse data rows
        data_rows = table.find_all("tr")[1:]  # Skip header row

        for row in data_rows:
            # Filter Java Edition rows
            if not is_java_edition(row):
                continue

            # Get all cells (th and td)
            cells = row.find_all(["th", "td"])
            if len(cells) < max(product_col, ingredient_col) + 1:
                continue

            # Extract output item from Product column (first <th>)
            output_cell = cells[product_col]
            output_links = output_cell.find_all("a", href=re.compile(r"^/w/"))
            if not output_links:
                continue

            output_item = extract_item_from_link(output_links[0])
            if not output_item:
                continue

            # Extract input item(s) from Ingredient column (first <td>)
            ingredient_cell = cells[ingredient_col]

            # Check for multiple ingredients separated by " or "
            # Split by <br> tags and " or " text
            ingredient_parts = []

            # Find all invslot elements
            invslots = ingredient_cell.find_all("span", class_="invslot")
            if invslots:
                # Get links from each invslot
                for invslot in invslots:
                    links = invslot.find_all("a", href=re.compile(r"^/w/"))
                    if links:
                        ingredient_parts.append(extract_item_from_link(links[0]))
            else:
                # Fallback: find all links directly
                ingredient_links = ingredient_cell.find_all("a", href=re.compile(r"^/w/"))
                for link in ingredient_links:
                    ingredient_parts.append(extract_item_from_link(link))

            # Filter out None values
            ingredient_items = [item for item in ingredient_parts if item]

            if not ingredient_items:
                continue

            # Create separate transformation for each ingredient option
            # This handles cases like "Raw Gold OR Nether Gold Ore"
            for input_item in ingredient_items:
                transformation = Transformation(
                    transformation_type=TransformationType.SMELTING,
                    inputs=[input_item],
                    outputs=[output_item],
                )

                # Use deduplication to avoid duplicate entries
                sig = transformation.get_signature()
                if sig not in seen_signatures:
                    seen_signatures.add(sig)
                    transformations.append(transformation)

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

    Simplified approach that parses ALL trades from ALL villager profession tables
    by dynamically detecting item columns per row instead of using fixed indices.

    Key simplifications:
    - No Java Edition filtering (both editions offer same trades, only probabilities differ)
    - No level extraction (level metadata not needed for transformation graph)
    - Dynamic column detection per row (avoids rowspan-induced index misalignment)

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
        # Extract villager type from table header with data-description attribute
        villager_header = table.find("th", attrs={"data-description": True})
        villager_type = villager_header.get("data-description", "Unknown") if villager_header else "Unknown"

        # Find the header row that contains "Item wanted" and "Item given"
        header_row = None
        for tr in table.find_all("tr"):
            headers = [th.get_text(strip=True) for th in tr.find_all("th")]
            if "Item wanted" in headers and "Item given" in headers:
                header_row = tr
                break

        if not header_row:
            continue

        # Parse data rows - all rows after the header row
        all_rows = table.find_all("tr")
        header_idx = all_rows.index(header_row)
        data_rows = all_rows[header_idx + 1:]

        for row in data_rows:
            # Find all cells in this row
            cells = row.find_all(["th", "td"])

            # Skip rows with too few cells (likely separator or header rows)
            if len(cells) < 2:
                continue

            # Dynamic column detection: find cells with item links
            # Typically there are 2 cells with item links: wanted (input) and given (output)
            cells_with_items = []
            for i, cell in enumerate(cells):
                # Check if cell contains item links
                item_links = cell.find_all("a", href=re.compile(r"^/w/"))
                if item_links:
                    cells_with_items.append((i, cell, item_links))

            # We need at least 2 cells with items (wanted and given)
            if len(cells_with_items) < 2:
                continue

            # Assume first cell with items is "wanted" (input) and second is "given" (output)
            wanted_cell = cells_with_items[0][1]
            wanted_links = cells_with_items[0][2]
            given_cell = cells_with_items[1][1]
            given_links = cells_with_items[1][2]

            # Extract input items (wanted)
            input_items: List[Item] = []
            cell_text = wanted_cell.get_text(strip=True)

            if len(wanted_links) == 1:
                # Single item - check for quantity prefix
                item = extract_item_from_link(wanted_links[0])
                if item:
                    quantity = parse_quantity(cell_text)
                    # Add item multiple times to represent quantity
                    for _ in range(quantity):
                        input_items.append(item)
            else:
                # Multiple items in cell (e.g., "Emerald + Book")
                for link in wanted_links:
                    item = extract_item_from_link(link)
                    if item:
                        # Try to find quantity for this specific item
                        link_str = str(link)
                        link_pos = str(wanted_cell).find(link_str)
                        if link_pos > 0:
                            # Get text before this link
                            preceding = str(wanted_cell)[:link_pos]
                            # Extract last quantity pattern before this link
                            quantity_match = re.findall(r'(\d+)\s*[×x]', preceding)
                            if quantity_match:
                                quantity = int(quantity_match[-1])
                            else:
                                quantity = 1
                        else:
                            quantity = 1

                        for _ in range(quantity):
                            input_items.append(item)

            # Extract output items (given)
            output_items: List[Item] = []
            output_text = given_cell.get_text(strip=True)

            if len(given_links) == 1:
                # Single output item
                item = extract_item_from_link(given_links[0])
                if item:
                    quantity = parse_quantity(output_text)
                    # Add item multiple times to represent quantity
                    for _ in range(quantity):
                        output_items.append(item)
            else:
                # Multiple output items
                for link in given_links:
                    item = extract_item_from_link(link)
                    if item:
                        output_items.append(item)

            # Create transformation if we have both inputs and outputs
            if input_items and output_items:
                transformations.append(
                    Transformation(
                        transformation_type=TransformationType.TRADING,
                        inputs=input_items,
                        outputs=[output_items[0]],  # Always use single output
                        metadata={
                            "villager_type": villager_type,
                        },
                    )
                )

    return transformations


def extract_items_from_element(element: Tag) -> List[Item]:
    """
    Extract all items from an element by finding item links.

    Args:
        element: BeautifulSoup Tag to search for item links

    Returns:
        List of unique Item objects found in the element
    """
    items = []
    seen_names = set()

    # Find all links with /w/ pattern
    links = element.find_all("a", href=re.compile(r"^/w/"))

    for link in links:
        item = extract_item_from_link(link)
        if item and item.name not in seen_names:
            # Skip experience-related items (not actual items)
            if "experience" in item.name.lower() or "xp" in item.name.lower():
                continue
            seen_names.add(item.name)
            items.append(item)

    return items


def find_subsections(heading: Tag) -> List[tuple[Tag, Tag]]:
    """
    Find all h3 subsections under a given h2 heading.

    Args:
        heading: BeautifulSoup Tag representing an h2 or h3 heading

    Returns:
        List of (subsection_heading, content_container) tuples
    """
    subsections = []

    # Find the next h2 to know where this section ends
    next_h2 = heading.find_next_sibling("h2")

    # Find all h3 elements between this heading and the next h2
    current = heading.find_next_sibling()
    while current:
        # Stop if we hit the next h2 section
        if current.name == "h2":
            break
        if next_h2 and current == next_h2:
            break

        # If this is an h3, it's a subsection
        if current.name == "h3":
            subsections.append((current, current))

        current = current.find_next_sibling()

    return subsections


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

    # Create virtual mob item
    mob_item = Item(name=mob_name, url=f"https://minecraft.wiki/w/{mob_name.replace(' ', '_')}")

    def _add_transformation(item: Item, probability: float = 1.0):
        """Helper to add a transformation with deduplication."""
        transformation = Transformation(
            transformation_type=TransformationType.MOB_DROP,
            inputs=[mob_item],
            outputs=[item],
            metadata={"probability": probability},
        )
        sig = transformation.get_signature()
        if sig not in seen_signatures:
            seen_signatures.add(sig)
            transformations.append(transformation)

    def _parse_drops_table(table: Tag):
        """Parse items from a drops table."""
        if not is_java_edition(table):
            return

        rows = table.find_all("tr")[1:]  # Skip header
        for row in rows:
            cells = row.find_all("td")
            if len(cells) < 1:
                continue

            # First cell usually contains item
            item_cell = cells[0]
            links = item_cell.find_all("a", href=re.compile(r"^/w/"))

            for link in links:
                item = extract_item_from_link(link)
                if item:
                    # Skip experience-related items (not actual items)
                    if "experience" in item.name.lower() or "xp" in item.name.lower():
                        continue
                    # Try to extract probability if present
                    probability = 1.0
                    if len(cells) > 2:
                        prob_text = cells[2].get_text(strip=True)
                        if "%" in prob_text:
                            try:
                                probability = float(prob_text.replace("%", "")) / 100.0
                            except ValueError:
                                pass
                    _add_transformation(item, probability)

    # Find "Drops" section
    drops_section = soup.find(id="Drops")
    if drops_section:
        # If we found a span with id="Drops", get its parent (the h2/h3 element)
        if drops_section.name == "span":
            drops_section = drops_section.find_parent(["h2", "h3"])

    if not drops_section:
        # Try finding h2/h3 with "Drops" text
        for heading in soup.find_all(["h2", "h3"]):
            if "drops" in heading.get_text().lower():
                drops_section = heading
                break

    if drops_section:
        # Parse main drops table (if exists)
        # Only search within the Drops section boundary (until next h2)
        next_h2 = drops_section.find_next_sibling("h2")
        table = None
        current_elem = drops_section.find_next_sibling()
        while current_elem:
            if current_elem == next_h2:
                break
            if current_elem.name == "table" and "wikitable" in current_elem.get("class", []):
                table = current_elem
                break
            current_elem = current_elem.find_next_sibling()

        if table:
            _parse_drops_table(table)

        # Parse subsections under "Drops"
        # Only parse tables in subsections, not lists or paragraphs
        # Lists and paragraphs often contain navigation/behavior descriptions with false positives
        subsections = find_subsections(drops_section)
        for subsection_heading, _ in subsections:
            # Extract ID from the nested span with class="mw-headline"
            id_span = subsection_heading.find('span', class_='mw-headline')
            subsection_id = id_span.get('id', '') if id_span else subsection_heading.get('id', '')
            subsection_text = subsection_heading.get_text().lower()

            # Skip experience-only subsections
            if 'experience' in subsection_text and 'item' not in subsection_text:
                continue

            # Expert rule for armadillo's "Brushing" subsection
            # This subsection uses a simple list format instead of wikitable
            if subsection_id == 'Brushing':
                next_heading = subsection_heading.find_next_sibling(["h2", "h3"])
                current_elem = subsection_heading.find_next_sibling()
                while current_elem:
                    if current_elem == next_heading:
                        break
                    # Look for unordered lists containing item links
                    if current_elem.name == "ul":
                        list_items = current_elem.find_all("li")
                        for li in list_items:
                            # Extract items from links within the list item
                            links = li.find_all("a", href=re.compile(r"^/w/"))
                            for link in links:
                                item = extract_item_from_link(link)
                                if item:
                                    _add_transformation(item)
                        break  # Only parse the first list in this subsection
                    current_elem = current_elem.find_next_sibling()
                continue  # Skip normal table parsing for Brushing subsection

            # Look for tables in the subsection
            # We need to check if the table appears before the next heading
            next_heading = subsection_heading.find_next_sibling(["h2", "h3"])

            # Find all tables between this subsection and the next heading
            current_elem = subsection_heading.find_next_sibling()
            while current_elem:
                if current_elem == next_heading:
                    break
                if current_elem.name == "table" and "wikitable" in current_elem.get("class", []):
                    _parse_drops_table(current_elem)
                    break  # Only parse the first table in this subsection
                current_elem = current_elem.find_next_sibling()

    # Parse special sections for behavioral drops
    # Only parse the Gifts section (e.g., cats bringing items) and only from tables
    # Avoid parsing Attacking/Behavior sections as they often describe game mechanics, not actual drops
    gifts_section = soup.find(id="Gifts")
    if gifts_section:
        # If we found a span with id="Gifts", get its parent (the h2/h3 element)
        if gifts_section.name == "span":
            gifts_section = gifts_section.find_parent(["h2", "h3"])
        if gifts_section:
            gifts_table = gifts_section.find_next("table", class_="wikitable")
            if gifts_table and is_java_edition(gifts_table):
                _parse_drops_table(gifts_table)

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

    The composting table has a structure where:
    - First row contains success rate percentages (30%, 50%, 65%, 85%, 100%)
    - Second row has <th colspan="6">Items</th> header
    - Following rows have <td> cells with <ul> lists containing item links
    - Each column corresponds to a success rate percentage

    Args:
        html_content: HTML content from composter wiki page

    Returns:
        List of Transformation objects for composting recipes (deduplicated)
    """
    soup = BeautifulSoup(html_content, "lxml")
    transformations: List[Transformation] = []
    seen_signatures = set()

    # Create bone meal item as output
    bone_meal = Item(name="Bone Meal", url="https://minecraft.wiki/w/Bone_Meal")

    # Find composting tables by looking for the "Items" header row
    tables = soup.find_all("table", class_="wikitable")

    for table in tables:
        if not is_java_edition(table):
            continue

        # Look for the row with "Items" header
        items_header_row = None
        percentage_row = None

        for row in table.find_all("tr"):
            th_tags = row.find_all("th")
            for th in th_tags:
                # Check if this is the "Items" header with colspan
                text = th.get_text(strip=True)
                if text == "Items" and th.get("colspan"):
                    items_header_row = row
                    # The previous row should contain the percentages
                    prev_row = row.find_previous_sibling("tr")
                    if prev_row:
                        percentage_row = prev_row
                    break
            if items_header_row:
                break

        if not items_header_row:
            continue

        # Extract success rates from percentage row
        success_rates = []
        if percentage_row:
            for cell in percentage_row.find_all("td"):
                rate_text = cell.get_text(strip=True)
                if "%" in rate_text:
                    try:
                        rate = float(rate_text.replace("%", "")) / 100.0
                        success_rates.append(rate)
                    except ValueError:
                        success_rates.append(0.0)

        # Parse rows following the "Items" header
        current_row = items_header_row.find_next_sibling("tr")
        while current_row:
            cells = current_row.find_all("td")
            if not cells:
                # No more data rows
                break

            # Each cell corresponds to a success rate column
            for col_idx, cell in enumerate(cells):
                # Get success rate for this column
                success_rate = success_rates[col_idx] if col_idx < len(success_rates) else 0.0

                # Find all item links in this cell (may be in <ul> lists)
                links = cell.find_all("a", href=re.compile(r"^/w/"))

                for link in links:
                    item = extract_item_from_link(link)
                    if item:
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

            current_row = current_row.find_next_sibling("tr")

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


def parse_bartering(html_content: str) -> List[Transformation]:
    """
    Parse bartering data from HTML content.

    Extracts Piglin bartering transformations where Gold Ingot is traded for various items.

    Args:
        html_content: HTML content from bartering wiki page

    Returns:
        List of Transformation objects for bartering trades
    """
    soup = BeautifulSoup(html_content, "lxml")
    transformations: List[Transformation] = []
    seen_signatures = set()

    # Find the bartering items table
    tables = soup.find_all("table", class_="wikitable")

    for table in tables:
        # Find the header row with "Item given"
        header_row = None
        for tr in table.find_all("tr"):
            headers = [th.get_text(strip=True) for th in tr.find_all("th")]
            if "Item given" in headers:
                header_row = tr
                break

        if not header_row:
            continue

        # Get column index for "Item given"
        headers = [th.get_text(strip=True) for th in header_row.find_all("th")]
        item_given_idx = headers.index("Item given")

        # Parse data rows
        all_rows = table.find_all("tr")
        header_idx = all_rows.index(header_row)
        data_rows = all_rows[header_idx + 1:]

        for row in data_rows:
            cells = row.find_all(["th", "td"])

            # Skip rows without an item_given cell
            if len(cells) <= item_given_idx:
                continue

            item_given_cell = cells[item_given_idx]

            # Extract items from the "Item given" cell
            # Some cells have multiple items separated by line breaks (alternative items)
            item_links = item_given_cell.find_all("a", href=re.compile(r"^/w/"))

            for link in item_links:
                # Filter out edition marker links (JE/BE links)
                href = link.get('href', '')
                if '/Java_Edition' in href or '/Bedrock_Edition' in href:
                    continue

                # Skip image-only links (they contain <img> tags and are duplicates of text links)
                if link.find('img'):
                    continue

                # Skip enchantment links that appear after "with" text
                # Example: <br />with <a href="/w/Soul_Speed">Soul Speed</a> (random level)
                # We need to check if there's "with" text before this link
                previous_text = ""
                for prev_sibling in link.previous_siblings:
                    if isinstance(prev_sibling, str):
                        previous_text = prev_sibling + previous_text
                    elif prev_sibling.name == 'br':
                        # Found a <br>, check accumulated text
                        if 'with' in previous_text.strip():
                            break
                        # Reset for next segment
                        previous_text = ""
                    else:
                        # Reset on other tags (like <span>)
                        previous_text = ""

                # If we found "with" in the text immediately before this link, skip it
                if 'with' in previous_text.strip():
                    continue

                # Check if this specific link has a BE only marker near it
                # Get the parent span that wraps this link
                # The structure is: <span class="nowrap">...<a>Item</a></span><sup>[JE/BE only]</sup><br/>
                link_parent = link.find_parent()
                if link_parent:
                    # Get the next siblings after the parent span (up to <br/>)
                    text_parts = []
                    for sibling in link_parent.next_siblings:
                        if sibling.name == 'br':
                            break
                        if isinstance(sibling, str):
                            text_parts.append(sibling)
                        else:
                            # Get text from element (like <sup>)
                            text_parts.append(sibling.get_text())

                    # Check if the text after this link's parent contains [BE only] or "Bedrock Edition"
                    text_after = ''.join(text_parts)
                    if ('[BE' in text_after and 'only' in text_after) or 'Bedrock Edition' in text_after:
                        continue

                # Extract item directly (don't use extract_item_from_link because it checks
                # ALL edition markers in the parent <td>, which would incorrectly filter out
                # Spectral Arrow when it shares a cell with Arrow [BE only])
                href = link.get('href', '')
                if not href or not href.startswith('/w/'):
                    continue

                # Extract name from title or href
                name = link.get('title', '')
                if not name:
                    name = href[3:].replace('_', ' ')

                if not name:
                    continue

                url = f'https://minecraft.wiki{href}'
                item = Item(name=name, url=url)

                # Skip education edition items
                if is_education_edition_item(item.name):
                    continue

                # Create Gold Ingot input
                gold_ingot = Item(
                    name="Gold Ingot",
                    url="https://minecraft.wiki/w/Gold_Ingot"
                )

                # Create transformation (no quantity, no probability - just the item)
                transformation = Transformation(
                    transformation_type=TransformationType.BARTERING,
                    inputs=[gold_ingot],
                    outputs=[item],
                    metadata={},
                )

                # Deduplicate using signature
                signature = transformation.get_signature()
                if signature not in seen_signatures:
                    seen_signatures.add(signature)
                    transformations.append(transformation)

    return transformations
