"""High-level game facade used by tests, parity checks, and search code."""

from __future__ import annotations

from chinese_chess.board import Board
from chinese_chess.exceptions import IllegalMoveError
from chinese_chess.move import parse_iccs_move
from chinese_chess.movegen.legal import generate_legal_moves
from chinese_chess.movegen.pseudo_legal import generate_pseudo_legal_moves
from chinese_chess.rules.check import is_check
from chinese_chess.rules.repetition import is_threefold_repetition
from chinese_chess.rules.terminal import game_over, is_checkmate, is_stalemate
from chinese_chess.types import BoardState, Move


class Game:
    """Mutable Xiangqi game state.

    The facade exposes pseudo-legal and legal move generation. Terminal state
    detection is intentionally deferred to the next phase.
    """

    def __init__(self, fen: str | None = None) -> None:
        self._board = Board(fen)

    def load_fen(self, fen: str) -> None:
        """Replace the current game position from FEN."""
        self._board.load_fen(fen)

    def fen(self) -> str:
        """Return the current position as FEN."""
        return self._board.fen()

    def board(self) -> BoardState:
        """Return a 10x9 matrix view of the current board."""
        return self._board.to_matrix()

    @property
    def board_obj(self) -> Board:
        """Return the mutable board object for low-level experiments."""
        return self._board

    @property
    def turn(self) -> str:
        """Return the side to move using xiangqi.js color symbols."""
        return self._board.side_to_move

    def get_legal_moves(self) -> list[Move]:
        """Return legal moves after self-check filtering.

        TODO Phase 5: terminal detection will build on this method for
        checkmate and stalemate.
        """
        return generate_legal_moves(self._board, self.turn)

    def get_pseudo_legal_moves(self) -> list[Move]:
        """Return piece-rule-valid moves without self-check filtering."""
        return generate_pseudo_legal_moves(self._board, self.turn)

    def make_move(self, move: Move | str) -> Move:
        """Apply a legal move given as a ``Move`` or ICCS string."""
        requested = parse_iccs_move(move) if isinstance(move, str) else move
        for legal_move in self.get_legal_moves():
            if legal_move.from_pos == requested.from_pos and legal_move.to_pos == requested.to_pos:
                return self._board.make_move(legal_move)
        raise IllegalMoveError(f"Illegal move: {requested.to_iccs()}.")

    def undo_move(self) -> Move | None:
        """Undo the last move applied through the board."""
        return self._board.undo_move()

    def is_in_check(self, color: str | None = None) -> bool:
        """Return whether ``color`` is in check, defaulting to side to move."""
        return self.is_check(color)

    def is_check(self, color: str | None = None) -> bool:
        """Return whether ``color`` is in check, defaulting to side to move."""
        return is_check(self._board, self.turn if color is None else color)

    def is_checkmate(self, color: str | None = None) -> bool:
        """Return whether ``color`` is checkmated, defaulting to side to move."""
        return is_checkmate(self._board, self.turn if color is None else color)

    def is_stalemate(self, color: str | None = None) -> bool:
        """Return whether ``color`` is stalemated, defaulting to side to move."""
        return is_stalemate(self._board, self.turn if color is None else color)

    def is_threefold_repetition(self) -> bool:
        """Return whether the simplified xiangqi.js repetition rule triggers."""
        return is_threefold_repetition(self._board)

    def game_over(self) -> bool:
        """Return whether the current position is terminal for this phase."""
        return game_over(self._board, self.turn)
