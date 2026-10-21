import asyncio
import unittest

import chess
import chess.engine

import main


class FakeEngine:
    def __init__(self, scores):
        self._scores = iter(scores)
        self.calls = 0

    async def analyse(self, board, limit):
        self.calls += 1
        score = next(self._scores)
        return {} if score is None else {"score": score}


def white_cp(value):
    return chess.engine.PovScore(chess.engine.Cp(value), chess.WHITE)


def white_mate(value):
    return chess.engine.PovScore(chess.engine.Mate(value), chess.WHITE)


class CalculateClassificationTests(unittest.TestCase):
    def setUp(self):
        self.original_engine = main.engine
        self.original_is_book_move = main.is_book_move

        def no_book_move(*args, **kwargs):
            return False

        main.is_book_move = no_book_move

    def tearDown(self):
        main.engine = self.original_engine
        main.is_book_move = self.original_is_book_move

    def classify_white_move(self, scores):
        fake_engine = FakeEngine(scores)
        main.engine = fake_engine
        board = chess.Board()
        result = asyncio.run(
            main.calculate_classification(
                board,
                chess.Move.from_uci("e2e4"),
                chess.WHITE,
                1500,
            )
        )
        return result, fake_engine

    def test_expected_points_buckets(self):
        cases = (
            (100, 100, "best"),
            (100, 85, "excellent"),
            (100, 20, "good"),
            (100, -20, "inaccuracy"),
            (200, -100, "mistake"),
            (300, -200, "blunder"),
        )

        for before_cp, after_cp, expected_classification in cases:
            with self.subTest(expected_classification=expected_classification):
                result, fake_engine = self.classify_white_move(
                    [white_cp(before_cp), white_cp(after_cp)]
                )

                self.assertEqual(result.classification, expected_classification)
                self.assertEqual(result.analysis_status, "evaluated")
                self.assertEqual(result.eval_before.cp, before_cp)
                self.assertEqual(result.eval_after.cp, after_cp)
                self.assertEqual(fake_engine.calls, 2)

    def test_normalizes_scores_to_the_black_mover(self):
        fake_engine = FakeEngine([white_cp(-100), white_cp(-20)])
        main.engine = fake_engine
        board = chess.Board()
        board.push_uci("e2e4")

        result = asyncio.run(
            main.calculate_classification(
                board,
                chess.Move.from_uci("e7e5"),
                chess.BLACK,
                1500,
            )
        )

        self.assertEqual(result.eval_before.cp, 100)
        self.assertEqual(result.eval_after.cp, 20)
        self.assertEqual(result.classification, "good")

    def test_classification_does_not_advance_the_game_board(self):
        fake_engine = FakeEngine([white_cp(50), white_cp(40)])
        main.engine = fake_engine
        board = chess.Board()
        move = chess.Move.from_uci("e2e4")

        asyncio.run(main.calculate_classification(board, move, chess.WHITE, 1500))

        self.assertEqual(board.fen(), chess.STARTING_FEN)
        board.push(move)
        self.assertEqual(board.turn, chess.BLACK)
        self.assertEqual(board.piece_at(chess.E4).symbol(), "P")

    def test_forced_move_skips_engine_analysis(self):
        fake_engine = FakeEngine([])
        main.engine = fake_engine
        board = chess.Board("k7/8/2K5/8/8/8/8/1R6 b - - 0 1")

        result = asyncio.run(
            main.calculate_classification(
                board,
                chess.Move.from_uci("a8a7"),
                chess.BLACK,
                1500,
            )
        )

        self.assertEqual(result.classification, "forced")
        self.assertTrue(result.is_forced)
        self.assertEqual(result.analysis_status, "forced")
        self.assertEqual(fake_engine.calls, 0)

    def test_book_move_skips_engine_analysis(self):
        def book_move(*args, **kwargs):
            return True

        main.is_book_move = book_move
        fake_engine = FakeEngine([])
        main.engine = fake_engine
        board = chess.Board()

        result = asyncio.run(
            main.calculate_classification(
                board,
                chess.Move.from_uci("e2e4"),
                chess.WHITE,
                1500,
            )
        )

        self.assertEqual(result.classification, "book")
        self.assertEqual(result.analysis_status, "book")
        self.assertFalse(result.is_forced)
        self.assertEqual(fake_engine.calls, 0)

    def test_mate_score_is_skipped_without_expected_points(self):
        result, _ = self.classify_white_move([white_cp(50), white_mate(-2)])

        self.assertIsNone(result.classification)
        self.assertEqual(result.analysis_status, "skipped")
        self.assertEqual(result.skipped_reason, "mate_score")
        self.assertEqual(result.eval_after.mate_in, -2)
        self.assertIsNone(result.expected_points_loss)

    def test_unavailable_score_is_skipped(self):
        result, _ = self.classify_white_move([None, None])

        self.assertIsNone(result.classification)
        self.assertEqual(result.analysis_status, "skipped")
        self.assertEqual(result.skipped_reason, "engine_score_unavailable")
        self.assertEqual(result.eval_before.kind, "unavailable")
