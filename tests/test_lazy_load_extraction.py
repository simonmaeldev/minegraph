"""Tests for lazy-load detection and extraction functionality."""

import pytest
from bs4 import BeautifulSoup
from src.core.lazy_load_detector import find_lazy_load_pages
from src.core.parsers import is_java_edition


def test_find_lazy_load_pages_basic():
    """Test basic lazy-load page detection."""
    html = """
    <html>
        <body>
            <div class="load-page" data-page="Crafting/Building blocks">
                <h3>Building blocks</h3>
            </div>
            <div class="load-page" data-page="Crafting/Decoration blocks">
                <h3>Decoration blocks</h3>
            </div>
            <div class="load-page" data-page="Crafting/Tools">
                <h3>Tools</h3>
            </div>
        </body>
    </html>
    """

    urls = find_lazy_load_pages(html)

    assert len(urls) == 3
    assert "https://minecraft.wiki/w/Crafting/Building_blocks" in urls
    assert "https://minecraft.wiki/w/Crafting/Decoration_blocks" in urls
    assert "https://minecraft.wiki/w/Crafting/Tools" in urls


def test_find_lazy_load_pages_filters_changed_recipes():
    """Test that Changed recipes sections are filtered out."""
    html = """
    <html>
        <body>
            <div class="load-page" data-page="Crafting/Building blocks">
                <h3>Building blocks</h3>
            </div>
            <div class="load-page" data-page="Crafting/Changed recipes">
                <h3>Changed recipes</h3>
            </div>
            <div class="load-page" data-page="Crafting/Tools">
                <h3>Tools</h3>
            </div>
        </body>
    </html>
    """

    urls = find_lazy_load_pages(html)

    assert len(urls) == 2
    assert "https://minecraft.wiki/w/Crafting/Building_blocks" in urls
    assert "https://minecraft.wiki/w/Crafting/Tools" in urls
    assert "https://minecraft.wiki/w/Crafting/Changed_recipes" not in urls


def test_find_lazy_load_pages_filters_removed_recipes():
    """Test that Removed recipes sections are filtered out."""
    html = """
    <html>
        <body>
            <div class="load-page" data-page="Crafting/Building blocks">
                <h3>Building blocks</h3>
            </div>
            <div class="load-page" data-page="Crafting/Removed recipes">
                <h3>Removed recipes</h3>
            </div>
        </body>
    </html>
    """

    urls = find_lazy_load_pages(html)

    assert len(urls) == 1
    assert "https://minecraft.wiki/w/Crafting/Building_blocks" in urls
    assert "https://minecraft.wiki/w/Crafting/Removed_recipes" not in urls


def test_find_lazy_load_pages_handles_empty_data_page():
    """Test handling of divs without data-page attribute."""
    html = """
    <html>
        <body>
            <div class="load-page">
                <h3>No data-page attribute</h3>
            </div>
            <div class="load-page" data-page="Crafting/Building blocks">
                <h3>Building blocks</h3>
            </div>
        </body>
    </html>
    """

    urls = find_lazy_load_pages(html)

    assert len(urls) == 1
    assert "https://minecraft.wiki/w/Crafting/Building_blocks" in urls


def test_find_lazy_load_pages_no_load_divs():
    """Test handling of HTML with no load-page divs."""
    html = """
    <html>
        <body>
            <div class="normal-div">
                <h3>Not a load-page</h3>
            </div>
        </body>
    </html>
    """

    urls = find_lazy_load_pages(html)

    assert len(urls) == 0


def test_is_java_edition_filters_bedrock():
    """Test that Bedrock Edition content is filtered out."""
    html = """
    <div>
        <span>Recipe for Bedrock Edition</span>
    </div>
    """
    soup = BeautifulSoup(html, "lxml")
    element = soup.find("div")

    assert is_java_edition(element) is False


def test_is_java_edition_filters_education():
    """Test that Minecraft Education content is filtered out."""
    html = """
    <div>
        <span>Recipe for Minecraft Education</span>
    </div>
    """
    soup = BeautifulSoup(html, "lxml")
    element = soup.find("div")

    assert is_java_edition(element) is False


def test_is_java_edition_accepts_java_content():
    """Test that Java Edition content is accepted."""
    html = """
    <div>
        <span>Recipe for Java Edition</span>
    </div>
    """
    soup = BeautifulSoup(html, "lxml")
    element = soup.find("div")

    assert is_java_edition(element) is True


def test_is_java_edition_accepts_unspecified_content():
    """Test that unspecified content defaults to Java Edition."""
    html = """
    <div>
        <span>Standard recipe with no edition specified</span>
    </div>
    """
    soup = BeautifulSoup(html, "lxml")
    element = soup.find("div")

    assert is_java_edition(element) is True


def test_is_java_edition_filters_bedrock_in_parent():
    """Test that Bedrock Edition in parent section is filtered."""
    html = """
    <section>
        <h2>Bedrock Edition recipes</h2>
        <div>
            <span>Some recipe</span>
        </div>
    </section>
    """
    soup = BeautifulSoup(html, "lxml")
    element = soup.find("div")

    assert is_java_edition(element) is False
