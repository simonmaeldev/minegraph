"""Unit tests for parser functions."""

import pytest
from bs4 import BeautifulSoup, Tag
from src.core.parsers import (
    is_java_edition,
    extract_item_from_link,
    parse_quantity,
    find_item_in_slot,
)
from src.core.data_models import Item


class TestIsJavaEdition:
    """Tests for is_java_edition filter function."""

    def test_accepts_unspecified_content(self):
        """Test that content without edition markers is accepted (default Java)."""
        html = '<div>Some recipe content</div>'
        soup = BeautifulSoup(html, "lxml")
        element = soup.find("div")
        assert is_java_edition(element) is True

    def test_rejects_bedrock_content(self):
        """Test that Bedrock Edition content is rejected."""
        html = '<div>This is for Bedrock Edition</div>'
        soup = BeautifulSoup(html, "lxml")
        element = soup.find("div")
        assert is_java_edition(element) is False

    def test_rejects_education_content(self):
        """Test that Education Edition content is rejected."""
        html = '<div>Education Edition feature</div>'
        soup = BeautifulSoup(html, "lxml")
        element = soup.find("div")
        assert is_java_edition(element) is False

    def test_accepts_java_edition_content(self):
        """Test that explicit Java Edition content is accepted."""
        html = '<div>Java Edition recipe</div>'
        soup = BeautifulSoup(html, "lxml")
        element = soup.find("div")
        assert is_java_edition(element) is True

    def test_rejects_bedrock_education_in_table_row(self):
        """Test that Bedrock/Education markers in sibling table cells are detected."""
        html = '''
        <table>
            <tr>
                <td>
                    <span class="mcui mcui-Crafting_Table">Recipe UI</span>
                </td>
                <td>
                    <sup>[<i><span title="This statement only applies to Bedrock Edition and Minecraft Education">
                    <a href="/w/Bedrock_Edition">Bedrock Edition</a> and
                    <a href="/w/Minecraft_Education">Minecraft Education</a> only</span></i>]</sup>
                </td>
            </tr>
        </table>
        '''
        soup = BeautifulSoup(html, "lxml")
        element = soup.find("span", class_="mcui")
        assert is_java_edition(element) is False

    def test_accepts_java_edition_in_table_row(self):
        """Test that Java Edition recipes in table rows are accepted."""
        html = '''
        <table>
            <tr>
                <td>
                    <span class="mcui mcui-Crafting_Table">Recipe UI</span>
                </td>
                <td>Regular crafting recipe description</td>
            </tr>
        </table>
        '''
        soup = BeautifulSoup(html, "lxml")
        element = soup.find("span", class_="mcui")
        assert is_java_edition(element) is True


class TestExtractItemFromLink:
    """Tests for extract_item_from_link function."""

    def test_extracts_item_from_valid_link(self):
        """Test extracting item from valid wiki link."""
        html = '<a href="/w/Iron_Ingot" title="Iron Ingot">Iron Ingot</a>'
        soup = BeautifulSoup(html, "lxml")
        link = soup.find("a")

        item = extract_item_from_link(link)

        assert item is not None
        assert item.name == "Iron Ingot"
        assert item.url == "https://minecraft.wiki/w/Iron_Ingot"

    def test_decodes_underscores_in_name(self):
        """Test that underscores in href are decoded to spaces."""
        html = '<a href="/w/Block_of_Iron">Block of Iron</a>'
        soup = BeautifulSoup(html, "lxml")
        link = soup.find("a")

        item = extract_item_from_link(link)

        assert item is not None
        assert "Block of Iron" in item.name or "Block of Iron" in item.url

    def test_returns_none_for_invalid_link(self):
        """Test that non-wiki links return None."""
        html = '<a href="https://example.com">External Link</a>'
        soup = BeautifulSoup(html, "lxml")
        link = soup.find("a")

        item = extract_item_from_link(link)

        assert item is None

    def test_returns_none_for_non_link_element(self):
        """Test that non-<a> elements return None."""
        html = '<div>Not a link</div>'
        soup = BeautifulSoup(html, "lxml")
        div = soup.find("div")

        item = extract_item_from_link(div)

        assert item is None

    def test_prefers_title_attribute(self):
        """Test that title attribute is used for cleaner names."""
        html = '<a href="/w/Diamond_Sword" title="Diamond Sword">Sword</a>'
        soup = BeautifulSoup(html, "lxml")
        link = soup.find("a")

        item = extract_item_from_link(link)

        assert item is not None
        assert item.name == "Diamond Sword"


class TestParseQuantity:
    """Tests for parse_quantity function."""

    def test_parses_multiply_symbol(self):
        """Test parsing '15 × Coal' format."""
        assert parse_quantity("15 × Coal") == 15
        assert parse_quantity("32 × Stick") == 32

    def test_parses_x_symbol(self):
        """Test parsing with lowercase x."""
        assert parse_quantity("10 x Iron") == 10

    def test_parses_standalone_number(self):
        """Test parsing standalone number."""
        assert parse_quantity("7") == 7
        assert parse_quantity("  25  ") == 25

    def test_defaults_to_one(self):
        """Test that missing quantity defaults to 1."""
        assert parse_quantity("Diamond") == 1
        assert parse_quantity("") == 1
        assert parse_quantity("No number here") == 1

    def test_parses_number_at_start(self):
        """Test parsing number at start of string."""
        assert parse_quantity("64 items") == 64


class TestFindItemInSlot:
    """Tests for find_item_in_slot function."""

    def test_finds_single_item(self):
        """Test finding a single item in a slot."""
        html = '''
        <span class="invslot">
            <span class="invslot-item">
                <a href="/w/Diamond" title="Diamond">Diamond</a>
            </span>
        </span>
        '''
        soup = BeautifulSoup(html, "lxml")
        slot = soup.find("span", class_="invslot")

        items = find_item_in_slot(slot)

        assert len(items) == 1
        assert items[0].name == "Diamond"

    def test_finds_multiple_alternatives(self):
        """Test finding multiple alternative items (animated slot)."""
        html = '''
        <span class="invslot animated">
            <span class="invslot-item">
                <a href="/w/Iron_Ingot">Iron Ingot</a>
            </span>
            <span class="invslot-item">
                <a href="/w/Gold_Ingot">Gold Ingot</a>
            </span>
            <span class="invslot-item">
                <a href="/w/Diamond">Diamond</a>
            </span>
        </span>
        '''
        soup = BeautifulSoup(html, "lxml")
        slot = soup.find("span", class_="invslot")

        items = find_item_in_slot(slot)

        assert len(items) == 3
        item_names = [item.name for item in items]
        assert "Iron Ingot" in item_names
        assert "Gold Ingot" in item_names
        assert "Diamond" in item_names

    def test_returns_empty_for_empty_slot(self):
        """Test that empty slot returns empty list."""
        html = '<span class="invslot"></span>'
        soup = BeautifulSoup(html, "lxml")
        slot = soup.find("span", class_="invslot")

        items = find_item_in_slot(slot)

        assert len(items) == 0


class TestParsers:
    """Integration tests for parser functions with realistic HTML."""

    def test_parse_crafting_simple(self):
        """Test parsing a simple crafting recipe."""
        # This would require actual HTML from wiki pages
        # For now, we test that the function exists and handles empty input
        from src.core.parsers import parse_crafting

        empty_html = "<html><body></body></html>"
        result = parse_crafting(empty_html)

        assert isinstance(result, list)

    def test_parse_smelting_simple(self):
        """Test parsing a smelting recipe."""
        from src.core.parsers import parse_smelting

        empty_html = "<html><body></body></html>"
        result = parse_smelting(empty_html)

        assert isinstance(result, list)

    def test_parse_trading_simple(self):
        """Test parsing a trading recipe."""
        from src.core.parsers import parse_trading

        empty_html = "<html><body></body></html>"
        result = parse_trading(empty_html)

        assert isinstance(result, list)

    def test_parse_mob_drops_simple(self):
        """Test parsing mob drops."""
        from src.core.parsers import parse_mob_drops

        empty_html = "<html><body></body></html>"
        result = parse_mob_drops(empty_html, "Zombie")

        assert isinstance(result, list)

    def test_filter_bedrock_education_recipes(self):
        """Test that parse_crafting filters out Bedrock/Education recipes like Bleach."""
        from src.core.parsers import parse_crafting

        # HTML that mimics the wiki structure for Bleach recipe
        html = '''
        <html><body>
        <table class="wikitable">
            <tr>
                <td>
                    <span class="mcui mcui-Crafting_Table pixel-image">
                        <span class="mcui-input">
                            <span class="mcui-row">
                                <span class="invslot"></span>
                                <span class="invslot"></span>
                                <span class="invslot"></span>
                            </span>
                            <span class="mcui-row">
                                <span class="invslot">
                                    <span class="invslot-item">
                                        <a href="/w/Gray_Wool" title="Gray Wool">Gray Wool</a>
                                    </span>
                                </span>
                                <span class="invslot">
                                    <span class="invslot-item">
                                        <a href="/w/Bleach" title="Bleach">Bleach</a>
                                    </span>
                                </span>
                                <span class="invslot"></span>
                            </span>
                            <span class="mcui-row">
                                <span class="invslot"></span>
                                <span class="invslot"></span>
                                <span class="invslot"></span>
                            </span>
                        </span>
                        <span class="mcui-arrow"></span>
                        <span class="mcui-output">
                            <span class="invslot invslot-large">
                                <span class="invslot-item">
                                    <a href="/w/White_Wool" title="White Wool">White Wool</a>
                                </span>
                            </span>
                        </span>
                    </span>
                </td>
                <td>
                    <sup class="nowrap Inline-Template">
                        [<i><span title="This statement only applies to Bedrock Edition and Minecraft Education">
                        <a href="/w/Bedrock_Edition">Bedrock Edition</a> and
                        <a href="/w/Minecraft_Education">Minecraft Education</a> only</span></i>]
                    </sup>
                </td>
            </tr>
        </table>
        </body></html>
        '''

        result = parse_crafting(html)

        # The Bedrock/Education recipe should be filtered out
        assert len(result) == 0

    def test_accept_java_edition_recipes(self):
        """Test that parse_crafting accepts Java Edition recipes."""
        from src.core.parsers import parse_crafting

        # HTML that mimics a standard Java Edition crafting recipe
        html = '''
        <html><body>
        <table class="wikitable">
            <tr>
                <td>
                    <span class="mcui mcui-Crafting_Table pixel-image">
                        <span class="mcui-input">
                            <span class="mcui-row">
                                <span class="invslot">
                                    <span class="invslot-item">
                                        <a href="/w/Iron_Ingot" title="Iron Ingot">Iron Ingot</a>
                                    </span>
                                </span>
                                <span class="invslot">
                                    <span class="invslot-item">
                                        <a href="/w/Iron_Ingot" title="Iron Ingot">Iron Ingot</a>
                                    </span>
                                </span>
                                <span class="invslot">
                                    <span class="invslot-item">
                                        <a href="/w/Iron_Ingot" title="Iron Ingot">Iron Ingot</a>
                                    </span>
                                </span>
                            </span>
                            <span class="mcui-row">
                                <span class="invslot">
                                    <span class="invslot-item">
                                        <a href="/w/Iron_Ingot" title="Iron Ingot">Iron Ingot</a>
                                    </span>
                                </span>
                                <span class="invslot">
                                    <span class="invslot-item">
                                        <a href="/w/Iron_Ingot" title="Iron Ingot">Iron Ingot</a>
                                    </span>
                                </span>
                                <span class="invslot">
                                    <span class="invslot-item">
                                        <a href="/w/Iron_Ingot" title="Iron Ingot">Iron Ingot</a>
                                    </span>
                                </span>
                            </span>
                            <span class="mcui-row">
                                <span class="invslot">
                                    <span class="invslot-item">
                                        <a href="/w/Iron_Ingot" title="Iron Ingot">Iron Ingot</a>
                                    </span>
                                </span>
                                <span class="invslot">
                                    <span class="invslot-item">
                                        <a href="/w/Iron_Ingot" title="Iron Ingot">Iron Ingot</a>
                                    </span>
                                </span>
                                <span class="invslot">
                                    <span class="invslot-item">
                                        <a href="/w/Iron_Ingot" title="Iron Ingot">Iron Ingot</a>
                                    </span>
                                </span>
                            </span>
                        </span>
                        <span class="mcui-arrow"></span>
                        <span class="mcui-output">
                            <span class="invslot invslot-large">
                                <span class="invslot-item">
                                    <a href="/w/Block_of_Iron" title="Block of Iron">Block of Iron</a>
                                </span>
                            </span>
                        </span>
                    </span>
                </td>
                <td>Normal crafting recipe</td>
            </tr>
        </table>
        </body></html>
        '''

        result = parse_crafting(html)

        # Java Edition recipe should be accepted
        assert len(result) == 1
        assert result[0].inputs[0].name == "Iron Ingot"
        assert result[0].outputs[0].name == "Block of Iron"

    def test_parse_crafting_includes_category_simple_recipe(self):
        """Test that parse_crafting includes category metadata for simple recipes."""
        from src.core.parsers import parse_crafting

        html = '''
        <html><body>
        <h2><span class="mw-headline" id="Building_blocks">Building blocks</span></h2>
        <table class="wikitable">
            <tr>
                <td>
                    <span class="mcui mcui-Crafting_Table pixel-image">
                        <span class="mcui-input">
                            <span class="mcui-row">
                                <span class="invslot">
                                    <span class="invslot-item">
                                        <a href="/w/Iron_Ingot" title="Iron Ingot">Iron Ingot</a>
                                    </span>
                                </span>
                                <span class="invslot">
                                    <span class="invslot-item">
                                        <a href="/w/Iron_Ingot" title="Iron Ingot">Iron Ingot</a>
                                    </span>
                                </span>
                                <span class="invslot">
                                    <span class="invslot-item">
                                        <a href="/w/Iron_Ingot" title="Iron Ingot">Iron Ingot</a>
                                    </span>
                                </span>
                            </span>
                            <span class="mcui-row">
                                <span class="invslot">
                                    <span class="invslot-item">
                                        <a href="/w/Iron_Ingot" title="Iron Ingot">Iron Ingot</a>
                                    </span>
                                </span>
                                <span class="invslot">
                                    <span class="invslot-item">
                                        <a href="/w/Iron_Ingot" title="Iron Ingot">Iron Ingot</a>
                                    </span>
                                </span>
                                <span class="invslot">
                                    <span class="invslot-item">
                                        <a href="/w/Iron_Ingot" title="Iron Ingot">Iron Ingot</a>
                                    </span>
                                </span>
                            </span>
                            <span class="mcui-row">
                                <span class="invslot">
                                    <span class="invslot-item">
                                        <a href="/w/Iron_Ingot" title="Iron Ingot">Iron Ingot</a>
                                    </span>
                                </span>
                                <span class="invslot">
                                    <span class="invslot-item">
                                        <a href="/w/Iron_Ingot" title="Iron Ingot">Iron Ingot</a>
                                    </span>
                                </span>
                                <span class="invslot">
                                    <span class="invslot-item">
                                        <a href="/w/Iron_Ingot" title="Iron Ingot">Iron Ingot</a>
                                    </span>
                                </span>
                            </span>
                        </span>
                        <span class="mcui-arrow"></span>
                        <span class="mcui-output">
                            <span class="invslot invslot-large">
                                <span class="invslot-item">
                                    <a href="/w/Block_of_Iron" title="Block of Iron">Block of Iron</a>
                                </span>
                            </span>
                        </span>
                    </span>
                </td>
            </tr>
        </table>
        </body></html>
        '''

        result = parse_crafting(html)

        assert len(result) == 1
        assert result[0].metadata.get("category") == "building_blocks"

    def test_parse_crafting_includes_category_with_alternatives(self):
        """Test that parse_crafting includes category metadata for recipes with alternatives."""
        from src.core.parsers import parse_crafting

        html = '''
        <html><body>
        <h2><span class="mw-headline" id="Redstone">Redstone</span></h2>
        <table class="wikitable">
            <tr>
                <td>
                    <span class="mcui mcui-Crafting_Table pixel-image">
                        <span class="mcui-input">
                            <span class="mcui-row">
                                <span class="invslot">
                                    <span class="invslot-item">
                                        <a href="/w/Redstone" title="Redstone">Redstone</a>
                                    </span>
                                </span>
                                <span class="invslot">
                                    <span class="invslot-item">
                                        <a href="/w/Redstone" title="Redstone">Redstone</a>
                                    </span>
                                </span>
                                <span class="invslot"></span>
                            </span>
                            <span class="mcui-row">
                                <span class="invslot">
                                    <span class="invslot-item">
                                        <a href="/w/Stone" title="Stone">Stone</a>
                                    </span>
                                    <span class="invslot-item">
                                        <a href="/w/Cobblestone" title="Cobblestone">Cobblestone</a>
                                    </span>
                                </span>
                                <span class="invslot"></span>
                                <span class="invslot"></span>
                            </span>
                            <span class="mcui-row">
                                <span class="invslot"></span>
                                <span class="invslot"></span>
                                <span class="invslot"></span>
                            </span>
                        </span>
                        <span class="mcui-arrow"></span>
                        <span class="mcui-output">
                            <span class="invslot invslot-large">
                                <span class="invslot-item">
                                    <a href="/w/Redstone_Repeater" title="Redstone Repeater">Repeater</a>
                                </span>
                            </span>
                        </span>
                    </span>
                </td>
            </tr>
        </table>
        </body></html>
        '''

        result = parse_crafting(html)

        # Should have 2 transformations (one per stone alternative)
        assert len(result) == 2
        for transformation in result:
            assert transformation.metadata.get("has_alternatives") is True
            assert transformation.metadata.get("category") == "redstone"

    def test_parse_crafting_no_category_without_heading(self):
        """Test that parse_crafting handles recipes without section headings."""
        from src.core.parsers import parse_crafting

        html = '''
        <html><body>
        <table class="wikitable">
            <tr>
                <td>
                    <span class="mcui mcui-Crafting_Table pixel-image">
                        <span class="mcui-input">
                            <span class="mcui-row">
                                <span class="invslot">
                                    <span class="invslot-item">
                                        <a href="/w/Stick" title="Stick">Stick</a>
                                    </span>
                                </span>
                                <span class="invslot"></span>
                                <span class="invslot"></span>
                            </span>
                            <span class="mcui-row">
                                <span class="invslot"></span>
                                <span class="invslot"></span>
                                <span class="invslot"></span>
                            </span>
                            <span class="mcui-row">
                                <span class="invslot"></span>
                                <span class="invslot"></span>
                                <span class="invslot"></span>
                            </span>
                        </span>
                        <span class="mcui-arrow"></span>
                        <span class="mcui-output">
                            <span class="invslot invslot-large">
                                <span class="invslot-item">
                                    <a href="/w/Torch" title="Torch">Torch</a>
                                </span>
                            </span>
                        </span>
                    </span>
                </td>
            </tr>
        </table>
        </body></html>
        '''

        result = parse_crafting(html)

        assert len(result) == 1
        # Category should not be present (or be None) when no heading is found
        assert "category" not in result[0].metadata or result[0].metadata.get("category") is None

    def test_parse_crafting_multiple_categories(self):
        """Test that parse_crafting correctly assigns different categories to different recipes."""
        from src.core.parsers import parse_crafting

        html = '''
        <html><body>
        <h2><span class="mw-headline" id="Transportation">Transportation</span></h2>
        <table class="wikitable">
            <tr>
                <td>
                    <span class="mcui mcui-Crafting_Table pixel-image">
                        <span class="mcui-input">
                            <span class="mcui-row">
                                <span class="invslot">
                                    <span class="invslot-item">
                                        <a href="/w/Iron_Ingot" title="Iron Ingot">Iron Ingot</a>
                                    </span>
                                </span>
                                <span class="invslot"></span>
                                <span class="invslot">
                                    <span class="invslot-item">
                                        <a href="/w/Iron_Ingot" title="Iron Ingot">Iron Ingot</a>
                                    </span>
                                </span>
                            </span>
                            <span class="mcui-row">
                                <span class="invslot">
                                    <span class="invslot-item">
                                        <a href="/w/Iron_Ingot" title="Iron Ingot">Iron Ingot</a>
                                    </span>
                                </span>
                                <span class="invslot">
                                    <span class="invslot-item">
                                        <a href="/w/Iron_Ingot" title="Iron Ingot">Iron Ingot</a>
                                    </span>
                                </span>
                                <span class="invslot">
                                    <span class="invslot-item">
                                        <a href="/w/Iron_Ingot" title="Iron Ingot">Iron Ingot</a>
                                    </span>
                                </span>
                            </span>
                            <span class="mcui-row">
                                <span class="invslot"></span>
                                <span class="invslot"></span>
                                <span class="invslot"></span>
                            </span>
                        </span>
                        <span class="mcui-arrow"></span>
                        <span class="mcui-output">
                            <span class="invslot invslot-large">
                                <span class="invslot-item">
                                    <a href="/w/Minecart" title="Minecart">Minecart</a>
                                </span>
                            </span>
                        </span>
                    </span>
                </td>
            </tr>
        </table>
        <h2><span class="mw-headline" id="Combat">Combat</span></h2>
        <table class="wikitable">
            <tr>
                <td>
                    <span class="mcui mcui-Crafting_Table pixel-image">
                        <span class="mcui-input">
                            <span class="mcui-row">
                                <span class="invslot"></span>
                                <span class="invslot">
                                    <span class="invslot-item">
                                        <a href="/w/Iron_Ingot" title="Iron Ingot">Iron Ingot</a>
                                    </span>
                                </span>
                                <span class="invslot"></span>
                            </span>
                            <span class="mcui-row">
                                <span class="invslot"></span>
                                <span class="invslot">
                                    <span class="invslot-item">
                                        <a href="/w/Stick" title="Stick">Stick</a>
                                    </span>
                                </span>
                                <span class="invslot"></span>
                            </span>
                            <span class="mcui-row">
                                <span class="invslot"></span>
                                <span class="invslot">
                                    <span class="invslot-item">
                                        <a href="/w/Stick" title="Stick">Stick</a>
                                    </span>
                                </span>
                                <span class="invslot"></span>
                            </span>
                        </span>
                        <span class="mcui-arrow"></span>
                        <span class="mcui-output">
                            <span class="invslot invslot-large">
                                <span class="invslot-item">
                                    <a href="/w/Iron_Sword" title="Iron Sword">Iron Sword</a>
                                </span>
                            </span>
                        </span>
                    </span>
                </td>
            </tr>
        </table>
        </body></html>
        '''

        result = parse_crafting(html)

        assert len(result) == 2

        # Find the minecart and sword transformations
        minecart = next(t for t in result if t.outputs[0].name == "Minecart")
        sword = next(t for t in result if t.outputs[0].name == "Iron Sword")

        assert minecart.metadata.get("category") == "transportation"
        assert sword.metadata.get("category") == "combat"
