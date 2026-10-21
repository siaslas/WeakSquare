import unittest

import chess

import opening_explorer


class BookMoveTests(unittest.TestCase):
    def setUp(self):
        self.original_open_book = opening_explorer._open_book

    def tearDown(self):
        opening_explorer._open_book = self.original_open_book

    @staticmethod
    def use_book_moves(moves):
        class Entry:
            def __init__(self, move):
                self.move = move

        class Reader:
            def find_all(self, board, minimum_weight):
                return (Entry(move) for move in moves)

        opening_explorer._open_book = lambda _: Reader()

    def test_recorded_early_move_is_book(self):
        board = chess.Board()
        move = chess.Move.from_uci("e2e4")
        self.use_book_moves({move})

        self.assertTrue(opening_explorer.is_book_move(board, move, ply_index=0))

    def test_unrecorded_move_is_not_book(self):
        board = chess.Board()
        move = chess.Move.from_uci("e2e4")
        self.use_book_moves({chess.Move.from_uci("d2d4")})

        self.assertFalse(opening_explorer.is_book_move(board, move, ply_index=0))

    def test_moves_after_opening_window_are_not_book(self):
        board = chess.Board()
        move = chess.Move.from_uci("e2e4")
        self.use_book_moves({move})

        self.assertFalse(opening_explorer.is_book_move(board, move, ply_index=20))

    def test_missing_book_safely_has_no_book_moves(self):
        self.original_open_book.cache_clear()
        missing_path = "/tmp/weaksquare-missing-opening-book.bin"
        self.assertIsNone(self.original_open_book(missing_path))
