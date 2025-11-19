"""Data models for Minecraft transformation extraction."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


class TransformationType(Enum):
    """Types of transformations in Minecraft."""
    BARTERING = "bartering"
    BLAST_FURNACE = "blast_furnace"
    BREWING = "brewing"
    COMPOSTING = "composting"
    CRAFTING = "crafting"
    GRINDSTONE = "grindstone"
    MOB_DROP = "mob_drop"
    SMELTING = "smelting"
    SMITHING = "smithing"
    SMOKER = "smoker"
    STONECUTTER = "stonecutter"
    TRADING = "trading"


@dataclass(frozen=True)
class Item:
    """Represents a Minecraft item with name and wiki URL."""
    name: str
    url: str

    def __hash__(self) -> int:
        """Hash based on name for set deduplication."""
        return hash(self.name)

    def __eq__(self, other: object) -> bool:
        """Equality based on name for set deduplication."""
        if not isinstance(other, Item):
            return False
        return self.name == other.name


@dataclass
class Transformation:
    """Represents a transformation from input items to output items."""
    transformation_type: TransformationType
    inputs: List[Item]
    outputs: List[Item]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate and deduplicate transformation data."""
        # Deduplicate inputs and outputs while maintaining list type
        self.inputs = list(set(self.inputs))
        self.outputs = list(set(self.outputs))

        if not self.inputs:
            raise ValueError("Transformation must have at least one input")
        if not self.outputs:
            raise ValueError("Transformation must have at least one output")
        if len(self.outputs) > 1:
            raise ValueError(
                f"Transformation must have exactly one output item, got {len(self.outputs)}: "
                f"{[item.name for item in self.outputs]}"
            )

    def get_signature(self) -> tuple:
        """
        Get a hashable signature for this transformation for deduplication.

        Returns:
            Tuple containing transformation type, sorted input names, sorted output names, and metadata
        """
        input_names = tuple(sorted(item.name for item in self.inputs))
        output_names = tuple(sorted(item.name for item in self.outputs))
        metadata_tuple = tuple(sorted(self.metadata.items()))
        return (self.transformation_type, input_names, output_names, metadata_tuple)
