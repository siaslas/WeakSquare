import { useState } from 'react';
import {Navigate, Routes, Route} from 'react-router-dom';
import {Chess} from 'chess.js';

import NavBar from './components/navBar.jsx';
import GamesPage from './components/gamesPage.jsx';
import AnalysisPage from './components/analysisPage.jsx';

function App() {
  const [chessGame, setChessGame] = useState(() => new Chess());
  const [chessPosition, setChessPosition] = useState(() => chessGame.fen());
  const [moveList, setMoveList] = useState([]);
  const [analysesByPly, setAnalysesByPly] = useState({});
  const [moveIndex, setMoveIndex] = useState(0);
  const [hasSelectedAnalysis, setHasSelectedAnalysis] = useState(false);

  function syncMoveIndex(update) {
    const nextMoveIndex = typeof update === "function" ? update(moveIndex) : update;

    chessGame.reset();
    for (let i = 0; i < nextMoveIndex; i++) {
      const move = moveList[i];
      chessGame.move({ from: move.from, to: move.to, promotion: move.promotion });
    }

    setMoveIndex(nextMoveIndex);
    setChessPosition(chessGame.fen());
  }

  function loadGameFromPgn(pgn){
    const game = new Chess();
    game.loadPgn(pgn);

    setMoveList(game.history({verbose: true}));
    setMoveIndex(0);
    setAnalysesByPly({});
    setHasSelectedAnalysis(false);
    chessGame.reset();
    setChessPosition(chessGame.fen());
  }

  function loadMoveAnalyses(analyses = []) {
    const nextAnalysesByPly = Object.fromEntries(
      analyses.map((analysis) => [analysis.ply_index, analysis])
    );
    setAnalysesByPly(nextAnalysesByPly);
  }

  function selectAnalysis(pgn, analyses) {
    loadGameFromPgn(pgn);
    loadMoveAnalyses(analyses);
    setHasSelectedAnalysis(true);
  }

  const currentMove = moveIndex > 0 ? moveList[moveIndex-1] : null;
  const currentMoveAnalysis = moveIndex > 0 ? analysesByPly[moveIndex - 1] : null;
  const currentClassification = currentMoveAnalysis?.classification;
  const analysisProps = { chessGame,
                          chessPosition,
                          setChessPosition, 
                          moveList,
                          moveIndex, 
                          goToMove: syncMoveIndex,
                          currentMoveToSquare: currentMove?.to,
                          currentClassification,
                          currentMoveAnalysis,
                        };

  return (
    <div className="flex">
      <div className="min-h-screen w-[100vw]">
        <h1 className="mb-[2rem]">WeakSquare</h1>
        <NavBar canAnalyze={hasSelectedAnalysis} />
        <Routes>
          <Route path="/" element={<GamesPage onGameLoaded={loadGameFromPgn} setMoveAnalyses={loadMoveAnalyses} onAnalysisSelected={selectAnalysis} />} />
          <Route
            path="/analysis"
            element={
              hasSelectedAnalysis
                ? <AnalysisPage analysisProps={analysisProps}/>
                : <Navigate to="/" replace />
            }
          />
        </Routes>
      </div>
    </div>
  );
}

export default App
