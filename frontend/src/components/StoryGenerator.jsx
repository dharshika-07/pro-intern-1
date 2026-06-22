import {useState, useEffect, useCallback} from "react"
import {useNavigate} from "react-router-dom";
import axios from "axios";
import ThemeInput from "./ThemeInput.jsx";
import LoadingStatus from "./LoadingStatus.jsx";
import {API_BASE_URL} from "../util.js";


function StoryGenerator() {
    const navigate = useNavigate()
    const [theme, setTheme] = useState("")
    const [jobId, setJobId] = useState(null)
    const [jobStatus, setJobStatus] = useState(null)
    const [error, setError] = useState(null)
    const [loading, setLoading] = useState(false)

    const fetchStory = useCallback(async (id) => {
        const targetUrl = `/story/${id}`;
        console.log(`[TEMP LOG] Frontend navigation event: Navigating to ${targetUrl}`, { story_id: id });
        try {
            setLoading(false)
            setJobStatus("completed")
            navigate(targetUrl)
        } catch (e) {
            console.error(`[TEMP LOG] Frontend caught exception during navigation to ${targetUrl}:`, e);
            setError(`Failed to load story: ${e.message}`)
            setLoading(false)
        }
    }, [navigate])

    const pollJobStatus = useCallback(async (id) => {
        const requestUrl = `${API_BASE_URL}/jobs/${id}`;
        console.log(`[TEMP LOG] Frontend API request: GET ${requestUrl}`, { job_id: id });
        try {
            const response = await axios.get(requestUrl)
            console.log(`[TEMP LOG] Frontend API response status: ${response.status} for GET ${requestUrl}`);
            console.log(`[TEMP LOG] Frontend API response body:`, response.data);
            const {status, story_id, error: jobError} = response.data
            console.log(`[TEMP LOG] Frontend job_id: ${id}, job status: ${status}, story_id: ${story_id}`);
            setJobStatus(status)

            if (status === "completed" && story_id) {
                fetchStory(story_id)
            } else if (status === "failed" || jobError) {
                setError(jobError || "Failed to generate story")
                setLoading(false)
            }
        } catch (e) {
            console.error(`[TEMP LOG] Frontend caught exception in pollJobStatus GET ${requestUrl}:`, e);
            if (e.response) {
                console.log(`[TEMP LOG] Frontend API response status (error): ${e.response.status}`);
                console.log(`[TEMP LOG] Frontend API response body (error):`, e.response.data);
            }
            if (e.response?.status !== 404) {
                setError(`Failed to check story status: ${e.message}`)
                setLoading(false)
            }
        }
    }, [fetchStory])

    const generateStory = useCallback(async (themeVal) => {
        setLoading(true)
        setError(null)
        setTheme(themeVal)
        const requestUrl = `${API_BASE_URL}/stories/create`;
        console.log(`[TEMP LOG] Frontend API request: POST ${requestUrl} with payload:`, { theme: themeVal });

        try {
            const response = await axios.post(requestUrl, {theme: themeVal})
            console.log(`[TEMP LOG] Frontend API response status: ${response.status} for POST ${requestUrl}`);
            console.log(`[TEMP LOG] Frontend API response body:`, response.data);
            const {job_id, status} = response.data
            console.log(`[TEMP LOG] Frontend generated job_id: ${job_id}, status: ${status}`);
            setJobId(job_id)
            setJobStatus(status)

            pollJobStatus(job_id)
        } catch (e) {
            console.error(`[TEMP LOG] Frontend caught exception in generateStory POST ${requestUrl}:`, e);
            if (e.response) {
                console.log(`[TEMP LOG] Frontend API response status (error): ${e.response.status}`);
                console.log(`[TEMP LOG] Frontend API response body (error):`, e.response.data);
            }
            setLoading(false)
            setError(`Failed to generate story: ${e.message}`)
        }
    }, [pollJobStatus])

    useEffect(() => {
        let pollInterval;

        if (jobId && (jobStatus === "pending" || jobStatus === "processing")) {
            console.log(`[DEBUG] StoryGenerator: Starting 5s poll interval for job: ${jobId} (status: ${jobStatus})`);
            pollInterval = setInterval(() => {
                pollJobStatus(jobId)
            }, 5000)
        }

        return () => {
            if (pollInterval) {
                console.log(`[DEBUG] StoryGenerator: Clearing poll interval for job: ${jobId}`);
                clearInterval(pollInterval)
            }
        }
    }, [jobId, jobStatus, pollJobStatus])

    const reset = () => {
        console.log(`[DEBUG] StoryGenerator: Resetting state.`);
        setJobId(null)
        setJobStatus(null)
        setError(null)
        setTheme("")
        setLoading(false)
    }

    return <div className="story-generator">
        {error && <div className="error-message">
            <p>{error}</p>
            <button onClick={reset}>Try Again</button>
        </div>}

        {!jobId && !error && !loading && <ThemeInput onSubmit={generateStory}/>}

        {loading && <LoadingStatus theme={theme} />}
    </div>
}

export default StoryGenerator