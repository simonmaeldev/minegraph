"""Tests for category extraction from crafting wiki pages."""

import pytest
from bs4 import BeautifulSoup
from src.core.parsers import extract_category_from_element


class TestExtractCategoryFromElement:
    """Test the extract_category_from_element helper function."""

    def test_category_from_h2_heading(self):
        """Test extracting category from h2 heading."""
        html = """
        <div>
            <h2><span class="mw-headline" id="Building_blocks">Building blocks</span></h2>
            <div>
                <span class="mcui-Crafting-Table">
                    <span class="mcui-input"></span>
                    <span class="mcui-output"></span>
                </span>
            </div>
        </div>
        """
        soup = BeautifulSoup(html, "lxml")
        crafting_ui = soup.find("span", class_="mcui-Crafting-Table")
        category = extract_category_from_element(crafting_ui)
        assert category == "building_blocks"

    def test_category_from_h3_heading(self):
        """Test extracting category from h3 heading."""
        html = """
        <div>
            <h3><span class="mw-headline" id="Redstone">Redstone</span></h3>
            <div>
                <span class="mcui-Crafting-Table">
                    <span class="mcui-input"></span>
                    <span class="mcui-output"></span>
                </span>
            </div>
        </div>
        """
        soup = BeautifulSoup(html, "lxml")
        crafting_ui = soup.find("span", class_="mcui-Crafting-Table")
        category = extract_category_from_element(crafting_ui)
        assert category == "redstone"

    def test_category_normalization_with_spaces(self):
        """Test that category names with spaces are normalized."""
        html = """
        <div>
            <h2><span class="mw-headline" id="Decoration_blocks">Decoration blocks</span></h2>
            <div>
                <span class="mcui-Crafting-Table">
                    <span class="mcui-input"></span>
                    <span class="mcui-output"></span>
                </span>
            </div>
        </div>
        """
        soup = BeautifulSoup(html, "lxml")
        crafting_ui = soup.find("span", class_="mcui-Crafting-Table")
        category = extract_category_from_element(crafting_ui)
        assert category == "decoration_blocks"

    def test_category_normalization_with_special_chars(self):
        """Test that special characters are removed from category names."""
        html = """
        <div>
            <h2><span class="mw-headline" id="Test">Test: Category!</span></h2>
            <div>
                <span class="mcui-Crafting-Table">
                    <span class="mcui-input"></span>
                    <span class="mcui-output"></span>
                </span>
            </div>
        </div>
        """
        soup = BeautifulSoup(html, "lxml")
        crafting_ui = soup.find("span", class_="mcui-Crafting-Table")
        category = extract_category_from_element(crafting_ui)
        assert category == "test_category"

    def test_no_heading_found(self):
        """Test that None is returned when no heading is found."""
        html = """
        <div>
            <span class="mcui-Crafting-Table">
                <span class="mcui-input"></span>
                <span class="mcui-output"></span>
            </span>
        </div>
        """
        soup = BeautifulSoup(html, "lxml")
        crafting_ui = soup.find("span", class_="mcui-Crafting-Table")
        category = extract_category_from_element(crafting_ui)
        assert category is None

    def test_excluded_section_removed_recipes(self):
        """Test that excluded sections return None."""
        html = """
        <div>
            <h2><span class="mw-headline" id="Removed_recipes">Removed recipes</span></h2>
            <div>
                <span class="mcui-Crafting-Table">
                    <span class="mcui-input"></span>
                    <span class="mcui-output"></span>
                </span>
            </div>
        </div>
        """
        soup = BeautifulSoup(html, "lxml")
        crafting_ui = soup.find("span", class_="mcui-Crafting-Table")
        category = extract_category_from_element(crafting_ui)
        assert category is None

    def test_excluded_section_changed_recipes(self):
        """Test that Changed_recipes section returns None."""
        html = """
        <div>
            <h2><span class="mw-headline" id="Changed_recipes">Changed recipes</span></h2>
            <div>
                <span class="mcui-Crafting-Table">
                    <span class="mcui-input"></span>
                    <span class="mcui-output"></span>
                </span>
            </div>
        </div>
        """
        soup = BeautifulSoup(html, "lxml")
        crafting_ui = soup.find("span", class_="mcui-Crafting-Table")
        category = extract_category_from_element(crafting_ui)
        assert category is None

    def test_nested_elements(self):
        """Test category extraction with nested DOM structure."""
        html = """
        <div>
            <h2><span class="mw-headline" id="Transportation">Transportation</span></h2>
            <div>
                <div>
                    <div>
                        <span class="mcui-Crafting-Table">
                            <span class="mcui-input"></span>
                            <span class="mcui-output"></span>
                        </span>
                    </div>
                </div>
            </div>
        </div>
        """
        soup = BeautifulSoup(html, "lxml")
        crafting_ui = soup.find("span", class_="mcui-Crafting-Table")
        category = extract_category_from_element(crafting_ui)
        assert category == "transportation"

    def test_multiple_headings_uses_closest(self):
        """Test that the closest (most specific) heading is used."""
        html = """
        <div>
            <h2><span class="mw-headline" id="General">General</span></h2>
            <div>
                <h3><span class="mw-headline" id="Combat">Combat</span></h3>
                <div>
                    <span class="mcui-Crafting-Table">
                        <span class="mcui-input"></span>
                        <span class="mcui-output"></span>
                    </span>
                </div>
            </div>
        </div>
        """
        soup = BeautifulSoup(html, "lxml")
        crafting_ui = soup.find("span", class_="mcui-Crafting-Table")
        category = extract_category_from_element(crafting_ui)
        # Should use the closest heading (Combat), not the higher level one
        assert category == "combat"

    def test_lowercase_conversion(self):
        """Test that category names are converted to lowercase."""
        html = """
        <div>
            <h2><span class="mw-headline" id="MATERIALS">MATERIALS</span></h2>
            <div>
                <span class="mcui-Crafting-Table">
                    <span class="mcui-input"></span>
                    <span class="mcui-output"></span>
                </span>
            </div>
        </div>
        """
        soup = BeautifulSoup(html, "lxml")
        crafting_ui = soup.find("span", class_="mcui-Crafting-Table")
        category = extract_category_from_element(crafting_ui)
        assert category == "materials"

    def test_mixed_case_normalization(self):
        """Test that mixed case is normalized properly."""
        html = """
        <div>
            <h2><span class="mw-headline" id="Utilities">Utilities and Tools</span></h2>
            <div>
                <span class="mcui-Crafting-Table">
                    <span class="mcui-input"></span>
                    <span class="mcui-output"></span>
                </span>
            </div>
        </div>
        """
        soup = BeautifulSoup(html, "lxml")
        crafting_ui = soup.find("span", class_="mcui-Crafting-Table")
        category = extract_category_from_element(crafting_ui)
        assert category == "utilities_and_tools"
