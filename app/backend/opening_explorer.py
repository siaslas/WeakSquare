import os
from functools import lru_cache
from pathlib import Path

import chess.polyglot


BOOK_MAX_PLY = 20
DEFAULT_BOOK_PATH = Path(__file__).parent / "assets" / "opening-book.bin"


def _configured_book_path() -> Path:
    return Path(os.getenv("OPENING_BOOK_PATH", DEFAULT_BOOK_PATH))


@lru_cache(maxsize=1)
def _open_book(book_path: str) -> chess.polyglot.MemoryMappedReader | None:
    """Open the configured local book once, or disable book lookup if absent."""
    try:
        return chess.polyglot.open_reader(book_path)
    except (FileNotFoundError, OSError, ValueError):
        return None


def _book_moves(board) -> set:
    reader = _open_book(str(_configured_book_path()))
    if reader is None:
        return set()

    try:
        return {entry.move for entry in reader.find_all(board, minimum_weight=1)}
    except (IndexError, OSError, ValueError):
        # A malformed or unavailable book must not prevent engine analysis.
        return set()

def is_book_move(board, move, ply_index: int | None = None) -> bool:
    """Return whether a move appears in the configured local Polyglot book."""
    effective_ply = board.ply() if ply_index is None else ply_index
    if effective_ply >= BOOK_MAX_PLY:
        return False

    return move in _book_moves(board)
