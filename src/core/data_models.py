"""Data models for Minecraft transformation extraction."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


class TransformationType(Enum):
    """Types of transformations in Minecraft."""
    CRAFTING = "crafting"
    SMELTING = "smelting"
    BLAST_FURNACE = "blast_furnace"
    SMOKER = "smoker"
    SMITHING = "smithing"
    STONECUTTER = "stonecutter"
    TRADING = "trading"
    MOB_DROP = "mob_drop"
    BREWING = "brewing"
    COMPOSTING = "composting"
    GRINDSTONE = "grindstone"


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
