import {Chessboard} from 'react-chessboard';
import {useState, useEffect} from 'react';
import ResizableBoard from './ResizableBoard';
import MoveNavigation from './moveNavigation.jsx';
import MoveListPanel from './moveListPanel.jsx';
import AnalysisPanel from './analysisPanel.jsx';

import bestIcon from '../assets/chess_move_icons_svg_set/best.svg';
import excellentIcon from "../assets/chess_move_icons_svg_set/excellent.svg";
import goodIcon from "../assets/chess_move_icons_svg_set/good.svg";
import inaccuracyIcon from "../assets/chess_move_icons_svg_set/inaccuracy.svg";
import mistakeIcon from "../assets/chess_move_icons_svg_set/mistake.svg";
import blunderIcon from "../assets/chess_move_icons_svg_set/blunder.svg";
import forcedIcon from "../assets/chess_move_icons_svg_set/forced.svg";
import bookIcon from "../assets/chess_move_icons_svg_set/book.svg";

const classificationMap = {
  best: bestIcon,
  excellent: excellentIcon,
  good: goodIcon,
  inaccuracy: inaccuracyIcon,
  mistake: mistakeIcon,
  blunder: blunderIcon,
  forced: forcedIcon,
  book: bookIcon,
}

function ChessBoard({chessGame, chessPosition, setChessPosition, moveList, moveIndex, goToMove, currentMoveToSquare, currentClassification}){
    const [moveFrom, setMoveFrom] = useState('');
    const [optionSquares, setOptionSquares] = useState({});

    useEffect(() => {
      setMoveFrom('');
      setOptionSquares({});
    }, [chessPosition]);

	    // Handle key press for left and right arrow keys
    useEffect(() => {
     function handleKeyDown(e) {
      if(!moveList || moveList.length === 0) return;

      if (e.key === "ArrowLeft"){
        goToMove((prev) => {
          if(prev === 0) return prev;
          return prev - 1;
        });
      }

      if(e.key === "ArrowRight") {
        goToMove((prev) => {
          if (prev === moveList.length) return prev;
          return prev + 1;
        });
      }
     }
     window.addEventListener('keydown', handleKeyDown);
     return () => window.removeEventListener('keydown', handleKeyDown);
    }, [moveList, goToMove])

		// Get the move options for a square to show valid moves
    function getMoveOptions(square) {
      // get the moves for the square
      const moves = chessGame.moves({
        square,
        verbose: true
      });

      // if no moves, clear the option squares
      if (moves.length === 0) {
        setOptionSquares({});
        return false;
      }

      // create a new object to store the option squares
      const newSquares = {};

      // loop through the moves and set the option squares
      for (const move of moves) {
        newSquares[move.to] = {
          background: chessGame.get(move.to) && chessGame.get(move.to)?.color !== chessGame.get(square)?.color ? 'radial-gradient(circle, rgba(188, 43, 178, 0.61) 85%, transparent 85%)' // larger circle for capturing
          : 'radial-gradient(circle, rgba(188, 43, 178, 0.61) 25%, transparent 25%)', // smaller circle for moving
          borderRadius: '50%'
        };
      }

      // set the square clicked to move from to yellow
      newSquares[square] = {
        background: 'rgba(255, 255, 0, 0.4)'
      };

      // set the option squares
      setOptionSquares(newSquares);

      // return true to indicate that there are move options
      return true;
    }
    function onSquareClick({square, piece}) {
      // Piece clicked to move
      if (!moveFrom && piece) {
        const hasMoveOptions = getMoveOptions(square);
        if (hasMoveOptions) {
          setMoveFrom(square);
        }
        return;
      }

      // Move to square clicked, check if valid move
      const moves = chessGame.moves({
        square: moveFrom,
        verbose: true
      });
      console.log(moves);
      const foundMove = moves.find(m => m.from === moveFrom && m.to === square);

      // Not a valid move
      if (!foundMove) {
        const hasMoveOptions = getMoveOptions(square);
        setMoveFrom(hasMoveOptions ? square : '');
        return;
      }

      // Make normal move
      try {
        chessGame.move({
          from: moveFrom,
          to: square,
          promotion: 'q'
        });
      } catch {
        const hasMoveOptions = getMoveOptions(square);
        if (hasMoveOptions) {
          setMoveFrom(square);
        }
        return;
      }

      // Update the position state
      setChessPosition(chessGame.fen());

      setMoveFrom('');
      setOptionSquares({});
    }
    // Handle piece drop
    function onPieceDrop({sourceSquare, targetSquare}) {
      // type narrow targetSquare potentially being null (e.g. if dropped off board)
      if (!targetSquare) {
        return false;
      }

      // try to make the move according to chess.js logic
      try {
        chessGame.move({
          from: sourceSquare,
          to: targetSquare,
          promotion: 'q' // always promote to a queen for example simplicity
        });

        // update the position state upon successful move to trigger a re-render of the chessboard
        setChessPosition(chessGame.fen());

				// clear moveFrom and optionSquares
        setMoveFrom('');
        setOptionSquares({});

        // return true as the move was successful
        return true;
      } catch {
        // return false as the move was not successful
        return false;
      }
    }

    function classificationOverlayRenderer ({square, children}) {
        const classificationIcon = classificationMap[currentClassification];

        return (
          <div style={{
            position: "relative",
            width: "100%",
            height: "100%",
            ...optionSquares[square]
          }}>
            {children}
            {square === currentMoveToSquare && classificationIcon && (
              <img
                src={classificationIcon}
                style={{
                  position: "absolute",
                  top: -12,
                  right: -12,
                  width: "60%",
                  height: "60%",
                  pointerEvents: "none",
                  zIndex: 3,
                }}
              />
            )}
          </div>
        );
    }
    // Set the chessboard options
    const chessboardOptions = {
      position: chessPosition,
      onPieceDrop,
			onSquareClick,
      id: 'play-vs-random',
			boardStyle: {
        borderRadius: '10px',
        boxShadow: '0 0 10px 0 rgba(0, 0, 0, 0.5)',
        border: '1px solid #000',
				margin: '0 auto',
				width: '100%',
      },
			squareStyles: optionSquares,
      squareRenderer: classificationOverlayRenderer,
    };

    // Render the chessboard
    return <Chessboard options={chessboardOptions} />;
}

function MoveAnalysisDetails({analysis}) {
  const classification = !analysis
    ? "Select a move"
    : analysis.is_forced
      ? "Forced"
      : analysis.classification ?? "Not classified";
  const loss = analysis?.expected_points_loss;

  return (
    <section className="rounded-lg border border-slate-300 bg-slate-100 px-4 py-3 text-center text-slate-700 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Classification</p>
      <p className="mb-3 font-semibold capitalize">{classification}</p>
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Expected-points loss</p>
      <p className="font-semibold">
        {loss !== null && loss !== undefined ? loss.toFixed(3) : "Not applicable"}
      </p>
    </section>
  );
}

export default function Analysis({analysisProps}){
  const [boardSize, setBoardSize] = useState(560);
  const {moveList, chessPosition, goToMove, currentMoveAnalysis} = analysisProps;
  const moveListWidth = 400;
  const panelGap = 35;

  return (
  <>
    <div className="flex max-w-[1500px] mx-auto mt-[100px] gap-[35px] justify-center">
      <aside className="w-[180px] self-start">
        <MoveAnalysisDetails analysis={currentMoveAnalysis} />
      </aside>
      <ResizableBoard boardSize={boardSize} onResize={setBoardSize}>
        <ChessBoard {...analysisProps} />
      </ResizableBoard>
      <MoveListPanel moveList={moveList} goToMove={goToMove} panelHeight={boardSize} />
    </div>
    <div className="mt-[40px]">
      <AnalysisPanel
        fen={chessPosition}
        panelWidth={boardSize + moveListWidth + panelGap}
      />
    </div>
    <MoveNavigation {...analysisProps} />
  </>
  );
}
