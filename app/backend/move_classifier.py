import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
  import chess

BASELINE_RATING = 1500
BASELINE_SCALE = 400
RATING_SCALE_SLOPE = 0.1
MINIMUM_SCALE = 250
MAXIMUM_SCALE = 600


@dataclass(frozen=True)
class EngineEvaluation:
  kind: str
  cp: int | None = None
  mate_in: int | None = None


@dataclass(frozen=True)
class MoveClassificationResult:
  classification: str | None
  eval_before: EngineEvaluation | None
  eval_after: EngineEvaluation | None
  expected_points_before: float | None
  expected_points_after: float | None
  expected_points_loss: float | None
  is_forced: bool
  analysis_status: str
  skipped_reason: str | None = None


def score_for_player(white_score: int, color: "chess.Color") -> int:
  return white_score if color else -white_score


def expected_points_from_cp(cp: int, rating: int | None = None) -> float:
  """Convert a player-relative centipawn score into expected points.

  Higher-rated players use a steeper curve because smaller evaluation swings
  should matter more to their move classification. Missing ratings use the
  baseline behavior.
  """
  effective_rating = BASELINE_RATING if rating is None else rating
  scale = BASELINE_SCALE - (effective_rating - BASELINE_RATING) * RATING_SCALE_SLOPE
  clamped_scale = max(MINIMUM_SCALE, min(MAXIMUM_SCALE, scale))
  clamped_cp = max(-1000, min(1000, cp))
  return 1 / (1 + math.exp(-clamped_cp / clamped_scale))


def classify_expected_points_loss(loss: float) -> str:
  if loss <= 0:
    return "best"
  if loss <= 0.03:
    return "excellent"
  if loss <= 0.08:
    return "good"
  if loss <= 0.15:
    return "inaccuracy"
  if loss <= 0.3:
    return "mistake"
  return "blunder"
