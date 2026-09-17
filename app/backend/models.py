from database import Base
from sqlalchemy import Column, Integer, String, Float, TIMESTAMP, Text, text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, nullable=False)
    pgn_hash = Column(String, unique=True, nullable=False)
    white_player = Column(String)
    black_player = Column(String)
    white_elo = Column(Integer)
    black_elo = Column(Integer)
    event = Column(String)
    site = Column(String)
    round_tag = Column(String)
    date = Column(String)
    result = Column(String)
    time_control = Column(String)
    eco = Column(String)
    opening = Column(String)
    raw_pgn = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))
    analysis_status: Mapped[str] = mapped_column(String, nullable=False, default="pending") 

class MoveAnalysis(Base):

    __tablename__ = "move_analyses"

    __table_args__ = (
        UniqueConstraint(
            "game_id",
            "ply_index",
            name="uq_move_analyses_game_ply",
        ),
    )

    id = Column(Integer, primary_key=True)
    game_id = Column(
        Integer,
        ForeignKey("games.id", ondelete="CASCADE"),
        nullable=False,
    )
    ply_index = Column(Integer, nullable=False)
    move_uci = Column(String, nullable=False)
    fen_before = Column(Text, nullable=False)
    expected_points_before = Column(Float)
    expected_points_after = Column(Float)
    expected_points_loss = Column(Float)
    classification = Column(String)
