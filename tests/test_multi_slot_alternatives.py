"""Tests for crafting recipes with multiple alternative slots."""

import pytest
from bs4 import BeautifulSoup
from src.core.parsers import parse_crafting


class TestMultiSlotAlternatives:
    """Tests for recipes with multiple slots containing animated alternatives."""

    def test_wool_dyeing_with_matching_dye(self):
        """Test that wool + dye recipes include both wool AND dye in inputs."""
        # HTML mimicking the wiki structure for "Any Wool + Matching Dye"
        # This has TWO animated slots: one with all wool colors, one with all dye colors
        html = '''
        <html><body>
        <table class="wikitable">
            <tr>
                <th>Wool</th>
                <td>Any Wool + Matching Dye</td>
                <td>
                    <span class="mcui mcui-Crafting_Table pixel-image">
                        <span class="mcui-input">
                            <span class="mcui-row">
                                <span class="invslot"></span>
                                <span class="invslot"></span>
                                <span class="invslot"></span>
                            </span>
                            <span class="mcui-row">
                                <!-- First animated slot: All wool colors -->
                                <span class="invslot animated">
                                    <span class="invslot-item">
                                        <a href="/w/White_Wool" title="White Wool">White Wool</a>
                                    </span>
                                    <span class="invslot-item">
                                        <a href="/w/Green_Wool" title="Green Wool">Green Wool</a>
                                    </span>
                                    <span class="invslot-item">
                                        <a href="/w/Blue_Wool" title="Blue Wool">Blue Wool</a>
                                    </span>
                                    <span class="invslot-item">
                                        <a href="/w/Red_Wool" title="Red Wool">Red Wool</a>
                                    </span>
                                </span>
                                <!-- Second animated slot: All matching dye colors -->
                                <span class="invslot animated">
                                    <span class="invslot-item">
                                        <a href="/w/White_Dye" title="White Dye">White Dye</a>
                                    </span>
                                    <span class="invslot-item">
                                        <a href="/w/Green_Dye" title="Green Dye">Green Dye</a>
                                    </span>
                                    <span class="invslot-item">
                                        <a href="/w/Blue_Dye" title="Blue Dye">Blue Dye</a>
                                    </span>
                                    <span class="invslot-item">
                                        <a href="/w/Red_Dye" title="Red Dye">Red Dye</a>
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
                            <!-- Output: matching colored wool -->
                            <span class="invslot invslot-large animated">
                                <span class="invslot-item">
                                    <a href="/w/White_Wool" title="White Wool">White Wool</a>
                                </span>
                                <span class="invslot-item">
                                    <a href="/w/Green_Wool" title="Green Wool">Green Wool</a>
                                </span>
                                <span class="invslot-item">
                                    <a href="/w/Blue_Wool" title="Blue Wool">Blue Wool</a>
                                </span>
                                <span class="invslot-item">
                                    <a href="/w/Red_Wool" title="Red Wool">Red Wool</a>
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

        # Should create 4 transformations (one per color)
        assert len(result) == 4, f"Expected 4 transformations, got {len(result)}"

        # Check that each transformation has both wool AND dye in inputs
        for transformation in result:
            input_names = [item.name for item in transformation.inputs]

            # Each transformation should have exactly 2 inputs: wool + dye
            assert len(input_names) == 2, f"Expected 2 inputs, got {len(input_names)}: {input_names}"

            # One input should be wool, one should be dye
            has_wool = any("Wool" in name for name in input_names)
            has_dye = any("Dye" in name for name in input_names)

            assert has_wool, f"Missing wool in inputs: {input_names}"
            assert has_dye, f"Missing dye in inputs: {input_names}"

        # Check specific color pairings (green wool + green dye → green wool)
        green_transformation = next(
            (t for t in result if any("Green Wool" in item.name for item in t.outputs)),
            None
        )
        assert green_transformation is not None, "Green Wool transformation not found"

        input_names = [item.name for item in green_transformation.inputs]
        assert "Green Wool" in input_names, f"Green Wool not in inputs: {input_names}"
        assert "Green Dye" in input_names, f"Green Dye not in inputs: {input_names}"

        # Verify output is correct
        assert len(green_transformation.outputs) == 1
        assert green_transformation.outputs[0].name == "Green Wool"

        # Verify metadata indicates alternatives
        assert green_transformation.metadata.get("has_alternatives") is True

    def test_single_alternative_slot_still_works(self):
        """Test that recipes with only ONE alternative slot still work correctly."""
        # Example: Bookshelf can be made with any wood planks + book
        html = '''
        <html><body>
        <span class="mcui mcui-Crafting_Table">
            <span class="mcui-input">
                <span class="mcui-row">
                    <span class="invslot animated">
                        <span class="invslot-item">
                            <a href="/w/Oak_Planks" title="Oak Planks">Oak Planks</a>
                        </span>
                        <span class="invslot-item">
                            <a href="/w/Spruce_Planks" title="Spruce Planks">Spruce Planks</a>
                        </span>
                    </span>
                    <span class="invslot">
                        <span class="invslot-item">
                            <a href="/w/Book" title="Book">Book</a>
                        </span>
                    </span>
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
                        <a href="/w/Bookshelf" title="Bookshelf">Bookshelf</a>
                    </span>
                </span>
            </span>
        </span>
        </body></html>
        '''

        result = parse_crafting(html)

        # Should create 2 transformations (one per wood type)
        assert len(result) == 2

        # Each should have planks + book as inputs
        for transformation in result:
            input_names = [item.name for item in transformation.inputs]
            assert len(input_names) == 2
            assert "Book" in input_names
            assert any("Planks" in name for name in input_names)

    def test_mismatched_alternative_counts_uses_first_slot(self):
        """Test that when alternative slots have different counts, only first varies."""
        # Hypothetical recipe with 3 alternatives in first slot, 2 in second
        html = '''
        <html><body>
        <span class="mcui mcui-Crafting_Table">
            <span class="mcui-input">
                <span class="mcui-row">
                    <span class="invslot animated">
                        <span class="invslot-item">
                            <a href="/w/Iron_Ingot" title="Iron Ingot">Iron Ingot</a>
                        </span>
                        <span class="invslot-item">
                            <a href="/w/Gold_Ingot" title="Gold Ingot">Gold Ingot</a>
                        </span>
                        <span class="invslot-item">
                            <a href="/w/Diamond" title="Diamond">Diamond</a>
                        </span>
                    </span>
                    <span class="invslot animated">
                        <span class="invslot-item">
                            <a href="/w/Stick" title="Stick">Stick</a>
                        </span>
                        <span class="invslot-item">
                            <a href="/w/Blaze_Rod" title="Blaze Rod">Blaze Rod</a>
                        </span>
                    </span>
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
                        <a href="/w/Pickaxe" title="Pickaxe">Pickaxe</a>
                    </span>
                </span>
            </span>
        </span>
        </body></html>
        '''

        result = parse_crafting(html)

        # With mismatched counts, should fall back to varying only first slot
        # So we expect 3 transformations (iron+stick, gold+stick, diamond+stick)
        # NOT 2 or 6 - just 3 based on first slot
        assert len(result) == 3

        # Each should have one item from first slot
        material_names = {"Iron Ingot", "Gold Ingot", "Diamond"}
        found_materials = set()

        for transformation in result:
            input_names = [item.name for item in transformation.inputs]
            # Should have one material from first slot
            materials = [name for name in input_names if name in material_names]
            assert len(materials) == 1
            found_materials.add(materials[0])

        # All three materials should appear
        assert found_materials == material_names
