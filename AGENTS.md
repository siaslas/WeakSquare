# WeakSquare Agent Instructions

## Collaboration style

- Do not provide complete solutions to LeetCode, NeetCode, or mathematical problems unless the user explicitly asks for the solution.
- The user has authorized the agent to implement project changes. Implement requested work directly, then present the resulting diff, rationale, and focused review points.
- Before making a substantial change, briefly explain the intended approach, important tradeoffs, and likely edge cases.
- Keep the user involved through concise explanations and review guidance, but do not wait for them to write implementation code unless they explicitly ask to take it on.
- Do not assume that a request for diagnosis authorizes implementation; explain the issue first unless a fix is explicitly requested.

## Project context

- The frontend is in `app/frontend` and uses React, Vite, Tailwind CSS, `chess.js`, and `react-chessboard`.
- The backend is in `app/backend` and uses FastAPI, SQLAlchemy, PostgreSQL, `python-chess`, and Stockfish.
- The project is a chess-training application focused on game analysis, move classification, training positions, and performance analytics.

## Working practices

- Preserve existing user changes and inspect `git status` before modifying overlapping files.
- Prefer focused, incremental changes over broad rewrites.
- Keep frontend and backend responsibilities clearly separated.
- When changing behavior, verify it with the narrowest useful check first, then run relevant lint, build, or tests.
- Document setup assumptions when a feature depends on PostgreSQL, Stockfish, environment variables, or a separate development server.
