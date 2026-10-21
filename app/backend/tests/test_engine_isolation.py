import asyncio
import unittest

import chess
import chess.engine

import main


class RejectingEngine:
    async def analyse(self, *args, **kwargs):
        raise AssertionError("The classification engine must not serve interactive analysis")


class InteractiveEngine:
    def __init__(self):
        self.calls = 0

    async def analyse(self, *args, **kwargs):
        self.calls += 1
        return [{"score": chess.engine.PovScore(chess.engine.Cp(25), chess.WHITE), "pv": []}]


class EngineIsolationTests(unittest.TestCase):
    def setUp(self):
        self.original_engine = main.engine
        self.original_interactive_engine = main.interactive_engine

    def tearDown(self):
        main.engine = self.original_engine
        main.interactive_engine = self.original_interactive_engine

    def test_evaluate_uses_the_interactive_engine(self):
        interactive = InteractiveEngine()
        main.engine = RejectingEngine()
        main.interactive_engine = interactive

        result = asyncio.run(main.evaluate(main.EvaluateRequest(fen=chess.STARTING_FEN)))

        self.assertEqual(interactive.calls, 1)
        self.assertEqual(result["pv_lines"][0]["score"], 25)
