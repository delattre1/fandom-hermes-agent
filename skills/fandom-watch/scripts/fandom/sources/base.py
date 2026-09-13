"""Source contract shared by every fandom reader."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SourceError(RuntimeError):
    """One provider's failure. A digest survives any of these."""

    source: str
    reason: str

    def __str__(self) -> str:
        return f"{self.source}: {self.reason}"