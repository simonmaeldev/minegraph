"""Tests for excluding historical/obsolete recipe sections."""

import pytest
from bs4 import BeautifulSoup
from src.core.parsers import is_in_excluded_section, parse_crafting, EXCLUDED_CRAFTING_SECTIONS


class TestIsInExcludedSection:
    """Tests for is_in_excluded_section helper function."""

    def test_detects_removed_recipes_section(self):
        """Test that elements within Removed_recipes section are detected."""
        html = '''
        <html><body>
        <h3><span class="mw-headline" id="Removed_recipes">Removed recipes</span></h3>
        <p>Some text</p>
        <table>
            <tr>
                <td>
                    <span class="mcui mcui-Crafting_Table">Recipe UI</span>
                </td>
            </tr>
        </table>
        </body></html>
        '''
        soup = BeautifulSoup(html, "lxml")
        element = soup.find("span", class_="mcui")

        assert is_in_excluded_section(element) is True

    def test_detects_changed_recipes_section(self):
        """Test that elements within Changed_recipes section are detected."""
        html = '''
        <html><body>
        <h3><span class="mw-headline" id="Changed_recipes">Changed recipes</span></h3>
        <div>
            <span class="mcui mcui-Crafting_Table">Recipe UI</span>
        </div>
        </body></html>
        '''
        soup = BeautifulSoup(html, "lxml")
        element = soup.find("span", class_="mcui")

        assert is_in_excluded_section(element) is True

    def test_accepts_valid_section(self):
        """Test that elements in valid sections are not flagged."""
        html = '''
        <html><body>
        <h3><span class="mw-headline" id="Current_recipes">Current recipes</span></h3>
        <span class="mcui mcui-Crafting_Table">Recipe UI</span>
        </body></html>
        '''
        soup = BeautifulSoup(html, "lxml")
        element = soup.find("span", class_="mcui")

        assert is_in_excluded_section(element) is False

    def test_accepts_element_with_no_section(self):
        """Test that elements without any section heading are accepted."""
        html = '''
        <html><body>
        <span class="mcui mcui-Crafting_Table">Recipe UI</span>
        </body></html>
        '''
        soup = BeautifulSoup(html, "lxml")
        element = soup.find("span", class_="mcui")

        assert is_in_excluded_section(element) is False

    def test_custom_excluded_ids(self):
        """Test that custom excluded IDs can be passed."""
        html = '''
        <html><body>
        <h3><span class="mw-headline" id="Experimental">Experimental</span></h3>
        <span class="mcui mcui-Crafting_Table">Recipe UI</span>
        </body></html>
        '''
        soup = BeautifulSoup(html, "lxml")
        element = soup.find("span", class_="mcui")

        # Should not be excluded with default set
        assert is_in_excluded_section(element) is False

        # Should be excluded with custom set
        assert is_in_excluded_section(element, {"Experimental"}) is True


class TestParseCraftingExclusions:
    """Integration tests for parse_crafting with exclusions."""

    def test_excludes_removed_recipes_section(self):
        """Test that parse_crafting excludes recipes from Removed_recipes section."""
        html = '''
        <html><body>
        <h3><span class="mw-headline" id="Removed_recipes">Removed recipes</span></h3>
        <p>These recipes have been removed from the game.</p>
        <table class="wikitable">
            <tr>
                <td>
                    <span class="mcui mcui-Crafting_Table pixel-image">
                        <span class="mcui-input">
                            <span class="mcui-row">
                                <span class="invslot">
                                    <span class="invslot-item">
                                        <a href="/w/Diamond" title="Diamond">Diamond</a>
                                    </span>
                                </span>
                                <span class="invslot"></span>
                                <span class="invslot"></span>
                            </span>
                        </span>
                        <span class="mcui-arrow"></span>
                        <span class="mcui-output">
                            <span class="invslot invslot-large">
                                <span class="invslot-item">
                                    <a href="/w/Removed_Item" title="Removed Item">Removed Item</a>
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

        # The removed recipe should be excluded
        assert len(result) == 0

    def test_excludes_changed_recipes_section(self):
        """Test that parse_crafting excludes recipes from Changed_recipes section."""
        html = '''
        <html><body>
        <h3><span class="mw-headline" id="Changed_recipes">Changed recipes</span></h3>
        <p>These recipes have been changed.</p>
        <div>
            <span class="mcui mcui-Crafting_Table pixel-image">
                <span class="mcui-input">
                    <span class="mcui-row">
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
                            <a href="/w/Old_Recipe" title="Old Recipe">Old Recipe</a>
                        </span>
                    </span>
                </span>
            </span>
        </div>
        </body></html>
        '''

        result = parse_crafting(html)

        # The changed recipe should be excluded
        assert len(result) == 0

    def test_accepts_valid_current_recipes(self):
        """Test that parse_crafting accepts recipes from valid sections."""
        html = '''
        <html><body>
        <h3><span class="mw-headline" id="Blocks">Blocks</span></h3>
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

        # Valid recipe should be accepted
        assert len(result) == 1
        assert result[0].inputs[0].name == "Iron Ingot"
        assert result[0].outputs[0].name == "Block of Iron"

    def test_mixed_sections(self):
        """Test that valid recipes are accepted while removed ones are excluded."""
        html = '''
        <html><body>
        <h3><span class="mw-headline" id="Blocks">Blocks</span></h3>
        <span class="mcui mcui-Crafting_Table pixel-image">
            <span class="mcui-input">
                <span class="mcui-row">
                    <span class="invslot">
                        <span class="invslot-item">
                            <a href="/w/Diamond" title="Diamond">Diamond</a>
                        </span>
                    </span>
                </span>
            </span>
            <span class="mcui-arrow"></span>
            <span class="mcui-output">
                <span class="invslot invslot-large">
                    <span class="invslot-item">
                        <a href="/w/Diamond_Block" title="Diamond Block">Diamond Block</a>
                    </span>
                </span>
            </span>
        </span>

        <h3><span class="mw-headline" id="Removed_recipes">Removed recipes</span></h3>
        <span class="mcui mcui-Crafting_Table pixel-image">
            <span class="mcui-input">
                <span class="mcui-row">
                    <span class="invslot">
                        <span class="invslot-item">
                            <a href="/w/Gold_Ingot" title="Gold Ingot">Gold Ingot</a>
                        </span>
                    </span>
                </span>
            </span>
            <span class="mcui-arrow"></span>
            <span class="mcui-output">
                <span class="invslot invslot-large">
                    <span class="invslot-item">
                        <a href="/w/Removed_Item" title="Removed Item">Removed Item</a>
                    </span>
                </span>
            </span>
        </span>
        </body></html>
        '''

        result = parse_crafting(html)

        # Only the valid recipe should be included
        assert len(result) == 1
        assert result[0].inputs[0].name == "Diamond"
        assert result[0].outputs[0].name == "Diamond Block"
