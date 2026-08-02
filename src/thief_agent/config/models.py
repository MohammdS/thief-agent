"""Validated models for byte-identical game configuration."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    """Reject unspecified fields and prevent post-validation mutation."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class PointConfig(StrictModel):
    """Represent a configured zero-based board coordinate."""

    row: int = Field(ge=0)
    col: int = Field(ge=0)


class BoardConfig(StrictModel):
    """Define board geometry and the fixed action alphabet."""

    width: int = Field(ge=7)
    height: int = Field(ge=7)
    coordinate_origin: Literal["top-left-zero-based"]
    thief_start: PointConfig
    police_start: PointConfig
    legal_moves: tuple[Literal["N", "S", "E", "W", "STAY"], ...]

    @model_validator(mode="after")
    def validate_geometry(self) -> BoardConfig:
        """Require distinct in-bounds starts and every fixed move exactly once."""
        expected = {"N", "S", "E", "W", "STAY"}
        if set(self.legal_moves) != expected or len(self.legal_moves) != len(expected):
            raise ValueError("legal_moves must contain N, S, E, W, STAY exactly once")
        for point in (self.thief_start, self.police_start):
            if point.row >= self.height or point.col >= self.width:
                raise ValueError("start position must be inside the board")
        if self.thief_start == self.police_start:
            raise ValueError("agent start positions must be distinct")
        return self


class BarrierConfig(StrictModel):
    """Define the minimum Police barrier capacity."""

    police_capacity: int = Field(ge=14)


class TurnConfig(StrictModel):
    """Define the mandatory lower bounds for game length."""

    max_steps: int = Field(ge=35)
    survival_threshold: int = Field(ge=35)


class ScentConfig(StrictModel):
    """Lock the fixed scent parameters from Appendix F."""

    field_size: Literal[5]
    center: float
    decay: float

    @model_validator(mode="after")
    def validate_fixed_scent(self) -> ScentConfig:
        """Reject any change to center intensity or decay."""
        if self.center != 0.9 or self.decay != 0.1:
            raise ValueError("scent center and decay are fixed by Appendix F")
        return self


class ScorePair(StrictModel):
    """Store Police and Thief points for one terminal outcome."""

    police: int = Field(ge=0)
    thief: int = Field(ge=0)


class ScoringConfig(StrictModel):
    """Lock every fixed scoring pair."""

    capture: ScorePair
    survival: ScorePair
    tie: ScorePair
    technical_loss: ScorePair

    @model_validator(mode="after")
    def validate_fixed_scores(self) -> ScoringConfig:
        """Reject any score that differs from Appendix F."""
        actual = tuple((pair.police, pair.thief) for pair in (
            self.capture, self.survival, self.tie, self.technical_loss,
        ))
        if actual != ((20, 5), (5, 10), (2, 2), (0, 0)):
            raise ValueError("scoring values are fixed by Appendix F")
        return self


class SeriesConfig(StrictModel):
    """Define fixed series values and the negotiated token budget."""

    subgames: int = Field(ge=1)
    diversity_reward: Literal[10]
    token_budget: int = Field(gt=0)


class NetworkConfig(StrictModel):
    """Enforce minimum network and gatekeeper limits."""

    requests_per_minute: int = Field(ge=30)
    concurrency: int = Field(ge=2)
    retry_delay_seconds: float = Field(ge=5)
    retries: int = Field(ge=3)
    queue_depth: int = Field(ge=100)
    response_timeout_seconds: float = Field(gt=0)
    watchdog_seconds: float = Field(gt=0)


class SharedConfig(StrictModel):
    """Represent the complete peer-agreed shared configuration."""

    schema_version: Literal["1.0"]
    game_id: str = Field(min_length=1)
    counted: bool
    group_id: str = Field(min_length=1)
    board: BoardConfig
    barriers: BarrierConfig
    turns: TurnConfig
    scent: ScentConfig
    scoring: ScoringConfig
    series: SeriesConfig
    network: NetworkConfig

    @model_validator(mode="after")
    def validate_counted_series(self) -> SharedConfig:
        """Require exactly six subgames whenever a series is counted."""
        if self.counted and self.series.subgames != 6:
            raise ValueError("counted series must contain exactly six subgames")
        return self
