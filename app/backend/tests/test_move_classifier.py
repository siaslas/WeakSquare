import unittest

from move_classifier import (
    EngineEvaluation,
    MoveClassificationResult,
    classify_expected_points_loss,
    expected_points_from_cp,
)


class ExpectedPointsFromCpTests(unittest.TestCase):
    def test_missing_rating_uses_baseline_rating(self):
        self.assertEqual(
            expected_points_from_cp(150, None),
            expected_points_from_cp(150, 1500),
        )

    def test_equal_position_is_neutral_at_every_rating(self):
        for rating in (None, 800, 1500, 2400):
            self.assertEqual(expected_points_from_cp(0, rating), 0.5)

    def test_expected_points_increase_with_centipawn_evaluation(self):
        for rating in (800, 1500, 2400):
            self.assertLess(
                expected_points_from_cp(-100, rating),
                expected_points_from_cp(100, rating),
            )

    def test_higher_rating_is_more_sensitive_to_a_positive_evaluation(self):
        self.assertGreater(
            expected_points_from_cp(100, 2400),
            expected_points_from_cp(100, 800),
        )

    def test_same_evaluation_drop_costs_more_at_higher_rating(self):
        low_rating_loss = (
            expected_points_from_cp(100, 800)
            - expected_points_from_cp(-100, 800)
        )
        high_rating_loss = (
            expected_points_from_cp(100, 2400)
            - expected_points_from_cp(-100, 2400)
        )

        self.assertGreater(high_rating_loss, low_rating_loss)


class MoveClassificationResultTests(unittest.TestCase):
    def test_forced_result_keeps_non_applicable_fields_explicit(self):
        result = MoveClassificationResult(
            classification="forced",
            eval_before=None,
            eval_after=None,
            expected_points_before=None,
            expected_points_after=None,
            expected_points_loss=None,
            is_forced=True,
            analysis_status="forced",
        )

        self.assertEqual(result.classification, "forced")
        self.assertTrue(result.is_forced)
        self.assertIsNone(result.expected_points_loss)

    def test_skipped_result_preserves_mate_evaluation(self):
        result = MoveClassificationResult(
            classification=None,
            eval_before=EngineEvaluation(kind="mate", mate_in=3),
            eval_after=EngineEvaluation(kind="cp", cp=50),
            expected_points_before=None,
            expected_points_after=None,
            expected_points_loss=None,
            is_forced=False,
            analysis_status="skipped",
            skipped_reason="mate_score",
        )

        self.assertEqual(result.eval_before.mate_in, 3)
        self.assertEqual(result.skipped_reason, "mate_score")


class ClassificationThresholdTests(unittest.TestCase):
    def test_good_inaccuracy_boundary(self):
        self.assertEqual(classify_expected_points_loss(0.05), "good")
        self.assertEqual(classify_expected_points_loss(0.050001), "inaccuracy")

    def test_expected_points_loss_buckets(self):
        cases = (
            (0.00, "best"),
            (0.02, "excellent"),
            (0.03, "good"),
            (0.10, "inaccuracy"),
            (0.20, "mistake"),
            (0.200001, "blunder"),
        )

        for loss, expected_classification in cases:
            with self.subTest(loss=loss):
                self.assertEqual(
                    classify_expected_points_loss(loss),
                    expected_classification,
                )


if __name__ == "__main__":
    unittest.main()
