# Move Classification Design Notes

## Goal

Given a position and the move played by a player, determine how good the move was and whether the position should be considered for training.

The first version will classify moves using engine evaluations and expected-points loss. Later versions can incorporate additional signals such as time spent on the move and recurring mistake patterns.

## Core model

The classifier compares the position before the player's move with the position after the player's move.

```text
eval_before = engine evaluation of the current position
eval_after = engine evaluation after the player's move

expected_points_before = f(eval_before, player_rating)
expected_points_after = f(eval_after, player_rating)

expected_points_loss = expected_points_before - expected_points_after
classification = bucket(expected_points_loss)
```

The player's rating must be considered because the same move may be judged differently for players at different skill levels. In particular, the expectations for great or brilliant moves should be rating-sensitive. The initial MVP can use a simpler rating-aware model and be refined after testing against real games.

## Evaluation perspective

All evaluations should be normalized to the moving player's perspective:

> A positive evaluation means the position is favorable for the player who made the move.

Stockfish commonly reports scores relative to White. Therefore:

- For a White move, use the White-relative score directly.
- For a Black move, negate the White-relative score.
- After the move, the side to move has changed, so normalize the resulting score to the original moving player before calculating expected points.

This convention should be applied consistently before any expected-points calculation.

## Task 1: Move classification contract

### Inputs

```text
board_before: chess.Board
move: chess.Move
moving_color: White or Black
player_rating: integer or null
```

### Processing rules

1. If the position has exactly one legal move, classify the move as `forced`.
2. Evaluate the position before the move.
3. Push the player's move onto a copy of the board.
4. Evaluate the resulting position.
5. Normalize both evaluations to the moving player's perspective.
6. If both evaluations are usable centipawn scores, convert them to expected points.
7. Calculate expected-points loss.
8. Convert the loss into a classification bucket.

### Output

```text
classification
eval_before
eval_after
expected_points_before
expected_points_after
expected_points_loss
is_forced
mate_before
mate_after
analysis_status
```

The output should be represented as a named result object rather than a positional tuple. Expected-points fields may be `null` when the move is forced or when mate scores are not yet supported by the expected-points model.

Possible `analysis_status` values:

```text
evaluated
forced
skipped
```

The board and move are inputs to the classifier. When the result is persisted, the database record should additionally identify the analyzed move with:

```text
game_id
ply_index
fen_before
move_uci
```

## Classification buckets

The initial MVP can use these categories:

```text
best
excellent
good
inaccuracy
mistake
blunder
forced
```

The following categories are intentionally deferred because they require more context than expected-points loss alone:

```text
great
brilliant
book
```

Current preliminary loss thresholds:

```text
loss <= 0.00  -> best
loss <= 0.03  -> excellent
loss <= 0.08  -> good
loss <= 0.15  -> inaccuracy
loss <= 0.30  -> mistake
loss >  0.30  -> blunder
```

These thresholds are provisional and should be validated against analyzed games before being treated as final.

## Engine scores and mate scores

Engine evaluations should preserve whether the result is:

- A centipawn score
- A mating score

Do not immediately convert mate scores into an ordinary large centipawn value such as `10000`. A mate score contains different information from a centipawn score.

The classifier can later represent mate information with separate fields such as:

```text
mate_before
mate_after
```

The classification field should remain a move-quality category. Do not encode engine outcomes as strings such as `#mate(3)` inside the classification field. Mate information and move classification are related, but they are separate concepts.

For the initial MVP, unsupported mate evaluations may produce:

```text
analysis_status = skipped
expected_points_before = null
expected_points_after = null
expected_points_loss = null
```

This can be replaced later with explicit mate-aware classification rules.

## Forced moves

A move is forced when the position has exactly one legal move:

```text
len(list(board_before.legal_moves)) == 1
```

The number of principal variations returned by Stockfish must not be used to detect forced moves. A single PV can be returned because of engine configuration or an interrupted search even when several legal moves exist.

For a forced move:

```text
classification = forced
is_forced = true
analysis_status = forced
```

Expected-points calculation is not required for this case.

## Training priority

The first training rule can be simple:

```text
if classification is mistake or blunder:
    add the position before the move to the training queue
```

Later, training priority can incorporate:

- Time spent before the move
- Whether the player had enough time to find a better move
- How often the same type of mistake occurs
- Whether the player continues repeating the mistake

The goal is for the training queue to evolve as the player's weaknesses change.

## Open decisions

- Exact rating-aware expected-points formula
- Behavior when a PGN has no player rating
- Mate-aware classification rules
- Whether skipped analysis should be retried or excluded
- Engine depth/time settings for production analysis
- How analysis versions should be tracked when engine settings change
