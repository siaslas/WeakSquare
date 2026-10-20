import unittest
from types import SimpleNamespace

from main import serialize_move_analysis


class MoveAnalysisSerializationTests(unittest.TestCase):
    def test_serializes_analysis_with_nested_evaluations(self):
        row = SimpleNamespace(
            ply_index=12,
            move_uci="g1f3",
            san="Nf3",
            fen_before="start-position-fen",
            moving_color="white",
            eval_before_kind="cp",
            eval_before_cp=42,
            eval_before_mate_in=None,
            eval_after_kind="mate",
            eval_after_cp=None,
            eval_after_mate_in=-3,
            expected_points_before=None,
            expected_points_after=None,
            expected_points_loss=None,
            classification=None,
            is_forced=False,
            analysis_status="skipped",
            skipped_reason="mate_score",
        )

        result = serialize_move_analysis(row)

        self.assertEqual(result["ply_index"], 12)
        self.assertEqual(result["eval_before"], {"kind": "cp", "cp": 42, "mate_in": None})
        self.assertEqual(result["eval_after"], {"kind": "mate", "cp": None, "mate_in": -3})
        self.assertEqual(result["analysis_status"], "skipped")
        self.assertEqual(result["skipped_reason"], "mate_score")


if __name__ == "__main__":
    unittest.main()
