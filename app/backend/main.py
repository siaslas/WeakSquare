import os
import io
import asyncio
import chess
import chess.engine
import chess.pgn
import hashlib
import logging
import json
from collections.abc import AsyncIterator
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from database import db_engine, get_db
from models import Game, MoveAnalysis
from move_classifier import classify_expected_points_loss, expected_points_from_cp, score_for_player

engine: chess.engine.UciProtocol | None = None
engine_lock = asyncio.Lock()
logger = logging.getLogger(__name__)

class EvaluateRequest(BaseModel):
    fen: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    global engine
    transport, engine = await chess.engine.popen_uci("stockfish")
    yield
    await engine.quit()

app = FastAPI(lifespan=lifespan)

# Allow local frontend origins by default, while still supporting override via CORS_ORIGINS.
origins_env = os.getenv("CORS_ORIGINS", "")
origins = [origin.strip() for origin in origins_env.split(",") if origin.strip()]
if not origins:
    origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/gamesList")
async def get_games_list(db: Session = Depends(get_db)):
    games = db.query(Game.id,
                     Game.white_player,
                     Game.black_player,
                     Game.event,
                     Game.date,
                     Game.result,
                     Game.raw_pgn).order_by(Game.created_at.desc()).all()
    
    return [
        {
            "id": game.id,
            "white_player": game.white_player,
            "black_player": game.black_player,
            'event': game.event,
            "date": game.date,
            "result": game.result,
            "pgn": game.raw_pgn,
        }

        for game in games
    ]

@app.post("/uploadFile/")
async def upload_file(file: UploadFile, db: Session = Depends(get_db)):
    active_engine = engine
    if active_engine is None:
        return {"error": "Engine not initialized"}

    contents = await file.read()
    pgn_hash = hashlib.sha256(contents).hexdigest()
    raw_pgn = contents.decode("utf-8")
    pgn = io.StringIO(raw_pgn)
    game = chess.pgn.read_game(pgn)

    if game is None:
        return {"error": "Invalid or empty PGN file"}
    
    white_elo, black_elo = get_elo(game, chess.WHITE), get_elo(game, chess.BLACK)

    db_game = Game(
        pgn_hash=pgn_hash,
        raw_pgn=raw_pgn,
        white_player=game.headers.get("White"),
        black_player=game.headers.get("Black"),
        white_elo=white_elo,
        black_elo=black_elo,
        event=game.headers.get("Event"),
        site=game.headers.get("Site"),
        round_tag=game.headers.get("Round"),
        date=game.headers.get("Date"),
        result=game.headers.get("Result"),
        time_control=game.headers.get("TimeControl"),
        eco=game.headers.get("ECO"),
        opening=game.headers.get("Opening"),
        analysis_status="analyzing"
    )

    db.add(db_game)
    try:
        db.commit()
        db.refresh(db_game)

    except IntegrityError:
        db.rollback()

        db_game = (
            db.query(Game)
            .filter(Game.pgn_hash == pgn_hash)
            .one()
        )

    game_id = db_game.id

    try:
        board = game.board()
        moves = []
        move_analysis_rows = [] # Stores move classifications
        node = game
        ply_index = 0

        while node.variations:
            next_node = node.variation(0)

            move = next_node.move
            moving_color = board.turn
            fen_before = board.fen()
            san = board.san(move)
            elo = white_elo if moving_color == chess.WHITE else black_elo

            classification, expected_before, expected_after, expected_points_loss = await calculate_classification(board, move, moving_color, elo)
            fen_after = board.fen()

            moves.append({
                "uci": move.uci(),
                "san": san,
                "fen_before": fen_before,
                "fen_after": fen_after,
                "expected_points_before": expected_before,
                "expected_points_after": expected_after,
                "expected_points_loss": expected_points_loss,
                "classification": classification,
            })

            # Storing the result of the calculations
            move_analysis_rows.append(
                MoveAnalysis(
                    game_id=game_id,
                    ply_index=ply_index,
                    move_uci=move.uci(),
                    fen_before=fen_before,
                    expected_points_before=expected_before,
                    expected_points_after=expected_after,
                    expected_points_loss=expected_points_loss,
                    classification=classification, 
                )
            )

            ply_index += 1
            node = next_node

        db.add_all(move_analysis_rows)
        db_game.analysis_status = "complete"
        db.commit()

    except Exception:
        db.rollback()
        logger.exception(
            f"Analysis failed for game_id={game_id}"
        )

        failed_game = (
            db.query(Game)
            .filter(Game.id == game_id)
            .one_or_none()
        )

        if failed_game is not None:
            failed_game.analysis_status = "failed"
            db.commit()
        raise

    return {
        "headers": dict(game.headers),
        "moves": moves
    }

def get_elo(game, color):
    rating = None
    value = game.headers.get("WhiteElo") if color == chess.WHITE else game.headers.get("BlackElo")

    try:
        rating = int(value) if value is not None else None
    except ValueError:
        pass
    return rating

@app.post("/evaluate")
async def evaluate(payload: EvaluateRequest):
    if engine is None:
        return {"error": "Engine not initialized"}
    
    pv_lines = []

    board = chess.Board(payload.fen)
    async with engine_lock:
        infoList = await engine.analyse(board, chess.engine.Limit(depth=15), multipv = 5)

    for infoDict in infoList:
        score = infoDict.get("score")
        pv = infoDict.get("pv") # List of move objects

        white_score = None 

        if score is not None:
            white_score = score.white().score(mate_score=10000)

        moves = []

        if pv:
            for move in pv:
                san = board.san(move)
                piece = board.piece_at(move.from_square)                

                moves.append({
                    "pieceMoved": piece.unicode_symbol() if piece else None,
                    "uci": move.uci(),
                    "san": san,
                    }
                )

                board.push(move)
        
        board.set_fen(payload.fen)
        
        pv_lines.append(
            {'score': white_score,
            'line': moves}
                        )
    return {"pv_lines": pv_lines}

async def generate_analysis_events(fen: str) -> AsyncIterator[str]:
    root_board = chess.Board(fen)

    async with engine_lock:
        with await engine.analysis(
            root_board,
            chess.engine.Limit(time=20),
            multipv=5,
        ) as analysis:
            async for info in analysis:
                pv_board = chess.Board(fen)
                score = info.get("score")
                pv = info.get("pv")

                white_score = None
                moves = []

                if score is not None:
                    white_score = score.white().score(mate_score=10000)

                if pv:
                    for move in pv:
                        san = pv_board.san(move)
                        piece = pv_board.piece_at(move.from_square)

                        moves.append({
                            "pieceMoved": piece.unicode_symbol() if piece else None,
                            "uci": move.uci(),
                            "san": san,
                        })

                        pv_board.push(move)

                payload = {
                    "multipv": info.get("multipv"),
                    "depth": info.get("depth"),
                    "whiteScore": white_score,
                    "line": moves,
                }

                yield f"data: {json.dumps(payload)}\n\n"

@app.get("/evaluate/stream", response_class=StreamingResponse)
async def stream_evaluate(fen : str) -> StreamingResponse:
    if engine is None:
        raise HTTPException(
            status_code=503,
            detail="Engine not initialized"
        )

    try:
        chess.Board(fen)
    except ValueError as error:
        raise HTTPException(status_code=400, detail="Invalid FEN") from error

    return StreamingResponse(
        generate_analysis_events(fen),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )

@app.get("/classificationData/{gameId}")
async def get_classification_data(gameId: int, db: Session=Depends(get_db)):
    game = db.query(Game).filter(Game.id == gameId).first()

    if game is None:
        raise HTTPException(status_code=404, 
                            detail="Game not found")
    
    if game.analysis_status in {"pending", "analyzing"}:
        return JSONResponse(
            status_code=202,
            content={
                "status": game.analysis_status,
                "classification": [],
            }
        )

    if game.analysis_status == "failed":
        raise HTTPException(
            status_code=500,
            detail="Game analysis failed"
        )
    
    rows = (
        db.query(MoveAnalysis.classification)
        .filter(MoveAnalysis.game_id == gameId)
        .order_by(MoveAnalysis.ply_index)
        .all()
    )

    classifications = [
        row.classification for row in rows
    ]
    
    return {
        "status": "complete",
        "classification": classifications
        }

async def calculate_classification(board, move, moving_color, elo):
    active_engine = engine

    if active_engine is None:
        raise RuntimeError("Engine is not initialized")

    if board.legal_moves.count() == 1:
        return ("forced", None, None, None)

    async with engine_lock:
        before_info = await active_engine.analyse(board, chess.engine.Limit(depth=15))
    before_score = before_info.get("score")

    expected_before = None
    expected_after = None
    expected_points_loss = None
    classification = None
    
    perspective = moving_color
    before_result = calc_score_result(before_score, perspective)

    board.push(move)

    async with engine_lock:
        after_info = await active_engine.analyse(board, chess.engine.Limit(depth=15))
    after_score = after_info.get("score")

    after_result = calc_score_result(after_score, perspective)

    if before_result["cp"] is not None and after_result["cp"] is not None:
        expected_before = expected_points_from_cp(before_result["cp"])
        expected_after = expected_points_from_cp(after_result["cp"])
        expected_points_loss = expected_before - expected_after
        classification = classify_expected_points_loss(expected_points_loss)

    return (classification, expected_before, expected_after, expected_points_loss)

def calc_score_result(score, perspective):
    result = {
                "kind": "unavailable",
                "cp": None,
                "mate_in": None,
              }
    if score is None:
        return result

    povScore = score.pov(perspective)

    if povScore.is_mate():
        result["kind"] = "mate"
        result["mate_in"] = povScore.mate()
    else:
        result["kind"] = "cp"
        result["cp"] = povScore.score()

    return result 

