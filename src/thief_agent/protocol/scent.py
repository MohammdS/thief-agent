"""Canonical wire representation for partial-observation scent heatmaps."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Annotated

from pydantic import Field

from thief_agent.config.models import StrictModel
from thief_agent.domain.types import Coord


class ScentCell(StrictModel):
    """Publish one global board cell intensity without an agent position field."""

    row: int = Field(ge=0)
    col: int = Field(ge=0)
    intensity: float = Field(ge=0, allow_inf_nan=False)


ScentHeatmap = Annotated[tuple[ScentCell, ...], Field(min_length=1)]


def encode_scent(values: Mapping[Coord, float]) -> tuple[ScentCell, ...]:
    """Return a stable row-major heatmap suitable for canonical JSON hashing."""
    return tuple(
        ScentCell(row=cell.row, col=cell.col, intensity=intensity)
        for cell, intensity in sorted(values.items())
    )


def decode_scent(values: tuple[ScentCell, ...]) -> dict[Coord, float]:
    """Convert a validated wire heatmap to the domain representation."""
    return {Coord(cell.row, cell.col): cell.intensity for cell in values}


def validate_heatmap(values: tuple[ScentCell, ...]) -> tuple[ScentCell, ...]:
    """Require unique row-major cells so equal maps have one canonical encoding."""
    coordinates = tuple((cell.row, cell.col) for cell in values)
    if coordinates != tuple(sorted(coordinates)):
        raise ValueError("scent heatmap cells must use row-major order")
    if len(coordinates) != len(set(coordinates)):
        raise ValueError("scent heatmap cells must be unique")
    return values
