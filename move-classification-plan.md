# Move Classification Plan

This document tracks the implementation plan for WeakSquare's move-classification pipeline. The goal is to build the feature incrementally while learning the design and implementation decisions along the way.

## Working agreement

- The learner writes most of the implementation.
- The tutor explains concepts, asks guiding questions, reviews code, and helps debug.
- Do not provide a complete implementation unless explicitly requested or necessary to unblock extended debugging.
- Work in focused increments and verify each increment with the narrowest useful tests.

## Current end-to-end path

```text
PGN file
  -> frontend reads PGN and loads chess.js game
  -> POST /uploadFile/
  -> backend parses PGN with python-chess
  -> each move is evaluated before and after with Stockfish
  -> scores are normalized to the moving player's perspective
  -> centipawns become expected points
  -> expected-points loss becomes a classification
  -> MoveAnalysis rows are stored in PostgreSQL
  -> classifications are returned to the frontend
  -> frontend associates them with moves and displays icons
```

## Relevant code

- `app/frontend/src/components/gamesPage.jsx`: reads the uploaded PGN and sends it to the backend.
- `app/frontend/src/App.jsx`: loads the PGN into chess.js and tracks the move and classification lists.
- `app/backend/main.py`: parses the PGN, analyzes each move, stores results, and serves classification data.
- `app/backend/move_classifier.py`: score normalization, expected-points conversion, and loss buckets.
- `app/backend/models.py`: `Game` and `MoveAnalysis` database models.
- `app/frontend/src/components/gamesList.jsx`: polls for stored analysis and loads completed games.
- `app/frontend/src/components/analysisPage.jsx`: maps classifications to icons and overlays them on the board.

## Known issues and assumptions

- Player ratings are not yet passed into the classifier or stored on `Game`.
- A single principal variation does not prove that a move is forced.
- Forced moves should be detected from the legal moves in the position.
- Mate scores are currently converted to a large centipawn value; they are not truly skipped.
- The frontend currently stores only a list of classification strings, matched by array position.
- Duplicate PGN handling can attempt to insert `MoveAnalysis` rows that already exist.
- The backend performs two engine calls per move, which may be slow for longer games.
- There are no focused tests for score perspective, expected-points boundaries, forced moves, or persistence.
- `Base.metadata.create_all()` does not provide schema migrations for future model changes.

## Ordered task list

### 1. Define the analysis contract

Document the input and output of one move classification. Include the board, move, moving color, rating, before/after evaluations, evaluation perspective, expected-points values, classification, and failure or skipped-analysis reasons.

Questions to settle:

- Does positive evaluation always mean favorable for the player who moved?
- What happens when evaluation is unavailable?
- Should classification return a named result object instead of a tuple?

Learning focus: designing a stable interface between engine code, domain logic, and persistence.

### 2. Build a normalized engine-evaluation result

Create an internal representation that distinguishes centipawn scores, mate scores, principal variation, depth, and score perspective. Stop silently treating every mate score as `10000`.

Learning focus: isolating third-party engine behavior behind a domain model.

### 3. Correctly identify forced moves

Detect a forced move with the number of legal moves in the position. Classify it before expected-points calculation. Test positions with exactly one legal move and positions where the engine returns only one PV despite multiple legal moves.

Learning focus: separating chess rules from engine output.

### 4. Add player ratings to the analysis pipeline

Extract supported rating headers from the PGN, decide how missing ratings behave, and store White and Black ratings on `Game`. Pass the moving player's rating to the classifier.

Learning focus: carrying metadata through parsing, business logic, persistence, and APIs.

### 5. Implement and test the rating-aware expected-points model

Update the expected-points interface to accept a rating. Decide whether rating changes the centipawn curve, classification thresholds, or both. Add table-driven tests for representative evaluations and ratings before tuning the model further.

Learning focus: translating a product idea into a testable mathematical model.

### 6. Replace the tuple-based classification result

Return a named result structure from `calculate_classification()`. Include classification, evaluations, expected points, loss, forced status, and skipped reasons. Update the upload flow to consume it.

Learning focus: using explicit domain objects instead of fragile positional values.

### 7. Make database persistence idempotent

Define behavior for duplicate uploads, failed analyses, partial analyses, and reanalysis with changed engine settings. Choose between returning existing results, rebuilding rows, upserting, or versioning analysis settings.

Learning focus: transactions, retries, state transitions, and uniqueness constraints.

### 8. Store the analysis data needed later

After deciding which future features require it, consider storing raw evaluations, moving color, player rating, engine settings, forced status, skipped reason, and SAN. Avoid adding columns without a clear use.

Learning focus: schema design driven by product requirements.

### 9. Return structured move analyses from the API

Change the classification endpoint to return move-analysis objects keyed by `ply_index`, rather than only strings. Update frontend state to associate analyses with moves by ply instead of relying only on array position.

Learning focus: designing a robust backend/frontend data contract.

### 10. Handle new classifications and skipped states in the UI

Support `forced`, skipped mate evaluations, missing classifications, analysis failures, and partial analysis. Decide which existing icon assets belong in the MVP and provide a safe fallback for unknown classifications.

Learning focus: building UI behavior around incomplete and evolving data.

### 11. Add an end-to-end test fixture

Create a small PGN containing a forced move, a normal best move, a move with evaluation loss, and optionally a mate-score position. Test the path from PGN parsing through classification, database rows, and API response. Use low engine limits or a replaceable engine test double.

Learning focus: testing a multi-layer feature without making every test slow or brittle.

## Recommended starting point

Begin with Tasks 1–3:

1. Define the result contract.
2. Normalize engine scores.
3. Detect forced moves correctly.

These address the most important correctness issues while keeping the first implementation increment small. Then proceed to ratings and persistence changes.
