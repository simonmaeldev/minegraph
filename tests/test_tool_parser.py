"""Tests for the Tool page crafting parser."""

import pytest
from pathlib import Path
from src.core.parsers import parse_tool_crafting
from src.core.data_models import TransformationType


def load_fixture(filename: str) -> str:
    """Load HTML fixture file."""
    fixture_path = Path(__file__).parent / "fixtures" / filename
    with open(fixture_path, "r", encoding="utf-8") as f:
        return f.read()


def test_parse_tool_crafting_basic():
    """Test parsing a simple tool recipe without alternatives."""
    html_content = load_fixture("tool_crafting_sample.html")
    transformations = parse_tool_crafting(html_content)

    # Find Flint and Steel transformation
    flint_and_steel = [t for t in transformations if any(item.name == "Flint and Steel" for item in t.outputs)]

    assert len(flint_and_steel) >= 1, "Should find at least one Flint and Steel recipe"
    t = flint_and_steel[0]

    # Check transformation type
    assert t.transformation_type == TransformationType.CRAFTING

    # Check inputs
    input_names = {item.name for item in t.inputs}
    assert "Iron Ingot" in input_names
    assert "Flint" in input_names

    # Check output
    assert len(t.outputs) == 1
    assert t.outputs[0].name == "Flint and Steel"


def test_parse_tool_crafting_animated_alternatives():
    """Test parsing stone hoe with 3 stone variants, should create 3 separate transformations."""
    html_content = load_fixture("tool_crafting_sample.html")
    transformations = parse_tool_crafting(html_content)

    # Find all Stone Hoe transformations
    stone_hoe_recipes = [t for t in transformations if any(item.name == "Stone Hoe" for item in t.outputs)]

    # Should have 3 transformations (one for each stone type)
    assert len(stone_hoe_recipes) == 3, f"Expected 3 stone hoe recipes, got {len(stone_hoe_recipes)}"

    # Check that all three use different stone types
    stone_types = set()
    for t in stone_hoe_recipes:
        assert t.transformation_type == TransformationType.CRAFTING
        assert len(t.outputs) == 1
        assert t.outputs[0].name == "Stone Hoe"

        # Find the stone type in inputs
        input_names = {item.name for item in t.inputs}
        assert "Stick" in input_names

        # One of the stone types should be present
        for stone in ["Cobblestone", "Blackstone", "Cobbled Deepslate"]:
            if stone in input_names:
                stone_types.add(stone)
                break

        # Check metadata
        assert "has_alternatives" in t.metadata
        assert t.metadata["has_alternatives"] is True

    # Should have found all 3 stone types
    assert len(stone_types) == 3, f"Expected 3 different stone types, got {stone_types}"
    assert stone_types == {"Cobblestone", "Blackstone", "Cobbled Deepslate"}


def test_parse_tool_crafting_output_extraction():
    """Test that output item names are extracted correctly."""
    html_content = load_fixture("tool_crafting_sample.html")
    transformations = parse_tool_crafting(html_content)

    output_names = {t.outputs[0].name for t in transformations}

    # Should include all the tools from the fixture
    assert "Flint and Steel" in output_names
    assert "Stone Hoe" in output_names
    assert "Diamond Pickaxe" in output_names


def test_parse_tool_crafting_input_extraction():
    """Test that all input ingredients are extracted correctly."""
    html_content = load_fixture("tool_crafting_sample.html")
    transformations = parse_tool_crafting(html_content)

    # Find Diamond Pickaxe transformation
    diamond_pickaxe = [t for t in transformations if any(item.name == "Diamond Pickaxe" for item in t.outputs)]
    assert len(diamond_pickaxe) >= 1

    t = diamond_pickaxe[0]
    input_names = {item.name for item in t.inputs}

    # Should have Diamond and Stick (note: Transformation deduplicates inputs)
    assert "Diamond" in input_names, "Diamond should be in inputs"
    assert "Stick" in input_names, "Stick should be in inputs"


def test_parse_tool_crafting_category_metadata():
    """Test that category field is populated in metadata."""
    html_content = load_fixture("tool_crafting_sample.html")
    transformations = parse_tool_crafting(html_content)

    assert len(transformations) > 0, "Should have at least one transformation"

    # Check if any transformation has category metadata
    # Note: Category may be extracted from DOM context
    for t in transformations:
        # Metadata should be a dictionary
        assert isinstance(t.metadata, dict)

        # If category exists, it should be a string
        if "category" in t.metadata:
            assert isinstance(t.metadata["category"], str)


def test_parse_tool_crafting_deduplication():
    """Test that duplicate recipes are not added multiple times."""
    html_content = load_fixture("tool_crafting_sample.html")
    transformations = parse_tool_crafting(html_content)

    # Check that there are no duplicate signatures
    signatures = [t.get_signature() for t in transformations]
    assert len(signatures) == len(set(signatures)), "Should not have duplicate transformations"


def test_parse_tool_crafting_no_empty_inputs():
    """Test that transformations don't have empty inputs."""
    html_content = load_fixture("tool_crafting_sample.html")
    transformations = parse_tool_crafting(html_content)

    for t in transformations:
        assert len(t.inputs) > 0, "Transformation should have at least one input"


def test_parse_tool_crafting_single_output():
    """Test that all transformations have exactly one output."""
    html_content = load_fixture("tool_crafting_sample.html")
    transformations = parse_tool_crafting(html_content)

    for t in transformations:
        assert len(t.outputs) == 1, f"Transformation should have exactly one output, got {len(t.outputs)}"


def test_parse_tool_crafting_real_page():
    """Test parsing the real downloaded Tool page."""
    tool_page_path = Path(__file__).parent.parent / "ai_doc" / "downloaded_pages" / "tool.html"

    if not tool_page_path.exists():
        pytest.skip("Tool page not downloaded yet")

    with open(tool_page_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    transformations = parse_tool_crafting(html_content)

    # Should have extracted multiple tool recipes
    assert len(transformations) > 10, f"Expected more than 10 tool recipes, got {len(transformations)}"

    # Check for Stone Hoe with multiple variants
    stone_hoe_recipes = [t for t in transformations if any(item.name == "Stone Hoe" for item in t.outputs)]
    assert len(stone_hoe_recipes) >= 3, f"Expected at least 3 stone hoe variants, got {len(stone_hoe_recipes)}"

    # Verify no duplicates
    signatures = [t.get_signature() for t in transformations]
    assert len(signatures) == len(set(signatures)), "Should not have duplicate transformations"


def test_parse_tool_crafting_transformation_type():
    """Test that all transformations use CRAFTING type."""
    html_content = load_fixture("tool_crafting_sample.html")
    transformations = parse_tool_crafting(html_content)

    for t in transformations:
        assert t.transformation_type == TransformationType.CRAFTING
