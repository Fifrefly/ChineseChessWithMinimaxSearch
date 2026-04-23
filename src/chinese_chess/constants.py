"""Constants mirrored from the xiangqi.js reference implementation.

The JavaScript reference uses a 10x9 board whose top row is black's home
rank and whose bottom row is red's home rank. Coordinates are written in
ICCS-style algebraic form such as ``a9`` through ``i0``.
"""

from __future__ import annotations

BOARD_ROWS = 10
BOARD_COLS = 9

MIN_ROW = 0
MAX_ROW = BOARD_ROWS - 1
MIN_COL = 0
MAX_COL = BOARD_COLS - 1

RED = "r"
BLACK = "b"
WHITE_ALIAS = "w"

COLORS = frozenset({RED, BLACK})
FEN_SIDE_TO_MOVE_SYMBOLS = frozenset({RED, BLACK, WHITE_ALIAS})

PAWN = "p"
CANNON = "c"
ROOK = "r"
KNIGHT = "n"
BISHOP = "b"
ADVISER = "a"
KING = "k"

PIECE_TYPES = frozenset({PAWN, CANNON, ROOK, KNIGHT, BISHOP, ADVISER, KING})
FEN_PIECE_SYMBOLS = frozenset("pcrnbakPCRNBAK")

DEFAULT_FEN = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR r - - 0 1"

ICCS_FILES = "abcdefghi"
ICCS_RANKS = "9876543210"

FEN_CASTLING_FIELD = "-"
FEN_EN_PASSANT_FIELD = "-"

NORMAL_MOVE_FLAG = "n"
CAPTURE_MOVE_FLAG = "c"

# Piece-count limits are validated by xiangqi.js before a position is loaded.
MAX_PIECE_COUNTS = {
    KING: 1,
    ADVISER: 2,
    BISHOP: 2,
    KNIGHT: 2,
    ROOK: 2,
    CANNON: 2,
    PAWN: 5,
}

