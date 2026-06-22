import {useState, useEffect} from 'react';
import {useParams, useNavigate} from "react-router-dom"
import axios from 'axios';
import LoadingStatus from "./LoadingStatus.jsx";
import StoryGame from "./StoryGame.jsx";
import {API_BASE_URL} from "../util.js";


function StoryLoader() {
    const {id} = useParams();
    const navigate = useNavigate();
    const [story, setStory] = useState(null);
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null);

    const [prevId, setPrevId] = useState(id);
    if (id !== prevId) {
        setPrevId(id);
        setStory(null);
        setLoading(true);
        setError(null);
    }

    useEffect(() => {
        let active = true;
        const requestUrl = `${API_BASE_URL}/stories/${id}/complete`;
        console.log(`[TEMP LOG] Frontend API request: GET ${requestUrl}`, { story_id: id });
        axios.get(requestUrl)
            .then(response => {
                console.log(`[TEMP LOG] Frontend API response status: ${response.status} for GET ${requestUrl}`);
                console.log(`[TEMP LOG] Frontend API response body:`, response.data);
                if (active) {
                    setStory(response.data);
                    setLoading(false);
                }
            })
            .catch(err => {
                console.error(`[TEMP LOG] Frontend caught exception in get_complete_story GET ${requestUrl}:`, err);
                if (err.response) {
                    console.log(`[TEMP LOG] Frontend API response status (error): ${err.response.status}`);
                    console.log(`[TEMP LOG] Frontend API response body (error):`, err.response.data);
                }
                if (active) {
                    if (err.response?.status === 404) {
                        setError("Story is not found.");
                    } else {
                        setError("Failed to load story");
                    }
                    setLoading(false);
                }
            });
        return () => {
            active = false;
        };
    }, [id]);

    const createNewStory = () => {
        navigate("/")
    }

    if (loading) {
        return <LoadingStatus theme={"story"} />
    }

    if (error) {
        return <div className="story-loader">
            <div className="error-message">
                <h2>Story Not Found</h2>
                <p>{error}</p>
                <button onClick={createNewStory}>Go to Story Generator</button>
            </div>
        </div>
    }

    if (story) {
        return <div className="story-loader">
            <StoryGame key={story.id} story={story} onNewStory={createNewStory} />
        </div>
    }
}

export default StoryLoader;