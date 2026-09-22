"""Contract sources. Add one by subclassing ContractSource - nothing else changes."""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

from contratos_core import Settings


@dataclass(slots=True)
class ContractRecord:
    """One contract, flattened into the rows four tables need."""
    contract: dict[str, Any]
    suppliers: list[tuple[int, str | None, str]] = field(default_factory=list)
    bidders: list[tuple[int, str | None, str]] = field(default_factory=list)
    locations: list[tuple[int, str, str, str]] = field(default_factory=list)


class ContractSource(ABC):
    """A stream of ContractRecords from somewhere."""

    name: str = "source"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def in_scope(self, buyer_nif: str | None) -> bool:
        """MUNICIPALITY_NIFS empty means national."""
        scope = self.settings.scope_nifs
        return not scope or buyer_nif in scope

    @abstractmethod
    def records(self) -> Iterator[ContractRecord]:
        ...
