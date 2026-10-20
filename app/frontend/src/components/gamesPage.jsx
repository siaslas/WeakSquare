import {useState} from 'react';
import axios from 'axios';
import GamesList from './gamesList';

function FileUploader({onGameLoaded, setMoveAnalyses}) {
  const [selectedFile, setSelectedFile] = useState(null);

	const onFileChange = (e) => { 
		setSelectedFile(e.target.files[0]);
	};

  const onFileUpload = async () => {
    if (!selectedFile) return;

    const pgn = await selectedFile.text();
    onGameLoaded(pgn);

    // Send pgn file to the backend
		const formData = new FormData();
		formData.append("file", selectedFile);
    await axios.post( 
      `${import.meta.env.VITE_API_URL}/uploadFile/`, 
      formData
    )
    .then((res) => {
      if (res.data.analyses) {
        setMoveAnalyses(res.data.analyses);
      }

    })
    .catch((err) => console.error(err.response?.data ?? err));
	};

  return (
		<div>
			<div className="flex justify-center gap-2">
				<input
					type="file"
					className="text-stone-900 border-2 rounded-[8px] p-4 cursor-pointer"
					style={{ backgroundColor: '#C98686' }}
					onChange={onFileChange}
				/>
				<button onClick={onFileUpload} style={{ backgroundColor: '#C98686' }}>Upload</button>
			</div>
		</div>
	);
}

export default function GamesPage({onGameLoaded, setMoveAnalyses}){
  return(
    <>
      <FileUploader onGameLoaded={onGameLoaded} setMoveAnalyses={setMoveAnalyses}/>
      <GamesList onGameLoaded={onGameLoaded} setMoveAnalyses={setMoveAnalyses}/>
    </>
  );
}
