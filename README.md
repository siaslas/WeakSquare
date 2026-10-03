# WeakSquare

Turn mistakes from your own chess games into focused practice.

WeakSquare is a chess-training web app in active development. It analyzes uploaded PGN games with Stockfish, classifies moves, and lets players revisit their games on an interactive board. The goal is to turn those analyses into a prioritized queue of positions where the player must find a better move, then use review outcomes to identify and improve recurring weaknesses.

## The training loop

1. **Import a game:** upload a PGN and save it in a persistent game library.
2. **Understand the moves:** compare engine evaluations before and after each move and classify the loss in expected points.
3. **Practice the mistakes:** collect positions before mistakes and blunders, then ask the player to find a better alternative.
4. **Learn from repetition:** record review outcomes, adjust training priority, and track weaknesses over time.

Game ingestion and analysis are implemented. The practice queue, review feedback loop, theme tagging, and performance analytics are planned.

## Current capabilities

- PGN upload and parsing with stored game metadata, raw PGN, and player Elo headers when available.
- PostgreSQL-backed game library with analysis states and saved per-move classifications.
- Interactive React game viewer with legal move selection, drag-and-drop, move-list navigation, keyboard controls, and a resizable board.
- Stockfish evaluation before and after moves, normalized to the moving player's perspective, with expected-points-loss classifications.
- Detection of forced moves from the number of legal moves in a position.
- Live position analysis over server-sent events, displaying up to five candidate continuations as engine results arrive.

## Architecture

Solid arrows show the current application. Dashed arrows show the intended training and analytics flow; these components are not implemented yet. Planned components represent responsibilities, not a commitment to separate services.

```mermaid
flowchart TB
    Player["Chess player"]

    subgraph Frontend["Frontend · React / Vite / Tailwind CSS"]
        Library["PGN upload and game library"]
        Viewer["Interactive game review<br/>chess.js / react-chessboard"]
        Practice["Planned: training queue and review UI"]
        Dashboard["Planned: weakness analytics"]
    end

    subgraph Backend["Backend · FastAPI / Python"]
        API["HTTP API<br/>upload, games, classifications, evaluation"]
        Parser["PGN parsing and chess rules<br/>python-chess"]
        Classifier["Move analysis<br/>before/after evaluations → expected-points loss"]
        EngineAccess["UCI engine access<br/>shared Stockfish process and async lock"]
        Training["Planned: select and prioritize<br/>mistake / blunder positions"]
        Reviews["Planned: record practice outcomes<br/>and update priorities"]
        Analytics["Planned: themes, recurring weaknesses,<br/>and progress trends"]
    end

    Engine["Stockfish"]
    DB[("PostgreSQL<br/>Game and MoveAnalysis")]
    FutureDB[("Planned persistence<br/>tags, training positions, review outcomes")]

    Player --> Library
    Player --> Viewer
    Library -->|"PGN upload / game retrieval"| API
    API --> Parser
    Parser --> Classifier
    Classifier --> EngineAccess
    EngineAccess <-->|"UCI"| Engine
    API <-->|"SQLAlchemy"| DB
    Classifier -->|"Persist per-move analysis"| DB
    Viewer -->|"Fetch classifications / request FEN analysis"| API
    API -->|"Position evaluation"| EngineAccess
    API -->|"JSON / streamed candidate lines via SSE"| Viewer

    DB -.->|"Positions before mistakes and blunders"| Training
    Training -.-> Practice
    Player -.-> Practice
    Practice -.->|"Attempts and feedback"| Reviews
    Reviews -.-> Training
    Training -.-> FutureDB
    Reviews -.-> FutureDB
    FutureDB -.-> Analytics
    DB -.-> Analytics
    Analytics -.-> Dashboard
```

### How analysis works today

The frontend reads a PGN into `chess.js` and uploads it to FastAPI. The backend parses the first game with `python-chess`, stores its metadata, walks the main line, and asks Stockfish to evaluate positions before and after each non-forced move. Usable centipawn scores are converted to expected points; the difference determines the move classification. Results are stored against the game and move index, then returned to the frontend for board overlays.

For an individual board position, the frontend opens an `EventSource` connection using its FEN. FastAPI streams Stockfish candidate lines and scores back as server-sent events. The frontend closes the stream when the position changes or the component unmounts.

The backend currently shares one Stockfish process behind an asynchronous lock. PGN analysis runs inside the upload request; there is no background job queue or worker pool. Concurrent requests therefore compete for engine access. The planned **training queue** is a queue of practice positions for players, distinct from any future infrastructure queue for engine jobs.

### Data model

| Model | Stored information |
| --- | --- |
| `Game` | Raw PGN, unique PGN hash, player names and Elo ratings, game metadata, creation time, and analysis status |
| `MoveAnalysis` | Game ID, ply index, move in UCI notation, FEN before the move, expected points before/after, expected-points loss, and classification |

A uniqueness constraint on `(game_id, ply_index)` identifies one saved analysis per move. Training positions and review outcomes do not yet have database models.

## Tech stack

| Layer | Tools |
| --- | --- |
| Frontend | React, Vite, Tailwind CSS, React Router, Axios |
| Chess interaction | chess.js, react-chessboard |
| Backend | Python, FastAPI, Pydantic |
| Chess analysis | python-chess, Stockfish via UCI |
| Persistence | PostgreSQL, SQLAlchemy, Alembic |
| Streaming | Server-sent events and browser EventSource |

## Local development

### Prerequisites

- Node.js and npm compatible with Vite 7.
- Python and a virtual environment.
- A running PostgreSQL instance and an application database.
- Stockfish installed and available as `stockfish` on your `PATH`.

The backend does not yet include a dependency manifest or lockfile. The following installs its directly used runtime dependencies; versions are not pinned.

### Backend

From the repository root:

```bash
cd app/backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install fastapi 'uvicorn[standard]' sqlalchemy psycopg2-binary python-dotenv python-multipart python-chess alembic
```

Create `app/backend/.env` with your local database connection:

```dotenv
SQLALCHEMY_DATABASE_URL=postgresql+psycopg2://USER:PASSWORD@localhost:5432/weaksquare
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

**Database setup:** the first Alembic revision is an empty baseline for an existing schema; it does not create tables in a fresh database. For a fresh development database, create the current SQLAlchemy tables and stamp the matching migration head:

```bash
python -c 'from database import Base, db_engine; import models; Base.metadata.create_all(bind=db_engine)'
alembic stamp head
```

Use that bootstrap only for a new, empty database. For an existing database already managed by Alembic, inspect its revision with `alembic current` and apply pending migrations with `alembic upgrade head`. An existing unversioned database needs its schema checked before stamping a baseline.

Start FastAPI from `app/backend` so its module imports and local `.env` resolve correctly:

```bash
python -m uvicorn main:app --reload --port 8000
```

Interactive API documentation is available at <http://localhost:8000/docs>.

### Frontend

In another terminal, from the repository root:

```bash
cd app/frontend
npm ci
```

Set the API URL in `app/frontend/.env.development`:

```dotenv
VITE_API_URL=http://localhost:8000
```

```bash
npm run dev
```

Open the local URL printed by Vite, normally <http://localhost:5173>. Upload a PGN, wait for analysis, and select **Analyze** from the game library to review it. Example PGNs are in [`app/backend/assets`](app/backend/assets).

## Development priorities

- Strengthen the move-analysis contract, mate-score behavior, and forced-move handling across the full game traversal.
- Add rating-aware classification: Elo headers are stored, but ratings do not yet affect the expected-points calculation.
- Make duplicate uploads and reanalysis safe; PGN hash deduplication alone does not prevent duplicate move-analysis inserts.
- Return structured analyses keyed by ply index instead of associating classification strings by array position.
- Add focused analysis and persistence tests.
- Build mistake/theme tagging, the prioritized practice queue, review outcomes, and weakness analytics.

WeakSquare is currently a local development prototype without user authentication or per-user game ownership. Its classification model and thresholds are provisional, and do not reproduce Chess.com's proprietary classifications.

## Project docs

- [Move classification design notes](docs/notes.md): analysis contract, evaluation perspective, provisional categories, and training goals.
- [Move classification implementation plan](docs/move-classification-plan.md): incremental work, edge cases, and verification priorities. Some status notes predate the current code.
- [Page and feature notes](docs/todo.md): game review, library, training queue, and analytics pages.
- [Original six-week roadmap](docs/roadmap.pdf): the progression from foundations and ingestion to training and analytics.
