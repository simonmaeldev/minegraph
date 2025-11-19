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

    def test_parse_trading_item_to_emerald(self):
        """Test parsing an item-to-emerald trade (selling to villager)."""
        from src.core.parsers import parse_trading
        from src.core.data_models import TransformationType

        html = '''
        <table class="wikitable" style="text-align:center">
            <tbody>
                <tr>
                    <th colspan="9" data-description="Armorer">
                        <span class="nowrap">
                            <a href="/w/Armorer" title="Armorer">
                                <span class="sprite-text">Armorer</span>
                            </a>
                        </span>
                    </th>
                </tr>
                <tr>
                    <th rowspan="2">Level</th>
                    <th><i><a href="/w/Java_Edition" title="Java Edition">Java Edition</a></i></th>
                    <th rowspan="2">Item wanted</th>
                    <th rowspan="2">Item given</th>
                </tr>
                <tr>
                    <th>Probability</th>
                </tr>
                <tr>
                    <th>Novice</th>
                    <td>40%</td>
                    <td>15 × <span class="nowrap">
                        <a href="/w/Coal" title="Coal">
                            <span class="sprite-text">Coal</span>
                        </a>
                    </span></td>
                    <td><span class="nowrap">
                        <a href="/w/Emerald" title="Emerald">
                            <span class="sprite-text">Emerald</span>
                        </a>
                    </span></td>
                </tr>
            </tbody>
        </table>
        '''

        result = parse_trading(html)

        assert len(result) == 1
        assert result[0].transformation_type == TransformationType.TRADING
        # Note: Transformation deduplicates inputs, so 15 Coal becomes 1 Coal in the graph
        assert len(result[0].inputs) == 1
        assert result[0].inputs[0].name == "Coal"
        assert len(result[0].outputs) == 1
        assert result[0].outputs[0].name == "Emerald"
        assert result[0].metadata["villager_type"] == "Armorer"

    def test_parse_trading_emerald_to_item(self):
        """Test parsing an emerald-to-item trade (buying from villager)."""
        from src.core.parsers import parse_trading
        from src.core.data_models import TransformationType

        html = '''
        <table class="wikitable" style="text-align:center">
            <tbody>
                <tr>
                    <th colspan="9" data-description="Armorer">
                        <span class="nowrap">
                            <a href="/w/Armorer" title="Armorer">
                                <span class="sprite-text">Armorer</span>
                            </a>
                        </span>
                    </th>
                </tr>
                <tr>
                    <th rowspan="2">Level</th>
                    <th><i><a href="/w/Java_Edition" title="Java Edition">Java Edition</a></i></th>
                    <th rowspan="2">Item wanted</th>
                    <th rowspan="2">Item given</th>
                </tr>
                <tr>
                    <th>Probability</th>
                </tr>
                <tr>
                    <th>Apprentice</th>
                    <td>40%</td>
                    <td>5 × <span class="nowrap">
                        <a href="/w/Emerald" title="Emerald">
                            <span class="sprite-text">Emerald</span>
                        </a>
                    </span></td>
                    <td><span class="nowrap">
                        <a href="/w/Iron_Helmet" title="Iron Helmet">
                            <span class="sprite-text">Iron Helmet</span>
                        </a>
                    </span></td>
                </tr>
            </tbody>
        </table>
        '''

        result = parse_trading(html)

        assert len(result) == 1
        assert result[0].transformation_type == TransformationType.TRADING
        # Note: Transformation deduplicates inputs, so 5 Emeralds becomes 1 Emerald in the graph
        assert len(result[0].inputs) == 1
        assert result[0].inputs[0].name == "Emerald"
        assert len(result[0].outputs) == 1
        assert result[0].outputs[0].name == "Iron Helmet"
        assert result[0].metadata["villager_type"] == "Armorer"

    def test_parse_trading_no_quantity_multiplier(self):
        """Test parsing a trade without quantity multiplier."""
        from src.core.parsers import parse_trading

        html = '''
        <table class="wikitable" style="text-align:center">
            <tbody>
                <tr>
                    <th colspan="9" data-description="Toolsmith">
                        <span class="nowrap">
                            <a href="/w/Toolsmith" title="Toolsmith">
                                <span class="sprite-text">Toolsmith</span>
                            </a>
                        </span>
                    </th>
                </tr>
                <tr>
                    <th rowspan="2">Level</th>
                    <th><i><a href="/w/Java_Edition" title="Java Edition">Java Edition</a></i></th>
                    <th rowspan="2">Item wanted</th>
                    <th rowspan="2">Item given</th>
                </tr>
                <tr>
                    <th>Probability</th>
                </tr>
                <tr>
                    <th>Journeyman</th>
                    <td>40%</td>
                    <td><span class="nowrap">
                        <a href="/w/Diamond" title="Diamond">
                            <span class="sprite-text">Diamond</span>
                        </a>
                    </span></td>
                    <td><span class="nowrap">
                        <a href="/w/Emerald" title="Emerald">
                            <span class="sprite-text">Emerald</span>
                        </a>
                    </span></td>
                </tr>
            </tbody>
        </table>
        '''

        result = parse_trading(html)

        assert len(result) == 1
        assert len(result[0].inputs) == 1  # 1 Diamond (default quantity)
        assert result[0].inputs[0].name == "Diamond"
        assert len(result[0].outputs) == 1
        assert result[0].outputs[0].name == "Emerald"

    def test_parse_trading_parses_all_editions(self):
        """Test that parse_trading now parses trades from all editions (both Bedrock and Java)."""
        from src.core.parsers import parse_trading

        html = '''
        <table class="wikitable" style="text-align:center">
            <tbody>
                <tr>
                    <th colspan="9" data-description="Farmer">
                        <span class="nowrap">
                            <a href="/w/Farmer" title="Farmer">
                                <span class="sprite-text">Farmer</span>
                            </a>
                        </span>
                    </th>
                </tr>
                <tr>
                    <th rowspan="2">Level</th>
                    <th><i><a href="/w/Bedrock_Edition" title="Bedrock Edition">Bedrock Edition</a></i></th>
                    <th rowspan="2">Item wanted</th>
                    <th rowspan="2">Item given</th>
                </tr>
                <tr>
                    <th>Probability</th>
                </tr>
                <tr>
                    <th>Novice</th>
                    <td>50%</td>
                    <td>20 × <span class="nowrap">
                        <a href="/w/Wheat" title="Wheat">
                            <span class="sprite-text">Wheat</span>
                        </a>
                    </span></td>
                    <td><span class="nowrap">
                        <a href="/w/Emerald" title="Emerald">
                            <span class="sprite-text">Emerald</span>
                        </a>
                    </span></td>
                </tr>
            </tbody>
        </table>
        '''

        result = parse_trading(html)

        # Should parse Bedrock Edition trades now (since both editions offer same trades)
        assert len(result) == 1
        assert result[0].inputs[0].name == "Wheat"
        assert result[0].outputs[0].name == "Emerald"
        assert result[0].metadata["villager_type"] == "Farmer"

    def test_parse_trading_multi_slot_trades(self):
        """Test parsing multiple trades in the same slot (rowspan structure)."""
        from src.core.parsers import parse_trading
        from src.core.data_models import TransformationType

        html = '''
        <table class="wikitable" style="text-align:center">
            <tbody>
                <tr>
                    <th colspan="9" data-description="Armorer">
                        <span class="nowrap">
                            <a href="/w/Armorer" title="Armorer">
                                <span class="sprite-text">Armorer</span>
                            </a>
                        </span>
                    </th>
                </tr>
                <tr>
                    <th rowspan="2">Level</th>
                    <th rowspan="2">Slot</th>
                    <th><i><a href="/w/Java_Edition" title="Java Edition">Java Edition</a></i></th>
                    <th rowspan="2">Item wanted</th>
                    <th rowspan="2">Item given</th>
                </tr>
                <tr>
                    <th>Probability</th>
                </tr>
                <tr>
                    <th rowspan="5">Apprentice</th>
                    <th rowspan="4">2</th>
                    <td>25%</td>
                    <td>5 × <span class="nowrap">
                        <a href="/w/Emerald" title="Emerald">
                            <span class="sprite-text">Emerald</span>
                        </a>
                    </span></td>
                    <td><span class="nowrap">
                        <a href="/w/Iron_Helmet" title="Iron Helmet">
                            <span class="sprite-text">Iron Helmet</span>
                        </a>
                    </span></td>
                </tr>
                <tr>
                    <td>25%</td>
                    <td>9 × <span class="nowrap">
                        <a href="/w/Emerald" title="Emerald">
                            <span class="sprite-text">Emerald</span>
                        </a>
                    </span></td>
                    <td><span class="nowrap">
                        <a href="/w/Iron_Chestplate" title="Iron Chestplate">
                            <span class="sprite-text">Iron Chestplate</span>
                        </a>
                    </span></td>
                </tr>
                <tr>
                    <td>25%</td>
                    <td>7 × <span class="nowrap">
                        <a href="/w/Emerald" title="Emerald">
                            <span class="sprite-text">Emerald</span>
                        </a>
                    </span></td>
                    <td><span class="nowrap">
                        <a href="/w/Iron_Leggings" title="Iron Leggings">
                            <span class="sprite-text">Iron Leggings</span>
                        </a>
                    </span></td>
                </tr>
                <tr>
                    <td>25%</td>
                    <td>4 × <span class="nowrap">
                        <a href="/w/Emerald" title="Emerald">
                            <span class="sprite-text">Emerald</span>
                        </a>
                    </span></td>
                    <td><span class="nowrap">
                        <a href="/w/Iron_Boots" title="Iron Boots">
                            <span class="sprite-text">Iron Boots</span>
                        </a>
                    </span></td>
                </tr>
            </tbody>
        </table>
        '''

        result = parse_trading(html)

        # Should parse all 4 armor pieces (multi-slot trades)
        assert len(result) == 4

        # Verify each armor piece is present
        armor_pieces = {t.outputs[0].name for t in result}
        assert "Iron Helmet" in armor_pieces
        assert "Iron Chestplate" in armor_pieces
        assert "Iron Leggings" in armor_pieces
        assert "Iron Boots" in armor_pieces

        # All should have Emerald as input and Armorer as villager type
        for trade in result:
            assert trade.transformation_type == TransformationType.TRADING
            assert trade.inputs[0].name == "Emerald"
            assert trade.metadata["villager_type"] == "Armorer"

    def test_parse_mob_drops_simple(self):
        """Test parsing mob drops."""
        from src.core.parsers import parse_mob_drops

        empty_html = "<html><body></body></html>"
        result = parse_mob_drops(empty_html, "Zombie")

        assert isinstance(result, list)

    def test_parse_mob_drops_from_main_table(self):
        """Test parsing mob drops from main drops table."""
        from src.core.parsers import parse_mob_drops

        html = '''
        <html><body>
        <h2><span class="mw-headline" id="Drops">Drops</span></h2>
        <table class="wikitable">
            <tr><th>Item</th><th>Amount</th><th>Chance</th></tr>
            <tr>
                <td><a href="/w/Rotten_Flesh" title="Rotten Flesh">Rotten Flesh</a></td>
                <td>0-2</td>
                <td>100%</td>
            </tr>
        </table>
        </body></html>
        '''

        result = parse_mob_drops(html, "Zombie")

        assert len(result) == 1
        assert result[0].outputs[0].name == "Rotten Flesh"
        assert result[0].inputs[0].name == "Zombie"

    def test_parse_mob_drops_from_subsection_with_table(self):
        """Test parsing mob drops from subsection with table."""
        from src.core.parsers import parse_mob_drops

        html = '''
        <html><body>
        <h2><span class="mw-headline" id="Drops">Drops</span></h2>
        <h3><span class="mw-headline" id="On_death">On death</span></h3>
        <table class="wikitable">
            <tr><th>Item</th></tr>
            <tr><td><a href="/w/Golden_Axe" title="Golden Axe">Golden Axe</a></td></tr>
            <tr><td><a href="/w/Gold_Ingot" title="Gold Ingot">Gold Ingot</a></td></tr>
        </table>
        </body></html>
        '''

        result = parse_mob_drops(html, "Piglin Brute")

        assert len(result) == 2
        item_names = {t.outputs[0].name for t in result}
        assert "Golden Axe" in item_names
        assert "Gold Ingot" in item_names

    def test_parse_mob_drops_from_gifts_section(self):
        """Test parsing mob drops from Gifts section (e.g., cat gifts)."""
        from src.core.parsers import parse_mob_drops

        html = '''
        <html><body>
        <h2><span class="mw-headline" id="Drops">Drops</span></h2>
        <table class="wikitable">
            <tr><th>Item</th></tr>
            <tr><td><a href="/w/String" title="String">String</a></td></tr>
        </table>
        <h3><span class="mw-headline" id="Gifts">Gifts</span></h3>
        <table class="wikitable">
            <tr><th>Item</th><th>Chance</th></tr>
            <tr><td><a href="/w/Rabbit%27s_Foot" title="Rabbit's Foot">Rabbit's Foot</a></td><td>16.13%</td></tr>
            <tr><td><a href="/w/Feather" title="Feather">Feather</a></td><td>16.13%</td></tr>
        </table>
        </body></html>
        '''

        result = parse_mob_drops(html, "Cat")

        assert len(result) >= 3
        item_names = {t.outputs[0].name for t in result}
        assert "String" in item_names
        assert "Rabbit's Foot" in item_names
        assert "Feather" in item_names

    def test_parse_mob_drops_ignores_experience(self):
        """Test that experience orbs are not treated as items."""
        from src.core.parsers import parse_mob_drops

        html = '''
        <html><body>
        <h2><span class="mw-headline" id="Drops">Drops</span></h2>
        <table class="wikitable">
            <tr><th>Item</th></tr>
            <tr><td><a href="/w/Experience" title="Experience">Experience</a></td></tr>
            <tr><td><a href="/w/String" title="String">String</a></td></tr>
        </table>
        </body></html>
        '''

        result = parse_mob_drops(html, "Spider")

        # Should only have String, not Experience
        assert len(result) == 1
        assert result[0].outputs[0].name == "String"

    def test_parse_mob_drops_deduplicates(self):
        """Test that same item from multiple sections is deduplicated."""
        from src.core.parsers import parse_mob_drops

        html = '''
        <html><body>
        <h2><span class="mw-headline" id="Drops">Drops</span></h2>
        <table class="wikitable">
            <tr><th>Item</th></tr>
            <tr><td><a href="/w/String" title="String">String</a></td></tr>
        </table>
        <h3><span class="mw-headline" id="On_death">On death</span></h3>
        <p>Also drops <a href="/w/String" title="String">String</a>.</p>
        </body></html>
        '''

        result = parse_mob_drops(html, "Spider")

        # Should only have one String transformation
        assert len(result) == 1
        assert result[0].outputs[0].name == "String"

    def test_parse_mob_drops_tadpole_zero_drops(self):
        """Test that tadpole correctly returns 0 drops (not biomes from Behavior section)."""
        from src.core.parsers import parse_mob_drops

        html = '''
        <html><body>
        <h2><span class="mw-headline" id="Drops">Drops</span></h2>
        <p>As with other baby animals, tadpoles do not drop any items or experience on death.</p>
        <h2><span class="mw-headline" id="Behavior">Behavior</span></h2>
        <table class="wikitable">
            <tr><th>Biome</th><th>Frog Variant</th></tr>
            <tr><td><a href="/w/River" title="River">River</a></td><td>Temperate</td></tr>
            <tr><td><a href="/w/Beach" title="Beach">Beach</a></td><td>Temperate</td></tr>
            <tr><td><a href="/w/Taiga" title="Taiga">Taiga</a></td><td>Cold</td></tr>
        </table>
        </body></html>
        '''

        result = parse_mob_drops(html, "Tadpole")

        # Should have 0 drops (biome links should not be extracted)
        assert len(result) == 0

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


class TestEducationEditionFiltering:
    """Tests for Education Edition content filtering."""

    def test_filters_infobox_links(self):
        """Test that links in infobox captions are filtered out."""
        html = '''
        <div class="infobox">
            <div class="infobox-imagecaption">
                <p><i><a href="/w/Bedrock_Edition" title="Bedrock Edition">Bedrock Edition</a></i></p>
            </div>
        </div>
        '''
        soup = BeautifulSoup(html, "lxml")
        link = soup.find("a")

        item = extract_item_from_link(link)

        assert item is None

    def test_filters_education_edition_chemistry_items(self):
        """Test that Education Edition chemistry items are filtered out."""
        html = '<a href="/w/Cerium_Chloride" title="Cerium Chloride">Cerium Chloride</a>'
        soup = BeautifulSoup(html, "lxml")
        link = soup.find("a")

        item = extract_item_from_link(link)

        assert item is None

    def test_filters_colored_torches(self):
        """Test that colored torches (Education Edition) are filtered out."""
        html = '<a href="/w/Blue_Torch" title="Blue Torch">Blue Torch</a>'
        soup = BeautifulSoup(html, "lxml")
        link = soup.find("a")

        item = extract_item_from_link(link)

        assert item is None

    def test_allows_java_edition_items(self):
        """Test that valid Java Edition items are NOT filtered."""
        html = '<a href="/w/Iron_Chain" title="Iron Chain">Iron Chain</a>'
        soup = BeautifulSoup(html, "lxml")
        link = soup.find("a")

        item = extract_item_from_link(link)

        assert item is not None
        assert item.name == "Iron Chain"

    def test_allows_copper_items(self):
        """Test that Java Edition copper items are NOT filtered despite 'Copper' being in blacklist."""
        html = '<a href="/w/Copper_Ingot" title="Copper Ingot">Copper Ingot</a>'
        soup = BeautifulSoup(html, "lxml")
        link = soup.find("a")

        item = extract_item_from_link(link)

        assert item is not None
        assert item.name == "Copper Ingot"

    def test_detects_inline_edition_markers(self):
        """Test that inline edition markers in table cells are detected."""
        html = '''
        <table>
            <tr>
                <td>
                    <span class="mcui mcui-Crafting_Table pixel-image">
                        <span class="mcui-output">
                            <span class="invslot">
                                <span class="invslot-item">
                                    <a href="/w/Blue_Sparkler" title="Blue Sparkler">Blue Sparkler</a>
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
        '''
        soup = BeautifulSoup(html, "lxml")
        element = soup.find("span", class_="mcui")

        assert is_java_edition(element) is False

    def test_allows_normal_table_content(self):
        """Test that normal table content without edition markers is accepted."""
        html = '''
        <table>
            <tr>
                <td>
                    <span class="mcui mcui-Crafting_Table pixel-image">
                        <span class="mcui-output">
                            <span class="invslot">
                                <span class="invslot-item">
                                    <a href="/w/Iron_Ingot" title="Iron Ingot">Iron Ingot</a>
                                </span>
                            </span>
                        </span>
                    </span>
                </td>
                <td>Regular crafting recipe</td>
            </tr>
        </table>
        '''
        soup = BeautifulSoup(html, "lxml")
        element = soup.find("span", class_="mcui")

        assert is_java_edition(element) is True


class TestParseComposting:
    """Tests for parse_composting function."""

    def test_parse_composting_empty_html(self):
        """Test that empty HTML returns empty list."""
        from src.core.parsers import parse_composting

        empty_html = "<html><body></body></html>"
        result = parse_composting(empty_html)

        assert isinstance(result, list)
        assert len(result) == 0

    def test_parse_composting_with_items(self):
        """Test parsing composting table with multiple items."""
        from src.core.parsers import parse_composting

        html = '''
        <html><body>
        <table class="wikitable">
            <tr>
                <td style="text-align:center">30%</td>
                <td style="text-align:center">50%</td>
                <td style="text-align:center">65%</td>
            </tr>
            <tr>
                <th colspan="6">Items</th>
            </tr>
            <tr>
                <td style="vertical-align:top">
                    <ul>
                        <li><a href="/w/Beetroot_Seeds" title="Beetroot Seeds">Beetroot Seeds</a></li>
                        <li><a href="/w/Kelp" title="Kelp">Kelp</a></li>
                    </ul>
                </td>
                <td style="vertical-align:top">
                    <ul>
                        <li><a href="/w/Cactus" title="Cactus">Cactus</a></li>
                        <li><a href="/w/Sugar_Cane" title="Sugar Cane">Sugar Cane</a></li>
                    </ul>
                </td>
                <td style="vertical-align:top">
                    <ul>
                        <li><a href="/w/Apple" title="Apple">Apple</a></li>
                        <li><a href="/w/Carrot" title="Carrot">Carrot</a></li>
                    </ul>
                </td>
            </tr>
        </table>
        </body></html>
        '''

        result = parse_composting(html)

        assert isinstance(result, list)
        assert len(result) == 6

        # Check that all items are parsed
        item_names = [t.inputs[0].name for t in result]
        assert "Beetroot Seeds" in item_names
        assert "Kelp" in item_names
        assert "Cactus" in item_names
        assert "Sugar Cane" in item_names
        assert "Apple" in item_names
        assert "Carrot" in item_names

        # Check that all outputs are bone meal
        for transformation in result:
            assert len(transformation.outputs) == 1
            assert transformation.outputs[0].name == "Bone Meal"

    def test_parse_composting_success_rates(self):
        """Test that success rates are correctly associated with items."""
        from src.core.parsers import parse_composting

        html = '''
        <html><body>
        <table class="wikitable">
            <tr>
                <td style="text-align:center">30%</td>
                <td style="text-align:center">65%</td>
            </tr>
            <tr>
                <th colspan="6">Items</th>
            </tr>
            <tr>
                <td style="vertical-align:top">
                    <ul>
                        <li><a href="/w/Kelp" title="Kelp">Kelp</a></li>
                    </ul>
                </td>
                <td style="vertical-align:top">
                    <ul>
                        <li><a href="/w/Apple" title="Apple">Apple</a></li>
                    </ul>
                </td>
            </tr>
        </table>
        </body></html>
        '''

        result = parse_composting(html)

        # Find transformations by item name
        kelp_transformation = next(t for t in result if t.inputs[0].name == "Kelp")
        apple_transformation = next(t for t in result if t.inputs[0].name == "Apple")

        # Check success rates
        assert kelp_transformation.metadata["success_rate"] == 0.3
        assert apple_transformation.metadata["success_rate"] == 0.65

    def test_parse_composting_deduplication(self):
        """Test that duplicate items are deduplicated."""
        from src.core.parsers import parse_composting

        html = '''
        <html><body>
        <table class="wikitable">
            <tr>
                <td style="text-align:center">30%</td>
            </tr>
            <tr>
                <th colspan="6">Items</th>
            </tr>
            <tr>
                <td style="vertical-align:top">
                    <ul>
                        <li><a href="/w/Kelp" title="Kelp">Kelp</a></li>
                        <li><a href="/w/Kelp" title="Kelp">Kelp</a></li>
                    </ul>
                </td>
            </tr>
        </table>
        </body></html>
        '''

        result = parse_composting(html)

        # Should only have one Kelp transformation despite duplicate links
        assert len(result) == 1
        assert result[0].inputs[0].name == "Kelp"

    def test_parse_composting_no_items_header(self):
        """Test that tables without Items header are skipped."""
        from src.core.parsers import parse_composting

        html = '''
        <html><body>
        <table class="wikitable">
            <tr>
                <th>Column 1</th>
                <th>Column 2</th>
            </tr>
            <tr>
                <td><a href="/w/Kelp" title="Kelp">Kelp</a></td>
                <td>30%</td>
            </tr>
        </table>
        </body></html>
        '''

        result = parse_composting(html)

        # Should return empty list since there's no Items header
        assert len(result) == 0

    def test_parse_composting_transformation_type(self):
        """Test that transformations have correct type."""
        from src.core.parsers import parse_composting
        from src.core.data_models import TransformationType

        html = '''
        <html><body>
        <table class="wikitable">
            <tr>
                <td style="text-align:center">30%</td>
            </tr>
            <tr>
                <th colspan="6">Items</th>
            </tr>
            <tr>
                <td style="vertical-align:top">
                    <ul>
                        <li><a href="/w/Kelp" title="Kelp">Kelp</a></li>
                    </ul>
                </td>
            </tr>
        </table>
        </body></html>
        '''

        result = parse_composting(html)

        assert len(result) == 1
        assert result[0].transformation_type == TransformationType.COMPOSTING


class TestParseBartering:
    """Tests for parse_bartering function."""

    def test_parse_bartering_basic(self):
        """Test parsing basic bartering table."""
        from src.core.parsers import parse_bartering

        empty_html = "<html><body></body></html>"
        result = parse_bartering(empty_html)

        assert isinstance(result, list)

    def test_parse_bartering_extracts_items(self):
        """Test that bartering parser extracts items correctly."""
        from src.core.parsers import parse_bartering
        from src.core.data_models import TransformationType

        html = '''
        <html><body>
        <table class="wikitable sortable">
            <caption>Bartering items</caption>
            <tbody>
                <tr>
                    <th>Item given</th>
                    <th>Quantity</th>
                    <th>Chance</th>
                    <th>Ingots needed</th>
                </tr>
                <tr>
                    <td>
                        <span class="nowrap">
                            <a href="/w/Ender_Pearl" title="Ender Pearl">
                                <span class="sprite-text">Ender Pearl</span>
                            </a>
                        </span>
                    </td>
                    <td>2-4</td>
                    <td>5⁄469<br />(~1.07%)</td>
                    <td>93.8</td>
                </tr>
                <tr>
                    <td>
                        <span class="nowrap">
                            <a href="/w/Fire_Charge" title="Fire Charge">
                                <span class="sprite-text">Fire Charge</span>
                            </a>
                        </span>
                    </td>
                    <td>1</td>
                    <td>10⁄469<br />(~2.13%)</td>
                    <td>46.9</td>
                </tr>
            </tbody>
        </table>
        </body></html>
        '''

        result = parse_bartering(html)

        assert len(result) == 2
        assert result[0].transformation_type == TransformationType.BARTERING
        assert result[1].transformation_type == TransformationType.BARTERING

        # Check that outputs are Ender Pearl and Fire Charge
        output_names = {t.outputs[0].name for t in result}
        assert "Ender Pearl" in output_names
        assert "Fire Charge" in output_names

    def test_parse_bartering_gold_ingot_input(self):
        """Test that all bartering transformations have Gold Ingot as input."""
        from src.core.parsers import parse_bartering

        html = '''
        <html><body>
        <table class="wikitable sortable">
            <tbody>
                <tr>
                    <th>Item given</th>
                    <th>Quantity</th>
                    <th>Chance</th>
                    <th>Ingots needed</th>
                </tr>
                <tr>
                    <td>
                        <a href="/w/Obsidian" title="Obsidian">Obsidian</a>
                    </td>
                    <td>1</td>
                    <td>10⁄469<br />(~2.13%)</td>
                    <td>46.9</td>
                </tr>
            </tbody>
        </table>
        </body></html>
        '''

        result = parse_bartering(html)

        assert len(result) == 1
        assert len(result[0].inputs) == 1
        assert result[0].inputs[0].name == "Gold Ingot"
        assert result[0].outputs[0].name == "Obsidian"

    def test_parse_bartering_filters_bedrock_items(self):
        """Test that Bedrock Edition items are filtered out."""
        from src.core.parsers import parse_bartering

        html = '''
        <html><body>
        <table class="wikitable sortable">
            <tbody>
                <tr>
                    <th>Item given</th>
                    <th>Quantity</th>
                    <th>Chance</th>
                    <th>Ingots needed</th>
                </tr>
                <tr>
                    <td>
                        <span class="nowrap">
                            <a href="/w/Spectral_Arrow" title="Spectral Arrow">Spectral Arrow</a>
                        </span>
                        [JE only]<br />
                        <span class="nowrap">
                            <a href="/w/Arrow" title="Arrow">Arrow</a>
                        </span>
                        [BE only]
                    </td>
                    <td>6-12</td>
                    <td>10⁄469<br />(~2.13%)</td>
                    <td>46.9</td>
                </tr>
            </tbody>
        </table>
        </body></html>
        '''

        result = parse_bartering(html)

        # Should only have Spectral Arrow (Java Edition), not Arrow (Bedrock Edition)
        output_names = [t.outputs[0].name for t in result]
        assert "Spectral Arrow" in output_names
        assert "Arrow" not in output_names

    def test_parse_bartering_empty_table(self):
        """Test handling of empty or missing table."""
        from src.core.parsers import parse_bartering

        html = '''
        <html><body>
        <table class="wikitable">
            <tbody>
                <tr>
                    <th>Wrong Header</th>
                </tr>
            </tbody>
        </table>
        </body></html>
        '''

        result = parse_bartering(html)

        assert isinstance(result, list)
        assert len(result) == 0

    def test_parse_bartering_deduplication(self):
        """Test that duplicate transformations are deduplicated."""
        from src.core.parsers import parse_bartering

        # Create HTML with duplicate items
        html = '''
        <html><body>
        <table class="wikitable sortable">
            <tbody>
                <tr>
                    <th>Item given</th>
                    <th>Quantity</th>
                    <th>Chance</th>
                    <th>Ingots needed</th>
                </tr>
                <tr>
                    <td>
                        <a href="/w/Gravel" title="Gravel">Gravel</a>
                    </td>
                    <td>8-16</td>
                    <td>20⁄469<br />(~4.27%)</td>
                    <td>23.45</td>
                </tr>
                <tr>
                    <td>
                        <a href="/w/Gravel" title="Gravel">Gravel</a>
                    </td>
                    <td>8-16</td>
                    <td>20⁄469<br />(~4.27%)</td>
                    <td>23.45</td>
                </tr>
            </tbody>
        </table>
        </body></html>
        '''

        result = parse_bartering(html)

        # Should deduplicate to single transformation
        assert len(result) == 1
        assert result[0].outputs[0].name == "Gravel"

    def test_parse_bartering_excludes_enchantments(self):
        """Test that enchantment links after 'with' text are not extracted as items."""
        from src.core.parsers import parse_bartering
        from src.core.data_models import TransformationType

        html = '''
        <html><body>
        <table class="wikitable sortable">
            <caption>Bartering items</caption>
            <tbody>
                <tr>
                    <th>Item given</th>
                    <th>Quantity</th>
                    <th>Chance</th>
                    <th>Ingots needed</th>
                </tr>
                <tr>
                    <td>
                        <span class="nowrap">
                            <a href="/w/Enchanted_Book" title="Enchanted Book">Enchanted Book</a>
                        </span>
                        <br />with <a href="/w/Soul_Speed" title="Soul Speed">Soul Speed</a> (random level)
                    </td>
                    <td>1</td>
                    <td>5⁄469<br />(~1.07%)</td>
                    <td>93.8</td>
                </tr>
                <tr>
                    <td>
                        <span class="nowrap">
                            <a href="/w/Iron_Boots" title="Iron Boots">Iron Boots</a>
                        </span>
                        <br />with <a href="/w/Soul_Speed" title="Soul Speed">Soul Speed</a> (random level)
                    </td>
                    <td>1</td>
                    <td>8⁄469<br />(~1.71%)</td>
                    <td>58.6</td>
                </tr>
            </tbody>
        </table>
        </body></html>
        '''

        result = parse_bartering(html)

        # Should extract exactly 2 items (Enchanted Book and Iron Boots)
        # Should NOT extract Soul Speed (it's an enchantment, not an item)
        assert len(result) == 2

        output_names = [t.outputs[0].name for t in result]
        assert "Enchanted Book" in output_names
        assert "Iron Boots" in output_names
        assert "Soul Speed" not in output_names

        # Verify all transformations have Gold Ingot as input
        for transformation in result:
            assert transformation.transformation_type == TransformationType.BARTERING
            assert len(transformation.inputs) == 1
            assert transformation.inputs[0].name == "Gold Ingot"
            assert len(transformation.outputs) == 1

    def test_parse_mob_drops_armadillo(self):
        """Test parsing armadillo mob drops from Brushing subsection."""
        from src.core.parsers import parse_mob_drops
        from src.core.data_models import TransformationType
        from pathlib import Path

        # Load actual armadillo HTML file
        html = Path('ai_doc/downloaded_pages/mobs/armadillo.html').read_text()

        result = parse_mob_drops(html, "Armadillo")

        # Should extract exactly 1 transformation: Armadillo -> Armadillo Scute
        assert len(result) == 1
        assert result[0].transformation_type == TransformationType.MOB_DROP
        assert result[0].inputs[0].name == "Armadillo"
        assert result[0].outputs[0].name == "Armadillo Scute"
