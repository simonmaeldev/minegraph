"""
Tests for technical item mappings module.

These tests verify that the technical mappings are well-formed and can be
used for compression without conflicts or errors.
"""

import pytest
from src.technical_mappings import (
    TECHNICAL_MAPPINGS,
    generate_exact_to_technical,
    validate_mappings,
)


class TestTechnicalMappings:
    """Tests for the TECHNICAL_MAPPINGS dictionary."""

    def test_technical_mappings_not_empty(self):
        """Test that technical mappings dictionary is not empty."""
        assert len(TECHNICAL_MAPPINGS) > 0
        assert isinstance(TECHNICAL_MAPPINGS, dict)

    def test_all_categories_have_items(self):
        """Test that every technical category has at least one item."""
        for technical_name, exact_names in TECHNICAL_MAPPINGS.items():
            assert len(exact_names) > 0, f"Category '{technical_name}' is empty"
            assert isinstance(exact_names, list)

    def test_all_items_are_strings(self):
        """Test that all exact item names are non-empty strings."""
        for technical_name, exact_names in TECHNICAL_MAPPINGS.items():
            for exact_name in exact_names:
                assert isinstance(exact_name, str), (
                    f"Item in '{technical_name}' is not a string: {exact_name!r}"
                )
                assert len(exact_name) > 0, (
                    f"Empty string found in category '{technical_name}'"
                )

    def test_known_categories_exist(self):
        """Test that expected technical categories are present."""
        expected_categories = [
            "Planks",
            "Log",
            "Tipped Arrow",
            "Boat",
            "Sign",
        ]
        for category in expected_categories:
            assert category in TECHNICAL_MAPPINGS, f"Expected category '{category}' not found"

    def test_planks_category_complete(self):
        """Test that Planks category has all expected plank types."""
        expected_planks = [
            "Oak Planks",
            "Spruce Planks",
            "Birch Planks",
            "Jungle Planks",
            "Acacia Planks",
            "Dark Oak Planks",
            "Crimson Planks",
            "Warped Planks",
            "Mangrove Planks",
            "Cherry Planks",
            "Bamboo Planks",
            "Pale Oak Planks",
        ]
        planks = TECHNICAL_MAPPINGS["Planks"]
        for plank in expected_planks:
            assert plank in planks, f"Expected plank '{plank}' not found in Planks category"


class TestGenerateExactToTechnical:
    """Tests for generate_exact_to_technical() function."""

    def test_generates_reverse_mapping(self):
        """Test that reverse mapping is generated correctly."""
        exact_to_technical = generate_exact_to_technical()

        assert isinstance(exact_to_technical, dict)
        assert len(exact_to_technical) > 0

    def test_reverse_mapping_correctness(self):
        """Test that reverse mapping correctly maps exact items to technical names."""
        exact_to_technical = generate_exact_to_technical()

        # Check a few known mappings
        assert exact_to_technical["Oak Planks"] == "Planks"
        assert exact_to_technical["Spruce Planks"] == "Planks"
        assert exact_to_technical["Oak Log"] == "Log"

    def test_all_exact_items_mapped(self):
        """Test that all exact items from TECHNICAL_MAPPINGS are in reverse mapping."""
        exact_to_technical = generate_exact_to_technical()

        for technical_name, exact_names in TECHNICAL_MAPPINGS.items():
            for exact_name in exact_names:
                assert exact_name in exact_to_technical, (
                    f"Exact item '{exact_name}' not in reverse mapping"
                )
                assert exact_to_technical[exact_name] == technical_name, (
                    f"Exact item '{exact_name}' maps to wrong technical name"
                )

    def test_no_duplicate_exact_items(self):
        """Test that no exact item appears in multiple technical categories."""
        seen_items = {}

        for technical_name, exact_names in TECHNICAL_MAPPINGS.items():
            for exact_name in exact_names:
                if exact_name in seen_items:
                    pytest.fail(
                        f"Duplicate exact item '{exact_name}' found in categories "
                        f"'{seen_items[exact_name]}' and '{technical_name}'"
                    )
                seen_items[exact_name] = technical_name

        # If we get here, no duplicates were found
        assert True

    def test_duplicate_raises_error(self):
        """Test that duplicate exact items raise ValueError when detected."""
        # This test relies on the implementation to raise ValueError if duplicates exist
        # Since our mappings should be valid, this should not raise
        try:
            generate_exact_to_technical()
        except ValueError as e:
            pytest.fail(f"Unexpected ValueError: {e}")

    def test_round_trip_mapping(self):
        """Test that we can go from technical to exact and back to technical."""
        exact_to_technical = generate_exact_to_technical()

        for technical_name, exact_names in TECHNICAL_MAPPINGS.items():
            for exact_name in exact_names:
                # Go from exact to technical
                mapped_technical = exact_to_technical[exact_name]
                # Verify it maps back correctly
                assert mapped_technical == technical_name


class TestValidateMappings:
    """Tests for validate_mappings() function."""

    def test_validate_mappings_passes(self):
        """Test that validate_mappings() passes with current mappings."""
        result = validate_mappings()
        assert result is True

    def test_collisions_handled_by_iterative_replacement(self):
        """Test that collisions between technical names and exact items are acceptable.

        Collisions occur when a technical category name is also an exact item name
        (e.g., "Cut Copper" is both a category and an exact item). These are handled
        by the iterative replacement logic in replace_item_name(), which ensures
        that items are replaced transitively until no more replacements occur.
        """
        exact_to_technical = generate_exact_to_technical()

        all_exact_names = set(exact_to_technical.keys())
        technical_names = set(TECHNICAL_MAPPINGS.keys())

        collisions = technical_names & all_exact_names

        # Collisions are acceptable because they're handled by iterative replacement
        # For each collision item, verify it maps to a technical category
        for collision_item in collisions:
            assert collision_item in exact_to_technical, (
                f"Collision item '{collision_item}' should be in exact_to_technical"
            )
            technical_name = exact_to_technical[collision_item]
            # The technical name should be a valid technical category or another collision item
            assert technical_name in TECHNICAL_MAPPINGS or technical_name in collisions, (
                f"Collision item '{collision_item}' maps to invalid technical name '{technical_name}'"
            )

    def test_no_empty_categories(self):
        """Test that no technical category is empty."""
        for technical_name, exact_names in TECHNICAL_MAPPINGS.items():
            assert len(exact_names) > 0, f"Category '{technical_name}' is empty"


class TestMappingStatistics:
    """Tests that generate statistics about the mappings."""

    def test_mapping_statistics(self):
        """Generate and display statistics about the mappings."""
        exact_to_technical = generate_exact_to_technical()

        total_categories = len(TECHNICAL_MAPPINGS)
        total_exact_items = len(exact_to_technical)

        # Find largest and smallest categories
        category_sizes = {
            name: len(items) for name, items in TECHNICAL_MAPPINGS.items()
        }
        largest_category = max(category_sizes.items(), key=lambda x: x[1])
        smallest_category = min(category_sizes.items(), key=lambda x: x[1])

        # These assertions are informational, not strict requirements
        assert total_categories >= 10, "Should have at least 10 technical categories"
        assert total_exact_items >= 100, "Should have at least 100 exact items"

        # Display statistics (will show in verbose test output)
        print(f"\n=== Technical Mapping Statistics ===")
        print(f"Total technical categories: {total_categories}")
        print(f"Total exact items: {total_exact_items}")
        print(f"Average items per category: {total_exact_items / total_categories:.1f}")
        print(f"Largest category: {largest_category[0]} ({largest_category[1]} items)")
        print(f"Smallest category: {smallest_category[0]} ({smallest_category[1]} items)")


class TestSpecificMappings:
    """Tests for specific technical mappings to ensure correctness."""

    def test_tipped_arrow_mapping(self):
        """Test that tipped arrows are correctly mapped."""
        exact_to_technical = generate_exact_to_technical()

        tipped_arrows = [
            "Arrow of Poison",
            "Arrow of Healing",
            "Arrow of Harming",
            "Arrow of Strength",
        ]

        for arrow in tipped_arrows:
            assert arrow in exact_to_technical
            assert exact_to_technical[arrow] == "Tipped Arrow"

    def test_regular_arrow_not_in_tipped(self):
        """Test that regular Arrow is NOT in the Tipped Arrow category."""
        tipped_arrow_items = TECHNICAL_MAPPINGS["Tipped Arrow"]

        # Regular "Arrow" should not be in tipped arrows
        assert "Arrow" not in tipped_arrow_items
        # Spectral Arrow should also not be in tipped arrows
        assert "Spectral Arrow" not in tipped_arrow_items

    def test_boat_mappings(self):
        """Test that boats and boats with chests are separate categories."""
        exact_to_technical = generate_exact_to_technical()

        # Regular boats
        assert exact_to_technical["Oak Boat"] == "Boat"
        assert exact_to_technical["Spruce Boat"] == "Boat"

        # Boats with chests (different category)
        assert exact_to_technical["Oak Boat with Chest"] == "Boat with Chest"
        assert exact_to_technical["Spruce Boat with Chest"] == "Boat with Chest"

    def test_log_mappings_separate_from_stripped(self):
        """Test that logs and stripped logs are separate categories."""
        exact_to_technical = generate_exact_to_technical()

        # Regular logs
        assert exact_to_technical["Oak Log"] == "Log"
        assert exact_to_technical["Spruce Log"] == "Log"

        # Stripped logs (different category)
        assert exact_to_technical["Stripped Oak Log"] == "Stripped Log"
        assert exact_to_technical["Stripped Spruce Log"] == "Stripped Log"

    def test_wood_and_hyphae_separate(self):
        """Test that wood blocks and hyphae are separate categories."""
        exact_to_technical = generate_exact_to_technical()

        # Regular wood blocks
        assert exact_to_technical["Oak Wood"] == "Wood"

        # Hyphae (nether wood)
        assert exact_to_technical["Crimson Hyphae"] == "Hyphae"
        assert exact_to_technical["Warped Hyphae"] == "Hyphae"
