"""Unit tests for data models."""

import pytest
from src.core.data_models import Item, Transformation, TransformationType


class TestItem:
    """Tests for Item data model."""

    def test_item_creation(self):
        """Test creating an Item with name and URL."""
        item = Item(name="Iron Ingot", url="https://minecraft.wiki/w/Iron_Ingot")
        assert item.name == "Iron Ingot"
        assert item.url == "https://minecraft.wiki/w/Iron_Ingot"

    def test_item_equality(self):
        """Test Item equality based on name."""
        item1 = Item(name="Diamond", url="https://minecraft.wiki/w/Diamond")
        item2 = Item(name="Diamond", url="https://minecraft.wiki/w/Diamond")
        item3 = Item(name="Emerald", url="https://minecraft.wiki/w/Emerald")

        assert item1 == item2
        assert item1 != item3

    def test_item_hashing(self):
        """Test Item hashing for set deduplication."""
        item1 = Item(name="Gold Ingot", url="https://minecraft.wiki/w/Gold_Ingot")
        item2 = Item(name="Gold Ingot", url="https://minecraft.wiki/w/Gold_Ingot")
        item3 = Item(name="Gold Block", url="https://minecraft.wiki/w/Gold_Block")

        # Same name should produce same hash
        assert hash(item1) == hash(item2)

        # Items with same name should be considered equal in a set
        item_set = {item1, item2, item3}
        assert len(item_set) == 2  # Only 2 unique items

    def test_item_in_set(self):
        """Test Item deduplication in sets."""
        items = [
            Item(name="Stone", url="https://minecraft.wiki/w/Stone"),
            Item(name="Stone", url="https://minecraft.wiki/w/Stone"),
            Item(name="Cobblestone", url="https://minecraft.wiki/w/Cobblestone"),
        ]

        unique_items = set(items)
        assert len(unique_items) == 2


class TestTransformationType:
    """Tests for TransformationType enum."""

    def test_enum_values(self):
        """Test that all expected transformation types exist."""
        expected_types = [
            "crafting",
            "smelting",
            "blast_furnace",
            "smoker",
            "smithing",
            "stonecutter",
            "trading",
            "mob_drop",
            "brewing",
            "composting",
            "grindstone",
        ]

        for expected in expected_types:
            # Check that enum has this value
            found = False
            for member in TransformationType:
                if member.value == expected:
                    found = True
                    break
            assert found, f"Missing transformation type: {expected}"

    def test_enum_access(self):
        """Test accessing enum members."""
        assert TransformationType.CRAFTING.value == "crafting"
        assert TransformationType.SMELTING.value == "smelting"
        assert TransformationType.TRADING.value == "trading"


class TestTransformation:
    """Tests for Transformation data model."""

    def test_transformation_creation(self):
        """Test creating a Transformation with inputs and outputs."""
        iron = Item(name="Iron Ingot", url="https://minecraft.wiki/w/Iron_Ingot")
        iron_block = Item(name="Block of Iron", url="https://minecraft.wiki/w/Block_of_Iron")

        transformation = Transformation(
            transformation_type=TransformationType.CRAFTING,
            inputs=[iron] * 9,
            outputs=[iron_block],
        )

        assert transformation.transformation_type == TransformationType.CRAFTING
        assert len(transformation.inputs) == 1  # Deduplicated from 9 to 1
        assert len(transformation.outputs) == 1
        assert transformation.inputs[0] == iron
        assert transformation.outputs[0] == iron_block

    def test_transformation_with_metadata(self):
        """Test Transformation with metadata."""
        coal = Item(name="Coal", url="https://minecraft.wiki/w/Coal")
        emerald = Item(name="Emerald", url="https://minecraft.wiki/w/Emerald")

        transformation = Transformation(
            transformation_type=TransformationType.TRADING,
            inputs=[coal] * 15,
            outputs=[emerald],
            metadata={
                "villager_type": "Armorer",
                "level": "Novice",
            },
        )

        assert len(transformation.inputs) == 1  # Deduplicated from 15 to 1
        assert transformation.inputs[0] == coal
        assert transformation.metadata["villager_type"] == "Armorer"
        assert transformation.metadata["level"] == "Novice"

    def test_transformation_requires_inputs(self):
        """Test that Transformation requires at least one input."""
        iron_block = Item(name="Block of Iron", url="https://minecraft.wiki/w/Block_of_Iron")

        with pytest.raises(ValueError, match="at least one input"):
            Transformation(
                transformation_type=TransformationType.CRAFTING,
                inputs=[],
                outputs=[iron_block],
            )

    def test_transformation_requires_outputs(self):
        """Test that Transformation requires at least one output."""
        iron = Item(name="Iron Ingot", url="https://minecraft.wiki/w/Iron_Ingot")

        with pytest.raises(ValueError, match="at least one output"):
            Transformation(
                transformation_type=TransformationType.CRAFTING,
                inputs=[iron],
                outputs=[],
            )

    def test_transformation_default_metadata(self):
        """Test that Transformation has empty dict metadata by default."""
        iron = Item(name="Iron Ingot", url="https://minecraft.wiki/w/Iron_Ingot")
        gold = Item(name="Gold Ingot", url="https://minecraft.wiki/w/Gold_Ingot")

        transformation = Transformation(
            transformation_type=TransformationType.SMELTING,
            inputs=[iron],
            outputs=[gold],
        )

        assert transformation.metadata == {}
        assert isinstance(transformation.metadata, dict)

    def test_transformation_deduplicates_inputs(self):
        """Test that Transformation automatically deduplicates input items."""
        stick = Item(name="Stick", url="https://minecraft.wiki/w/Stick")
        wool = Item(name="Wool", url="https://minecraft.wiki/w/Wool")
        painting = Item(name="Painting", url="https://minecraft.wiki/w/Painting")

        # Create transformation with 8 sticks and 1 wool (painting recipe)
        transformation = Transformation(
            transformation_type=TransformationType.CRAFTING,
            inputs=[stick] * 8 + [wool],
            outputs=[painting],
        )

        # Should deduplicate to 2 unique items
        assert len(transformation.inputs) == 2
        assert stick in transformation.inputs
        assert wool in transformation.inputs

    def test_transformation_deduplicates_outputs(self):
        """Test that Transformation automatically deduplicates output items."""
        iron = Item(name="Iron Ingot", url="https://minecraft.wiki/w/Iron_Ingot")
        gold = Item(name="Gold Ingot", url="https://minecraft.wiki/w/Gold_Ingot")

        # Create transformation with duplicate outputs
        transformation = Transformation(
            transformation_type=TransformationType.CRAFTING,
            inputs=[iron],
            outputs=[gold, gold, gold],
        )

        # Should deduplicate to 1 unique output
        assert len(transformation.outputs) == 1
        assert transformation.outputs[0] == gold
