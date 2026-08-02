"""Pure game rules shared by runtime validation and replay."""

from thief_agent.domain.board import apply_move, legal_moves, place_barrier
from thief_agent.domain.state import BoardState
from thief_agent.domain.types import Coord, Move, Role

__all__ = ["BoardState", "Coord", "Move", "Role", "apply_move", "legal_moves", "place_barrier"]

