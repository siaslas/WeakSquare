import {useState, useEffect} from 'react';
import { useNavigate } from "react-router-dom";
import axios from 'axios';

function wait(milliseconds){
  return new Promise((resolve) => {
    setTimeout(resolve, milliseconds);
  });
}
async function retrieveClassificationData(gameId){
  // Hit the backend endpoint classificationData
  const maxAttempts = 120

  for (let attempt = 0; attempt < maxAttempts; attempt += 1){
    const res = await axios.get(
      `${import.meta.env.VITE_API_URL}/classificationData/${gameId}`,
      {
        validateStatus: (status) => 
          status === 200 || status === 202,
      }
    );

    if (res.data.status === "complete"){
      return res.data.analyses;
    }

    await wait(1000);
  }

  throw new Error("Game analysis times out");
}

export default function GamesList({onAnalysisSelected}){
  const [games, setGames] = useState([]);
  const [loadingGameId, setloadingGameId] = useState(null);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    const fetchGames = async () => {
      await axios.get(`${import.meta.env.VITE_API_URL}/gamesList`)
      .then((res) => {
        setGames(res.data);
      })
    };

    fetchGames();
    const interval = setInterval(fetchGames, 5000);
   
    return () => clearInterval(interval);
  }, []);

  const handleAnalyze = async (pgn, gameId) => {

    setloadingGameId(gameId);
    setError("");

    try {
      const analyses = await retrieveClassificationData(gameId);
      onAnalysisSelected(pgn, analyses);
      navigate("/analysis"); 
    } catch (requestError) {
      console.error(requestError.response?.data ?? requestError);
      setError(
        requestError.response.data?.detail ??
        "Unable to load game analysis"
      );
    } finally {
      setloadingGameId(null);
    }
  };

  return(
   <>
    <div>
      {error && <p className="text-red-600">{error}</p>}
      <div>
        {games.map((game, index) => (
          <div key={game.id} className="flex w-[85%] max-w-[1000px] mx-auto gap-4 my-[15px] items-center">
            <ul className="flex-1 m-0 p-0 list-none">
              <li
                style={{ backgroundColor: index % 2 === 0 ? '#94C5CC' : '#B4D2E7' }}
                className="grid w-full grid-cols-4 gap-4 items-center px-4 text-left"
              >
                <div className="flex flex-wrap">
                  <span className="w-full">White: {game.white_player}</span>
                  <span className="w-full">Black: {game.black_player}</span>
                </div>
                <span>Result: {game.result}</span>
                <span>Event: {game.event}</span>
                <span>Date: {game.date}</span>
              </li>
            </ul>
            <button
              disabled={loadingGameId == game.id}
              onClick={() => handleAnalyze(game.pgn, game.id)}
              style={{ backgroundColor: '#C98686' }}
            >
              {loadingGameId === game.id
                ? "Waiting for analysis..."
                : "Analyze"
              }
            </button>
          </div>
        ))}
      </div>
    </div>
   </> 
  );
}
