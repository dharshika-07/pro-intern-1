import {useState} from 'react';

function StoryGame({story, onNewStory}) {
    const rootNodeId = story?.root_node?.id || null;
    const [currentNodeId, setCurrentNodeId] = useState(rootNodeId);
    const [history, setHistory] = useState([{ id: rootNodeId, label: "Start" }]);

    const currentNode = story?.all_nodes?.[currentNodeId] || null;
    const isEnding = currentNode?.is_ending || false;
    const isWinningEnding = currentNode?.is_winning_ending || false;
    const options = (!isEnding && currentNode?.options) ? currentNode.options : [];

    const chooseOption = (optionId, optionText) => {
        setCurrentNodeId(optionId)
        setHistory(prev => [...prev, { id: optionId, label: optionText }])
    }

    const navigateToHistory = (index) => {
        const target = history[index]
        setCurrentNodeId(target.id)
        setHistory(history.slice(0, index + 1))
    }

    const restartStory = () => {
        setCurrentNodeId(rootNodeId)
        setHistory([{ id: rootNodeId, label: "Start" }])
    }

    return <div className="story-game">
        <header className="story-header">
            <h2>{story.title}</h2>
        </header>

        {/* Breadcrumb Navigation Path */}
        <nav className="breadcrumbs-container">
            {history.map((item, index) => (
                <span key={index} className="breadcrumb-item">
                    {index > 0 && <span className="breadcrumb-separator"> / </span>}
                    {index === history.length - 1 ? (
                        <span className="breadcrumb-current">{item.label}</span>
                    ) : (
                        <button 
                            onClick={() => navigateToHistory(index)} 
                            className="breadcrumb-link"
                        >
                            {item.label}
                        </button>
                    )}
                </span>
            ))}
        </nav>

        <div className="story-content">
            {currentNode && <div className="story-node">
                <p>{currentNode.content}</p>

                {isEnding ?
                    <div className="story-ending">
                        <h3>{isWinningEnding ? "Congratulations!" : "The End"}</h3>
                        <p className={isWinningEnding ? "winning-message" : "ending-message"}>
                            {isWinningEnding ? "You reached a winning ending." : "Your adventure has ended."}
                        </p>
                    </div>
                    :
                    <div className="story-options">
                        <h3>What will you do?</h3>
                        <div className="options-list">
                            {options.map((option, index) => {
                                return <button
                                        key={index}
                                        onClick={() => chooseOption(option.node_id, option.text)}
                                        className="option-btn"
                                        >
                                        {option.text}
                                    </button>
                            })}
                        </div>
                    </div>
                }
            </div>}

            <div className="story-controls">
                <button onClick={restartStory} className="reset-btn">
                    Restart Story
                </button>
            </div>

            {onNewStory && <button onClick={onNewStory} className="new-story-btn">
                New Story
            </button>}

        </div>
    </div>
}

export default StoryGame