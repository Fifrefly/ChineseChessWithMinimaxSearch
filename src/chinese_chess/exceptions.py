"""Project-specific exceptions for invalid positions and illegal moves."""

from __future__ import annotations


class ChineseChessError(Exception):
    """Base class for all package-specific exceptions."""


class InvalidFENError(ChineseChessError):
    """Raised when a FEN string cannot be parsed or validated."""


class IllegalMoveError(ChineseChessError):
    """Raised when a requested move is not legal in the current position."""


class BoardStateError(ChineseChessError):
    """Raised when board state dimensions or coordinates are invalid."""


# Backward-compatible spelling from the initial skeleton.
InvalidFenError = InvalidFENError
